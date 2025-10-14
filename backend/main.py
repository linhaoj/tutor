from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.database import get_db, create_tables
from app.models import (
    User, Student, WordSet, Word, StudentWord,
    Schedule, LearningSession, LearningRecord,
    LearningProgress, AntiForgetSession, StudentReview
)

# 创建FastAPI应用
app = FastAPI(
    title="英语陪练系统",
    description="智能英语单词学习和抗遗忘系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://47.108.248.168:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """应用启动时创建数据库表"""
    create_tables()

@app.get("/")
async def root():
    return {"message": "英语陪练系统 API 服务已启动"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)