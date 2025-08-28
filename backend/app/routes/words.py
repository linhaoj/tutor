from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import pandas as pd
import io

from app.database import get_db
from app.models import Word, Student, StudentWord

router = APIRouter()

# Pydantic模型
class WordCreate(BaseModel):
    english: str
    chinese: str
    word_set: str = None

class WordResponse(BaseModel):
    id: int
    english: str
    chinese: str
    word_set: str = None
    
    class Config:
        from_attributes = True

class WordImportResponse(BaseModel):
    total_imported: int
    successful: int
    failed: int
    errors: List[str] = []

class AssignWordsRequest(BaseModel):
    student_id: int
    word_ids: List[int]

@router.post("/", response_model=WordResponse)
async def create_word(word: WordCreate, db: Session = Depends(get_db)):
    """创建单个单词"""
    # 检查单词是否已存在
    existing = db.query(Word).filter(Word.english == word.english).first()
    if existing:
        raise HTTPException(status_code=400, detail="单词已存在")
    
    db_word = Word(
        english=word.english,
        chinese=word.chinese,
        word_set=word.word_set
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    
    return db_word

@router.get("/", response_model=List[WordResponse])
async def get_words(word_set: str = None, db: Session = Depends(get_db)):
    """获取单词列表，可按单词集过滤"""
    query = db.query(Word)
    if word_set:
        query = query.filter(Word.word_set == word_set)
    
    words = query.all()
    return words

@router.get("/sets")
async def get_word_sets(db: Session = Depends(get_db)):
    """获取所有单词集名称"""
    sets = db.query(Word.word_set).distinct().filter(Word.word_set.isnot(None)).all()
    return [{"name": word_set[0]} for word_set in sets]

@router.post("/import", response_model=WordImportResponse)
async def import_words_from_excel(
    file: UploadFile = File(...),
    word_set: str = None,
    db: Session = Depends(get_db)
):
    """从Excel文件导入单词"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
    
    try:
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 检查必要的列
        required_columns = ['english', 'chinese']  # 或者 ['英文', '中文']
        
        # 尝试不同的列名组合
        if 'english' in df.columns and 'chinese' in df.columns:
            english_col, chinese_col = 'english', 'chinese'
        elif '英文' in df.columns and '中文' in df.columns:
            english_col, chinese_col = '英文', '中文'
        elif 'English' in df.columns and 'Chinese' in df.columns:
            english_col, chinese_col = 'English', 'Chinese'
        else:
            # 如果列名不匹配，尝试使用前两列
            if len(df.columns) >= 2:
                english_col, chinese_col = df.columns[0], df.columns[1]
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Excel文件应包含英文和中文两列，列名可以是：english/chinese, 英文/中文, English/Chinese，或者确保前两列分别是英文和中文"
                )
        
        total_rows = len(df)
        successful = 0
        failed = 0
        errors = []
        
        # 如果没有指定word_set，使用文件名
        if not word_set:
            word_set = file.filename.rsplit('.', 1)[0]
        
        # 逐行处理
        for index, row in df.iterrows():
            try:
                english = str(row[english_col]).strip()
                chinese = str(row[chinese_col]).strip()
                
                # 跳过空行
                if not english or not chinese or english == 'nan' or chinese == 'nan':
                    continue
                
                # 检查单词是否已存在
                existing = db.query(Word).filter(Word.english == english).first()
                if existing:
                    errors.append(f"第{index+2}行: 单词 '{english}' 已存在")
                    failed += 1
                    continue
                
                # 创建新单词
                new_word = Word(
                    english=english,
                    chinese=chinese,
                    word_set=word_set
                )
                db.add(new_word)
                successful += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
                failed += 1
        
        db.commit()
        
        return WordImportResponse(
            total_imported=total_rows,
            successful=successful,
            failed=failed,
            errors=errors[:10]  # 只返回前10个错误
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件处理失败: {str(e)}")

@router.post("/assign")
async def assign_words_to_student(request: AssignWordsRequest, db: Session = Depends(get_db)):
    """将单词分配给学生"""
    # 验证学生是否存在
    student = db.query(Student).filter(Student.id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 验证单词是否存在
    words = db.query(Word).filter(Word.id.in_(request.word_ids)).all()
    if len(words) != len(request.word_ids):
        raise HTTPException(status_code=404, detail="部分单词不存在")
    
    assigned_count = 0
    skipped_count = 0
    
    for word_id in request.word_ids:
        # 检查是否已经分配过
        existing = db.query(StudentWord).filter(
            StudentWord.student_id == request.student_id,
            StudentWord.word_id == word_id
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建学生单词关系
        student_word = StudentWord(
            student_id=request.student_id,
            word_id=word_id,
            grid_position=0  # 初始在格子0（未学）
        )
        db.add(student_word)
        assigned_count += 1
    
    db.commit()
    
    return {
        "message": f"成功分配{assigned_count}个单词，跳过{skipped_count}个已存在的单词",
        "assigned": assigned_count,
        "skipped": skipped_count
    }

@router.get("/{word_id}", response_model=WordResponse)
async def get_word(word_id: int, db: Session = Depends(get_db)):
    """获取单个单词信息"""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="单词不存在")
    return word

@router.put("/{word_id}", response_model=WordResponse)
async def update_word(word_id: int, word: WordCreate, db: Session = Depends(get_db)):
    """更新单词"""
    db_word = db.query(Word).filter(Word.id == word_id).first()
    if not db_word:
        raise HTTPException(status_code=404, detail="单词不存在")
    
    # 检查英文单词是否被其他单词使用
    if word.english != db_word.english:
        existing = db.query(Word).filter(
            Word.english == word.english,
            Word.id != word_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="英文单词已存在")
    
    db_word.english = word.english
    db_word.chinese = word.chinese
    db_word.word_set = word.word_set
    
    db.commit()
    db.refresh(db_word)
    
    return db_word

@router.delete("/{word_id}")
async def delete_word(word_id: int, db: Session = Depends(get_db)):
    """删除单词"""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="单词不存在")
    
    # 检查是否有学生正在学习这个单词
    student_words = db.query(StudentWord).filter(StudentWord.word_id == word_id).all()
    if student_words:
        raise HTTPException(
            status_code=400, 
            detail=f"无法删除，有{len(student_words)}个学生正在学习这个单词"
        )
    
    db.delete(word)
    db.commit()
    
    return {"message": f"单词 '{word.english}' 已删除"}

@router.get("/student/{student_id}")
async def get_student_words(student_id: int, grid_position: int = None, db: Session = Depends(get_db)):
    """获取学生的单词列表，可按格子位置过滤"""
    query = db.query(StudentWord).join(Word).filter(StudentWord.student_id == student_id)
    
    if grid_position is not None:
        query = query.filter(StudentWord.grid_position == grid_position)
    
    student_words = query.all()
    
    result = []
    for sw in student_words:
        result.append({
            "id": sw.word.id,
            "english": sw.word.english,
            "chinese": sw.word.chinese,
            "word_set": sw.word.word_set,
            "grid_position": sw.grid_position,
            "last_reviewed_at": sw.last_reviewed_at,
            "review_count": sw.review_count
        })
    
    return result