"""课程安排API - 简化版"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models import Schedule, Student, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/schedules", tags=["课程安排"])


class ScheduleCreate(BaseModel):
    student_id: int
    date: str
    time: str
    word_set_name: str
    course_type: str = "learning"
    duration: int = 60
    class_type: str = "big"


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
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建课程安排"""
    student = db.query(Student).filter(
        Student.id == schedule_data.student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    schedule = Schedule(
        teacher_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有课程"""
    schedules = db.query(Schedule).filter(Schedule.teacher_id == current_user.id).all()
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
        raise HTTPException(status_code=404, detail="课程不存在")

    schedule.completed = True
    db.commit()
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
