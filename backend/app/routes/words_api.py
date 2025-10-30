"""单词管理API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import io

from app.database import get_db
from app.models import WordSet, Word, User
from app.routes.auth import get_current_user
from app.logger import get_logger

logger = get_logger("words")

router = APIRouter(prefix="/api/words", tags=["单词管理"])


class WordSetCreate(BaseModel):
    name: str
    is_global: bool = True


class WordCreate(BaseModel):
    english: str
    chinese: str


class WordResponse(BaseModel):
    id: int
    english: str
    chinese: str
    word_set_name: str

    class Config:
        from_attributes = True


class WordSetResponse(BaseModel):
    id: int
    name: str
    owner_id: str
    is_global: bool
    word_count: int


@router.post("/sets", response_model=WordSetResponse)
async def create_word_set(
    word_set_data: WordSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建单词集"""
    existing = db.query(WordSet).filter(WordSet.name == word_set_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="单词集名称已存在")

    word_set = WordSet(
        name=word_set_data.name,
        owner_id=current_user.id,
        is_global=word_set_data.is_global
    )
    db.add(word_set)
    db.commit()
    db.refresh(word_set)

    return WordSetResponse(
        id=word_set.id,
        name=word_set.name,
        owner_id=word_set.owner_id,
        is_global=word_set.is_global,
        word_count=0
    )


@router.get("/sets", response_model=List[WordSetResponse])
async def get_word_sets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有单词集（全局共享）"""
    word_sets = db.query(WordSet).filter(WordSet.is_global == True).all()

    return [
        WordSetResponse(
            id=ws.id,
            name=ws.name,
            owner_id=ws.owner_id,
            is_global=ws.is_global,
            word_count=len(ws.words)
        )
        for ws in word_sets
    ]


@router.get("/sets/{word_set_name}/words", response_model=List[WordResponse])
async def get_words_by_set(
    word_set_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定单词集的所有单词"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    return [
        WordResponse(
            id=word.id,
            english=word.english,
            chinese=word.chinese,
            word_set_name=word_set.name
        )
        for word in word_set.words
    ]


@router.post("/sets/{word_set_name}/words", response_model=WordResponse)
async def add_word_to_set(
    word_set_name: str,
    word_data: WordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加单词到单词集"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    word = Word(
        word_set_id=word_set.id,
        english=word_data.english,
        chinese=word_data.chinese
    )
    db.add(word)
    db.commit()
    db.refresh(word)

    return WordResponse(
        id=word.id,
        english=word.english,
        chinese=word.chinese,
        word_set_name=word_set.name
    )


@router.post("/sets/{word_set_name}/import-excel")
async def import_words_from_excel(
    word_set_name: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从Excel导入单词"""
    logger.info(f"教师 {current_user.username} 开始导入单词: 单词集={word_set_name}, 文件={file.filename}")

    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        logger.warning(f"导入单词失败: 单词集不存在 - {word_set_name}")
        raise HTTPException(status_code=404, detail="单词集不存在")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        if 'english' not in df.columns or 'chinese' not in df.columns:
            logger.warning(f"导入单词失败: Excel格式错误 - 缺少english或chinese列")
            raise HTTPException(status_code=400, detail="Excel文件必须包含english和chinese列")

        imported_count = 0
        for _, row in df.iterrows():
            word = Word(
                word_set_id=word_set.id,
                english=str(row['english']),
                chinese=str(row['chinese'])
            )
            db.add(word)
            imported_count += 1

        db.commit()
        logger.info(f"单词导入成功: 单词集={word_set_name}, 导入数量={imported_count}, 教师={current_user.username}")
        return {"message": f"成功导入 {imported_count} 个单词"}

    except Exception as e:
        logger.error(f"导入单词失败: 单词集={word_set_name}, 错误={str(e)}")
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.delete("/words/{word_id}")
async def delete_word(
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除单词"""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="单词不存在")

    db.delete(word)
    db.commit()
    return {"message": "单词删除成功"}


@router.put("/sets/{word_set_name}/rename")
async def rename_word_set(
    word_set_name: str,
    rename_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名单词集"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    new_name = rename_data.get('new_name')
    if not new_name:
        raise HTTPException(status_code=400, detail="新名称不能为空")

    # 检查新名称是否已存在
    existing = db.query(WordSet).filter(WordSet.name == new_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="单词集名称已存在")

    old_name = word_set.name
    word_set.name = new_name
    db.commit()

    logger.info(f"重命名单词集: {old_name} → {new_name}, 教师={current_user.username}")
    return {"message": "单词集重命名成功", "old_name": old_name, "new_name": new_name}


@router.delete("/sets/{word_set_name}")
async def delete_word_set(
    word_set_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除单词集及其所有单词"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    # 先删除所有关联的单词（解决外键约束问题）
    word_count = len(word_set.words)
    for word in word_set.words:
        db.delete(word)

    logger.info(f"删除单词集: 单词集={word_set_name}, 单词数={word_count}, 教师={current_user.username}")

    # 再删除单词集
    db.delete(word_set)
    db.commit()

    return {"message": f"单词集删除成功（包含{word_count}个单词）"}


@router.post("/sets/{word_set_name}/batch-add")
async def batch_add_words(
    word_set_name: str,
    words: List[WordCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量添加单词到单词集"""
    word_set = db.query(WordSet).filter(WordSet.name == word_set_name).first()
    if not word_set:
        raise HTTPException(status_code=404, detail="单词集不存在")

    added_count = 0
    for word_data in words:
        word = Word(
            word_set_id=word_set.id,
            english=word_data.english,
            chinese=word_data.chinese
        )
        db.add(word)
        added_count += 1

    db.commit()
    logger.info(f"批量添加单词: 单词集={word_set_name}, 数量={added_count}, 教师={current_user.username}")
    return {"message": f"成功添加 {added_count} 个单词"}
