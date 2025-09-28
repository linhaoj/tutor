<template>
  <div class="post-learning-test">
    <!-- 学习进度头部 -->
    <div class="study-header">
      <el-card>
        <div class="header-content">
          <h2>{{ studentName }} - 训后检测</h2>
          <div class="progress-info">
            <span>总单词: {{ allWords.length }}个 | 已检测: {{ checkedCount }}/{{ allWords.length }}</span>
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
        title="训后检测说明"
        description="这是最后的训后检测环节。请对本次学习的所有单词进行最终检测。绿色按钮表示通过，红色按钮表示不通过。通过的单词将进入下一个学习阶段，不通过的单词将回到未学习状态。"
        type="success"
        :closable="false"
      />
    </div>

    <!-- 所有单词列表 -->
    <div class="words-list">
      <div 
        v-for="(word, index) in allWords" 
        :key="word.id"
        class="word-item"
      >
        <!-- 单词卡 -->
        <div 
          class="word-card" 
          :class="{ 
            'passed': word.status === 'passed',
            'failed': word.status === 'failed'
          }"
          @click="toggleWordDisplay(index)"
        >
          <div class="word-content">
            <div class="word-text">
              {{ word.showChinese ? word.chinese : word.english }}
            </div>
            <div class="word-number">#{{ index + 1 }}</div>
          </div>
        </div>
        
        <!-- 右侧按钮区域 -->
        <div class="test-actions" v-if="word.status === 'unchecked'">
          <el-button 
            type="success" 
            :icon="Check"
            size="large"
            @click="markWordStatus(index, 'passed')"
            class="pass-button"
          >
            通过
          </el-button>
          
          <el-button 
            type="danger" 
            :icon="Close"
            size="large"
            @click="markWordStatus(index, 'failed')"
            class="fail-button"
          >
            不通过
          </el-button>
        </div>
        
        <!-- 状态标识 -->
        <div class="status-mark" v-if="word.status === 'passed'">
          <el-button
            type="success"
            size="large"
            @click="resetWordStatus(index)"
            class="reset-button"
          >
            ✓ 通过 (点击重新检测)
          </el-button>
        </div>
        
        <div class="status-mark" v-if="word.status === 'failed'">
          <el-button
            type="danger"
            size="large"
            @click="resetWordStatus(index)"
            class="reset-button"
          >
            ✗ 不通过 (点击重新检测)
          </el-button>
        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="action-buttons">
      <div class="main-actions">
        <el-button
          type="primary"
          @click="continuePractice"
          size="large"
        >
          继续练习
        </el-button>

        <el-button
          type="warning"
          @click="endPracticeAndCreateAntiForget"
          size="large"
        >
          结束练习并创造抗遗忘
        </el-button>
      </div>

      <div v-if="uncheckedCount > 0" class="completion-hint">
        <span>还有 {{ uncheckedCount }} 个单词未检测</span>
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
import { useLearningProgressStore } from '@/stores/learningProgress'
import { useAntiForgetSessionStore } from '@/stores/antiForgetSession'
import { useAntiForgetStore } from '@/stores/antiForget'
import { useAuthStore } from '@/stores/auth'
import { useScheduleStore } from '@/stores/schedule'
import { useUIStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const studentsStore = useStudentsStore()
const progressStore = useLearningProgressStore()
const antiForgetSessionStore = useAntiForgetSessionStore()
const antiForgetStore = useAntiForgetStore()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const uiStore = useUIStore()

// 单词接口
interface PostTestWord {
  id: number
  english: string
  chinese: string
  showChinese: boolean
  status: 'unchecked' | 'passed' | 'failed'
  originalIndex: number // 原始索引，用于进度更新
}

// 响应式数据
const studentName = ref('学生')
const allWords = ref<PostTestWord[]>([])

// 计算属性
const checkedCount = computed(() => {
  return allWords.value.filter(word => word.status !== 'unchecked').length
})

const uncheckedCount = computed(() => {
  return allWords.value.filter(word => word.status === 'unchecked').length
})

const progressPercentage = computed(() => {
  if (allWords.value.length === 0) return 0
  return Math.round((checkedCount.value / allWords.value.length) * 100)
})

const passedWords = computed(() => {
  return allWords.value.filter(word => word.status === 'passed')
})

const failedWords = computed(() => {
  return allWords.value.filter(word => word.status === 'failed')
})

// 方法
const toggleWordDisplay = (index: number) => {
  if (allWords.value[index]) {
    allWords.value[index].showChinese = !allWords.value[index].showChinese
  }
}

const markWordStatus = (index: number, status: 'passed' | 'failed') => {
  const word = allWords.value[index]
  if (word && word.status === 'unchecked') {
    word.status = status

    // 获取当前阶段信息用于显示
    const studentId = parseInt(route.params.studentId as string)
    const wordSet = route.query.wordSet as string
    const currentProgress = progressStore.getWordProgress(studentId, wordSet, word.originalIndex)
    const currentStage = currentProgress ? currentProgress.currentStage : 0

    const statusText = status === 'passed' ? '通过' : '不通过'
    const progressText = status === 'passed' ? `（将从阶段${currentStage}进入阶段${Math.min(currentStage + 1, 7)}）` : `（保持阶段${currentStage}）`

    ElMessage.success(`"${word.english}" 标记为${statusText}${progressText}`)

    // 保存当前检测状态
    saveCurrentTestStatus()
  }
}

// 保存当前检测状态到sessionStorage
const saveCurrentTestStatus = () => {
  const wordSetName = route.query.wordSet as string || ''
  const totalWords = parseInt(route.query.totalWords as string) || 10
  const startIndex = parseInt(route.query.startIndex as string) || 0
  const studentId = parseInt(route.params.studentId as string)

  const storageKey = `postTestStatus_${studentId}_${wordSetName}_${startIndex}_${totalWords}`
  const statusData: { [key: number]: 'passed' | 'failed' | 'unchecked' } = {}

  allWords.value.forEach(word => {
    statusData[word.originalIndex] = word.status
  })

  try {
    sessionStorage.setItem(storageKey, JSON.stringify(statusData))
    console.log('已保存检测状态:', statusData)
  } catch (error) {
    console.warn('保存检测状态失败:', error)
  }
}

const resetWordStatus = (index: number) => {
  const word = allWords.value[index]
  if (word && word.status !== 'unchecked') {
    word.status = 'unchecked'
    word.showChinese = false

    ElMessage.info(`"${word.english}" 重新设为未检测状态`)

    // 保存当前检测状态
    saveCurrentTestStatus()
  }
}

const continuePractice = () => {
  // 更新学习进度
  updateLearningProgress()

  // 将通过的单词添加到抗遗忘会话
  recordPassedWordsForAntiForget()

  // 清理sessionStorage中的检测状态数据
  clearTestStatusStorage()

  // 跳转到学习进度页面，传递refresh参数让页面刷新数据
  const studentId = route.params.studentId
  const wordSet = route.query.wordSet
  const teacherId = route.query.teacherId
  router.push({
    path: `/study/${studentId}`,
    query: { wordSet, teacherId, refresh: Date.now() } // 添加teacherId和时间戳
  })

  ElMessage.success('训后检测完成！已更新学习进度，通过的单词已记录到抗遗忘会话中')
}

// 清理sessionStorage中的检测状态数据
const clearTestStatusStorage = () => {
  const wordSetName = route.query.wordSet as string || ''
  const totalWords = parseInt(route.query.totalWords as string) || 10
  const startIndex = parseInt(route.query.startIndex as string) || 0
  const studentId = parseInt(route.params.studentId as string)

  const storageKey = `postTestStatus_${studentId}_${wordSetName}_${startIndex}_${totalWords}`
  try {
    sessionStorage.removeItem(storageKey)
    console.log('已清理检测状态缓存:', storageKey)
  } catch (error) {
    console.warn('清理检测状态缓存失败:', error)
  }
}

const endPracticeAndCreateAntiForget = () => {
  // 更新学习进度
  updateLearningProgress()

  // 创建抗遗忘任务（内部会自动记录通过的单词）
  createAntiForgetTasks()

  // 标记当前课程为已完成
  markCourseAsCompleted()

  // 清理sessionStorage中的检测状态数据
  clearTestStatusStorage()

  // 完全结束课程（清除计时）
  uiStore.endCourse()
}

const markCourseAsCompleted = () => {
  try {
    const scheduleIdStr = sessionStorage.getItem('currentScheduleId')
    const teacherId = route.query.teacherId as string
    const studentId = parseInt(route.params.studentId as string)
    
    if (scheduleIdStr && teacherId && studentId) {
      const scheduleId = parseInt(scheduleIdStr)
      
      // 获取课程信息来确定扣减时长
      const schedule = scheduleStore.getSchedulesByUserId(teacherId).find(s => s.id === scheduleId)
      if (schedule) {
        // 根据课程类型扣减时长：大课(60分钟) = 1.0h，小课(30分钟) = 0.5h
        const hoursToDeduct = schedule.classType === 'big' ? 1.0 : 0.5
        
        // 扣减学生课程时长
        const success = studentsStore.deductStudentHours(studentId, hoursToDeduct, teacherId)
        if (success) {
          console.log(`学生课程时长已扣减: ${hoursToDeduct}h (${schedule.classType === 'big' ? '大课' : '小课'})`)
        } else {
          console.warn('扣减学生课程时长失败')
        }
      }
      
      // 标记课程为已完成
      scheduleStore.completeSchedule(scheduleId)
      console.log('课程已标记为完成:', scheduleId)
    } else {
      console.warn('缺少课程完成所需信息', { scheduleIdStr, teacherId, studentId })
    }
  } catch (error) {
    console.error('标记课程完成失败:', error)
  }
}

const updateLearningProgress = () => {
  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string

  if (!studentId || !wordSet) {
    ElMessage.error('缺少必要的学习信息')
    return
  }

  let promotedCount = 0
  let unchangedCount = 0
  let uncheckedCount = 0

  // 处理所有单词，不只是有明确状态的单词
  allWords.value.forEach(word => {
    // 获取当前阶段
    const currentProgress = progressStore.getWordProgress(studentId, wordSet, word.originalIndex)
    const currentStage = currentProgress ? currentProgress.currentStage : 0

    if (word.status === 'passed') {
      // 通过的单词 - 阶段+1
      const newStage = Math.min(currentStage + 1, 7)
      progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, newStage)

      if (newStage > currentStage) {
        promotedCount++
        console.log(`单词 "${word.english}" 从阶段${currentStage}进入阶段${newStage}`)
      }
    } else if (word.status === 'failed') {
      // 未通过的单词 - 保持当前阶段不变
      progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, currentStage)
      unchangedCount++
      console.log(`单词 "${word.english}" 保持在阶段${currentStage}（未通过）`)
    } else if (word.status === 'unchecked') {
      // 未检测的单词 - 如果当前阶段是0，提升到阶段1（认为已经学过）
      if (currentStage === 0) {
        const newStage = 1
        progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, newStage)
        promotedCount++
        uncheckedCount++
        console.log(`单词 "${word.english}" 从阶段${currentStage}进入阶段${newStage}（未检测视为已学习）`)
      } else {
        // 如果已经不在阶段0，保持当前阶段
        progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, currentStage)
        unchangedCount++
        console.log(`单词 "${word.english}" 保持在阶段${currentStage}（未检测但已学过）`)
      }
    }
  })

  let message = `学习进度已更新：${promotedCount}个单词进入下一阶段，${unchangedCount}个单词保持当前阶段`
  if (uncheckedCount > 0) {
    message += `，${uncheckedCount}个未检测单词视为已学习`
  }

  ElMessage.success(message)
}

const recordPassedWordsForAntiForget = () => {
  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string
  
  console.log('调试信息:', {
    studentId,
    wordSet,
    allWordsCount: allWords.value.length,
    passedWordsCount: passedWords.value.length,
    passedWords: passedWords.value
  })
  
  if (!studentId || !wordSet) {
    console.error('缺少必要参数:', { studentId, wordSet })
    return
  }
  
  if (passedWords.value.length === 0) {
    console.warn('没有通过的单词需要记录')
    return
  }
  
  // 将通过的单词转换为抗遗忘会话格式
  const passedWordsData = passedWords.value.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese
  }))
  
  // 添加到抗遗忘会话
  antiForgetSessionStore.addPassedWordsToSession(studentId, wordSet, passedWordsData)
  
  console.log(`已将 ${passedWords.value.length} 个通过的单词记录到抗遗忘会话中`)
  
  // 验证是否成功添加
  const currentSession = antiForgetSessionStore.getCurrentSession(studentId)
  console.log('当前会话单词数:', currentSession?.words.length)
}

const createAntiForgetTasks = async () => {
  const studentId = parseInt(route.params.studentId as string)
  
  if (!studentId) {
    ElMessage.error('缺少学生信息')
    return
  }
  
  // 先记录本次的通过单词到会话
  recordPassedWordsForAntiForget()
  
  // 获取当前会话（不要立即完成，先让用户看到正确的单词数量）
  const currentSession = antiForgetSessionStore.getCurrentSession(studentId)
  
  if (!currentSession || currentSession.words.length === 0) {
    ElMessage.warning('没有找到需要创建抗遗忘的单词')
    return
  }
  
  try {
    // 让用户选择抗遗忘课程的时间（此时显示正确的单词数量）
    const selectedTime = await promptForAntiForgetTime()
    
    if (!selectedTime) {
      ElMessage.info('已取消创建抗遗忘课程')
      return
    }
    
    // 现在完成会话并获取所有累积的单词
    const completedSession = antiForgetSessionStore.completeSession(studentId)
    
    if (!completedSession) {
      ElMessage.error('完成会话时出现错误')
      return
    }
    
    // 创建抗遗忘日程
    await createAntiForgetSchedule(completedSession, selectedTime)
    
    // 生成PDF文件
    await generateWordsReport(completedSession.words)
    
    ElMessage.success('抗遗忘课程已创建完成！')
    
    // 跳转到日程管理页面查看
    router.push('/')
    
  } catch (error) {
    console.error('创建抗遗忘任务失败:', error)
    console.error('错误详情:', error.message, error.stack)
    ElMessage.error(`创建抗遗忘任务失败: ${error.message || '未知错误'}`)
  }
}

const promptForAntiForgetTime = (): Promise<string | null> => {
  return new Promise((resolve) => {
    // 生成时间选项（6:00-22:00，每30分钟一个）
    const timeSlots = []
    for (let hour = 6; hour <= 22; hour++) {
      timeSlots.push(`${hour.toString().padStart(2, '0')}:00`)
      if (hour < 22) {
        timeSlots.push(`${hour.toString().padStart(2, '0')}:30`)
      }
    }

    const currentSession = antiForgetSessionStore.getCurrentSession(parseInt(route.params.studentId as string))
    const wordsCount = currentSession?.words.length || 0

    // 创建HTML字符串作为message
    const messageContent = `
      <div style="text-align: left; line-height: 1.8;">
        <p>将为您创建 <strong>${wordsCount}</strong> 个单词的抗遗忘课程。</p>
        <p><strong>抗遗忘时间安排：</strong>第1、2、3、5、7、9、12、14、17、21天</p>
        <br/>
        <div style="margin: 20px 0;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">选择上课时间：</label>
          <select id="antiForgetTimeSelect" style="width: 100%; max-width: 200px; padding: 8px 12px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 14px; background: white;">
            <option value="">请选择时间</option>
            ${timeSlots.map(time => `<option value="${time}">${time}</option>`).join('')}
          </select>
        </div>
      </div>
    `

    // 使用ElMessageBox.confirm替代
    ElMessageBox.confirm(
      messageContent,
      '设置抗遗忘时间',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
        beforeClose: (action, instance, done) => {
          if (action === 'confirm') {
            const select = document.getElementById('antiForgetTimeSelect') as HTMLSelectElement
            const selectedTime = select?.value
            
            if (!selectedTime) {
              ElMessage.warning('请选择上课时间')
              return false // 阻止关闭
            }
            
            resolve(selectedTime)
            done()
          } else {
            resolve(null)
            done()
          }
        }
      }
    ).catch(() => {
      resolve(null)
    })
  })
}

// 获取主要的单词集名称
const getMainWordSetName = (words: any[]) => {
  if (!words || words.length === 0) {
    return '未知单词集'
  }
  
  // 统计各个单词集的单词数量
  const wordSetCounts = {}
  words.forEach(word => {
    const wordSetName = word.wordSetName || '未知单词集'
    wordSetCounts[wordSetName] = (wordSetCounts[wordSetName] || 0) + 1
  })
  
  // 找到单词数量最多的单词集
  let maxCount = 0
  let mainWordSet = '未知单词集'
  
  for (const [wordSetName, count] of Object.entries(wordSetCounts)) {
    if (count > maxCount) {
      maxCount = count
      mainWordSet = wordSetName
    }
  }
  
  return mainWordSet
}

const createAntiForgetSchedule = async (session: any, time: string) => {
  try {
    const { useScheduleStore } = await import('@/stores/schedule')
    const scheduleStore = useScheduleStore()
    
    // 抗遗忘的时间间隔（天数）
    const antiForgetDays = [1, 2, 3, 5, 7, 9, 12, 14, 17, 21]
    
    const today = new Date()
    const studentId = parseInt(route.params.studentId as string)
    
    // 使用当前用户的权限获取学生数据
    const currentUser = authStore.currentUser
    if (!currentUser) {
      throw new Error('用户未登录')
    }
    
    // 获取该老师的所有学生
    const userStudents = studentsStore.getStudentsByUserId(currentUser.id)
    const student = userStudents.find(s => s.id === studentId)
    
    if (!student) {
      throw new Error('找不到学生信息')
    }
    
    // 创建抗遗忘复习会话，使用学习会话中的单词数据
    const sessionWords = session.words.map(word => ({
      id: word.id,
      english: word.english,
      chinese: word.chinese
    }))
    
    const antiForgetSessionId = antiForgetStore.createAntiForgetSession(
      studentId,
      getMainWordSetName(session.words),
      currentUser.id,
      sessionWords
    )
    
    console.log(`已创建抗遗忘复习会话，会话ID: ${antiForgetSessionId}，单词数: ${sessionWords.length}`)
    
    // 为每个抗遗忘日期创建课程
    antiForgetDays.forEach(dayOffset => {
      const targetDate = new Date(today)
      targetDate.setDate(today.getDate() + dayOffset)
      
      const dateStr = targetDate.toISOString().split('T')[0]
      
      // 创建符合Schedule接口的对象
      const scheduleData = {
        date: dateStr,
        time: time,
        studentName: student.name,
        studentId: studentId,
        wordSet: getMainWordSetName(session.words),
        type: 'review' as const, // 抗遗忘课程类型
        duration: 30, // 抗遗忘课程默认30分钟
        classType: 'small' as const, // 抗遗忘课程默认小课
        completed: false
      }
      
      scheduleStore.addSchedule(scheduleData)
    })
    
    console.log(`已成功创建 ${antiForgetDays.length} 个抗遗忘课程`)
    
  } catch (error) {
    console.error('创建抗遗忘日程失败:', error)
    console.error('创建日程错误详情:', error.message, error.stack)
    throw error
  }
}

// 中文文本处理帮助函数 - 使用拼音或英文替代
const processChinese = (text: string, doc: any, x: number, y: number, fallback?: string) => {
  if (!text) return
  
  // 由于jsPDF默认不支持中文字体，中文会显示为乱码
  // 我们使用一个更实用的方法：如果有英文备选就用英文，否则用拼音
  
  if (text.match(/[\u4e00-\u9fff]/)) {
    // 包含中文字符
    if (fallback) {
      // 优先使用英文备选
      doc.text(fallback, x, y)
    } else {
      // 没有英文备选，尝试转换为拼音或简单标识
      const pinyinText = convertToPinyin(text)
      doc.text(pinyinText, x, y)
    }
  } else {
    // 不包含中文，直接显示
    doc.text(text, x, y)
  }
}

// 中文转英文翻译函数（扩展版）
const convertToPinyin = (text: string): string => {
  // 扩展的常见单词翻译映射
  const commonWords: Record<string, string> = {
    // 系统标签
    '学生姓名': 'Student Name',
    '陪练姓名': 'Tutor Name', 
    '总单词数': 'Total Words',
    '打印时间': 'Print Time',
    '第几天': 'Day',
    '复习日期': 'Review Date',
    '遗忘词数': 'Forgotten Words',
    '单词学习报告': 'Word Learning Report',
    
    // 常见名词
    '苹果': 'apple',
    '香蕉': 'banana', 
    '橙子': 'orange',
    '葡萄': 'grape',
    '草莓': 'strawberry',
    '西瓜': 'watermelon',
    '盘子': 'plate',
    '杯子': 'cup',
    '碗': 'bowl',
    '桌子': 'table',
    '椅子': 'chair',
    '门': 'door',
    '窗户': 'window',
    '书': 'book',
    '笔': 'pen',
    '纸': 'paper',
    '水': 'water',
    '火': 'fire',
    '土': 'earth',
    '风': 'wind',
    
    // 常见动词
    '学习': 'study/learn',
    '吃': 'eat',
    '喝': 'drink', 
    '跑': 'run',
    '走': 'walk',
    '看': 'look/see',
    '听': 'listen',
    '说': 'speak/say',
    '写': 'write',
    '读': 'read',
    '睡觉': 'sleep',
    '起床': 'get up',
    
    // 常见形容词
    '大': 'big/large',
    '小': 'small',
    '高': 'tall/high',
    '矮': 'short',
    '长': 'long',
    '短': 'short',
    '好': 'good',
    '坏': 'bad',
    '新': 'new',
    '旧': 'old',
    '热': 'hot',
    '冷': 'cold',
    
    // 数字和时间
    '一': 'one',
    '二': 'two', 
    '三': 'three',
    '四': 'four',
    '五': 'five',
    '六': 'six',
    '七': 'seven',
    '八': 'eight',
    '九': 'nine',
    '十': 'ten',
    '天': 'day',
    '月': 'month',
    '年': 'year',
    
    // 人物和关系
    '人': 'person',
    '男人': 'man',
    '女人': 'woman',
    '孩子': 'child',
    '朋友': 'friend',
    '家人': 'family',
    '老师': 'teacher',
    '学生': 'student'
  }
  
  // 先检查是否有直接映射
  if (commonWords[text]) {
    return commonWords[text]
  }
  
  // 检查部分匹配（如果文本包含已知单词）
  for (const [chinese, english] of Object.entries(commonWords)) {
    if (text.includes(chinese)) {
      return text.replace(chinese, english)
    }
  }
  
  // 如果没有匹配，返回原文本（但用拼音标识代替）
  const chineseCharCount = (text.match(/[\u4e00-\u9fff]/g) || []).length
  if (chineseCharCount > 0) {
    return `(${chineseCharCount} Chinese chars)`
  }
  
  // 如果没有中文字符，直接返回
  return text
}

const generateWordsReport = async (words: any[]) => {
  try {
    // 动态导入jsPDF
    const jsPDFModule = await import('jspdf')
    const jsPDF = jsPDFModule.jsPDF || jsPDFModule.default
    
    // 创建PDF文档 - 启用Unicode支持
    const doc = new jsPDF({
      orientation: 'landscape', // 横向，方便放置3个表格
      unit: 'mm',
      format: 'a4',
      compress: true
    })
    
    // 设置默认字体和编码
    doc.setFont('helvetica')
    
    // 设置文档属性支持Unicode
    try {
      doc.setLanguage('zh-CN')
    } catch (e) {
      console.warn('Language setting failed:', e)
    }
    
    // 添加标题
    doc.setFontSize(16)
    processChinese('单词学习报告', doc, 20, 20)
    
    let yPosition = 40
    
    // 按5个单词为一组进行处理
    for (let groupIndex = 0; groupIndex < words.length; groupIndex += 15) { // 每页最多3组(15个单词)
      if (yPosition > 160) { // 如果超过页面高度，创建新页面
        doc.addPage()
        yPosition = 20
      }
      
      // 获取当前页面的3组单词（每组5个）
      const pageGroups = []
      for (let i = 0; i < 3; i++) {
        const startIndex = groupIndex + (i * 5)
        if (startIndex < words.length) {
          const group = words.slice(startIndex, Math.min(startIndex + 5, words.length))
          pageGroups.push(group)
        }
      }
      
      // 绘制3个并列的单词表格
      drawWordTables(doc, pageGroups, yPosition)
      yPosition += 80 // 单词表格高度
      
      // 在每页最后添加复习进度表格和信息表格
      if (groupIndex + 15 >= words.length || yPosition > 160) {
        yPosition += 10
        drawReviewProgressTable(doc, yPosition)
        yPosition += 60
        
        drawInfoTable(doc, yPosition, words.length)
        yPosition = 300 // 强制下一组换页
      }
    }
    
    // 在浏览器中显示PDF而不是直接下载
    const pdfBlob = doc.output('blob')
    const pdfUrl = URL.createObjectURL(pdfBlob)
    
    // 在新标签页中打开PDF
    const newWindow = window.open(pdfUrl, '_blank')
    if (newWindow) {
      newWindow.document.title = `单词学习报告_${new Date().toISOString().split('T')[0]}`
    }
    
    // 提供下载选项
    setTimeout(() => {
      ElMessageBox.confirm(
        '预览PDF报告完成，是否下载保存？',
        '下载PDF',
        {
          confirmButtonText: '下载',
          cancelButtonText: '不需要',
          type: 'info'
        }
      ).then(() => {
        const fileName = `单词学习报告_${new Date().toISOString().split('T')[0]}.pdf`
        doc.save(fileName)
        ElMessage.success(`PDF报告已下载: ${fileName}`)
      }).catch(() => {
        // 用户选择不下载，清理URL
        URL.revokeObjectURL(pdfUrl)
      })
    }, 1000)
    
    ElMessage.success('PDF报告已在新标签页中打开')
    
  } catch (error) {
    console.error('生成PDF失败:', error)
    
    // 如果jsPDF不可用，使用备用方案：生成简单的文本报告
    generateSimpleTextReport(words)
  }
}

const drawWordTables = (doc: any, pageGroups: any[][], yStart: number) => {
  const tableWidth = 85 // 每个表格宽度
  const tableSpacing = 95 // 表格间距
  const rowHeight = 15 // 行高
  const startX = 20
  
  for (let tableIndex = 0; tableIndex < pageGroups.length; tableIndex++) {
    const group = pageGroups[tableIndex]
    const tableX = startX + (tableIndex * tableSpacing)
    
    // 绘制单词行（不要标题行）
    for (let rowIndex = 0; rowIndex < group.length; rowIndex++) {
      const word = group[rowIndex]
      const rowY = yStart + (rowIndex * rowHeight)
      
      // 绘制行边框
      doc.setLineWidth(0.5)
      doc.rect(tableX, rowY, tableWidth, rowHeight)
      
      // 绘制分隔线（中间分隔英文和中文）
      doc.line(tableX + 40, rowY, tableX + 40, rowY + rowHeight)
      
      // 添加单词内容
      doc.setFontSize(10)
      
      // 英文部分
      const englishText = word.english || ''
      doc.text(englishText, tableX + 2, rowY + 10)
      
      // 中文部分 - 使用帮助函数处理
      const chineseText = word.chinese || ''
      // 传递null作为fallback，让系统自己转换
      processChinese(chineseText, doc, tableX + 42, rowY + 10)
    }
  }
}

const drawReviewProgressTable = (doc: any, yStart: number) => {
  const cellWidth = 25 // 每个单元格宽度
  const cellHeight = 15 // 单元格高度
  const startX = 20
  
  // 生成抗遗忘日期（第1、2、3、5、7、9、12、14、17、21天）
  const antiForgetDays = [1, 2, 3, 5, 7, 9, 12, 14, 17, 21]
  const today = new Date()
  
  // 绘制表格框架（3行11列）
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 11; col++) {
      const x = startX + (col * cellWidth)
      const y = yStart + (row * cellHeight)
      
      doc.setLineWidth(0.5)
      doc.rect(x, y, cellWidth, cellHeight)
      
      doc.setFontSize(9)
      
      if (row === 0) {
        // 第一行：标签列 + 天数数据
        if (col === 0) {
          processChinese('第几天', doc, x + 2, y + 10)
        } else if (col - 1 < antiForgetDays.length) {
          doc.text(antiForgetDays[col - 1].toString(), x + 8, y + 10)
        }
      } else if (row === 1) {
        // 第二行：标签列 + 复习日期
        if (col === 0) {
          processChinese('复习日期', doc, x + 2, y + 10)
        } else if (col - 1 < antiForgetDays.length) {
          const targetDate = new Date(today)
          targetDate.setDate(today.getDate() + antiForgetDays[col - 1])
          const dateStr = `${String(targetDate.getMonth() + 1).padStart(2, '0')}-${String(targetDate.getDate()).padStart(2, '0')}`
          doc.text(dateStr, x + 3, y + 10)
        }
      } else if (row === 2) {
        // 第三行：标签列 + 遗忘词数（留空供填写）
        if (col === 0) {
          processChinese('遗忘词数', doc, x + 2, y + 10)
        }
        // 其他列留空供用户填写
      }
    }
  }
}

const drawInfoTable = (doc: any, yStart: number, totalWords: number) => {
  const tableWidth = 270 // 表格宽度
  const tableHeight = 40 // 表格高度
  const startX = 20
  
  // 绘制大框
  doc.setLineWidth(0.5)
  doc.rect(startX, yStart, tableWidth, tableHeight)
  
  // 获取学生姓名
  const studentId = parseInt(route.params.studentId as string)
  const currentUser = authStore.currentUser
  if (!currentUser) {
    ElMessage.error('用户未登录')
    return
  }
  
  const userStudents = studentsStore.getStudentsByUserId(currentUser.id)
  const student = userStudents.find(s => s.id === studentId)
  const studentName = student ? student.name : '未知学生'
  
  // 填写信息
  doc.setFontSize(12)
  processChinese(`学生姓名: ${studentName}`, doc, startX + 10, yStart + 15)
  processChinese('陪练姓名: lyb', doc, startX + 120, yStart + 15)
  processChinese(`总单词数: ${totalWords}`, doc, startX + 200, yStart + 15)
  processChinese(`打印时间: ${new Date().toLocaleDateString('zh-CN')}`, doc, startX + 10, yStart + 30)

}

const generateSimpleTextReport = (words: any[]) => {
  // 备用方案：生成简单的文本报告
  let content = `单词学习报告\n生成时间: ${new Date().toLocaleString('zh-CN')}\n总单词数: ${words.length}\n\n`
  
  words.forEach((word, index) => {
    content += `${index + 1}. ${word.english} - ${word.chinese}\n`
  })
  
  // 创建下载链接
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `单词学习报告_${new Date().toISOString().split('T')[0]}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('文本报告已生成下载')
}


// 初始化数据
const initializeWords = () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const totalWords = parseInt(route.query.totalWords as string) || 10
  const startIndex = parseInt(route.query.startIndex as string) || 0
  const studentId = parseInt(route.params.studentId as string)

  // 获取指定单词集的单词
  let sourceWords = wordSetName
    ? wordsStore.getWordsBySet(wordSetName)
    : wordsStore.words

  // 获取本次学习的所有单词
  sourceWords = sourceWords.slice(startIndex, startIndex + totalWords)

  // 尝试从sessionStorage恢复之前的检测状态
  const storageKey = `postTestStatus_${studentId}_${wordSetName}_${startIndex}_${totalWords}`
  let savedStatus: { [key: number]: 'passed' | 'failed' | 'unchecked' } = {}

  try {
    const saved = sessionStorage.getItem(storageKey)
    if (saved) {
      savedStatus = JSON.parse(saved)
      console.log('恢复了之前的检测状态:', savedStatus)
    }
  } catch (error) {
    console.warn('无法恢复检测状态:', error)
  }

  // 转换为训后检测用的单词格式
  allWords.value = sourceWords.map((word, index) => {
    const originalIndex = startIndex + index
    const savedWordStatus = savedStatus[originalIndex] || 'unchecked'

    return {
      id: word.id,
      english: word.english,
      chinese: word.chinese,
      showChinese: false,
      status: savedWordStatus,
      originalIndex // 保存原始索引用于进度更新
    }
  })

  ElMessage.success(`开始训后检测，共 ${allWords.value.length} 个单词`)
}

// 生命周期
onMounted(() => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/study/' + route.params.studentId)
  }

  // 获取学生信息
  const studentId = parseInt(route.params.studentId as string)
  if (studentId) {
    const currentUser = authStore.currentUser
    if (currentUser) {
      const userStudents = studentsStore.getStudentsByUserId(currentUser.id)
      const student = userStudents.find(s => s.id === studentId)
      if (student) {
        studentName.value = student.name
      }
    }
  }

  // 初始化单词数据
  initializeWords()
})
</script>

<style scoped>
.post-learning-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 15px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #fefefe;
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
  min-width: 300px;
}

.progress-info span {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.task-description {
  margin-bottom: 20px;
}

/* 单词列表 */
.words-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.word-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  border-radius: 10px;
  background: #f8fdf8;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.word-item:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.word-card {
  flex: 1;
  background: linear-gradient(135deg, #81c784 0%, #66bb6a 100%);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border: 1px solid rgba(129, 199, 132, 0.3);
}

.word-card:hover {
  background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(76, 175, 80, 0.2);
}

.word-card.passed {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  border-color: rgba(76, 175, 80, 0.5);
}

.word-card.failed {
  background: linear-gradient(135deg, #ef5350 0%, #d32f2f 100%);
  border-color: rgba(239, 83, 80, 0.5);
}

.word-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.word-text {
  font-size: 22px;
  font-weight: 600;
  color: #1b5e20;
  text-align: left;
  line-height: 1.4;
  word-break: break-word;
  flex: 1;
  text-shadow: 0 1px 2px rgba(255,255,255,0.7);
}

.word-number {
  font-size: 13px;
  color: #2e7d32;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(255,255,255,0.7);
}

.test-actions {
  display: flex;
  flex-direction: row;
  gap: 15px;
  min-width: 200px;
}

.pass-button, .fail-button {
  flex: 1;
  height: 50px;
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
  min-width: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.reset-button {
  width: 100%;
  height: 50px;
  font-size: 14px;
  font-weight: 600;
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-top: auto;
  padding-top: 30px;
}

.main-actions {
  display: flex;
  gap: 20px;
}

.action-buttons .el-button {
  padding: 15px 40px;
  font-size: 16px;
}

.completion-hint {
  color: #f5222d;
  font-weight: 500;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .post-learning-test {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .progress-info {
    min-width: auto;
    justify-content: center;
  }
  
  .word-item {
    flex-direction: column;
    gap: 15px;
  }
  
  .test-actions, .status-mark {
    min-width: auto;
    width: 100%;
  }
  
  .word-text {
    font-size: 20px;
  }
  
  .main-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .main-actions .el-button {
    width: 100%;
  }
}
</style>