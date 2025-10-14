"""学习进度API - 简化版"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import LearningProgress, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger

logger = get_logger("progress")

router = APIRouter(prefix="/api/progress", tags=["学习进度"])


class ProgressCreate(BaseModel):
    student_id: int
    word_set_name: str
    word_index: int
    current_stage: int
    total_groups: int
    tasks_completed: dict


class ProgressResponse(BaseModel):
    id: int
    student_id: int
    word_set_name: str
    word_index: int
    current_stage: int
    total_groups: int
    tasks_completed: dict


@router.post("", response_model=ProgressResponse)
async def create_or_update_progress(
    progress_data: ProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建或更新学习进度"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == progress_data.student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        logger.warning(f"保存进度失败: 学生不存在 - ID={progress_data.student_id}, 教师={current_user.username}")
        raise HTTPException(status_code=404, detail="学生不存在")

    # 查找现有进度
    progress = db.query(LearningProgress).filter(
        LearningProgress.student_id == progress_data.student_id,
        LearningProgress.word_set_name == progress_data.word_set_name,
        LearningProgress.word_index == progress_data.word_index
    ).first()

    action = "更新" if progress else "创建"

    if progress:
        # 更新
        progress.current_stage = progress_data.current_stage
        progress.total_groups = progress_data.total_groups
        progress.tasks_completed = progress_data.tasks_completed
    else:
        # 创建
        progress = LearningProgress(**progress_data.dict())
        db.add(progress)

    db.commit()
    db.refresh(progress)

    logger.info(f"学习进度{action}成功: 学生={student.name}, 单词集={progress_data.word_set_name}, 单词索引={progress_data.word_index}, 阶段={progress_data.current_stage}/{progress_data.total_groups}")

    return ProgressResponse(
        id=progress.id,
        student_id=progress.student_id,
        word_set_name=progress.word_set_name,
        word_index=progress.word_index,
        current_stage=progress.current_stage,
        total_groups=progress.total_groups,
        tasks_completed=progress.tasks_completed
    )


@router.get("/student/{student_id}", response_model=List[ProgressResponse])
async def get_student_progress(
    student_id: int,
    word_set_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的学习进度"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    query = db.query(LearningProgress).filter(LearningProgress.student_id == student_id)
    if word_set_name:
        query = query.filter(LearningProgress.word_set_name == word_set_name)

    progress_list = query.all()

    return [
        ProgressResponse(
            id=p.id,
            student_id=p.student_id,
            word_set_name=p.word_set_name,
            word_index=p.word_index,
            current_stage=p.current_stage,
            total_groups=p.total_groups,
            tasks_completed=p.tasks_completed
        )
        for p in progress_list
    ]
