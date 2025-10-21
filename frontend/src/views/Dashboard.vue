<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>日程管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加课程
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" :size="40">
        <Loading />
      </el-icon>
      <p>加载中...</p>
    </div>

    <!-- 日程按日期分组 -->
    <div v-else class="schedule-groups">
      <div 
        v-for="dateGroup in groupedSchedules" 
        :key="dateGroup.date"
        class="date-group"
      >
        <div 
          class="date-header" 
          @click="toggleDateGroup(dateGroup.date)"
        >
          <el-icon class="expand-icon" :class="{ expanded: dateGroup.expanded }">
            <ArrowRight />
          </el-icon>
          <span class="date-text">{{ formatDate(dateGroup.date) }}</span>
          <span class="course-count">{{ dateGroup.schedules.length }} 门课程</span>
        </div>
        
        <div v-show="dateGroup.expanded" class="schedule-list">
          <!-- 今日课程：分为未完成和已完成两栏 -->
          <div v-if="isToday(dateGroup.date)" class="today-schedule-columns">
            <!-- 未完成课程栏 -->
            <div class="schedule-column incomplete-column">
              <div class="column-header">
                <h3>未完成 ({{ getTodayIncompleteSchedules(dateGroup.schedules).length }})</h3>
              </div>
              <div class="column-content">
                <div 
                  v-for="schedule in getTodayIncompleteSchedules(dateGroup.schedules)" 
                  :key="schedule.id"
                  class="schedule-item"
                >
                  <div class="schedule-time">{{ schedule.time }}</div>
                  <div class="schedule-content">
                    <div class="schedule-title">
                      {{ schedule.word_set_name }}
                      <span class="word-count-badge">{{ getWordCount(schedule) }}词</span>
                    </div>
                    <div class="schedule-student">{{ schedule.studentName }}</div>
                    <div class="schedule-meta">
                      <el-tag
                        :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                        size="small"
                      >
                        {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                      </el-tag>
                      <el-tag
                        :type="schedule.classType === 'big' ? 'primary' : 'info'"
                        size="small"
                        style="margin-left: 8px"
                      >
                        {{ schedule.classType === 'big' ? '大课' : '小课' }}
                      </el-tag>
                      <span class="duration-text">{{ schedule.duration || (schedule.classType === 'big' ? 60 : 30) }}分钟</span>
                      <span v-if="getLastReviewTime(schedule)" class="last-review-text">
                        · 最后复习: {{ getLastReviewTime(schedule) }}
                      </span>
                    </div>
                  </div>
                  <div class="schedule-actions">
                    <el-button 
                      type="success" 
                      @click="startStudy(schedule)"
                    >
                      {{ schedule.course_type === 'review' ? '复习' : '学习' }}
                    </el-button>
                    <el-button 
                      v-if="authStore.isAdmin"
                      size="small" 
                      type="danger" 
                      @click="deleteSchedule(schedule)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
                <div v-if="getTodayIncompleteSchedules(dateGroup.schedules).length === 0" class="empty-column">
                  <el-empty description="暂无未完成课程" :image-size="80" />
                </div>
              </div>
            </div>
            
            <!-- 已完成课程栏 -->
            <div class="schedule-column completed-column">
              <div class="column-header">
                <h3>已完成 ({{ getTodayCompletedSchedules(dateGroup.schedules).length }})</h3>
              </div>
              <div class="column-content">
                <div 
                  v-for="schedule in getTodayCompletedSchedules(dateGroup.schedules)" 
                  :key="schedule.id"
                  class="schedule-item completed"
                >
                  <div class="schedule-time">{{ schedule.time }}</div>
                  <div class="schedule-content">
                    <div class="schedule-title">
                      {{ schedule.word_set_name }}
                      <span class="word-count-badge">{{ getWordCount(schedule) }}词</span>
                    </div>
                    <div class="schedule-student">{{ schedule.studentName }}</div>
                    <div class="schedule-meta">
                      <el-tag
                        :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                        size="small"
                      >
                        {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                      </el-tag>
                      <el-tag
                        :type="schedule.classType === 'big' ? 'primary' : 'info'"
                        size="small"
                        style="margin-left: 8px"
                      >
                        {{ schedule.classType === 'big' ? '大课' : '小课' }}
                      </el-tag>
                      <span class="duration-text">{{ schedule.duration || (schedule.classType === 'big' ? 60 : 30) }}分钟</span>
                      <el-tag type="success" size="small" style="margin-left: 8px">
                        ✓ 已完成
                      </el-tag>
                      <span v-if="getLastReviewTime(schedule)" class="last-review-text">
                        · 最后复习: {{ getLastReviewTime(schedule) }}
                      </span>
                    </div>
                  </div>
                </div>
                <div v-if="getTodayCompletedSchedules(dateGroup.schedules).length === 0" class="empty-column">
                  <el-empty description="暂无已完成课程" :image-size="80" />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 非今日课程：保持原有显示方式 -->
          <div v-else class="other-day-schedules">
            <div 
              v-for="schedule in dateGroup.schedules" 
              :key="schedule.id"
              class="schedule-item"
            >
              <div class="schedule-time">{{ schedule.time }}</div>
              <div class="schedule-content">
                <div class="schedule-title">
                  {{ schedule.word_set_name }}
                  <span class="word-count-badge">{{ getWordCount(schedule) }}词</span>
                </div>
                <div class="schedule-student">{{ schedule.studentName }}</div>
                <div class="schedule-meta">
                  <el-tag
                    :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                    size="small"
                  >
                    {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                  </el-tag>
                  <el-tag
                    :type="schedule.classType === 'big' ? 'primary' : 'info'"
                    size="small"
                    style="margin-left: 8px"
                  >
                    {{ schedule.classType === 'big' ? '大课' : '小课' }}
                  </el-tag>
                  <span class="duration-text">{{ schedule.duration || (schedule.classType === 'big' ? 60 : 30) }}分钟</span>
                  <span v-if="getLastReviewTime(schedule)" class="last-review-text">
                    · 最后复习: {{ getLastReviewTime(schedule) }}
                  </span>
                </div>
              </div>
              <div class="schedule-actions">
                <el-button 
                  type="success" 
                  @click="startStudy(schedule)"
                >
                  {{ schedule.course_type === 'review' ? '复习' : '学习' }}
                </el-button>
                <el-button 
                  v-if="authStore.isAdmin"
                  size="small" 
                  type="danger" 
                  @click="deleteSchedule(schedule)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="groupedSchedules.length === 0" class="empty-state">
      <el-empty description="暂无课程安排" />
    </div>

    <!-- 添加课程对话框 -->
    <el-dialog 
      v-model="addDialogVisible" 
      title="添加课程"
      width="500px"
    >
      <el-form :model="courseForm" label-width="100px">
        <el-form-item label="选择学生" required>
          <el-select v-model="courseForm.studentId" placeholder="请选择学生" style="width: 100%">
            <el-option 
              v-for="student in students" 
              :key="student.id" 
              :label="student.name" 
              :value="student.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择单词集" required>
          <el-select v-model="courseForm.wordSet" placeholder="请选择单词集" style="width: 100%">
            <el-option 
              v-for="set in wordSets" 
              :key="set.name" 
              :label="set.name" 
              :value="set.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="课程类型" required>
          <el-radio-group v-model="courseForm.type">
            <el-radio value="learning">单词学习</el-radio>
            <el-radio value="review">抗遗忘</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="课程规模">
          <el-radio-group v-model="courseForm.classType" @change="updateDuration">
            <el-radio value="big">大课 (60分钟)</el-radio>
            <el-radio value="small">小课 (30分钟)</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="课程时长">
          <el-input-number
            v-model="courseForm.duration"
            :min="15"
            :max="120"
            :step="15"
            style="width: 100%"
          />
          <span style="color: #999; font-size: 12px; margin-left: 8px;">分钟</span>
        </el-form-item>
        
        <el-form-item label="上课日期" required>
          <el-date-picker
            v-model="courseForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="上课时间" required>
  <el-select 
    v-model="courseForm.time" 
    placeholder="选择时间"
    filterable
    allow-create
    style="width: 100%"
  >
    <el-option 
      v-for="timeSlot in timeSlots" 
      :key="timeSlot" 
      :label="timeSlot" 
      :value="timeSlot" 
    />
  </el-select>
  <div class="form-help">
    可选择预设时间或输入自定义时间（如：14:15）
  </div>
</el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addCourse" :loading="adding">
          添加课程
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowRight, Loading } from '@element-plus/icons-vue'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'
import { useAuthStore } from '@/stores/auth'
import { useAntiForgetStore } from '@/stores/antiForget'

// 先初始化所有store
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const wordsStore = useWordsStore()
const scheduleStore = useScheduleStore()
const antiForgetStore = useAntiForgetStore()

// 再定义计算属性
// 直接使用store的reactive属性（后端API已经按用户过滤）
const students = computed(() => studentsStore.students)
const wordSets = computed(() => wordsStore.wordSets)

const router = useRouter()

// 使用 schedule store 的数据

// wordSets 现在从 words store 中获取

// 状态
const isLoading = ref(true)
const addDialogVisible = ref(false)
const adding = ref(false)

// 表单
const courseForm = reactive({
  studentId: '',
  wordSet: '',
  type: 'study',
  date: '',
  time: '',
  duration: 60,
  classType: 'big'
})

// 计算属性 - 按日期分组（使用store的computed属性）
const groupedSchedules = computed(() => {
  // 确保返回的是数组
  const schedules = scheduleStore.getGroupedSchedules
  return Array.isArray(schedules) ? schedules : []
})

// 生成时间选项（6:00-22:00，每30分钟一个）
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 6; hour <= 22; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    if (hour < 22) { // 22:30 超出范围
      slots.push(`${hour.toString().padStart(2, '0')}:30`)
    }
  }
  return slots
})

// 方法
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T00:00:00+08:00') // 北京时间
  const today = new Date()
  const beijingToday = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const todayStr = beijingToday.toISOString().split('T')[0]
  
  const tomorrow = new Date(beijingToday)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const tomorrowStr = tomorrow.toISOString().split('T')[0]
  
  if (dateStr === todayStr) {
    return `今天 (${dateStr})`
  } else if (dateStr === tomorrowStr) {
    return `明天 (${dateStr})`
  } else {
    return dateStr
  }
}


// 方法
const toggleDateGroup = (date: string) => {
  scheduleStore.toggleDateGroupExpanded(date)
}

// 判断是否是今天
const isToday = (dateString: string) => {
  const today = new Date()
  const targetDate = new Date(dateString)
  return today.toDateString() === targetDate.toDateString()
}

// 获取今日未完成课程
const getTodayIncompleteSchedules = (schedules: any[]) => {
  return schedules.filter(schedule => !schedule.completed)
}

// 获取今日已完成课程
const getTodayCompletedSchedules = (schedules: any[]) => {
  return schedules.filter(schedule => schedule.completed)
}

const startStudy = (schedule: any) => {
  // 记录课程开始时间（只在首次设置）
  if (!sessionStorage.getItem('courseStartTime')) {
    const startTime = Date.now()
    sessionStorage.setItem('courseStartTime', startTime.toString())
    console.log('设置课程开始时间:', new Date().toLocaleTimeString())
  } else {
    console.log('课程已在进行中，继续计时')
  }
  sessionStorage.setItem('currentScheduleId', schedule.id.toString())

  if (schedule.course_type === 'review') {
    console.log('进入抗遗忘模式:', schedule)

    // 查找现有的抗遗忘会话
    const currentUser = authStore.currentUser
    if (!currentUser) {
      ElMessage.error('用户未登录')
      return
    }

    // 尝试查找抗遗忘会话
    // 先用当前用户ID查找，如果找不到且当前用户不是管理员，则尝试用管理员ID查找
    let existingSession = antiForgetStore.getActiveSession(
      schedule.student_id,
      schedule.word_set_name,
      currentUser.id
    )

    let sessionTeacherId = currentUser.id

    // 如果当前用户是教师且没找到会话，尝试查找管理员创建的会话
    if (!existingSession && !authStore.isAdmin) {
      console.log('当前用户未找到会话，尝试查找管理员创建的会话...')
      // 获取所有会话，查找匹配的
      const allSessions = antiForgetStore.sessions
      existingSession = allSessions.find(session =>
        session.student_id === schedule.student_id &&
        session.word_set_name === schedule.word_set_name &&
        session.review_count < session.total_reviews
      )

      if (existingSession) {
        sessionTeacherId = existingSession.teacher_id
        console.log(`找到会话，teacherId: ${sessionTeacherId}`)
      }
    }

    // 如果没有现有会话，说明这是第一次抗遗忘复习
    // 抗遗忘会话应该已经在学习完成时创建，这里只是获取
    if (!existingSession) {
      ElMessage.error('未找到抗遗忘复习数据，请确认已完成相关学习并创建了抗遗忘计划')
      return
    }

    // 跳转到抗遗忘复习页面
    router.push({
      name: 'AntiForgetReview',
      params: { studentId: schedule.student_id },
      query: {
        wordSet: schedule.word_set_name,
        teacherId: sessionTeacherId,
        sessionId: existingSession.id
      }
    })
  } else if (schedule.course_type === 'learning') {
    // 跳转到学习准备页面，显示九宫格和选择学习单词数
    router.push({
      name: 'StudyHome',
      params: { studentId: schedule.student_id },
      query: {
        wordSet: schedule.word_set_name,
        teacherId: authStore.currentUser?.id || ''
      }
    })
  } else {
    ElMessage.error('未知的课程类型: ' + schedule.course_type)
  }
}

const updateDuration = () => {
  if (courseForm.classType === 'big') {
    courseForm.duration = 60
  } else if (courseForm.classType === 'small') {
    courseForm.duration = 30
  }
}

const showAddDialog = () => {
  Object.assign(courseForm, {
    studentId: '',
    wordSet: '',
    type: 'learning',
    date: '',
    time: '',
    duration: 60,
    classType: 'big'
  })
  addDialogVisible.value = true
}

const addCourse = async () => {
  if (!courseForm.studentId || !courseForm.wordSet || !courseForm.date || !courseForm.time) {
    ElMessage.error('请填写完整的课程信息')
    return
  }
  
  adding.value = true
  
  try {
    const student = students.value.find(s => s.id === parseInt(courseForm.studentId))
    // 使用本地时区格式化日期，避免时区转换问题
    const dateStr = courseForm.date instanceof Date
      ? courseForm.date.getFullYear() + '-' +
        String(courseForm.date.getMonth() + 1).padStart(2, '0') + '-' +
        String(courseForm.date.getDate()).padStart(2, '0')
      : courseForm.date
    const timeStr = courseForm.time
    
    const newSchedule = {
      time: timeStr,
      date: dateStr,
      wordSet: courseForm.wordSet,
      studentName: student?.name || '',
      studentId: parseInt(courseForm.studentId),
      type: courseForm.type as 'learning' | 'review',
      duration: courseForm.duration,
      classType: courseForm.classType as 'big' | 'small'
    }
    
    scheduleStore.addSchedule(newSchedule)
    
    ElMessage.success('课程添加成功')
    addDialogVisible.value = false
  } catch (error) {
    ElMessage.error('添加课程失败')
  } finally {
    adding.value = false
  }
}

const deleteSchedule = async (schedule: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${schedule.studentName} 的课程吗？`,
      '确认删除',
      { type: 'warning' }
    )

    scheduleStore.deleteSchedule(schedule.id)
    ElMessage.success('课程删除成功')
  } catch {}
}

// 获取单词集的单词数量（本次复习的单词数）
const getWordCount = (schedule: any) => {
  const currentUser = authStore.currentUser
  if (!currentUser) return 0

  // 如果是抗遗忘课程，返回本次复习的单词数
  if (schedule.course_type === 'review') {
    const session = antiForgetStore.getActiveSession(
      schedule.student_id,
      schedule.word_set_name,
      currentUser.id
    )

    if (session) {
      return session.words.length
    }

    // 如果当前用户是教师，尝试查找管理员创建的会话
    if (!authStore.isAdmin) {
      const allSessions = antiForgetStore.sessions
      const existingSession = allSessions.find(s =>
        s.student_id === schedule.student_id &&
        s.word_set_name === schedule.word_set_name &&
        s.review_count < s.total_reviews
      )

      if (existingSession) {
        return existingSession.words.length
      }
    }
  }

  // 如果是学习课程，返回整个单词库的单词数
  // 需要先查找匹配的wordSet来获取单词数
  const wordSet = wordSets.value.find(ws => ws.name === schedule.word_set_name)
  return wordSet ? wordSet.word_count : 0
}

// 获取最后复习时间
const getLastReviewTime = (schedule: any) => {
  if (schedule.course_type !== 'review') {
    return null
  }

  // 从 antiForget store 获取最后复习时间
  const currentUser = authStore.currentUser
  if (!currentUser) return null

  const session = antiForgetStore.getActiveSession(
    schedule.student_id,
    schedule.word_set_name,
    currentUser.id
  )

  if (!session || !session.lastReviewDate) {
    return null
  }

  // 格式化日期时间
  const date = new Date(session.lastReviewDate)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  try {
    isLoading.value = true
    // 并行加载所有必要的数据
    await Promise.all([
      scheduleStore.fetchSchedules(),
      studentsStore.fetchStudents(),
      wordsStore.fetchWordSets()
    ])

    // 加载所有学生的抗遗忘会话数据
    const currentUser = authStore.currentUser
    if (currentUser) {
      for (const student of studentsStore.students) {
        await antiForgetStore.fetchStudentSessions(student.id)
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败，请刷新页面重试')
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #409eff;
}

.loading-container p {
  margin-top: 20px;
  font-size: 16px;
  color: #606266;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.date-group {
  margin-bottom: 20px;
}

.date-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.date-header:hover {
  background: #e6f7ff;
}

.expand-icon {
  margin-right: 10px;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.date-text {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.course-count {
  color: #909399;
  font-size: 14px;
}

.schedule-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 今日课程两栏布局 */
.today-schedule-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-top: 10px;
}

.schedule-column {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  background: #fafafa;
  overflow: hidden;
}

.incomplete-column {
  border-color: #409eff;
}

.completed-column {
  border-color: #67c23a;
}

.column-header {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 15px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.incomplete-column .column-header {
  background: linear-gradient(135deg, #409eff 0%, #36a2ff 100%);
  color: white;
}

.completed-column .column-header {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.column-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.column-content {
  padding: 15px;
  max-height: 600px;
  overflow-y: auto;
}

.empty-column {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* 已完成课程样式 */
.schedule-item.completed {
  opacity: 0.8;
  background: #f0f9ff;
  border: 1px dashed #67c23a;
}

.schedule-item.completed .schedule-title {
  text-decoration: line-through;
  color: #909399;
}

/* 非今日课程保持原有样式 */
.other-day-schedules {
  /* 与原有.schedule-list相同的样式 */
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-left: 30px;
}

.schedule-time {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-right: 20px;
  min-width: 80px;
}

.schedule-content {
  flex: 1;
}

.schedule-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.schedule-student {
  font-size: 14px;
  color: #e6a23c;
  margin-bottom: 8px;
}

.schedule-type {
  display: flex;
}

.schedule-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  margin-top: 50px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 新增课程显示样式 */
.schedule-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.duration-text {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.word-count-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 8px;
  font-weight: 500;
}

.last-review-text {
  color: #67c23a;
  font-size: 12px;
  margin-left: 4px;
  font-weight: 500;
}
</style>