"""阅读课 API"""
import re
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import ReadingArticle, Schedule, User, LearningProgress, Word, WordSet, AntiForgetSession, Student
from app.routes.auth import get_current_user
from app.services.llm_common import (
    count_words, call_llm, build_translation_prompt, build_lookup_prompt,
    generate_translation_sync as _generate_translation_sync,
)

router = APIRouter(prefix="/api/reading", tags=["阅读课"])


# word count 目标范围
def get_word_count_range(num_words: int):
    if num_words <= 5:
        return (100, 200)
    elif num_words <= 10:
        return (200, 350)
    else:
        return (300, 500)


# ── Pydantic Schemas ──────────────────────────────────────────

class WordItem(BaseModel):
    english: str
    chinese: str

class GenerateRequest(BaseModel):
    word_set_name: str
    words: List[WordItem]

class GenerateResponse(BaseModel):
    article: str
    translation: List[str]   # 按段落的中文翻译
    word_count: int
    words_used: List[WordItem]

class SaveArticleRequest(BaseModel):
    word_set_name: str
    words_used: List[WordItem]
    article_content: str
    translation: List[str]
    word_count: int

class SaveArticleResponse(BaseModel):
    id: int
    word_count: int
    created_at: str

class UpdateArticleRequest(BaseModel):
    article_content: str
    translation: Optional[List[str]] = None

class ArticleResponse(BaseModel):
    id: int
    schedule_id: Optional[int]
    word_set_name: str
    words_used: List[dict]
    article_content: str
    translation: Optional[List[str]]
    word_count: int
    created_at: str

class BindScheduleRequest(BaseModel):
    schedule_id: int

class LookupWordRequest(BaseModel):
    word: str
    article_context: str   # 整篇文章，用于上下文理解

class LookupWordResponse(BaseModel):
    word: str
    chinese_meaning: str   # AI 给出的中文释义

class AntiForgetWordItem(BaseModel):
    english: str
    chinese: str           # 老师审查后确认的中文意思

class CreateReadingAntiForgetRequest(BaseModel):
    student_id: int
    word_set_name: str
    words: List[AntiForgetWordItem]
    time: str              # 抗遗忘上课时间 "14:00"
    schedule_id: int       # 用于标记课程完成


# ── 工具函数 ──────────────────────────────────────────────────
# count_words / call_llm / build_translation_prompt / build_lookup_prompt / generate_translation_sync
# 已抽取到 app/services/llm_common.py，供阅读课和听力课共用

def build_article_prompt(words: List[WordItem], min_wc: int, max_wc: int) -> str:
    word_list = ", ".join([f"{w.english} ({w.chinese})" for w in words])
    return f"""You are an English teacher creating a reading passage for a student.

Target vocabulary words (you MUST use ALL of them naturally in the passage):
{word_list}

Requirements:
1. Write a coherent English passage between {min_wc} and {max_wc} words.
2. Every target word listed above must appear at least once.
3. CRITICAL - vocabulary difficulty: use ONLY elementary/middle-school level vocabulary (the simplest, most common English words) for everything EXCEPT the target words above. Do NOT use advanced, rare, or low-frequency words elsewhere in the passage. The target words should stand out as the only challenging vocabulary — everything else must be easy enough that the student spends zero effort on words other than the target list.
4. Keep sentence structure simple and clear (avoid complex/nested clauses) so the difficulty comes only from the target words, not from grammar or surrounding vocabulary.
5. Any style is fine (story, dialogue, article, etc.).
6. Output ONLY the passage text, no titles, no explanations, no markdown formatting.
7. Use blank lines to separate paragraphs (at least 2 paragraphs).
"""


def generate_article_sync(words: List[WordItem], min_wc: int, max_wc: int) -> str:
    """同步生成文章（在 executor 中运行）"""
    prompt = build_article_prompt(words, min_wc, max_wc)
    article = ""
    max_retries = 3

    for attempt in range(max_retries):
        article = call_llm(prompt).strip()
        wc = count_words(article)

        article_lower = article.lower()
        missing = [w.english for w in words if w.english.lower() not in article_lower]

        print(f"第{attempt+1}次生成: {wc}词, 缺失: {missing}")

        if min_wc <= wc <= max_wc and len(missing) == 0:
            break

        issues = []
        if wc < min_wc:
            issues.append(f"too short ({wc} words, minimum {min_wc})")
        elif wc > max_wc:
            issues.append(f"too long ({wc} words, maximum {max_wc})")
        if missing:
            issues.append(f"forgot to use: {', '.join(missing)}")

        prompt = build_article_prompt(words, min_wc, max_wc) + \
            f"\n\nIMPORTANT - fix these problems from your previous attempt: {'; '.join(issues)}."

    return article


def generate_translation_sync(article: str) -> List[str]:
    """同步生成翻译（委托给 llm_common 的共用实现）"""
    return _generate_translation_sync(article)


# ── API 端点 ──────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_article(
    req: GenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """并行生成文章 + 中文翻译"""
    if not req.words:
        raise HTTPException(status_code=400, detail="单词列表不能为空")

    min_wc, max_wc = get_word_count_range(len(req.words))

    print(f"\n===== 生成文章 =====")
    print(f"单词({len(req.words)}): {[w.english for w in req.words]}")
    print(f"目标字数: {min_wc}-{max_wc}")

    # 第一步：先生成文章
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        article = await loop.run_in_executor(
            executor, generate_article_sync, req.words, min_wc, max_wc
        )

    # 第二步：并行生成翻译
    with ThreadPoolExecutor() as executor:
        translation = await loop.run_in_executor(
            executor, generate_translation_sync, article
        )

    wc = count_words(article)
    print(f"最终: {wc}词, {len(translation)}段翻译")

    return GenerateResponse(
        article=article,
        translation=translation,
        word_count=wc,
        words_used=req.words
    )


@router.post("/lookup-word", response_model=LookupWordResponse)
async def lookup_word(
    req: LookupWordRequest,
    current_user: User = Depends(get_current_user),
):
    """双击单词 → AI 给出文章上下文中的中文释义"""
    prompt = build_lookup_prompt(req.word, req.article_context)

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        meaning = await loop.run_in_executor(executor, call_llm, prompt)

    return LookupWordResponse(
        word=req.word,
        chinese_meaning=meaning.strip()
    )


@router.post("/articles", response_model=SaveArticleResponse)
async def save_article(
    req: SaveArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存文章（含翻译）"""
    article = ReadingArticle(
        word_set_name=req.word_set_name,
        words_used=[w.dict() for w in req.words_used],
        article_content=req.article_content,
        translation=req.translation,
        word_count=req.word_count,
        created_by=current_user.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return SaveArticleResponse(
        id=article.id,
        word_count=article.word_count,
        created_at=article.created_at.isoformat()
    )


@router.put("/articles/{article_id}", response_model=SaveArticleResponse)
async def update_article(
    article_id: int,
    req: UpdateArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑文章（排课时小修改）"""
    article = db.query(ReadingArticle).filter(ReadingArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.article_content = req.article_content
    article.word_count = count_words(req.article_content)
    if req.translation is not None:
        article.translation = req.translation
    article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(article)

    return SaveArticleResponse(
        id=article.id,
        word_count=article.word_count,
        created_at=article.created_at.isoformat()
    )


@router.post("/articles/{article_id}/bind-schedule")
async def bind_schedule(
    article_id: int,
    req: BindScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """将文章绑定到课程"""
    article = db.query(ReadingArticle).filter(ReadingArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    article.schedule_id = req.schedule_id
    db.commit()
    return {"success": True}


@router.get("/articles/by-schedule/{schedule_id}", response_model=ArticleResponse)
async def get_article_by_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据课程ID获取文章（上课时使用）"""
    article = db.query(ReadingArticle).filter(
        ReadingArticle.schedule_id == schedule_id
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="未找到该课程的文章")

    return ArticleResponse(
        id=article.id,
        schedule_id=article.schedule_id,
        word_set_name=article.word_set_name,
        words_used=article.words_used,
        article_content=article.article_content,
        translation=article.translation,
        word_count=article.word_count,
        created_at=article.created_at.isoformat()
    )


@router.get("/learned-words/{student_id}/{word_set_name}")
async def get_learned_words(
    student_id: int,
    word_set_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生格子1-7的已学单词"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    all_words = db.query(Word).filter(Word.word_set_id == word_set.id).all()
    progress_records = db.query(LearningProgress).filter(
        LearningProgress.student_id == student_id,
        LearningProgress.word_set_name == word_set_name
    ).all()

    stage_map = {p.word_index: p.current_stage for p in progress_records}

    learned_words = []
    for idx, word in enumerate(all_words):
        stage = stage_map.get(idx, 0)
        if 1 <= stage <= 7:
            learned_words.append({
                "id": word.id,
                "english": word.english,
                "chinese": word.chinese,
                "stage": stage,
                "index": idx
            })

    return {"words": learned_words, "total": len(learned_words)}


@router.post("/create-anti-forget")
async def create_reading_anti_forget(
    req: CreateReadingAntiForgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """阅读课结课后创建抗遗忘（老师审查后调用）"""
    from app.models import Schedule
    import uuid
    from datetime import date, timedelta

    if not req.words:
        raise HTTPException(status_code=400, detail="没有需要加入抗遗忘的单词")

    # 创建抗遗忘会话
    session_id = f"af-reading-{req.student_id}-{req.word_set_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    words_data = [{"id": f"r-{i}", "english": w.english, "chinese": w.chinese}
                  for i, w in enumerate(req.words)]

    session = AntiForgetSession(
        id=session_id,
        student_id=req.student_id,
        teacher_id=current_user.id,
        word_set_name=req.word_set_name,
        words=words_data,
        review_count=0,
        total_reviews=10,
    )
    db.add(session)

    # 解析上课时间（"14:00" → hour, minute）
    try:
        hour, minute = map(int, req.time.split(":"))
    except Exception:
        hour, minute = 9, 0

    # 创建10次抗遗忘课程安排
    anti_forget_days = [1, 2, 3, 5, 7, 9, 12, 14, 17, 21]
    today = date.today()

    # 在循环外查一次学生信息，避免重复查询
    student = db.query(Student).filter(Student.id == req.student_id).first()

    for day_offset in anti_forget_days:
        target_date = today + timedelta(days=day_offset)

        if not student:
            continue

        # 构造 scheduled_at（本地时间存为 UTC，与其他课程保持一致）
        scheduled_at = datetime(
            target_date.year, target_date.month, target_date.day,
            hour, minute, 0
        )

        schedule = Schedule(
            teacher_id=current_user.id,
            student_id=req.student_id,
            student_name=student.name,
            scheduled_at=scheduled_at,
            date=target_date,
            time=req.time,
            word_set_name=req.word_set_name,
            course_type="review",
            duration=30,
            class_type="small",
            session_id=session_id,
            completed=False,
        )
        db.add(schedule)

    # 标记原课程完成
    original_schedule = db.query(Schedule).filter(
        Schedule.id == req.schedule_id
    ).first()
    if original_schedule:
        original_schedule.completed = True
        # 扣课时
        student = db.query(Student).filter(Student.id == req.student_id).first()
        if student:
            hours = 1.0 if original_schedule.class_type == "big" else 0.5
            student.remaining_hours = max(0, student.remaining_hours - hours)

    db.commit()

    return {"success": True, "session_id": session_id}
