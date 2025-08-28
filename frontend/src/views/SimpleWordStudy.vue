<template>
  <div class="simple-word-study">
    <!-- 学习进度头部 -->
    <div class="study-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 单词学习</h2>
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
          :class="{ 'moved-to-box': word.movedToBox }"
          @click="toggleWordDisplay(index)"
        >
          <div class="word-text">
            {{ word.showChinese ? word.chinese : word.english }}
          </div>
        </div>
        
        <!-- 右侧按钮区域 -->
        <div class="card-actions" v-if="!word.movedToBox">
          <el-button 
            type="success" 
            :icon="ArrowDown"
            size="large"
            @click="moveToBox(index)"
            class="move-button"
          >
            学完了
          </el-button>
          
          <!-- 预留按钮位置 -->
          <div class="reserved-button">
            <!-- 预留给未来功能 -->
          </div>
        </div>
        
        <!-- 已学完标识 -->
        <div class="completed-mark" v-if="word.movedToBox">
          <el-tag type="success" size="large">已学完</el-tag>
        </div>
      </div>
    </div>

    <!-- 底部小盒子区域 -->
    <div class="bottom-boxes">
      <div class="box-container">
        <h3>已学单词</h3>
        <div class="word-box" :class="{ 'has-words': boxWords.length > 0 }">
          <div 
            v-for="(word, index) in boxWords" 
            :key="word.id"
            class="box-word-item"
            @click="moveBackToCard(word)"
          >
            <span class="box-word-text">{{ word.english }}</span>
          </div>
          <div v-if="boxWords.length === 0" class="empty-box">
            <el-icon><Box /></el-icon>
            <span>点击绿色箭头将单词放到这里</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="action-buttons">
      <el-button @click="goBack">返回</el-button>
      <el-button 
        v-if="currentGroupCompleted"
        type="warning" 
        @click="goToNextTask"
        size="large"
      >
        进入第二个学习任务
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Box } from '@element-plus/icons-vue'
import { useWordsStore } from '@/stores/words'
import { useStudentsStore } from '@/stores/students'
import { useLearningProgressStore } from '@/stores/learningProgress'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()
const progressStore = useLearningProgressStore()

// 单词接口
interface StudyWord {
  id: number
  english: string
  chinese: string
  showChinese: boolean
  movedToBox: boolean
}

// 响应式数据
const studentName = ref('学生')
const allWords = ref<StudyWord[]>([])
const displayWords = ref<StudyWord[]>([])
const boxWords = ref<StudyWord[]>([])
const currentRound = ref(1)
const completedWords = ref(0)

// 计算属性
const totalWords = computed(() => allWords.value.length)

const progressPercentage = computed(() => {
  if (totalWords.value === 0) return 0
  return Math.round((completedWords.value / totalWords.value) * 100)
})

const remainingWords = computed(() => {
  return allWords.value.filter(word => !word.movedToBox)
})

const currentGroupCompleted = computed(() => {
  return displayWords.value.length > 0 && displayWords.value.every(word => word.movedToBox)
})

const hasMoreWords = computed(() => {
  return remainingWords.value.length > displayWords.value.length
})

// 方法
const toggleWordDisplay = (index: number) => {
  if (displayWords.value[index]) {
    displayWords.value[index].showChinese = !displayWords.value[index].showChinese
  }
}

const moveToBox = (index: number) => {
  const word = displayWords.value[index]
  if (word && !word.movedToBox) {
    // 标记为已移动
    word.movedToBox = true
    
    // 在原数组中也标记为已学完
    const originalWord = allWords.value.find(w => w.id === word.id)
    if (originalWord) {
      originalWord.movedToBox = true
    }
    
    // 添加到小盒子
    boxWords.value.push({ ...word })
    
    // 更新完成数量
    completedWords.value++
    
    ElMessage.success(`"${word.english}" 已学完`)
    
    // 检查当前组是否全部完成
    if (currentGroupCompleted.value) {
      ElMessage.success('当前组的5个单词已全部学完！')
    }
  }
}

const moveBackToCard = (word: StudyWord) => {
  // 从小盒子移除
  const boxIndex = boxWords.value.findIndex(w => w.id === word.id)
  if (boxIndex !== -1) {
    boxWords.value.splice(boxIndex, 1)
  }
  
  // 在原数组中标记为未移动
  const originalWord = allWords.value.find(w => w.id === word.id)
  if (originalWord) {
    originalWord.movedToBox = false
    originalWord.showChinese = false
  }
  
  // 如果显示区域还有空位，重新添加到显示区域
  if (displayWords.value.length < 5) {
    displayWords.value.push({
      ...word,
      movedToBox: false,
      showChinese: false
    })
  }
  
  // 更新完成数量
  completedWords.value--
  
  ElMessage.info(`"${word.english}" 已移回卡片区域`)
}

const startNextGroup = () => {
  if (!currentGroupCompleted.value) {
    ElMessage.warning('请先完成当前组的所有单词')
    return
  }
  
  if (remainingWords.value.length === 0) {
    ElMessage.success('恭喜！所有单词都已学完')
    return
  }
  
  // 清空当前显示和小盒子
  displayWords.value = []
  boxWords.value = []
  
  // 加载下一组的5个单词
  loadNextGroup()
  
  currentRound.value++
  ElMessage.success(`开始第 ${currentRound.value} 组学习`)
}

const goToNextTask = () => {
  if (!currentGroupCompleted.value) {
    ElMessage.warning('请先完成当前组的所有单词')
    return
  }
  
  // 标记第一个任务完成
  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string
  progressStore.completeTask(studentId, wordSet, 1, 1)
  
  // 跳转到第二个学习任务（检查任务）
  router.push({
    name: 'WordCheckTask',
    params: { studentId: route.params.studentId },
    query: { 
      wordSet: route.query.wordSet,
      wordsCount: 5,
      groupNumber: 1
    }
  })
  
  ElMessage.success('第一个任务完成！进入第二个学习任务：检查阶段')
}

const completeAllLearning = () => {
  ElMessage.success('恭喜！所有单词学习完成！')
  setTimeout(() => {
    goBack()
  }, 2000)
}

const loadNextGroup = () => {
  const wordsToLoad = remainingWords.value.slice(0, 5)
  displayWords.value = wordsToLoad.map(word => ({ ...word, showChinese: false }))
}

const goBack = () => {
  router.push('/learning')
}

// 初始化数据
const initializeWords = () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const wordsCount = parseInt(route.query.wordsCount as string) || 20
  
  // 获取指定单词集的单词
  let sourceWords = wordSetName 
    ? wordsStore.getWordsBySet(wordSetName)
    : wordsStore.words.slice(0, wordsCount)
  
  // 限制数量
  sourceWords = sourceWords.slice(0, wordsCount)
  
  // 转换为学习用的单词格式
  allWords.value = sourceWords.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese,
    showChinese: false,
    movedToBox: false
  }))
  
  // 加载第一组的5个单词
  loadNextGroup()
  
  ElMessage.success(`开始学习 ${allWords.value.length} 个单词`)
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
  
  // 初始化学习进度
  const wordSet = route.query.wordSet as string
  const wordsCount = parseInt(route.query.wordsCount as string) || 20
  const totalGroups = Math.ceil(wordsCount / 5) // 每组5个单词
  
  if (studentId && wordSet) {
    progressStore.startLearningProgress(studentId, wordSet, totalGroups)
  }
  
  // 初始化单词数据
  initializeWords()
})
</script>

<style scoped>
.simple-word-study {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.study-header {
  margin-bottom: 30px;
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

/* 单词卡区域 */
.word-cards-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 40px;
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

.word-card.moved-to-box {
  background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
  opacity: 0.7;
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

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 150px;
}

.move-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
}

.reserved-button {
  height: 40px;
  /* 预留给未来功能的按钮空间 */
}

.completed-mark {
  min-width: 150px;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 底部小盒子 */
.bottom-boxes {
  margin-bottom: 30px;
}

.box-container h3 {
  margin: 0 0 15px 0;
  color: #303133;
  text-align: center;
}

.word-box {
  min-height: 120px;
  border: 3px dashed #dcdfe6;
  border-radius: 12px;
  padding: 20px;
  background: #fafafa;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.word-box.has-words {
  border-color: #67c23a;
  background: #f0f9ff;
}

.box-word-item {
  background: #67c23a;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.box-word-item:hover {
  background: #5daf34;
  transform: translateY(-2px);
}

.box-word-text {
  font-size: 14px;
}

.empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
  text-align: center;
}

.empty-box .el-icon {
  font-size: 32px;
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: auto;
  padding-top: 20px;
}

.action-buttons .el-button {
  padding: 12px 30px;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .word-cards-area {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .simple-word-study {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .word-cards-area {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .card-content {
    padding: 20px 15px;
    min-height: 150px;
  }
  
  .word-text {
    font-size: 18px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .word-cards-area {
    grid-template-columns: 1fr;
  }
}
</style>