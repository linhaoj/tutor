"""学生复习记录API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List
from pydantic import BaseModel
from datetime import datetime, date

from app.database import get_db
from app.models import StudentReview, Student, User
from app.routes.auth import get_current_user
from app.logger import get_logger
from app.database_safety import safe_transaction

logger = get_logger("student_reviews")

router = APIRouter(prefix="/api/student-reviews", tags=["学生复习"])


class ReviewWord(BaseModel):
    id: int
    english: str
    chinese: str
    is_starred: bool = False


class ReviewCreate(BaseModel):
    student_id: int
    word_set_name: str
    learn_date: str  # YYYY-MM-DD
    words: List[dict]


class ReviewResponse(BaseModel):
    id: str
    student_id: int
    word_set_name: str
    learn_date: str
    words: List[dict]
    created_at: datetime


@router.post("/", response_model=ReviewResponse)
@safe_transaction("创建学生复习记录")
async def create_student_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建学生复习记录（训后检测完成时调用）"""
    # 验证学生归属
    student = db.query(Student).filter(
        Student.id == review_data.student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 生成唯一ID: review_{student_id}_{word_set_name}_{timestamp}
    timestamp = int(datetime.now().timestamp())
    review_id = f"review_{review_data.student_id}_{review_data.word_set_name}_{timestamp}"

    # 创建复习记录
    review = StudentReview(
        id=review_id,
        student_id=review_data.student_id,
        word_set_name=review_data.word_set_name,
        learn_date=datetime.strptime(review_data.learn_date, "%Y-%m-%d").date(),
        words=review_data.words
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    logger.info(f"创建学生复习记录: ID={review_id}, 学生={student.name}, 单词集={review_data.word_set_name}, 单词数={len(review_data.words)}")

    return ReviewResponse(
        id=review.id,
        student_id=review.student_id,
        word_set_name=review.word_set_name,
        learn_date=review.learn_date.isoformat(),
        words=review.words,
        created_at=review.created_at
    )


@router.get("/student/{student_id}", response_model=List[ReviewResponse])
async def get_student_reviews(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的所有复习记录"""
    # 学生端：验证是否是自己的记录
    if current_user.role == 'student':
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.user_id == current_user.id
        ).first()
        if not student:
            raise HTTPException(status_code=403, detail="无权访问")
    else:
        # 教师/管理员：验证学生归属
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.teacher_id == current_user.id
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")

    reviews = db.query(StudentReview).filter(
        StudentReview.student_id == student_id
    ).order_by(StudentReview.learn_date.desc()).all()

    return [
        ReviewResponse(
            id=r.id,
            student_id=r.student_id,
            word_set_name=r.word_set_name,
            learn_date=r.learn_date.isoformat(),
            words=r.words,
            created_at=r.created_at
        )
        for r in reviews
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定复习记录"""
    review = db.query(StudentReview).filter(
        StudentReview.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="复习记录不存在")

    # 权限验证
    student = db.query(Student).filter(Student.id == review.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    if current_user.role == 'student':
        if student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问")
    else:
        if student.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问")

    return ReviewResponse(
        id=review.id,
        student_id=review.student_id,
        word_set_name=review.word_set_name,
        learn_date=review.learn_date.isoformat(),
        words=review.words,
        created_at=review.created_at
    )


@router.post("/{review_id}/toggle-star/{word_id}")
@safe_transaction("切换单词星标")
async def toggle_word_star(
    review_id: str,
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换单词的星标状态"""
    review = db.query(StudentReview).filter(
        StudentReview.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="复习记录不存在")

    # 权限验证
    student = db.query(Student).filter(Student.id == review.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    if current_user.role == 'student':
        if student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问")
    else:
        if student.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问")

    # 在words JSON中找到对应的单词并切换is_starred
    words = review.words
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
    review.words = words
    flag_modified(review, 'words')
    db.commit()

    logger.info(f"切换星标: 复习={review_id}, 单词ID={word_id}, 新状态={new_state}")

    return {"is_starred": new_state}


@router.delete("/{review_id}")
@safe_transaction("删除复习记录")
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除复习记录"""
    review = db.query(StudentReview).filter(
        StudentReview.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="复习记录不存在")

    # 权限验证（只有教师/管理员可以删除）
    if current_user.role == 'student':
        raise HTTPException(status_code=403, detail="学生无权删除记录")

    student = db.query(Student).filter(Student.id == review.student_id).first()
    if not student or student.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问")

    db.delete(review)
    db.commit()

    logger.info(f"删除复习记录: ID={review_id}")

    return {"success": True}
