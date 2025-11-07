<template>
  <div class="study-home">
    <!-- 课程计时器 -->
    <CourseTimer />
    
    <div class="page-header">
      <h1>{{ studentName }} - {{ currentWordSet || '单词学习' }}</h1>
    </div>

    <!-- 九宫格统计 -->
    <div class="grid-stats">
      <h2>学习进度</h2>
      <div class="grid-container">
        <div 
          v-for="i in 9" 
          :key="i-1"
          class="grid-cell"
          :class="getGridCellClass(i-1)"
        >
          <div class="grid-number">格子 {{ i-1 }}</div>
          <div class="grid-count">{{ (gridStats as any)[`grid_${i-1}`] || 0 }}</div>
          <div class="grid-label">{{ getGridLabel(i-1) }}</div>
        </div>
      </div>
    </div>

    <!-- 总体统计 -->
    <div class="overall-stats">
      <el-card>
        <h3>词库统计</h3>
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-label">总单词数：</span>
            <span class="stat-value">{{ totalWords }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已学单词：</span>
            <span class="stat-value learned">{{ learnedWords }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未学单词：</span>
            <span class="stat-value unlearned">{{ unlearnedWords }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">可学习单词：</span>
            <span class="stat-value available">{{ availableWords }}</span>
          </div>
        </div>
        
        <el-progress 
          :percentage="progressPercentage" 
          :stroke-width="12"
          :show-text="true"
          class="progress-bar"
        />
      </el-card>
    </div>

    <!-- 开始学习 -->
    <div class="start-learning">
      <el-card>
        <h3>开始学习</h3>
        <div class="learning-options">
          <!-- 学习模式选择 -->
          <div class="option-group">
            <label>学习模式：</label>
            <el-select
              v-model="learningMode"
              placeholder="请选择"
              style="width: 200px"
              @change="onLearningModeChange"
            >
              <el-option label="学习新词" value="new" />
              <el-option label="复习旧词" value="review" />
            </el-select>
          </div>

          <div class="option-group">
            <label>选择学习单词数量：</label>
            <el-select
              v-model="selectedWordsCount"
              placeholder="请选择"
              style="width: 200px"
            >
              <el-option label="5个单词" :value="5" />
              <el-option label="10个单词" :value="10" />
              <el-option label="15个单词" :value="15" />
              <el-option label="20个单词" :value="20" />
              <el-option label="25个单词" :value="25" />
              <el-option label="30个单词" :value="30" />
              <el-option label="自定义" :value="0" />
            </el-select>
          </div>

          <div v-if="selectedWordsCount === 0" class="option-group">
            <label>自定义数量：</label>
            <el-input-number
              v-model="customWordsCount"
              :min="Math.min(1, availableWords)"
              :max="Math.max(1, availableWords)"
              :disabled="availableWords === 0"
              style="width: 200px"
            />
          </div>

          <div class="available-info">
            <el-alert
              :title="`${learningMode === 'new' ? '可学习新词' : '可复习单词'}: ${availableWords} 个`"
              :type="learningMode === 'new' ? 'info' : 'success'"
              :closable="false"
            />
          </div>

          <div class="start-actions">
            <el-button 
              type="primary" 
              size="large"
              @click="startLearning"
              :disabled="!canStartLearning"
            >
              开始学习 ({{ finalWordsCount }} 个单词)
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useLearningProgressStore } from '@/stores/learningProgress'
import { useUIStore } from '@/stores/ui'
import CourseTimer from '@/components/CourseTimer.vue'

const route = useRoute()
const router = useRouter()
const studentsStore = useStudentsStore()
const wordsStore = useWordsStore()
const progressStore = useLearningProgressStore()
const uiStore = useUIStore()

// Props
const studentId = ref<number>(parseInt(route.params.studentId as string))
const teacherId = ref<string>(route.query.teacherId as string || '')

// 响应式数据
const studentName = ref<string>('')
const currentWordSet = ref<string>('')
const selectedWordsCount = ref(10)
const customWordsCount = ref(10)
const learningMode = ref<'new' | 'review'>('new') // 学习模式：new=学习新词，review=复习旧词

// 真实的九宫格数据（基于学习进度）
const gridStats = ref({
  grid_0: 0,  // 未学习
  grid_1: 0,  // 阶段1
  grid_2: 0,  // 阶段2
  grid_3: 0,  // 阶段3
  grid_4: 0,  // 阶段4
  grid_5: 0,  // 阶段5
  grid_6: 0,  // 阶段6
  grid_7: 0,  // 阶段7
  grid_8: 0   // 已掌握（预留）
})

// 计算属性
const totalWords = computed(() => {
  return Object.values(gridStats.value).reduce((sum, count) => sum + count, 0)
})

const unlearnedWords = computed(() => gridStats.value.grid_0)

const learnedWords = computed(() => {
  return totalWords.value - unlearnedWords.value
})

const availableWords = computed(() => {
  if (learningMode.value === 'new') {
    // 学习新词：只有格子0的单词可用
    return gridStats.value.grid_0
  } else {
    // 复习旧词：格子1-7的单词可用
    let count = 0
    for (let i = 1; i <= 7; i++) {
      count += (gridStats.value as any)[`grid_${i}`] || 0
    }
    return count
  }
})

const progressPercentage = computed(() => {
  if (totalWords.value === 0) return 0
  return Math.round((learnedWords.value / totalWords.value) * 100)
})

const finalWordsCount = computed(() => {
  return selectedWordsCount.value === 0 ? customWordsCount.value : selectedWordsCount.value
})

const canStartLearning = computed(() => {
  const count = finalWordsCount.value
  return count > 0 && count <= availableWords.value
})

// 方法
const getGridCellClass = (position: number) => {
  if (position === 0) return 'unlearned'
  if (position >= 1 && position <= 7) return 'learning'
  if (position === 8) return 'mastered'
  return ''
}

const getGridLabel = (position: number) => {
  if (position === 0) return '未学'
  if (position >= 1 && position <= 7) return '学习中'
  if (position === 8) return '已掌握'
  return ''
}

const startLearning = () => {
  if (!canStartLearning.value) {
    ElMessage.error(`可学习单词不足，最多只能选择${availableWords.value}个单词`)
    return
  }

  // 跳转到单词筛选页面
  router.push({
    name: 'WordFilter',
    params: { studentId: studentId.value },
    query: {
      wordSet: route.query.wordSet || '',
      wordsCount: finalWordsCount.value,
      teacherId: teacherId.value,
      learningMode: learningMode.value, // 传递学习模式
      scheduleId: route.query.scheduleId || '' // 传递课程ID
    }
  })
}

// 学习模式切换处理
const onLearningModeChange = () => {
  // 切换模式时，重置自定义数量
  if (selectedWordsCount.value === 0) {
    customWordsCount.value = Math.min(10, availableWords.value)
  }

  // 如果当前选择的数量超过可用单词数，自动调整
  if (finalWordsCount.value > availableWords.value) {
    selectedWordsCount.value = Math.min(10, availableWords.value)
    ElMessage.warning(`已切换为${learningMode.value === 'new' ? '学习新词' : '复习旧词'}模式，可用单词数为${availableWords.value}`)
  }
}

// 监听可用单词数变化，自动调整选择
watch(availableWords, (newAvailable) => {
  if (selectedWordsCount.value === 0) {
    // 自定义模式：确保不超过可用数量
    if (customWordsCount.value > newAvailable) {
      customWordsCount.value = Math.max(1, newAvailable)
    }
  } else {
    // 预设模式：如果超过可用数量，自动切换到自定义
    if (selectedWordsCount.value > newAvailable) {
      selectedWordsCount.value = 0
      customWordsCount.value = Math.max(1, newAvailable)
    }
  }
})


// 加载真实的九宫格统计数据
const loadRealGridStats = async () => {
  if (!studentId.value || !currentWordSet.value) {
    console.warn('缺少学生ID或单词集信息')
    return
  }

  try {
    console.log('StudyHome - 准备获取九宫格统计:', {
      studentId: studentId.value,
      currentWordSet: currentWordSet.value
    })

    // 直接从后端API获取九宫格统计数据
    const stats = await progressStore.getGridStats(studentId.value, currentWordSet.value)

    // 更新响应式数据
    gridStats.value = stats

    console.log('九宫格统计数据已更新:', stats)

  } catch (error) {
    console.error('加载九宫格统计数据失败:', error)
    ElMessage.error('加载学习进度数据失败')
  }
}

// 初始化课程模式
const initializeCourseMode = () => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/')
  }

  // 设置计时开始时间（如果还没有设置）
  if (!sessionStorage.getItem('courseStartTime')) {
    sessionStorage.setItem('courseStartTime', Date.now().toString())
    console.log('设置课程开始时间:', new Date().toLocaleTimeString())
  } else {
    console.log('课程已在进行中，继续计时')
  }
}

// 清理上一轮学习的临时数据
const clearTemporaryLearningData = () => {
  const keysToRemove = [
    'learning_session_id',
    'current_learning_words',
    'current_group_number',
    'current_stage',
    'stage1_results',
    'stage2_results',
    'stage3_results',
    'total_learning_words',
    'filtered_words'
  ]

  keysToRemove.forEach(key => {
    sessionStorage.removeItem(key)
  })

  // 清理所有组的单词数据
  for (let i = 1; i <= 10; i++) {
    sessionStorage.removeItem(`learned_words_group_${i}`)
    sessionStorage.removeItem(`simpleStudyGroup_${i}`)
  }

  // 清理所有训后检测状态（使用通配符模式清理）
  const allKeys = Object.keys(sessionStorage)
  allKeys.forEach(key => {
    if (key.startsWith('postTestStatus_')) {
      sessionStorage.removeItem(key)
      console.log('清理训后检测状态:', key)
    }
  })

  console.log('StudyHome - 已清理上一轮学习的临时数据')
}

// 生命周期
onMounted(async () => {
  try {
    // 清理上一轮学习的临时数据
    clearTemporaryLearningData()

    // 初始化课程模式
    initializeCourseMode()

    // 获取学生信息（后端API自动按当前用户过滤）
    await studentsStore.fetchStudents()
    const student = studentsStore.students.find(s => s.id === studentId.value)

    if (student) {
      studentName.value = student.name
    } else {
      console.warn('找不到学生信息', { studentId: studentId.value, teacherId: teacherId.value })
      ElMessage.error('找不到学生信息')
      return
    }

    // 获取单词集信息
    currentWordSet.value = route.query.wordSet as string || ''

    // 获取真实的九宫格统计数据
    await loadRealGridStats()

  } catch (error) {
    ElMessage.error('加载学习数据失败')
    console.error(error)
  }
})

// 在路由更新时刷新数据（处理同一路由但参数变化的情况）
onBeforeRouteUpdate(async (to, from) => {
  console.log('StudyHome 路由更新，刷新九宫格数据')
  if (to.path === from.path) {
    await loadRealGridStats()
  }
})

// 监听路由变化，每次进入页面都刷新数据
watch(() => route.fullPath, async () => {
  if (route.name === 'StudyHome') {
    console.log('StudyHome 页面路由变化，刷新九宫格数据')
    await loadRealGridStats()
  }
})

// 监听refresh参数，如果有变化则重新加载数据
watch(() => route.query.refresh, async (newRefresh) => {
  if (newRefresh) {
    console.log('检测到refresh参数，重新加载九宫格数据')
    await loadRealGridStats()
  }
})
</script>

<style scoped>
.study-home {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
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

.grid-stats {
  margin-bottom: 30px;
}

.grid-stats h2 {
  color: #303133;
  margin-bottom: 20px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  max-width: 600px;
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

.grid-cell.unlearned {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #606266;
}

.grid-cell.learning {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.grid-cell.mastered {
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

.overall-stats {
  margin-bottom: 30px;
}

.overall-stats h3 {
  margin: 0 0 20px 0;
  color: #303133;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-label {
  color: #606266;
}

.stat-value {
  font-weight: 600;
  font-size: 18px;
}

.stat-value.learned {
  color: #67c23a;
}

.stat-value.unlearned {
  color: #909399;
}

.stat-value.available {
  color: #409eff;
}

.progress-bar {
  margin-top: 20px;
}

.start-learning h3 {
  margin: 0 0 20px 0;
  color: #303133;
}

.learning-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 15px;
}

.option-group label {
  min-width: 150px;
  color: #606266;
  font-weight: 500;
}

.available-info {
  margin: 10px 0;
}

.start-actions {
  text-align: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .option-group {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .option-group label {
    min-width: auto;
  }
}
</style>