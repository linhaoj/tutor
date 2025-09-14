import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export interface Schedule {
  id: number
  date: string
  time: string
  studentName: string
  studentId: number
  wordSet: string
  type: 'learning' | 'review'
  duration: number // 课程持续时间（分钟）
  classType: 'big' | 'small' // 大课(60分钟) 或 小课(30分钟)
  completed?: boolean
  created_at?: string
}

export interface DateGroup {
  date: string
  schedules: Schedule[]
  expanded: boolean
}

export const useScheduleStore = defineStore('schedule', () => {
  const authStore = useAuthStore()
  
  // 获取当前用户的localStorage key
  const getScheduleStorageKey = () => {
    const currentUser = authStore.currentUser
    return currentUser ? `schedule_${currentUser.id}` : 'schedule_guest'
  }
  
  const getExpandedStatesStorageKey = () => {
    const currentUser = authStore.currentUser
    return currentUser ? `scheduleDateStates_${currentUser.id}` : 'scheduleDateStates_guest'
  }
  
  // 从localStorage加载日程数据（按用户隔离）
  const loadSchedulesFromStorage = () => {
    try {
      const storageKey = getScheduleStorageKey()
      const saved = localStorage.getItem(storageKey)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  // 从localStorage加载日期组展开状态（按用户隔离）
  const loadExpandedStatesFromStorage = () => {
    try {
      const storageKey = getExpandedStatesStorageKey()
      const saved = localStorage.getItem(storageKey)
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  }

  const schedules = ref<Schedule[]>(loadSchedulesFromStorage())
  const expandedStates = ref<Record<string, boolean>>(loadExpandedStatesFromStorage())

  // 保存到localStorage（按用户隔离）
  const saveSchedulesToStorage = () => {
    const storageKey = getScheduleStorageKey()
    localStorage.setItem(storageKey, JSON.stringify(schedules.value))
  }

  const saveExpandedStatesToStorage = () => {
    const storageKey = getExpandedStatesStorageKey()
    localStorage.setItem(storageKey, JSON.stringify(expandedStates.value))
  }

  // 添加新日程
  const addSchedule = (schedule: Omit<Schedule, 'id' | 'created_at'>) => {
    const newSchedule: Schedule = {
      ...schedule,
      id: Date.now(),
      created_at: new Date().toISOString()
    }
    schedules.value.push(newSchedule)
    saveSchedulesToStorage()
  }

  // 更新日程
  const updateSchedule = (id: number, updatedSchedule: Partial<Schedule>) => {
    const index = schedules.value.findIndex(s => s.id === id)
    if (index !== -1) {
      schedules.value[index] = { ...schedules.value[index], ...updatedSchedule }
      saveSchedulesToStorage()
    }
  }

  // 删除日程
  const deleteSchedule = (id: number) => {
    const index = schedules.value.findIndex(s => s.id === id)
    if (index !== -1) {
      schedules.value.splice(index, 1)
      saveSchedulesToStorage()
    }
  }

  // 标记日程为完成
  const completeSchedule = (id: number) => {
    updateSchedule(id, { completed: true })
  }

  // 获取指定日期的日程
  const getSchedulesByDate = (date: string) => {
    return schedules.value.filter(s => s.date === date)
  }

  // 获取学生的日程
  const getSchedulesByStudent = (studentName: string) => {
    return schedules.value.filter(s => s.studentName === studentName)
  }

  // 切换日期组的展开状态
  const toggleDateGroupExpanded = (date: string) => {
    expandedStates.value[date] = !expandedStates.value[date]
    saveExpandedStatesToStorage()
  }

  // 获取日期组的展开状态
  const isDateGroupExpanded = (date: string): boolean => {
    return expandedStates.value[date] ?? true // 默认展开
  }

  // 获取按日期分组的日程
  const getGroupedSchedules = (): DateGroup[] => {
    const groups: Record<string, Schedule[]> = {}
    
    schedules.value.forEach(schedule => {
      if (!groups[schedule.date]) {
        groups[schedule.date] = []
      }
      groups[schedule.date].push(schedule)
    })

    return Object.keys(groups)
      .sort() // 按日期排序
      .map(date => ({
        date,
        schedules: groups[date].sort((a, b) => a.time.localeCompare(b.time)), // 按时间排序
        expanded: isDateGroupExpanded(date)
      }))
  }

  // 获取今日需要复习的数量
  const getTodayReviewCount = (): number => {
    const today = new Date().toISOString().split('T')[0]
    return schedules.value.filter(s => 
      s.date === today && 
      s.type === 'review' && 
      !s.completed
    ).length
  }

  // 重新加载当前用户的数据（用于用户切换时）
  const reloadUserData = () => {
    schedules.value = loadSchedulesFromStorage()
    expandedStates.value = loadExpandedStatesFromStorage()
  }

  // 管理员专用：跨用户操作方法
  const getSchedulesByUserId = (userId: string): Schedule[] => {
    try {
      const saved = localStorage.getItem(`schedule_${userId}`)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const deleteScheduleForUser = (userId: string, scheduleId: number) => {
    const userSchedules = getSchedulesByUserId(userId)
    const updatedSchedules = userSchedules.filter(s => s.id !== scheduleId)
    localStorage.setItem(`schedule_${userId}`, JSON.stringify(updatedSchedules))
  }

  // 获取指定用户的按日期分组的日程
  const getGroupedSchedulesByUserId = (userId: string): DateGroup[] => {
    const userSchedules = getSchedulesByUserId(userId)
    const groups: Record<string, Schedule[]> = {}
    
    userSchedules.forEach(schedule => {
      if (!groups[schedule.date]) {
        groups[schedule.date] = []
      }
      groups[schedule.date].push(schedule)
    })

    return Object.keys(groups)
      .sort() // 按日期排序
      .map(date => ({
        date,
        schedules: groups[date].sort((a, b) => a.time.localeCompare(b.time)), // 按时间排序
        expanded: isDateGroupExpanded(date)
      }))
  }

  return {
    schedules,
    expandedStates,
    addSchedule,
    updateSchedule,
    deleteSchedule,
    completeSchedule,
    getSchedulesByDate,
    getSchedulesByStudent,
    toggleDateGroupExpanded,
    isDateGroupExpanded,
    getGroupedSchedules,
    getTodayReviewCount,
    reloadUserData,
    getSchedulesByUserId,
    deleteScheduleForUser,
    getGroupedSchedulesByUserId
  }
})