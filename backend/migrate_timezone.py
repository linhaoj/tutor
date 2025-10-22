"""
数据库迁移脚本：添加时区支持

为 Schedule 表添加 scheduled_at 字段（UTC时间）
并从现有的 date 和 time 字段迁移数据
"""

from app.database import get_db, engine
from app.models import Schedule
from sqlalchemy import text
from datetime import datetime, time as dt_time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_timezone():
    """添加scheduled_at字段并迁移现有数据"""

    logger.info("开始时区迁移...")

    with engine.connect() as conn:
        # 1. 检查 scheduled_at 列是否已存在
        result = conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('schedules') WHERE name='scheduled_at'"
        ))
        column_exists = result.fetchone()[0] > 0

        if not column_exists:
            logger.info("添加 scheduled_at 列...")
            # 添加新列（允许NULL，稍后填充数据）
            conn.execute(text(
                "ALTER TABLE schedules ADD COLUMN scheduled_at DATETIME"
            ))
            conn.commit()
            logger.info("✅ scheduled_at 列添加成功")
        else:
            logger.info("scheduled_at 列已存在，跳过添加")

        # 2. 迁移现有数据：合并 date 和 time 为 scheduled_at
        logger.info("迁移现有数据...")

        result = conn.execute(text(
            "SELECT id, date, time FROM schedules WHERE scheduled_at IS NULL"
        ))
        rows = result.fetchall()

        if rows:
            logger.info(f"发现 {len(rows)} 条需要迁移的记录")

            for row in rows:
                schedule_id, date_str, time_str = row

                try:
                    # 解析日期和时间
                    # date_str 格式: "2025-10-21"
                    # time_str 格式: "15:00"

                    date_parts = date_str.split('-')
                    time_parts = time_str.split(':')

                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])

                    # 假设原始时间是北京时间 (UTC+8)
                    # 转换为 UTC: 减去 8 小时
                    local_dt = datetime(year, month, day, hour, minute)

                    # 简单处理：假设原数据是北京时间，转为UTC
                    # UTC = 北京时间 - 8小时
                    utc_dt = local_dt.replace(hour=max(0, hour - 8))

                    # 如果小时<8，需要减一天
                    if hour < 8:
                        from datetime import timedelta
                        utc_dt = local_dt - timedelta(hours=8)

                    # 更新数据库
                    conn.execute(
                        text("UPDATE schedules SET scheduled_at = :scheduled_at WHERE id = :id"),
                        {"scheduled_at": utc_dt, "id": schedule_id}
                    )

                    logger.info(f"  迁移 ID={schedule_id}: {date_str} {time_str} (北京) → {utc_dt} (UTC)")

                except Exception as e:
                    logger.error(f"  迁移 ID={schedule_id} 失败: {e}")
                    # 使用默认值
                    conn.execute(
                        text("UPDATE schedules SET scheduled_at = :scheduled_at WHERE id = :id"),
                        {"scheduled_at": datetime.utcnow(), "id": schedule_id}
                    )

            conn.commit()
            logger.info("✅ 数据迁移完成")
        else:
            logger.info("没有需要迁移的数据")

        # 3. 将 date 和 time 列改为可选（nullable=True）
        # SQLite 不支持直接修改列属性，所以我们在模型中已经设置为 nullable=True

        logger.info("✅ 迁移完成！")


if __name__ == "__main__":
    migrate_timezone()
