#!/bin/bash

# 修复所有使用不存在store方法的Vue文件

cd /Users/laovexl/Downloads/tutor/frontend/src/views

echo "开始修复store方法调用..."

# 1. 替换 getWordsBySetForUser - 需要使用getWordsBySet异步方法
files_with_getWordsBySetForUser=$(grep -l "getWordsBySetForUser" *.vue 2>/dev/null || true)

if [ ! -z "$files_with_getWordsBySetForUser" ]; then
  echo "发现使用 getWordsBySetForUser 的文件:"
  echo "$files_with_getWordsBySetForUser"
  echo ""
  echo "注意: getWordsBySetForUser需要手动检查和修复,因为它需要async/await"
fi

# 2. 替换 getWordSetsByUserId - 替换为 wordsStore.wordSets
echo "修复 getWordSetsByUserId..."
sed -i '' 's/wordsStore\.getWordSetsByUserId([^)]*)/wordsStore.wordSets/g' *.vue

# 3. 替换 getStudentsByUserId - 替换为 studentsStore.students
echo "修复 getStudentsByUserId..."
sed -i '' 's/studentsStore\.getStudentsByUserId([^)]*)/studentsStore.students/g' *.vue

# 4. 替换 getGroupedSchedulesByUserId - 替换为 scheduleStore.getGroupedSchedules
echo "修复 getGroupedSchedulesByUserId..."
sed -i '' 's/scheduleStore\.getGroupedSchedulesByUserId([^)]*)/scheduleStore.getGroupedSchedules/g' *.vue

echo ""
echo "修复完成!"
echo "请检查以下文件中的 getWordsBySetForUser 调用,可能需要手动修改:"
echo "$files_with_getWordsBySetForUser"
