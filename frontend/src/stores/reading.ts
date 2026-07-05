/**
 * 阅读课 Store
 * 管理文章生成、保存、编辑
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface WordItem {
  english: string
  chinese: string
}

export interface ReadingArticle {
  id: number
  schedule_id: number | null
  word_set_name: string
  words_used: WordItem[]
  article_content: string
  translation: string[]    // 按段落的中文翻译
  word_count: number
  created_at: string
}

export const useReadingStore = defineStore('reading', () => {
  const loading = ref(false)

  /**
   * 调用后端 Gemini 接口生成文章
   */
  async function generateArticle(wordSetName: string, words: WordItem[]) {
    loading.value = true
    try {
      const res = await api.post('/api/reading/generate', {
        word_set_name: wordSetName,
        words
      })
      return res.data as { article: string; translation: string[]; word_count: number; words_used: WordItem[] }
    } finally {
      loading.value = false
    }
  }

  /**
   * 双击单词，AI 给出上下文中的中文释义
   */
  async function lookupWord(word: string, articleContext: string) {
    const res = await api.post('/api/reading/lookup-word', {
      word,
      article_context: articleContext
    })
    return res.data as { word: string; chinese_meaning: string }
  }

  /**
   * 保存文章到数据库（含翻译）
   */
  async function saveArticle(
    wordSetName: string,
    wordsUsed: WordItem[],
    articleContent: string,
    translation: string[],
    wordCount: number
  ) {
    const res = await api.post('/api/reading/articles', {
      word_set_name: wordSetName,
      words_used: wordsUsed,
      article_content: articleContent,
      translation,
      word_count: wordCount
    })
    return res.data as { id: number; word_count: number; created_at: string }
  }

  /**
   * 阅读课结课创建抗遗忘
   */
  async function createReadingAntiForget(
    studentId: number,
    wordSetName: string,
    words: WordItem[],
    time: string,
    scheduleId: number
  ) {
    const res = await api.post('/api/reading/create-anti-forget', {
      student_id: studentId,
      word_set_name: wordSetName,
      words,
      time,
      schedule_id: scheduleId
    })
    return res.data
  }

  /**
   * 编辑文章内容
   */
  async function updateArticle(articleId: number, articleContent: string) {
    const res = await api.put(`/api/reading/articles/${articleId}`, {
      article_content: articleContent
    })
    return res.data as { id: number; word_count: number; created_at: string }
  }

  /**
   * 将文章绑定到课程
   */
  async function bindArticleToSchedule(articleId: number, scheduleId: number) {
    await api.post(`/api/reading/articles/${articleId}/bind-schedule`, {
      schedule_id: scheduleId
    })
  }

  /**
   * 根据课程ID获取文章
   */
  async function getArticleBySchedule(scheduleId: number) {
    try {
      const res = await api.get(`/api/reading/articles/by-schedule/${scheduleId}`)
      return res.data as ReadingArticle
    } catch {
      return null
    }
  }

  /**
   * 获取学生在某单词集格子1-7的已学单词
   */
  async function getLearnedWords(studentId: number, wordSetName: string) {
    const res = await api.get(`/api/reading/learned-words/${studentId}/${encodeURIComponent(wordSetName)}`)
    return res.data.words as Array<{
      id: number
      english: string
      chinese: string
      stage: number
      index: number
    }>
  }

  return {
    loading,
    generateArticle,
    lookupWord,
    saveArticle,
    updateArticle,
    bindArticleToSchedule,
    getArticleBySchedule,
    getLearnedWords,
    createReadingAntiForget
  }
})
