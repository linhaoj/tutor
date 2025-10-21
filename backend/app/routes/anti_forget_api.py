"""抗遗忘会话API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import AntiForgetSession, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction

logger = get_logger("anti_forget")

router = APIRouter(prefix="/api/anti-forget", tags=["抗遗忘"])


class AntiForgetWord(BaseModel):
    id: int
    english: str
    chinese: str
    is_starred: bool = False


class SessionCreate(BaseModel):
    student_id: int
    word_set_name: str
    teacher_id: str
    words: List[dict]  # 单词列表


class SessionResponse(BaseModel):
    id: str
    student_id: int
    word_set_name: str
    teacher_id: str
    words: List[dict]
    review_count: int
    total_reviews: int
    created_at: datetime


@router.post("/sessions", response_model=SessionResponse)
@safe_transaction("创建抗遗忘会话")
async def create_anti_forget_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建抗遗忘会话"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == session_data.student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 生成会话ID：af_{student_id}_{word_set_name}_{timestamp}
    timestamp = int(datetime.now().timestamp())
    session_id = f"af_{session_data.student_id}_{session_data.word_set_name}_{timestamp}"

    # 创建会话
    session = AntiForgetSession(
        id=session_id,
        student_id=session_data.student_id,
        teacher_id=current_user.id,
        word_set_name=session_data.word_set_name,
        words=session_data.words,
        review_count=0,
        total_reviews=10
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(f"创建抗遗忘会话: ID={session_id}, 学生={student.name}, 单词集={session_data.word_set_name}, 单词数={len(session_data.words)}")

    return SessionResponse(
        id=session.id,
        student_id=session.student_id,
        word_set_name=session.word_set_name,
        teacher_id=session.teacher_id,
        words=session.words,
        review_count=session.review_count,
        total_reviews=session.total_reviews,
        created_at=session.created_at
    )


@router.get("/sessions/student/{student_id}", response_model=List[SessionResponse])
async def get_student_sessions(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的所有抗遗忘会话"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    sessions = db.query(AntiForgetSession).filter(
        AntiForgetSession.student_id == student_id
    ).all()

    return [
        SessionResponse(
            id=s.id,
            student_id=s.student_id,
            word_set_name=s.word_set_name,
            teacher_id=s.teacher_id,
            words=s.words,
            review_count=s.review_count,
            total_reviews=s.total_reviews,
            created_at=s.created_at
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定的抗遗忘会话"""
    session = db.query(AntiForgetSession).filter(
        AntiForgetSession.id == session_id,
        AntiForgetSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return SessionResponse(
        id=session.id,
        student_id=session.student_id,
        word_set_name=session.word_set_name,
        teacher_id=session.teacher_id,
        words=session.words,
        review_count=session.review_count,
        total_reviews=session.total_reviews,
        created_at=session.created_at
    )


@router.post("/sessions/{session_id}/toggle-star/{word_id}")
@safe_transaction("切换单词五角星状态")
async def toggle_word_star(
    session_id: str,
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换单词的五角星标记状态"""
    session = db.query(AntiForgetSession).filter(
        AntiForgetSession.id == session_id,
        AntiForgetSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 在words JSON中找到对应的单词并切换is_starred
    words = session.words
    updated = False
    new_state = False

    for word in words:
        if word.get('id') == word_id:
            word['is_starred'] = not word.get('is_starred', False)
            new_state = word['is_starred']
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="单词不存在")

    # 更新数据库 - 使用flag_modified告诉SQLAlchemy JSON字段已修改
    session.words = words
    flag_modified(session, 'words')  # 关键：标记JSON字段已修改
    db.commit()

    logger.info(f"切换五角星: 会话={session_id}, 单词ID={word_id}, 新状态={new_state}")

    return {"is_starred": new_state}


@router.post("/sessions/{session_id}/complete-review")
@safe_transaction("完成一次复习")
async def complete_review(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成一次抗遗忘复习"""
    session = db.query(AntiForgetSession).filter(
        AntiForgetSession.id == session_id,
        AntiForgetSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 增加复习计数
    session.review_count += 1
    db.commit()

    is_completed = session.review_count >= session.total_reviews

    logger.info(f"完成复习: 会话={session_id}, 当前次数={session.review_count}/{session.total_reviews}, 已完成={is_completed}")

    return {
        "current_count": session.review_count,
        "total_count": session.total_reviews,
        "is_completed": is_completed
    }


@router.get("/sessions/{session_id}/stats")
async def get_review_stats(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取复习统计数据"""
    session = db.query(AntiForgetSession).filter(
        AntiForgetSession.id == session_id,
        AntiForgetSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 统计五角星单词数量
    starred_count = sum(1 for word in session.words if word.get('is_starred', False))

    return {
        "current_review": session.review_count,
        "total_reviews": session.total_reviews,
        "starred_words": starred_count,
        "total_words": len(session.words),
        "progress": int((session.review_count / session.total_reviews) * 100)
    }


@router.delete("/sessions/{session_id}")
@safe_transaction("删除抗遗忘会话")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除抗遗忘会话（完成所有复习后）"""
    session = db.query(AntiForgetSession).filter(
        AntiForgetSession.id == session_id,
        AntiForgetSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    db.delete(session)
    db.commit()

    logger.info(f"删除抗遗忘会话: ID={session_id}")

    return {"success": True}
