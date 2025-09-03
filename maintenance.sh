#!/bin/bash

# 系统维护脚本

PROJECT_PATH="/var/www/tutor"
BACKUP_PATH="/backup/tutor"
LOG_RETENTION_DAYS=30

echo "=== 英语陪练系统维护 ==="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 创建备份目录
mkdir -p $BACKUP_PATH

# 数据库备份
echo "1. 备份数据库..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp $PROJECT_PATH/backend/tutor.db $BACKUP_PATH/tutor_${BACKUP_DATE}.db 2>/dev/null || echo "数据库文件不存在，跳过备份"

# 清理旧的备份文件（保留7天）
echo "2. 清理旧备份文件..."
find $BACKUP_PATH -name "tutor_*.db" -mtime +7 -delete 2>/dev/null || echo "无旧备份文件需要清理"

# 清理日志文件
echo "3. 清理日志文件..."

# 清理Nginx日志
if [ -f "/var/log/nginx/tutor_access.log" ]; then
    # 保留最近的1000行，其余删除
    tail -1000 /var/log/nginx/tutor_access.log > /tmp/tutor_access.log
    mv /tmp/tutor_access.log /var/log/nginx/tutor_access.log
    echo "Nginx访问日志已清理"
fi

if [ -f "/var/log/nginx/tutor_error.log" ]; then
    tail -1000 /var/log/nginx/tutor_error.log > /tmp/tutor_error.log
    mv /tmp/tutor_error.log /var/log/nginx/tutor_error.log
    echo "Nginx错误日志已清理"
fi

# 清理PM2日志
pm2 flush 2>/dev/null && echo "PM2日志已清理" || echo "PM2日志清理失败"

# 重启服务（可选）
read -p "4. 是否重启服务？(y/N): " restart_choice
if [[ $restart_choice =~ ^[Yy]$ ]]; then
    echo "重启服务..."
    pm2 restart tutor-backend
    systemctl reload nginx
    echo "服务重启完成"
else
    echo "跳过服务重启"
fi

# 系统资源清理
echo "5. 清理系统临时文件..."
# 清理npm缓存
npm cache clean --force 2>/dev/null || echo "npm缓存清理失败"

# 清理pip缓存
pip3 cache purge 2>/dev/null || echo "pip缓存清理失败"

# 清理系统临时文件
find /tmp -type f -mtime +7 -delete 2>/dev/null || echo "临时文件清理完成"

# 系统包清理
apt autoremove -y 2>/dev/null && apt autoclean 2>/dev/null || echo "系统包清理完成"

echo ""
echo "=== 维护完成 ==="
echo ""
echo "备份位置: $BACKUP_PATH"
echo "数据库备份: tutor_${BACKUP_DATE}.db"
echo ""
echo "建议设置定期执行此脚本（如每周一次）："
echo "0 2 * * 0 /var/www/tutor/maintenance.sh"