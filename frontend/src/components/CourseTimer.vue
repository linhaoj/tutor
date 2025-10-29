<template>
  <div class="course-timer" :class="{ 'timer-warning': isWarning, 'timer-expired': isExpired }">
    <div class="timer-container">
      <el-icon class="timer-icon"><Timer /></el-icon>
      <span class="timer-text">本次课程已进行：</span>
      <span class="timer-display">{{ formattedTime }}</span>
      <span v-if="showTimeLimit" class="time-limit-hint">/ {{ timeLimitText }}</span>
    </div>
    <div v-if="isWarning && !isExpired" class="warning-message">
      ⚠️ 还有 {{ remainingMinutes }} 分钟课程将自动结束
    </div>
    <div v-if="isExpired" class="expired-message">
      ⏰ 课程时间已到，即将跳转到训后检测...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Timer } from '@element-plus/icons-vue'
import {
  COURSE_TIME_LIMIT_SECONDS,
  COURSE_TIME_LIMIT_MINUTES,
  TIME_WARNING_BEFORE_SECONDS
} from '@/config/courseConfig'

// Props
interface Props {
  enableTimeLimit?: boolean  // 是否启用时间限制（默认true）
  showTimeLimit?: boolean    // 是否显示时间限制提示（默认true）
}

const props = withDefaults(defineProps<Props>(), {
  enableTimeLimit: true,
  showTimeLimit: true
})

// Emits
const emit = defineEmits<{
  timeWarning: [remainingSeconds: number]  // 时间即将到达时触发
  timeExpired: []  // 时间到达限制时触发
}>()

const elapsedSeconds = ref(0)
let intervalId: number | null = null
let hasWarned = false  // 防止重复警告
let hasExpired = false // 防止重复触发过期事件

const formattedTime = computed(() => {
  const minutes = Math.floor(elapsedSeconds.value / 60)
  const seconds = elapsedSeconds.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

const timeLimitText = computed(() => {
  return `${COURSE_TIME_LIMIT_MINUTES}:00`
})

// 是否接近时间限制（警告状态）
const isWarning = computed(() => {
  if (!props.enableTimeLimit) return false
  const remaining = COURSE_TIME_LIMIT_SECONDS - elapsedSeconds.value
  return remaining > 0 && remaining <= TIME_WARNING_BEFORE_SECONDS
})

// 是否已超过时间限制
const isExpired = computed(() => {
  if (!props.enableTimeLimit) return false
  return elapsedSeconds.value >= COURSE_TIME_LIMIT_SECONDS
})

// 剩余分钟数
const remainingMinutes = computed(() => {
  const remaining = COURSE_TIME_LIMIT_SECONDS - elapsedSeconds.value
  return Math.ceil(remaining / 60)
})

const startTimer = () => {
  // 从sessionStorage获取开始时间
  const startTimeStr = sessionStorage.getItem('courseStartTime')
  if (!startTimeStr) {
    console.warn('没有找到课程开始时间')
    return
  }

  const startTime = parseInt(startTimeStr)
  const updateTimer = () => {
    const now = Date.now()
    const newElapsed = Math.floor((now - startTime) / 1000)
    const oldElapsed = elapsedSeconds.value
    elapsedSeconds.value = newElapsed

    // 检查是否启用时间限制
    if (!props.enableTimeLimit) return

    // 检查是否需要发出警告
    if (!hasWarned && isWarning.value) {
      hasWarned = true
      const remaining = COURSE_TIME_LIMIT_SECONDS - newElapsed
      console.log(`⚠️ 课程时间警告：还剩 ${Math.ceil(remaining / 60)} 分钟`)
      emit('timeWarning', remaining)
    }

    // 检查是否时间已到
    if (!hasExpired && isExpired.value) {
      hasExpired = true
      console.log('⏰ 课程时间已到，触发自动结束')
      emit('timeExpired')
    }
  }

  // 立即更新一次
  updateTimer()

  // 每秒更新
  intervalId = setInterval(updateTimer, 1000) as unknown as number
}

const stopTimer = () => {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  stopTimer()
})

// 组件名称
defineOptions({
  name: 'CourseTimer'
})
</script>

<style scoped>
.course-timer {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

/* 警告状态（接近时间限制） */
.course-timer.timer-warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
  animation: pulse-warning 2s ease-in-out infinite;
}

/* 过期状态（时间已到） */
.course-timer.timer-expired {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  box-shadow: 0 4px 15px rgba(250, 112, 154, 0.5);
  animation: pulse-expired 1s ease-in-out infinite;
}

@keyframes pulse-warning {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes pulse-expired {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 4px 15px rgba(250, 112, 154, 0.5);
  }
  50% {
    transform: scale(1.03);
    box-shadow: 0 6px 20px rgba(250, 112, 154, 0.7);
  }
}

.timer-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: white;
  font-weight: 600;
}

.timer-icon {
  font-size: 18px;
  color: #f7ba2a;
}

.timer-text {
  font-size: 14px;
}

.timer-display {
  font-size: 18px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  min-width: 60px;
  text-align: center;
}

.time-limit-hint {
  font-size: 14px;
  opacity: 0.8;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.warning-message,
.expired-message {
  text-align: center;
  margin-top: 8px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 13px;
  color: white;
  font-weight: 600;
}

.expired-message {
  animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@media (max-width: 768px) {
  .course-timer {
    padding: 10px 15px;
    margin-bottom: 15px;
  }

  .timer-container {
    flex-direction: column;
    gap: 5px;
  }

  .timer-text {
    font-size: 12px;
  }

  .timer-display {
    font-size: 16px;
  }

  .time-limit-hint {
    font-size: 12px;
  }

  .warning-message,
  .expired-message {
    font-size: 12px;
    margin-top: 6px;
    padding: 5px 10px;
  }
}
</style>