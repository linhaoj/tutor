/**
 * 单词Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface Word {
  id: number
  english: string
  chinese: string
  word_set_name: string
}

export interface WordSet {
  id: number
  name: string
  owner_id: string
  is_global: boolean
  word_count: number
}

export const useWordsStore = defineStore('words', () => {
  const words = ref<Word[]>([])
  const wordSets = ref<WordSet[]>([])
  const loading = ref(false)
  const currentWordSetName = ref<string | null>(null)

  /**
   * 获取所有单词集（全局共享）
   */
  const fetchWordSets = async () => {
    loading.value = true
    try {
      const response = await api.get('/api/words/sets')
      wordSets.value = response.data
    } catch (error) {
      console.error('Fetch word sets error:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取指定单词集的所有单词
   */
  const fetchWords = async (wordSetName: string) => {
    loading.value = true
    try {
      const response = await api.get(`/api/words/sets/${encodeURIComponent(wordSetName)}/words`)
      words.value = response.data
      currentWordSetName.value = wordSetName
    } catch (error) {
      console.error('Fetch words error:', error)
      words.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建单词集
   */
  const createWordSet = async (data: {
    name: string
    is_global?: boolean
  }): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post('/api/words/sets', data)
      wordSets.value.push(response.data)
      return { success: true, message: '单词集创建成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '创建单词集失败'
      }
    }
  }

  /**
   * 添加单词到单词集
   */
  const addWord = async (wordSetName: string, wordData: {
    english: string
    chinese: string
  }): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post(
        `/api/words/sets/${encodeURIComponent(wordSetName)}/words`,
        wordData
      )

      // 如果当前正在查看这个单词集，添加到本地列表
      if (currentWordSetName.value === wordSetName) {
        words.value.push(response.data)
      }

      // 更新单词集的单词数量
      const wordSet = wordSets.value.find(ws => ws.name === wordSetName)
      if (wordSet) {
        wordSet.word_count++
      }

      return { success: true, message: '单词添加成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '添加单词失败'
      }
    }
  }

  /**
   * 删除单词
   */
  const deleteWord = async (wordId: number): Promise<{ success: boolean, message: string }> => {
    try {
      await api.delete(`/api/words/words/${wordId}`)

      // 从本地列表移除
      const wordIndex = words.value.findIndex(w => w.id === wordId)
      if (wordIndex !== -1) {
        const wordSetName = words.value[wordIndex].word_set_name
        words.value.splice(wordIndex, 1)

        // 更新单词集的单词数量
        const wordSet = wordSets.value.find(ws => ws.name === wordSetName)
        if (wordSet && wordSet.word_count > 0) {
          wordSet.word_count--
        }
      }

      return { success: true, message: '单词删除成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '删除单词失败'
      }
    }
  }

  /**
   * Excel导入单词
   */
  const importWordsFromExcel = async (
    wordSetName: string,
    file: File
  ): Promise<{ success: boolean, message: string }> => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post(
        `/api/words/sets/${encodeURIComponent(wordSetName)}/import-excel`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      // 刷新单词列表
      if (currentWordSetName.value === wordSetName) {
        await fetchWords(wordSetName)
      }

      // 刷新单词集列表（更新word_count）
      await fetchWordSets()

      return {
        success: true,
        message: response.data.message || 'Excel导入成功'
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || 'Excel导入失败'
      }
    }
  }

  /**
   * 获取单词集的单词（不改变当前状态，用于临时查询）
   */
  const getWordsBySet = async (wordSetName: string): Promise<Word[]> => {
    try {
      const response = await api.get(`/api/words/sets/${encodeURIComponent(wordSetName)}/words`)
      return response.data
    } catch (error) {
      console.error('Get words by set error:', error)
      return []
    }
  }

  /**
   * 获取单个单词
   */
  const getWord = (id: number): Word | undefined => {
    return words.value.find(w => w.id === id)
  }

  /**
   * 批量导入单词（兼容旧代码）
   */
  const importWords = async (wordSetName: string, newWords: Array<{ english: string, chinese: string }>) => {
    const results = []
    for (const word of newWords) {
      const result = await addWord(wordSetName, word)
      results.push(result)
    }
    return results
  }

  return {
    words,
    wordSets,
    loading,
    currentWordSetName,
    fetchWordSets,
    fetchWords,
    createWordSet,
    addWord,
    deleteWord,
    importWordsFromExcel,
    getWordsBySet,
    getWord,
    importWords
  }
})
