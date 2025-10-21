/**
 * 课程安排Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/config'

export interface Schedule {
  id: number
  student_id: number
  student_name: string
  date: string  // YYYY-MM-DD
  time: string
  word_set_name: string
  course_type: string
  duration: number
  class_type: string
  completed: boolean
}

export interface DateGroup {
  date: string
  schedules: Schedule[]
  expanded: boolean
}

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref<Schedule[]>([])
  const loading = ref(false)
  const expandedStates = ref<Record<string, boolean>>({})

  /**
   * 获取所有课程
   * @param teacherId 可选：管理员可以指定教师ID查询该教师的课程
   */
  const fetchSchedules = async (teacherId?: string) => {
    loading.value = true
    try {
      const params = teacherId ? { teacher_id: teacherId } : {}
      const response = await api.get('/api/schedules', { params })
      schedules.value = response.data
    } catch (error) {
      console.error('Fetch schedules error:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建课程
   */
  const addSchedule = async (scheduleData: {
    student_id: number
    date: string
    time: string
    word_set_name: string
    course_type?: string
    duration?: number
    class_type?: string
  }): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post('/api/schedules', scheduleData)
      schedules.value.push(response.data)
      return { success: true, message: '课程创建成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '创建课程失败'
      }
    }
  }

  /**
   * 标记课程为完成
   */
  const completeSchedule = async (id: number): Promise<{ success: boolean, message: string }> => {
    try {
      await api.put(`/api/schedules/${id}/complete`)

      // 更新本地状态
      const schedule = schedules.value.find(s => s.id === id)
      if (schedule) {
        schedule.completed = true
      }

      return { success: true, message: '课程已标记为完成' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '标记失败'
      }
    }
  }

  /**
   * 删除课程
   */
  const deleteSchedule = async (id: number): Promise<{ success: boolean, message: string }> => {
    try {
      await api.delete(`/api/schedules/${id}`)
      schedules.value = schedules.value.filter(s => s.id !== id)
      return { success: true, message: '课程删除成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '删除课程失败'
      }
    }
  }

  /**
   * 更新课程（通用方法）
   */
  const updateSchedule = async (
    id: number,
    updates: Partial<Schedule>
  ): Promise<{ success: boolean, message: string }> => {
    const schedule = schedules.value.find(s => s.id === id)
    if (schedule) {
      Object.assign(schedule, updates)
      return { success: true, message: '课程更新成功' }
    }
    return { success: false, message: '课程不存在' }
  }

  /**
   * 获取指定日期的课程
   */
  const getSchedulesByDate = (date: string): Schedule[] => {
    return schedules.value.filter(s => s.date === date)
  }

  /**
   * 获取学生的课程
   */
  const getSchedulesByStudent = (studentId: number): Schedule[] => {
    return schedules.value.filter(s => s.student_id === studentId)
  }

  /**
   * 切换日期组的展开状态
   */
  const toggleDateGroupExpanded = (date: string) => {
    expandedStates.value[date] = !expandedStates.value[date]
    localStorage.setItem('schedule_expanded_states', JSON.stringify(expandedStates.value))
  }

  /**
   * 获取日期组的展开状态
   */
  const isDateGroupExpanded = (date: string): boolean => {
    return expandedStates.value[date] ?? true  // 默认展开
  }

  /**
   * 获取按日期分组的课程（只显示今天及未来的课程）
   */
  const getGroupedSchedules = computed((): DateGroup[] => {
    const groups: Record<string, Schedule[]> = {}

    // 获取今天的日期（本地时区）
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]

    // 只包含今天及未来的课程
    schedules.value.forEach(schedule => {
      if (schedule.date >= todayStr) {
        if (!groups[schedule.date]) {
          groups[schedule.date] = []
        }
        groups[schedule.date].push(schedule)
      }
    })

    return Object.keys(groups)
      .sort()  // 按日期排序
      .map(date => ({
        date,
        schedules: groups[date].sort((a, b) => a.time.localeCompare(b.time)),  // 按时间排序
        expanded: isDateGroupExpanded(date)
      }))
  })

  /**
   * 获取今日需要复习的数量
   */
  const getTodayReviewCount = computed((): number => {
    const today = new Date().toISOString().split('T')[0]
    return schedules.value.filter(s =>
      s.date === today &&
      s.course_type === 'review' &&
      !s.completed
    ).length
  })

  /**
   * 初始化（恢复展开状态）
   */
  const initializeExpandedStates = () => {
    try {
      const saved = localStorage.getItem('schedule_expanded_states')
      if (saved) {
        expandedStates.value = JSON.parse(saved)
      }
    } catch (error) {
      console.error('Load expanded states error:', error)
    }
  }

  // 初始化
  initializeExpandedStates()

  return {
    schedules,
    loading,
    expandedStates,
    fetchSchedules,
    addSchedule,
    updateSchedule,
    deleteSchedule,
    completeSchedule,
    getSchedulesByDate,
    getSchedulesByStudent,
    toggleDateGroupExpanded,
    isDateGroupExpanded,
    getGroupedSchedules,
    getTodayReviewCount
  }
})
