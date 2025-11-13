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
import { Check, Close, VideoPlay } from '@element-plus/icons-vue'
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
const progressUpdated = ref(false) // 防止重复更新进度

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

const speakWord = (text: string) => {
  if ('speechSynthesis' in window) {
    // 停止当前正在播放的语音
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US' // 设置为英语
    utterance.rate = 0.8 // 语速稍慢一些，便于学习
    utterance.volume = 1 // 音量最大

    utterance.onstart = () => {
      ElMessage.info(`正在播放: ${text}`)
    }

    utterance.onerror = (event) => {
      ElMessage.error('语音播放失败')
      console.error('Speech synthesis error:', event)
    }

    window.speechSynthesis.speak(utterance)
  } else {
    ElMessage.warning('您的浏览器不支持语音功能')
  }
}

const markWordStatus = async (index: number, status: 'passed' | 'failed') => {
  const word = allWords.value[index]
  if (word && word.status === 'unchecked') {
    word.status = status

    // 获取当前阶段信息用于显示
    const studentId = parseInt(route.params.studentId as string)
    const wordSet = route.query.wordSet as string
    const currentProgress = await progressStore.getWordProgress(studentId, wordSet, word.originalIndex)
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

const continuePractice = async () => {
  // 更新学习进度
  await updateLearningProgress()

  // 将通过的单词添加到抗遗忘会话
  recordPassedWordsForAntiForget()

  // 清理sessionStorage中的检测状态数据
  clearTestStatusStorage()

  // 跳转回 StudyHome 页面，开始新的一轮学习
  const studentId = route.params.studentId
  const wordSet = route.query.wordSet
  const teacherId = route.query.teacherId

  ElMessage.success('本轮学习已提交！通过的单词已记录到抗遗忘会话中')

  // 跳转回学习准备页面
  router.push({
    path: `/study/${studentId}`,
    query: {
      wordSet,
      teacherId,
      refresh: Date.now() // 添加时间戳强制刷新九宫格数据
    }
  })
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

const endPracticeAndCreateAntiForget = async () => {
  try {
    // 在路由跳转前，先保存当前路由参数（避免跳转后丢失）
    const wordSetName = route.query.wordSet as string || ''
    const totalWords = parseInt(route.query.totalWords as string) || 10
    const startIndex = parseInt(route.query.startIndex as string) || 0
    const studentId = parseInt(route.params.studentId as string)

    // 更新学习进度
    await updateLearningProgress()

    // 创建抗遗忘任务（内部会自动记录通过的单词）
    await createAntiForgetTasks()

    // 标记当前课程为已完成（只有创建抗遗忘成功后才执行）
    await markCourseAsCompleted()

    // 清理sessionStorage中的检测状态数据（使用保存的参数）
    const storageKey =
  `postTestStatus_${studentId}_${wordSetName}_${startIndex}_${totalWords}`
    try {
      sessionStorage.removeItem(storageKey)
      console.log('已清理检测状态缓存:', storageKey)
    } catch (error) {
      console.warn('清理检测状态缓存失败:', error)
    }

    // 完全结束课程（清除计时）
    uiStore.endCourse()
  } catch (error) {
    // 如果创建抗遗忘失败（用户取消等），不做任何操作
    // 错误已经在 createAntiForgetTasks 中显示过了
    console.log('📌 用户取消或操作失败，保持在当前页面')
  }
}

const markCourseAsCompleted = async () => {
  try {
    const scheduleIdStr = sessionStorage.getItem('currentScheduleId')
    const courseStartTime = sessionStorage.getItem('courseStartTime')
    const teacherId = route.query.teacherId as string
    const studentId = parseInt(route.params.studentId as string)

    console.log('🔍 标记课程完成 - 调试信息:', {
      scheduleIdStr,
      courseStartTime,
      teacherId,
      studentId,
      'scheduleIdStr存在': !!scheduleIdStr,
      'teacherId存在': !!teacherId,
      'studentId有效': !isNaN(studentId) && studentId > 0
    })

    // 如果缺少信息，给出详细提示但不影响其他功能
    if (!scheduleIdStr || !teacherId || !studentId) {
      const missing = []
      if (!scheduleIdStr) missing.push('课程ID(scheduleId)')
      if (!teacherId) missing.push('教师ID(teacherId)')
      if (!studentId || isNaN(studentId)) missing.push('学生ID(studentId)')

      console.warn('⚠️ 无法自动标记课程完成，缺少以下信息:', missing.join(', '))
      console.info('💡 提示: 请从日程管理页面点击"学习"按钮进入课程，避免直接刷新或书签访问')
      // 不显示错误消息，因为核心学习功能已完成
      return
    }

    // 所有信息齐全，开始标记课程完成
    const scheduleId = parseInt(scheduleIdStr)

    // 注意：只有单词学习课程才扣减课时，抗遗忘复习不扣课时
    // 获取课程信息来确定扣减时长（后端API自动过滤）
    await scheduleStore.fetchSchedules()
    const schedule = scheduleStore.schedules.find(s => s.id === scheduleId)

    console.log('📅 找到的课程信息:', schedule)

    if (schedule) {
      // 🚨 防止重复标记：如果课程已完成，跳过
      if (schedule.completed) {
        console.log('⚠️ 课程已完成，跳过重复标记和扣课时')
        return
      }
      // 根据课程类型扣减时长：大课(60分钟) = 1.0h，小课(30分钟) = 0.5h
      const hoursToDeduct = schedule.class_type === 'big' ? 1.0 : 0.5

      console.log(`⏰ 准备扣减课时: ${hoursToDeduct}h (${schedule.class_type === 'big' ? '大课' : '小课'})`)

      // 扣减学生课程时长（单词学习课程）
      const success = await studentsStore.deductStudentHours(studentId, hoursToDeduct)
      if (success) {
        console.log(`✅ 单词学习课程时长已扣减: ${hoursToDeduct}h`)
        ElMessage.success(`课时已扣减: ${hoursToDeduct}h`)
      } else {
        console.warn('❌ 扣减学生课程时长失败')
        ElMessage.warning('扣减课时失败')
      }
    } else {
      console.warn('⚠️ 未找到课程信息, scheduleId:', scheduleId)
    }

    // 标记课程为已完成（后端API通过JWT自动识别用户）
    await scheduleStore.completeSchedule(scheduleId)
    console.log('✅ 单词学习课程已标记为完成:', scheduleId)
    ElMessage.success('课程已标记为完成')
  } catch (error) {
    console.error('❌ 标记课程完成失败:', error)
    ElMessage.error('标记课程完成失败')
  }
}

const updateLearningProgress = async () => {
  // 🚨 防止重复更新进度
  if (progressUpdated.value) {
    console.log('⚠️ 进度已更新过，跳过重复更新')
    return
  }

  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string

  if (!studentId || !wordSet) {
    ElMessage.error('缺少必要的学习信息')
    return
  }

  let promotedCount = 0
  let unchangedCount = 0
  let uncheckedCount = 0

  console.log('=== 开始更新学习进度 ===')
  console.log('总单词数:', allWords.value.length)
  console.log('单词列表:', allWords.value.map(w => `${w.english}(idx:${w.originalIndex}, status:${w.status})`))

  // 处理所有单词，不只是有明确状态的单词
  for (const word of allWords.value) {
    // 获取当前阶段（使用新的API方式，不需要teacherId）
    const currentProgress = await progressStore.getWordProgress(studentId, wordSet, word.originalIndex)
    const currentStage = currentProgress ? currentProgress.currentStage : 0

    console.log(`处理单词 "${word.english}" - originalIndex: ${word.originalIndex}, 当前阶段: ${currentStage}, 状态: ${word.status}`)

    if (word.status === 'passed') {
      // 通过的单词 - 阶段+1
      const newStage = Math.min(currentStage + 1, 7)
      await progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, newStage)

      if (newStage > currentStage) {
        promotedCount++
        console.log(`✓ 单词 "${word.english}" (idx:${word.originalIndex}) 从阶段${currentStage}进入阶段${newStage}`)
      }
    } else if (word.status === 'failed') {
      // 未通过的单词 - 保持当前阶段不变
      await progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, currentStage)
      unchangedCount++
      console.log(`× 单词 "${word.english}" (idx:${word.originalIndex}) 保持在阶段${currentStage}（未通过）`)
    } else if (word.status === 'unchecked') {
      // 未检测的单词 - 保持当前阶段不变（不管在哪个格子）
      await progressStore.updateWordProgress(studentId, wordSet, word.originalIndex, currentStage)
      unchangedCount++
      uncheckedCount++
      console.log(`? 单词 "${word.english}" (idx:${word.originalIndex}) 保持在阶段${currentStage}（未检测）`)
    }
  }

  console.log('=== 进度更新完成 ===')
  console.log(`提升: ${promotedCount}, 不变: ${unchangedCount}, 未检测: ${uncheckedCount}`)

  let message = `学习进度已更新：${promotedCount}个单词进入下一阶段，${unchangedCount}个单词保持当前阶段`
  if (uncheckedCount > 0) {
    message += `，${uncheckedCount}个未检测单词视为已学习`
  }

  ElMessage.success(message)

  // 🚨 标记进度已更新，防止重复更新
  progressUpdated.value = true
}

const recordPassedWordsForAntiForget = () => {
  const studentId = parseInt(route.params.studentId as string)
  const wordSet = route.query.wordSet as string

  console.log('🔍 recordPassedWordsForAntiForget - 调试信息:', {
    studentId,
    wordSet,
    allWordsCount: allWords.value.length,
    passedWordsCount: passedWords.value.length,
    passedWords: passedWords.value.map(w => ({ id: w.id, english: w.english }))
  })

  if (!studentId || !wordSet) {
    console.error('❌ 缺少必要参数:', { studentId, wordSet })
    return
  }

  if (passedWords.value.length === 0) {
    console.warn('⚠️ 没有通过的单词需要记录')
    return
  }

  // 记录添加前的会话状态
  const sessionBefore = antiForgetSessionStore.getCurrentSession(studentId)
  console.log('📊 添加前会话状态:', {
    单词数: sessionBefore?.words.length || 0,
    单词列表: sessionBefore?.words.map(w => ({ id: w.id, english: w.english })) || []
  })

  // 将通过的单词转换为抗遗忘会话格式
  const passedWordsData = passedWords.value.map(word => ({
    id: word.id,
    english: word.english,
    chinese: word.chinese
  }))

  console.log('➕ 准备添加的单词:', passedWordsData.map(w => ({ id: w.id, english: w.english })))

  // 添加到抗遗忘会话
  antiForgetSessionStore.addPassedWordsToSession(studentId, wordSet, passedWordsData)

  // 验证是否成功添加
  const sessionAfter = antiForgetSessionStore.getCurrentSession(studentId)
  console.log('📊 添加后会话状态:', {
    单词数: sessionAfter?.words.length || 0,
    单词列表: sessionAfter?.words.map(w => ({ id: w.id, english: w.english })) || [],
    新增数量: (sessionAfter?.words.length || 0) - (sessionBefore?.words.length || 0)
  })
  console.log(`✅ 已将 ${passedWords.value.length} 个通过的单词记录到抗遗忘会话中，实际新增 ${(sessionAfter?.words.length || 0) - (sessionBefore?.words.length || 0)} 个`)
}

const createAntiForgetTasks = async () => {
  const studentId = parseInt(route.params.studentId as string)
  
  if (!studentId) {
    ElMessage.error('缺少学生信息')
    throw new Error('缺少学生信息')
  }

  // 先记录本次的通过单词到会话
  recordPassedWordsForAntiForget()

  // 获取当前会话（不要立即完成，先让用户看到正确的单词数量）
  const currentSession = antiForgetSessionStore.getCurrentSession(studentId)

  if (!currentSession || currentSession.words.length === 0) {
    ElMessage.warning('没有找到需要创建抗遗忘的单词')
    throw new Error('没有找到需要创建抗遗忘的单词')
  }

  try {
    // 让用户选择抗遗忘课程的时间（此时显示正确的单词数量）
    const selectedTime = await promptForAntiForgetTime()

    if (!selectedTime) {
      ElMessage.info('已取消创建抗遗忘课程')
      throw new Error('用户取消创建抗遗忘课程')
    }

    // 现在完成会话并获取所有累积的单词
    const completedSession = antiForgetSessionStore.completeSession(studentId)

    if (!completedSession) {
      ElMessage.error('完成会话时出现错误')
      throw new Error('完成会话时出现错误')
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
    // 🚨 重新抛出错误，防止后续的 markCourseAsCompleted 被执行
    throw error
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

    // 使用teacherId获取学生数据（后端API自动处理权限）
    await studentsStore.fetchStudents()
    const student = studentsStore.students.find(s => s.id === studentId)

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
    const antiForgetSessionId = await antiForgetStore.createAntiForgetSession(
      studentId,
      currentWordSet,
      sessionTeacherId,
      sessionWords
    )

    console.log(`已创建抗遗忘复习会话，会话ID: ${antiForgetSessionId}，teacherId: ${sessionTeacherId}，单词集: ${currentWordSet}，单词数: ${sessionWords.length}`)

    // 第一步：检测所有时间冲突
    const conflicts: Array<{ dayOffset: number, date: string, originalTime: string }> = []

    for (const dayOffset of antiForgetDays) {
      const targetDate = new Date(today)
      targetDate.setDate(today.getDate() + dayOffset)
      const dateStr = targetDate.toISOString().split('T')[0]

      // 检查该学生在该日期该时间是否已有课程
      const existingSchedules = scheduleStore.schedules.filter(
        s => s.student_id === studentId &&
             s.date === dateStr &&
             s.time === time
      )

      if (existingSchedules.length > 0) {
        conflicts.push({ dayOffset, date: dateStr, originalTime: time })
      }
    }

    // 第二步：如果有冲突，询问用户
    let scheduleTimes: Record<number, string> = {} // 记录每个dayOffset对应的时间

    if (conflicts.length > 0) {
      // 格式化冲突列表（移到 try 外面，让 catch 块也能访问）
      const conflictList = conflicts.map(c => {
        const date = new Date(c.date)
        return `${date.getMonth() + 1}月${date.getDate()}日 ${c.originalTime}`
      }).join('、')

      try {
        await ElMessageBox.confirm(
          `以下日期的 ${time} 时段已有课程安排：\n\n${conflictList}\n\n请选择处理方式：`,
          '时间冲突提示',
          {
            confirmButtonText: '自动延后30分钟',
            cancelButtonText: '重新选择时间',
            type: 'warning',
            distinguishCancelAndClose: true
          }
        )

        // 用户选择"自动延后30分钟"
        console.log('用户选择：自动延后30分钟')

        // 为冲突的日期自动延后
        for (const conflict of conflicts) {
          let adjustedTime = conflict.originalTime
          let attempts = 0
          const maxAttempts = 20

          while (attempts < maxAttempts) {
            // 延后30分钟
            const [hours, minutes] = adjustedTime.split(':').map(Number)
            let newMinutes = minutes + 30
            let newHours = hours

            if (newMinutes >= 60) {
              newMinutes -= 60
              newHours += 1
            }

            if (newHours >= 22) {
              newHours = 8
              newMinutes = 0
            }

            adjustedTime = `${String(newHours).padStart(2, '0')}:${String(newMinutes).padStart(2, '0')}`

            // 检查新时间是否还有冲突
            const stillConflict = scheduleStore.schedules.some(
              s => s.student_id === studentId &&
                   s.date === conflict.date &&
                   s.time === adjustedTime
            )

            if (!stillConflict) break
            attempts++
          }

          scheduleTimes[conflict.dayOffset] = adjustedTime
          console.log(`${conflict.date} 时间调整为: ${adjustedTime}`)
        }

      } catch (action) {
        if (action === 'cancel') {
          // 用户选择"重新选择时间"
          console.log('✅ 用户选择：重新选择时间')
          console.log('📋 冲突列表:', conflictList)
          console.log('🔔 即将弹出时间输入框...')

          try {
            // 显示时间选择对话框
            console.log('🪟 正在调用 ElMessageBox.prompt...')
            const { value: newTime } = await ElMessageBox.prompt(
              `请为这 ${conflicts.length} 个冲突的日期选择新的上课时间：\n${conflictList}`,
              '重新选择时间',
              {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                inputPlaceholder: '请输入时间，格式如 14:00',
                inputPattern: /^([01]\d|2[0-3]):([0-5]\d)$/,
                inputErrorMessage: '时间格式不正确，请输入如 14:00'
              }
            )

            console.log('✅ 用户输入的新时间:', newTime)

            // 验证新时间是否还有冲突
            let hasConflictWithNewTime = false
            for (const conflict of conflicts) {
              const stillConflict = scheduleStore.schedules.some(
                s => s.student_id === studentId &&
                     s.date === conflict.date &&
                     s.time === newTime
              )
              if (stillConflict) {
                hasConflictWithNewTime = true
                break
              }
            }

            if (hasConflictWithNewTime) {
              ElMessage.error('选择的时间仍有冲突，已取消创建抗遗忘课程')
              throw new Error('时间仍有冲突')
            }

            // 为所有冲突日期使用新时间
            for (const conflict of conflicts) {
              scheduleTimes[conflict.dayOffset] = newTime
            }

            console.log(`✅ 所有冲突日期使用新时间: ${newTime}`)
          } catch (promptAction) {
            // 用户在时间输入框中点击了取消
            console.log('❌ 用户取消了时间输入，promptAction:', promptAction)
            ElMessage.info('已取消创建抗遗忘课程')
            throw new Error('用户取消时间输入')
          }
        } else {
          // 用户点击了关闭按钮，取消操作
          ElMessage.info('已取消创建抗遗忘课程')
          throw new Error('用户取消操作')
        }
      }
    }

    // 第三步：创建所有课程
    for (const dayOffset of antiForgetDays) {
      const targetDate = new Date(today)
      targetDate.setDate(today.getDate() + dayOffset)
      const dateStr = targetDate.toISOString().split('T')[0]

      // 使用调整后的时间（如果有冲突）或原时间
      const finalTime = scheduleTimes[dayOffset] || time

      // 创建符合后端API的对象（使用snake_case）
      const scheduleData = {
        student_id: studentId,
        date: dateStr,
        time: finalTime,
        word_set_name: currentWordSet,
        course_type: 'review', // 抗遗忘课程类型
        duration: 30, // 抗遗忘课程默认30分钟
        class_type: 'small', // 抗遗忘课程默认小课
        session_id: antiForgetSessionId // 关联抗遗忘会话ID
      }

      await scheduleStore.addSchedule(scheduleData)
    }
    
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
const syncReviewToStudent = async (
  studentId: number,
  wordSetName: string,
  learnDate: string,
  words: { id: number; english: string; chinese: string }[]
) => {
  try {
    // 创建学生复习记录（使用async/await）
    const reviewId = await studentReviewsStore.createReview(
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

    // 获取学生信息（后端API自动处理权限）
    const studentId = parseInt(route.params.studentId as string)
    await studentsStore.fetchStudents()
    const student = studentsStore.students.find(s => s.id === studentId)
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

// 初始化数据（改为async）
const initializeWords = async () => {
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

  // 🚨 优先从 filteredWords 加载完整的学习单词列表（最可靠）
  // 筛选阶段已经确定了要学习的所有单词，训后检测应该显示全部单词
  let sourceWords = []
  const filteredWordsStr = sessionStorage.getItem('filteredWords')

  if (filteredWordsStr) {
    try {
      const filteredWords = JSON.parse(filteredWordsStr)
      // 🚨 关键改动：加载全部筛选后的单词，而不是只加载已学习的组
      sourceWords = filteredWords
      console.log(`PostLearningTest - 从filteredWords加载全部单词 (${sourceWords.length}个):`, sourceWords.map((w: any) => w.english))
    } catch (error) {
      console.warn('解析 filteredWords 失败:', error)
    }
  }

  // 如果 filteredWords 不存在或为空，fallback到分组加载
  if (sourceWords.length === 0) {
    console.warn('PostLearningTest - filteredWords不存在，尝试从分组加载')
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

    // 如果分组数据也没有，最后才从单词库加载
    if (!loadedFromSession || sourceWords.length === 0) {
      console.warn('PostLearningTest - 使用最后备用逻辑从单词库加载')
      if (wordSetName) {
        // 使用异步方法获取单词（后端API自动处理权限）
        sourceWords = await wordsStore.getWordsBySet(wordSetName)
        console.log(`加载单词集 "${wordSetName}"，单词数: ${sourceWords.length}`)
      } else {
        sourceWords = wordsStore.words
      }
      sourceWords = sourceWords.slice(startIndex, startIndex + totalWords)
    }
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
    // 优先使用从sessionStorage传来的originalIndex
    // 如果没有（旧数据或备用逻辑），则使用startIndex + index计算
    const originalIndex = word.originalIndex !== undefined ? word.originalIndex : (startIndex + index)
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
onMounted(async () => {
  // 确保处于课程模式（不重新设置计时）
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/study/' + route.params.studentId)
  }

  // 获取学生信息（后端API自动处理权限）
  const studentId = parseInt(route.params.studentId as string)
  if (studentId) {
    const currentUser = authStore.currentUser
    if (currentUser) {
      await studentsStore.fetchStudents()
      const student = studentsStore.students.find(s => s.id === studentId)
      if (student) {
        studentName.value = student.name
      }
    }
  }

  // 初始化单词数据
  await initializeWords()
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
  gap: 10px;
  min-width: 280px;
}

.pass-button, .fail-button, .speak-button {
  flex: 1;
  height: 50px;
  font-size: 14px;
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