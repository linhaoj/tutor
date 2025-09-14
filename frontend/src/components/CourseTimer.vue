<template>
  <div class="course-timer">
    <div class="timer-container">
      <el-icon class="timer-icon"><Timer /></el-icon>
      <span class="timer-text">本次课程已进行：</span>
      <span class="timer-display">{{ formattedTime }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Timer } from '@element-plus/icons-vue'

const elapsedSeconds = ref(0)
let intervalId: number | null = null

const formattedTime = computed(() => {
  const minutes = Math.floor(elapsedSeconds.value / 60)
  const seconds = elapsedSeconds.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
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
    elapsedSeconds.value = Math.floor((now - startTime) / 1000)
  }
  
  // 立即更新一次
  updateTimer()
  
  // 每秒更新
  intervalId = setInterval(updateTimer, 1000)
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
}
</style>