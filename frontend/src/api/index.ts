import axios from 'axios'
import type { AxiosResponse } from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在这里可以添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// 类型定义
export interface Student {
  id: number
  name: string
  email?: string
  created_at: string
  total_words: number
  learned_words: number
}

export interface Word {
  id: number
  english: string
  chinese: string
  word_set?: string
}

export interface WordCard {
  id: number
  english: string
  chinese: string
  student_word_id: number
  current_stage: string
}

export interface LearningSession {
  id: number
  student_id: number
  words_count: number
  current_stage: string
  current_group: number
  total_groups: number
  completed: boolean
  word_cards: WordCard[]
}

export interface GridStats {
  grid_0: number
  grid_1: number
  grid_2: number
  grid_3: number
  grid_4: number
  grid_5: number
  grid_6: number
  grid_7: number
  grid_8: number
}

// 学生相关API
export const studentAPI = {
  // 获取所有学生
  getStudents: (): Promise<Student[]> => api.get('/students'),
  
  // 获取单个学生
  getStudent: (id: number): Promise<Student> => api.get(`/students/${id}`),
  
  // 创建学生
  createStudent: (data: { name: string; email?: string }): Promise<Student> => 
    api.post('/students', data),
  
  // 更新学生
  updateStudent: (id: number, data: { name: string; email?: string }): Promise<Student> =>
    api.put(`/students/${id}`, data),
  
  // 删除学生
  deleteStudent: (id: number): Promise<{ message: string }> =>
    api.delete(`/students/${id}`),
  
  // 获取学生统计
  getStudentStats: (id: number): Promise<any> => api.get(`/students/${id}/stats`)
}

// 单词相关API
export const wordAPI = {
  // 获取所有单词
  getWords: (wordSet?: string): Promise<Word[]> => 
    api.get('/words', { params: { word_set: wordSet } }),
  
  // 获取单词集列表
  getWordSets: (): Promise<{ name: string }[]> => api.get('/words/sets'),
  
  // 创建单词
  createWord: (data: { english: string; chinese: string; word_set?: string }): Promise<Word> =>
    api.post('/words', data),
  
  // 导入Excel单词
  importWordsFromExcel: (file: File, wordSet?: string): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    if (wordSet) {
      formData.append('word_set', wordSet)
    }
    return api.post('/words/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 分配单词给学生
  assignWordsToStudent: (data: { student_id: number; word_ids: number[] }): Promise<any> =>
    api.post('/words/assign', data),
  
  // 获取学生的单词
  getStudentWords: (studentId: number, gridPosition?: number): Promise<any[]> =>
    api.get(`/words/student/${studentId}`, { params: { grid_position: gridPosition } }),
  
  // 更新单词
  updateWord: (id: number, data: { english: string; chinese: string; word_set?: string }): Promise<Word> =>
    api.put(`/words/${id}`, data),
  
  // 删除单词
  deleteWord: (id: number): Promise<{ message: string }> =>
    api.delete(`/words/${id}`)
}

// 学习相关API
export const learningAPI = {
  // 开始学习会话
  startSession: (data: { student_id: number; words_count: number }): Promise<LearningSession> =>
    api.post('/learning/start', data),
  
  // 完成第一阶段
  completeStage1: (data: { session_id: number; results: any[] }): Promise<any> =>
    api.post('/learning/stage1/complete', data),
  
  // 获取第二阶段单词
  getStage2Words: (sessionId: number): Promise<LearningSession> =>
    api.get(`/learning/stage2/${sessionId}`),
  
  // 完成第二阶段
  completeStage2: (data: { session_id: number; results: any[] }): Promise<any> =>
    api.post('/learning/stage2/complete', data),
  
  // 获取第三阶段单词
  getStage3Words: (sessionId: number): Promise<LearningSession> =>
    api.get(`/learning/stage3/${sessionId}`),
  
  // 完成第三阶段
  completeStage3: (data: { session_id: number; results: any[] }): Promise<any> =>
    api.post('/learning/stage3/complete', data),
  
  // 获取九宫格统计
  getGridStats: (studentId: number): Promise<GridStats> =>
    api.get(`/learning/grid/${studentId}`),
  
  // 获取学生学习历史
  getStudentSessions: (studentId: number): Promise<any[]> =>
    api.get(`/learning/sessions/${studentId}`)
}

export default api