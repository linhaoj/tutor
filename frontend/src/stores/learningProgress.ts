import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface GroupProgress {
  groupNumber: number
  task1Completed: boolean  // 第一个任务（基础学习）
  task2Completed: boolean  // 第二个任务（检查）
  task3Completed: boolean  // 第三个任务（混组检测）
  completedAt?: string
}

export interface WordProgress {
  wordIndex: number // 单词在单词集中的索引
  currentStage: number // 当前所在阶段 (0-7，0表示全新单词)
  lastUpdated: string
}

export interface StudentProgress {
  studentId: number
  wordSet: string
  groups: GroupProgress[]
  currentGroup: number
  totalGroups: number
  allTasksCompleted: boolean
  startedAt: string
  completedAt?: string
  wordProgresses: WordProgress[] // 每个单词的学习进度
}

export const useLearningProgressStore = defineStore('learningProgress', () => {
  // 从localStorage加载进度数据
  const loadProgressFromStorage = () => {
    try {
      const saved = localStorage.getItem('learningProgress')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const studentProgresses = ref<StudentProgress[]>(loadProgressFromStorage())

  // 保存到localStorage
  const saveProgressToStorage = () => {
    localStorage.setItem('learningProgress', JSON.stringify(studentProgresses.value))
  }

  // 开始新的学习进度
  const startLearningProgress = (studentId: number, wordSet: string, totalGroups: number, totalWords = totalGroups * 5) => {
    const existingIndex = studentProgresses.value.findIndex(
      p => p.studentId === studentId && p.wordSet === wordSet
    )

    const groups: GroupProgress[] = Array.from({ length: totalGroups }, (_, i) => ({
      groupNumber: i + 1,
      task1Completed: false,
      task2Completed: false,
      task3Completed: false
    }))

    // 初始化单词进度，所有单词都从第0阶段（全新单词）开始
    const wordProgresses: WordProgress[] = Array.from({ length: totalWords }, (_, i) => ({
      wordIndex: i,
      currentStage: 0, // 0表示全新单词
      lastUpdated: new Date().toISOString()
    }))

    const newProgress: StudentProgress = {
      studentId,
      wordSet,
      groups,
      currentGroup: 1,
      totalGroups,
      allTasksCompleted: false,
      startedAt: new Date().toISOString(),
      wordProgresses
    }

    if (existingIndex !== -1) {
      studentProgresses.value[existingIndex] = newProgress
    } else {
      studentProgresses.value.push(newProgress)
    }

    saveProgressToStorage()
    return newProgress
  }

  // 完成任务
  const completeTask = (studentId: number, wordSet: string, groupNumber: number, taskNumber: 1 | 2 | 3) => {
    const progress = studentProgresses.value.find(
      p => p.studentId === studentId && p.wordSet === wordSet
    )

    if (!progress) return false

    const group = progress.groups.find(g => g.groupNumber === groupNumber)
    if (!group) return false

    // 标记任务完成
    if (taskNumber === 1) {
      group.task1Completed = true
    } else if (taskNumber === 2) {
      group.task2Completed = true
    } else if (taskNumber === 3) {
      group.task3Completed = true
      group.completedAt = new Date().toISOString()
    }

    // 检查是否可以进入下一组
    if (taskNumber === 2 && group.task1Completed && group.task2Completed) {
      // 第二个任务完成后，可以进入混组检测
      progress.currentGroup = Math.max(progress.currentGroup, groupNumber)
    }

    // 检查是否所有任务都完成
    const allCompleted = progress.groups.every(g => 
      g.task1Completed && g.task2Completed && g.task3Completed
    )

    if (allCompleted) {
      progress.allTasksCompleted = true
      progress.completedAt = new Date().toISOString()
    }

    saveProgressToStorage()
    return true
  }

  // 获取学生进度
  const getStudentProgress = (studentId: number, wordSet: string) => {
    return studentProgresses.value.find(
      p => p.studentId === studentId && p.wordSet === wordSet
    )
  }

  // 获取已完成的组数（用于混组检测）
  const getCompletedGroupsCount = (studentId: number, wordSet: string) => {
    const progress = getStudentProgress(studentId, wordSet)
    if (!progress) return 0

    return progress.groups.filter(g => g.task1Completed && g.task2Completed).length
  }

  // 检查是否可以开始某个任务
  const canStartTask = (studentId: number, wordSet: string, groupNumber: number, taskNumber: 1 | 2 | 3) => {
    const progress = getStudentProgress(studentId, wordSet)
    if (!progress) return taskNumber === 1 // 只有第一个任务可以在没有进度的情况下开始

    const group = progress.groups.find(g => g.groupNumber === groupNumber)
    if (!group) return false

    if (taskNumber === 1) {
      return true // 第一个任务总是可以开始
    } else if (taskNumber === 2) {
      return group.task1Completed // 第二个任务需要第一个任务完成
    } else if (taskNumber === 3) {
      // 混组检测需要至少有一组完成了前两个任务
      return getCompletedGroupsCount(studentId, wordSet) >= groupNumber
    }

    return false
  }

  // 更新单个单词的学习进度
  const updateWordProgress = (studentId: number, wordSet: string, wordIndex: number, newStage: number) => {
    const progress = studentProgresses.value.find(
      p => p.studentId === studentId && p.wordSet === wordSet
    )

    if (!progress) return false

    // 确保wordProgresses数组存在
    if (!progress.wordProgresses) {
      progress.wordProgresses = []
    }

    // 查找或创建单词进度
    let wordProgress = progress.wordProgresses.find(wp => wp.wordIndex === wordIndex)
    
    if (!wordProgress) {
      // 如果不存在，创建新的单词进度记录
      wordProgress = {
        wordIndex,
        currentStage: 0,
        lastUpdated: new Date().toISOString()
      }
      progress.wordProgresses.push(wordProgress)
    }

    // 更新阶段和时间
    wordProgress.currentStage = Math.max(0, Math.min(7, newStage)) // 确保在0-7范围内
    wordProgress.lastUpdated = new Date().toISOString()

    saveProgressToStorage()
    return true
  }

  // 获取单个单词的学习进度
  const getWordProgress = (studentId: number, wordSet: string, wordIndex: number) => {
    const progress = getStudentProgress(studentId, wordSet)
    if (!progress || !progress.wordProgresses) return null

    return progress.wordProgresses.find(wp => wp.wordIndex === wordIndex) || null
  }

  // 获取所有单词的进度统计
  const getWordProgressStats = (studentId: number, wordSet: string) => {
    const progress = getStudentProgress(studentId, wordSet)
    if (!progress || !progress.wordProgresses) return null

    const stats = Array.from({ length: 8 }, (_, i) => ({
      stage: i,
      count: progress.wordProgresses.filter(wp => wp.currentStage === i).length
    }))

    return {
      totalWords: progress.wordProgresses.length,
      stageStats: stats
    }
  }

  // 重置学生进度
  const resetProgress = (studentId: number, wordSet: string) => {
    const index = studentProgresses.value.findIndex(
      p => p.studentId === studentId && p.wordSet === wordSet
    )

    if (index !== -1) {
      studentProgresses.value.splice(index, 1)
      saveProgressToStorage()
    }
  }

  return {
    studentProgresses,
    startLearningProgress,
    completeTask,
    getStudentProgress,
    getCompletedGroupsCount,
    canStartTask,
    updateWordProgress,
    getWordProgress,
    getWordProgressStats,
    resetProgress
  }
})