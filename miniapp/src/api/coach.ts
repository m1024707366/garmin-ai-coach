import { apiClient } from './client'
import type {
  ChatHistoryResponse,
  CoachProfileResponse,
  CoachProfileUpdateRequest,
  DailyAnalysisResponse,
  EveningReviewResponse,
  HomeSummaryResponse,
  InjuryLog,
  InjuryLogCreateRequest,
  InjuryLogUpdateRequest,
  MorningReportResponse,
  PeriodAnalysisResponse,
  WechatBindGarminRequest,
  WechatBindGarminResponse,
  WechatChatRequest,
  WechatChatResponse,
  WechatProfileResponse,
  WechatUnbindGarminResponse,
  WeeklySummaryResponse,
} from '../types'

export const getDailyAnalysis = async () => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis')
}

export const getDailyAnalysisByDate = async (date: string) => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis', { target_date: date })
}

export const getHomeSummary = async () => {
  return apiClient.get<HomeSummaryResponse>('/api/coach/home-summary')
}

export const getPeriodAnalysis = async (period: string) => {
  return apiClient.get<PeriodAnalysisResponse>('/api/coach/period-analysis', { period })
}

export const bindGarmin = async (payload: WechatBindGarminRequest) => {
  return apiClient.post<WechatBindGarminResponse>('/api/wechat/bind-garmin', payload)
}

export const unbindGarmin = async () => {
  return apiClient.post<WechatUnbindGarminResponse>('/api/wechat/unbind-garmin')
}

export const getProfile = async () => {
  return apiClient.get<WechatProfileResponse>('/api/wechat/profile')
}

export const chat = async (payload: WechatChatRequest) => {
  return apiClient.post<WechatChatResponse>('/api/wechat/chat', payload)
}

export const getChatHistory = async (limit: number = 20) => {
  return apiClient.get<ChatHistoryResponse>('/api/wechat/chat/history', { limit })
}

// ==================== T4: 晨间报告 ====================
export const getMorningReport = async (targetDate?: string) => {
  const params = targetDate ? { target_date: targetDate } : undefined
  return apiClient.get<MorningReportResponse>('/api/coach/morning-report', params)
}

// ==================== T5: 晚间复盘 ====================
export const getEveningReview = async (targetDate?: string) => {
  const params = targetDate ? { target_date: targetDate } : undefined
  return apiClient.get<EveningReviewResponse>('/api/coach/evening-review', params)
}

// ==================== T6: 周度总结 ====================
export const getWeeklySummary = async (targetDate?: string) => {
  const params = targetDate ? { target_date: targetDate } : undefined
  return apiClient.get<WeeklySummaryResponse>('/api/coach/weekly-summary', params)
}

// ==================== T7: 伤病记录 ====================
export const getInjuryLogs = async (onlyActive = true) => {
  return apiClient.get<InjuryLog[]>('/api/coach/injury-log', { only_active: onlyActive })
}

export const createInjuryLog = async (payload: InjuryLogCreateRequest) => {
  return apiClient.post<InjuryLog>('/api/coach/injury-log', payload as unknown as Record<string, unknown>)
}

export const updateInjuryLog = async (logId: number, payload: InjuryLogUpdateRequest) => {
  return apiClient.put<InjuryLog>(`/api/coach/injury-log/${logId}`, payload as unknown as Record<string, unknown>)
}

// ==================== T8: 教练档案 ====================
export const getCoachProfile = async () => {
  return apiClient.get<CoachProfileResponse>('/api/coach/profile')
}

export const updateCoachProfile = async (payload: CoachProfileUpdateRequest) => {
  return apiClient.put<CoachProfileResponse>('/api/coach/profile', payload as unknown as Record<string, unknown>)
}
