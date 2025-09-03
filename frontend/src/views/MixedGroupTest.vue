<template>
  <div class="mixed-group-test">
    <!-- 学习进度头部 -->
    <div class="study-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 第三个学习任务（混组检测）</h2>
          <div class="progress-info">
            <span>当前检测: 第{{ currentTestingGroup }}组 | 总进度: {{ completedGroups }}/{{ totalLearningGroups }}组</span>
            <el-progress 
              :percentage="overallProgress" 
              :stroke-width="6"
              :show-text="false"
            />
          </div>
          <!-- 下一组按钮 -->
          <div class="skip-button">
            <el-button 
              type="warning" 
              @click="skipToNextGroup"
              :disabled="totalGroups >= totalLearningGroups"
              size="small"
            >
              下一组
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 任务说明 -->
    <div class="task-description">
      <el-alert
        :title="`混组检测 - 第${currentTestingGroup}组`"
        :description="`正在检测第${currentTestingGroup}组单词。需要按顺序检测第1组到第${totalGroups}组的所有单词。绿色表示掌握，红色表示需要继续学习。`"
        type="warning"
        :closable="false"
      />
    </div>

    <!-- 当前组信息 -->
    <div class="group-info">
      <el-card>
        <div class="group-status">
          <h3>第{{ currentTestingGroup }}组检测进度</h3>
          <div class="group-progress">
            <span>{{ currentGroupProgress }}/{{ currentGroupWords.length }} 个单词</span>
            <el-progress 
              :percentage="currentGroupProgressPercentage" 
              :stroke-width="8"
              status="success"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 5个单词卡区域 -->
    <div class="word-cards-area">
      <div 
        v-for="(word, index) in currentGroupWords" 
        :key="word.id"
        class="word-card-row"
      >
        <!-- 单词卡 -->
        <div 
          class="word-card" 
          :class="{ 
            'mastered': word.status === 'mastered',
            'need-review': word.status === 'need-review' 
          }"
          @click="toggleWordDisplay(index)"
        >
          <div class="word-text">
            {{ word.showChinese ? word.chinese : word.english }}
          </div>
        </div>
        
        <!-- 右侧按钮区域 -->
        <div class="card-actions" v-if="word.status === 'unchecked'">
          <el-button 
            type="success" 
            :icon="Check"
            size="large"
            @click="markWordStatus(index, 'mastered')"
            class="master-button"
          >
            掌握了
          </el-button>
          
          <el-button 
            type="danger" 
            :icon="Close"
            size="large"
            @click="markWordStatus(index, 'need-review')"
            class="review-button"
          >
            需要复习
          </el-button>
        </div>
        
        <!-- 状态标识 -->
        <div class="status-mark" v-if="word.status === 'mastered'">
          <el-button
            type="success"
            size="large"
            @click="resetWordStatus(index)"
            class="reset-button"
          >
            ✓ 掌握了 (点击重新检测)
          </el-button>
        </div>
        
        <div class="status-mark" v-if="word.status === 'need-review'">
          <el-button
            type="danger"
            size="large"
            @click="resetWordStatus(index)"
            class="reset-button"
          >
            ✗ 需要复习 (点击重新检测)
          </el-button>
        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="action-buttons">
      <el-button @click="goBack">返回</el-button>
      
      <el-button 
        v-if="currentGroupCompleted && currentTestingGroup < totalGroups"
        type="primary" 
        @click="moveToNextGroup"
        size="large"
      >
        检测下一组 (第{{ currentTestingGroup + 1 }}组)
      </el-button>
      
      <el-button 
        v-if="allGroupsCompleted && isLastLearningGroup"
        type="success" 
        @click="completeAllTests"
        size="large"
      >
        完成所有检测，进入最后一步
      </el-button>
      
      <el-button 
        v-if="allGroupsCompleted && !isLastLearningGroup"
        type="warning" 
        @click="startNextGroupLearning(false)"
        size="large"
      >
        开始学习第{{ totalGroups.value + 1 }}组单词
      </el-button>
      
      <div v-if="!currentGroupCompleted" class="completion-hint">
        <span>还有 {{ remainingWordsInGroup }} 个单词需要检测</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import { useWordsStore } from '@/stores/words'
import { useStudentsStore } from '@/stores/students'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()

// 单词接口
interface TestWord {
  id: number
  english: string
  chinese: string
  showChinese: boolean
  status: 'unchecked' | 'mastered' | 'need-review'
  groupNumber: number
}

// 响应式数据
const studentName = ref('学生')
const allGroupWords = ref<TestWord[][]>([]) // 按组存储的所有单词
const currentTestingGroup = ref(1) // 当前正在检测的组
const totalGroups = ref(1) // 当前需要检测的组数（不是总学习组数）
const totalLearningGroups = ref(1) // 总学习目标组数（例如10个单词=2组）
const completedGroups = ref(0) // 已完成的组数

// 计算属性
const currentGroupWords = computed(() => {
  return allGroupWords.value[currentTestingGroup.value - 1] || []
})

const currentGroupProgress = computed(() => {
  return currentGroupWords.value.filter(word => word.status !== 'unchecked').length
})

const currentGroupProgressPercentage = computed(() => {
  if (currentGroupWords.value.length === 0) return 0
  return Math.round((currentGroupProgress.value / currentGroupWords.value.length) * 100)
})

const currentGroupCompleted = computed(() => {
  return currentGroupWords.value.length > 0 && 
         currentGroupWords.value.every(word => word.status !== 'unchecked')
})

const allGroupsCompleted = computed(() => {
  return currentTestingGroup.value === totalGroups.value && currentGroupCompleted.value
})

const isLastLearningGroup = computed(() => {
  return totalGroups.value >= totalLearningGroups.value
})

const overallProgress = computed(() => {
  if (totalLearningGroups.value === 0) return 0
  let completedGroupsCount = completedGroups.value
  if (currentGroupCompleted.value && currentTestingGroup.value <= totalGroups.value) {
    completedGroupsCount = Math.max(completedGroups.value, currentTestingGroup.value)
  }
  return Math.round((completedGroupsCount / totalLearningGroups.value) * 100)
})

const remainingWordsInGroup = computed(() => {
  return currentGroupWords.value.filter(word => word.status === 'unchecked').length
})

// 方法
const toggleWordDisplay = (index: number) => {
  if (currentGroupWords.value[index]) {
    currentGroupWords.value[index].showChinese = !currentGroupWords.value[index].showChinese
  }
}

const markWordStatus = (index: number, status: 'mastered' | 'need-review') => {
  const word = currentGroupWords.value[index]
  if (word && word.status === 'unchecked') {
    word.status = status
    
    const statusText = status === 'mastered' ? '掌握了' : '需要复习'
    ElMessage.success(`"${word.english}" 标记为${statusText}`)
    
    // 检查当前组是否完成
    if (currentGroupCompleted.value) {
      ElMessage.success(`第${currentTestingGroup.value}组检测完成！`)
    }
    
    // 检查是否所有组都完成
    if (allGroupsCompleted.value) {
      ElMessage.success('所有组检测完成！可以进入最后一步')
    }
  }
}

const resetWordStatus = (index: number) => {
  const word = currentGroupWords.value[index]
  if (word && word.status !== 'unchecked') {
    word.status = 'unchecked'
    word.showChinese = false
    
    ElMessage.info(`"${word.english}" 重新设为未检测状态`)
  }
}

const moveToNextGroup = () => {
  if (!currentGroupCompleted.value) {
    ElMessage.warning('请先完成当前组的检测')
    return
  }
  
  if (currentTestingGroup.value < totalGroups.value) {
    completedGroups.value = Math.max(completedGroups.value, currentTestingGroup.value)
    currentTestingGroup.value++
    ElMessage.success(`开始检测第${currentTestingGroup.value}组`)
  }
}

const skipToNextGroup = async () => {
  // 检查是否已经是最后一组学习
  if (totalGroups.value >= totalLearningGroups.value) {
    ElMessage.warning('已经是最后一组了，无法跳过')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要跳过当前混组检测吗？所有未检测的单词将被标记为掌握，并直接开始第${totalGroups.value + 1}组单词学习。`,
      '确认跳过',
      {
        confirmButtonText: '确定跳过',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 将所有组的所有未检测单词标记为掌握
    allGroupWords.value.forEach(group => {
      group.forEach(word => {
        if (word.status === 'unchecked') {
          word.status = 'mastered' // 跳过的单词标记为掌握
        }
      })
    })
    
    ElMessage.success(`已跳过混组检测，开始第${totalGroups.value + 1}组单词学习`)
    
    // 直接跳转到下一组的第一个学习任务（跳过模式）
    startNextGroupLearning(true)
  } catch {
    // 用户取消
  }
}

const completeAllTests = () => {
  if (!allGroupsCompleted.value) {
    ElMessage.warning('请先完成所有组的检测')
    return
  }
  
  // 跳转到训后检测页面
  const studentId = route.params.studentId
  const wordSet = route.query.wordSet as string
  const totalWordsCount = totalLearningGroups.value * 5
  
  ElMessage.success('混组检测全部完成！进入训后检测阶段')
  
  router.push({
    name: 'PostLearningTest',
    params: { studentId },
    query: { 
      wordSet,
      totalWords: totalWordsCount,
      startIndex: 0 // 从第0个单词开始，检测所有学过的单词
    }
  })
}

const startNextGroupLearning = (skipMode = false) => {
  if (!skipMode && !allGroupsCompleted.value) {
    ElMessage.warning('请先完成当前检测')
    return
  }
  
  const studentId = route.params.studentId
  const wordSet = route.query.wordSet as string
  const nextGroupNumber = totalGroups.value + 1
  const totalWordsCount = totalLearningGroups.value * 5
  
  if (!skipMode) {
    ElMessage.success(`第${totalGroups.value}组检测完成！开始第${nextGroupNumber}组单词学习`)
  }
  
  // 跳转到第一个学习任务，学习下一组的5个单词
  router.push({
    name: 'SimpleWordStudy',
    params: { studentId },
    query: { 
      wordSet,
      wordsCount: 5,
      groupNumber: nextGroupNumber,
      totalWords: totalWordsCount, // 传递总学习单词数
      startIndex: totalGroups.value * 5 // 从当前组数*5的位置开始
    }
  })
}

const goBackToStudyHome = () => {
  const studentId = route.params.studentId
  router.push(`/study/${studentId}`)
}

const goBack = () => {
  const studentId = route.params.studentId
  router.push(`/study/${studentId}`)
}

// 初始化数据
const initializeWords = () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const completedGroupsCount = parseInt(route.query.completedGroups as string) || 1
  const totalWordsCount = parseInt(route.query.totalWords as string) || completedGroupsCount * 5
  
  // 计算总学习组数
  totalLearningGroups.value = Math.ceil(totalWordsCount / 5)
  
  // 获取指定单词集的单词
  let sourceWords = wordSetName 
    ? wordsStore.getWordsBySet(wordSetName)
    : wordsStore.words
  
  // 按组分配单词（每组5个）
  const groupedWords: TestWord[][] = []
  
  for (let i = 0; i < completedGroupsCount; i++) {
    const groupStartIndex = i * 5 // 每组的实际起始位置
    const groupWords = sourceWords.slice(groupStartIndex, groupStartIndex + 5).map((word, index) => ({
      id: word.id,
      english: word.english,
      chinese: word.chinese,
      showChinese: false,
      status: 'unchecked' as const,
      groupNumber: i + 1
    }))
    groupedWords.push(groupWords)
  }
  
  allGroupWords.value = groupedWords
  totalGroups.value = completedGroupsCount
  currentTestingGroup.value = 1
  completedGroups.value = 0
  
  ElMessage.success(`开始混组检测，需要检测第1到第${totalGroups.value}组单词 (总共${totalLearningGroups.value}组)`)
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
.mixed-group-test {
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
  flex-wrap: wrap;
  gap: 15px;
}

.header-content h2 {
  margin: 0;
  color: #303133;
  flex: 1;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 300px;
}

.progress-info span {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.skip-button {
  min-width: 100px;
}

.task-description {
  margin-bottom: 20px;
}

.group-info {
  margin-bottom: 20px;
}

.group-status h3 {
  margin: 0 0 15px 0;
  color: #303133;
  text-align: center;
}

.group-progress {
  display: flex;
  align-items: center;
  gap: 15px;
}

.group-progress span {
  min-width: 120px;
  font-size: 14px;
  color: #606266;
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

.word-card.mastered {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.word-card.need-review {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
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
  gap: 15px;
  min-width: 160px;
}

.master-button, .review-button {
  width: 100%;
  height: 55px;
  font-size: 16px;
  font-weight: 600;
}

.master-button {
  background: #52c41a;
  border-color: #52c41a;
}

.master-button:hover {
  background: #389e0d;
  border-color: #389e0d;
}

.review-button {
  background: #faad14;
  border-color: #faad14;
  color: white;
}

.review-button:hover {
  background: #d48806;
  border-color: #d48806;
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
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: auto;
  padding-top: 20px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 12px 30px;
  font-size: 16px;
}

.completion-hint {
  color: #faad14;
  font-weight: 500;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mixed-group-test {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .progress-info {
    min-width: auto;
    justify-content: center;
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
    width: 100%;
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