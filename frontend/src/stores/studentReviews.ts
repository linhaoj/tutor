import { defineStore } from 'pinia'
import { ref } from 'vue'

// 学生复习记录中的单词
export interface ReviewWord {
  id: number
  english: string
  chinese: string
  isStarred?: boolean // 学生标记的星星
}

// 学生复习记录
export interface StudentReview {
  id: string // 唯一ID
  studentId: number // 学生ID
  wordSetName: string // 单词库名称
  learnDate: string // 学习日期 (YYYY-MM-DD)
  words: ReviewWord[] // 学习的单词列表
  createdAt: string // 创建时间
  lastReviewedAt?: string // 最后复习时间
}

export const useStudentReviewsStore = defineStore('studentReviews', () => {
  // 从localStorage加载数据
  const loadReviewsFromStorage = () => {
    try {
      const saved = localStorage.getItem('studentReviews')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const reviews = ref<StudentReview[]>(loadReviewsFromStorage())

  // 保存到localStorage
  const saveReviewsToStorage = () => {
    localStorage.setItem('studentReviews', JSON.stringify(reviews.value))
  }

  // 创建新的复习记录
  const createReview = (
    studentId: number,
    wordSetName: string,
    learnDate: string,
    words: { id: number; english: string; chinese: string }[]
  ): string => {
    const reviewId = `review_${studentId}_${Date.now()}`

    const newReview: StudentReview = {
      id: reviewId,
      studentId,
      wordSetName,
      learnDate,
      words: words.map(w => ({
        ...w,
        isStarred: false
      })),
      createdAt: new Date().toISOString()
    }

    reviews.value.push(newReview)
    saveReviewsToStorage()

    console.log(`创建学生复习记录: 学生ID=${studentId}, 单词库=${wordSetName}, 日期=${learnDate}, 单词数=${words.length}`)

    return reviewId
  }

  // 获取学生的所有复习记录
  const getStudentReviews = (studentId: number): StudentReview[] => {
    return reviews.value
      .filter(r => r.studentId === studentId)
      .sort((a, b) => new Date(b.learnDate).getTime() - new Date(a.learnDate).getTime())
  }

  // 获取特定复习记录
  const getReview = (reviewId: string): StudentReview | null => {
    return reviews.value.find(r => r.id === reviewId) || null
  }

  // 更新单词的星星状态
  const toggleWordStar = (reviewId: string, wordId: number): boolean => {
    const review = reviews.value.find(r => r.id === reviewId)
    if (!review) return false

    const word = review.words.find(w => w.id === wordId)
    if (!word) return false

    word.isStarred = !word.isStarred
    saveReviewsToStorage()

    return true
  }

  // 更新最后复习时间
  const updateLastReviewedAt = (reviewId: string) => {
    const review = reviews.value.find(r => r.id === reviewId)
    if (review) {
      review.lastReviewedAt = new Date().toISOString()
      saveReviewsToStorage()
    }
  }

  // 获取学生的已学单词统计（按单词库分组）
  const getStudentWordsStats = (studentId: number) => {
    const studentReviews = getStudentReviews(studentId)

    // 按单词库统计
    const wordSetStats = new Map<string, Set<number>>()

    studentReviews.forEach(review => {
      if (!wordSetStats.has(review.wordSetName)) {
        wordSetStats.set(review.wordSetName, new Set())
      }
      review.words.forEach(word => {
        wordSetStats.get(review.wordSetName)!.add(word.id)
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

  // 删除复习记录
  const deleteReview = (reviewId: string) => {
    const index = reviews.value.findIndex(r => r.id === reviewId)
    if (index !== -1) {
      reviews.value.splice(index, 1)
      saveReviewsToStorage()
    }
  }

  return {
    reviews,
    createReview,
    getStudentReviews,
    getReview,
    toggleWordStar,
    updateLastReviewedAt,
    getStudentWordsStats,
    deleteReview
  }
})
