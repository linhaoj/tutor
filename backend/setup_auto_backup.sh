#!/bin/bash

# 设置自动备份定时任务
# 用途：在服务器上配置每天自动备份数据库
# 使用方法：sudo ./setup_auto_backup.sh

echo "⚙️  设置自动备份定时任务"
echo "================================"
echo ""

# 检查是否在服务器上
if [ ! -d "/var/www/tutor" ]; then
    echo "❌ 错误: 此脚本只能在服务器上运行"
    echo "当前路径不是服务器路径: /var/www/tutor"
    exit 1
fi

# 备份脚本路径
BACKUP_SCRIPT="/var/www/tutor/backend/backup_database.sh"
LOG_DIR="/var/www/tutor/backups/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查备份脚本是否存在
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ 错误: 备份脚本不存在: $BACKUP_SCRIPT"
    exit 1
fi

# 确保脚本可执行
chmod +x "$BACKUP_SCRIPT"

echo "📝 创建定时任务..."
echo ""

# 定时任务配置
# 每天凌晨 2:00 执行备份
CRON_SCHEDULE="0 2 * * *"
CRON_COMMAND="$BACKUP_SCRIPT >> $LOG_DIR/auto_backup.log 2>&1"
CRON_JOB="$CRON_SCHEDULE $CRON_COMMAND"

# 检查是否已存在相同的定时任务
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "⚠️  检测到已存在的备份定时任务"
    echo ""
    echo "当前定时任务:"
    crontab -l | grep "$BACKUP_SCRIPT"
    echo ""
    echo -n "是否替换? (yes/no): "
    read confirmation

    if [ "$confirmation" != "yes" ]; then
        echo "❌ 操作已取消"
        exit 0
    fi

    # 删除旧任务
    crontab -l | grep -v "$BACKUP_SCRIPT" | crontab -
    echo "✅ 已删除旧任务"
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 定时任务已添加!"
echo ""
echo "📋 定时任务详情:"
echo "  执行时间: 每天凌晨 2:00"
echo "  执行脚本: $BACKUP_SCRIPT"
echo "  日志文件: $LOG_DIR/auto_backup.log"
echo ""

# 显示当前所有定时任务
echo "📋 当前所有定时任务:"
crontab -l
echo ""

echo "✨ 设置完成!"
echo ""
echo "💡 提示:"
echo "  • 查看备份日志: tail -f $LOG_DIR/auto_backup.log"
echo "  • 查看所有备份: ./list_backups.sh"
echo "  • 手动备份: ./backup_database.sh"
echo "  • 恢复备份: ./restore_database.sh"
