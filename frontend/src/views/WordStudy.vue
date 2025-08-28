<template>
  <div class="word-study-container">
    <!-- 学习进度条 -->
    <div class="progress-header">
      <el-card>
        <div class="progress-info">
          <h2>{{ studentName }} - 背单词</h2>
          <div class="stage-info">
            <el-tag :type="stageTagType">{{ stageText }}</el-tag>
            <span class="group-info">第{{ currentSession?.current_group }}组 / 共{{ currentSession?.total_groups }}组</span>
          </div>
          <el-progress 
            :percentage="progressPercentage" 
            :stroke-width="8"
            status="success"
          />
        </div>
      </el-card>
    </div>

    <!-- 第一阶段：初学 -->
    <div v-if="currentStage === 'stage1'" class="stage-content">
      <h3>第一阶段：初学单词</h3>
      <div class="word-cards-container">
        <div 
          v-for="(card, index) in wordCards" 
          :key="card.student_word_id"
          class="word-card"
          :class="{ 'completed': completedCards.includes(index) }"
        >
          <div class="card-content" @click="flipCard(index)">
            <div class="word-text">
              {{ cardFlipped[index] ? card.chinese : card.english }}
            </div>
          </div>
          <div class="card-actions">
            <el-button 
              type="success" 
              @click="markCardCompleted(index)"
              :disabled="completedCards.includes(index)"
            >
              学完了
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="stage-actions">
        <el-button 
          type="primary" 
          size="large"
          @click="completeStage1"
          :disabled="completedCards.length < wordCards.length"
        >
          进入第二阶段
        </el-button>
      </div>
    </div>

    <!-- 第二阶段：巩固 -->
    <div v-if="currentStage === 'stage2'" class="stage-content">
      <h3>第二阶段：巩固练习</h3>
      <div class="word-cards-container">
        <div 
          v-for="(card, index) in wordCards" 
          :key="card.student_word_id"
          class="word-card"
        >
          <div class="card-content" @click="flipCard(index)">
            <div class="word-text">
              {{ cardFlipped[index] ? card.chinese : card.english }}
            </div>
          </div>
          <div class="card-actions">
            <el-button 
              type="success" 
              @click="moveToBasket(index, 'green')"
              :disabled="cardResults[index] === 'green'"
            >
              认识
            </el-button>
            <el-button 
              type="danger" 
              @click="moveToBasket(index, 'red')"
              :disabled="cardResults[index] === 'red'"
            >
              不认识
            </el-button>
          </div>
        </div>
      </div>

      <!-- 篮子区域 -->
      <div class="baskets-container">
        <div class="basket green-basket" @click="showBasketWords('green')">
          <h4>认识的单词 ({{ greenBasket.length }})</h4>
          <div class="basket-preview">
            <span v-for="word in greenBasket.slice(0, 3)" :key="word.student_word_id">
              {{ word.english }}
            </span>
            <span v-if="greenBasket.length > 3">...</span>
          </div>
        </div>
        
        <div class="basket red-basket" @click="showBasketWords('red')">
          <h4>不认识的单词 ({{ redBasket.length }})</h4>
          <div class="basket-preview">
            <span v-for="word in redBasket.slice(0, 3)" :key="word.student_word_id">
              {{ word.english }}
            </span>
            <span v-if="redBasket.length > 3">...</span>
          </div>
        </div>
      </div>
      
      <div class="stage-actions">
        <el-button 
          type="primary" 
          size="large"
          @click="completeStage2"
          :disabled="greenBasket.length < wordCards.length"
        >
          {{ allWordsGreen ? '继续下一阶段' : `还有${wordCards.length - greenBasket.length}个单词需要练习` }}
        </el-button>
      </div>
    </div>

    <!-- 第三阶段：检测 -->
    <div v-if="currentStage === 'stage3'" class="stage-content">
      <h3>第三阶段：训后检测</h3>
      <p class="stage-description">测试所有学过的单词，绿色表示掌握，红色表示需要重新学习</p>
      
      <div class="word-cards-container">
        <div 
          v-for="(card, index) in wordCards" 
          :key="card.student_word_id"
          class="word-card"
          :class="{ 'tested': cardResults[index] }"
        >
          <div class="card-content" @click="flipCard(index)">
            <div class="word-text">
              {{ cardFlipped[index] ? card.chinese : card.english }}
            </div>
          </div>
          <div class="card-actions">
            <el-button 
              type="success" 
              @click="markFinalResult(index, 'green')"
              :disabled="!!cardResults[index]"
            >
              掌握了
            </el-button>
            <el-button 
              type="danger" 
              @click="markFinalResult(index, 'red')"
              :disabled="!!cardResults[index]"
            >
              没掌握
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="stage-actions">
        <el-button 
          type="primary" 
          size="large"
          @click="completeStage3"
          :disabled="Object.keys(cardResults).length < wordCards.length"
        >
          完成学习
        </el-button>
      </div>
    </div>

    <!-- 完成页面 -->
    <div v-if="sessionCompleted" class="completion-screen">
      <el-result
        icon="success"
        title="学习完成！"
        :sub-title="`成功学习了${currentSession?.words_count}个单词`"
      >
        <template #extra>
          <el-button type="primary" @click="goToLearningCenter">返回学习中心</el-button>
          <el-button @click="startNewSession">再学一组</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { learningAPI, studentAPI, type LearningSession, type WordCard } from '@/api'

const route = useRoute()
const router = useRouter()

// Props
const studentId = ref<number>(parseInt(route.params.studentId as string))

// 响应式数据
const studentName = ref<string>('')
const currentSession = ref<LearningSession | null>(null)
const currentStage = ref<string>('stage1')
const wordCards = ref<WordCard[]>([])
const sessionCompleted = ref<boolean>(false)

// 卡片状态
const cardFlipped = reactive<Record<number, boolean>>({})
const cardResults = reactive<Record<number, string>>({})
const completedCards = ref<number[]>([])

// 第二阶段篮子
const greenBasket = ref<WordCard[]>([])
const redBasket = ref<WordCard[]>([])

// 计算属性
const stageText = computed(() => {
  switch (currentStage.value) {
    case 'stage1': return '第一阶段：初学'
    case 'stage2': return '第二阶段：巩固'
    case 'stage3': return '第三阶段：检测'
    default: return '学习中'
  }
})

const stageTagType = computed(() => {
  switch (currentStage.value) {
    case 'stage1': return 'info'
    case 'stage2': return 'warning'
    case 'stage3': return 'danger'
    default: return 'info'
  }
})

const progressPercentage = computed(() => {
  if (!currentSession.value) return 0
  
  const totalStages = 3
  const currentStageNum = parseInt(currentStage.value.replace('stage', ''))
  const stageProgress = currentStageNum - 1
  
  return Math.round((stageProgress / totalStages) * 100)
})

const allWordsGreen = computed(() => {
  return greenBasket.value.length === wordCards.value.length
})

// 方法
const flipCard = (index: number) => {
  cardFlipped[index] = !cardFlipped[index]
}

const markCardCompleted = (index: number) => {
  if (!completedCards.value.includes(index)) {
    completedCards.value.push(index)
  }
}

const moveToBasket = (index: number, result: 'green' | 'red') => {
  const card = wordCards.value[index]
  
  // 从另一个篮子中移除（如果存在）
  if (result === 'green') {
    redBasket.value = redBasket.value.filter(c => c.student_word_id !== card.student_word_id)
    if (!greenBasket.value.find(c => c.student_word_id === card.student_word_id)) {
      greenBasket.value.push(card)
    }
  } else {
    greenBasket.value = greenBasket.value.filter(c => c.student_word_id !== card.student_word_id)
    if (!redBasket.value.find(c => c.student_word_id === card.student_word_id)) {
      redBasket.value.push(card)
    }
  }
  
  cardResults[index] = result
}

const showBasketWords = (basketType: 'green' | 'red') => {
  const basket = basketType === 'green' ? greenBasket.value : redBasket.value
  
  ElMessageBox.confirm(
    `是否重新选择这些单词？`,
    basketType === 'green' ? '认识的单词' : '不认识的单词',
    {
      confirmButtonText: '重新选择',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    // 重新显示这些单词卡
    basket.forEach(card => {
      const index = wordCards.value.findIndex(c => c.student_word_id === card.student_word_id)
      if (index !== -1) {
        delete cardResults[index]
      }
    })
    
    // 清空对应篮子
    if (basketType === 'green') {
      greenBasket.value = []
    } else {
      redBasket.value = []
    }
  })
}

const markFinalResult = (index: number, result: 'green' | 'red') => {
  cardResults[index] = result
}

const completeStage1 = async () => {
  try {
    const results = wordCards.value.map((card, index) => ({
      student_word_id: card.student_word_id,
      result: 'completed'
    }))
    
    await learningAPI.completeStage1({
      session_id: currentSession.value!.id,
      results
    })
    
    // 重置状态并进入第二阶段
    Object.keys(cardFlipped).forEach(key => delete cardFlipped[key])
    completedCards.value = []
    
    currentStage.value = 'stage2'
    
    ElMessage.success('第一阶段完成！')
  } catch (error) {
    ElMessage.error('完成第一阶段失败')
    console.error(error)
  }
}

const completeStage2 = async () => {
  if (!allWordsGreen.value) {
    ElMessage.warning('请确保所有单词都在绿色篮子中')
    return
  }
  
  try {
    const results = wordCards.value.map(card => ({
      student_word_id: card.student_word_id,
      result: 'green'
    }))
    
    const response = await learningAPI.completeStage2({
      session_id: currentSession.value!.id,
      results
    })
    
    if (response.next_stage === 'stage3') {
      // 进入第三阶段
      await loadStage3Words()
    } else {
      // 继续下一组
      await loadNextGroup()
    }
    
    ElMessage.success('第二阶段完成！')
  } catch (error) {
    ElMessage.error('完成第二阶段失败')
    console.error(error)
  }
}

const completeStage3 = async () => {
  try {
    const results = wordCards.value.map((card, index) => ({
      student_word_id: card.student_word_id,
      result: cardResults[index]
    }))
    
    await learningAPI.completeStage3({
      session_id: currentSession.value!.id,
      results
    })
    
    sessionCompleted.value = true
    ElMessage.success('学习完成！单词格子位置已更新')
  } catch (error) {
    ElMessage.error('完成学习失败')
    console.error(error)
  }
}

const loadNextGroup = async () => {
  try {
    currentSession.value = await learningAPI.getStage2Words(currentSession.value!.id)
    wordCards.value = currentSession.value.word_cards
    currentStage.value = 'stage1'
    
    // 重置状态
    Object.keys(cardFlipped).forEach(key => delete cardFlipped[key])
    Object.keys(cardResults).forEach(key => delete cardResults[key])
    completedCards.value = []
    greenBasket.value = []
    redBasket.value = []
  } catch (error) {
    ElMessage.error('加载下一组单词失败')
    console.error(error)
  }
}

const loadStage3Words = async () => {
  try {
    currentSession.value = await learningAPI.getStage3Words(currentSession.value!.id)
    wordCards.value = currentSession.value.word_cards
    currentStage.value = 'stage3'
    
    // 重置状态
    Object.keys(cardFlipped).forEach(key => delete cardFlipped[key])
    Object.keys(cardResults).forEach(key => delete cardResults[key])
  } catch (error) {
    ElMessage.error('加载第三阶段单词失败')
    console.error(error)
  }
}

const goToLearningCenter = () => {
  router.push('/learning')
}

const startNewSession = () => {
  router.push(`/learning`)
}

// 初始化
onMounted(async () => {
  try {
    // 获取学生信息
    const student = await studentAPI.getStudent(studentId.value)
    studentName.value = student.name
    
    // 这里应该从学习中心传递会话ID，暂时模拟
    // 实际应用中应该通过路由参数传递sessionId
    ElMessage.info('请先在学习中心开始学习会话')
    router.push('/learning')
  } catch (error) {
    ElMessage.error('加载学生信息失败')
    console.error(error)
  }
})
</script>

<style scoped>
.word-study-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.progress-header {
  margin-bottom: 30px;
}

.progress-info h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.stage-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.group-info {
  color: #606266;
  font-size: 14px;
}

.stage-content {
  margin-bottom: 30px;
}

.stage-content h3 {
  color: #303133;
  margin-bottom: 20px;
}

.stage-description {
  color: #606266;
  margin-bottom: 20px;
}

.word-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.word-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.word-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.word-card.completed {
  border: 2px solid #67c23a;
}

.word-card.tested {
  opacity: 0.7;
}

.card-content {
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.word-text {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.card-actions {
  padding: 15px;
  text-align: center;
  border-top: 1px solid #ebeef5;
}

.card-actions .el-button {
  margin: 0 5px;
}

.baskets-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 30px 0;
}

.basket {
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 120px;
}

.green-basket {
  border: 2px solid #67c23a;
}

.green-basket:hover {
  background-color: #f0f9ff;
}

.red-basket {
  border: 2px solid #f56c6c;
}

.red-basket:hover {
  background-color: #fef0f0;
}

.basket h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.basket-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  justify-content: center;
}

.basket-preview span {
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.stage-actions {
  text-align: center;
  margin-top: 30px;
}

.completion-screen {
  text-align: center;
  padding: 50px 0;
}

@media (max-width: 768px) {
  .word-cards-container {
    grid-template-columns: 1fr;
  }
  
  .baskets-container {
    grid-template-columns: 1fr;
  }
  
  .word-card .card-content {
    padding: 20px 15px;
    min-height: 80px;
  }
  
  .word-text {
    font-size: 20px;
  }
}
</style>