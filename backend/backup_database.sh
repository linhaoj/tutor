#!/bin/bash

# 数据库备份脚本
# 用途：自动备份 SQLite 数据库文件
# 使用方法：./backup_database.sh [backup_name]

# 配置
DB_FILE="/var/www/tutor/backend/english_tutor.db"
BACKUP_DIR="/var/www/tutor/backups/database"
BACKUP_RETENTION_DAYS=30  # 保留30天的备份

# 如果在本地开发环境，使用本地路径
if [ ! -f "$DB_FILE" ]; then
    DB_FILE="./english_tutor.db"
    BACKUP_DIR="./backups/database"
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
if [ -z "$1" ]; then
    # 如果没有指定备份名称，使用时间戳
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="backup_${TIMESTAMP}.db"
else
    # 使用指定的备份名称
    BACKUP_NAME="${1}.db"
fi

BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}"

# 检查数据库文件是否存在
if [ ! -f "$DB_FILE" ]; then
    echo "❌ 错误: 数据库文件不存在: $DB_FILE"
    exit 1
fi

# 执行备份
echo "📦 开始备份数据库..."
echo "源文件: $DB_FILE"
echo "目标文件: $BACKUP_FILE"

# 使用 SQLite 的 backup 命令确保数据一致性
sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"

if [ $? -eq 0 ]; then
    # 获取文件大小
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ 备份成功!"
    echo "备份文件: $BACKUP_FILE"
    echo "文件大小: $SIZE"

    # 创建备份信息文件
    INFO_FILE="${BACKUP_FILE}.info"
    cat > "$INFO_FILE" << EOF
备份时间: $(date +"%Y-%m-%d %H:%M:%S")
源数据库: $DB_FILE
备份文件: $BACKUP_FILE
文件大小: $SIZE
备份说明: $2
EOF

    echo ""
    echo "📄 备份信息已保存到: $INFO_FILE"
else
    echo "❌ 备份失败!"
    exit 1
fi

# 清理旧备份（保留最近30天）
echo ""
echo "🧹 清理旧备份（保留${BACKUP_RETENTION_DAYS}天）..."
find "$BACKUP_DIR" -name "backup_*.db" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "backup_*.db.info" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

# 列出所有备份
echo ""
echo "📋 当前所有备份:"
ls -lh "$BACKUP_DIR"/*.db 2>/dev/null | awk '{print $9, "(" $5 ")"}'

echo ""
echo "✨ 备份完成!"
