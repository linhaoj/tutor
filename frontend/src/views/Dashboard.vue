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
          <!-- 今日课程：分为未完成和已完成两栏（垂直排列） -->
          <div v-if="isToday(dateGroup.date)" class="today-schedule-columns">
            <!-- 未完成课程栏 -->
            <div class="schedule-column incomplete-column">
              <div
                class="column-header"
                @click="todayIncompleteExpanded = !todayIncompleteExpanded"
              >
                <el-icon class="expand-icon" :class="{ expanded: todayIncompleteExpanded }">
                  <ArrowRight />
                </el-icon>
                <h3>未完成 ({{ getTodayIncompleteSchedules(dateGroup.schedules).length }})</h3>
              </div>
              <div v-show="todayIncompleteExpanded" class="column-content">
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
                    <div class="schedule-student">{{ schedule.student_name }}</div>
                    <div class="schedule-meta">
                      <el-tag
                        :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                        size="small"
                      >
                        {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                      </el-tag>
                      <el-tag
                        type="primary"
                        size="small"
                        style="margin-left: 8px"
                      >
                        大课
                      </el-tag>
                      <span class="duration-text">{{ schedule.duration || 60 }}分钟</span>
                      <span v-if="getLastReviewTime(schedule)" class="last-review-text">
                        · 最后复习: {{ getLastReviewTime(schedule) }}
                      </span>
                    </div>
                  </div>
                  <div class="schedule-actions">
                    <el-tooltip
                      :content="isToday(schedule.date) ? (schedule.course_type === 'review' ? '开始复习' : '开始学习') : '只能学习今日课程'"
                      placement="top"
                    >
                      <span>
                        <el-button
                          type="success"
                          @click="startStudy(schedule)"
                          :disabled="false"
                        >
                          {{ schedule.course_type === 'review' ? '复习' : '学习' }}
                        </el-button>
                      </span>
                    </el-tooltip>
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
              <div
                class="column-header"
                @click="todayCompletedExpanded = !todayCompletedExpanded"
              >
                <el-icon class="expand-icon" :class="{ expanded: todayCompletedExpanded }">
                  <ArrowRight />
                </el-icon>
                <h3>已完成 ({{ getTodayCompletedSchedules(dateGroup.schedules).length }})</h3>
              </div>
              <div v-show="todayCompletedExpanded" class="column-content">
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
                    <div class="schedule-student">{{ schedule.student_name }}</div>
                    <div class="schedule-meta">
                      <el-tag
                        :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                        size="small"
                      >
                        {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                      </el-tag>
                      <el-tag
                        type="primary"
                        size="small"
                        style="margin-left: 8px"
                      >
                        大课
                      </el-tag>
                      <span class="duration-text">{{ schedule.duration || 60 }}分钟</span>
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
                <div class="schedule-student">{{ schedule.student_name }}</div>
                <div class="schedule-meta">
                  <el-tag
                    :type="schedule.course_type === 'review' ? 'warning' : 'success'"
                    size="small"
                  >
                    {{ schedule.course_type === 'review' ? '抗遗忘' : '单词学习' }}
                  </el-tag>
                  <el-tag
                    type="primary"
                    size="small"
                    style="margin-left: 8px"
                  >
                    大课
                  </el-tag>
                  <span class="duration-text">{{ schedule.duration || 60 }}分钟</span>
                  <span v-if="getLastReviewTime(schedule)" class="last-review-text">
                    · 最后复习: {{ getLastReviewTime(schedule) }}
                  </span>
                </div>
              </div>
              <div class="schedule-actions">
                <el-tooltip
                  :content="isToday(schedule.date) ? (schedule.course_type === 'review' ? '开始复习' : '开始学习') : '只能学习今日课程'"
                  placement="top"
                >
                  <span>
                    <el-button
                      type="success"
                      @click="startStudy(schedule)"
                      :disabled="false"
                    >
                      {{ schedule.course_type === 'review' ? '复习' : '学习' }}
                    </el-button>
                  </span>
                </el-tooltip>
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
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
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

// 今日课程展开/收起状态
const todayIncompleteExpanded = ref(true)  // 未完成默认展开
const todayCompletedExpanded = ref(false)  // 已完成默认收起

// 表单
const courseForm = reactive<{
  studentId: string
  wordSet: string
  type: string
  date: string | Date
  time: string
  duration: number
  classType: string
}>({
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
  // 获取今天的日期（本地时区）
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  // 获取明天的日期
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const tomorrowYear = tomorrow.getFullYear()
  const tomorrowMonth = String(tomorrow.getMonth() + 1).padStart(2, '0')
  const tomorrowDay = String(tomorrow.getDate()).padStart(2, '0')
  const tomorrowStr = `${tomorrowYear}-${tomorrowMonth}-${tomorrowDay}`

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
  // 获取今天的日期字符串（本地时区）
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  console.log('🔍 isToday检查:', { dateString, todayStr, 结果: dateString === todayStr })

  // 直接比较日期字符串
  return dateString === todayStr
}

// 获取今日未完成课程
const getTodayIncompleteSchedules = (schedules: any[]) => {
  return schedules.filter(schedule => !schedule.completed)
}

// 获取今日已完成课程
const getTodayCompletedSchedules = (schedules: any[]) => {
  return schedules.filter(schedule => schedule.completed)
}

const startStudy = async (schedule: any) => {
  // 检查计时器版本，如果不匹配则清空计时器数据
  const storedVersion = sessionStorage.getItem(`timer_version_${schedule.id}`)
  const currentVersion = schedule.timer_version || 0

  if (storedVersion !== null && parseInt(storedVersion) !== currentVersion) {
    console.log(`🔄 计时器版本已更新 (${storedVersion} -> ${currentVersion})，清空计时器数据`)
    sessionStorage.removeItem('courseStartTime')
    sessionStorage.removeItem('currentScheduleId')
    ElMessage.info('计时器已被管理员重置')
  }

  // 存储当前计时器版本
  sessionStorage.setItem(`timer_version_${schedule.id}`, currentVersion.toString())

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

    const currentUser = authStore.currentUser
    if (!currentUser) {
      ElMessage.error('用户未登录')
      return
    }

    let existingSession = null
    let sessionTeacherId = currentUser.id

    // 优先使用课程中保存的session_id（新逻辑）
    if (schedule.session_id) {
      console.log('使用课程关联的session_id:', schedule.session_id)
      existingSession = antiForgetStore.getSession(schedule.session_id)

      if (!existingSession) {
        // 如果本地缓存没有，尝试从服务器获取
        console.log('本地缓存未找到，从服务器获取会话...')
        existingSession = await antiForgetStore.fetchSession(schedule.session_id)
      }

      if (existingSession) {
        sessionTeacherId = existingSession.teacher_id
        console.log(`找到会话，teacherId: ${sessionTeacherId}`)
      }
    } else {
      // 兼容旧数据：没有session_id的课程，使用旧逻辑查找
      console.log('旧版本课程，使用student_id + word_set_name查找会话')
      existingSession = antiForgetStore.getActiveSession(
        schedule.student_id,
        schedule.word_set_name,
        currentUser.id
      )

      // 如果当前用户是教师且没找到会话，尝试查找其他教师创建的会话
      if (!existingSession && !authStore.isAdmin) {
        console.log('当前用户未找到会话，尝试查找其他教师创建的会话...')
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
    }

    // 如果还是没找到会话
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
        teacherId: authStore.currentUser?.id || '',
        scheduleId: schedule.id.toString()
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
    const studentId = parseInt(courseForm.studentId)
    const student = students.value.find(s => s.id === studentId)

    console.log('添加课程 - 课时验证:', {
      courseForm: courseForm,
      studentId: studentId,
      allStudents: students.value,
      foundStudent: student
    })

    if (!student) {
      ElMessage.error('找不到学生信息')
      adding.value = false
      return
    }

    // 检查学生课时是否足够
    const requiredHours = 1.0
    const remainingHours = student.remaining_hours || 0

    console.log('课时检查:', {
      studentName: student.name,
      remainingHours: remainingHours,
      requiredHours: requiredHours,
      classType: courseForm.classType,
      isInsufficient: remainingHours < requiredHours
    })

    if (remainingHours < requiredHours) {
      // 课时不足，显示详细提示
      await ElMessageBox.alert(
        `学生 ${student.name} 的剩余课时不足！\n\n` +
        `剩余课时: ${remainingHours}小时\n` +
        `需要课时: ${requiredHours}小时\n` +
        `缺少课时: ${(requiredHours - remainingHours).toFixed(1)}小时\n\n` +
        `请先为学生充值课时后再安排课程。`,
        '课时不足',
        {
          confirmButtonText: '知道了',
          type: 'warning'
        }
      )
      adding.value = false
      return
    }

    // 使用本地时区格式化日期，避免时区转换问题
    let dateStr: string
    if (courseForm.date instanceof Date) {
      dateStr = courseForm.date.getFullYear() + '-' +
        String(courseForm.date.getMonth() + 1).padStart(2, '0') + '-' +
        String(courseForm.date.getDate()).padStart(2, '0')
    } else {
      dateStr = courseForm.date as string
    }
    const timeStr = courseForm.time

    const newSchedule = {
      time: timeStr,
      date: dateStr,
      word_set_name: courseForm.wordSet,
      student_name: student?.name || '',
      student_id: parseInt(courseForm.studentId),
      course_type: courseForm.type as 'learning' | 'review',
      duration: courseForm.duration,
      class_type: 'big' as 'big' | 'small'
    }

    const result = await scheduleStore.addSchedule(newSchedule)

    console.log('📅 课程添加调试:', {
      添加的课程: newSchedule,
      返回结果: result,
      当前所有课程: scheduleStore.schedules,
      今日课程过滤: scheduleStore.schedules.filter(s => {
        const today = new Date()
        const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
        console.log(`课程日期: ${s.date}, 今天: ${todayStr}, 匹配: ${s.date === todayStr}`)
        return s.date === todayStr
      })
    })

    ElMessage.success(`课程添加成功！学生剩余课时: ${(remainingHours - requiredHours).toFixed(1)}小时`)
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
    // 优先使用 schedule 中的 session_id（精确匹配）
    if (schedule.session_id) {
      const session = antiForgetStore.getSession(schedule.session_id)
      if (session) {
        return session.words.length
      }
    }

    // 兼容旧数据：如果没有 session_id，使用旧的查找方式
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

  if (!session || !session.created_at) {
    return null
  }

  // 格式化日期时间 (使用created_at作为最后复习时间)
  const date = new Date(session.created_at)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 存储上次的timer_version，用于检测变化
const lastTimerVersions = ref<Record<number, number>>({})

// 定期检查timer_version是否被管理员重置
const checkTimerVersionChanges = async () => {
  try {
    // 获取最新的schedules
    await scheduleStore.fetchSchedules()

    // 检查每个课程的timer_version是否变化
    scheduleStore.schedules.forEach(schedule => {
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

// 轮询间隔（毫秒）- 每10秒检查一次
let timerCheckInterval: number | null = null

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

    // 初始化timer_version记录
    scheduleStore.schedules.forEach(schedule => {
      lastTimerVersions.value[schedule.id] = schedule.timer_version || 0
    })

    // 启动定期检查（每10秒）
    timerCheckInterval = window.setInterval(checkTimerVersionChanges, 10000)
    console.log('🔄 已启动timer_version自动检查（每10秒）')
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败，请刷新页面重试')
  } finally {
    isLoading.value = false
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (timerCheckInterval) {
    clearInterval(timerCheckInterval)
    console.log('🛑 已停止timer_version自动检查')
  }
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
  box-sizing: border-box;
  min-width: 0;
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

/* 今日课程垂直布局 */
.today-schedule-columns {
  display: flex;
  flex-direction: column;
  gap: 15px;
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
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.column-header:hover {
  opacity: 0.9;
}

.incomplete-column .column-header {
  background: linear-gradient(135deg, #409eff 0%, #36a2ff 100%);
  color: white;
}

.completed-column .column-header {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.column-header .expand-icon {
  margin-right: 10px;
  transition: transform 0.3s ease;
}

.column-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
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
  align-items: flex-start;
  padding: 14px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-left: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.schedule-time {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  min-width: 60px;
  flex-shrink: 0;
}

.schedule-content {
  flex: 1;
  min-width: 0;
}

.schedule-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
  word-break: break-word;
}

.schedule-student {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 6px;
}

.schedule-type {
  display: flex;
}

.schedule-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}

/* 禁用的按钮样式优化 */
.schedule-actions .el-button.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.schedule-actions .el-tooltip__trigger {
  display: inline-block;
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
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.duration-text {
  color: #909399;
  font-size: 12px;
}

.word-count-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 6px;
  font-weight: 500;
}

.last-review-text {
  color: #67c23a;
  font-size: 12px;
  font-weight: 500;
}

/* 响应式：窄屏下 schedule-item 操作按钮换行到底部 */
@media (max-width: 480px) {
  .schedule-item {
    padding: 12px;
  }

  .schedule-time {
    font-size: 18px;
  }

  .schedule-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .date-header {
    padding: 12px 14px;
  }

  .column-content {
    padding: 10px;
  }
}
</style>