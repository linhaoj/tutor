#!/bin/bash

# 英语陪练系统部署脚本
# 使用说明：bash deploy.sh [项目路径]

set -e  # 遇到错误立即退出

# 配置变量
PROJECT_NAME="tutor"
DEFAULT_PROJECT_PATH="/var/www/tutor"
PROJECT_PATH=${1:-$DEFAULT_PROJECT_PATH}
BACKEND_PORT=8000
FRONTEND_PORT=5173
DOMAIN=${2:-"your-domain.com"}

echo "=== 英语陪练系统部署开始 ==="
echo "项目路径: $PROJECT_PATH"
echo "后端端口: $BACKEND_PORT"
echo "前端端口: $FRONTEND_PORT"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 创建项目目录
echo "1. 创建项目目录..."
mkdir -p $PROJECT_PATH
cd $PROJECT_PATH

# 如果是更新部署，停止现有服务
echo "2. 停止现有服务..."
pm2 stop tutor-backend 2>/dev/null || echo "后端服务未运行"
pm2 stop tutor-frontend 2>/dev/null || echo "前端服务未运行"

# 检查是否已存在项目文件
if [ -d "$PROJECT_PATH/frontend" ] && [ -d "$PROJECT_PATH/backend" ]; then
    echo "3. 更新现有项目..."
    git pull origin main || echo "Git更新失败，请手动上传代码"
else
    echo "3. 首次部署，请手动上传项目文件到 $PROJECT_PATH"
    echo "   或者使用 git clone 你的仓库地址到此目录"
    read -p "   按回车键继续（确保项目文件已就位）..."
fi

# 安装后端依赖
echo "4. 安装后端依赖..."
cd $PROJECT_PATH/backend
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# 创建数据库（如果不存在）
echo "5. 初始化数据库..."
python3 -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('数据库初始化完成')
"

# 安装前端依赖并构建
echo "6. 安装前端依赖并构建..."
cd $PROJECT_PATH/frontend
npm install
npm run build

# 设置权限
echo "7. 设置文件权限..."
chown -R www-data:www-data $PROJECT_PATH
chmod -R 755 $PROJECT_PATH

echo ""
echo "=== 部署完成 ==="
echo ""
echo "下一步操作："
echo "1. 配置 Nginx（运行 setup_nginx.sh）"
echo "2. 启动服务（运行 start_services.sh）"
echo "3. 配置域名和SSL证书（可选）"
echo ""