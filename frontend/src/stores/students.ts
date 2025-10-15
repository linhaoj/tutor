/**
 * 学生Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface Student {
  id: number
  teacher_id: string
  name: string
  email?: string
  remaining_hours: number
  created_at: string
  updated_at: string
}

export const useStudentsStore = defineStore('students', () => {
  const students = ref<Student[]>([])
  const loading = ref(false)

  /**
   * 获取所有学生
   */
  const fetchStudents = async () => {
    loading.value = true
    try {
      const response = await api.get('/api/students')
      students.value = response.data
    } catch (error) {
      console.error('Fetch students error:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取单个学生
   */
  const getStudent = async (id: number): Promise<Student | null> => {
    try {
      const response = await api.get(`/api/students/${id}`)
      return response.data
    } catch (error) {
      console.error('Get student error:', error)
      return null
    }
  }

  /**
   * 创建学生
   */
  const addStudent = async (studentData: {
    name: string
    email?: string
    remaining_hours?: number
  }): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post('/api/students', studentData)
      students.value.push(response.data)
      return { success: true, message: '学生创建成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '创建学生失败'
      }
    }
  }

  /**
   * 更新学生信息
   */
  const updateStudent = async (
    id: number,
    updates: Partial<Student>
  ): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.put(`/api/students/${id}`, updates)
      const index = students.value.findIndex(s => s.id === id)
      if (index !== -1) {
        students.value[index] = response.data
      }
      return { success: true, message: '学生信息更新成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '更新学生失败'
      }
    }
  }

  /**
   * 删除学生
   */
  const deleteStudent = async (id: number): Promise<{ success: boolean, message: string }> => {
    try {
      await api.delete(`/api/students/${id}`)
      students.value = students.value.filter(s => s.id !== id)
      return { success: true, message: '学生删除成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '删除学生失败'
      }
    }
  }

  /**
   * 扣减学生课时
   */
  const deductStudentHours = async (
    id: number,
    hours: number
  ): Promise<{ success: boolean, message: string, remaining_hours?: number }> => {
    try {
      const response = await api.post(`/api/students/${id}/deduct-hours`, null, {
        params: { hours }
      })

      // 更新本地数据
      const index = students.value.findIndex(s => s.id === id)
      if (index !== -1) {
        students.value[index].remaining_hours = response.data.remaining_hours
      }

      return {
        success: true,
        message: response.data.message,
        remaining_hours: response.data.remaining_hours
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '扣减课时失败'
      }
    }
  }

  return {
    students,
    loading,
    fetchStudents,
    getStudent,
    addStudent,
    updateStudent,
    deleteStudent,
    deductStudentHours
  }
})
