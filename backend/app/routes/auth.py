"""用户认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.logger import get_logger

logger = get_logger("auth")

# JWT配置
SECRET_KEY = "your-secret-key-change-this-in-production"  # 生产环境需要更换
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30天

router = APIRouter(prefix="/api/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Pydantic模型
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    display_name: str
    email: Optional[str] = None
    student_id: Optional[int] = None
    created_at: str
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "teacher"
    email: Optional[str] = None
    student_id: Optional[int] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_admin(current_user: User = Depends(get_current_user)):
    """验证当前用户是管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user


# API路由
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    logger.info(f"用户尝试登录: {form_data.username}")

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.verify_password(form_data.password):
        logger.warning(f"登录失败: 用户名或密码错误 - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    logger.info(f"登录成功: 用户={user.username}, 角色={user.role}, ID={user.id}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
        email=current_user.email,
        student_id=current_user.student_id,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """注册新用户（仅管理员）"""
    logger.info(f"管理员 {current_user.username} 尝试创建新用户: {user_data.username}")

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"创建用户失败: 用户名已存在 - {user_data.username}")
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            logger.warning(f"创建用户失败: 邮箱已被使用 - {user_data.email}")
            raise HTTPException(status_code=400, detail="邮箱已被使用")

    # 创建新用户
    new_user = User(
        id=f"user-{int(datetime.utcnow().timestamp() * 1000)}",
        username=user_data.username,
        role=user_data.role,
        display_name=user_data.display_name,
        email=user_data.email,
        student_id=user_data.student_id
    )
    new_user.set_password(user_data.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"新用户创建成功: 用户名={new_user.username}, 角色={new_user.role}, ID={new_user.id}")

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        display_name=new_user.display_name,
        email=new_user.email,
        student_id=new_user.student_id,
        created_at=new_user.created_at.isoformat(),
        last_login_at=None
    )


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅管理员）"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            display_name=user.display_name,
            email=user.email,
            student_id=user.student_id,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
        )
        for user in users
    ]


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    if user_id == current_user.id:
        logger.warning(f"用户 {current_user.username} 尝试删除自己的账号")
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"删除用户失败: 用户不存在 - ID={user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")

    deleted_username = user.username
    db.delete(user)
    db.commit()

    logger.info(f"用户删除成功: 管理员={current_user.username}, 被删除用户={deleted_username}, ID={user_id}")
    return {"message": "用户删除成功"}


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    # 只有管理员或用户本人可以修改
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if user_update.display_name:
        user.display_name = user_update.display_name
    if user_update.email:
        # 检查邮箱是否已被其他用户使用
        existing_email = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = user_update.email

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        display_name=user.display_name,
        email=user.email,
        student_id=user.student_id,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not current_user.verify_password(password_data.old_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    # 设置新密码
    current_user.set_password(password_data.new_password)
    db.commit()

    return {"message": "密码修改成功"}


@router.post("/reset-password/{user_id}")
async def reset_user_password(
    user_id: str,
    new_password: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """重置用户密码（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.set_password(new_password)
    db.commit()

    return {"message": "密码重置成功"}
