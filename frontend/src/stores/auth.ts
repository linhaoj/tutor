import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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

  // 从localStorage加载用户数据
  const loadUsersFromStorage = () => {
    try {
      const saved = localStorage.getItem('users')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  // 从localStorage加载当前用户session
  const loadCurrentUserFromStorage = () => {
    try {
      const saved = localStorage.getItem('currentUser')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  }

  // 初始化默认管理员账号
  const initializeDefaultUsers = () => {
    const users = loadUsersFromStorage()
    
    // 如果没有用户，创建默认管理员
    if (users.length === 0) {
      const defaultAdmin: User = {
        id: 'admin-001',
        username: 'admin',
        role: 'admin',
        displayName: '系统管理员',
        email: 'admin@example.com',
        createdAt: new Date().toISOString()
      }
      
      users.push(defaultAdmin)
      localStorage.setItem('users', JSON.stringify(users))
      
      // 同时保存默认密码（实际项目中应该加密）
      const passwords = { 'admin': 'admin123' }
      localStorage.setItem('userPasswords', JSON.stringify(passwords))
    }
    
    return users
  }

  // 保存用户数据到localStorage
  const saveUsersToStorage = (users: User[]) => {
    localStorage.setItem('users', JSON.stringify(users))
  }

  const savePasswordsToStorage = (passwords: Record<string, string>) => {
    localStorage.setItem('userPasswords', JSON.stringify(passwords))
  }

  // 登录
  const login = async (credentials: LoginCredentials): Promise<{ success: boolean, message: string }> => {
    try {
      const users = loadUsersFromStorage()
      const passwords = JSON.parse(localStorage.getItem('userPasswords') || '{}')
      
      // 查找用户
      const user = users.find((u: User) => u.username === credentials.username)
      if (!user) {
        return { success: false, message: '用户名不存在' }
      }

      // 验证密码
      const storedPassword = passwords[credentials.username]
      if (!storedPassword || storedPassword !== credentials.password) {
        return { success: false, message: '密码错误' }
      }

      // 更新最后登录时间
      user.lastLoginAt = new Date().toISOString()
      saveUsersToStorage(users)

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
      const users = loadUsersFromStorage()
      const passwords = JSON.parse(localStorage.getItem('userPasswords') || '{}')

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

      saveUsersToStorage(users)
      savePasswordsToStorage(passwords)

      return { success: true, message: '用户创建成功' }
    } catch (error) {
      console.error('Register error:', error)
      return { success: false, message: '创建用户过程中发生错误' }
    }
  }

  // 获取所有用户（仅管理员可用）
  const getAllUsers = (): User[] => {
    if (!isAdmin.value) return []
    return loadUsersFromStorage()
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
      const users = loadUsersFromStorage()
      const passwords = JSON.parse(localStorage.getItem('userPasswords') || '{}')

      const userIndex = users.findIndex((u: User) => u.id === userId)
      if (userIndex === -1) {
        return { success: false, message: '用户不存在' }
      }

      const userToDelete = users[userIndex]
      delete passwords[userToDelete.username]
      users.splice(userIndex, 1)

      saveUsersToStorage(users)
      savePasswordsToStorage(passwords)

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
      const users = loadUsersFromStorage()
      const userIndex = users.findIndex((u: User) => u.id === userId)
      
      if (userIndex === -1) {
        return { success: false, message: '用户不存在' }
      }

      // 不允许修改的字段
      const { id, username, createdAt, ...allowedUpdates } = updates
      users[userIndex] = { ...users[userIndex], ...allowedUpdates }

      saveUsersToStorage(users)

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
      const users = loadUsersFromStorage()
      const passwords = JSON.parse(localStorage.getItem('userPasswords') || '{}')
      
      const user = users.find((u: User) => u.id === userId)
      if (!user) {
        return { success: false, message: '用户不存在' }
      }

      // 如果不是管理员，需要验证旧密码
      if (!isAdmin.value && passwords[user.username] !== oldPassword) {
        return { success: false, message: '原密码错误' }
      }

      passwords[user.username] = newPassword
      savePasswordsToStorage(passwords)

      return { success: true, message: '密码修改成功' }
    } catch (error) {
      console.error('Change password error:', error)
      return { success: false, message: '修改密码过程中发生错误' }
    }
  }

  // 初始化认证状态
  const initializeAuth = () => {
    // 确保有默认用户
    initializeDefaultUsers()
    
    // 恢复登录状态
    const savedUser = loadCurrentUserFromStorage()
    if (savedUser) {
      currentUser.value = savedUser
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