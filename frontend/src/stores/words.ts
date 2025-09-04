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

  return { 
    words, 
    wordSets,
    addWord, 
    updateWord, 
    deleteWord, 
    deleteWordSet,
    importWords,
    getWordsBySet,
    getWord
  }
})