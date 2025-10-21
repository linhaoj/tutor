"""课程安排API - 简化版"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models import Schedule, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction

logger = get_logger("schedule")

router = APIRouter(prefix="/api/schedules", tags=["课程安排"])


class ScheduleCreate(BaseModel):
    student_id: int
    date: str
    time: str
    word_set_name: str
    course_type: str = "learning"
    duration: int = 60
    class_type: str = "big"
    teacher_id: Optional[str] = None  # 管理员可以指定教师ID


class ScheduleResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    date: str
    time: str
    word_set_name: str
    course_type: str
    duration: int
    class_type: str
    completed: bool


@router.post("", response_model=ScheduleResponse)
@safe_transaction("创建课程安排")
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建课程安排

    - 教师：为自己的学生创建课程
    - 管理员：可以通过teacher_id参数为指定教师的学生创建课程
    """
    # 确定teacher_id
    if schedule_data.teacher_id:
        # 管理员为指定教师创建课程
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="只有管理员可以为其他教师创建课程")

        # 验证教师存在
        teacher = db.query(User).filter(User.id == schedule_data.teacher_id).first()
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=404, detail="指定的教师不存在")

        teacher_id = schedule_data.teacher_id
        logger.info(f"管理员 {current_user.username} 为教师 {teacher.username} 创建课程")
    else:
        # 教师为自己创建课程
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(status_code=403, detail="权限不足")
        teacher_id = current_user.id

    # 验证学生存在且属于该教师
    student = db.query(Student).filter(
        Student.id == schedule_data.student_id,
        Student.teacher_id == teacher_id
    ).first()
    if not student:
        logger.warning(f"创建课程失败: 学生不存在或不属于该教师 - ID={schedule_data.student_id}, 教师ID={teacher_id}")
        raise HTTPException(status_code=404, detail="学生不存在或不属于该教师")

    schedule = Schedule(
        teacher_id=teacher_id,
        student_id=schedule_data.student_id,
        student_name=student.name,
        date=date.fromisoformat(schedule_data.date),
        time=schedule_data.time,
        word_set_name=schedule_data.word_set_name,
        course_type=schedule_data.course_type,
        duration=schedule_data.duration,
        class_type=schedule_data.class_type,
        completed=False
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    logger.info(f"课程创建成功: 教师ID={teacher_id}, 学生={student.name}, 日期={schedule_data.date}, 时间={schedule_data.time}, 类型={schedule_data.course_type}, 时长={schedule_data.duration}分钟")

    return ScheduleResponse(
        id=schedule.id,
        student_id=schedule.student_id,
        student_name=schedule.student_name,
        date=schedule.date.isoformat(),
        time=schedule.time,
        word_set_name=schedule.word_set_name,
        course_type=schedule.course_type,
        duration=schedule.duration,
        class_type=schedule.class_type,
        completed=schedule.completed
    )


@router.get("", response_model=List[ScheduleResponse])
async def get_schedules(
    teacher_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程列表

    - 教师：获取自己的课程
    - 管理员：可通过teacher_id参数获取指定教师的课程
    """
    # 确定查询的teacher_id
    if teacher_id:
        # 管理员查询指定教师的课程
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="只有管理员可以查询其他教师的课程")
        query_teacher_id = teacher_id
    else:
        # 查询当前用户的课程
        query_teacher_id = current_user.id

    schedules = db.query(Schedule).filter(Schedule.teacher_id == query_teacher_id).all()
    return [
        ScheduleResponse(
            id=s.id,
            student_id=s.student_id,
            student_name=s.student_name,
            date=s.date.isoformat(),
            time=s.time,
            word_set_name=s.word_set_name,
            course_type=s.course_type,
            duration=s.duration,
            class_type=s.class_type,
            completed=s.completed
        )
        for s in schedules
    ]


@router.put("/{schedule_id}/complete")
async def complete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记课程为已完成"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.teacher_id == current_user.id
    ).first()
    if not schedule:
        logger.warning(f"完成课程失败: 课程不存在 - ID={schedule_id}, 教师={current_user.username}")
        raise HTTPException(status_code=404, detail="课程不存在")

    schedule.completed = True
    db.commit()

    logger.info(f"课程标记完成: 学生={schedule.student_name}, 日期={schedule.date}, 类型={schedule.course_type}")
    return {"message": "课程已标记为完成"}


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除课程"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.teacher_id == current_user.id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="课程不存在")

    db.delete(schedule)
    db.commit()
    return {"message": "课程删除成功"}
