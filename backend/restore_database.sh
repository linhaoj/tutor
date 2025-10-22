#!/bin/bash

# 数据库恢复脚本
# 用途：从备份恢复数据库
# 使用方法：./restore_database.sh [backup_file]

# 配置
DB_FILE="/var/www/tutor/backend/english_tutor.db"
BACKUP_DIR="/var/www/tutor/backups/database"

# 如果在本地开发环境，使用本地路径
if [ ! -d "/var/www/tutor" ]; then
    DB_FILE="./english_tutor.db"
    BACKUP_DIR="./backups/database"
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔄 数据库恢复工具"
echo "================================"

# 如果没有指定备份文件，列出所有备份
if [ -z "$1" ]; then
    echo "📋 可用的备份文件:"
    echo ""

    # 列出所有备份文件
    BACKUPS=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null)

    if [ -z "$BACKUPS" ]; then
        echo "❌ 没有找到任何备份文件"
        exit 1
    fi

    # 显示备份列表（带编号）
    i=1
    declare -a BACKUP_ARRAY
    for backup in $BACKUPS; do
        BACKUP_ARRAY[$i]=$backup

        # 获取备份信息
        INFO_FILE="${backup}.info"
        if [ -f "$INFO_FILE" ]; then
            BACKUP_TIME=$(grep "备份时间:" "$INFO_FILE" | cut -d: -f2-)
            FILE_SIZE=$(grep "文件大小:" "$INFO_FILE" | cut -d: -f2-)
        else
            BACKUP_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup")
            FILE_SIZE=$(du -h "$backup" | cut -f1)
        fi

        printf "${GREEN}%2d${NC}) %s\n" $i "$(basename $backup)"
        printf "    时间: %s  大小: %s\n" "$BACKUP_TIME" "$FILE_SIZE"
        echo ""

        ((i++))
    done

    # 让用户选择
    echo -n "请输入要恢复的备份编号 (1-$((i-1)))，或按 Ctrl+C 取消: "
    read choice

    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -ge $i ]; then
        echo "❌ 无效的选择"
        exit 1
    fi

    BACKUP_FILE="${BACKUP_ARRAY[$choice]}"
else
    # 使用指定的备份文件
    if [[ "$1" == /* ]]; then
        # 绝对路径
        BACKUP_FILE="$1"
    else
        # 相对路径或文件名
        if [ -f "$1" ]; then
            BACKUP_FILE="$1"
        else
            BACKUP_FILE="${BACKUP_DIR}/$1"
        fi
    fi
fi

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo ""
echo "⚠️  ${YELLOW}警告: 此操作将覆盖当前数据库！${NC}"
echo "当前数据库: $DB_FILE"
echo "备份文件: $BACKUP_FILE"
echo ""

# 显示备份信息
INFO_FILE="${BACKUP_FILE}.info"
if [ -f "$INFO_FILE" ]; then
    echo "📄 备份信息:"
    cat "$INFO_FILE"
    echo ""
fi

# 确认操作
echo -n "是否继续? (yes/no): "
read confirmation

if [ "$confirmation" != "yes" ]; then
    echo "❌ 操作已取消"
    exit 0
fi

# 创建当前数据库的紧急备份
if [ -f "$DB_FILE" ]; then
    EMERGENCY_BACKUP="${BACKUP_DIR}/emergency_backup_$(date +%Y%m%d_%H%M%S).db"
    echo ""
    echo "📦 创建紧急备份..."
    sqlite3 "$DB_FILE" ".backup '$EMERGENCY_BACKUP'"
    echo "✅ 紧急备份已保存: $EMERGENCY_BACKUP"
fi

# 停止后端服务（如果正在运行）
echo ""
echo "🛑 停止后端服务..."
if pgrep -f "python.*main.py" > /dev/null; then
    pkill -f "python.*main.py"
    sleep 2
    echo "✅ 后端服务已停止"
else
    echo "ℹ️  后端服务未运行"
fi

# 执行恢复
echo ""
echo "🔄 开始恢复数据库..."
cp "$BACKUP_FILE" "$DB_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 数据库恢复成功!"
    echo ""
    echo "📊 数据库信息:"
    echo "文件: $DB_FILE"
    echo "大小: $(du -h $DB_FILE | cut -f1)"

    # 验证数据库完整性
    echo ""
    echo "🔍 验证数据库完整性..."
    sqlite3 "$DB_FILE" "PRAGMA integrity_check;" > /tmp/db_check.txt

    if grep -q "ok" /tmp/db_check.txt; then
        echo "✅ 数据库完整性检查通过"
    else
        echo "❌ 警告: 数据库完整性检查失败"
        cat /tmp/db_check.txt
    fi

    echo ""
    echo "✨ 恢复完成!"
    echo ""
    echo "⚠️  请手动重启后端服务:"
    echo "   cd /var/www/tutor/backend && pm2 restart all"
else
    echo "❌ 恢复失败!"
    echo ""
    echo "尝试从紧急备份恢复:"
    echo "   ./restore_database.sh $EMERGENCY_BACKUP"
    exit 1
fi
