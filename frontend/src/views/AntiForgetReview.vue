<template>
  <div class="anti-forget-review">
    <!-- 课程计时器 -->
    <CourseTimer />
    
    <!-- 页面头部 -->
    <div class="review-header">
      <el-card>
        <div class="header-content">
          <div class="title-section">
            <h2>{{ studentName }} - 抗遗忘复习</h2>
            <div class="word-set-info">
              <el-tag type="primary" size="large">{{ wordSetName }}</el-tag>
            </div>
          </div>
          
          <div class="progress-section">
            <div class="review-progress">
              <span class="progress-text">复习进度: {{ currentReview }}/{{ totalReviews }} 次</span>
              <el-progress 
                :percentage="reviewProgressPercentage" 
                :stroke-width="8"
                :show-text="true"
                status="success"
              />
            </div>
            <div class="word-stats">
              <span class="stat-item">
                <el-icon class="star-icon"><Star /></el-icon>
                已标记: {{ starredWordsCount }} 个
              </span>
              <span class="stat-item">总单词: {{ totalWordsCount }} 个</span>
            </div>
          </div>

          <div class="action-section">
            <el-button
              type="success"
              @click="completeCurrentReview"
              :disabled="!hasAnyChanges"
            >
              完成本次复习
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 复习说明 -->
    <div class="review-instructions">
      <el-alert
        title="复习说明"
        description="点击单词卡或发音按钮可以听取单词读音。点击五角星可以标记需要重点关注的单词，标记状态会在下次复习时保持。每完成一次复习，进度会自动更新。"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 单词列表区域 -->
    <div class="words-container">
      <div class="words-grid">
        <div 
          v-for="(word, index) in shuffledWords" 
          :key="`${word.id}_${shuffleKey}`"
          class="word-item"
        >
          <!-- 单词卡片 -->
          <div
            class="word-card"
            :class="{ 'starred': word.isStarred }"
            @click="toggleWordDisplay(index)"
          >
            <div class="word-content">
              <div class="word-text">
                {{ word.showChinese ? word.chinese : word.english }}
              </div>
            </div>
          </div>
          
          <!-- 发音和五角星按钮 -->
          <div class="action-buttons-container">
            <el-button
              class="pronunciation-button"
              @click="playPronunciation(word.english)"
              :icon="VideoPlay"
              circle
              size="large"
            />
            <el-button
              :class="['star-button', { 'starred': word.isStarred }]"
              @click="toggleWordStar(word.id)"
              :icon="Star"
              circle
              size="large"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部统计信息 -->
    <div class="review-footer">
      <el-card>
        <div class="footer-content">
          <div class="completion-stats">
            <h3>本次复习统计</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-number">{{ starredWordsCount }}</div>
                <div class="stat-label">已标记单词</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ unstarredWordsCount }}</div>
                <div class="stat-label">未标记单词</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ remainingReviews }}</div>
                <div class="stat-label">剩余复习次数</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, VideoPlay } from '@element-plus/icons-vue'
import { useAntiForgetStore, type AntiForgetWord } from '@/stores/antiForget'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'
import { useUIStore } from '@/stores/ui'
import CourseTimer from '@/components/CourseTimer.vue'

const route = useRoute()
const router = useRouter()
const antiForgetStore = useAntiForgetStore()
const studentsStore = useStudentsStore()
const wordsStore = useWordsStore()
const scheduleStore = useScheduleStore()
const uiStore = useUIStore()

// 扩展的单词接口，包含显示状态
interface ReviewWord extends AntiForgetWord {
  showChinese: boolean
}

// 响应式数据
const studentId = ref<number>(parseInt(route.params.studentId as string))
const studentName = ref<string>('')
const wordSetName = ref<string>('')
const teacherId = ref<string>('')
const sessionId = ref<string>('')
const shuffledWords = ref<ReviewWord[]>([])
const shuffleKey = ref<number>(Date.now()) // 用于强制重新渲染
const hasAnyChanges = ref<boolean>(false)

// 复习统计数据
const currentReview = ref<number>(0)
const totalReviews = ref<number>(10)
const starredWordsCount = ref<number>(0)
const totalWordsCount = ref<number>(0)

// 计算属性
const reviewProgressPercentage = computed(() => {
  if (totalReviews.value === 0) return 0
  return Math.round((currentReview.value / totalReviews.value) * 100)
})

const unstarredWordsCount = computed(() => {
  return totalWordsCount.value - starredWordsCount.value
})

const remainingReviews = computed(() => {
  return Math.max(0, totalReviews.value - currentReview.value)
})

// Fisher-Yates 洗牌算法
const shuffleArray = <T>(array: T[]): T[] => {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

// 发音功能
const playPronunciation = (word: string) => {
  if ('speechSynthesis' in window) {
    // 停止当前播放的语音
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(word)
    utterance.lang = 'en-US'
    utterance.rate = 0.8
    utterance.pitch = 1.0
    utterance.volume = 1.0

    window.speechSynthesis.speak(utterance)
  } else {
    ElMessage.warning('您的浏览器不支持语音播放功能')
  }
}

// 方法
const toggleWordDisplay = (index: number) => {
  if (shuffledWords.value[index]) {
    shuffledWords.value[index].showChinese = !shuffledWords.value[index].showChinese
  }
}

const toggleWordStar = (wordId: number) => {
  const newStarState = antiForgetStore.toggleWordStar(sessionId.value, wordId)
  
  // 更新本地显示状态
  const wordIndex = shuffledWords.value.findIndex(w => w.id === wordId)
  if (wordIndex !== -1) {
    shuffledWords.value[wordIndex].isStarred = newStarState
    hasAnyChanges.value = true
  }
  
  // 更新统计数据
  updateStats()
  
  const word = shuffledWords.value[wordIndex]
  if (word) {
    ElMessage.success(`"${word.english}" ${newStarState ? '已标记' : '取消标记'}`)
  }
}

const updateStats = () => {
  starredWordsCount.value = shuffledWords.value.filter(w => w.isStarred).length
}

const completeCurrentReview = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要完成本次复习吗？本次复习标记了 ${starredWordsCount.value} 个单词。`,
      '完成复习',
      {
        confirmButtonText: '完成',
        cancelButtonText: '取消',
        type: 'success',
      }
    )
    
    const result = antiForgetStore.completeReview(sessionId.value)
    if (result) {
      ElMessage.success(`第${result.currentCount}次复习完成！还需复习${result.totalCount - result.currentCount}次`)
      
      if (result.isCompleted) {
        ElMessage.success('恭喜！所有抗遗忘复习已完成！')
        
        // 标记当前课程为已完成
        markAntiForgetCourseAsCompleted()
        
        setTimeout(() => {
          // 完全结束课程并跳转到日程管理
          uiStore.endCourse()
          router.push('/')
        }, 2000)
      } else {
        // 刷新页面数据，准备下一次复习
        setTimeout(() => {
          loadReviewData()
        }, 1000)
      }
    }
  } catch {
    // 用户取消
  }
}

const markAntiForgetCourseAsCompleted = () => {
  try {
    const scheduleIdStr = sessionStorage.getItem('currentScheduleId')
    
    if (scheduleIdStr && teacherId.value && studentId.value) {
      const scheduleId = parseInt(scheduleIdStr)
      
      // 获取课程信息来确定扣减时长
      const schedule = scheduleStore.getSchedulesByUserId(teacherId.value).find(s => s.id === scheduleId)
      if (schedule) {
        // 根据课程类型扣减时长：大课(60分钟) = 1.0h，小课(30分钟) = 0.5h
        const hoursToDeduct = schedule.classType === 'big' ? 1.0 : 0.5
        
        // 扣减学生课程时长
        const success = studentsStore.deductStudentHours(studentId.value, hoursToDeduct, teacherId.value)
        if (success) {
          console.log(`学生课程时长已扣减: ${hoursToDeduct}h (${schedule.classType === 'big' ? '大课' : '小课'})`)
        } else {
          console.warn('扣减学生课程时长失败')
        }
      }
      
      // 标记课程为已完成
      scheduleStore.completeSchedule(scheduleId)
      console.log('抗遗忘课程已标记为完成:', scheduleId)
    } else {
      console.warn('缺少课程完成所需信息', { scheduleIdStr, teacherId: teacherId.value, studentId: studentId.value })
    }
  } catch (error) {
    console.error('标记抗遗忘课程完成失败:', error)
  }
}


// 加载复习数据
const loadReviewData = () => {
  console.log('AntiForgetReview - 加载复习数据:', {
    studentId: studentId.value,
    sessionId: sessionId.value
  })

  // 获取路由参数
  wordSetName.value = route.query.wordSet as string || ''
  teacherId.value = route.query.teacherId as string || ''
  sessionId.value = route.query.sessionId as string || ''

  // 获取学生信息（支持跨用户访问）
  let student = null
  if (teacherId.value) {
    // 从教师的学生列表中查找
    const teacherStudents = studentsStore.getStudentsByUserId(teacherId.value)
    student = teacherStudents.find(s => s.id === studentId.value)
    console.log(`从教师 ${teacherId.value} 的学生列表中查找学生 ${studentId.value}:`, student ? '找到' : '未找到')
  } else {
    // 从当前用户的学生列表中查找
    student = studentsStore.students.find(s => s.id === studentId.value)
    console.log(`从当前用户的学生列表中查找学生 ${studentId.value}:`, student ? '找到' : '未找到')
  }

  if (student) {
    studentName.value = student.name
  } else {
    console.warn('未找到学生信息，使用默认名称')
    studentName.value = '学生'
  }
  
  // 获取会话数据
  const session = antiForgetStore.getSession(sessionId.value)
  if (!session) {
    ElMessage.error('找不到复习会话数据')
    uiStore.endCourse() // 错误时也结束课程
    router.push('/')
    return
  }
  
  console.log('AntiForgetReview - 找到会话数据:', session)
  
  // 更新复习统计
  currentReview.value = session.reviewCount
  totalReviews.value = session.totalReviews
  totalWordsCount.value = session.words.length
  
  // 打乱单词顺序并设置显示状态
  const wordsWithDisplay: ReviewWord[] = session.words.map(word => ({
    ...word,
    showChinese: false
  }))
  
  shuffledWords.value = shuffleArray(wordsWithDisplay)
  shuffleKey.value = Date.now() // 强制重新渲染
  
  // 更新统计
  updateStats()
  
  console.log('AntiForgetReview - 单词已打乱，数量:', shuffledWords.value.length)
  ElMessage.success(`开始第${currentReview.value + 1}次复习，共${totalWordsCount.value}个单词`)
}

// 监听路由参数变化（用于刷新数据）
watch(() => route.query.refresh, (newRefresh) => {
  if (newRefresh) {
    console.log('检测到refresh参数，重新加载复习数据')
    loadReviewData()
  }
})

// 生命周期
onMounted(() => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/')
  }

  loadReviewData()
})
</script>

<style scoped>
.anti-forget-review {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.review-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
}

.title-section h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.word-set-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-section {
  flex: 1;
  min-width: 300px;
}

.review-progress {
  margin-bottom: 15px;
}

.progress-text {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.word-stats {
  display: flex;
  gap: 20px;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: #606266;
}

.star-icon {
  color: #f7ba2a;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 140px;
}

.review-instructions {
  margin-bottom: 30px;
}

.words-container {
  margin-bottom: 30px;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.word-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
}

.word-item:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.word-item.starred {
  background: linear-gradient(135deg, #fff7e6 0%, #fff1d6 100%);
  border: 2px solid #f7ba2a;
}

.word-card {
  flex: 1;
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.word-card:hover {
  background: linear-gradient(135deg, #4fd1c7 0%, #38b2ac 100%);
}

.word-card.starred {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
}

.word-content {
  text-align: center;
  color: white;
}

.word-text {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.4;
  color: white;
}

.action-buttons-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.pronunciation-button {
  width: 50px;
  height: 50px;
  border: 2px solid #e4e7ed;
  background: white;
  color: #48bb78;
  transition: all 0.3s ease;
}

.pronunciation-button:hover {
  border-color: #48bb78;
  color: #38a169;
  background: #f0fff4;
  transform: scale(1.1);
}

.star-button {
  width: 50px;
  height: 50px;
  border: 2px solid #e4e7ed;
  background: white;
  color: #c0c4cc;
  transition: all 0.3s ease;
}

.star-button:hover {
  border-color: #f7ba2a;
  color: #f7ba2a;
  transform: scale(1.1);
}

.star-button.starred {
  border-color: #f7ba2a;
  background: #f7ba2a;
  color: white;
  box-shadow: 0 4px 12px rgba(247, 186, 42, 0.3);
}

.review-footer {
  margin-top: 40px;
}

.footer-content h3 {
  margin: 0 0 20px 0;
  color: #303133;
  text-align: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .anti-forget-review {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-section {
    flex-direction: row;
    min-width: auto;
  }
  
  .words-grid {
    grid-template-columns: 1fr;
  }
  
  .word-item {
    flex-direction: column;
    gap: 15px;
  }

  .action-buttons-container {
    width: 100%;
    flex-direction: row;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .word-stats {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .word-text {
    font-size: 18px;
  }
  
  .word-hint {
    font-size: 12px;
  }
}
</style>