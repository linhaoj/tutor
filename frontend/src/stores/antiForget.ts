import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface AntiForgetSession {
  id: string
  studentId: number
  wordSetName: string
  teacherId: string
  words: AntiForgetWord[]
  createdAt: string
  reviewCount: number // 已复习次数
  totalReviews: number // 计划总复习次数（通常是10次）
}

export interface AntiForgetWord {
  id: number
  english: string
  chinese: string
  isStarred: boolean // 五角星标记状态
  lastStarredAt?: string // 最后一次标记的时间
}

export interface AntiForgetReviewRecord {
  sessionId: string
  studentId: number
  reviewDate: string
  starredWords: number[] // 该次复习中被标记的单词ID列表
}

export const useAntiForgetStore = defineStore('antiForget', () => {
  // 从localStorage加载抗遗忘会话数据
  const loadSessionsFromStorage = () => {
    try {
      const saved = localStorage.getItem('antiForgetSessions')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  // 从localStorage加载复习记录
  const loadReviewRecordsFromStorage = () => {
    try {
      const saved = localStorage.getItem('antiForgetReviews')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const sessions = ref<AntiForgetSession[]>(loadSessionsFromStorage())
  const reviewRecords = ref<AntiForgetReviewRecord[]>(loadReviewRecordsFromStorage())

  // 保存到localStorage
  const saveSessionsToStorage = () => {
    localStorage.setItem('antiForgetSessions', JSON.stringify(sessions.value))
  }

  const saveReviewRecordsToStorage = () => {
    localStorage.setItem('antiForgetReviews', JSON.stringify(reviewRecords.value))
  }

  // 创建新的抗遗忘会话
  const createAntiForgetSession = (
    studentId: number, 
    wordSetName: string, 
    teacherId: string, 
    words: { id: number; english: string; chinese: string }[]
  ) => {
    const sessionId = `af_${studentId}_${wordSetName}_${Date.now()}`
    
    const antiForgetWords: AntiForgetWord[] = words.map(word => ({
      id: word.id,
      english: word.english,
      chinese: word.chinese,
      isStarred: false
    }))

    const session: AntiForgetSession = {
      id: sessionId,
      studentId,
      wordSetName,
      teacherId,
      words: antiForgetWords,
      createdAt: new Date().toISOString(),
      reviewCount: 0,
      totalReviews: 10 // 默认10次复习
    }

    sessions.value.push(session)
    saveSessionsToStorage()
    
    console.log('创建抗遗忘会话:', session)
    return sessionId
  }

  // 获取学生的抗遗忘会话
  const getStudentAntiForgetSessions = (studentId: number) => {
    return sessions.value.filter(session => session.studentId === studentId)
  }

  // 获取特定会话
  const getSession = (sessionId: string) => {
    return sessions.value.find(session => session.id === sessionId)
  }

  // 获取学生特定单词集的活跃会话（未完成的）
  const getActiveSession = (studentId: number, wordSetName: string, teacherId: string) => {
    return sessions.value.find(session => 
      session.studentId === studentId && 
      session.wordSetName === wordSetName &&
      session.teacherId === teacherId &&
      session.reviewCount < session.totalReviews
    )
  }

  // 切换单词的五角星状态
  const toggleWordStar = (sessionId: string, wordId: number) => {
    const session = getSession(sessionId)
    if (session) {
      const word = session.words.find(w => w.id === wordId)
      if (word) {
        word.isStarred = !word.isStarred
        word.lastStarredAt = word.isStarred ? new Date().toISOString() : undefined
        saveSessionsToStorage()
        
        console.log(`单词 ${word.english} 五角星状态切换为:`, word.isStarred)
        return word.isStarred
      }
    }
    return false
  }

  // 记录一次复习完成
  const completeReview = (sessionId: string) => {
    const session = getSession(sessionId)
    if (session) {
      session.reviewCount++
      
      // 记录这次复习的标记单词
      const starredWordIds = session.words
        .filter(word => word.isStarred)
        .map(word => word.id)
      
      const reviewRecord: AntiForgetReviewRecord = {
        sessionId,
        studentId: session.studentId,
        reviewDate: new Date().toISOString(),
        starredWords: starredWordIds
      }
      
      reviewRecords.value.push(reviewRecord)
      saveSessionsToStorage()
      saveReviewRecordsToStorage()
      
      console.log(`完成第${session.reviewCount}次复习，剩余${session.totalReviews - session.reviewCount}次`)
      return {
        currentCount: session.reviewCount,
        totalCount: session.totalReviews,
        isCompleted: session.reviewCount >= session.totalReviews
      }
    }
    return null
  }

  // 获取复习统计
  const getReviewStats = (sessionId: string) => {
    const session = getSession(sessionId)
    if (session) {
      const starredCount = session.words.filter(word => word.isStarred).length
      const totalWords = session.words.length
      
      return {
        sessionId,
        currentReview: session.reviewCount,
        totalReviews: session.totalReviews,
        remainingReviews: session.totalReviews - session.reviewCount,
        starredWords: starredCount,
        totalWords: totalWords,
        progress: Math.round((session.reviewCount / session.totalReviews) * 100)
      }
    }
    return null
  }

  // 清理已完成的会话（可选）
  const cleanupCompletedSessions = (olderThanDays: number = 30) => {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays)
    
    const initialCount = sessions.value.length
    sessions.value = sessions.value.filter(session => {
      if (session.reviewCount >= session.totalReviews) {
        const createdDate = new Date(session.createdAt)
        return createdDate > cutoffDate
      }
      return true
    })
    
    if (sessions.value.length < initialCount) {
      saveSessionsToStorage()
      console.log(`清理了 ${initialCount - sessions.value.length} 个已完成的会话`)
    }
  }

  return {
    sessions,
    reviewRecords,
    createAntiForgetSession,
    getStudentAntiForgetSessions,
    getSession,
    getActiveSession,
    toggleWordStar,
    completeReview,
    getReviewStats,
    cleanupCompletedSessions
  }
})