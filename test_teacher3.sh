#!/bin/bash

echo "=== 测试创建教师3 ==="
echo ""

# 登录获取token
echo "1. 登录获取token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token获取成功"
echo ""

# 创建教师3
echo "2. 创建教师teacher3..."
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher3","password":"123456","display_name":"王老师","role":"teacher"}' | python3 -m json.tool

echo ""
echo "✅ 教师创建成功"
echo ""

# 获取用户列表
echo "3. 获取所有用户列表..."
curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="
