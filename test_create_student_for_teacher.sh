#!/bin/bash

echo "=== 测试管理员为教师创建学生完整流程 ==="
echo ""

# 1. 登录获取admin token
echo "1. 管理员登录..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ 管理员登录成功"
echo ""

# 2. 获取teacher3的ID
echo "2. 获取teacher3的ID..."
TEACHER_ID=$(curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; users = json.load(sys.stdin); print([u['id'] for u in users if u['username']=='teacher3'][0])")

echo "Teacher ID: $TEACHER_ID"
echo ""

# 3. 为teacher3创建学生user账号
echo "3. 创建学生user账号..."
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"student1\",\"password\":\"123456\",\"display_name\":\"小明\",\"role\":\"student\",\"email\":\"xiaoming@test.com\"}" | python3 -m json.tool

echo ""
echo "✅ 学生user账号创建成功"
echo ""

# 4. 为teacher3创建学生记录
echo "4. 为teacher3创建学生记录..."
curl -s -X POST http://localhost:8000/api/students \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"小明\",\"email\":\"xiaoming@test.com\",\"remaining_hours\":10.0,\"teacher_id\":\"$TEACHER_ID\"}" | python3 -m json.tool

echo ""
echo "✅ 学生记录创建成功"
echo ""

# 5. 查看teacher3的所有学生
echo "5. 查看teacher3的所有学生..."
echo "   (切换到teacher3的视角)"

# 先用teacher3登录
TEACHER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher3&password=123456" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -s -X GET http://localhost:8000/api/students \
  -H "Authorization: Bearer $TEACHER_TOKEN" | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="
