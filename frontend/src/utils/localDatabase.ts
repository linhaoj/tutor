/**
 * 本地文件数据库服务
 * 使用IndexedDB作为主要存储，localStorage作为备份
 */

interface DatabaseConfig {
  name: string
  version: number
  stores: string[]
}

class LocalDatabase {
  private db: IDBDatabase | null = null
  private dbName: string
  private version: number
  private stores: string[]

  constructor(config: DatabaseConfig) {
    this.dbName = config.name
    this.version = config.version
    this.stores = config.stores
  }

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version)

      request.onerror = () => {
        console.error('数据库打开失败:', request.error)
        reject(request.error)
      }

      request.onsuccess = () => {
        this.db = request.result
        console.log('数据库连接成功')
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        // 创建对象存储
        this.stores.forEach(storeName => {
          if (!db.objectStoreNames.contains(storeName)) {
            const objectStore = db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true })
            // 为用户数据创建索引
            if (storeName !== 'users' && storeName !== 'words') {
              objectStore.createIndex('userId', 'userId', { unique: false })
            }
          }
        })
      }
    })
  }

  async save<T>(storeName: string, data: T, key?: string): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const objectStore = transaction.objectStore(storeName)
      
      const saveData = key ? { id: key, data, timestamp: Date.now() } : { data, timestamp: Date.now() }
      const request = key ? objectStore.put(saveData) : objectStore.add(saveData)

      request.onsuccess = () => {
        // 同时保存到localStorage作为备份
        const backupKey = key ? `backup_${storeName}_${key}` : `backup_${storeName}`
        localStorage.setItem(backupKey, JSON.stringify(data))
        resolve()
      }

      request.onerror = () => {
        console.error(`保存数据失败 [${storeName}]:`, request.error)
        // 如果IndexedDB失败，至少保存到localStorage
        const backupKey = key ? `backup_${storeName}_${key}` : `backup_${storeName}`
        localStorage.setItem(backupKey, JSON.stringify(data))
        resolve() // 不reject，因为localStorage备份成功
      }
    })
  }

  async load<T>(storeName: string, key?: string): Promise<T | null> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const objectStore = transaction.objectStore(storeName)
      
      const request = key ? objectStore.get(key) : objectStore.getAll()

      request.onsuccess = () => {
        const result = request.result
        if (result) {
          if (Array.isArray(result)) {
            resolve(result.map(item => item.data) as T)
          } else {
            resolve(result.data as T)
          }
        } else {
          // 尝试从localStorage备份中读取
          const backupKey = key ? `backup_${storeName}_${key}` : `backup_${storeName}`
          const backup = localStorage.getItem(backupKey)
          resolve(backup ? JSON.parse(backup) : null)
        }
      }

      request.onerror = () => {
        console.error(`读取数据失败 [${storeName}]:`, request.error)
        // 从localStorage备份中读取
        const backupKey = key ? `backup_${storeName}_${key}` : `backup_${storeName}`
        const backup = localStorage.getItem(backupKey)
        resolve(backup ? JSON.parse(backup) : null)
      }
    })
  }

  async loadByUserId<T>(storeName: string, userId: string): Promise<T[]> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const objectStore = transaction.objectStore(storeName)
      
      if (objectStore.indexNames.contains('userId')) {
        const index = objectStore.index('userId')
        const request = index.getAll(userId)

        request.onsuccess = () => {
          const result = request.result || []
          resolve(result.map(item => item.data))
        }

        request.onerror = () => {
          console.error(`按用户ID读取数据失败 [${storeName}]:`, request.error)
          // 从localStorage备份中读取
          const backupKey = `backup_${storeName}_${userId}`
          const backup = localStorage.getItem(backupKey)
          resolve(backup ? JSON.parse(backup) : [])
        }
      } else {
        resolve([])
      }
    })
  }

  async delete(storeName: string, key: string): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const objectStore = transaction.objectStore(storeName)
      
      const request = objectStore.delete(key)

      request.onsuccess = () => {
        // 同时删除localStorage备份
        localStorage.removeItem(`backup_${storeName}_${key}`)
        resolve()
      }

      request.onerror = () => {
        console.error(`删除数据失败 [${storeName}]:`, request.error)
        // 删除localStorage备份
        localStorage.removeItem(`backup_${storeName}_${key}`)
        reject(request.error)
      }
    })
  }

  async exportData(): Promise<Record<string, any>> {
    const exportData: Record<string, any> = {}

    for (const storeName of this.stores) {
      try {
        const data = await this.load(storeName)
        exportData[storeName] = data
      } catch (error) {
        console.error(`导出数据失败 [${storeName}]:`, error)
      }
    }

    return exportData
  }

  async importData(data: Record<string, any>): Promise<void> {
    for (const [storeName, storeData] of Object.entries(data)) {
      if (this.stores.includes(storeName)) {
        try {
          await this.save(storeName, storeData)
        } catch (error) {
          console.error(`导入数据失败 [${storeName}]:`, error)
        }
      }
    }
  }

  // 数据备份到文件
  async backupToFile(): Promise<void> {
    try {
      const data = await this.exportData()
      const dataStr = JSON.stringify(data, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `tutor-backup-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      
      console.log('数据备份完成')
    } catch (error) {
      console.error('数据备份失败:', error)
      throw error
    }
  }

  // 从文件恢复数据
  async restoreFromFile(file: File): Promise<void> {
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      await this.importData(data)
      console.log('数据恢复完成')
    } catch (error) {
      console.error('数据恢复失败:', error)
      throw error
    }
  }
}

// 创建数据库实例
export const tutorDB = new LocalDatabase({
  name: 'TutorDatabase',
  version: 1,
  stores: ['users', 'students', 'words', 'wordSets', 'schedules', 'learningProgress', 'settings', 'currentUser']
})

// 初始化数据库
export const initDatabase = async (): Promise<void> => {
  try {
    await tutorDB.init()
    console.log('Tutor数据库初始化完成')
  } catch (error) {
    console.error('数据库初始化失败:', error)
    // 即使IndexedDB失败，我们仍然可以使用localStorage
  }
}

export default tutorDB