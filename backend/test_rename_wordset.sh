#!/bin/bash

# 测试单词集重命名API
BASE_URL="http://localhost:8000"

echo "=== 测试单词集重命名功能 ==="
echo ""

# 1. 登录获取token
echo "1. 登录管理员账号..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ 登录成功，获取到token"
echo ""

# 2. 获取所有单词集
echo "2. 获取所有单词集..."
WORDSETS=$(curl -s -X GET "${BASE_URL}/api/words/sets" \
  -H "Authorization: Bearer $TOKEN")

echo "当前单词集:"
echo "$WORDSETS" | python3 -m json.tool
echo ""

# 3. 创建测试单词集
echo "3. 创建测试单词集 'TestWordSet'..."
CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/words/sets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "TestWordSet", "is_global": true}')

echo "$CREATE_RESPONSE" | python3 -m json.tool
echo ""

# 4. 测试重命名 - 正常情况
echo "4. 重命名 'TestWordSet' 为 'RenamedWordSet'..."
RENAME_RESPONSE=$(curl -s -X PUT "${BASE_URL}/api/words/sets/TestWordSet/rename" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_name": "RenamedWordSet"}')

echo "$RENAME_RESPONSE" | python3 -m json.tool
echo ""

# 5. 验证重命名是否成功
echo "5. 验证重命名结果..."
WORDSETS_AFTER=$(curl -s -X GET "${BASE_URL}/api/words/sets" \
  -H "Authorization: Bearer $TOKEN")

if echo "$WORDSETS_AFTER" | grep -q "RenamedWordSet"; then
  echo "✅ 重命名成功！找到 'RenamedWordSet'"
else
  echo "❌ 重命名失败！未找到 'RenamedWordSet'"
fi
echo ""

# 6. 测试重命名 - 重复名称（应该失败）
echo "6. 测试重命名为已存在的名称（应该失败）..."
if echo "$WORDSETS_AFTER" | grep -q "Sheet1"; then
  DUPLICATE_RESPONSE=$(curl -s -X PUT "${BASE_URL}/api/words/sets/RenamedWordSet/rename" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"new_name": "Sheet1"}')

  echo "$DUPLICATE_RESPONSE" | python3 -m json.tool

  if echo "$DUPLICATE_RESPONSE" | grep -q "已存在"; then
    echo "✅ 正确阻止了重复名称"
  else
    echo "⚠️  未能阻止重复名称"
  fi
else
  echo "⏭️  跳过测试（没有Sheet1单词集）"
fi
echo ""

# 7. 测试重命名 - 空名称（应该失败）
echo "7. 测试空名称（应该失败）..."
EMPTY_RESPONSE=$(curl -s -X PUT "${BASE_URL}/api/words/sets/RenamedWordSet/rename" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_name": ""}')

echo "$EMPTY_RESPONSE" | python3 -m json.tool

if echo "$EMPTY_RESPONSE" | grep -q "不能为空"; then
  echo "✅ 正确阻止了空名称"
else
  echo "⚠️  未能阻止空名称"
fi
echo ""

# 8. 清理测试数据
echo "8. 清理测试数据..."
DELETE_RESPONSE=$(curl -s -X DELETE "${BASE_URL}/api/words/sets/RenamedWordSet" \
  -H "Authorization: Bearer $TOKEN")

echo "$DELETE_RESPONSE" | python3 -m json.tool
echo ""

echo "=== 测试完成 ==="
