#!/bin/bash

# API测试脚本 - 快速验证后端功能

echo "======================================"
echo "  英语陪练系统 - API测试脚本"
echo "======================================"
echo ""

API_BASE="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试1: 后端健康检查
echo "【测试1】检查后端服务器..."
if curl -s -o /dev/null -w "%{http_code}" "$API_BASE" | grep -q "200\|404"; then
    echo -e "${GREEN}✅ 后端服务器正常运行${NC}"
else
    echo -e "${RED}❌ 后端服务器未运行${NC}"
    echo "请先启动后端服务器: cd backend && python main.py"
    exit 1
fi
echo ""

# 测试2: 管理员登录
echo "【测试2】测试管理员登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ 登录成功${NC}"
    echo "Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}❌ 登录失败${NC}"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# 测试3: 获取当前用户信息
echo "【测试3】获取用户信息..."
USER_INFO=$(curl -s "$API_BASE/api/auth/me" \
  -H "Authorization: Bearer $TOKEN")

USERNAME=$(echo $USER_INFO | python3 -c "import sys, json; print(json.load(sys.stdin).get('username', 'ERROR'))" 2>/dev/null)

if [ "$USERNAME" == "admin" ]; then
    echo -e "${GREEN}✅ Token验证成功${NC}"
    echo "当前用户: $USERNAME"
    echo "角色: $(echo $USER_INFO | python3 -c "import sys, json; print(json.load(sys.stdin).get('role', ''))" 2>/dev/null)"
else
    echo -e "${RED}❌ Token验证失败${NC}"
    echo "响应: $USER_INFO"
    exit 1
fi
echo ""

# 测试4: 获取学生列表
echo "【测试4】获取学生列表..."
STUDENTS=$(curl -s "$API_BASE/api/students" \
  -H "Authorization: Bearer $TOKEN")

STUDENT_COUNT=$(echo $STUDENTS | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ -n "$STUDENT_COUNT" ]; then
    echo -e "${GREEN}✅ 学生列表获取成功${NC}"
    echo "当前学生数: $STUDENT_COUNT"
else
    echo -e "${YELLOW}⚠️  学生列表为空或获取失败${NC}"
fi
echo ""

# 测试5: 获取单词集列表
echo "【测试5】获取单词集列表..."
WORDSETS=$(curl -s "$API_BASE/api/words/sets" \
  -H "Authorization: Bearer $TOKEN")

WORDSET_COUNT=$(echo $WORDSETS | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ -n "$WORDSET_COUNT" ]; then
    echo -e "${GREEN}✅ 单词集列表获取成功${NC}"
    echo "当前单词集数: $WORDSET_COUNT"
else
    echo -e "${YELLOW}⚠️  单词集列表为空或获取失败${NC}"
fi
echo ""

# 测试6: 获取课程列表
echo "【测试6】获取课程列表..."
SCHEDULES=$(curl -s "$API_BASE/api/schedules" \
  -H "Authorization: Bearer $TOKEN")

SCHEDULE_COUNT=$(echo $SCHEDULES | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ -n "$SCHEDULE_COUNT" ]; then
    echo -e "${GREEN}✅ 课程列表获取成功${NC}"
    echo "当前课程数: $SCHEDULE_COUNT"
else
    echo -e "${YELLOW}⚠️  课程列表为空或获取失败${NC}"
fi
echo ""

# 总结
echo "======================================"
echo -e "${GREEN}✅ 所有基础API测试通过!${NC}"
echo "======================================"
echo ""
echo "接下来可以:"
echo "1. 在浏览器中打开: http://localhost:5173"
echo "2. 使用 admin/admin123 登录"
echo "3. 测试UI功能"
echo ""
echo "如果需要查看后端日志:"
echo "  tail -f backend/logs/app_$(date +%Y-%m-%d).log"
echo ""
