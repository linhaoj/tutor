from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from datetime import datetime, date

from app.database import get_db
from app.models import Student, StudentWord, LearningSession

router = APIRouter()

# Pydantic模型
class StudentCreate(BaseModel):
    name: str
    email: str = None

class StudentResponse(BaseModel):
    id: int
    name: str
    email: str = None
    created_at: datetime
    total_words: int = 0
    learned_words: int = 0
    
    class Config:
        from_attributes = True

class StudentStats(BaseModel):
    student_id: int
    student_name: str
    grid_stats: dict  # {0: 10, 1: 5, 2: 3, ...} 每个格子的单词数量
    last_session_date: date = None
    total_sessions: int = 0

@router.post("/", response_model=StudentResponse)
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """创建新学生"""
    # 检查邮箱是否已存在
    if student.email:
        existing = db.query(Student).filter(Student.email == student.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已存在")
    
    db_student = Student(name=student.name, email=student.email)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    # 计算统计信息
    total_words = db.query(StudentWord).filter(StudentWord.student_id == db_student.id).count()
    learned_words = db.query(StudentWord).filter(
        StudentWord.student_id == db_student.id,
        StudentWord.grid_position > 0
    ).count()
    
    response = StudentResponse(
        id=db_student.id,
        name=db_student.name,
        email=db_student.email,
        created_at=db_student.created_at,
        total_words=total_words,
        learned_words=learned_words
    )
    
    return response

@router.get("/", response_model=List[StudentResponse])
async def get_students(db: Session = Depends(get_db)):
    """获取所有学生列表"""
    students = db.query(Student).all()
    result = []
    
    for student in students:
        total_words = db.query(StudentWord).filter(StudentWord.student_id == student.id).count()
        learned_words = db.query(StudentWord).filter(
            StudentWord.student_id == student.id,
            StudentWord.grid_position > 0
        ).count()
        
        result.append(StudentResponse(
            id=student.id,
            name=student.name,
            email=student.email,
            created_at=student.created_at,
            total_words=total_words,
            learned_words=learned_words
        ))
    
    return result

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: Session = Depends(get_db)):
    """获取单个学生信息"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    total_words = db.query(StudentWord).filter(StudentWord.student_id == student_id).count()
    learned_words = db.query(StudentWord).filter(
        StudentWord.student_id == student_id,
        StudentWord.grid_position > 0
    ).count()
    
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        created_at=student.created_at,
        total_words=total_words,
        learned_words=learned_words
    )

@router.get("/{student_id}/stats", response_model=StudentStats)
async def get_student_stats(student_id: int, db: Session = Depends(get_db)):
    """获取学生的详细统计信息（九宫格分布）"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 查询九宫格统计
    grid_query = db.query(
        StudentWord.grid_position,
        func.count(StudentWord.id).label('count')
    ).filter(
        StudentWord.student_id == student_id
    ).group_by(StudentWord.grid_position).all()
    
    # 转换为字典格式
    grid_stats = {}
    for position, count in grid_query:
        grid_stats[position] = count
    
    # 确保所有格子都有数据（0-8）
    for i in range(9):
        if i not in grid_stats:
            grid_stats[i] = 0
    
    # 获取最后学习日期和总学习次数
    last_session = db.query(LearningSession).filter(
        LearningSession.student_id == student_id
    ).order_by(LearningSession.created_at.desc()).first()
    
    total_sessions = db.query(LearningSession).filter(
        LearningSession.student_id == student_id
    ).count()
    
    return StudentStats(
        student_id=student_id,
        student_name=student.name,
        grid_stats=grid_stats,
        last_session_date=last_session.session_date if last_session else None,
        total_sessions=total_sessions
    )

@router.delete("/{student_id}")
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    """删除学生"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    db.delete(student)
    db.commit()
    
    return {"message": f"学生 {student.name} 已删除"}

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    """更新学生信息"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 检查邮箱是否被其他学生使用
    if student.email and student.email != db_student.email:
        existing = db.query(Student).filter(
            Student.email == student.email,
            Student.id != student_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被其他学生使用")
    
    db_student.name = student.name
    db_student.email = student.email
    db_student.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_student)
    
    # 返回更新后的信息
    total_words = db.query(StudentWord).filter(StudentWord.student_id == student_id).count()
    learned_words = db.query(StudentWord).filter(
        StudentWord.student_id == student_id,
        StudentWord.grid_position > 0
    ).count()
    
    return StudentResponse(
        id=db_student.id,
        name=db_student.name,
        email=db_student.email,
        created_at=db_student.created_at,
        total_words=total_words,
        learned_words=learned_words
    )