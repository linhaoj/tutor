#!/bin/bash

# 系统监控脚本

echo "=== 英语陪练系统运行状态监控 ==="
echo "监控时间: $(date)"
echo ""

# 检查PM2服务状态
echo "1. PM2服务状态："
pm2 status 2>/dev/null || echo "PM2未运行或未安装"
echo ""

# 检查Nginx状态
echo "2. Nginx状态："
systemctl status nginx --no-pager -l | head -3
echo ""

# 检查端口监听
echo "3. 端口监听状态："
echo "80端口:" && netstat -tlnp | grep :80 | head -1
echo "443端口:" && netstat -tlnp | grep :443 | head -1
echo "8000端口:" && netstat -tlnp | grep :8000 | head -1
echo ""

# 检查磁盘使用率
echo "4. 磁盘使用率："
df -h / | tail -1
echo ""

# 检查内存使用
echo "5. 内存使用："
free -h | head -2
echo ""

# 检查CPU负载
echo "6. CPU负载："
uptime
echo ""

# 检查日志文件大小
echo "7. 日志文件大小："
echo "Nginx访问日志:" && du -sh /var/log/nginx/tutor_access.log 2>/dev/null || echo "日志文件不存在"
echo "Nginx错误日志:" && du -sh /var/log/nginx/tutor_error.log 2>/dev/null || echo "日志文件不存在"
echo "PM2日志:" && du -sh /var/log/pm2/ 2>/dev/null || echo "PM2日志目录不存在"
echo ""

# 检查最近的错误日志
echo "8. 最近的Nginx错误日志（最后10行）："
tail -10 /var/log/nginx/tutor_error.log 2>/dev/null || echo "无错误日志或文件不存在"
echo ""

# 服务健康检查
echo "9. 服务健康检查："
echo "后端API健康检查:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null && echo "后端服务正常" || echo "后端服务异常"

echo "前端页面检查:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null && echo "前端服务正常" || echo "前端服务异常"

echo ""
echo "=== 监控完成 ==="