/**
 * 学习进度Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface LearningProgress {
  id: number
  student_id: number
  word_set_name: string
  word_index: number
  current_stage: number
  total_groups: number
  tasks_completed: Record<string, any>
}

export const useLearningProgressStore = defineStore('learningProgress', () => {
  const progresses = ref<LearningProgress[]>([])
  const loading = ref(false)

  /**
   * 获取学生的学习进度
   */
  const fetchStudentProgress = async (
    studentId: number,
    wordSetName?: string
  ): Promise<LearningProgress[]> => {
    loading.value = true
    try {
      const params = wordSetName ? { word_set_name: wordSetName } : {}
      const response = await api.get(`/api/progress/student/${studentId}`, { params })
      progresses.value = response.data
      return response.data
    } catch (error) {
      console.error('Fetch student progress error:', error)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建或更新学习进度
   */
  const saveProgress = async (progressData: {
    student_id: number
    word_set_name: string
    word_index: number
    current_stage: number
    total_groups: number
    tasks_completed: Record<string, any>
  }): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post('/api/progress', progressData)

      // 更新本地缓存
      const index = progresses.value.findIndex(
        p =>
          p.student_id === progressData.student_id &&
          p.word_set_name === progressData.word_set_name &&
          p.word_index === progressData.word_index
      )

      if (index !== -1) {
        progresses.value[index] = response.data
      } else {
        progresses.value.push(response.data)
      }

      return { success: true, message: '进度保存成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '保存进度失败'
      }
    }
  }

  /**
   * 获取特定学生和单词集的进度
   */
  const getProgress = (studentId: number, wordSetName: string, wordIndex: number) => {
    return progresses.value.find(
      p =>
        p.student_id === studentId &&
        p.word_set_name === wordSetName &&
        p.word_index === wordIndex
    )
  }

  /**
   * 批量保存进度（用于学习流程中的多个单词）
   */
  const batchSaveProgress = async (
    progressList: Array<{
      student_id: number
      word_set_name: string
      word_index: number
      current_stage: number
      total_groups: number
      tasks_completed: Record<string, any>
    }>
  ): Promise<{ success: boolean, message: string }> => {
    try {
      const results = await Promise.all(progressList.map(p => saveProgress(p)))
      const allSuccess = results.every(r => r.success)

      if (allSuccess) {
        return { success: true, message: '所有进度保存成功' }
      } else {
        return { success: false, message: '部分进度保存失败' }
      }
    } catch (error) {
      return { success: false, message: '批量保存失败' }
    }
  }

  return {
    progresses,
    loading,
    fetchStudentProgress,
    saveProgress,
    getProgress,
    batchSaveProgress
  }
})
