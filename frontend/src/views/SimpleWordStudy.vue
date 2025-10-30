<template>
  <div class="simple-word-study">
    <!-- 课程计时器 -->
    <CourseTimer @time-expired="handleTimeExpired" />

    <!-- 学习进度头部 -->
    <div class="study-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 单词学习</h2>
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
          
          <!-- 发音按钮 -->
          <el-button 
            type="primary" 
            :icon="VideoPlay"
            size="large"
            @click="speakWord(word.english)"
            class="speak-button"
          >
            发音
          </el-button>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Box, VideoPlay } from '@element-plus/icons-vue'
import { useWordsStore } from '@/stores/words'
import { useStudentsStore } from '@/stores/students'
import { useLearningProgressStore } from '@/stores/learningProgress'
import { useUIStore } from '@/stores/ui'
import CourseTimer from '@/components/CourseTimer.vue'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()
const progressStore = useLearningProgressStore()
const uiStore = useUIStore()

// 单词接口
interface StudyWord {
  id: number
  english: string
  chinese: string
  showChinese: boolean
  movedToBox: boolean
  originalIndex?: number // 单词在完整单词库中的索引
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

    ElMessage({
      message: `"${word.english}" 已学完`,
      type: 'success'
    })

    // 检查当前组是否全部完成
    if (currentGroupCompleted.value) {
      ElMessage({
        message: '当前组的5个单词已全部学完！',
        type: 'success'
      })
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
  
  // 找到displayWords中对应的单词并恢复状态
  const displayIndex = displayWords.value.findIndex(w => w.id === word.id)
  if (displayIndex !== -1) {
    displayWords.value[displayIndex].movedToBox = false
    displayWords.value[displayIndex].showChinese = false
  } else {
    // 如果不在displayWords中，检查是否有空位可以添加
    const activeWordsInDisplay = displayWords.value.filter(w => !w.movedToBox).length
    if (activeWordsInDisplay < 5) {
      displayWords.value.push({
        ...word,
        movedToBox: false,
        showChinese: false
      })
    }
  }
  
  // 更新完成数量
  completedWords.value--
  
  ElMessage({ message: `"${word.english}" 已移回卡片区域`, type: 'info' })
}

const speakWord = (text: string) => {
  console.log('=== speakWord 被调用 ===', text)

  if (!('speechSynthesis' in window)) {
    console.log('speechSynthesis 不可用')
    ElMessage({
      message: '您的浏览器不支持语音功能',
      type: 'warning'
    })
    return
  }

  console.log('speechSynthesis 可用')
  console.log('paused:', window.speechSynthesis.paused)
  console.log('speaking:', window.speechSynthesis.speaking)
  console.log('pending:', window.speechSynthesis.pending)

  // Chrome 需要先 resume 才能播放
  if (window.speechSynthesis.paused) {
    console.log('调用 resume()')
    window.speechSynthesis.resume()
  }

  // 停止当前播放
  console.log('调用 cancel()')
  window.speechSynthesis.cancel()

  const speak = () => {
    console.log('>>> speak() 函数开始执行')

    // 创建 utterance
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US'
    utterance.rate = 0.9
    utterance.volume = 1
    utterance.pitch = 1

    console.log('utterance 已创建:', {
      text: utterance.text,
      lang: utterance.lang,
      rate: utterance.rate,
      volume: utterance.volume
    })

    // 获取语音列表并设置
    const voices = window.speechSynthesis.getVoices()
    console.log('可用语音数量:', voices.length)

    const enVoices = voices.filter(v => v.lang.startsWith('en'))
    console.log('英文语音数量:', enVoices.length)

    if (enVoices.length > 0) {
      const usVoice = enVoices.find(v => v.lang === 'en-US') || enVoices[0]
      utterance.voice = usVoice
      console.log('使用语音:', usVoice.name, usVoice.lang)
    }

    utterance.onstart = () => {
      console.log('✅ 开始播放:', text)
    }

    utterance.onend = () => {
      console.log('✅ 播放结束:', text)
    }

    utterance.onerror = (event) => {
      console.error('❌ 播放错误:', event.error, event)
    }

    // Chrome 修复：在调用 speak 前先 resume
    console.log('调用 resume() before speak')
    window.speechSynthesis.resume()

    console.log('调用 speak()')
    window.speechSynthesis.speak(utterance)

    console.log('speak() 调用完成，检查状态:')
    setTimeout(() => {
      console.log('50ms 后状态 - speaking:', window.speechSynthesis.speaking, 'pending:', window.speechSynthesis.pending)
    }, 50)
  }

  // 获取语音列表
  console.log('获取语音列表...')
  const voices = window.speechSynthesis.getVoices()
  console.log('当前语音数量:', voices.length)

  if (voices.length === 0) {
    // 等待语音加载
    console.log('语音未加载，等待 voiceschanged 事件')
    window.speechSynthesis.addEventListener('voiceschanged', function handler() {
      console.log('voiceschanged 事件触发')
      window.speechSynthesis.removeEventListener('voiceschanged', handler)
      speak()
    }, { once: true })
  } else {
    console.log('语音已加载，直接调用 speak()')
    speak()
  }
}

const startNextGroup = () => {
  if (!currentGroupCompleted.value) {
    ElMessage({
      message: '请先完成当前组的所有单词',
      type: 'warning'
    })
    return
  }

  if (remainingWords.value.length === 0) {
    ElMessage({
      message: '恭喜！所有单词都已学完',
      type: 'success'
    })
    return
  }
  
  // 清空当前显示和小盒子
  displayWords.value = []
  boxWords.value = []
  
  // 加载下一组的5个单词
  loadNextGroup()

  currentRound.value++
  ElMessage({
    message: `开始第 ${currentRound.value} 组学习`,
    type: 'success'
  })
}

const goToNextTask = () => {
  if (!currentGroupCompleted.value) {
    ElMessage({
      message: '请先完成当前组的所有单词',
      type: 'warning'
    })
    return
  }

  // 保存当前组的单词到sessionStorage，供WordCheckTask使用
  const groupNumber = parseInt(route.query.groupNumber as string) || 1
  const sessionKey = `simpleStudyGroup_${groupNumber}`
  const currentGroupWords = displayWords.value.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese,
    originalIndex: word.originalIndex // 保存原始索引
  }))
  sessionStorage.setItem(sessionKey, JSON.stringify(currentGroupWords))
  console.log(`SimpleWordStudy - 已保存第${groupNumber}组单词到sessionStorage:`, currentGroupWords.map(w => w.english))

  // 注意：不再立即更新后端进度，只在最终提交时更新
  // 临时数据保存在sessionStorage中

  // 获取总学习单词数
  const totalWordsCount = parseInt(route.query.totalWords as string) || allWords.value.length

  // 跳转到第二个学习任务（检查任务）
  router.push({
    name: 'WordCheckTask',
    params: { studentId: route.params.studentId },
    query: {
      wordSet: route.query.wordSet,
      wordsCount: 5,
      groupNumber,
      totalWords: totalWordsCount, // 传递总学习单词数
      startIndex: route.query.startIndex, // 传递起始位置
      teacherId: route.query.teacherId, // 传递教师ID
      learningMode: route.query.learningMode, // 传递学习模式
      filtered: route.query.filtered // 传递筛选标记
    }
  })

  ElMessage({
    message: '第一个任务完成！进入第二个学习任务：检查阶段',
    type: 'success'
  })
}

/**
 * 处理课程时间到达（60分钟自动结束）
 * 直接跳转到训后检测，不再继续学习
 */
const handleTimeExpired = () => {
  console.log('⏰ 课程时间已到，自动跳转到训后检测')

  // 获取当前组号
  const groupNumber = parseInt(route.query.groupNumber as string) || 1

  // 🚨 关键：保存当前组已学习的单词到sessionStorage（保存displayWords，即当前正在学习的5个单词）
  const sessionKey = `simpleStudyGroup_${groupNumber}`
  const learnedWords = displayWords.value.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese,
    originalIndex: word.originalIndex
  }))
  sessionStorage.setItem(sessionKey, JSON.stringify(learnedWords))
  console.log(`⏰ 自动结束 - 已保存第${groupNumber}组单词(${learnedWords.length}个):`, learnedWords.map(w => w.english))

  const currentBatchStartGroup = 1  // 批次总是从第1组开始
  const currentBatchGroupCount = groupNumber  // 已经学习到第几组
  const totalWordsCount = groupNumber * 5  // 实际学习的单词数

  console.log('⏰ SimpleWordStudy自动结束 - 训后检测参数:', {
    groupNumber,
    currentBatchStartGroup,
    currentBatchGroupCount,
    totalWordsCount
  })

  ElMessage({
    message: '⏰ 课程时间已到，自动进入训后检测',
    type: 'warning',
    duration: 3000
  })

  // 延迟1秒后跳转，让用户看到提示
  setTimeout(() => {
    router.push({
      name: 'PostLearningTest',
      params: { studentId: route.params.studentId },
      query: {
        wordSet: route.query.wordSet,
        totalWords: totalWordsCount,
        startIndex: 0,
        teacherId: route.query.teacherId,
        learningMode: route.query.learningMode,
        filtered: route.query.filtered,
        currentBatchStartGroup: currentBatchStartGroup,
        currentBatchGroupCount: currentBatchGroupCount,
        autoEnd: 'true'  // 标记为自动结束
      }
    })
  }, 1000)
}

const completeAllLearning = () => {
  ElMessage({
    message: '恭喜！所有单词学习完成！',
    type: 'success'
  })
  setTimeout(() => {
    uiStore.exitCourseMode()
    const studentId = route.params.studentId
    router.push(`/study/${studentId}`)
  }, 2000)
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

const loadNextGroup = async () => {
  console.log('=== 加载新组单词 ===')
  console.log('allWords 总数:', allWords.value.length)
  console.log('allWords 内容:', allWords.value.map(w => `${w.english}(moved:${w.movedToBox})`))
  console.log('remainingWords 数量:', remainingWords.value.length)
  console.log('remainingWords 内容:', remainingWords.value.map(w => w.english))

  // 关键修复：先打乱剩余单词，再取前5个
  // 这样每次加载新组时，都会从不同位置随机选择5个单词
  const shuffledRemaining = shuffleArray([...remainingWords.value])
  console.log('剩余单词（打乱后）:', shuffledRemaining.map(w => w.english))

  const wordsToLoad = shuffledRemaining.slice(0, 5)
  console.log('本组将加载的单词:', wordsToLoad.map(w => w.english))

  // 再次打乱这组5个单词的显示顺序
  const shuffledWords = shuffleArray(wordsToLoad)
  console.log('本组单词（最终显示顺序）:', shuffledWords.map(w => w.english))

  displayWords.value = shuffledWords.map(word => ({ ...word, showChinese: false }))

  console.log('displayWords 已更新:', displayWords.value.map(w => w.english))

  // 等待DOM更新完成
  await nextTick()
  console.log('DOM已更新完成')
}


// 初始化数据
const initializeWords = async () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const wordsCount = parseInt(route.query.wordsCount as string) || 20
  const startIndex = parseInt(route.query.startIndex as string) || 0
  const teacherId = route.query.teacherId as string || ''
  let isFiltered = route.query.filtered === 'true' // 检查是否经过筛选

  let sourceWords = []

  if (isFiltered) {
    // 如果是经过筛选的单词，从sessionStorage获取
    try {
      const filteredWords = sessionStorage.getItem('filteredWords')
      if (filteredWords) {
        sourceWords = JSON.parse(filteredWords)
        console.log('SimpleWordStudy - 使用筛选后的单词:', sourceWords.length)

        // 关键修复：根据startIndex和wordsCount截取当前组的单词
        sourceWords = sourceWords.slice(startIndex, startIndex + wordsCount)
        console.log(`SimpleWordStudy - 当前组单词 (startIndex=${startIndex}, wordsCount=${wordsCount}):`, sourceWords.map((w: any) => w.english))
      } else {
        console.warn('未找到筛选后的单词，使用默认逻辑')
        isFiltered = false
      }
    } catch (error) {
      console.error('获取筛选后的单词失败:', error)
    }
  }

  if (!isFiltered) {
    // 使用原有逻辑获取单词（使用异步方法，后端API自动处理权限）
    sourceWords = wordSetName
      ? await wordsStore.getWordsBySet(wordSetName)
      : wordsStore.words

    console.log('SimpleWordStudy - 加载单词数据:', {
      teacherId,
      wordSetName,
      wordsCount: sourceWords.length
    })

    // 从指定位置开始，取指定数量的单词
    sourceWords = sourceWords.slice(startIndex, startIndex + wordsCount)
  }

  // 注意：不要在这里打乱全部单词顺序
  // 因为我们要保证每组学习时都是随机的，而不是整体随机后再分组

  console.log('=== 初始化单词 ===')
  console.log('源单词（原始顺序）:', sourceWords.map((w: any) => w.english))

  // 转换为学习用的单词格式（保持原始顺序）
  allWords.value = sourceWords.map((word: any) => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese,
    showChinese: false,
    movedToBox: false,
    originalIndex: word.originalIndex // 保留原始索引（从filteredWords传递过来）
  }))

  console.log('SimpleWordStudy - 准备学习单词数量:', allWords.value.length)
  console.log('allWords 初始内容（原始顺序）:', allWords.value.map(w => w.english))

  // 加载第一组的5个单词（loadNextGroup会自动打乱）
  await loadNextGroup()

  const groupNumber = parseInt(route.query.groupNumber as string) || 1
  ElMessage({
    message: `开始第${groupNumber}组学习，共 ${allWords.value.length} 个单词`,
    type: 'success'
  })
}

// 生命周期
onMounted(async () => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/study/' + route.params.studentId)
  }

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
  await initializeWords()
})
</script>

<style scoped>
.simple-word-study {
  max-width: 800px;
  margin: 0 auto;
  padding: 15px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #fefefe;
}

.study-header {
  margin-bottom: 30px;
}

.header-content {
  text-align: center;
}

.header-content h2 {
  margin: 0;
  color: #303133;
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
  gap: 15px;
  padding: 8px;
  border-radius: 10px;
  background: #f8fdf8;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.word-card-row:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.word-card {
  flex: 1;
  background: linear-gradient(135deg, #81c784 0%, #66bb6a 100%);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(129, 199, 132, 0.3);
}

.word-card:hover {
  background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(76, 175, 80, 0.2);
}

.word-card.moved-to-box {
  background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
  opacity: 0.8;
  border-color: rgba(165, 214, 167, 0.5);
}

.word-text {
  font-size: 24px;
  font-weight: 600;
  color: #1b5e20;
  text-align: center;
  line-height: 1.4;
  word-break: break-word;
  padding: 15px;
  text-shadow: 0 1px 2px rgba(255,255,255,0.7);
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
}

.move-button {
  width: 100%;
  height: 42px;
  font-size: 14px;
  font-weight: 600;
}

.speak-button {
  width: 100%;
  height: 36px;
  font-size: 13px;
  font-weight: 500;
  background: #42a5f5;
  border-color: #42a5f5;
}

.speak-button:hover {
  background: #1e88e5;
  border-color: #1e88e5;
}

.completed-mark {
  min-width: 120px;
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
  min-height: 100px;
  border: 2px dashed #c8e6c9;
  border-radius: 10px;
  padding: 15px;
  background: #f1f8e9;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.word-box.has-words {
  border-color: #4caf50;
  background: #e8f5e8;
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
@media (max-width: 600px) {
  .simple-word-study {
    padding: 10px;
    max-width: 100%;
  }

  .header-content {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .word-card-row {
    gap: 10px;
    padding: 6px;
  }

  .word-card {
    min-height: 80px;
  }

  .word-text {
    font-size: 20px;
    padding: 10px;
  }

  .card-actions {
    min-width: 100px;
  }

  .move-button {
    height: 38px;
    font-size: 13px;
  }

  .speak-button {
    height: 32px;
    font-size: 12px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 10px;
  }
}

@media (max-width: 400px) {
  .word-text {
    font-size: 18px;
  }

  .card-actions {
    min-width: 90px;
  }
}
</style>