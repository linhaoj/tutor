<template>
  <div class="students-page">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加学生
      </el-button>
    </div>

    <!-- 学生列表 -->
    <el-table :data="studentsStore.students" style="width: 100%" v-loading="studentsStore.loading">
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="剩余课时" width="120">
        <template #default="scope">
          <span :class="getHoursClass(scope.row.remaining_hours)">
            {{ scope.row.remaining_hours.toFixed(1) }}h
          </span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="scope">
          <el-button size="small" @click="viewProgress(scope.row)">查看进度</el-button>
          <el-button size="small" @click="editStudent(scope.row)">编辑</el-button>
          <el-button
            size="small"
            type="danger"
            @click="deleteStudent(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑学生对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑学生信息' : '添加学生'"
      width="450px"
    >
      <el-form :model="studentForm" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="studentForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-form-item label="剩余课时">
          <el-input-number
            v-model="studentForm.remaining_hours"
            :precision="1"
            :step="0.5"
            :min="0"
            :max="1000"
            :disabled="!authStore.isAdmin"
            placeholder="剩余课程时长（小时）"
            style="width: 100%"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            <template v-if="authStore.isAdmin">
              大课60分钟 = 1.0h，小课30分钟 = 0.5h
            </template>
            <template v-else>
              <span style="color: #f56c6c;">⚠️ 只有管理员可以修改课时</span>
            </template>
          </div>
        </el-form-item>

        <!-- 管理员可以为其他教师创建学生 -->
        <el-form-item v-if="authStore.isAdmin && !isEditing" label="所属教师">
          <el-select v-model="studentForm.teacher_id" placeholder="选择教师" style="width: 100%">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.display_name"
              :value="teacher.id"
            />
          </el-select>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            留空则为当前登录用户创建学生
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStudent" :loading="saving">
          {{ isEditing ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看学习进度对话框 -->
    <el-dialog
      v-model="progressDialogVisible"
      :title="`${selectedStudent?.name} - 学习进度`"
      width="900px"
      @close="closeProgressDialog"
    >
      <div class="progress-dialog-content">
        <!-- 词库选择器 -->
        <div class="word-set-selector">
          <el-form-item label="选择词库：" label-width="100px">
            <el-select
              v-model="selectedWordSet"
              placeholder="请选择词库"
              @change="loadGridStats"
              style="width: 300px"
            >
              <el-option
                v-for="wordSet in studentWordSets"
                :key="wordSet"
                :label="wordSet"
                :value="wordSet"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 九宫格统计 -->
        <div v-if="selectedWordSet" class="grid-stats">
          <h3>{{ selectedWordSet }} - 学习进度统计</h3>
          <div class="grid-container">
            <div
              v-for="i in 9"
              :key="i"
              class="grid-cell"
              :class="`stage-${i-1}`"
            >
              <div class="grid-number">格子 {{ i-1 }}</div>
              <div class="grid-count">{{ gridStats[`grid_${i-1}`] || 0 }}</div>
              <div class="grid-label">{{ getGridLabel(i-1) }}</div>
            </div>
          </div>

          <!-- 总计信息 -->
          <div class="stats-summary">
            <el-descriptions :column="3" border>
              <el-descriptions-item label="总单词数">
                {{ totalWords }}
              </el-descriptions-item>
              <el-descriptions-item label="未学习">
                {{ gridStats.grid_0 || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="学习中">
                {{ learningWords }}
              </el-descriptions-item>
              <el-descriptions-item label="已掌握" :span="3">
                {{ masteredWords }} ({{ masteredPercentage }}%)
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 未选择词库提示 -->
        <div v-else class="empty-hint">
          <el-empty description="请选择一个词库查看学习进度" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useStudentsStore } from '../stores/students'
import { useAuthStore } from '../stores/auth'
import { useWordsStore } from '../stores/words'
import { useLearningProgressStore } from '../stores/learningProgress'

const studentsStore = useStudentsStore()
const authStore = useAuthStore()
const wordsStore = useWordsStore()
const progressStore = useLearningProgressStore()

const dialogVisible = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const teachers = ref<any[]>([])

const studentForm = ref({
  id: 0,
  name: '',
  email: '',
  remaining_hours: 0,
  teacher_id: ''
})

// 查看进度相关
const progressDialogVisible = ref(false)
const selectedStudent = ref<any>(null)
const selectedWordSet = ref('')
const studentWordSets = ref<string[]>([])
const gridStats = ref<Record<string, number>>({
  grid_0: 0,
  grid_1: 0,
  grid_2: 0,
  grid_3: 0,
  grid_4: 0,
  grid_5: 0,
  grid_6: 0,
  grid_7: 0,
  grid_8: 0
})

// 九宫格计算属性
const totalWords = computed(() => {
  return Object.values(gridStats.value).reduce((sum, count) => sum + count, 0)
})

const learningWords = computed(() => {
  let count = 0
  for (let i = 1; i <= 7; i++) {
    count += gridStats.value[`grid_${i}`] || 0
  }
  return count
})

const masteredWords = computed(() => {
  // 格子8是已掌握（预留），格子7也算已掌握
  return (gridStats.value.grid_7 || 0) + (gridStats.value.grid_8 || 0)
})

const masteredPercentage = computed(() => {
  if (totalWords.value === 0) return 0
  return Math.round((masteredWords.value / totalWords.value) * 100)
})

const getGridLabel = (index: number) => {
  const labels = [
    '未学习',
    '阶段1',
    '阶段2',
    '阶段3',
    '阶段4',
    '阶段5',
    '阶段6',
    '阶段7',
    '已掌握'
  ]
  return labels[index] || '未知'
}

const getHoursClass = (hours: number) => {
  if (!hours || hours <= 0) return 'hours-empty'
  if (hours <= 1) return 'hours-low'
  if (hours <= 5) return 'hours-medium'
  return 'hours-high'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const showAddDialog = async () => {
  isEditing.value = false
  studentForm.value = {
    id: 0,
    name: '',
    email: '',
    remaining_hours: 0,
    teacher_id: ''
  }

  // 如果是管理员，加载教师列表
  if (authStore.isAdmin) {
    const users = await authStore.getAllUsers()
    teachers.value = users.filter((u: any) => u.role === 'teacher')
  }

  dialogVisible.value = true
}

const editStudent = (student: any) => {
  isEditing.value = true
  studentForm.value = {
    id: student.id,
    name: student.name,
    email: student.email || '',
    remaining_hours: student.remaining_hours,
    teacher_id: student.teacher_id
  }
  dialogVisible.value = true
}

const saveStudent = async () => {
  if (!studentForm.value.name) {
    ElMessage.error('请输入学生姓名')
    return
  }

  saving.value = true

  try {
    if (isEditing.value) {
      // 更新学生信息
      const result = await studentsStore.updateStudent(studentForm.value.id, {
        name: studentForm.value.name,
        email: studentForm.value.email || undefined,
        remaining_hours: studentForm.value.remaining_hours
      })

      if (result.success) {
        ElMessage.success('学生信息更新成功')
        dialogVisible.value = false
      } else {
        ElMessage.error(result.message)
      }
    } else {
      // 创建新学生
      const result = await studentsStore.addStudent({
        name: studentForm.value.name,
        email: studentForm.value.email || undefined,
        remaining_hours: studentForm.value.remaining_hours,
        teacher_id: studentForm.value.teacher_id || undefined
      })

      if (result.success) {
        ElMessage.success('学生添加成功')
        dialogVisible.value = false
      } else {
        ElMessage.error(result.message)
      }
    }
  } catch (error) {
    console.error('保存学生失败:', error)
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

const deleteStudent = async (student: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${student.name} 吗？这将删除该学生的所有学习数据。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const result = await studentsStore.deleteStudent(student.id)
    if (result.success) {
      ElMessage.success('学生删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消删除
  }
}

// 查看学生学习进度
const viewProgress = async (student: any) => {
  selectedStudent.value = student
  selectedWordSet.value = ''
  studentWordSets.value = []

  // 重置九宫格数据
  gridStats.value = {
    grid_0: 0,
    grid_1: 0,
    grid_2: 0,
    grid_3: 0,
    grid_4: 0,
    grid_5: 0,
    grid_6: 0,
    grid_7: 0,
    grid_8: 0
  }

  progressDialogVisible.value = true

  // 加载学生学习过的词库列表
  try {
    // 使用 fetchStudentProgress 获取学生所有学习进度（不传wordSetName）
    const allProgress = await progressStore.fetchStudentProgress(student.id)

    // 获取学生学习过的所有词库（有进度记录的词库）
    const wordSetsSet = new Set<string>()
    allProgress.forEach((progress: any) => {
      if (progress.word_set_name) {
        wordSetsSet.add(progress.word_set_name)
      }
    })

    studentWordSets.value = Array.from(wordSetsSet)

    if (studentWordSets.value.length === 0) {
      ElMessage.info('该学生还没有学习记录')
    }
  } catch (error) {
    console.error('加载学生词库列表失败:', error)
    ElMessage.error('加载词库列表失败')
  }
}

// 加载九宫格统计数据
const loadGridStats = async () => {
  if (!selectedStudent.value || !selectedWordSet.value) return

  try {
    const stats = await progressStore.getGridStats(
      selectedStudent.value.id,
      selectedWordSet.value
    )

    gridStats.value = stats
    console.log('九宫格统计数据:', stats)
  } catch (error) {
    console.error('加载九宫格统计失败:', error)
    ElMessage.error('加载学习进度失败')
  }
}

// 关闭进度对话框
const closeProgressDialog = () => {
  selectedStudent.value = null
  selectedWordSet.value = ''
  studentWordSets.value = []
  gridStats.value = {
    grid_0: 0,
    grid_1: 0,
    grid_2: 0,
    grid_3: 0,
    grid_4: 0,
    grid_5: 0,
    grid_6: 0,
    grid_7: 0,
    grid_8: 0
  }
}

onMounted(async () => {
  // 加载学生列表
  await studentsStore.fetchStudents()
})
</script>

<style scoped>
.students-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

/* 剩余时长颜色样式 */
.hours-empty {
  color: #f56c6c;
  font-weight: bold;
}

.hours-low {
  color: #e6a23c;
  font-weight: bold;
}

.hours-medium {
  color: #409eff;
  font-weight: bold;
}

.hours-high {
  color: #67c23a;
  font-weight: bold;
}

/* 学习进度对话框样式 */
.progress-dialog-content {
  min-height: 400px;
}

.word-set-selector {
  margin-bottom: 30px;
}

.grid-stats {
  margin-top: 20px;
}

.grid-stats h3 {
  color: #303133;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  max-width: 600px;
  margin-bottom: 30px;
}

.grid-cell {
  aspect-ratio: 1;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s ease;
}

.grid-cell:hover {
  transform: translateY(-2px);
}

/* 格子0：未学习 */
.grid-cell.stage-0 {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #606266;
}

/* 格子1-7：学习中 */
.grid-cell.stage-1,
.grid-cell.stage-2,
.grid-cell.stage-3,
.grid-cell.stage-4,
.grid-cell.stage-5,
.grid-cell.stage-6,
.grid-cell.stage-7 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 格子8：已掌握 */
.grid-cell.stage-8 {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.grid-number {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 5px;
}

.grid-count {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.grid-label {
  font-size: 12px;
  opacity: 0.9;
}

/* 统计总结样式 */
.stats-summary {
  margin-top: 30px;
}

.stats-summary :deep(.el-descriptions__title) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stats-summary :deep(.el-descriptions__body) {
  background: #f8f9fa;
}

.stats-summary :deep(.el-descriptions__label) {
  font-weight: 500;
  color: #606266;
}

.stats-summary :deep(.el-descriptions__content) {
  font-weight: 600;
  font-size: 16px;
  color: #409eff;
}

/* 空提示样式 */
.empty-hint {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
