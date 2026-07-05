from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

# 加载环境变量（.env 是已提交的基础配置，.env.local 是不进git的本地/服务器专属密钥，不会覆盖已有变量）
load_dotenv()
load_dotenv(".env.local")

# 数据库URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./english_tutor.db"
)

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建所有表
def create_tables():
    from app.models import Base
    Base.metadata.create_all(bind=engine)