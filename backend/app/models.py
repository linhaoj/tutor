from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
import bcrypt

Base = declarative_base()

class User(Base):
    """用户表 - 所有登录用户（管理员、教师、学生）"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)  # 例如: admin-001, user-1234567890
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt哈希
    role = Column(String(20), nullable=False)  # 'admin', 'teacher', 'student'
    display_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    # 关系
    managed_students = relationship("Student", back_populates="teacher", foreign_keys="Student.teacher_id")
    student_profile = relationship("Student", back_populates="user", foreign_keys="Student.user_id", uselist=False)
    word_sets = relationship("WordSet", back_populates="owner")
    schedules = relationship("Schedule", back_populates="teacher")

    def set_password(self, password: str):
        """设置密码（自动哈希）"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Student(Base):
    """学生表 - 学生的教学数据"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, unique=True)  # 关联的用户账号
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)  # 所属教师
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    remaining_hours = Column(Float, default=0)  # 剩余课时
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="student_profile", foreign_keys=[user_id])
    teacher = relationship("User", back_populates="managed_students", foreign_keys=[teacher_id])
    student_words = relationship("StudentWord", back_populates="student", cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="student", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="student", cascade="all, delete-orphan")
    learning_progress = relationship("LearningProgress", back_populates="student", cascade="all, delete-orphan")
    anti_forget_sessions = relationship("AntiForgetSession", back_populates="student", cascade="all, delete-orphan")
    student_reviews = relationship("StudentReview", back_populates="student", cascade="all, delete-orphan")


class WordSet(Base):
    """单词集表 - 全局共享"""
    __tablename__ = "word_sets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)  # 创建者
    is_global = Column(Boolean, default=True)  # 是否全局共享
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    owner = relationship("User", back_populates="word_sets")
    words = relationship("Word", back_populates="word_set")


class Word(Base):
    """单词表"""
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word_set_id = Column(Integer, ForeignKey("word_sets.id"), nullable=False)
    english = Column(String(255), nullable=False, index=True)
    chinese = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    word_set = relationship("WordSet", back_populates="words")
    student_words = relationship("StudentWord", back_populates="word")


class StudentWord(Base):
    """学生单词学习记录"""
    __tablename__ = "student_words"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    current_stage = Column(Integer, default=0)  # 0-7 学习阶段
    last_reviewed_at = Column(DateTime)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="student_words")
    word = relationship("Word", back_populates="student_words")
    learning_records = relationship("LearningRecord", back_populates="student_word")


class Schedule(Base):
    """课程安排表"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    student_name = Column(String(100), nullable=False)  # 冗余，便于查询

    # 时区支持：存储UTC时间
    scheduled_at = Column(DateTime, nullable=False, index=True)  # UTC时间

    # 向后兼容字段（保留旧字段，但逐步迁移）
    date = Column(Date, nullable=True, index=True)  # 旧字段：仅日期
    time = Column(String(10), nullable=True)  # 旧字段：仅时间 "14:00"

    word_set_name = Column(String(100), nullable=False)
    course_type = Column(String(20), nullable=False)  # 'learning', 'review'
    duration = Column(Integer, default=60)  # 课程时长（分钟）
    class_type = Column(String(10), default='big')  # 'big' (60min), 'small' (30min)
    completed = Column(Boolean, default=False)
    session_id = Column(String(100), nullable=True)  # 关联的抗遗忘会话ID（仅review类型课程）
    timer_version = Column(Integer, default=0)  # 计时器版本号，重置时递增
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    teacher = relationship("User", back_populates="schedules")
    student = relationship("Student", back_populates="schedules")


class LearningSession(Base):
    """学习会话表"""
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    word_set_name = Column(String(100), nullable=False)
    session_date = Column(Date, default=date.today)
    words_count = Column(Integer, nullable=False)
    total_groups = Column(Integer, nullable=False)
    current_group = Column(Integer, default=1)
    current_stage = Column(String(20), default="stage1")  # stage1, stage2, stage3
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="learning_sessions")
    learning_records = relationship("LearningRecord", back_populates="session")


class LearningRecord(Base):
    """学习记录表"""
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=False)
    student_word_id = Column(Integer, ForeignKey("student_words.id"), nullable=False)
    stage = Column(String(20), nullable=False)  # stage1, stage2, stage3
    action_type = Column(String(20))  # 'learn', 'review', 'test'
    result = Column(String(20))  # 'completed', 'passed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("LearningSession", back_populates="learning_records")
    student_word = relationship("StudentWord", back_populates="learning_records")


class LearningProgress(Base):
    """学习进度表"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    word_set_name = Column(String(100), nullable=False)
    word_index = Column(Integer, nullable=False)  # 单词在单词集中的索引
    current_stage = Column(Integer, default=0)  # 0-7 学习阶段
    total_groups = Column(Integer, nullable=False)
    tasks_completed = Column(JSON)  # 例如: {"1": [1, 2, 3], "2": [1, 2]}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="learning_progress")


class AntiForgetSession(Base):
    """抗遗忘会话表"""
    __tablename__ = "anti_forget_sessions"

    id = Column(String(100), primary_key=True)  # 例如: "af-1-wordset-20250114-123456"
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    word_set_name = Column(String(100), nullable=False)
    words = Column(JSON, nullable=False)  # 单词列表
    review_count = Column(Integer, default=0)  # 当前复习次数
    total_reviews = Column(Integer, default=10)  # 总复习次数
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="anti_forget_sessions")
    teacher = relationship("User", foreign_keys=[teacher_id])


class StudentReview(Base):
    """学生复习记录表"""
    __tablename__ = "student_reviews"

    id = Column(String(100), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    word_set_name = Column(String(100), nullable=False)
    learn_date = Column(Date, nullable=False)
    words = Column(JSON, nullable=False)  # 单词列表
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="student_reviews")


# 用于Excel导入的临时表
class WordImport(Base):
    __tablename__ = "word_imports"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String(255), nullable=False)
    chinese = Column(Text, nullable=False)
    word_set = Column(String(100))
    imported_by = Column(String(100))
    import_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
