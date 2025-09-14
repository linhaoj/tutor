import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import tutorDB from '@/utils/localDatabase'

export interface User {
  id: string
  username: string
  role: 'admin' | 'teacher' // admin可以管理用户，teacher是普通老师
  displayName: string
  email?: string
  createdAt: string
  lastLoginAt?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  // 当前用户
  const currentUser = ref<User | null>(null)
  const isLoggedIn = computed(() => !!currentUser.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')

  // 从localStorage加载用户数据（简化版）
  const loadUsersFromStorage = (): User[] => {
    try {
      const saved = localStorage.getItem('backup_users_userList') || localStorage.getItem('users')
      return saved ? JSON.parse(saved) : []
    } catch (error) {
      console.error('加载用户数据失败:', error)
      return []
    }
  }

  // 从localStorage加载当前用户session（简化版）
  const loadCurrentUserFromStorage = (): User | null => {
    try {
      const saved = localStorage.getItem('currentUser')
      return saved ? JSON.parse(saved) : null
    } catch (error) {
      console.error('加载当前用户失败:', error)
      return null
    }
  }

  // 初始化默认管理员账号
  const initializeDefaultUsers = (): User[] => {
    const users = loadUsersFromStorage()
    
    console.log('初始化默认用户 - 当前用户数量:', users.length)
    console.log('初始化默认用户 - 当前用户:', users)
    
    // 如果没有用户，或者没有admin用户，创建默认管理员
    const adminExists = users.find(u => u.username === 'admin')
    if (users.length === 0 || !adminExists) {
      console.log('初始化默认用户 - 创建默认管理员')
      
      // 如果admin用户不存在，添加它
      if (!adminExists) {
        const defaultAdmin: User = {
          id: 'admin-001',
          username: 'admin',
          role: 'admin',
          displayName: '系统管理员',
          email: 'admin@example.com',
          createdAt: new Date().toISOString()
        }
        
        users.push(defaultAdmin)
        saveUsersToStorage(users)
      }
      
      // 确保admin密码存在
      const passwords = loadPasswordsFromStorage()
      if (!passwords['admin']) {
        passwords['admin'] = 'admin123'
        savePasswordsToStorage(passwords)
        console.log('初始化默认用户 - 保存默认密码')
      }
    }
    
    return users
  }

  // 保存用户数据到数据库
  const saveUsersToStorage = async (users: User[]) => {
    try {
      await tutorDB.save('users', users, 'userList')
    } catch (error) {
      console.error('保存用户数据失败:', error)
      // 回退到localStorage
      localStorage.setItem('users', JSON.stringify(users))
    }
  }

  const savePasswordsToStorage = async (passwords: Record<string, string>) => {
    try {
      await tutorDB.save('users', passwords, 'userPasswords')
    } catch (error) {
      console.error('保存密码数据失败:', error)
      // 回退到localStorage
      localStorage.setItem('userPasswords', JSON.stringify(passwords))
    }
  }

  const loadPasswordsFromStorage = (): Record<string, string> => {
    try {
      const saved = localStorage.getItem('backup_users_userPasswords') || localStorage.getItem('userPasswords')
      return saved ? JSON.parse(saved) : {}
    } catch (error) {
      console.error('加载密码数据失败:', error)
      return {}
    }
  }

  // 登录
  const login = async (credentials: LoginCredentials): Promise<{ success: boolean, message: string }> => {
    try {
      const users = loadUsersFromStorage()
      const passwords = loadPasswordsFromStorage()
      
      console.log('登录调试 - 用户列表:', users)
      console.log('登录调试 - 密码列表:', Object.keys(passwords))
      console.log('登录调试 - 尝试登录用户:', credentials.username)
      console.log('登录调试 - localStorage keys:', Object.keys(localStorage).filter(k => k.includes('user')))
      
      // 查找用户
      const user = users.find((u: User) => u.username === credentials.username)
      if (!user) {
        console.log('登录调试 - 用户未找到')
        return { success: false, message: '用户名不存在' }
      }

      // 验证密码
      const storedPassword = passwords[credentials.username]
      if (!storedPassword || storedPassword !== credentials.password) {
        return { success: false, message: '密码错误' }
      }

      // 更新最后登录时间
      user.lastLoginAt = new Date().toISOString()
      await saveUsersToStorage(users)

      // 设置当前用户
      currentUser.value = user
      localStorage.setItem('currentUser', JSON.stringify(user))

      return { success: true, message: '登录成功' }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, message: '登录过程中发生错误' }
    }
  }

  // 登出
  const logout = () => {
    currentUser.value = null
    localStorage.removeItem('currentUser')
  }

  // 注册新用户（仅管理员可用）
  const registerUser = async (userData: {
    username: string
    password: string
    displayName: string
    role: 'admin' | 'teacher'
    email?: string
  }): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value) {
      return { success: false, message: '权限不足' }
    }

    try {
      const users = await loadUsersFromStorage()
      const passwords = await loadPasswordsFromStorage()

      // 检查用户名是否已存在
      if (users.find((u: User) => u.username === userData.username)) {
        return { success: false, message: '用户名已存在' }
      }

      // 创建新用户
      const newUser: User = {
        id: `user-${Date.now()}`,
        username: userData.username,
        role: userData.role,
        displayName: userData.displayName,
        email: userData.email,
        createdAt: new Date().toISOString()
      }

      users.push(newUser)
      passwords[userData.username] = userData.password

      await saveUsersToStorage(users)
      await savePasswordsToStorage(passwords)

      return { success: true, message: '用户创建成功' }
    } catch (error) {
      console.error('Register error:', error)
      return { success: false, message: '创建用户过程中发生错误' }
    }
  }

  // 获取所有用户（仅管理员可用）
  const getAllUsers = async (): Promise<User[]> => {
    if (!isAdmin.value) return []
    return await loadUsersFromStorage()
  }

  // 删除用户（仅管理员可用）
  const deleteUser = async (userId: string): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value) {
      return { success: false, message: '权限不足' }
    }

    if (userId === currentUser.value?.id) {
      return { success: false, message: '不能删除自己的账号' }
    }

    try {
      const users = await loadUsersFromStorage()
      const passwords = await loadPasswordsFromStorage()

      const userIndex = users.findIndex((u: User) => u.id === userId)
      if (userIndex === -1) {
        return { success: false, message: '用户不存在' }
      }

      const userToDelete = users[userIndex]
      delete passwords[userToDelete.username]
      users.splice(userIndex, 1)

      await saveUsersToStorage(users)
      await savePasswordsToStorage(passwords)

      // 清理用户的个人数据
      localStorage.removeItem(`students_${userId}`)
      localStorage.removeItem(`schedule_${userId}`)
      localStorage.removeItem(`learningProgress_${userId}`)

      return { success: true, message: '用户删除成功' }
    } catch (error) {
      console.error('Delete user error:', error)
      return { success: false, message: '删除用户过程中发生错误' }
    }
  }

  // 修改用户信息（管理员或用户本人可用）
  const updateUser = async (userId: string, updates: Partial<User>): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value && userId !== currentUser.value?.id) {
      return { success: false, message: '权限不足' }
    }

    try {
      const users = await loadUsersFromStorage()
      const userIndex = users.findIndex((u: User) => u.id === userId)
      
      if (userIndex === -1) {
        return { success: false, message: '用户不存在' }
      }

      // 不允许修改的字段
      const { id, username, createdAt, ...allowedUpdates } = updates
      users[userIndex] = { ...users[userIndex], ...allowedUpdates }

      await saveUsersToStorage(users)

      // 如果修改的是当前用户，更新currentUser
      if (userId === currentUser.value?.id) {
        currentUser.value = users[userIndex]
        localStorage.setItem('currentUser', JSON.stringify(currentUser.value))
      }

      return { success: true, message: '用户信息更新成功' }
    } catch (error) {
      console.error('Update user error:', error)
      return { success: false, message: '更新用户信息过程中发生错误' }
    }
  }

  // 修改密码
  const changePassword = async (userId: string, oldPassword: string, newPassword: string): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value && userId !== currentUser.value?.id) {
      return { success: false, message: '权限不足' }
    }

    try {
      const users = await loadUsersFromStorage()
      const passwords = await loadPasswordsFromStorage()
      
      const user = users.find((u: User) => u.id === userId)
      if (!user) {
        return { success: false, message: '用户不存在' }
      }

      // 如果不是管理员，需要验证旧密码
      if (!isAdmin.value && passwords[user.username] !== oldPassword) {
        return { success: false, message: '原密码错误' }
      }

      passwords[user.username] = newPassword
      await savePasswordsToStorage(passwords)

      return { success: true, message: '密码修改成功' }
    } catch (error) {
      console.error('Change password error:', error)
      return { success: false, message: '修改密码过程中发生错误' }
    }
  }

  // 重置认证数据（临时调试用）
  const resetAuthData = () => {
    const keysToRemove = Object.keys(localStorage).filter(key => 
      key.includes('user') || key.includes('User') || key.includes('backup_')
    )
    keysToRemove.forEach(key => localStorage.removeItem(key))
    console.log('已清除认证相关数据:', keysToRemove)
  }

  // 初始化认证状态
  const initializeAuth = () => {
    try {
      // 临时调试：如果遇到登录问题，可以取消注释下面这行来重置数据
      // resetAuthData()
      
      // 确保有默认用户
      initializeDefaultUsers()
      
      // 恢复登录状态
      const savedUser = loadCurrentUserFromStorage()
      if (savedUser) {
        currentUser.value = savedUser
      }
    } catch (error) {
      console.error('初始化认证状态失败:', error)
    }
  }

  return {
    // 状态
    currentUser,
    isLoggedIn,
    isAdmin,

    // 方法
    login,
    logout,
    registerUser,
    getAllUsers,
    deleteUser,
    updateUser,
    changePassword,
    initializeAuth
  }
})