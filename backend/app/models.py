from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    student_words = relationship("StudentWord", back_populates="student")
    learning_sessions = relationship("LearningSession", back_populates="student")

class Word(Base):
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True, index=True)
    english = Column(String(255), nullable=False, index=True)
    chinese = Column(Text, nullable=False)
    word_set = Column(String(100))  # 单词集合名称
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    student_words = relationship("StudentWord", back_populates="word")

class StudentWord(Base):
    __tablename__ = "student_words"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    grid_position = Column(Integer, default=0)  # 0-8 九宫格位置
    last_reviewed_at = Column(DateTime)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    student = relationship("Student", back_populates="student_words")
    word = relationship("Word", back_populates="student_words")
    learning_records = relationship("LearningRecord", back_populates="student_word")
    
    # 唯一约束：每个学生的每个单词只能有一条记录
    __table_args__ = (UniqueConstraint('student_id', 'word_id', name='unique_student_word'),)

class LearningSession(Base):
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_date = Column(Date, default=date.today)
    words_count = Column(Integer, nullable=False)  # 本次学习单词总数
    current_stage = Column(String(20), default="stage1")  # stage1, stage2, stage3
    current_group = Column(Integer, default=1)  # 当前学习的组数
    total_groups = Column(Integer)  # 总组数
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    student = relationship("Student", back_populates="learning_sessions")
    learning_records = relationship("LearningRecord", back_populates="session")

class LearningRecord(Base):
    __tablename__ = "learning_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=False)
    student_word_id = Column(Integer, ForeignKey("student_words.id"), nullable=False)
    stage = Column(String(20), nullable=False)  # stage1, stage2, stage3
    action_type = Column(String(20))  # 'learn', 'review', 'test'
    result = Column(String(20))  # 'completed', 'green', 'red', 'pending'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("LearningSession", back_populates="learning_records")
    student_word = relationship("StudentWord", back_populates="learning_records")

# 用于Excel导入的临时表
class WordImport(Base):
    __tablename__ = "word_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    english = Column(String(255), nullable=False)
    chinese = Column(Text, nullable=False)
    word_set = Column(String(100))
    imported_by = Column(String(100))  # 导入者
    import_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)  # 是否已处理到words表