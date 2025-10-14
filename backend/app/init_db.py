"""数据库初始化脚本"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
import bcrypt


def create_default_admin():
    """创建默认管理员账号"""
    db: Session = SessionLocal()
    try:
        # 检查是否已存在admin用户
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if not existing_admin:
            # 创建默认管理员
            admin = User(
                id="admin-001",
                username="admin",
                role="admin",
                display_name="系统管理员",
                email="admin@example.com"
            )
            admin.set_password("admin123")

            db.add(admin)
            db.commit()
            db.refresh(admin)

            print("✅ 默认管理员账号已创建")
            print("   用户名: admin")
            print("   密码: admin123")
        else:
            print("ℹ️  管理员账号已存在")

    except Exception as e:
        print(f"❌ 创建管理员账号失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    from app.database import create_tables

    print("🔧 正在创建数据库表...")
    create_tables()
    print("✅ 数据库表创建完成")

    print("\n🔧 正在创建默认管理员账号...")
    create_default_admin()

    print("\n✅ 数据库初始化完成！")


if __name__ == "__main__":
    init_database()
