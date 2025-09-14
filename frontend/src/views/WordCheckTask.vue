<template>
  <div class="word-check-task">
    <!-- 课程计时器 -->
    <CourseTimer />
    
    <!-- 学习进度头部 -->
    <div class="study-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 第二个学习任务（检查）</h2>
          <div class="progress-info">
            <span>进度: {{ completedWords }}/{{ totalWords }}</span>
            <el-progress 
              :percentage="progressPercentage" 
              :stroke-width="6"
              :show-text="false"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 任务说明 -->
    <div class="task-description">
      <el-alert
        title="第二个学习任务说明"
        description="这是检查阶段，点击绿色箭头表示过关，红色箭头表示不过关。点击红色篮子中的单词可以重新检查。所有单词都过关（绿色）后才能进入下一个任务。"
        type="info"
        :closable="false"
      />
    </div>

    <!-- 5个单词卡区域 -->
    <div class="word-cards-area">
      <div 
        v-for="(word, index) in displayWords" 
        :key="word.id"
        class="word-card-row"
      >
        <!-- 单词卡 -->
        <div 
          class="word-card" 
          :class="{ 
            'passed': word.status === 'passed',
            'failed': word.status === 'failed',
            'hidden': word.status === 'failed'
          }"
          @click="toggleWordDisplay(index)"
        >
          <div class="word-text" v-if="word.status !== 'failed'">
            {{ word.showChinese ? word.chinese : word.english }}
          </div>
          <div class="hidden-text" v-else>
            <el-icon><Hide /></el-icon>
            <span>单词已隐藏</span>
          </div>
        </div>
        
        <!-- 右侧按钮区域（红绿箭头） -->
        <div class="card-actions" v-if="word.status === 'unchecked'">
          <el-button 
            type="success" 
            :icon="ArrowRight"
            size="large"
            @click="markWordStatus(index, 'passed')"
            class="pass-button"
          >
            过关
          </el-button>
          
          <el-button 
            type="danger" 
            :icon="ArrowDown"
            size="large"
            @click="markWordStatus(index, 'failed')"
            class="fail-button"
          >
            不过关
          </el-button>
        </div>
        
        <!-- 已过关状态 - 可以重新点击 -->
        <div class="status-mark" v-if="word.status === 'passed'">
          <el-button
            type="success"
            size="large"
            @click="resetWordStatus(index)"
            class="reset-button"
          >
            ✓ 过关 (点击重新检查)
          </el-button>
        </div>
        
        <!-- 不过关状态 - 只显示标识 -->
        <div class="status-mark" v-if="word.status === 'failed'">
          <el-tag type="danger" size="large">✗ 不过关 (已放入篮子)</el-tag>
        </div>
      </div>
    </div>

    <!-- 红色篮子区域 -->
    <div class="failed-basket-area">
      <div class="basket-container">
        <h3>需要重新检查的单词</h3>
        <div class="failed-basket" :class="{ 'has-words': failedWords.length > 0 }">
          <div 
            v-for="(word, index) in failedWords" 
            :key="word.id"
            class="failed-word-item"
            @click="returnWordToCheck(word)"
          >
            <div class="word-placeholder">
              <el-icon><Document /></el-icon>
              <span>单词 #{{ index + 1 }}</span>
            </div>
          </div>
          
          <div v-if="failedWords.length === 0" class="empty-basket">
            <el-icon><SuccessFilled /></el-icon>
            <span>暂无需要重新检查的单词</span>
          </div>
        </div>
        <div class="basket-info">
          <span>不过关单词数量: {{ failedWords.length }}</span>
        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="action-buttons">
      <el-button @click="goBack">返回</el-button>
      <el-button 
        v-if="allWordsPassed"
        type="success" 
        @click="goToNextTask"
        size="large"
      >
        进入第三个学习任务
      </el-button>
      <div v-else class="completion-hint">
        <span>还有 {{ remainingWordsCount }} 个单词需要检查</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, ArrowDown, Document, SuccessFilled, Hide } from '@element-plus/icons-vue'
import { useWordsStore } from '@/stores/words'
import { useStudentsStore } from '@/stores/students'
import { useLearningProgressStore } from '@/stores/learningProgress'
import CourseTimer from '@/components/CourseTimer.vue'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()
const progressStore = useLearningProgressStore()

// 单词接口
interface CheckWord {
  id: number
  english: string
  chinese: string
  showChinese: boolean
  status: 'unchecked' | 'passed' | 'failed'  // 未检查、过关、不过关
}

// 响应式数据
const studentName = ref('学生')
const allWords = ref<CheckWord[]>([])
const displayWords = ref<CheckWord[]>([])
const failedWords = ref<CheckWord[]>([])
const completedWords = ref(0)

// 计算属性
const totalWords = computed(() => allWords.value.length)

const progressPercentage = computed(() => {
  if (totalWords.value === 0) return 0
  return Math.round((completedWords.value / totalWords.value) * 100)
})

const allWordsPassed = computed(() => {
  return displayWords.value.length > 0 && 
         displayWords.value.every(word => word.status === 'passed') &&
         failedWords.value.length === 0
})

const remainingWordsCount = computed(() => {
  return displayWords.value.filter(word => word.status === 'unchecked').length + failedWords.value.length
})

// 方法
const toggleWordDisplay = (index: number) => {
  if (displayWords.value[index]) {
    displayWords.value[index].showChinese = !displayWords.value[index].showChinese
  }
}

const markWordStatus = (index: number, status: 'passed' | 'failed') => {
  const word = displayWords.value[index]
  if (word && word.status === 'unchecked') {
    word.status = status
    
    // 更新原数组中的状态
    const originalWord = allWords.value.find(w => w.id === word.id)
    if (originalWord) {
      originalWord.status = status
    }
    
    // 如果是不过关，添加到红色篮子
    if (status === 'failed') {
      failedWords.value.push({ ...word })
      ElMessage.warning(`"${word.english}" 标记为不过关，单词已隐藏并放入篮子中`)
    } else {
      ElMessage.success(`"${word.english}" 标记为过关`)
    }
    
    // 更新完成数量
    completedWords.value++
    
    // 检查是否全部完成
    if (allWordsPassed.value) {
      ElMessage.success('所有单词都已过关！可以进入下一个学习任务')
    }
  }
}

const resetWordStatus = (index: number) => {
  const word = displayWords.value[index]
  if (word && word.status === 'passed') {
    word.status = 'unchecked'
    word.showChinese = false
    
    // 更新原数组中的状态
    const originalWord = allWords.value.find(w => w.id === word.id)
    if (originalWord) {
      originalWord.status = 'unchecked'
    }
    
    // 减少完成数量
    completedWords.value--
    
    ElMessage.info(`"${word.english}" 重新设为未检查状态`)
  }
}

const returnWordToCheck = (word: CheckWord) => {
  // 从红色篮子中移除
  const basketIndex = failedWords.value.findIndex(w => w.id === word.id)
  if (basketIndex !== -1) {
    failedWords.value.splice(basketIndex, 1)
  }
  
  // 重置为未检查状态
  const displayIndex = displayWords.value.findIndex(w => w.id === word.id)
  if (displayIndex !== -1) {
    displayWords.value[displayIndex].status = 'unchecked'
    displayWords.value[displayIndex].showChinese = false
    
    // 更新原数组
    const originalWord = allWords.value.find(w => w.id === word.id)
    if (originalWord) {
      originalWord.status = 'unchecked'
    }
    
    // 减少完成数量
    completedWords.value--
    
    ElMessage.info(`"${word.english}" 已重新放回检查区域`)
  }
}

const goToNextTask = () => {
  if (!allWordsPassed.value) {
    ElMessage.warning('请确保所有单词都已过关')
    return
  }
  
  // 标记第二个任务完成
  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string
  const groupNumber = parseInt(route.query.groupNumber as string) || 1
  
  progressStore.completeTask(studentId, wordSet, groupNumber, 2)
  
  // 获取总学习单词数（从localStorage或其他方式）
  const totalWordsCount = parseInt(route.query.totalWords as string) || groupNumber * 5
  
  // 跳转到混组检测页面，检测到当前组为止的所有组
  router.push({
    name: 'MixedGroupTest',
    params: { studentId: route.params.studentId },
    query: { 
      wordSet: route.query.wordSet,
      completedGroups: groupNumber, // 传递当前完成的组号
      totalWords: totalWordsCount, // 传递总学习单词数
      startIndex: route.query.startIndex, // 传递起始位置信息
      teacherId: route.query.teacherId // 传递老师ID
    }
  })
  
  ElMessage.success('第二个任务完成！进入第三个学习任务：混组检测')
}

const goBack = () => {
  const studentId = route.params.studentId
  router.push(`/study/${studentId}`)
}

// Fisher-Yates 洗牌算法
const shuffleArray = <T>(array: T[]): T[] => {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

// 初始化数据
const initializeWords = () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const wordsCount = 5 // 固定5个单词
  const startIndex = parseInt(route.query.startIndex as string) || 0 // 新增：起始位置
  const teacherId = route.query.teacherId as string || ''
  
  // 获取指定单词集的单词（使用老师的用户ID）
  let sourceWords = wordSetName 
    ? (teacherId ? wordsStore.getWordsBySetForUser(teacherId, wordSetName) : wordsStore.getWordsBySet(wordSetName))
    : wordsStore.words
  
  // 从指定位置开始，取5个单词（与第一个任务保持一致）
  sourceWords = sourceWords.slice(startIndex, startIndex + wordsCount)
  
  // 打乱这5个单词的顺序
  const shuffledWords = shuffleArray(sourceWords)
  
  console.log('WordCheckTask - 加载单词（已打乱）:', shuffledWords.map(w => w.english))
  
  // 转换为检查用的单词格式
  allWords.value = shuffledWords.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese,
    showChinese: false,
    status: 'unchecked' as const
  }))
  
  // 显示这5个单词
  displayWords.value = [...allWords.value]
  
  const groupNumber = parseInt(route.query.groupNumber as string) || 1
  ElMessage.success(`开始第${groupNumber}组检查任务，检查 ${allWords.value.length} 个单词`)
}

// 生命周期
onMounted(() => {
  // 获取学生信息
  const studentId = parseInt(route.params.studentId as string)
  if (studentId) {
    const student = studentsStore.students.find(s => s.id === studentId)
    if (student) {
      studentName.value = student.name
    }
  }
  
  // 初始化单词数据
  initializeWords()
})
</script>

<style scoped>
.word-check-task {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.study-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  color: #303133;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 250px;
}

.progress-info span {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.task-description {
  margin-bottom: 20px;
}

/* 单词卡区域 */
.word-cards-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.word-card-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
}

.word-card-row:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.word-card {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.word-card:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-2px);
}

.word-card.passed {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.word-card.failed {
  background: linear-gradient(135deg, #ff7875 0%, #f5222d 100%);
}

.word-card.hidden {
  background: linear-gradient(135deg, #8c8c8c 0%, #595959 100%);
}

.word-text {
  font-size: 28px;
  font-weight: 600;
  color: white;
  text-align: center;
  line-height: 1.4;
  word-break: break-word;
  padding: 20px;
}

.hidden-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: white;
  padding: 20px;
  font-size: 16px;
  opacity: 0.8;
}

.hidden-text .el-icon {
  font-size: 32px;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-width: 160px;
}

.pass-button, .fail-button {
  width: 100%;
  height: 55px;
  font-size: 16px;
  font-weight: 600;
}

.pass-button {
  background: #52c41a;
  border-color: #52c41a;
}

.pass-button:hover {
  background: #389e0d;
  border-color: #389e0d;
}

.fail-button {
  background: #f5222d;
  border-color: #f5222d;
}

.fail-button:hover {
  background: #cf1322;
  border-color: #cf1322;
}

.status-mark {
  min-width: 160px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.reset-button {
  width: 100%;
  height: 55px;
  font-size: 14px;
  font-weight: 600;
  background: #52c41a;
  border-color: #52c41a;
}

.reset-button:hover {
  background: #73d13d;
  border-color: #73d13d;
}

/* 红色篮子区域 */
.failed-basket-area {
  margin-bottom: 30px;
}

.basket-container h3 {
  margin: 0 0 15px 0;
  color: #303133;
  text-align: center;
}

.failed-basket {
  min-height: 100px;
  border: 3px dashed #f5222d;
  border-radius: 12px;
  padding: 20px;
  background: #fff2f0;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.failed-basket.has-words {
  border-color: #cf1322;
  background: #fff1f0;
}

.failed-word-item {
  background: #f5222d;
  color: white;
  padding: 15px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  min-width: 100px;
}

.failed-word-item:hover {
  background: #cf1322;
  transform: translateY(-2px);
}

.word-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.word-placeholder .el-icon {
  font-size: 24px;
}

.word-placeholder span {
  font-size: 12px;
  font-weight: 500;
}

.empty-basket {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #52c41a;
  text-align: center;
}

.empty-basket .el-icon {
  font-size: 32px;
}

.basket-info {
  text-align: center;
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: auto;
  padding-top: 20px;
}

.action-buttons .el-button {
  padding: 12px 30px;
  font-size: 16px;
}

.completion-hint {
  color: #f5222d;
  font-weight: 500;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .word-check-task {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .word-card-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .card-actions {
    flex-direction: row;
    min-width: auto;
    width: 100%;
  }
  
  .status-mark {
    min-width: auto;
  }
  
  .word-text {
    font-size: 24px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 15px;
  }
}
</style>