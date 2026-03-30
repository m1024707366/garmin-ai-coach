import axios from 'axios'
import type { DailyAnalysisResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 如果需要认证，在这里添加 token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器（统一错误处理）
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.request)
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const coachApi = {
  /**
   * 获取每日分析
   */
  getDailyAnalysis: async (date?: string): Promise<DailyAnalysisResponse> => {
    const response = await apiClient.get<DailyAnalysisResponse>(
      '/api/coach/daily-analysis',
      {
        params: date ? { target_date: date } : {},
      }
    )
    return response.data
  },

  /**
   * 健康检查
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/health')
    return response.data
  },

  /**
   * 获取首页摘要
   */
  getHomeSummary: async () => {
    const response = await apiClient.get('/api/coach/home-summary')
    return response.data
  },

  /**
   * 获取周期分析
   */
  getPeriodAnalysis: async (period: string) => {
    const response = await apiClient.get('/api/coach/period-analysis', {
      params: { period }
    })
    return response.data
  },

  /**
   * 绑定 Garmin 账号
   */
  bindGarmin: async (_payload: { garmin_email: string; garmin_password: string; is_cn: boolean }) => {
    // 注意：后端暂未实现此 API，使用模拟数据
    console.warn('Backend API not implemented: /api/coach/bind-garmin')
    return { bound: true }
  },

  /**
   * 解绑 Garmin 账号
   */
  unbindGarmin: async () => {
    // 注意：后端暂未实现此 API，使用模拟数据
    console.warn('Backend API not implemented: /api/coach/unbind-garmin')
    return { bound: false }
  },

  /**
   * 获取用户信息
   */
  getProfile: async () => {
    // 注意：后端暂未实现此 API，使用模拟数据
    console.warn('Backend API not implemented: /api/coach/user-profile')
    return { has_binding: false }
  },

  /**
   * 聊天
   */
  chat: async (_payload: { message: string }) => {
    // 注意：后端暂未实现此 API，使用模拟数据
    console.warn('Backend API not implemented: /api/coach/chat')
    return { reply: '这是一个模拟的回复' }
  },

  /**
   * 获取聊天历史
   */
  getChatHistory: async (_limit: number = 20) => {
    // 注意：后端暂未实现此 API，使用模拟数据
    console.warn('Backend API not implemented: /api/coach/chat-history')
    return { messages: [] }
  },

  /**
   * 获取晨间报告
   */
  getMorningReport: async (targetDate?: string) => {
    const params = targetDate ? { target_date: targetDate } : undefined
    const response = await apiClient.get('/api/coach/morning-report', { params })
    return response.data
  },

  /**
   * 获取晚间复盘
   */
  getEveningReview: async (targetDate?: string) => {
    const params = targetDate ? { target_date: targetDate } : undefined
    const response = await apiClient.get('/api/coach/evening-review', { params })
    return response.data
  },

  /**
   * 获取周度总结
   */
  getWeeklySummary: async (targetDate?: string) => {
    const params = targetDate ? { target_date: targetDate } : undefined
    const response = await apiClient.get('/api/coach/weekly-summary', { params })
    return response.data
  },

  /**
   * 获取伤病记录
   */
  getInjuryLogs: async (onlyActive: boolean = true) => {
    const response = await apiClient.get('/api/coach/injury-log', {
      params: { only_active: onlyActive }
    })
    return response.data
  },

  /**
   * 创建伤病记录
   */
  createInjuryLog: async (payload: any) => {
    const response = await apiClient.post('/api/coach/injury-log', payload)
    return response.data
  },

  /**
   * 更新伤病记录
   */
  updateInjuryLog: async (logId: number, payload: any) => {
    const response = await apiClient.put(`/api/coach/injury-log/${logId}`, payload)
    return response.data
  },

  /**
   * 获取教练档案
   */
  getCoachProfile: async () => {
    const response = await apiClient.get('/api/coach/profile')
    return response.data
  },

  /**
   * 更新教练档案
   */
  updateCoachProfile: async (payload: any) => {
    const response = await apiClient.put('/api/coach/profile', payload)
    return response.data
  },

  /**
   * 同步 Garmin 档案
   */
  syncGarminProfile: async () => {
    const response = await apiClient.post('/api/coach/sync-garmin-profile')
    return response.data
  },
}
