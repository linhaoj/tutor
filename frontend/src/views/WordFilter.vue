<template>
  <div class="word-filter">
    <!-- 课程计时器 -->
    <CourseTimer />
    
    <!-- 页面头部 -->
    <div class="filter-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 单词筛选</h2>
          <div class="progress-info">
            <span>本次学习: {{ wordsCount }}个单词 | 轮次: {{ currentRound }}/10</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 筛选说明 -->
    <div class="filter-instructions">
      <el-alert
        title="单词筛选说明"
        :description="getInstructionText()"
        type="info"
        :closable="false"
      />
    </div>

    <!-- 单词列表 -->
    <div class="words-list">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>请选择你已经认识的单词</span>
            <div class="selection-info">
              已选择: {{ selectedKnownWords.length }} / {{ currentWords.length }}
            </div>
          </div>
        </template>

        <div class="words-grid">
          <div 
            v-for="(word, index) in currentWords" 
            :key="`${word.id}-${index}`"
            class="word-item"
            :class="{ 'selected': selectedKnownWords.includes(index) }"
            @click="toggleWordSelection(index)"
          >
            <div class="word-content">
              <div class="english">{{ word.english }}</div>
            </div>
            <div class="word-actions">
              <el-button
                type="primary"
                :icon="VideoPlay"
                size="small"
                circle
                @click.stop="playPronunciation(word.english)"
                class="pronunciation-btn"
                title="播放发音"
              />
            </div>
            <div class="selection-indicator" v-if="selectedKnownWords.includes(index)">
              <el-icon class="check-icon"><Check /></el-icon>
            </div>
          </div>
        </div>

        <div class="filter-actions">
          <div class="selection-summary">
            <span v-if="selectedKnownWords.length === 0" class="no-selection">
              没有选择任何单词，可以开始学习了
            </span>
            <span v-else class="has-selection">
              选择了 {{ selectedKnownWords.length }} 个认识的单词，将被替换为新单词
            </span>
          </div>
          
          <div class="action-buttons">
            <el-button
              type="primary"
              size="large"
              @click="confirmSelection"
              :loading="processing"
            >
              {{ selectedKnownWords.length === 0 ? '开始学习' : '替换并继续' }}
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, VideoPlay } from '@element-plus/icons-vue'
import { useWordsStore } from '@/stores/words'
import { useStudentsStore } from '@/stores/students'
import { useLearningProgressStore } from '@/stores/learningProgress'
import { useUIStore } from '@/stores/ui'
import CourseTimer from '@/components/CourseTimer.vue'

interface Word {
  id: number
  english: string
  chinese: string
}

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()
const progressStore = useLearningProgressStore()
const uiStore = useUIStore()

// 路由参数
const studentId = ref<number>(parseInt(route.params.studentId as string))
const teacherId = ref<string>(route.query.teacherId as string || '')
const wordSetName = ref<string>(route.query.wordSet as string || '')
const wordsCount = ref<number>(parseInt(route.query.wordsCount as string) || 10)

// 状态数据
const studentName = ref<string>('')
const currentWords = ref<Word[]>([])
const selectedKnownWords = ref<number[]>([])
const processing = ref(false)
const currentRound = ref(1)
const maxRounds = 10

// 计算属性
const getInstructionText = () => {
  if (currentRound.value === 1) {
    return `这是第${currentRound.value}轮筛选。请选择你已经认识的单词，系统将自动替换为新的单词。已认识的单词会直接标记为"已掌握"，跳过后续学习阶段。`
  } else {
    return `这是第${currentRound.value}轮筛选。继续选择你认识的单词，确保最终学习的都是真正需要学的新单词。`
  }
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

// 获取可用的替换单词
const getAvailableReplacementWords = (excludeWords: Word[]): Word[] => {
  let allWords: Word[] = []
  
  if (teacherId.value) {
    allWords = wordsStore.getWordsBySetForUser(teacherId.value, wordSetName.value)
  } else {
    allWords = wordsStore.getWordsBySet(wordSetName.value)
  }

  // 排除已经在当前学习列表中的单词
  const excludeIds = new Set(excludeWords.map(w => w.id))
  const availableWords = allWords.filter(word => !excludeIds.has(word.id))

  // 过滤出真正需要学习的单词（格子0-6的单词）
  return availableWords.filter((_, index) => {
    const wordIndex = allWords.findIndex(w => w.id === _.id)
    const wordProgress = progressStore.getWordProgressForUser(
      teacherId.value,
      studentId.value,
      wordSetName.value,
      wordIndex
    )
    const stage = wordProgress ? wordProgress.currentStage : 0
    return stage >= 0 && stage <= 6
  })
}

// 播放单词发音
const playPronunciation = (word: string) => {
  try {
    // 使用 Web Speech API 播放发音
    if ('speechSynthesis' in window) {
      // 停止当前播放
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(word)
      utterance.lang = 'en-US' // 设置英语发音
      utterance.rate = 0.8 // 稍慢的语速
      utterance.volume = 1.0

      window.speechSynthesis.speak(utterance)
    } else {
      ElMessage.warning('您的浏览器不支持语音播放功能')
    }
  } catch (error) {
    console.error('播放发音失败:', error)
    ElMessage.error('播放发音失败')
  }
}

// 切换单词选择状态
const toggleWordSelection = (index: number) => {
  const selectedIndex = selectedKnownWords.value.indexOf(index)
  if (selectedIndex > -1) {
    selectedKnownWords.value.splice(selectedIndex, 1)
  } else {
    selectedKnownWords.value.push(index)
  }
}

// 确认选择
const confirmSelection = async () => {
  processing.value = true
  
  try {
    if (selectedKnownWords.value.length === 0) {
      // 没有选择任何单词，直接开始学习
      startLearning()
      return
    }

    // 将已认识的单词标记为已掌握（跳到最后一个格子）
    const knownWords = selectedKnownWords.value.map(index => currentWords.value[index])
    
    // 获取完整的单词库来找到单词的真实索引
    let allWords: Word[] = []
    if (teacherId.value) {
      allWords = wordsStore.getWordsBySetForUser(teacherId.value, wordSetName.value)
    } else {
      allWords = wordsStore.getWordsBySet(wordSetName.value)
    }

    // 标记已认识的单词为已掌握（阶段8）
    knownWords.forEach(word => {
      const wordIndexInFullSet = allWords.findIndex(w => w.id === word.id)
      if (wordIndexInFullSet !== -1) {
        progressStore.updateWordProgress(
          studentId.value,
          wordSetName.value,
          wordIndexInFullSet,
          8 // 直接跳到最后一个格子（已掌握）
        )
        console.log(`单词 ${word.english} 标记为已掌握`)
      }
    })

    // 获取可用的替换单词
    const availableReplacements = getAvailableReplacementWords(currentWords.value)
    
    if (availableReplacements.length < selectedKnownWords.value.length) {
      ElMessage.warning(`可替换的单词不足，只能替换 ${availableReplacements.length} 个单词`)
    }

    // 替换已认识的单词
    const replacementWords = shuffleArray(availableReplacements).slice(0, selectedKnownWords.value.length)
    
    // 创建新的单词列表
    const newWords = [...currentWords.value]
    selectedKnownWords.value.forEach((selectedIndex, i) => {
      if (i < replacementWords.length) {
        newWords[selectedIndex] = replacementWords[i]
      }
    })

    // 更新当前单词列表
    currentWords.value = newWords
    selectedKnownWords.value = []
    currentRound.value++

    // 检查是否达到最大轮次
    if (currentRound.value > maxRounds) {
      ElMessage.success('筛选完成，开始学习！')
      startLearning()
      return
    }

    ElMessage.success(`第${currentRound.value - 1}轮筛选完成，请继续选择认识的单词`)

  } catch (error) {
    console.error('单词筛选失败:', error)
    ElMessage.error('单词筛选失败，请重试')
  } finally {
    processing.value = false
  }
}

// 开始学习
const startLearning = () => {
  // 将筛选后的单词存储到sessionStorage中，供学习页面使用
  const wordsForLearning = currentWords.value.slice(0, wordsCount.value)
  sessionStorage.setItem('filteredWords', JSON.stringify(wordsForLearning))

  // 检查是否是继续练习（从训后检测返回）
  const continueSession = route.query.continueSession === 'true'

  let nextGroupNumber = 1

  if (continueSession) {
    // 继续练习：计算下一个 groupNumber
    for (let i = 1; i <= 100; i++) {
      const key = `simpleStudyGroup_${i}`
      if (!sessionStorage.getItem(key)) {
        nextGroupNumber = i
        break
      }
    }
    console.log(`继续练习 - 计算出的下一个 groupNumber: ${nextGroupNumber}`)
  } else {
    // 首次学习：清空之前的 sessionStorage group keys
    for (let i = 1; i <= 100; i++) {
      const key = `simpleStudyGroup_${i}`
      sessionStorage.removeItem(key)
    }
    nextGroupNumber = 1
  }

  // 跳转到第一个学习任务
  router.push({
    name: 'SimpleWordStudy',
    params: { studentId: studentId.value },
    query: {
      wordSet: wordSetName.value,
      wordsCount: wordsCount.value,
      teacherId: teacherId.value,
      filtered: 'true', // 标记这些单词已经过筛选
      groupNumber: nextGroupNumber.toString()
    }
  })
}

// 跳过筛选，直接开始学习（用于继续练习）
const skipFilterAndStartLearning = () => {
  // 计算下一个 groupNumber
  // 通过检查 sessionStorage 中已有的 group key 来确定
  let nextGroupNumber = 1
  for (let i = 1; i <= 100; i++) {
    const key = `simpleStudyGroup_${i}`
    if (!sessionStorage.getItem(key)) {
      nextGroupNumber = i
      break
    }
  }

  console.log(`继续练习 - 计算出的下一个 groupNumber: ${nextGroupNumber}`)

  // sessionStorage 中已经有更新后的 filteredWords
  // 直接跳转到学习页面
  router.push({
    name: 'SimpleWordStudy',
    params: { studentId: studentId.value },
    query: {
      wordSet: wordSetName.value,
      wordsCount: currentWords.value.length,
      teacherId: teacherId.value,
      filtered: 'true',
      groupNumber: nextGroupNumber // 传递正确的 groupNumber
    }
  })
}


// 初始化单词列表
const initializeWords = () => {
  try {
    // 检查是否是继续练习（从训后检测返回）
    const continueSession = route.query.continueSession === 'true'

    if (continueSession) {
      // 继续练习：清空之前的筛选，重新从所有可学习的单词中筛选
      console.log('继续练习模式：重新初始化单词列表')
      // 不使用 savedWords，而是重新从单词库加载
      // 继续下面的正常初始化流程
    }

    let allWords: Word[] = []

    if (teacherId.value) {
      allWords = wordsStore.getWordsBySetForUser(teacherId.value, wordSetName.value)
    } else {
      allWords = wordsStore.getWordsBySet(wordSetName.value)
    }

    if (!allWords || allWords.length === 0) {
      ElMessage.error('找不到单词集数据')
      uiStore.exitCourseMode()
      router.push({
        name: 'StudyHome',
        params: { studentId: studentId.value },
        query: {
          wordSet: wordSetName.value,
          teacherId: teacherId.value
        }
      })
      return
    }

    // 过滤出需要学习的单词（格子0-6）
    const wordsToLearn = allWords.filter((_, index) => {
      const wordProgress = progressStore.getWordProgressForUser(
        teacherId.value,
        studentId.value,
        wordSetName.value,
        index
      )
      const stage = wordProgress ? wordProgress.currentStage : 0
      return stage >= 0 && stage <= 6
    })

    if (wordsToLearn.length < wordsCount.value) {
      ElMessage.warning(`可学习单词不足，只有 ${wordsToLearn.length} 个单词可学习`)
    }

    // 随机选择要学习的单词
    const shuffledWords = shuffleArray(wordsToLearn)
    currentWords.value = shuffledWords.slice(0, wordsCount.value)

    console.log(`初始化完成，准备学习 ${currentWords.value.length} 个单词`)

  } catch (error) {
    console.error('初始化单词失败:', error)
    ElMessage.error('加载单词数据失败')
    uiStore.exitCourseMode()
    router.push({
      name: 'StudyHome',
      params: { studentId: studentId.value },
      query: {
        wordSet: wordSetName.value,
        teacherId: teacherId.value
      }
    })
  }
}

// 页面加载
onMounted(async () => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/study/' + route.params.studentId)
  }

  try {
    // 获取学生信息
    if (teacherId.value) {
      const teacherStudents = studentsStore.getStudentsByUserId(teacherId.value)
      const student = teacherStudents.find(s => s.id === studentId.value)
      if (student) {
        studentName.value = student.name
      }
    } else {
      const student = studentsStore.getStudent(studentId.value)
      if (student) {
        studentName.value = student.name
      }
    }

    if (!studentName.value) {
      ElMessage.error('找不到学生信息')
      uiStore.exitCourseMode()
      router.push({
        name: 'StudyHome',
        params: { studentId: studentId.value },
        query: {
          wordSet: wordSetName.value,
          teacherId: teacherId.value
        }
      })
      return
    }

    // 初始化单词列表
    initializeWords()

  } catch (error) {
    console.error('页面初始化失败:', error)
    ElMessage.error('页面加载失败')
    uiStore.exitCourseMode()
    router.push({
      name: 'StudyHome',
      params: { studentId: studentId.value },
      query: {
        wordSet: wordSetName.value,
        teacherId: teacherId.value
      }
    })
  }
})
</script>

<style scoped>
.word-filter {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.filter-header {
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
  color: #606266;
  font-size: 14px;
}

.filter-instructions {
  margin-bottom: 30px;
}

.words-list {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-info {
  color: #409eff;
  font-weight: 600;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.word-item {
  position: relative;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.word-item:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.word-item.selected {
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.15);
}

.word-content {
  flex: 1;
  text-align: left;
}

.english {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.word-actions {
  margin-left: 15px;
}

.pronunciation-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.selection-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background: #67c23a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-icon {
  color: white;
  font-size: 14px;
}

.filter-actions {
  margin-top: 30px;
  text-align: center;
}

.selection-summary {
  margin-bottom: 20px;
  font-size: 16px;
}

.no-selection {
  color: #67c23a;
  font-weight: 600;
}

.has-selection {
  color: #e6a23c;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

@media (max-width: 768px) {
  .words-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .action-buttons {
    flex-direction: column;
  }

  .english {
    font-size: 22px;
  }

  .word-item {
    padding: 15px;
  }

  .pronunciation-btn {
    width: 36px;
    height: 36px;
  }
}
</style>