#!/bin/bash

# 服务启动脚本
# 使用PM2管理前后端进程

PROJECT_PATH="/var/www/tutor"
BACKEND_PORT=8000

echo "=== 启动英语陪练系统服务 ==="

# 检查PM2是否安装
if ! command -v pm2 &> /dev/null; then
    echo "安装PM2..."
    npm install -g pm2
fi

# 启动后端服务
echo "1. 启动后端服务..."
cd $PROJECT_PATH/backend
pm2 start --name "tutor-backend" --interpreter python3 main.py -- --host 0.0.0.0 --port $BACKEND_PORT

# 使用nginx服务静态前端文件（推荐）
echo "2. 前端文件已构建到 frontend/dist 目录"
echo "   请确保Nginx配置正确指向该目录"

# 显示服务状态
echo ""
echo "3. 服务状态："
pm2 status

echo ""
echo "=== 服务启动完成 ==="
echo ""
echo "后端API: http://localhost:$BACKEND_PORT"
echo "前端需要通过Nginx访问"
echo ""
echo "常用命令："
echo "- 查看服务状态: pm2 status"
echo "- 重启后端: pm2 restart tutor-backend"
echo "- 查看日志: pm2 logs tutor-backend"
echo "- 停止服务: pm2 stop tutor-backend"
echo ""