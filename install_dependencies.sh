#!/bin/bash

# 依赖安装脚本 - 适用于Ubuntu/Debian系统

echo "=== 安装部署依赖 ==="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 更新系统包
echo "1. 更新系统包..."
apt update && apt upgrade -y

# 安装基础工具
echo "2. 安装基础工具..."
apt install -y curl wget git vim unzip

# 安装Python 3.8+
echo "3. 安装Python..."
apt install -y python3 python3-pip python3-venv python3-dev

# 安装Node.js 20.x
echo "4. 安装Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 安装Nginx
echo "5. 安装Nginx..."
apt install -y nginx

# 安装PM2（全局）
echo "6. 安装PM2..."
npm install -g pm2

# 配置防火墙（如果使用UFW）
echo "7. 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 22      # SSH
    ufw allow 80      # HTTP
    ufw allow 443     # HTTPS
    ufw --force enable
    echo "防火墙已配置：开放端口 22, 80, 443"
else
    echo "未检测到UFW防火墙，请手动配置防火墙规则"
fi

# 创建www-data用户目录
echo "8. 创建web目录..."
mkdir -p /var/www
chown -R www-data:www-data /var/www

# 显示安装结果
echo ""
echo "=== 依赖安装完成 ==="
echo ""
echo "已安装软件版本："
python3 --version
node --version
npm --version
nginx -v
pm2 --version

echo ""
echo "下一步："
echo "1. 上传项目代码到服务器"
echo "2. 运行 bash deploy.sh 进行部署"
echo ""