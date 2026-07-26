/**
 * 听力课 Store
 * 管理OCR识别、翻译、音频上传、时间戳对齐、文章保存
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface ParagraphTimestamp {
  index: number
  text: string
  start: number
  end: number
  match_score?: number
}

export interface ListeningArticle {
  id: number
  schedule_id: number | null
  title: string | null
  article_content: string
  translation: string[]
  paragraph_timestamps: ParagraphTimestamp[]
  audio_url: string
  audio_duration_seconds: number
  created_at: string
}

export interface AntiForgetWordItem {
  english: string
  chinese: string
}

export const useListeningStore = defineStore('listening', () => {
  const loading = ref(false)

  /**
   * 截图识别文字（OCR）
   */
  async function ocrImage(imageFile: File) {
    const formData = new FormData()
    formData.append('image', imageFile)
    const res = await api.post('/api/listening/ocr', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data as { recognized_text: string }
  }

  /**
   * 按段落翻译原文
   */
  async function translateArticle(articleContent: string) {
    const res = await api.post('/api/listening/translate', {
      article_content: articleContent
    })
    return res.data as { translation: string[] }
  }

  /**
   * 上传音频文件
   */
  async function uploadAudio(audioFile: File) {
    const formData = new FormData()
    formData.append('audio', audioFile)
    const res = await api.post('/api/listening/upload-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data as { temp_audio_id: string; duration_seconds: number; original_filename: string }
  }

  /**
   * 自动对齐时间戳（调用腾讯云ASR + 文本相似度匹配）
   */
  async function alignTimestamps(tempAudioId: string, articleContent: string) {
    const res = await api.post('/api/listening/align-timestamps', {
      temp_audio_id: tempAudioId,
      article_content: articleContent
    })
    return res.data as { paragraphs: ParagraphTimestamp[]; audio_duration_seconds: number }
  }

  /**
   * 保存文章（含确认后的时间戳）
   */
  async function saveArticle(payload: {
    title?: string
    articleContent: string
    translation: string[]
    paragraphTimestamps: ParagraphTimestamp[]
    tempAudioId: string
    audioOriginalFilename: string
    audioMimetype: string
    audioDurationSeconds: number
  }) {
    const res = await api.post('/api/listening/articles', {
      title: payload.title,
      article_content: payload.articleContent,
      translation: payload.translation,
      paragraph_timestamps: payload.paragraphTimestamps,
      temp_audio_id: payload.tempAudioId,
      audio_original_filename: payload.audioOriginalFilename,
      audio_mimetype: payload.audioMimetype,
      audio_duration_seconds: payload.audioDurationSeconds
    })
    return res.data as { id: number; created_at: string }
  }

  /**
   * 编辑文章
   */
  async function updateArticle(
    articleId: number,
    payload: { articleContent?: string; translation?: string[]; paragraphTimestamps?: ParagraphTimestamp[] }
  ) {
    const res = await api.put(`/api/listening/articles/${articleId}`, {
      article_content: payload.articleContent,
      translation: payload.translation,
      paragraph_timestamps: payload.paragraphTimestamps
    })
    return res.data as { id: number; created_at: string }
  }

  /**
   * 将文章绑定到课程
   */
  async function bindArticleToSchedule(articleId: number, scheduleId: number) {
    await api.post(`/api/listening/articles/${articleId}/bind-schedule`, {
      schedule_id: scheduleId
    })
  }

  /**
   * 根据课程ID获取文章
   */
  async function getArticleBySchedule(scheduleId: number) {
    try {
      const res = await api.get(`/api/listening/articles/by-schedule/${scheduleId}`)
      return res.data as ListeningArticle
    } catch {
      return null
    }
  }

  /**
   * 双击单词，AI给出上下文中的中文释义
   */
  async function lookupWord(word: string, articleContext: string) {
    const res = await api.post('/api/listening/lookup-word', {
      word,
      article_context: articleContext
    })
    return res.data as { word: string; chinese_meaning: string }
  }

  /**
   * 听力课结课创建抗遗忘
   */
  async function createListeningAntiForget(
    studentId: number,
    words: AntiForgetWordItem[],
    time: string,
    scheduleId: number
  ) {
    const res = await api.post('/api/listening/create-anti-forget', {
      student_id: studentId,
      words,
      time,
      schedule_id: scheduleId
    })
    return res.data
  }

  return {
    loading,
    ocrImage,
    translateArticle,
    uploadAudio,
    alignTimestamps,
    saveArticle,
    updateArticle,
    bindArticleToSchedule,
    getArticleBySchedule,
    lookupWord,
    createListeningAntiForget
  }
})
