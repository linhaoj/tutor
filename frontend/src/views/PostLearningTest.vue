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
import { useStudentReviewsStore } from '@/stores/studentReviews'

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
const studentReviewsStore = useStudentReviewsStore()

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

  // 跳转到 WordFilter 页面，继续使用之前筛选的单词
  const studentId = route.params.studentId
  const wordSet = route.query.wordSet
  const teacherId = route.query.teacherId
  const totalWords = route.query.totalWords

  router.push({
    path: `/word-filter/${studentId}`,
    query: {
      wordSet,
      teacherId,
      wordsCount: totalWords, // 保持原来的总单词数
      continueSession: 'true' // 标记为继续练习
    }
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
      
      // 使用跨用户方法标记课程为已完成
      scheduleStore.completeScheduleForUser(teacherId, scheduleId)
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
  const teacherId = route.query.teacherId as string

  if (!studentId || !wordSet || !teacherId) {
    ElMessage.error('缺少必要的学习信息')
    return
  }

  let promotedCount = 0
  let unchangedCount = 0
  let uncheckedCount = 0

  // 处理所有单词，不只是有明确状态的单词
  allWords.value.forEach(word => {
    // 使用跨用户方法获取当前阶段
    const currentProgress = progressStore.getWordProgressForUser(teacherId, studentId, wordSet, word.originalIndex)
    const currentStage = currentProgress ? currentProgress.currentStage : 0

    if (word.status === 'passed') {
      // 通过的单词 - 阶段+1
      const newStage = Math.min(currentStage + 1, 7)
      progressStore.updateWordProgressForUser(teacherId, studentId, wordSet, word.originalIndex, newStage)

      if (newStage > currentStage) {
        promotedCount++
        console.log(`单词 "${word.english}" 从阶段${currentStage}进入阶段${newStage}`)
      }
    } else if (word.status === 'failed') {
      // 未通过的单词 - 保持当前阶段不变
      progressStore.updateWordProgressForUser(teacherId, studentId, wordSet, word.originalIndex, currentStage)
      unchangedCount++
      console.log(`单词 "${word.english}" 保持在阶段${currentStage}（未通过）`)
    } else if (word.status === 'unchecked') {
      // 未检测的单词 - 如果当前阶段是0，提升到阶段1（认为已经学过）
      if (currentStage === 0) {
        const newStage = 1
        progressStore.updateWordProgressForUser(teacherId, studentId, wordSet, word.originalIndex, newStage)
        promotedCount++
        uncheckedCount++
        console.log(`单词 "${word.english}" 从阶段${currentStage}进入阶段${newStage}（未检测视为已学习）`)
      } else {
        // 如果已经不在阶段0，保持当前阶段
        progressStore.updateWordProgressForUser(teacherId, studentId, wordSet, word.originalIndex, currentStage)
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

    // 生成PDF文件（使用会话中的所有通过单词）
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
    const teacherId = route.query.teacherId as string // 获取教师ID
    const currentWordSet = route.query.wordSet as string // 获取当前单词集

    // 使用当前用户的权限获取学生数据
    const currentUser = authStore.currentUser
    if (!currentUser) {
      throw new Error('用户未登录')
    }

    // 使用teacherId获取学生数据（支持跨用户访问）
    const userIdForStudent = teacherId || currentUser.id
    const userStudents = studentsStore.getStudentsByUserId(userIdForStudent)
    const student = userStudents.find(s => s.id === studentId)

    if (!student) {
      throw new Error('找不到学生信息')
    }

    // 使用会话中的所有通过单词（不过滤，因为会话中的单词应该都是本次学习的）
    console.log(`会话总单词数: ${session.words.length}, 单词集: ${currentWordSet}`)

    // 创建抗遗忘复习会话，使用所有通过的单词
    const sessionWords = session.words.map((word: any) => ({
      id: word.id,
      english: word.english,
      chinese: word.chinese
    }))

    // 使用teacherId作为会话的创建者（保持数据一致性）
    const sessionTeacherId = teacherId || currentUser.id
    const antiForgetSessionId = antiForgetStore.createAntiForgetSession(
      studentId,
      currentWordSet,
      sessionTeacherId,
      sessionWords
    )

    console.log(`已创建抗遗忘复习会话，会话ID: ${antiForgetSessionId}，teacherId: ${sessionTeacherId}，单词集: ${currentWordSet}，单词数: ${sessionWords.length}`)

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
        wordSet: currentWordSet,
        type: 'review' as const, // 抗遗忘课程类型
        duration: 30, // 抗遗忘课程默认30分钟
        classType: 'small' as const, // 抗遗忘课程默认小课
        completed: false
      }
      
      scheduleStore.addSchedule(scheduleData)
    })
    
    console.log(`已成功创建 ${antiForgetDays.length} 个抗遗忘课程`)

    // 同步复习记录到学生账号
    syncReviewToStudent(studentId, currentWordSet, today.toISOString().split('T')[0], sessionWords)

  } catch (error) {
    console.error('创建抗遗忘日程失败:', error)
    console.error('创建日程错误详情:', error.message, error.stack)
    throw error
  }
}

// 同步复习记录到学生账号
const syncReviewToStudent = (
  studentId: number,
  wordSetName: string,
  learnDate: string,
  words: { id: number; english: string; chinese: string }[]
) => {
  try {
    // 创建学生复习记录
    const reviewId = studentReviewsStore.createReview(
      studentId,
      wordSetName,
      learnDate,
      words
    )

    console.log(`已同步复习记录到学生账号: 学生ID=${studentId}, 复习ID=${reviewId}, 单词数=${words.length}`)
  } catch (error) {
    console.error('同步学生复习记录失败:', error)
    // 不抛出错误，避免影响主流程
  }
}

// 创建HTML内容用于PDF生成
// mode: 'both' = 中英对照, 'english' = 只显示英文, 'chinese' = 只显示中文
const createPDFHtmlContent = (words: any[], studentName: string, teacherName: string, mode: 'both' | 'english' | 'chinese' = 'both'): string => {
  const antiForgetDays = [1, 2, 3, 5, 7, 9, 12, 14, 17, 21]
  const today = new Date()

  // 生成单词表格HTML
  const generateWordTables = (pageWords: any[]) => {
    const tables = []
    for (let i = 0; i < 3; i++) {
      const startIdx = i * 5
      const endIdx = Math.min(startIdx + 5, pageWords.length)
      if (startIdx >= pageWords.length) break

      const wordsInTable = pageWords.slice(startIdx, endIdx)

      // 根据mode决定显示内容
      const rows = wordsInTable.map(word => {
        if (mode === 'both') {
          // 中英对照：两列
          return `
            <tr>
              <td style="width: 40%; padding: 8px; border: 1px solid #333;">${word.english}</td>
              <td style="width: 60%; padding: 8px; border: 1px solid #333;">${word.chinese}</td>
            </tr>
          `
        } else if (mode === 'english') {
          // 只显示英文：左边英文，右边留白
          return `
            <tr>
              <td style="width: 40%; padding: 8px; border: 1px solid #333;">${word.english}</td>
              <td style="width: 60%; padding: 8px; border: 1px solid #333;">&nbsp;</td>
            </tr>
          `
        } else {
          // 只显示中文：左边留白，右边中文
          return `
            <tr>
              <td style="width: 40%; padding: 8px; border: 1px solid #333;">&nbsp;</td>
              <td style="width: 60%; padding: 8px; border: 1px solid #333;">${word.chinese}</td>
            </tr>
          `
        }
      }).join('')

      tables.push(`
        <table style="width: 30%; border-collapse: collapse; margin-right: 15px; display: inline-table; vertical-align: top;">
          ${rows}
        </table>
      `)
    }
    return tables.join('')
  }

  // 生成复习进度表格
  const generateReviewTable = () => {
    const dayRow = antiForgetDays.map(day => `<td style="border: 1px solid #333; padding: 5px; text-align: center;">${day}</td>`).join('')
    const dateRow = antiForgetDays.map(day => {
      const date = new Date(today)
      date.setDate(today.getDate() + day)
      return `<td style="border: 1px solid #333; padding: 5px; text-align: center;">${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}</td>`
    }).join('')
    const emptyRow = antiForgetDays.map(() => `<td style="border: 1px solid #333; padding: 5px;">&nbsp;</td>`).join('')

    return `
      <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <tr>
          <td style="border: 1px solid #333; padding: 5px; width: 80px; font-weight: bold;">第几天</td>
          ${dayRow}
        </tr>
        <tr>
          <td style="border: 1px solid #333; padding: 5px; font-weight: bold;">复习日期</td>
          ${dateRow}
        </tr>
        <tr>
          <td style="border: 1px solid #333; padding: 5px; font-weight: bold;">遗忘词数</td>
          ${emptyRow}
        </tr>
      </table>
    `
  }

  // 生成信息表格
  const generateInfoTable = () => {
    return `
      <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <tr>
          <td style="border: 1px solid #333; padding: 15px;">
            <div style="margin-bottom: 10px;"><strong>学生姓名:</strong> ${studentName}</div>
            <div style="margin-bottom: 10px;"><strong>教师姓名:</strong> ${teacherName}</div>
            <div style="margin-bottom: 10px;"><strong>总单词数:</strong> ${words.length}</div>
            <div><strong>打印时间:</strong> ${new Date().toLocaleDateString('zh-CN')}</div>
          </td>
        </tr>
      </table>
    `
  }

  // 生成所有页面
  let htmlContent = `
    <div style="width: 1100px; padding: 20px; font-family: 'Microsoft YaHei', 'SimSun', Arial, sans-serif; background: white;">
      <h2 style="text-align: center; margin-bottom: 30px;">单词学习报告</h2>
  `

  // 每页15个单词（3组 x 5个）
  for (let i = 0; i < words.length; i += 15) {
    const pageWords = words.slice(i, i + 15)
    htmlContent += `
      <div style="margin-bottom: 40px; page-break-after: always;">
        <div style="margin-bottom: 30px;">
          ${generateWordTables(pageWords)}
        </div>
        ${i + 15 >= words.length ? generateReviewTable() + generateInfoTable() : ''}
      </div>
    `
  }

  htmlContent += `</div>`
  return htmlContent
}

const generateWordsReport = async (words: any[]) => {
  try {
    // 获取当前登录用户信息
    const currentUser = authStore.currentUser
    if (!currentUser) {
      ElMessage.error('用户未登录')
      return
    }

    // 获取学生信息
    const studentId = parseInt(route.params.studentId as string)
    const teacherId = route.query.teacherId as string
    const userIdForStudent = teacherId || currentUser.id
    const userStudents = studentsStore.getStudentsByUserId(userIdForStudent)
    const student = userStudents.find(s => s.id === studentId)
    const studentName = student ? student.name : '未知学生'

    // 获取教师姓名（当前登录用户的用户名）
    const teacherName = currentUser.username || '未知教师'

    // 动态导入所需库
    const [jsPDFModule, html2canvasModule] = await Promise.all([
      import('jspdf'),
      import('html2canvas')
    ])
    const jsPDF = jsPDFModule.jsPDF || jsPDFModule.default
    const html2canvas = html2canvasModule.default

    ElMessage.info('正在生成3个PDF报告（中英对照、纯英文、纯中文），请稍候...')

    // 辅助函数：生成单个PDF
    const generateSinglePDF = async (mode: 'both' | 'english' | 'chinese', suffix: string) => {
      // 创建临时HTML容器
      const htmlContent = createPDFHtmlContent(words, studentName, teacherName, mode)
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = htmlContent
      tempDiv.style.position = 'absolute'
      tempDiv.style.left = '-9999px'
      tempDiv.style.top = '0'
      document.body.appendChild(tempDiv)

      // 等待字体加载
      await new Promise(resolve => setTimeout(resolve, 100))

      // 使用html2canvas将HTML转换为canvas
      const canvas = await html2canvas(tempDiv.firstElementChild as HTMLElement, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false
      })

      // 移除临时元素
      document.body.removeChild(tempDiv)

      // 创建PDF
      const imgWidth = 297 // A4横向宽度(mm)
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4'
      })

      // 将canvas转换为图片并添加到PDF
      const imgData = canvas.toDataURL('image/png')

      // 如果内容超过一页，需要分页
      const pageHeight = 210 // A4横向高度(mm)
      let heightLeft = imgHeight
      let position = 0

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      return pdf
    }

    // 生成三个PDF
    const dateStr = new Date().toISOString().split('T')[0]
    const [pdfBoth, pdfEnglish, pdfChinese] = await Promise.all([
      generateSinglePDF('both', '中英对照'),
      generateSinglePDF('english', '纯英文'),
      generateSinglePDF('chinese', '纯中文')
    ])

    // 直接下载三个PDF，不预览
    pdfBoth.save(`单词学习报告_${studentName}_中英对照_${dateStr}.pdf`)
    pdfEnglish.save(`单词学习报告_${studentName}_纯英文_${dateStr}.pdf`)
    pdfChinese.save(`单词学习报告_${studentName}_纯中文_${dateStr}.pdf`)

    ElMessage.success('3个PDF报告已生成并下载完成！')

  } catch (error) {
    console.error('生成PDF失败:', error)
    ElMessage.error('生成PDF失败，请重试')
  }
}

// 初始化数据
const initializeWords = () => {
  // 从路由参数获取信息
  const wordSetName = route.query.wordSet as string || ''
  const totalWords = parseInt(route.query.totalWords as string) || 10
  const startIndex = parseInt(route.query.startIndex as string) || 0
  const studentId = parseInt(route.params.studentId as string)
  const teacherId = route.query.teacherId as string

  // 获取当前批次的起始组号和组数
  const currentBatchStartGroup = parseInt(route.query.currentBatchStartGroup as string) || 1
  const currentBatchGroupCount = parseInt(route.query.currentBatchGroupCount as string) || Math.ceil(totalWords / 5)

  console.log('PostLearningTest - 初始化参数:', {
    wordSetName,
    totalWords,
    currentBatchStartGroup,
    currentBatchGroupCount
  })

  // 只加载当前批次的组
  let sourceWords = []
  let loadedFromSession = true

  for (let i = 0; i < currentBatchGroupCount; i++) {
    const groupNumber = currentBatchStartGroup + i
    const sessionKey = `simpleStudyGroup_${groupNumber}`
    const savedWords = sessionStorage.getItem(sessionKey)

    if (savedWords) {
      const groupWords = JSON.parse(savedWords)
      sourceWords.push(...groupWords)
      console.log(`PostLearningTest - 从sessionStorage加载第${groupNumber}组单词:`, groupWords.map((w: any) => w.english))
    } else {
      console.warn(`PostLearningTest - 第${groupNumber}组未找到sessionStorage数据`)
      loadedFromSession = false
      break
    }
  }

  // 如果sessionStorage没有数据，使用备用逻辑从单词库加载
  if (!loadedFromSession || sourceWords.length === 0) {
    console.warn('PostLearningTest - 使用备用逻辑从单词库加载')
    if (teacherId && wordSetName) {
      sourceWords = wordsStore.getWordsBySetForUser(teacherId, wordSetName)
      console.log(`从教师 ${teacherId} 加载单词集 "${wordSetName}"，单词数: ${sourceWords.length}`)
    } else if (wordSetName) {
      sourceWords = wordsStore.getWordsBySet(wordSetName)
      console.log(`从当前用户加载单词集 "${wordSetName}"，单词数: ${sourceWords.length}`)
    } else {
      sourceWords = wordsStore.words
    }
    sourceWords = sourceWords.slice(startIndex, startIndex + totalWords)
  }

  console.log('PostLearningTest - 最终加载的单词:', sourceWords.map(w => w.english))

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