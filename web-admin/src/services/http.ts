import axios from 'axios'
import { ElMessage } from 'element-plus'

import router from '@/router'
import { useAuthStore } from '@/stores/auth'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8867'

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string' ? detail : error.message || '请求失败'

    if (status === 401) {
      const auth = useAuthStore()
      auth.logout()
      router.push({ name: 'login' })
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  },
)
