"""课程安排API - 简化版（支持时区）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date

from app.database import get_db
from app.models import Schedule, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction

logger = get_logger("schedule")

router = APIRouter(prefix="/api/schedules", tags=["课程安排"])


class ScheduleCreate(BaseModel):
    student_id: int
    # 新字段：ISO 8601格式的datetime字符串（前端会发送UTC时间）
    scheduled_at: Optional[str] = None  # 例如："2025-10-21T15:00:00Z"
    # 旧字段：向后兼容
    date: Optional[str] = None
    time: Optional[str] = None
    word_set_name: str
    course_type: str = "learning"
    duration: int = 60
    class_type: str = "big"
    teacher_id: Optional[str] = None  # 管理员可以指定教师ID


class ScheduleResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    # 新字段：ISO 8601格式的datetime字符串（返回UTC时间）
    scheduled_at: str  # 例如："2025-10-21T15:00:00Z"
    # 旧字段：向后兼容（前端暂时还需要）
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

    # 解析时间：优先使用新的 scheduled_at 字段
    if schedule_data.scheduled_at:
        # 前端发送UTC时间的ISO 8601字符串
        scheduled_at = datetime.fromisoformat(schedule_data.scheduled_at.replace('Z', '+00:00'))
        # 同时填充旧字段以保持向后兼容
        schedule_date = scheduled_at.date()
        schedule_time = scheduled_at.strftime('%H:%M')
    elif schedule_data.date and schedule_data.time:
        # 向后兼容：使用旧字段
        schedule_date = date.fromisoformat(schedule_data.date)
        schedule_time = schedule_data.time
        # 组合为datetime（假设是北京时间，转为UTC）
        from datetime import timedelta
        local_dt = datetime.combine(schedule_date, datetime.strptime(schedule_time, '%H:%M').time())
        scheduled_at = local_dt - timedelta(hours=8)  # 北京时间转UTC
    else:
        raise HTTPException(status_code=400, detail="必须提供scheduled_at或date+time")

    schedule = Schedule(
        teacher_id=teacher_id,
        student_id=schedule_data.student_id,
        student_name=student.name,
        scheduled_at=scheduled_at,  # 新字段：UTC时间
        date=schedule_date,  # 旧字段：向后兼容
        time=schedule_time,  # 旧字段：向后兼容
        word_set_name=schedule_data.word_set_name,
        course_type=schedule_data.course_type,
        duration=schedule_data.duration,
        class_type=schedule_data.class_type,
        completed=False
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    logger.info(f"课程创建成功: 教师ID={teacher_id}, 学生={student.name}, 时间={scheduled_at.isoformat()}Z (UTC), 类型={schedule_data.course_type}, 时长={schedule_data.duration}分钟")

    return ScheduleResponse(
        id=schedule.id,
        student_id=schedule.student_id,
        student_name=schedule.student_name,
        scheduled_at=schedule.scheduled_at.isoformat() + 'Z',  # 新字段：返回UTC时间
        date=schedule.date.isoformat(),  # 旧字段：向后兼容
        time=schedule.time,  # 旧字段：向后兼容
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
            scheduled_at=s.scheduled_at.isoformat() + 'Z',  # UTC时间
            date=s.date.isoformat() if s.date else '',  # 向后兼容
            time=s.time if s.time else '',  # 向后兼容
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
    """标记课程为已完成

    - 教师：可以标记自己创建的课程
    - 管理员：可以标记任意课程
    """
    # 管理员可以完成任意课程，教师只能完成自己创建的课程
    if current_user.role == "admin":
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    else:
        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.teacher_id == current_user.id
        ).first()

    if not schedule:
        logger.warning(f"完成课程失败: 课程不存在或无权限 - ID={schedule_id}, 用户={current_user.username}")
        raise HTTPException(status_code=404, detail="课程不存在或无权限")

    schedule.completed = True
    db.commit()

    logger.info(f"课程标记完成: 学生={schedule.student_name}, 日期={schedule.date}, 类型={schedule.course_type}, 操作人={current_user.username}")
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
