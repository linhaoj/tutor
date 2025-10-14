"""学生管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Student, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/students", tags=["学生管理"])


class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    remaining_hours: float = 0


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    remaining_hours: Optional[float] = None


class StudentResponse(BaseModel):
    id: int
    teacher_id: str
    name: str
    email: Optional[str]
    remaining_hours: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建学生"""
    # 检查邮箱是否已存在
    if student_data.email:
        existing = db.query(Student).filter(Student.email == student_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")

    student = Student(
        teacher_id=current_user.id,
        name=student_data.name,
        email=student_data.email,
        remaining_hours=student_data.remaining_hours
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentResponse(
        id=student.id,
        teacher_id=student.teacher_id,
        name=student.name,
        email=student.email,
        remaining_hours=student.remaining_hours,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat()
    )


@router.get("", response_model=List[StudentResponse])
async def get_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有学生"""
    students = db.query(Student).filter(Student.teacher_id == current_user.id).all()

    return [
        StudentResponse(
            id=s.id,
            teacher_id=s.teacher_id,
            name=s.name,
            email=s.email,
            remaining_hours=s.remaining_hours,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat()
        )
        for s in students
    ]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个学生信息"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    return StudentResponse(
        id=student.id,
        teacher_id=student.teacher_id,
        name=student.name,
        email=student.email,
        remaining_hours=student.remaining_hours,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat()
    )


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新学生信息"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 更新字段
    if student_update.name is not None:
        student.name = student_update.name
    if student_update.email is not None:
        # 检查邮箱是否被其他学生使用
        if student_update.email:
            existing = db.query(Student).filter(
                Student.email == student_update.email,
                Student.id != student_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
        student.email = student_update.email
    if student_update.remaining_hours is not None:
        student.remaining_hours = student_update.remaining_hours

    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)

    return StudentResponse(
        id=student.id,
        teacher_id=student.teacher_id,
        name=student.name,
        email=student.email,
        remaining_hours=student.remaining_hours,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat()
    )


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除学生"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    db.delete(student)
    db.commit()

    return {"message": "学生删除成功"}


@router.post("/{student_id}/deduct-hours")
async def deduct_student_hours(
    student_id: int,
    hours: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """扣减学生课时"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    if student.remaining_hours < hours:
        raise HTTPException(status_code=400, detail="剩余课时不足")

    student.remaining_hours -= hours
    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)

    return {
        "message": "课时扣减成功",
        "remaining_hours": student.remaining_hours
    }
