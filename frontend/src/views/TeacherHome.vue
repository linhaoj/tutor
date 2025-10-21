<template>
  <div class="teacher-home">
    <div class="page-header">
      <div class="header-left">
        <h1>教师工作台</h1>
        <el-tag type="success" size="large">教师</el-tag>
      </div>
      <div class="header-right">
        <span class="welcome-text">欢迎，{{ authStore.currentUser?.displayName }}</span>
        <el-dropdown @command="handleCommand">
          <el-button type="primary">
            <el-icon><Avatar /></el-icon>
            操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="teacher-content">
      <div class="stats-cards">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon students">
                  <el-icon><User /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ teacherStudents.length }}</div>
                  <div class="stat-label">我的学生</div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon wordsets">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ teacherWordSets.length }}</div>
                  <div class="stat-label">单词集</div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon schedules">
                  <el-icon><Calendar /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ teacherSchedules.length }}</div>
                  <div class="stat-label">课程安排</div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon today">
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ todaySchedules.length }}</div>
                  <div class="stat-label">今日课程</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div class="main-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>今日课程安排</span>
              </template>
              <div class="today-schedules">
                <div v-if="todaySchedules.length === 0" class="empty-state">
                  <el-empty description="今天没有课程安排" />
                </div>
                <div v-else>
                  <div 
                    v-for="schedule in todaySchedules" 
                    :key="schedule.id"
                    class="schedule-item"
                  >
                    <div class="schedule-time">{{ schedule.time }}</div>
                    <div class="schedule-content">
                      <div class="schedule-title">{{ schedule.wordSet }}</div>
                      <div class="schedule-student">{{ schedule.studentName }}</div>
                      <div class="schedule-type">
                        <el-tag 
                          :type="schedule.type === 'review' ? 'warning' : 'success'" 
                          size="small"
                        >
                          {{ schedule.type === 'review' ? '抗遗忘' : '单词学习' }}
                        </el-tag>
                      </div>
                    </div>
                    <div class="schedule-actions">
                      <el-button 
                        type="success" 
                        size="small"
                        @click="startLearning(schedule)"
                        :disabled="schedule.completed"
                      >
                        {{ schedule.completed ? '已完成' : '开始学习' }}
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>最近学习统计</span>
              </template>
              <div class="learning-stats">
                <div class="stat-item">
                  <div class="stat-label">本周完成课程</div>
                  <div class="stat-value">{{ weeklyCompletedCount }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">本月完成课程</div>
                  <div class="stat-value">{{ monthlyCompletedCount }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">总学习时长</div>
                  <div class="stat-value">{{ totalLearningHours }}小时</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div class="quick-actions">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="actions-grid">
            <el-button 
              type="primary" 
              size="large"
              @click="goToStats"
            >
              <el-icon><DataLine /></el-icon>
              查看统计
            </el-button>
            <el-button 
              type="success" 
              size="large"
              @click="contactAdmin"
            >
              <el-icon><ChatDotSquare /></el-icon>
              联系管理员
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Avatar, 
  ArrowDown, 
  User, 
  Document, 
  Calendar, 
  Clock,
  DataLine,
  ChatDotSquare
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'
import type { Student } from '@/stores/students'
import type { WordSet } from '@/stores/words'
import type { Schedule } from '@/stores/schedule'

const router = useRouter()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const wordsStore = useWordsStore()
const scheduleStore = useScheduleStore()

// 教师数据
const teacherStudents = ref<Student[]>([])
const teacherWordSets = ref<WordSet[]>([])
const teacherSchedules = ref<Schedule[]>([])

// 计算属性
const todaySchedules = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return teacherSchedules.value
    .filter(s => s.date === today)
    .sort((a, b) => a.time.localeCompare(b.time))
})

const weeklyCompletedCount = computed(() => {
  const oneWeekAgo = new Date()
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)
  const oneWeekAgoStr = oneWeekAgo.toISOString().split('T')[0]
  
  return teacherSchedules.value.filter(s => 
    s.completed && s.date >= oneWeekAgoStr
  ).length
})

const monthlyCompletedCount = computed(() => {
  const oneMonthAgo = new Date()
  oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1)
  const oneMonthAgoStr = oneMonthAgo.toISOString().split('T')[0]
  
  return teacherSchedules.value.filter(s => 
    s.completed && s.date >= oneMonthAgoStr
  ).length
})

const totalLearningHours = computed(() => {
  // 假设每个课程1小时，实际项目中应该记录真实时长
  return teacherSchedules.value.filter(s => s.completed).length
})

// 方法
const loadTeacherData = async () => {
  if (!authStore.currentUser) return

  console.log('教师登录 - 当前用户ID:', authStore.currentUser.id)

  // 直接使用store的reactive属性（后端API已经按用户过滤）
  await studentsStore.fetchStudents()
  await wordsStore.fetchWordSets()
  await scheduleStore.fetchSchedules()

  teacherStudents.value = studentsStore.students
  teacherWordSets.value = wordsStore.wordSets
  teacherSchedules.value = scheduleStore.schedules

  console.log('教师登录 - 加载到的学生数量:', teacherStudents.value.length)
  console.log('教师登录 - 加载到的单词集数量:', teacherWordSets.value.length)
  console.log('教师登录 - 加载到的日程数量:', teacherSchedules.value.length)
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

const startLearning = (schedule: Schedule) => {
  router.push({
    name: 'StudyHome',
    params: { studentId: schedule.studentId },
    query: { 
      wordSet: schedule.wordSet,
      teacherId: authStore.currentUser?.id || ''
    }
  })
}

const goToStats = () => {
  router.push('/stats')
}

const contactAdmin = () => {
  ElMessage.info('联系管理员功能开发中...')
}

// 生命周期
onMounted(() => {
  // 检查教师权限
  if (!authStore.isLoggedIn || authStore.isAdmin) {
    router.push('/login')
    return
  }
  
  loadTeacherData()
})
</script>

<style scoped>
.teacher-home {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-text {
  color: #606266;
  font-size: 14px;
}

.teacher-content {
  padding: 30px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-cards {
  margin-bottom: 30px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 24px;
  color: white;
}

.stat-icon.students {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.wordsets {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.schedules {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.today {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.main-content {
  margin-bottom: 30px;
}

.today-schedules {
  max-height: 400px;
  overflow-y: auto;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.schedule-item:last-child {
  border-bottom: none;
}

.schedule-time {
  font-weight: bold;
  color: #409eff;
  min-width: 80px;
  margin-right: 20px;
}

.schedule-content {
  flex: 1;
}

.schedule-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.schedule-student {
  color: #606266;
  font-size: 14px;
  margin-bottom: 5px;
}

.schedule-actions {
  margin-left: 15px;
}

.learning-stats {
  padding: 20px 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: bold;
  color: #303133;
  font-size: 18px;
}

.quick-actions {
  margin-bottom: 30px;
}

.actions-grid {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.actions-grid .el-button {
  flex: 1;
  min-width: 150px;
  height: 60px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.empty-state {
  padding: 40px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    padding: 15px 20px;
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .teacher-content {
    padding: 20px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 15px;
  }
  
  .actions-grid {
    flex-direction: column;
  }
  
  .actions-grid .el-button {
    min-width: auto;
  }
}
</style>