import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Student {
  id: number
  name: string
  email?: string
  total_words?: number
  learned_words?: number
}

export const useStudentsStore = defineStore('students', () => {
  // 从localStorage加载初始数据
  const loadFromStorage = () => {
    try {
      const saved = localStorage.getItem('students')
      return saved ? JSON.parse(saved) : [
        { id: 1, name: '张三', email: 'zhangsan@example.com', total_words: 100, learned_words: 30 },
        { id: 2, name: '李四', email: 'lisi@example.com', total_words: 150, learned_words: 80 }
      ]
    } catch {
      return [
        { id: 1, name: '张三', email: 'zhangsan@example.com', total_words: 100, learned_words: 30 },
        { id: 2, name: '李四', email: 'lisi@example.com', total_words: 150, learned_words: 80 }
      ]
    }
  }

  const students = ref<Student[]>(loadFromStorage())

  // 保存到localStorage
  const saveToStorage = () => {
    localStorage.setItem('students', JSON.stringify(students.value))
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

  return { 
    students, 
    addStudent, 
    updateStudent, 
    deleteStudent, 
    getStudent 
  }
})