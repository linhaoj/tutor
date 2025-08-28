import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface WordCard {
  id: number
  english: string
  chinese: string
  student_word_id: number
  current_stage: string
}

export interface LearningSession {
  id: number
  student_id: number
  words_count: number
  current_stage: string
  current_group: number
  total_groups: number
  completed: boolean
  created_at: string
  word_cards: WordCard[]
}

export interface GridStats {
  grid_0: number
  grid_1: number
  grid_2: number
  grid_3: number
  grid_4: number
  grid_5: number
  grid_6: number
  grid_7: number
  grid_8: number
}

export const useLearningStore = defineStore('learning', () => {
  // 从localStorage加载学习会话数据
  const loadSessionsFromStorage = () => {
    try {
      const saved = localStorage.getItem('learningSessions')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  // 从localStorage加载统计数据
  const loadStatsFromStorage = () => {
    try {
      const saved = localStorage.getItem('gridStats')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  }

  const sessions = ref<LearningSession[]>(loadSessionsFromStorage())
  const gridStats = ref<Record<number, GridStats>>(loadStatsFromStorage())
  const currentSession = ref<LearningSession | null>(null)

  // 保存到localStorage
  const saveSessionsToStorage = () => {
    localStorage.setItem('learningSessions', JSON.stringify(sessions.value))
  }

  const saveStatsToStorage = () => {
    localStorage.setItem('gridStats', JSON.stringify(gridStats.value))
  }

  // 开始新的学习会话
  const startSession = (session: LearningSession) => {
    sessions.value.push(session)
    currentSession.value = session
    saveSessionsToStorage()
  }

  // 更新当前会话
  const updateCurrentSession = (updatedSession: Partial<LearningSession>) => {
    if (currentSession.value) {
      currentSession.value = { ...currentSession.value, ...updatedSession }
      
      // 同时更新sessions数组中的对应项
      const index = sessions.value.findIndex(s => s.id === currentSession.value!.id)
      if (index !== -1) {
        sessions.value[index] = currentSession.value
        saveSessionsToStorage()
      }
    }
  }

  // 完成会话
  const completeSession = (sessionId: number) => {
    const index = sessions.value.findIndex(s => s.id === sessionId)
    if (index !== -1) {
      sessions.value[index].completed = true
      saveSessionsToStorage()
    }
    
    if (currentSession.value?.id === sessionId) {
      currentSession.value.completed = true
    }
  }

  // 更新学生的网格统计
  const updateGridStats = (studentId: number, stats: GridStats) => {
    gridStats.value[studentId] = stats
    saveStatsToStorage()
  }

  // 获取学生的学习会话
  const getStudentSessions = (studentId: number) => {
    return sessions.value.filter(s => s.student_id === studentId)
  }

  // 获取学生的网格统计
  const getStudentGridStats = (studentId: number): GridStats | null => {
    return gridStats.value[studentId] || null
  }

  // 获取最近的学习会话
  const getRecentSessions = (limit: number = 10) => {
    return sessions.value
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, limit)
  }

  // 清除当前会话
  const clearCurrentSession = () => {
    currentSession.value = null
  }

  return {
    sessions,
    gridStats,
    currentSession,
    startSession,
    updateCurrentSession,
    completeSession,
    updateGridStats,
    getStudentSessions,
    getStudentGridStats,
    getRecentSessions,
    clearCurrentSession
  }
})