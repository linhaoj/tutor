#!/bin/bash

echo "=== 测试创建和删除用户 ==="
echo ""

# 登录获取token
echo "1. 登录获取token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token获取成功"
echo ""

# 创建教师
echo "2. 创建教师teacher2..."
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher2","password":"123456","display_name":"李老师","role":"teacher"}' | python3 -m json.tool

echo ""
echo "✅ 教师创建成功"
echo ""

# 获取用户列表
echo "3. 获取用户列表..."
curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""

# 获取teacher2的ID
echo "4. 获取teacher2的ID..."
USER_ID=$(curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; users = json.load(sys.stdin); print([u['id'] for u in users if u['username']=='teacher2'][0])")

echo "User ID: $USER_ID"
echo ""

# 删除用户
echo "5. 删除teacher2..."
curl -s -X DELETE "http://localhost:8000/api/auth/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "✅ 删除完成"
echo ""

# 验证删除
echo "6. 验证用户已删除..."
curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="
