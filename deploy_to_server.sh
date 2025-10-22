#!/bin/bash

# 部署到服务器脚本
# 用途：一键部署代码到生产服务器
# 使用方法：./deploy_to_server.sh

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器信息
SERVER="root@47.108.248.168"
SERVER_PATH="/var/www/tutor"

echo -e "${BLUE}🚀 部署英语陪练系统到生产服务器${NC}"
echo "================================"
echo ""

# 检查1: 确认当前在正确的目录
if [ ! -f "package.json" ] && [ ! -d "backend" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查2: 确认git状态
echo -e "${YELLOW}📋 检查Git状态...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  警告: 有未提交的更改${NC}"
    git status --short
    echo ""
    echo -n "是否继续部署? (yes/no): "
    read confirmation
    if [ "$confirmation" != "yes" ]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 0
    fi
fi

# 检查3: 确认要部署的分支
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}✅ 当前分支: $CURRENT_BRANCH${NC}"
echo ""

# 步骤1: 提交代码到Git（如果有更改）
if ! git diff-index --quiet HEAD --; then
    echo -e "${BLUE}📝 提交代码到Git...${NC}"
    echo -n "请输入提交信息: "
    read commit_message
    git add .
    git commit -m "$commit_message"
    echo -e "${GREEN}✅ 代码已提交${NC}"
fi

# 步骤2: 推送到远程仓库
echo ""
echo -e "${BLUE}📤 推送代码到远程仓库...${NC}"
git push origin $CURRENT_BRANCH
echo -e "${GREEN}✅ 代码已推送${NC}"

# 步骤3: 构建前端
echo ""
echo -e "${BLUE}🔨 构建前端...${NC}"
cd frontend
npm run build-only
echo -e "${GREEN}✅ 前端构建完成${NC}"
cd ..

# 步骤4: 连接服务器并备份数据库
echo ""
echo -e "${BLUE}💾 备份服务器数据库...${NC}"
ssh $SERVER "cd $SERVER_PATH/backend && ./backup_database.sh pre_deploy_$(date +%Y%m%d_%H%M%S) '部署前自动备份'"
echo -e "${GREEN}✅ 数据库备份完成${NC}"

# 步骤5: 停止服务器服务
echo ""
echo -e "${BLUE}🛑 停止服务器服务...${NC}"
ssh $SERVER "cd $SERVER_PATH && pm2 stop all"
echo -e "${GREEN}✅ 服务已停止${NC}"

# 步骤6: 拉取最新代码
echo ""
echo -e "${BLUE}📥 拉取最新代码到服务器...${NC}"
ssh $SERVER "cd $SERVER_PATH && git pull origin $CURRENT_BRANCH"
echo -e "${GREEN}✅ 代码已更新${NC}"

# 步骤7: 更新Python依赖（如果requirements.txt有变化）
echo ""
echo -e "${BLUE}📦 检查Python依赖...${NC}"
ssh $SERVER "cd $SERVER_PATH/backend && source venv/bin/activate && pip install -r requirements.txt --quiet"
echo -e "${GREEN}✅ Python依赖已更新${NC}"

# 步骤8: 重新构建前端（在服务器上）
echo ""
echo -e "${BLUE}🔨 在服务器上重新构建前端...${NC}"
ssh $SERVER "cd $SERVER_PATH/frontend && npm run build-only"
echo -e "${GREEN}✅ 服务器前端构建完成${NC}"

# 步骤9: 重启服务
echo ""
echo -e "${BLUE}🚀 重启服务器服务...${NC}"
ssh $SERVER "cd $SERVER_PATH && pm2 restart all"
sleep 3
ssh $SERVER "pm2 status"
echo -e "${GREEN}✅ 服务已重启${NC}"

# 步骤10: 验证部署
echo ""
echo -e "${BLUE}🔍 验证部署...${NC}"
echo "正在检查网站是否可访问..."

# 检查网站是否可访问
if curl -s -o /dev/null -w "%{http_code}" http://47.108.248.168:5173 | grep -q "200"; then
    echo -e "${GREEN}✅ 网站访问正常${NC}"
else
    echo -e "${YELLOW}⚠️  警告: 网站可能无法访问，请手动检查${NC}"
fi

# 完成
echo ""
echo "================================"
echo -e "${GREEN}✨ 部署完成！${NC}"
echo ""
echo "📋 部署信息:"
echo "  • 服务器: http://47.108.248.168:5173"
echo "  • 分支: $CURRENT_BRANCH"
echo "  • 时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "💡 后续操作:"
echo "  • 访问网站测试功能是否正常"
echo "  • 查看服务器日志: ssh $SERVER 'tail -f $SERVER_PATH/backend/logs/app_*.log'"
echo "  • 如有问题，恢复备份: ssh $SERVER 'cd $SERVER_PATH/backend && ./restore_database.sh'"
echo ""
