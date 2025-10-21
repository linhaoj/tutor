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
      // 使用后端的批量更新API
      const response = await api.post('/api/progress/batch-update', {
        updates: progressList
      })

      // 更新本地缓存
      if (response.data.success) {
        // 重新获取进度以同步最新数据
        if (progressList.length > 0) {
          await fetchStudentProgress(
            progressList[0].student_id,
            progressList[0].word_set_name
          )
        }
      }

      return { success: true, message: '所有进度保存成功' }
    } catch (error) {
      return { success: false, message: '批量保存失败' }
    }
  }

  /**
   * 获取单个单词的学习进度
   * 这是被7个页面频繁调用的核心方法
   */
  const getWordProgress = async (
    studentId: number,
    wordSetName: string,
    wordIndex: number
  ): Promise<{
    currentStage: number
    totalGroups: number
    tasksCompleted: Record<string, any>
  } | null> => {
    try {
      const response = await api.get(
        `/api/progress/student/${studentId}/word/${wordSetName}/${wordIndex}`
      )
      return {
        currentStage: response.data.current_stage,
        totalGroups: response.data.total_groups,
        tasksCompleted: response.data.tasks_completed || {}
      }
    } catch (error) {
      console.error('Get word progress error:', error)
      // 返回默认值（未学习状态）
      return {
        currentStage: 0,
        totalGroups: 0,
        tasksCompleted: {}
      }
    }
  }

  /**
   * 获取九宫格统计数据（StudyHome专用）
   */
  const getGridStats = async (
    studentId: number,
    wordSetName: string
  ): Promise<Record<string, number>> => {
    try {
      const response = await api.get(
        `/api/progress/student/${studentId}/word-set/${wordSetName}/grid-stats`
      )
      return response.data
    } catch (error) {
      console.error('Get grid stats error:', error)
      // 返回空统计
      return {
        grid_0: 0,
        grid_1: 0,
        grid_2: 0,
        grid_3: 0,
        grid_4: 0,
        grid_5: 0,
        grid_6: 0,
        grid_7: 0,
        grid_8: 0
      }
    }
  }

  /**
   * 更新单词学习进度（训后检测核心功能）
   */
  const updateWordProgress = async (
    studentId: number,
    wordSetName: string,
    wordIndex: number,
    newStage: number,
    totalGroups: number = 0,
    tasksCompleted: Record<string, any> = {}
  ): Promise<boolean> => {
    try {
      await saveProgress({
        student_id: studentId,
        word_set_name: wordSetName,
        word_index: wordIndex,
        current_stage: newStage,
        total_groups: totalGroups,
        tasks_completed: tasksCompleted
      })
      return true
    } catch (error) {
      console.error('Update word progress error:', error)
      return false
    }
  }

  /**
   * 批量更新单词进度（PostLearningTest使用）
   */
  const updateWordProgressForUser = async (
    userId: string,
    studentId: number,
    wordSetName: string,
    wordIndex: number,
    newStage: number
  ): Promise<void> => {
    // userId参数是为了兼容旧代码，实际不需要（后端通过JWT自动识别）
    await updateWordProgress(studentId, wordSetName, wordIndex, newStage)
  }

  /**
   * 标记任务完成（阶段切换）
   */
  const completeTask = async (
    studentId: number,
    wordSetName: string,
    groupNumber: number,
    taskNumber: number
  ): Promise<boolean> => {
    try {
      await api.post('/api/progress/complete-task', {
        student_id: studentId,
        word_set_name: wordSetName,
        group_number: groupNumber,
        task_number: taskNumber
      })
      return true
    } catch (error) {
      console.error('Complete task error:', error)
      return false
    }
  }

  /**
   * 初始化学习进度（SimpleWordStudy使用）
   */
  const startLearningProgress = async (
    studentId: number,
    wordSetName: string,
    totalGroups: number
  ): Promise<void> => {
    // 如果需要初始化特定逻辑，可以在这里实现
    // 目前在首次保存进度时自动创建记录
    console.log('Start learning progress:', { studentId, wordSetName, totalGroups })
  }

  return {
    progresses,
    loading,
    fetchStudentProgress,
    saveProgress,
    getProgress,
    batchSaveProgress,
    getWordProgress,
    getGridStats,
    updateWordProgress,
    updateWordProgressForUser,
    completeTask,
    startLearningProgress
  }
})
