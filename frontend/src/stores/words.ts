import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Word {
  id: number
  english: string
  chinese: string
  word_set?: string
}

export interface WordSet {
  name: string
  words?: Word[]
}

export const useWordsStore = defineStore('words', () => {
  // 从localStorage加载单词数据
  const loadWordsFromStorage = () => {
    try {
      const saved = localStorage.getItem('words')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  // 从localStorage加载单词集数据
  const loadWordSetsFromStorage = () => {
    try {
      const saved = localStorage.getItem('wordSets')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  const words = ref<Word[]>(loadWordsFromStorage())
  const wordSets = ref<WordSet[]>(loadWordSetsFromStorage())

  // 保存到localStorage
  const saveWordsToStorage = () => {
    localStorage.setItem('words', JSON.stringify(words.value))
  }

  const saveWordSetsToStorage = () => {
    localStorage.setItem('wordSets', JSON.stringify(wordSets.value))
  }

  const addWord = (word: Word) => {
    words.value.push(word)
    saveWordsToStorage()
    
    // 如果是新的单词集，也要添加到wordSets中
    if (word.word_set && !wordSets.value.find(s => s.name === word.word_set)) {
      wordSets.value.push({ name: word.word_set })
      saveWordSetsToStorage()
    }
  }

  const updateWord = (id: number, updatedWord: Partial<Word>) => {
    const index = words.value.findIndex(w => w.id === id)
    if (index !== -1) {
      const oldWordSet = words.value[index].word_set
      words.value[index] = { ...words.value[index], ...updatedWord }
      saveWordsToStorage()
      
      // 如果是新的单词集，添加到wordSets中
      if (updatedWord.word_set && updatedWord.word_set !== oldWordSet && 
          !wordSets.value.find(s => s.name === updatedWord.word_set)) {
        wordSets.value.push({ name: updatedWord.word_set })
        saveWordSetsToStorage()
      }
    }
  }

  const deleteWord = (id: number) => {
    const index = words.value.findIndex(w => w.id === id)
    if (index !== -1) {
      words.value.splice(index, 1)
      saveWordsToStorage()
    }
  }
  

  const deleteWordSet = (wordSetName: string) => {
    // 删除该单词集下的所有单词
    words.value = words.value.filter(w => w.word_set !== wordSetName)
    saveWordsToStorage()
    
    // 从单词集列表中移除
    const setIndex = wordSets.value.findIndex(s => s.name === wordSetName)
    if (setIndex !== -1) {
      wordSets.value.splice(setIndex, 1)
      saveWordSetsToStorage()
    }
  }

  const importWords = (newWords: Word[]) => {
    words.value.push(...newWords)
    saveWordsToStorage()
    
    // 更新单词集列表
    newWords.forEach(word => {
      if (word.word_set && !wordSets.value.find(s => s.name === word.word_set)) {
        wordSets.value.push({ name: word.word_set })
      }
    })
    saveWordSetsToStorage()
  }

  const getWordsBySet = (wordSetName: string) => {
    return words.value.filter(w => w.word_set === wordSetName)
  }

  const getWord = (id: number) => {
    return words.value.find(w => w.id === id)
  }

  // 管理员专用：跨用户操作方法
  const getWordSetsByUserId = (userId: string): WordSet[] => {
    try {
      // 先尝试从用户特定的数据中加载
      const saved = localStorage.getItem(`wordSets_${userId}`) || 
                   localStorage.getItem(`backup_wordSets_${userId}`)
      
      if (saved) {
        const userWordSets = JSON.parse(saved)
        console.log(`Words Store - 用户 ${userId} 的原始数据:`, userWordSets)
        
        // 为每个单词集加载其单词（如果单词集本身包含words字段就直接使用）
        const result = userWordSets.map((wordSet: any) => ({
          name: wordSet.name,
          description: wordSet.description || '',
          created_at: wordSet.created_at || '',
          userId: wordSet.userId || userId,
          words: wordSet.words || []
        }))
        
        console.log(`Words Store - 用户 ${userId} 的处理后数据:`, result)
        console.log(`Words Store - 第一个单词集的words:`, result[0]?.words)
        
        return result
      }
      
      return []
    } catch (error) {
      console.error('获取用户单词集失败:', error)
      return []
    }
  }

  const getWordsBySetForUser = (userId: string, wordSetName: string): Word[] => {
    console.log('=== getWordsBySetForUser 开始执行 ===', { userId, wordSetName })
    try {
      // 尝试多个可能的localStorage键
      const possibleKeys = [
        `words_${userId}`,
        `backup_words_${userId}`,
        `wordSets_${userId}`,
        `backup_wordSets_${userId}`
      ]
      
      console.log('getWordsBySetForUser - 查找单词:', { userId, wordSetName, possibleKeys })
      
      // 检查每个可能的键
      for (const key of possibleKeys) {
        const saved = localStorage.getItem(key)
        if (saved) {
          console.log(`getWordsBySetForUser - 找到数据在键 ${key}:`, saved.substring(0, 100) + '...')
          const data = JSON.parse(saved)
          
          // 如果是单词集格式，需要从words字段中过滤
          if (Array.isArray(data) && data.length > 0 && data[0].words) {
            console.log('getWordsBySetForUser - 检测到单词集格式，查找单词集:', data.map(ws => ws.name))
            const wordSet = data.find((ws: any) => ws.name === wordSetName)
            if (wordSet && wordSet.words) {
              console.log(`getWordsBySetForUser - 找到单词集 "${wordSetName}"，单词数:`, wordSet.words.length)
              return wordSet.words
            }
          } else if (Array.isArray(data)) {
            // 如果是直接的单词数组格式
            const filteredWords = data.filter((w: Word) => w.word_set === wordSetName)
            if (filteredWords.length > 0) {
              console.log(`getWordsBySetForUser - 找到单词（直接格式），数量:`, filteredWords.length)
              return filteredWords
            }
          }
        }
      }
      
      console.log(`getWordsBySetForUser - 未找到单词集 "${wordSetName}"`)
      return []
    } catch (error) {
      console.error('getWordsBySetForUser - 发生异常:', error)
      console.error('getWordsBySetForUser - 异常详情:', error.message, error.stack)
      return []
    }
  }

  return { 
    words, 
    wordSets,
    addWord, 
    updateWord, 
    deleteWord, 
    deleteWordSet,
    importWords,
    getWordsBySet,
    getWord,
    getWordSetsByUserId,
    getWordsBySetForUser
  }
})