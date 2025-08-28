from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from pydantic import BaseModel
from datetime import datetime
import random

from app.database import get_db
from app.models import Student, Word, StudentWord, LearningSession, LearningRecord

router = APIRouter()

# Pydantic模型
class WordCard(BaseModel):
    id: int
    english: str
    chinese: str
    student_word_id: int
    current_stage: str
    
class LearningSessionCreate(BaseModel):
    student_id: int
    words_count: int
    
class LearningSessionResponse(BaseModel):
    id: int
    student_id: int
    words_count: int
    current_stage: str
    current_group: int
    total_groups: int
    completed: bool
    word_cards: List[WordCard]
    
class StageResult(BaseModel):
    session_id: int
    results: List[dict]  # [{"student_word_id": 1, "result": "green"}, ...]
    
class GridStats(BaseModel):
    grid_0: int = 0  # 未学
    grid_1: int = 0  # 第1格
    grid_2: int = 0  # 第2格
    grid_3: int = 0  # 第3格
    grid_4: int = 0  # 第4格
    grid_5: int = 0  # 第5格
    grid_6: int = 0  # 第6格
    grid_7: int = 0  # 第7格
    grid_8: int = 0  # 已掌握

@router.post("/start", response_model=LearningSessionResponse)
async def start_learning_session(session_data: LearningSessionCreate, db: Session = Depends(get_db)):
    """开始学习会话"""
    # 验证学生是否存在
    student = db.query(Student).filter(Student.id == session_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 获取可学习的单词（格子0-7）
    available_words = db.query(StudentWord).join(Word).filter(
        and_(
            StudentWord.student_id == session_data.student_id,
            StudentWord.grid_position < 8  # 不包括已掌握的单词
        )
    ).all()
    
    if len(available_words) < session_data.words_count:
        raise HTTPException(
            status_code=400, 
            detail=f"可学习单词不足，当前只有{len(available_words)}个单词"
        )
    
    # 随机选择单词
    selected_words = random.sample(available_words, session_data.words_count)
    
    # 计算总组数（每组5个单词）
    total_groups = (session_data.words_count + 4) // 5
    
    # 创建学习会话
    session = LearningSession(
        student_id=session_data.student_id,
        words_count=session_data.words_count,
        current_stage="stage1",
        current_group=1,
        total_groups=total_groups,
        completed=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 获取第一组单词（前5个）
    first_group_words = selected_words[:5]
    word_cards = []
    
    for sw in first_group_words:
        word_cards.append(WordCard(
            id=sw.word.id,
            english=sw.word.english,
            chinese=sw.word.chinese,
            student_word_id=sw.id,
            current_stage="stage1"
        ))
        
        # 创建学习记录
        record = LearningRecord(
            session_id=session.id,
            student_word_id=sw.id,
            stage="stage1",
            action_type="learn",
            result="pending"
        )
        db.add(record)
    
    db.commit()
    
    return LearningSessionResponse(
        id=session.id,
        student_id=session.student_id,
        words_count=session.words_count,
        current_stage=session.current_stage,
        current_group=session.current_group,
        total_groups=session.total_groups,
        completed=session.completed,
        word_cards=word_cards
    )

@router.post("/stage1/complete", response_model=dict)
async def complete_stage1(result: StageResult, db: Session = Depends(get_db)):
    """完成第一阶段（初学）"""
    session = db.query(LearningSession).filter(LearningSession.id == result.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="学习会话不存在")
    
    # 更新学习记录
    for word_result in result.results:
        record = db.query(LearningRecord).filter(
            and_(
                LearningRecord.session_id == result.session_id,
                LearningRecord.student_word_id == word_result["student_word_id"],
                LearningRecord.stage == "stage1"
            )
        ).first()
        
        if record:
            record.result = "completed"  # 第一阶段都标记为完成
    
    # 更新会话状态到第二阶段
    session.current_stage = "stage2"
    db.commit()
    
    return {"message": "第一阶段完成，进入第二阶段"}

@router.get("/stage2/{session_id}", response_model=LearningSessionResponse)
async def get_stage2_words(session_id: int, db: Session = Depends(get_db)):
    """获取第二阶段的单词"""
    session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="学习会话不存在")
    
    # 获取当前组的单词
    start_idx = (session.current_group - 1) * 5
    end_idx = min(start_idx + 5, session.words_count)
    
    # 获取当前组的学习记录
    records = db.query(LearningRecord).join(StudentWord).join(Word).filter(
        and_(
            LearningRecord.session_id == session_id,
            LearningRecord.stage == "stage1"
        )
    ).all()
    
    # 取当前组的单词
    current_group_records = records[start_idx:end_idx]
    word_cards = []
    
    for record in current_group_records:
        word_cards.append(WordCard(
            id=record.student_word.word.id,
            english=record.student_word.word.english,
            chinese=record.student_word.word.chinese,
            student_word_id=record.student_word_id,
            current_stage="stage2"
        ))
    
    return LearningSessionResponse(
        id=session.id,
        student_id=session.student_id,
        words_count=session.words_count,
        current_stage=session.current_stage,
        current_group=session.current_group,
        total_groups=session.total_groups,
        completed=session.completed,
        word_cards=word_cards
    )

@router.post("/stage2/complete", response_model=dict)
async def complete_stage2(result: StageResult, db: Session = Depends(get_db)):
    """完成第二阶段（巩固）"""
    session = db.query(LearningSession).filter(LearningSession.id == result.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="学习会话不存在")
    
    # 检查是否所有单词都是绿色
    all_green = all(word_result["result"] == "green" for word_result in result.results)
    
    if not all_green:
        return {"message": "还有单词未达到绿色标准，请继续练习", "all_green": False}
    
    # 创建第二阶段的学习记录
    for word_result in result.results:
        record = LearningRecord(
            session_id=result.session_id,
            student_word_id=word_result["student_word_id"],
            stage="stage2",
            action_type="review",
            result=word_result["result"]
        )
        db.add(record)
    
    # 检查是否需要进入第三阶段
    if session.current_group == session.total_groups:
        # 所有组都完成了，进入第三阶段
        session.current_stage = "stage3"
    else:
        # 还有其他组，继续第一阶段
        session.current_group += 1
        session.current_stage = "stage1"
    
    db.commit()
    
    return {
        "message": "第二阶段完成",
        "all_green": True,
        "next_stage": session.current_stage,
        "current_group": session.current_group
    }

@router.get("/stage3/{session_id}", response_model=LearningSessionResponse)
async def get_stage3_words(session_id: int, db: Session = Depends(get_db)):
    """获取第三阶段的单词（训后检测）"""
    session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="学习会话不存在")
    
    # 获取所有已学过的单词（第1到当前组的所有单词）
    all_records = db.query(LearningRecord).join(StudentWord).join(Word).filter(
        and_(
            LearningRecord.session_id == session_id,
            LearningRecord.stage == "stage2",
            LearningRecord.result == "green"
        )
    ).all()
    
    # 随机打乱顺序
    random.shuffle(all_records)
    
    word_cards = []
    for record in all_records:
        word_cards.append(WordCard(
            id=record.student_word.word.id,
            english=record.student_word.word.english,
            chinese=record.student_word.word.chinese,
            student_word_id=record.student_word_id,
            current_stage="stage3"
        ))
    
    return LearningSessionResponse(
        id=session.id,
        student_id=session.student_id,
        words_count=session.words_count,
        current_stage=session.current_stage,
        current_group=session.current_group,
        total_groups=session.total_groups,
        completed=session.completed,
        word_cards=word_cards
    )

@router.post("/stage3/complete", response_model=dict)
async def complete_stage3(result: StageResult, db: Session = Depends(get_db)):
    """完成第三阶段（最终检测）"""
    session = db.query(LearningSession).filter(LearningSession.id == result.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="学习会话不存在")
    
    # 处理最终结果并更新单词格子位置
    for word_result in result.results:
        # 创建第三阶段记录
        record = LearningRecord(
            session_id=result.session_id,
            student_word_id=word_result["student_word_id"],
            stage="stage3",
            action_type="test",
            result=word_result["result"]
        )
        db.add(record)
        
        # 更新单词格子位置
        student_word = db.query(StudentWord).filter(
            StudentWord.id == word_result["student_word_id"]
        ).first()
        
        if student_word:
            if word_result["result"] == "green":
                # 绿色：格子晋级
                student_word.grid_position = min(student_word.grid_position + 1, 8)
                student_word.last_reviewed_at = datetime.utcnow()
                student_word.review_count += 1
            else:
                # 红色：回到格子1（如果原来在格子0则保持0）
                if student_word.grid_position > 0:
                    student_word.grid_position = 1
                student_word.last_reviewed_at = datetime.utcnow()
    
    # 标记会话完成
    session.completed = True
    db.commit()
    
    return {"message": "学习会话完成！单词格子位置已更新"}

@router.get("/grid/{student_id}", response_model=GridStats)
async def get_grid_stats(student_id: int, db: Session = Depends(get_db)):
    """获取学生的九宫格统计"""
    # 查询每个格子的单词数量
    grid_query = db.query(
        StudentWord.grid_position,
        func.count(StudentWord.id).label('count')
    ).filter(
        StudentWord.student_id == student_id
    ).group_by(StudentWord.grid_position).all()
    
    # 初始化统计结果
    stats = GridStats()
    
    # 填充统计数据
    for position, count in grid_query:
        setattr(stats, f'grid_{position}', count)
    
    return stats

@router.get("/sessions/{student_id}")
async def get_student_sessions(student_id: int, db: Session = Depends(get_db)):
    """获取学生的学习历史"""
    sessions = db.query(LearningSession).filter(
        LearningSession.student_id == student_id
    ).order_by(LearningSession.created_at.desc()).all()
    
    return sessions