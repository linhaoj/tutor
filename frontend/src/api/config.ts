/**
 * API配置文件
 * 统一管理所有HTTP请求
 */
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// API基础URL
// 开发环境使用局域网IP，支持手机访问
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://10.2.118.25:8000'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加token
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一处理错误
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<{ detail: string }>) => {
    // 处理不同的错误状态码
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权 - 清除token并跳转到登录页
          localStorage.removeItem('auth_token')
          localStorage.removeItem('current_user')
          ElMessage.error('登录已过期，请重新登录')
          // 跳转到登录页（通过window.location避免循环导入）
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          break

        case 403:
          ElMessage.error('权限不足')
          break

        case 404:
          ElMessage.error(data?.detail || '资源不存在')
          break

        case 400:
          // 业务错误（如课时不足、数据重复等）
          ElMessage.warning(data?.detail || '请求参数错误')
          break

        case 500:
          ElMessage.error(data?.detail || '服务器错误，请稍后重试')
          break

        default:
          ElMessage.error(data?.detail || '请求失败')
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      // 其他错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default api
export { API_BASE_URL }
