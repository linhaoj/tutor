#!/bin/bash

echo "=== 英语陪练系统服务器环境检查 ==="
echo ""

# 检查操作系统
echo "1. 操作系统信息："
cat /etc/os-release 2>/dev/null || echo "无法获取操作系统信息"
echo ""

# 检查Python版本
echo "2. Python版本："
python3 --version 2>/dev/null || echo "Python3 未安装"
echo ""

# 检查pip版本
echo "3. pip版本："
pip3 --version 2>/dev/null || echo "pip3 未安装"
echo ""

# 检查Node.js版本
echo "4. Node.js版本："
node --version 2>/dev/null || echo "Node.js 未安装"
echo ""

# 检查npm版本
echo "5. npm版本："
npm --version 2>/dev/null || echo "npm 未安装"
echo ""

# 检查Git版本
echo "6. Git版本："
git --version 2>/dev/null || echo "Git 未安装"
echo ""

# 检查Nginx版本
echo "7. Nginx版本："
nginx -v 2>/dev/null || echo "Nginx 未安装"
echo ""

# 检查PM2版本
echo "8. PM2版本："
pm2 --version 2>/dev/null || echo "PM2 未安装"
echo ""

# 检查防火墙状态
echo "9. 防火墙状态："
systemctl status firewalld 2>/dev/null | grep Active || echo "firewalld 未运行或未安装"
echo ""

# 检查端口占用情况
echo "10. 关键端口占用情况："
echo "端口 80:" && netstat -tlnp | grep :80 2>/dev/null || echo "端口 80 未被占用"
echo "端口 443:" && netstat -tlnp | grep :443 2>/dev/null || echo "端口 443 未被占用"
echo "端口 5173:" && netstat -tlnp | grep :5173 2>/dev/null || echo "端口 5173 未被占用"
echo "端口 8000:" && netstat -tlnp | grep :8000 2>/dev/null || echo "端口 8000 未被占用"
echo ""

echo "=== 环境检查完成 ==="
echo ""
echo "所需环境要求："
echo "- Python 3.8+"
echo "- Node.js 20+"
echo "- nginx"
echo "- pm2 (可选，用于进程管理)"
echo ""
echo "如果缺少上述软件，请先安装再进行部署。"