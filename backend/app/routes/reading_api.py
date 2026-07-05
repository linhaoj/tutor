"""阅读课 API"""
import os
import re
import json
import urllib.request
import urllib.error
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

router = APIRouter(prefix="/api/reading", tags=["阅读课"])

# ── LLM 配置 ─────────────────────────────────────────────────
# GITHUB_TOKEN 从环境变量读取，配置在 backend/.env.local（不进git，需在本地和服务器上各自创建）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = "meta/llama-3.3-70b-instruct"
GITHUB_API_URL = "https://models.github.ai/inference/chat/completions"

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

def count_words(text: str) -> int:
    return len(re.findall(r"\b[a-zA-Z']+\b", text))


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """调用 GitHub Models（同步，供 executor 使用）"""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN 未配置，请在 backend/.env.local 中设置")

    payload = json.dumps({
        "model": GITHUB_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        GITHUB_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise HTTPException(status_code=502, detail=f"LLM API 错误: {e.code} {body}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用 LLM 失败: {str(e)}")


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


def build_translation_prompt(article: str) -> str:
    return f"""You are a professional translator. Translate the following English passage into Simplified Chinese (简体中文).

Rules:
1. Translate paragraph by paragraph — each English paragraph must have a complete, accurate Chinese translation of the SAME content.
2. Do NOT summarize, shorten, or skip any sentences. Every sentence must be translated in full.
3. Use Simplified Chinese characters only (NOT Traditional Chinese).
4. CRITICAL: Every single English word must be translated into Chinese. Do NOT leave any English words, phrases, or terms in the output. Not even technical terms, proper nouns, or difficult words — find a Chinese equivalent for everything.
5. Output ONLY a JSON array of strings, one string per paragraph, in the same order.
6. No extra explanation, no markdown formatting, just the raw JSON array.

Example output format: ["第一段完整翻译", "第二段完整翻译"]

English passage:
{article}
"""


def build_lookup_prompt(word: str, article: str) -> str:
    return f"""You are a Chinese English teacher. A student double-clicked the word "{word}" in the following English article.

Determine the SINGLE most accurate part of speech for "{word}" as it is used in this article, then provide its Simplified Chinese meaning.

Rules:
- Choose ONLY ONE part of speech: vt. OR vi. OR n. OR adj. OR adv. OR prep. OR conj.
- Do NOT combine multiple parts of speech (e.g. never write "vt. n.")
- A noun is always n., even if it looks like a verb form
- Use Simplified Chinese only (NOT Traditional Chinese)
- Chinese meaning: 1-5 characters, concise
- Output ONLY the result, nothing else. No labels, no explanations, no "词性:" or "释义:" prefixes.
- Exact format: abbreviation + period + space + Chinese meaning

Examples of correct output:
vt. 注意到
n. 涡轮机
adj. 遥远的

Examples of WRONG output (never do this):
词性: n. 释义: 质量
词性: vt. 简体中文释义: 注意到

Article:
{article}
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
    """同步生成翻译（在 executor 中运行）"""
    # 计算英文段落数，供校验用
    en_paragraphs = [p.strip() for p in re.split(r'\n{2,}', article) if p.strip()]
    expected_count = len(en_paragraphs)

    prompt = build_translation_prompt(article)
    # 翻译用最大输出 token，防止长文章被截断（API 上限 4096）
    result = call_llm(prompt, max_tokens=4096).strip()

    print(f"\n===== 翻译原始返回 =====\n{result}\n========================")

    # 尝试多种方式解析 JSON 数组
    cleaned = re.sub(r"```json\s*|\s*```", "", result).strip()

    # 方法1：直接 JSON 解析
    try:
        translations = json.loads(cleaned)
        if isinstance(translations, list) and len(translations) > 0:
            print(f"翻译解析成功: {len(translations)} 段（期望 {expected_count} 段）")
            return [str(t) for t in translations]
    except Exception:
        pass

    # 方法2：找到第一个 [ 到最后一个 ] 之间的内容
    try:
        start = cleaned.index('[')
        end = cleaned.rindex(']') + 1
        translations = json.loads(cleaned[start:end])
        if isinstance(translations, list) and len(translations) > 0:
            print(f"翻译解析成功(方法2): {len(translations)} 段")
            return [str(t) for t in translations]
    except Exception:
        pass

    # 方法3：用正则提取 JSON 字符串数组中的各项（处理截断情况）
    try:
        # 找出所有被引号包裹的段落（处理截断的 JSON）
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', cleaned)
        # 过滤掉空字符串和明显不是翻译内容的项
        items = [s.replace('\\"', '"').replace('\\n', '\n') for s in items if len(s) > 5]
        if len(items) >= expected_count:
            print(f"翻译解析成功(方法3-正则): {len(items)} 段")
            return items[:expected_count]
        elif len(items) > 0:
            # 数量不够但有内容，补齐
            print(f"翻译解析成功(方法3-补齐): {len(items)} 段 → 补到 {expected_count} 段")
            while len(items) < expected_count:
                items.append("")
            return items[:expected_count]
    except Exception:
        pass

    # fallback：按空行分段（中文翻译段落通常也用空行分隔）
    print(f"翻译JSON解析失败，使用fallback按段落分割")
    chunks = [c.strip() for c in re.split(r'\n{2,}', cleaned) if c.strip()]
    if len(chunks) >= expected_count:
        return chunks[:expected_count]

    # 按单换行分割
    lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
    if len(lines) >= expected_count:
        return lines[:expected_count]

    # 最终fallback：有多少用多少，不足则补空字符串
    while len(lines) < expected_count:
        lines.append("")
    return lines[:expected_count]


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
