/**
 * 认证Store - 连接后端API
 * 使用JWT token进行身份验证
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/config'

export interface User {
  id: string
  username: string
  role: 'admin' | 'teacher' | 'student'
  display_name: string
  email?: string
  created_at: string
  last_login_at?: string
  student_id?: number
}

export interface LoginCredentials {
  username: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const currentUser = ref<User | null>(null)
  const authToken = ref<string | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!currentUser.value && !!authToken.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')
  const isStudent = computed(() => currentUser.value?.role === 'student')

  /**
   * 登录
   */
  const login = async (credentials: LoginCredentials): Promise<{ success: boolean, message: string }> => {
    try {
      // 使用FormData发送登录请求（OAuth2标准）
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await api.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const { access_token } = response.data

      // 保存token
      authToken.value = access_token
      localStorage.setItem('auth_token', access_token)

      // 获取当前用户信息
      await fetchCurrentUser()

      return { success: true, message: '登录成功' }
    } catch (error: any) {
      console.error('Login error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    }
  }

  /**
   * 获取当前用户信息
   */
  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/api/auth/me')
      currentUser.value = response.data
      localStorage.setItem('current_user', JSON.stringify(response.data))
    } catch (error) {
      console.error('Fetch current user error:', error)
      // 清除认证信息
      logout()
      throw error
    }
  }

  /**
   * 登出
   */
  const logout = () => {
    currentUser.value = null
    authToken.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('current_user')
  }

  /**
   * 注册新用户（仅管理员）
   */
  const registerUser = async (userData: {
    username: string
    password: string
    display_name: string
    role: 'admin' | 'teacher' | 'student'
    email?: string
    student_id?: number
  }): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value) {
      return { success: false, message: '权限不足' }
    }

    try {
      await api.post('/api/auth/register', userData)
      return { success: true, message: '用户创建成功' }
    } catch (error: any) {
      console.error('Register user error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '创建用户失败'
      }
    }
  }

  /**
   * 获取所有用户（仅管理员）
   */
  const getAllUsers = async (): Promise<User[]> => {
    if (!isAdmin.value) return []

    try {
      const response = await api.get('/api/auth/users')
      return response.data
    } catch (error) {
      console.error('Get all users error:', error)
      return []
    }
  }

  /**
   * 删除用户（仅管理员）
   */
  const deleteUser = async (userId: string): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value) {
      return { success: false, message: '权限不足' }
    }

    if (userId === currentUser.value?.id) {
      return { success: false, message: '不能删除自己的账号' }
    }

    try {
      await api.delete(`/api/auth/users/${userId}`)
      return { success: true, message: '用户删除成功' }
    } catch (error: any) {
      console.error('Delete user error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '删除用户失败'
      }
    }
  }

  /**
   * 更新用户信息（管理员或用户本人）
   */
  const updateUser = async (
    userId: string,
    updates: { display_name?: string; email?: string }
  ): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value && userId !== currentUser.value?.id) {
      return { success: false, message: '权限不足' }
    }

    try {
      const response = await api.put(`/api/auth/users/${userId}`, updates)

      // 如果更新的是当前用户，刷新用户信息
      if (userId === currentUser.value?.id) {
        currentUser.value = response.data
        localStorage.setItem('current_user', JSON.stringify(response.data))
      }

      return { success: true, message: '用户信息更新成功' }
    } catch (error: any) {
      console.error('Update user error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '更新用户信息失败'
      }
    }
  }

  /**
   * 修改密码
   */
  const changePassword = async (
    userId: string,
    oldPassword: string,
    newPassword: string
  ): Promise<{ success: boolean, message: string }> => {
    // 如果是管理员重置密码(oldPassword为空),使用reset API
    if (!oldPassword && isAdmin.value) {
      return resetUserPassword(userId, newPassword)
    }

    try {
      await api.post('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      return { success: true, message: '密码修改成功' }
    } catch (error: any) {
      console.error('Change password error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '修改密码失败'
      }
    }
  }

  /**
   * 重置用户密码（仅管理员）
   */
  const resetUserPassword = async (
    userId: string,
    newPassword: string
  ): Promise<{ success: boolean, message: string }> => {
    if (!isAdmin.value) {
      return { success: false, message: '权限不足' }
    }

    try {
      await api.post(`/api/auth/reset-password/${userId}`, null, {
        params: { new_password: newPassword }
      })
      return { success: true, message: '密码重置成功' }
    } catch (error: any) {
      console.error('Reset password error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '重置密码失败'
      }
    }
  }

  /**
   * 初始化认证状态（从localStorage恢复）
   */
  const initializeAuth = () => {
    try {
      // 恢复token
      const savedToken = localStorage.getItem('auth_token')
      if (savedToken) {
        authToken.value = savedToken
      }

      // 恢复用户信息
      const savedUser = localStorage.getItem('current_user')
      if (savedUser) {
        currentUser.value = JSON.parse(savedUser)
      }

      // 如果有token但没有用户信息，尝试获取
      if (savedToken && !currentUser.value) {
        fetchCurrentUser().catch(() => {
          // 如果获取失败，清除认证信息
          logout()
        })
      }
    } catch (error) {
      console.error('Initialize auth error:', error)
      // 初始化失败，清除所有认证信息
      logout()
    }
  }

  return {
    // 状态
    currentUser,
    authToken,
    isLoggedIn,
    isAdmin,
    isStudent,

    // 方法
    login,
    logout,
    registerUser,
    getAllUsers,
    deleteUser,
    updateUser,
    changePassword,
    resetUserPassword,
    initializeAuth,
    fetchCurrentUser
  }
})
