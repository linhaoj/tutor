import { defineStore } from 'pinia'
import { ref } from 'vue'

// 抗遗忘会话中的单词
export interface AntiForgetWord {
  id: number
  english: string
  chinese: string
  wordSetName: string
  addedAt: string // 添加到抗遗忘会话的时间
}

// 抗遗忘会话
export interface AntiForgetSession {
  studentId: number
  sessionId: string // 唯一会话ID
  startDate: string // 开始日期
  words: AntiForgetWord[] // 累积的通过单词
  createdAt: string
}

export const useAntiForgetSessionStore = defineStore('antiForgetSession', () => {
  // 从localStorage加载数据
  const loadSessionsFromStorage = () => {
    try {
      const saved = localStorage.getItem('antiForgetSessions')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const sessions = ref<AntiForgetSession[]>(loadSessionsFromStorage())

  // 保存到localStorage
  const saveSessionsToStorage = () => {
    localStorage.setItem('antiForgetSessions', JSON.stringify(sessions.value))
  }

  // 获取当前学生的活跃会话
  const getCurrentSession = (studentId: number) => {
    return sessions.value.find(s => s.studentId === studentId && !isSessionEnded(s))
  }

  // 检查会话是否已结束（超过24小时未更新视为结束）
  const isSessionEnded = (session: AntiForgetSession) => {
    const now = new Date()
    const lastUpdate = new Date(session.createdAt)
    const hoursDiff = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60)
    return hoursDiff > 24 // 24小时后会话过期
  }

  // 开始新的抗遗忘会话或获取现有会话
  const startOrGetSession = (studentId: number) => {
    let currentSession = getCurrentSession(studentId)
    
    if (!currentSession) {
      // 创建新会话
      const sessionId = `session_${studentId}_${Date.now()}`
      currentSession = {
        studentId,
        sessionId,
        startDate: new Date().toISOString().split('T')[0], // 今天的日期
        words: [],
        createdAt: new Date().toISOString()
      }
      sessions.value.push(currentSession)
      saveSessionsToStorage()
    }
    
    return currentSession
  }

  // 添加通过的单词到当前会话
  const addPassedWordsToSession = (studentId: number, wordSetName: string, passedWords: { id: number, english: string, chinese: string }[]) => {
    const session = startOrGetSession(studentId)
    
    passedWords.forEach(word => {
      // 检查单词是否已存在（避免重复）
      const existingWord = session.words.find(w => w.id === word.id && w.wordSetName === wordSetName)
      
      if (!existingWord) {
        const antiForgetWord: AntiForgetWord = {
          ...word,
          wordSetName,
          addedAt: new Date().toISOString()
        }
        session.words.push(antiForgetWord)
      }
    })
    
    // 更新会话时间
    session.createdAt = new Date().toISOString()
    saveSessionsToStorage()
    
    return session
  }

  // 完成会话并创建抗遗忘任务
  const completeSession = (studentId: number) => {
    const session = getCurrentSession(studentId)
    if (!session) {
      return null
    }

    // 返回会话数据用于创建抗遗忘任务
    const completedSession = { ...session }
    
    // 从活跃会话中移除（标记为已完成）
    const index = sessions.value.findIndex(s => s.sessionId === session.sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      saveSessionsToStorage()
    }
    
    return completedSession
  }

  // 获取会话统计信息
  const getSessionStats = (studentId: number) => {
    const session = getCurrentSession(studentId)
    if (!session) {
      return null
    }

    const wordSetStats = new Map<string, number>()
    session.words.forEach(word => {
      wordSetStats.set(word.wordSetName, (wordSetStats.get(word.wordSetName) || 0) + 1)
    })

    return {
      totalWords: session.words.length,
      wordSetStats: Array.from(wordSetStats.entries()).map(([name, count]) => ({ name, count })),
      sessionDays: Math.ceil((new Date().getTime() - new Date(session.startDate).getTime()) / (1000 * 60 * 60 * 24))
    }
  }

  // 清理过期会话
  const cleanupExpiredSessions = () => {
    const initialCount = sessions.value.length
    sessions.value = sessions.value.filter(session => !isSessionEnded(session))
    
    if (sessions.value.length < initialCount) {
      saveSessionsToStorage()
    }
  }

  return {
    sessions,
    getCurrentSession,
    startOrGetSession,
    addPassedWordsToSession,
    completeSession,
    getSessionStats,
    cleanupExpiredSessions
  }
})