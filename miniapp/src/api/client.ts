import Taro from '@tarojs/taro'

import { clearWechatSession, ensureWechatSession, getAccessToken } from './auth'

export const getApiBase = () => process.env.TARO_APP_API_BASE_URL || ''

const normalizeUrl = (base: string, path: string) => {
  if (!base) {
    return path
  }
  const trimmedBase = base.replace(/\/+$/, '')
  const trimmedPath = path.replace(/^\/+/, '')
  return `${trimmedBase}/${trimmedPath}`
}

export const apiClient = {
  get: async <T,>(path: string, params?: Record<string, unknown>): Promise<T> => {
    await ensureWechatSession()
    const token = getAccessToken()
    const response = await Taro.request<T>({
      url: normalizeUrl(getApiBase(), path),
      method: 'GET',
      data: params,
      header: token ? { Authorization: `Bearer ${token}` } : undefined,
      timeout: 15000,
    })
    if (response.statusCode === 401) {
      clearWechatSession()
      throw new Error('登录已失效，请重试')
    }
    if (response.statusCode >= 400) {
      const detail = (response.data as { detail?: string } | undefined)?.detail
      throw new Error(detail || '请求失败')
    }
    return response.data as T
  },
  post: async <T,>(path: string, data?: Record<string, unknown>): Promise<T> => {
    await ensureWechatSession()
    const token = getAccessToken()
    const response = await Taro.request<T>({
      url: normalizeUrl(getApiBase(), path),
      method: 'POST',
      data,
      header: token ? { Authorization: `Bearer ${token}` } : undefined,
      timeout: 15000,
    })
    if (response.statusCode === 401) {
      clearWechatSession()
      throw new Error('登录已失效，请重试')
    }
    if (response.statusCode >= 400) {
      const detail = (response.data as { detail?: string } | undefined)?.detail
      throw new Error(detail || '请求失败')
    }
    return response.data as T
  },
  put: async <T,>(path: string, data?: Record<string, unknown>): Promise<T> => {
    await ensureWechatSession()
    const token = getAccessToken()
    const response = await Taro.request<T>({
      url: normalizeUrl(getApiBase(), path),
      method: 'PUT',
      data,
      header: token ? { Authorization: `Bearer ${token}` } : undefined,
      timeout: 15000,
    })
    if (response.statusCode === 401) {
      clearWechatSession()
      throw new Error('登录已失效，请重试')
    }
    if (response.statusCode >= 400) {
      const detail = (response.data as { detail?: string } | undefined)?.detail
      throw new Error(detail || '请求失败')
    }
    return response.data as T
  },
}
