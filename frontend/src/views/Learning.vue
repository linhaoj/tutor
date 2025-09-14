<template>
  <div class="learning-center">
    <div class="page-header">
      <h1>学习中心</h1>
      <p>选择学生并开始背单词学习</p>
    </div>

    <!-- 学生选择卡片 -->
    <div class="students-grid">
      <el-card 
        v-for="student in students" 
        :key="student.id"
        class="student-card"
        shadow="hover"
      >
        <div class="student-info">
          <div class="student-header">
            <h3>{{ student.name }}</h3>
            <el-tag v-if="student.email" size="small">{{ student.email }}</el-tag>
          </div>
          
          <div class="student-stats">
            <div class="stat-item">
              <span class="stat-label">总单词数:</span>
              <span class="stat-value">{{ student.total_words }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已学单词:</span>
              <span class="stat-value">{{ student.learned_words }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">学习进度:</span>
              <el-progress 
                :percentage="getProgressPercentage(student)" 
                :stroke-width="6"
                :show-text="false"
              />
            </div>
          </div>

          <!-- 九宫格显示 -->
          <div v-if="studentGridStats[student.id]" class="grid-display">
            <h4>单词分布</h4>
            <div class="grid-container">
              <div 
                v-for="i in 9" 
                :key="i-1"
                class="grid-cell"
                :class="getGridCellClass(i-1)"
              >
                <div class="grid-number">{{ i-1 }}</div>
                <div class="grid-count">{{ studentGridStats[student.id][`grid_${i-1}` as keyof GridStats] || 0 }}</div>
              </div>
            </div>
            <div class="grid-legend">
              <span class="legend-item">
                <span class="legend-color unlearned"></span>
                未学 (0)
              </span>
              <span class="legend-item">
                <span class="legend-color learning"></span>
                学习中 (1-7)
              </span>
              <span class="legend-item">
                <span class="legend-color mastered"></span>
                已掌握 (8)
              </span>
            </div>
          </div>

          <div class="student-actions">
            <el-button 
              type="primary" 
              @click="showStartDialog(student)"
              :disabled="student.total_words === 0"
            >
              开始学习
            </el-button>
            <el-button 
              type="info" 
              @click="viewStudentDetail(student.id)"
            >
              查看详情
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 开始学习对话框 -->
    <el-dialog 
      v-model="startDialogVisible" 
      title="开始学习" 
      width="500px"
    >
      <div v-if="selectedStudent" class="start-dialog-content">
        <h3>{{ selectedStudent.name }} - 开始新的学习会话</h3>
        
        <div class="form-group">
          <label>选择学习单词数量:</label>
          <el-select v-model="selectedWordsCount" placeholder="请选择">
            <el-option label="5个单词" :value="5" />
            <el-option label="10个单词" :value="10" />
            <el-option label="15个单词" :value="15" />
            <el-option label="20个单词" :value="20" />
            <el-option label="自定义" :value="0" />
          </el-select>
        </div>

        <div v-if="selectedWordsCount === 0" class="form-group">
          <label>自定义数量:</label>
          <el-input-number 
            v-model="customWordsCount" 
            :min="1" 
            :max="availableWordsCount"
            placeholder="输入数量"
          />
        </div>

        <div class="available-info">
          <el-alert
            :title="`可学习单词: ${availableWordsCount} 个`"
            type="info"
            :closable="false"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="startDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="startLearningSession"
          :loading="startingSession"
        >
          开始学习
        </el-button>
      </template>
    </el-dialog>

    <!-- 学习历史 -->
    <div class="learning-history">
      <h2>最近学习记录</h2>
      <el-table :data="recentSessions" style="width: 100%">
        <el-table-column prop="student_name" label="学生" width="120" />
        <el-table-column prop="session_date" label="学习日期" width="120" />
        <el-table-column prop="words_count" label="单词数量" width="100" />
        <el-table-column prop="completed" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.completed ? 'success' : 'warning'">
              {{ scope.row.completed ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="开始时间" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studentAPI, learningAPI, type Student, type GridStats } from '@/api'

const router = useRouter()

// 响应式数据
const students = ref<Student[]>([])
const studentGridStats = ref<Record<number, GridStats>>({})
const recentSessions = ref<any[]>([])

// 对话框相关
const startDialogVisible = ref(false)
const selectedStudent = ref<Student | null>(null)
const selectedWordsCount = ref(10)
const customWordsCount = ref(10)
const startingSession = ref(false)

// 计算属性
const availableWordsCount = computed(() => {
  if (!selectedStudent.value) return 0
  const stats = studentGridStats.value[selectedStudent.value.id]
  if (!stats) return 0
  
  // 计算格子0-7的单词总数（可学习的单词）
  let count = 0
  for (let i = 0; i <= 7; i++) {
    count += stats[`grid_${i}` as keyof GridStats] || 0
  }
  return count
})

// 方法
const getProgressPercentage = (student: Student) => {
  if (student.total_words === 0) return 0
  return Math.round((student.learned_words / student.total_words) * 100)
}

const getGridCellClass = (position: number) => {
  if (position === 0) return 'unlearned'
  if (position >= 1 && position <= 7) return 'learning'
  if (position === 8) return 'mastered'
  return ''
}

const showStartDialog = async (student: Student) => {
  selectedStudent.value = student
  
  // 获取该学生的九宫格统计（如果还没有的话）
  if (!studentGridStats.value[student.id]) {
    try {
      const stats = await learningAPI.getGridStats(student.id)
      studentGridStats.value[student.id] = stats
    } catch (error) {
      ElMessage.error('获取学生学习统计失败')
      return
    }
  }
  
  startDialogVisible.value = true
}

const startLearningSession = async () => {
  if (!selectedStudent.value) return
  
  const wordsCount = selectedWordsCount.value === 0 ? customWordsCount.value : selectedWordsCount.value
  
  if (wordsCount > availableWordsCount.value) {
    ElMessage.error(`可学习单词不足，最多只能选择${availableWordsCount.value}个单词`)
    return
  }
  
  startingSession.value = true
  
  try {
    const session = await learningAPI.startSession({
      student_id: selectedStudent.value.id,
      words_count: wordsCount
    })
    
    // 跳转到学习页面，并传递会话信息
    router.push({
      name: 'WordStudy',
      params: { studentId: selectedStudent.value.id },
      query: { sessionId: session.id }
    })
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '开始学习失败')
  } finally {
    startingSession.value = false
    startDialogVisible.value = false
  }
}

const viewStudentDetail = (studentId: number) => {
  router.push(`/students/${studentId}`)
}

const loadStudents = async () => {
  try {
    students.value = await studentAPI.getStudents()
    
    // 为每个学生获取九宫格统计
    for (const student of students.value) {
      try {
        const stats = await learningAPI.getGridStats(student.id)
        studentGridStats.value[student.id] = stats
      } catch (error) {
        console.error(`获取学生${student.id}的统计失败:`, error)
      }
    }
  } catch (error) {
    ElMessage.error('加载学生列表失败')
  }
}

const loadRecentSessions = async () => {
  try {
    // 这里应该有一个获取所有最近会话的API
    // 暂时模拟数据
    recentSessions.value = []
  } catch (error) {
    console.error('加载学习历史失败:', error)
  }
}

// 生命周期
onMounted(() => {
  loadStudents()
  loadRecentSessions()
})
</script>

<style scoped>
.learning-center {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  color: #303133;
  margin-bottom: 10px;
}

.page-header p {
  color: #606266;
  font-size: 16px;
}

.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.student-card {
  transition: all 0.3s ease;
}

.student-card:hover {
  transform: translateY(-4px);
}

.student-info {
  padding: 10px;
}

.student-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.student-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.student-stats {
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  color: #303133;
}

.grid-display {
  margin-bottom: 20px;
}

.grid-display h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  margin-bottom: 12px;
}

.grid-cell {
  aspect-ratio: 1;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.grid-cell.unlearned {
  background-color: #f5f7fa;
  color: #909399;
}

.grid-cell.learning {
  background-color: #e6f7ff;
  color: #1890ff;
}

.grid-cell.mastered {
  background-color: #f6ffed;
  color: #52c41a;
}

.grid-number {
  font-size: 10px;
  opacity: 0.8;
}

.grid-count {
  font-size: 14px;
  font-weight: bold;
}

.grid-legend {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.unlearned {
  background-color: #f5f7fa;
  border: 1px solid #909399;
}

.legend-color.learning {
  background-color: #e6f7ff;
  border: 1px solid #1890ff;
}

.legend-color.mastered {
  background-color: #f6ffed;
  border: 1px solid #52c41a;
}

.student-actions {
  display: flex;
  gap: 12px;
}

.student-actions .el-button {
  flex: 1;
}

.start-dialog-content h3 {
  margin: 0 0 20px 0;
  color: #303133;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #606266;
  font-size: 14px;
}

.available-info {
  margin-top: 20px;
}

.learning-history {
  margin-top: 40px;
}

.learning-history h2 {
  color: #303133;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .students-grid {
    grid-template-columns: 1fr;
  }
  
  .student-actions {
    flex-direction: column;
  }
  
  .grid-legend {
    flex-direction: column;
    gap: 8px;
  }
}
</style>