import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export interface Student {
  id: number
  name: string
  email?: string
  total_words?: number
  learned_words?: number
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

  return { 
    students, 
    addStudent, 
    updateStudent, 
    deleteStudent, 
    getStudent,
    reloadUserData
  }
})