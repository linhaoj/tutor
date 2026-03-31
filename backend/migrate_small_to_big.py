"""
迁移脚本：将所有小课改为大课
运行一次后可删除此文件

用法：
  cd backend
  python migrate_small_to_big.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'english_tutor.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM schedules WHERE class_type = 'small'")
count = cursor.fetchone()[0]
print(f"找到 {count} 条小课记录，开始迁移...")

cursor.execute("""
    UPDATE schedules
    SET class_type = 'big', duration = 60
    WHERE class_type = 'small'
""")

conn.commit()
conn.close()

print(f"完成：{count} 条记录已更新为大课（60分钟）")
