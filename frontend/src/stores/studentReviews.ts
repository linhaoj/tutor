/**
 * 学生复习记录Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

// 学生复习记录中的单词
export interface ReviewWord {
  id: number
  english: string
  chinese: string
  is_starred?: boolean // 学生标记的星星
}

// 学生复习记录
export interface StudentReview {
  id: string // 唯一ID
  student_id: number // 学生ID
  word_set_name: string // 单词库名称
  learn_date: string // 学习日期 (YYYY-MM-DD)
  words: ReviewWord[] // 学习的单词列表
  created_at: string // 创建时间
}

export const useStudentReviewsStore = defineStore('studentReviews', () => {
  const reviews = ref<StudentReview[]>([])
  const loading = ref(false)

  /**
   * 创建新的复习记录
   */
  const createReview = async (
    studentId: number,
    wordSetName: string,
    learnDate: string,
    words: { id: number; english: string; chinese: string }[]
  ): Promise<string> => {
    try {
      const response = await api.post('/api/student-reviews/', {
        student_id: studentId,
        word_set_name: wordSetName,
        learn_date: learnDate,
        words: words.map(w => ({
          id: w.id,
          english: w.english,
          chinese: w.chinese,
          is_starred: false
        }))
      })

      reviews.value.push(response.data)
      console.log(`创建学生复习记录: 学生ID=${studentId}, 单词库=${wordSetName}, 日期=${learnDate}, 单词数=${words.length}`)
      return response.data.id
    } catch (error: any) {
      console.error('创建复习记录失败:', error)
      throw new Error(error.response?.data?.detail || '创建复习记录失败')
    }
  }

  /**
   * 获取学生的所有复习记录
   */
  const fetchStudentReviews = async (studentId: number): Promise<void> => {
    loading.value = true
    try {
      const response = await api.get(`/api/student-reviews/student/${studentId}`)
      reviews.value = response.data
      console.log(`获取学生${studentId}的复习记录:`, response.data.length, '条')
    } catch (error) {
      console.error('获取复习记录失败:', error)
      reviews.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取学生的所有复习记录（本地缓存）
   */
  const getStudentReviews = (studentId: number): StudentReview[] => {
    return reviews.value
      .filter(r => r.student_id === studentId)
      .sort((a, b) => new Date(b.learn_date).getTime() - new Date(a.learn_date).getTime())
  }

  /**
   * 获取特定复习记录（从服务器）
   */
  const fetchReview = async (reviewId: string): Promise<StudentReview | null> => {
    try {
      const response = await api.get(`/api/student-reviews/${reviewId}`)

      // 更新本地缓存
      const index = reviews.value.findIndex(r => r.id === reviewId)
      if (index !== -1) {
        reviews.value[index] = response.data
      } else {
        reviews.value.push(response.data)
      }

      return response.data
    } catch (error) {
      console.error('获取复习记录失败:', error)
      return null
    }
  }

  /**
   * 获取特定复习记录（本地缓存）
   */
  const getReview = (reviewId: string): StudentReview | null => {
    return reviews.value.find(r => r.id === reviewId) || null
  }

  /**
   * 更新单词的星星状态
   */
  const toggleWordStar = async (reviewId: string, wordId: number): Promise<boolean> => {
    try {
      const response = await api.post(`/api/student-reviews/${reviewId}/toggle-star/${wordId}`)

      // 更新本地缓存
      const review = reviews.value.find(r => r.id === reviewId)
      if (review) {
        const word = review.words.find(w => w.id === wordId)
        if (word) {
          word.is_starred = response.data.is_starred
          console.log(`单词 ${word.english} 星标状态切换为:`, word.is_starred)
        }
      }

      return response.data.is_starred
    } catch (error) {
      console.error('切换星标失败:', error)
      return false
    }
  }

  /**
   * 获取学生的已学单词统计（按单词库分组）
   */
  const getStudentWordsStats = (studentId: number) => {
    const studentReviews = getStudentReviews(studentId)

    // 按单词库统计
    const wordSetStats = new Map<string, Set<number>>()

    studentReviews.forEach(review => {
      if (!wordSetStats.has(review.word_set_name)) {
        wordSetStats.set(review.word_set_name, new Set())
      }
      review.words.forEach(word => {
        wordSetStats.get(review.word_set_name)!.add(word.id)
      })
    })

    // 总单词数（去重）
    const allWordIds = new Set<number>()
    studentReviews.forEach(review => {
      review.words.forEach(word => allWordIds.add(word.id))
    })

    return {
      totalWords: allWordIds.size,
      wordSetStats: Array.from(wordSetStats.entries()).map(([name, ids]) => ({
        wordSetName: name,
        count: ids.size
      }))
    }
  }

  /**
   * 删除复习记录
   */
  const deleteReview = async (reviewId: string): Promise<boolean> => {
    try {
      await api.delete(`/api/student-reviews/${reviewId}`)

      // 从本地缓存中移除
      const index = reviews.value.findIndex(r => r.id === reviewId)
      if (index !== -1) {
        reviews.value.splice(index, 1)
      }

      console.log('删除复习记录成功:', reviewId)
      return true
    } catch (error) {
      console.error('删除复习记录失败:', error)
      return false
    }
  }

  return {
    reviews,
    loading,
    createReview,
    fetchStudentReviews,
    getStudentReviews,
    fetchReview,
    getReview,
    toggleWordStar,
    getStudentWordsStats,
    deleteReview
  }
})
