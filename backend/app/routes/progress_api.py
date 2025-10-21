"""学习进度API - 简化版"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import LearningProgress, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction

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
@safe_transaction("保存学习进度")
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


@router.get("/student/{student_id}/word/{word_set_name}/{word_index}")
async def get_word_progress(
    student_id: int,
    word_set_name: str,
    word_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个单词的学习进度"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 查找进度
    progress = db.query(LearningProgress).filter(
        LearningProgress.student_id == student_id,
        LearningProgress.word_set_name == word_set_name,
        LearningProgress.word_index == word_index
    ).first()

    if not progress:
        # 如果没有进度记录，返回默认值（阶段0）
        return {
            "current_stage": 0,
            "total_groups": 0,
            "tasks_completed": {}
        }

    return {
        "current_stage": progress.current_stage,
        "total_groups": progress.total_groups,
        "tasks_completed": progress.tasks_completed
    }


@router.get("/student/{student_id}/word-set/{word_set_name}/grid-stats")
async def get_grid_stats(
    student_id: int,
    word_set_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取九宫格统计数据（按学习阶段分组）"""
    from app.models import WordSet, Word

    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 获取该单词集的单词总数
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        # 如果单词集不存在，返回空统计
        return {
            "grid_0": 0, "grid_1": 0, "grid_2": 0, "grid_3": 0, "grid_4": 0,
            "grid_5": 0, "grid_6": 0, "grid_7": 0, "grid_8": 0
        }

    total_words = db.query(Word).filter(Word.word_set_id == word_set.id).count()

    # 获取该单词集的所有进度
    progress_list = db.query(LearningProgress).filter(
        LearningProgress.student_id == student_id,
        LearningProgress.word_set_name == word_set_name
    ).all()

    # 统计每个阶段的单词数量
    grid_stats = {
        "grid_0": 0, "grid_1": 0, "grid_2": 0, "grid_3": 0, "grid_4": 0,
        "grid_5": 0, "grid_6": 0, "grid_7": 0, "grid_8": 0
    }

    # 先统计已有进度的单词
    for progress in progress_list:
        stage = progress.current_stage
        if 0 <= stage <= 8:
            grid_stats[f"grid_{stage}"] += 1

    # 计算未学习的单词数量 = 总数 - 已有进度的单词数
    learned_words_count = len(progress_list)
    unlearned_count = total_words - learned_words_count

    # 将未学习的单词加到grid_0
    grid_stats["grid_0"] += unlearned_count

    logger.info(f"九宫格统计: 学生={student.name}, 单词集={word_set_name}, 总单词数={total_words}, 已学={learned_words_count}, 统计={grid_stats}")

    return grid_stats


class BatchProgressUpdate(BaseModel):
    updates: List[ProgressCreate]


@router.post("/batch-update")
@safe_transaction("批量更新学习进度")
async def batch_update_progress(
    batch_data: BatchProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新学习进度（训后检测使用）"""
    updated_count = 0
    created_count = 0

    for progress_data in batch_data.updates:
        # 验证学生归属
        student = db.query(Student).filter(
            Student.id == progress_data.student_id,
            Student.teacher_id == current_user.id
        ).first()
        if not student:
            continue  # 跳过不属于当前教师的学生

        # 查找现有进度
        progress = db.query(LearningProgress).filter(
            LearningProgress.student_id == progress_data.student_id,
            LearningProgress.word_set_name == progress_data.word_set_name,
            LearningProgress.word_index == progress_data.word_index
        ).first()

        if progress:
            # 更新
            progress.current_stage = progress_data.current_stage
            progress.total_groups = progress_data.total_groups
            progress.tasks_completed = progress_data.tasks_completed
            updated_count += 1
        else:
            # 创建
            progress = LearningProgress(**progress_data.dict())
            db.add(progress)
            created_count += 1

    db.commit()

    logger.info(f"批量更新学习进度完成: 创建={created_count}, 更新={updated_count}, 总数={len(batch_data.updates)}")

    return {
        "success": True,
        "created": created_count,
        "updated": updated_count,
        "total": len(batch_data.updates)
    }


class CompleteTaskRequest(BaseModel):
    student_id: int
    word_set_name: str
    group_number: int
    task_number: int


@router.post("/complete-task")
@safe_transaction("标记任务完成")
async def complete_task(
    task_data: CompleteTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记某个任务完成（用于阶段切换）"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == task_data.student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 这个API可能需要更复杂的逻辑
    # 目前简单返回成功，具体逻辑由前端控制
    logger.info(f"标记任务完成: 学生={student.name}, 单词集={task_data.word_set_name}, 组={task_data.group_number}, 任务={task_data.task_number}")

    return {"success": True}
