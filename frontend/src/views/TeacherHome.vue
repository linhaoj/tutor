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
                  <div class="stat-number">{{ regularCoursesCount }}</div>
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
                  <div class="stat-number">{{ todayRegularCoursesCount }}</div>
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
                      <div class="schedule-title">{{ schedule.word_set_name }}</div>
                      <div class="schedule-student">{{ schedule.student_name }}</div>
                      <div class="schedule-type">
                        <el-tag
                          :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                          size="small"
                        >
                          {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
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

// 只统计正课（不含抗遗忘）的课程安排总数
const regularCoursesCount = computed(() => {
  return teacherSchedules.value.filter(s => s.course_type !== 'review').length
})

// 今日所有课程（用于下方列表显示）
const todaySchedules = computed(() => {
  // 使用本地时区的日期，而不是UTC日期
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  console.log('🏠 TeacherHome今日课程:', {
    今天日期: todayStr,
    所有课程: teacherSchedules.value,
    今日课程: teacherSchedules.value.filter(s => s.date === todayStr)
  })

  return teacherSchedules.value
    .filter(s => s.date === todayStr)
    .sort((a, b) => a.time.localeCompare(b.time))
})

// 今日正课数量（不含抗遗忘）
const todayRegularCoursesCount = computed(() => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  return teacherSchedules.value.filter(s =>
    s.date === todayStr && s.course_type !== 'review'
  ).length
})

// 本周完成的正课数量（不含抗遗忘）
const weeklyCompletedCount = computed(() => {
  const oneWeekAgo = new Date()
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)
  const oneWeekAgoStr = `${oneWeekAgo.getFullYear()}-${String(oneWeekAgo.getMonth() + 1).padStart(2, '0')}-${String(oneWeekAgo.getDate()).padStart(2, '0')}`

  return teacherSchedules.value.filter(s =>
    s.completed && s.date >= oneWeekAgoStr && s.course_type !== 'review'
  ).length
})

// 本月完成的正课数量（不含抗遗忘）
const monthlyCompletedCount = computed(() => {
  const oneMonthAgo = new Date()
  oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1)
  const oneMonthAgoStr = `${oneMonthAgo.getFullYear()}-${String(oneMonthAgo.getMonth() + 1).padStart(2, '0')}-${String(oneMonthAgo.getDate()).padStart(2, '0')}`

  return teacherSchedules.value.filter(s =>
    s.completed && s.date >= oneMonthAgoStr && s.course_type !== 'review'
  ).length
})

// 总正课学习时长（不含抗遗忘，按课程时长累计）
const totalLearningHours = computed(() => {
  const completedRegularCourses = teacherSchedules.value.filter(s =>
    s.completed && s.course_type !== 'review'
  )

  // 累计实际时长（大课1.0h，小课0.5h）
  return completedRegularCourses.reduce((total, course) => {
    const hours = course.class_type === 'big' ? 1.0 : 0.5
    return total + hours
  }, 0)
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
  // 记录课程开始时间（只在首次设置）
  if (!sessionStorage.getItem('courseStartTime')) {
    const startTime = Date.now()
    sessionStorage.setItem('courseStartTime', startTime.toString())
    console.log('设置课程开始时间:', new Date().toLocaleTimeString())
  } else {
    console.log('课程已在进行中，继续计时')
  }

  // 保存课程ID，用于后续标记课程完成和扣减课时
  sessionStorage.setItem('currentScheduleId', schedule.id.toString())
  console.log('已设置 currentScheduleId:', schedule.id)

  router.push({
    name: 'StudyHome',
    params: { studentId: schedule.student_id.toString() },
    query: {
      wordSet: schedule.word_set_name,
      teacherId: authStore.currentUser?.id || '',
      scheduleId: schedule.id.toString() // 传递课程ID
    }
  })
}

const goToStats = () => {
  router.push('/stats')
}

const contactAdmin = () => {
  ElMessage.info('联系管理员功能开发中...')
}

// 存储上次的timer_version，用于检测变化
const lastTimerVersions = ref<Record<number, number>>({})

// 定期检查timer_version是否被管理员重置
const checkTimerVersionChanges = async () => {
  try {
    // 获取最新的schedules
    await scheduleStore.fetchSchedules()
    teacherSchedules.value = scheduleStore.schedules

    // 检查每个课程的timer_version是否变化
    teacherSchedules.value.forEach(schedule => {
      const lastVersion = lastTimerVersions.value[schedule.id]
      const currentVersion = schedule.timer_version || 0

      if (lastVersion !== undefined && lastVersion !== currentVersion) {
        console.log(`⚠️ 课程 ${schedule.id} 计时器被重置: ${lastVersion} -> ${currentVersion}`)
        ElMessage.warning(`课程"${schedule.word_set_name}"的计时器已被管理员重置`)

        // 清空该课程的sessionStorage
        sessionStorage.removeItem('courseStartTime')
        sessionStorage.removeItem('currentScheduleId')
        sessionStorage.removeItem(`timer_version_${schedule.id}`)
      }

      // 更新记录
      lastTimerVersions.value[schedule.id] = currentVersion
    })
  } catch (error) {
    console.error('检查timer_version失败:', error)
  }
}

// 轮询间隔 - 每10秒检查一次
let timerCheckInterval: number | null = null

// 生命周期
onMounted(async () => {
  // 检查教师权限
  if (!authStore.isLoggedIn || authStore.isAdmin) {
    router.push('/login')
    return
  }

  await loadTeacherData()

  // 初始化timer_version记录
  teacherSchedules.value.forEach(schedule => {
    lastTimerVersions.value[schedule.id] = schedule.timer_version || 0
  })

  // 启动定期检查（每10秒）
  timerCheckInterval = window.setInterval(checkTimerVersionChanges, 10000)
  console.log('🔄 TeacherHome: 已启动timer_version自动检查（每10秒）')
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (timerCheckInterval) {
    clearInterval(timerCheckInterval)
    console.log('🛑 TeacherHome: 已停止timer_version自动检查')
  }
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