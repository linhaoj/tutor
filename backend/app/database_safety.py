"""数据库事务安全模块 - 保证数据一致性"""
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException
from app.logger import get_logger

logger = get_logger("db_safety")


class DatabaseTransactionError(Exception):
    """数据库事务错误"""
    pass


def safe_transaction(operation_name: str = "数据库操作"):
    """
    数据库事务安全装饰器

    功能：
    1. 自动捕获所有数据库异常
    2. 失败时自动回滚事务
    3. 记录详细错误日志
    4. 返回友好的错误信息给用户

    用法：
        @safe_transaction("创建学生")
        async def create_student(db: Session, ...):
            # 你的数据库操作
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 找到Session对象
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            if db is None:
                db = kwargs.get('db')

            if db is None:
                logger.error(f"{operation_name}: 未找到数据库Session对象")
                raise HTTPException(status_code=500, detail="系统错误: 数据库连接失败")

            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                return result

            except IntegrityError as e:
                # 数据完整性错误（唯一约束、外键约束等）
                db.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                logger.error(f"{operation_name}失败 [完整性错误]: {error_msg}")

                # 友好的错误提示
                if "UNIQUE constraint failed" in error_msg or "Duplicate entry" in error_msg:
                    raise HTTPException(status_code=400, detail="数据重复: 该记录已存在")
                elif "FOREIGN KEY constraint failed" in error_msg:
                    raise HTTPException(status_code=400, detail="关联数据不存在")
                else:
                    raise HTTPException(status_code=400, detail=f"数据完整性错误: {error_msg}")

            except SQLAlchemyError as e:
                # 其他数据库错误
                db.rollback()
                error_msg = str(e)
                logger.error(f"{operation_name}失败 [数据库错误]: {error_msg}")
                raise HTTPException(status_code=500, detail="数据库操作失败，所有更改已回滚")

            except HTTPException:
                # 业务逻辑错误（如权限不足、资源不存在），直接抛出
                db.rollback()
                raise

            except Exception as e:
                # 未预期的错误
                db.rollback()
                error_msg = str(e)
                logger.error(f"{operation_name}失败 [未知错误]: {error_msg}", exc_info=True)
                raise HTTPException(status_code=500, detail="系统错误，所有更改已回滚")

        return wrapper
    return decorator


def validate_business_rule(condition: bool, error_message: str):
    """
    业务规则验证

    用法：
        validate_business_rule(
            student.remaining_hours >= hours,
            f"剩余课时不足: 当前{student.remaining_hours}h，需要{hours}h"
        )
    """
    if not condition:
        logger.warning(f"业务规则验证失败: {error_message}")
        raise HTTPException(status_code=400, detail=error_message)


class TransactionContext:
    """
    事务上下文管理器 - 用于复杂的多步骤操作

    用法：
        async with TransactionContext(db, "创建课程并扣减课时") as ctx:
            # 步骤1: 创建课程
            schedule = Schedule(...)
            db.add(schedule)
            ctx.checkpoint("课程创建成功")

            # 步骤2: 扣减课时
            student.remaining_hours -= 1.0
            ctx.checkpoint("课时扣减成功")

            # 自动提交
    """
    def __init__(self, db: Session, operation_name: str):
        self.db = db
        self.operation_name = operation_name
        self.checkpoints = []

    async def __aenter__(self):
        logger.debug(f"开始事务: {self.operation_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 成功，提交事务
            try:
                self.db.commit()
                logger.info(f"事务提交成功: {self.operation_name} | 检查点: {' → '.join(self.checkpoints)}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"事务提交失败: {self.operation_name} | 错误: {str(e)}")
                raise HTTPException(status_code=500, detail="数据保存失败，所有更改已回滚")
        else:
            # 失败，回滚事务
            self.db.rollback()
            logger.error(f"事务回滚: {self.operation_name} | 已完成: {' → '.join(self.checkpoints)} | 错误: {str(exc_val)}")

            # 如果是HTTPException，直接抛出
            if isinstance(exc_val, HTTPException):
                return False

            # 其他异常，包装成HTTPException
            raise HTTPException(status_code=500, detail=f"{self.operation_name}失败，所有更改已回滚")

        return False  # 不抑制异常

    def checkpoint(self, message: str):
        """记录检查点"""
        self.checkpoints.append(message)
        logger.debug(f"事务检查点: {self.operation_name} | {message}")
