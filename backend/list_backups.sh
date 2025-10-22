#!/bin/bash

# 列出所有数据库备份
# 使用方法：./list_backups.sh

# 配置
BACKUP_DIR="/var/www/tutor/backups/database"

# 如果在本地开发环境，使用本地路径
if [ ! -d "/var/www/tutor" ]; then
    BACKUP_DIR="./backups/database"
fi

echo "📋 数据库备份列表"
echo "================================"
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 获取所有备份文件
BACKUPS=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null)

if [ -z "$BACKUPS" ]; then
    echo "ℹ️  没有找到任何备份文件"
    echo "使用 ./backup_database.sh 创建备份"
    exit 0
fi

# 统计信息
TOTAL_COUNT=$(echo "$BACKUPS" | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

echo "备份目录: $BACKUP_DIR"
echo "备份总数: $TOTAL_COUNT"
echo "占用空间: $TOTAL_SIZE"
echo ""
echo "--------------------------------"
echo ""

# 显示每个备份的详细信息
i=1
for backup in $BACKUPS; do
    BASENAME=$(basename "$backup")
    FILE_SIZE=$(du -h "$backup" | cut -f1)

    # 读取备份信息文件
    INFO_FILE="${backup}.info"
    if [ -f "$INFO_FILE" ]; then
        BACKUP_TIME=$(grep "备份时间:" "$INFO_FILE" | cut -d: -f2- | xargs)
        DESCRIPTION=$(grep "备份说明:" "$INFO_FILE" | cut -d: -f2- | xargs)
    else
        # 如果没有信息文件，使用文件修改时间
        BACKUP_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup")
        DESCRIPTION="无描述"
    fi

    # 计算备份年龄
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        FILE_AGE=$(( ($(date +%s) - $(stat -f %m "$backup")) / 86400 ))
    else
        # Linux
        FILE_AGE=$(( ($(date +%s) - $(stat -c %Y "$backup")) / 86400 ))
    fi

    # 显示备份信息
    printf "备份 #%d\n" $i
    printf "  文件名: %s\n" "$BASENAME"
    printf "  大小:   %s\n" "$FILE_SIZE"
    printf "  时间:   %s (%d天前)\n" "$BACKUP_TIME" "$FILE_AGE"
    if [ "$DESCRIPTION" != "无描述" ] && [ ! -z "$DESCRIPTION" ]; then
        printf "  说明:   %s\n" "$DESCRIPTION"
    fi
    echo ""

    ((i++))
done

echo "--------------------------------"
echo ""
echo "💡 提示:"
echo "  • 恢复备份: ./restore_database.sh"
echo "  • 创建备份: ./backup_database.sh [名称] [说明]"
echo "  • 自动清理超过30天的备份"
