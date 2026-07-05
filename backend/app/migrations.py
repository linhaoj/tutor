"""数据库迁移模块 - 自动检测和应用数据库架构更改"""

from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError
from app.database import engine, SessionLocal
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_database():
    """执行数据库迁移 - 在应用启动时自动运行"""
    logger.info("🔍 开始检查数据库架构...")
    db = SessionLocal()
    migration_count = 0

    try:
        # ========== 学生表迁移 ==========
        if not check_column_exists('students', 'user_id'):
            logger.info("🔧 迁移 #1: 给 students 表添加 user_id 列")
            # 添加列，允许NULL（旧数据没有关联用户）
            db.execute(text("ALTER TABLE students ADD COLUMN user_id TEXT"))
            db.commit()
            logger.info("✅ students.user_id 列添加成功")
            migration_count += 1

        if not check_column_exists('students', 'teacher_id'):
            logger.info("🔧 迁移 #2: 给 students 表添加 teacher_id 列")
            db.execute(text("ALTER TABLE students ADD COLUMN teacher_id TEXT"))
            db.commit()
            logger.info("✅ students.teacher_id 列添加成功")
            migration_count += 1

        if not check_column_exists('students', 'remaining_hours'):
            logger.info("🔧 迁移 #3: 给 students 表添加 remaining_hours 列")
            db.execute(text("ALTER TABLE students ADD COLUMN remaining_hours REAL DEFAULT 0"))
            db.commit()
            logger.info("✅ students.remaining_hours 列添加成功")
            migration_count += 1

        # ========== 单词表迁移 ==========
        if not check_column_exists('words', 'word_set_id'):
            logger.info("🔧 迁移 #4: 给 words 表添加 word_set_id 列")
            db.execute(text("ALTER TABLE words ADD COLUMN word_set_id INTEGER"))
            db.commit()
            logger.info("✅ words.word_set_id 列添加成功")
            migration_count += 1

        # ========== 课程表迁移 ==========
        if not check_column_exists('schedules', 'scheduled_at'):
            logger.info("🔧 迁移 #5: 给 schedules 表添加 scheduled_at 列")
            db.execute(text("ALTER TABLE schedules ADD COLUMN scheduled_at TIMESTAMP"))
            db.commit()
            logger.info("✅ schedules.scheduled_at 列添加成功")
            migration_count += 1

            # 数据迁移：将旧的 date + time 转换为 scheduled_at
            logger.info("🔄 迁移现有课程数据到新字段...")
            # 使用 || 连接字符串，避免 :00 被误认为绑定参数
            result = db.execute(text("""
                UPDATE schedules
                SET scheduled_at = datetime(date || ' ' || time || char(58) || '00')
                WHERE date IS NOT NULL AND time IS NOT NULL
            """))
            db.commit()
            logger.info(f"✅ 已迁移 {result.rowcount} 条课程记录")

        if not check_column_exists('schedules', 'teacher_id'):
            logger.info("🔧 迁移 #6: 给 schedules 表添加 teacher_id 列")
            db.execute(text("ALTER TABLE schedules ADD COLUMN teacher_id TEXT"))
            db.commit()
            logger.info("✅ schedules.teacher_id 列添加成功")
            migration_count += 1

        # ========== 单词集表迁移 ==========
        if not check_column_exists('word_sets', 'owner_id'):
            logger.info("🔧 迁移 #7: 给 word_sets 表添加 owner_id 列")
            db.execute(text("ALTER TABLE word_sets ADD COLUMN owner_id TEXT"))
            db.commit()
            logger.info("✅ word_sets.owner_id 列添加成功")
            migration_count += 1

        if not check_column_exists('word_sets', 'is_global'):
            logger.info("🔧 迁移 #8: 给 word_sets 表添加 is_global 列")
            db.execute(text("ALTER TABLE word_sets ADD COLUMN is_global BOOLEAN DEFAULT 1"))
            db.commit()
            logger.info("✅ word_sets.is_global 列添加成功（默认全局共享）")
            migration_count += 1

        # ========== 课程表 session_id 迁移 ==========
        if not check_column_exists('schedules', 'session_id'):
            logger.info("🔧 迁移 #9: 给 schedules 表添加 session_id 列")
            db.execute(text("ALTER TABLE schedules ADD COLUMN session_id TEXT"))
            db.commit()
            logger.info("✅ schedules.session_id 列添加成功（用于关联抗遗忘会话）")
            migration_count += 1

        # ========== reading_articles 表迁移 ==========
        # 表可能由旧版本创建（没有 translation 列），需要补上
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        if 'reading_articles' in existing_tables:
            if not check_column_exists('reading_articles', 'translation'):
                logger.info("🔧 迁移 #10: 给 reading_articles 表添加 translation 列")
                db.execute(text("ALTER TABLE reading_articles ADD COLUMN translation JSON"))
                db.commit()
                logger.info("✅ reading_articles.translation 列添加成功")
                migration_count += 1

        # ========== 完成迁移 ==========
        if migration_count > 0:
            logger.info(f"🎉 数据库迁移完成！共执行 {migration_count} 项迁移")
        else:
            logger.info("✅ 数据库架构已是最新版本，无需迁移")

    except OperationalError as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ 迁移过程中出现未知错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migrations():
    """验证所有必需的列是否存在"""
    required_columns = {
        'students': ['user_id', 'teacher_id', 'remaining_hours'],
        'schedules': ['scheduled_at', 'teacher_id', 'session_id'],
        'word_sets': ['owner_id', 'is_global'],
        'words': ['word_set_id'],
    }

    logger.info("🔍 验证数据库架构...")
    all_verified = True

    for table_name, columns in required_columns.items():
        for column_name in columns:
            if not check_column_exists(table_name, column_name):
                logger.error(f"❌ 缺少列: {table_name}.{column_name}")
                all_verified = False
            else:
                logger.debug(f"✅ {table_name}.{column_name} 存在")

    if all_verified:
        logger.info("✅ 所有必需的列都已存在")
    else:
        logger.error("❌ 部分必需的列缺失，请检查迁移日志")

    return all_verified
