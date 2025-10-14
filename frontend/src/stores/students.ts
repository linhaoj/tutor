import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export interface Student {
  id: number
  name: string
  email?: string
  total_words?: number
  learned_words?: number
  remainingHours?: number  // 剩余课程时长，以小时为单位
  username?: string // 学生账号用户名
  hasAccount?: boolean // 是否已创建账号
  userId?: string // 关联的User ID
}

export const useStudentsStore = defineStore('students', () => {
  const authStore = useAuthStore()
  
  // 获取当前用户的localStorage key
  const getStorageKey = () => {
    const currentUser = authStore.currentUser
    return currentUser ? `students_${currentUser.id}` : 'students_guest'
  }
  
  // 从localStorage加载初始数据（按用户隔离）
  const loadFromStorage = () => {
    try {
      const storageKey = getStorageKey()
      const saved = localStorage.getItem(storageKey)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const students = ref<Student[]>(loadFromStorage())

  // 保存到localStorage（按用户隔离）
  const saveToStorage = () => {
    const storageKey = getStorageKey()
    localStorage.setItem(storageKey, JSON.stringify(students.value))
  }

  const addStudent = (student: Student) => {
    students.value.push(student)
    saveToStorage()
  }

  const updateStudent = (id: number, updatedStudent: Partial<Student>) => {
    const index = students.value.findIndex(s => s.id === id)
    if (index !== -1) {
      students.value[index] = { ...students.value[index], ...updatedStudent }
      saveToStorage()
    }
  }

  const deleteStudent = (id: number) => {
    const index = students.value.findIndex(s => s.id === id)
    if (index !== -1) {
      students.value.splice(index, 1)
      saveToStorage()
    }
  }

  const getStudent = (id: number) => {
    return students.value.find(s => s.id === id)
  }

  // 重新加载当前用户的数据（用于用户切换时）
  const reloadUserData = () => {
    students.value = loadFromStorage()
  }

  // 管理员专用：跨用户操作方法
  const getStudentsByUserId = (userId: string): Student[] => {
    try {
      const saved = localStorage.getItem(`students_${userId}`)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const deleteStudentForUser = (userId: string, studentId: number) => {
    const userStudents = getStudentsByUserId(userId)
    const updatedStudents = userStudents.filter(s => s.id !== studentId)
    localStorage.setItem(`students_${userId}`, JSON.stringify(updatedStudents))
  }

  // 扣减学生课程时长
  const deductStudentHours = (studentId: number, hours: number, userId?: string) => {
    if (userId) {
      // 跨用户操作（管理员功能）
      const userStudents = getStudentsByUserId(userId)
      const studentIndex = userStudents.findIndex(s => s.id === studentId)
      if (studentIndex !== -1) {
        const currentHours = userStudents[studentIndex].remainingHours || 0
        userStudents[studentIndex].remainingHours = Math.max(0, currentHours - hours)
        localStorage.setItem(`students_${userId}`, JSON.stringify(userStudents))
        console.log(`学生 ${userStudents[studentIndex].name} 课程时长扣减 ${hours}h，剩余: ${userStudents[studentIndex].remainingHours}h`)
        return true
      }
    } else {
      // 当前用户操作
      const student = students.value.find(s => s.id === studentId)
      if (student) {
        const currentHours = student.remainingHours || 0
        student.remainingHours = Math.max(0, currentHours - hours)
        saveToStorage()
        console.log(`学生 ${student.name} 课程时长扣减 ${hours}h，剩余: ${student.remainingHours}h`)
        return true
      }
    }
    return false
  }

  return { 
    students, 
    addStudent, 
    updateStudent, 
    deleteStudent, 
    getStudent,
    saveToStorage,
    reloadUserData,
    getStudentsByUserId,
    deleteStudentForUser,
    deductStudentHours
  }
})