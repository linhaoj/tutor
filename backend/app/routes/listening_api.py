"""听力课 API"""
import os
import uuid
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import ListeningArticle, Schedule, User, AntiForgetSession, Student
from app.routes.auth import get_current_user
from app.services.llm_common import (
    call_llm, call_vision_llm, build_lookup_prompt, generate_translation_sync,
)
from app.services.tencent_asr_client import call_tencent_asr
from app.services.paragraph_alignment import align_paragraphs_to_asr

router = APIRouter(prefix="/api/listening", tags=["听力课"])

# 音频本地存储根目录（相对于backend目录），数据库只存相对路径
LISTENING_AUDIO_STORAGE_DIR = os.getenv("LISTENING_AUDIO_STORAGE_DIR", "uploads/audio")
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg"}
MAX_AUDIO_SIZE_BYTES = 100 * 1024 * 1024  # 100MB


def _audio_storage_root() -> str:
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), LISTENING_AUDIO_STORAGE_DIR)
    os.makedirs(root, exist_ok=True)
    return root


# ── Pydantic Schemas ──────────────────────────────────────────

class ParagraphTimestamp(BaseModel):
    index: int
    text: str = ""
    start: float
    end: float
    match_score: Optional[float] = None


class OCRResponse(BaseModel):
    recognized_text: str


class TranslateRequest(BaseModel):
    article_content: str


class TranslateResponse(BaseModel):
    translation: List[str]


class UploadAudioResponse(BaseModel):
    temp_audio_id: str
    duration_seconds: float
    original_filename: str


class AlignTimestampsRequest(BaseModel):
    temp_audio_id: str
    article_content: str


class AlignTimestampsResponse(BaseModel):
    paragraphs: List[ParagraphTimestamp]
    audio_duration_seconds: float


class SaveListeningArticleRequest(BaseModel):
    title: Optional[str] = None
    article_content: str
    translation: List[str]
    paragraph_timestamps: List[ParagraphTimestamp]
    temp_audio_id: str
    audio_original_filename: str
    audio_mimetype: str
    audio_duration_seconds: float


class SaveListeningArticleResponse(BaseModel):
    id: int
    created_at: str


class UpdateListeningArticleRequest(BaseModel):
    article_content: Optional[str] = None
    translation: Optional[List[str]] = None
    paragraph_timestamps: Optional[List[ParagraphTimestamp]] = None


class BindScheduleRequest(BaseModel):
    schedule_id: int


class ListeningArticleResponse(BaseModel):
    id: int
    schedule_id: Optional[int]
    title: Optional[str]
    article_content: str
    translation: Optional[List[str]]
    paragraph_timestamps: Optional[List[ParagraphTimestamp]]
    audio_url: str
    audio_duration_seconds: Optional[float]
    created_at: str


class LookupWordRequest(BaseModel):
    word: str
    article_context: str


class LookupWordResponse(BaseModel):
    word: str
    chinese_meaning: str


class AntiForgetWordItem(BaseModel):
    english: str
    chinese: str


class CreateListeningAntiForgetRequest(BaseModel):
    student_id: int
    words: List[AntiForgetWordItem]
    time: str
    schedule_id: int


# ── 工具函数 ──────────────────────────────────────────────────

def build_ocr_prompt() -> str:
    return """You are an OCR engine. Extract ALL English text from this image exactly as it appears,
preserving line breaks and paragraph structure where visually apparent.
Output ONLY the extracted text, no explanations, no markdown, no commentary.
If the image contains no readable text, output an empty string."""


def _get_audio_duration_seconds(file_path: str) -> float:
    """用 mutagen 解析音频时长"""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path)
        if audio is not None and audio.info is not None:
            return round(float(audio.info.length), 2)
    except Exception:
        pass
    return 0.0


# ── API 端点 ──────────────────────────────────────────────────

@router.post("/ocr", response_model=OCRResponse)
async def ocr_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """截图识别文字（OCR），前端自行决定把识别结果追加到文本框的哪个位置"""
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="图片内容为空")

    prompt = build_ocr_prompt()
    mimetype = image.content_type or "image/png"

    # call_vision_llm 是同步网络调用，放到线程池跑，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        recognized_text = await loop.run_in_executor(
            executor, call_vision_llm, prompt, contents, mimetype
        )

    return OCRResponse(recognized_text=recognized_text.strip())


@router.post("/translate", response_model=TranslateResponse)
async def translate_article(
    req: TranslateRequest,
    current_user: User = Depends(get_current_user),
):
    """按段落翻译（老师上传的原文可能没有翻译，点击按钮补上）"""
    if not req.article_content.strip():
        raise HTTPException(status_code=400, detail="原文内容不能为空")

    # 听力课按单个换行分段（不是空行），显式传入避免与阅读课的双换行规则冲突
    paragraphs = [p.strip() for p in req.article_content.split("\n") if p.strip()]

    # generate_translation_sync 内部是同步网络调用，放到线程池跑，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        translation = await loop.run_in_executor(
            executor, generate_translation_sync, req.article_content, paragraphs
        )
    return TranslateResponse(translation=translation)


@router.post("/upload-audio", response_model=UploadAudioResponse)
async def upload_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传音频文件，落盘到本地固定目录，返回临时ID供后续保存文章时绑定"""
    ext = os.path.splitext(audio.filename or "")[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的音频格式，仅支持: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}")

    today = date.today()
    rel_dir = os.path.join(str(today.year), f"{today.month:02d}")
    abs_dir = os.path.join(_audio_storage_root(), rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}{ext}"
    rel_path = os.path.join(rel_dir, filename)
    abs_path = os.path.join(abs_dir, filename)

    # 分块写入磁盘，避免大文件一次性读入内存
    size = 0
    with open(abs_path, "wb") as f:
        while chunk := await audio.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_AUDIO_SIZE_BYTES:
                f.close()
                os.remove(abs_path)
                raise HTTPException(status_code=400, detail="音频文件过大，最大支持100MB")
            f.write(chunk)

    duration = _get_audio_duration_seconds(abs_path)

    return UploadAudioResponse(
        temp_audio_id=rel_path,
        duration_seconds=duration,
        original_filename=audio.filename or filename,
    )


@router.post("/align-timestamps", response_model=AlignTimestampsResponse)
async def align_timestamps(
    req: AlignTimestampsRequest,
    current_user: User = Depends(get_current_user),
):
    """调用腾讯云ASR + 文本相似度匹配，返回段落级时间戳预览（不写数据库）"""
    # 按单个换行分段（老师手动换行决定分段，不是空行/双换行）
    paragraphs = [p.strip() for p in req.article_content.split("\n") if p.strip()]
    if not paragraphs:
        raise HTTPException(status_code=400, detail="原文内容不能为空")

    abs_path = os.path.join(_audio_storage_root(), req.temp_audio_id)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="音频文件不存在，请重新上传")

    # call_tencent_asr 内部用同步轮询（time.sleep），必须放到线程池跑，
    # 否则会阻塞整个事件循环，导致服务器在识别期间无法处理任何其他请求
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        asr_words = await loop.run_in_executor(executor, call_tencent_asr, abs_path)

    aligned = align_paragraphs_to_asr(paragraphs, asr_words)
    duration = _get_audio_duration_seconds(abs_path)

    return AlignTimestampsResponse(
        paragraphs=[ParagraphTimestamp(**p) for p in aligned],
        audio_duration_seconds=duration,
    )


@router.post("/articles", response_model=SaveListeningArticleResponse)
async def save_article(
    req: SaveListeningArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存听力课文章（含确认后的时间戳）"""
    abs_path = os.path.join(_audio_storage_root(), req.temp_audio_id)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="音频文件不存在，请重新上传")

    article = ListeningArticle(
        title=req.title,
        article_content=req.article_content,
        translation=req.translation,
        paragraph_timestamps=[p.dict() for p in req.paragraph_timestamps],
        audio_file_path=req.temp_audio_id,
        audio_original_filename=req.audio_original_filename,
        audio_mimetype=req.audio_mimetype,
        audio_duration_seconds=req.audio_duration_seconds,
        alignment_status="confirmed",
        created_by=current_user.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return SaveListeningArticleResponse(
        id=article.id,
        created_at=article.created_at.isoformat()
    )


@router.put("/articles/{article_id}", response_model=SaveListeningArticleResponse)
async def update_article(
    article_id: int,
    req: UpdateListeningArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑文章（排课时小修改）"""
    article = db.query(ListeningArticle).filter(ListeningArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if req.article_content is not None:
        article.article_content = req.article_content
    if req.translation is not None:
        article.translation = req.translation
    if req.paragraph_timestamps is not None:
        article.paragraph_timestamps = [p.dict() for p in req.paragraph_timestamps]
    article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(article)

    return SaveListeningArticleResponse(
        id=article.id,
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
    article = db.query(ListeningArticle).filter(ListeningArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    article.schedule_id = req.schedule_id
    db.commit()
    return {"success": True}


@router.get("/articles/by-schedule/{schedule_id}", response_model=ListeningArticleResponse)
async def get_article_by_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据课程ID获取文章（上课时使用）"""
    article = db.query(ListeningArticle).filter(
        ListeningArticle.schedule_id == schedule_id
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="未找到该课程的听力材料")

    return ListeningArticleResponse(
        id=article.id,
        schedule_id=article.schedule_id,
        title=article.title,
        article_content=article.article_content,
        translation=article.translation,
        paragraph_timestamps=article.paragraph_timestamps,
        audio_url=f"/api/listening/audio/{article.id}",
        audio_duration_seconds=article.audio_duration_seconds,
        created_at=article.created_at.isoformat()
    )


@router.get("/audio/{article_id}")
async def stream_audio(
    article_id: int,
    db: Session = Depends(get_db)
):
    """流式提供音频文件（不鉴权：<audio>标签原生请求不带Authorization头）"""
    article = db.query(ListeningArticle).filter(ListeningArticle.id == article_id).first()
    if not article or not article.audio_file_path:
        raise HTTPException(status_code=404, detail="音频不存在")

    abs_path = os.path.join(_audio_storage_root(), article.audio_file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    return FileResponse(abs_path, media_type=article.audio_mimetype or "audio/mpeg")


@router.post("/lookup-word", response_model=LookupWordResponse)
async def lookup_word(
    req: LookupWordRequest,
    current_user: User = Depends(get_current_user),
):
    """双击单词 → AI 给出文章上下文中的中文释义（与阅读课共用同一套prompt）"""
    prompt = build_lookup_prompt(req.word, req.article_context)

    # call_llm 是同步网络调用，放到线程池跑，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        meaning = await loop.run_in_executor(executor, call_llm, prompt)

    return LookupWordResponse(
        word=req.word,
        chinese_meaning=meaning.strip()
    )


@router.post("/create-anti-forget")
async def create_listening_anti_forget(
    req: CreateListeningAntiForgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """听力课结课后创建抗遗忘（老师审查后调用），结构与阅读课的create-anti-forget一致"""
    if not req.words:
        raise HTTPException(status_code=400, detail="没有需要加入抗遗忘的单词")

    session_id = f"af-listening-{req.student_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    words_data = [{"id": f"l-{i}", "english": w.english, "chinese": w.chinese}
                  for i, w in enumerate(req.words)]

    session = AntiForgetSession(
        id=session_id,
        student_id=req.student_id,
        teacher_id=current_user.id,
        word_set_name="听力课",
        words=words_data,
        review_count=0,
        total_reviews=10,
    )
    db.add(session)

    try:
        hour, minute = map(int, req.time.split(":"))
    except Exception:
        hour, minute = 9, 0

    anti_forget_days = [1, 2, 3, 5, 7, 9, 12, 14, 17, 21]
    today = date.today()

    student = db.query(Student).filter(Student.id == req.student_id).first()

    for day_offset in anti_forget_days:
        target_date = today + timedelta(days=day_offset)

        if not student:
            continue

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
            word_set_name="听力课",
            course_type="review",
            duration=30,
            class_type="small",
            session_id=session_id,
            completed=False,
        )
        db.add(schedule)

    original_schedule = db.query(Schedule).filter(
        Schedule.id == req.schedule_id
    ).first()
    if original_schedule:
        original_schedule.completed = True
        student = db.query(Student).filter(Student.id == req.student_id).first()
        if student:
            hours = 1.0 if original_schedule.class_type == "big" else 0.5
            student.remaining_hours = max(0, student.remaining_hours - hours)

    db.commit()

    return {"success": True, "session_id": session_id}
