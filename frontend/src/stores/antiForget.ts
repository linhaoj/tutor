/**
 * 抗遗忘会话Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface AntiForgetSession {
  id: string
  student_id: number
  word_set_name: string
  teacher_id: string
  words: AntiForgetWord[]
  review_count: number
  total_reviews: number
  created_at: string
}

export interface AntiForgetWord {
  id: number
  english: string
  chinese: string
  is_starred: boolean
}

export const useAntiForgetStore = defineStore('antiForget', () => {
  const sessions = ref<AntiForgetSession[]>([])
  const loading = ref(false)

  /**
   * 创建新的抗遗忘会话
   */
  const createAntiForgetSession = async (
    studentId: number,
    wordSetName: string,
    teacherId: string,
    words: { id: number; english: string; chinese: string }[]
  ): Promise<string> => {
    try {
      const response = await api.post('/api/anti-forget/sessions', {
        student_id: studentId,
        word_set_name: wordSetName,
        teacher_id: teacherId,
        words: words.map(w => ({
          id: w.id,
          english: w.english,
          chinese: w.chinese,
          is_starred: false
        }))
      })

      // 更新本地缓存
      sessions.value.push(response.data)

      console.log('创建抗遗忘会话成功:', response.data.id)
      return response.data.id
    } catch (error: any) {
      console.error('创建抗遗忘会话失败:', error)
      throw new Error(error.response?.data?.detail || '创建抗遗忘会话失败')
    }
  }

  /**
   * 获取学生的所有抗遗忘会话
   */
  const fetchStudentSessions = async (studentId: number): Promise<void> => {
    loading.value = true
    try {
      const response = await api.get(`/api/anti-forget/sessions/student/${studentId}`)
      sessions.value = response.data
      console.log(`获取学生${studentId}的抗遗忘会话:`, response.data.length, '个')
    } catch (error) {
      console.error('获取抗遗忘会话失败:', error)
      sessions.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取特定会话（从服务器）
   */
  const fetchSession = async (sessionId: string): Promise<AntiForgetSession | null> => {
    try {
      const response = await api.get(`/api/anti-forget/sessions/${sessionId}`)

      // 更新本地缓存
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = response.data
      } else {
        sessions.value.push(response.data)
      }

      return response.data
    } catch (error) {
      console.error('获取会话失败:', error)
      return null
    }
  }

  /**
   * 获取特定会话（从本地缓存）
   */
  const getSession = (sessionId: string): AntiForgetSession | undefined => {
    return sessions.value.find(s => s.id === sessionId)
  }

  /**
   * 获取学生的抗遗忘会话（从本地缓存）
   */
  const getStudentAntiForgetSessions = (studentId: number): AntiForgetSession[] => {
    return sessions.value.filter(s => s.student_id === studentId)
  }

  /**
   * 获取学生特定单词集的活跃会话（未完成的）
   */
  const getActiveSession = (
    studentId: number,
    wordSetName: string,
    teacherId: string
  ): AntiForgetSession | undefined => {
    return sessions.value.find(
      s =>
        s.student_id === studentId &&
        s.word_set_name === wordSetName &&
        s.teacher_id === teacherId &&
        s.review_count < s.total_reviews
    )
  }

  /**
   * 切换单词的五角星状态
   */
  const toggleWordStar = async (sessionId: string, wordId: number): Promise<boolean> => {
    try {
      const response = await api.post(
        `/api/anti-forget/sessions/${sessionId}/toggle-star/${wordId}`
      )

      // 更新本地缓存
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        const word = session.words.find(w => w.id === wordId)
        if (word) {
          word.is_starred = response.data.is_starred
          console.log(`单词 ${word.english} 五角星状态切换为:`, word.is_starred)
        }
      }

      return response.data.is_starred
    } catch (error) {
      console.error('切换五角星失败:', error)
      return false
    }
  }

  /**
   * 完成一次复习
   */
  const completeReview = async (
    sessionId: string
  ): Promise<{ currentCount: number; totalCount: number; isCompleted: boolean } | null> => {
    try {
      const response = await api.post(
        `/api/anti-forget/sessions/${sessionId}/complete-review`
      )

      // 更新本地缓存
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.review_count = response.data.current_count
      }

      console.log(
        `完成第${response.data.current_count}次复习，剩余${response.data.total_count - response.data.current_count}次`
      )

      return {
        currentCount: response.data.current_count,
        totalCount: response.data.total_count,
        isCompleted: response.data.is_completed
      }
    } catch (error) {
      console.error('完成复习失败:', error)
      return null
    }
  }

  /**
   * 获取复习统计
   */
  const getReviewStats = async (sessionId: string): Promise<{
    sessionId: string
    currentReview: number
    totalReviews: number
    remainingReviews: number
    starredWords: number
    totalWords: number
    progress: number
  } | null> => {
    try {
      const response = await api.get(`/api/anti-forget/sessions/${sessionId}/stats`)

      return {
        sessionId,
        currentReview: response.data.current_review,
        totalReviews: response.data.total_reviews,
        remainingReviews: response.data.total_reviews - response.data.current_review,
        starredWords: response.data.starred_words,
        totalWords: response.data.total_words,
        progress: response.data.progress
      }
    } catch (error) {
      console.error('获取统计失败:', error)
      return null
    }
  }

  /**
   * 删除会话（完成所有复习后）
   */
  const deleteSession = async (sessionId: string): Promise<boolean> => {
    try {
      await api.delete(`/api/anti-forget/sessions/${sessionId}`)

      // 从本地缓存中移除
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value.splice(index, 1)
      }

      console.log('删除会话成功:', sessionId)
      return true
    } catch (error) {
      console.error('删除会话失败:', error)
      return false
    }
  }

  /**
   * 清理已完成的会话（可选）
   */
  const cleanupCompletedSessions = async (studentId: number): Promise<void> => {
    const completedSessions = sessions.value.filter(
      s => s.student_id === studentId && s.review_count >= s.total_reviews
    )

    for (const session of completedSessions) {
      await deleteSession(session.id)
    }

    console.log(`清理了 ${completedSessions.length} 个已完成的会话`)
  }

  return {
    sessions,
    loading,
    createAntiForgetSession,
    fetchStudentSessions,
    fetchSession,
    getSession,
    getStudentAntiForgetSessions,
    getActiveSession,
    toggleWordStar,
    completeReview,
    getReviewStats,
    deleteSession,
    cleanupCompletedSessions
  }
})
