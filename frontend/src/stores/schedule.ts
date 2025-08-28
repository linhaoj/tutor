import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Schedule {
  id: number
  date: string
  time: string
  studentName: string
  studentId: number
  wordSet: string
  type: 'learning' | 'review'
  completed?: boolean
  created_at?: string
}

export interface DateGroup {
  date: string
  schedules: Schedule[]
  expanded: boolean
}

export const useScheduleStore = defineStore('schedule', () => {
  // 从localStorage加载日程数据
  const loadSchedulesFromStorage = () => {
    try {
      const saved = localStorage.getItem('schedules')
      return saved ? JSON.parse(saved) : [
        {
          id: 1,
          date: '2025-08-03',
          time: '09:00',
          studentName: '张三',
          studentId: 1,
          wordSet: '新版小学考纲单词V6.0',
          type: 'learning',
          completed: false,
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          date: '2025-08-03',
          time: '14:00',
          studentName: '李四',
          studentId: 2,
          wordSet: '【升序版】托福初级单词',
          type: 'review',
          completed: false,
          created_at: new Date().toISOString()
        },
        {
          id: 3,
          date: '2025-08-04',
          time: '10:00',
          studentName: '张三',
          studentId: 1,
          wordSet: '高中英语必修单词',
          type: 'learning',
          completed: false,
          created_at: new Date().toISOString()
        }
      ]
    } catch {
      return []
    }
  }

  // 从localStorage加载日期组展开状态
  const loadExpandedStatesFromStorage = () => {
    try {
      const saved = localStorage.getItem('scheduleDateStates')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  }

  const schedules = ref<Schedule[]>(loadSchedulesFromStorage())
  const expandedStates = ref<Record<string, boolean>>(loadExpandedStatesFromStorage())

  // 保存到localStorage
  const saveSchedulesToStorage = () => {
    localStorage.setItem('schedules', JSON.stringify(schedules.value))
  }

  const saveExpandedStatesToStorage = () => {
    localStorage.setItem('scheduleDateStates', JSON.stringify(expandedStates.value))
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
    getTodayReviewCount
  }
})