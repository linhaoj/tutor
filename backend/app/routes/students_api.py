"""学生管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction, validate_business_rule

logger = get_logger("students")

router = APIRouter(prefix="/api/students", tags=["学生管理"])


class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    remaining_hours: float = 0
    teacher_id: Optional[str] = None  # 管理员可以指定教师ID


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
@safe_transaction("创建学生")
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建学生

    - 教师：为自己创建学生
    - 管理员：可以通过teacher_id参数为指定教师创建学生
    """
    # 确定teacher_id
    if student_data.teacher_id:
        # 管理员为指定教师创建学生
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="只有管理员可以为其他教师创建学生")

        # 验证教师存在
        teacher = db.query(User).filter(User.id == student_data.teacher_id).first()
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=404, detail="指定的教师不存在")

        teacher_id = student_data.teacher_id
        logger.info(f"管理员 {current_user.username} 为教师 {teacher.username} 创建学生: {student_data.name}")
    else:
        # 教师为自己创建学生
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(status_code=403, detail="权限不足")
        teacher_id = current_user.id
        logger.info(f"教师 {current_user.username} 创建学生: {student_data.name}")

    # 检查邮箱是否已存在
    if student_data.email:
        existing = db.query(Student).filter(Student.email == student_data.email).first()
        if existing:
            logger.warning(f"创建学生失败: 邮箱已被使用 - {student_data.email}")
            raise HTTPException(status_code=400, detail="邮箱已被使用")

    # 验证课时数有效性
    validate_business_rule(
        student_data.remaining_hours >= 0,
        f"课时数不能为负数: {student_data.remaining_hours}"
    )

    student = Student(
        teacher_id=teacher_id,
        name=student_data.name,
        email=student_data.email,
        remaining_hours=student_data.remaining_hours
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    logger.info(f"学生创建成功: 教师ID={teacher_id}, 学生={student.name}, ID={student.id}, 课时={student.remaining_hours}h")

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
@safe_transaction("更新学生信息")
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
        # 验证课时数有效性
        validate_business_rule(
            student_update.remaining_hours >= 0,
            f"课时数不能为负数: {student_update.remaining_hours}"
        )
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
@safe_transaction("扣减学生课时")
async def deduct_student_hours(
    student_id: int,
    hours: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    扣减学生课时 - 核心业务操作

    事务安全保证:
    1. 扣减失败自动回滚
    2. 课时不会变成负数
    3. 并发操作安全
    """
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()

    if not student:
        logger.warning(f"扣减课时失败: 学生不存在 - ID={student_id}, 教师={current_user.username}")
        raise HTTPException(status_code=404, detail="学生不存在")

    # 业务规则验证：课时数有效性
    validate_business_rule(
        hours > 0,
        f"扣减课时必须大于0: {hours}h"
    )

    validate_business_rule(
        hours <= 10,
        f"单次扣减课时不能超过10小时: {hours}h (防止误操作)"
    )

    # 业务规则验证：余额充足
    validate_business_rule(
        student.remaining_hours >= hours,
        f"剩余课时不足: 当前{student.remaining_hours}h，需要{hours}h"
    )

    # 执行扣减（记录原值用于日志）
    old_hours = student.remaining_hours
    student.remaining_hours -= hours
    student.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(student)

    logger.info(f"课时扣减成功: 学生={student.name}, 扣减={hours}h, {old_hours}h → {student.remaining_hours}h, 操作人={current_user.username}")

    return {
        "message": "课时扣减成功",
        "remaining_hours": student.remaining_hours,
        "deducted_hours": hours,
        "previous_hours": old_hours
    }
