export type DailyAnalysisResponse = {
  date: string
  raw_data_summary: string
  ai_advice: string
  summary?: {
    sleep?: number | null
    battery?: number | null
    stress?: number | null
  }
  charts?: {
    labels: string[]
    paces: number[]
    heart_rates: number[]
    cadences: number[]
  }
}

// 准备度评分
export type ReadinessScore = {
  score: number
  verdict: string
  factors: Array<{
    name: string
    value: string | number
    status: 'green' | 'yellow' | 'red'
    change: string
  }>
}

export type HomeSummaryResponse = {
  latest_run: {
    start_time: string
    distance_km: number
    intensity?: string | null
    avg_pace?: string | null
    duration_min?: number | null
  } | null
  // 准备度评分
  readiness?: ReadinessScore | null
  week_stats: {
    distance_km: number
    avg_speed_kmh?: number | null
  } | null
  month_stats: {
    distance_km: number
    avg_speed_kmh?: number | null
  } | null
  ai_brief: {
    week?: string | null
    month?: string | null
  } | null
  updated_at?: string | null
}

export type PeriodAnalysisResponse = {
  period: string
  start_date: string
  end_date: string
  run_count: number
  total_distance_km: number
  avg_speed_kmh?: number | null
  sleep_days: number
  avg_sleep_hours?: number | null
  ai_analysis?: string | null
}

export type WechatLoginRequest = {
  code: string
}

export type WechatLoginResponse = {
  openid: string
  unionid?: string
  access_token: string
  token_type: string
  expires_in: number
}

export type WechatBindGarminRequest = {
  garmin_email: string
  garmin_password: string
  is_cn?: boolean
}

export type WechatBindGarminResponse = {
  bound: boolean
  backfill_started?: boolean
  backfill_days?: number
}

export type WechatUnbindGarminResponse = {
  bound: boolean
}

export type WechatProfileResponse = {
  openid: string
  has_binding: boolean
  garmin_email?: string
  is_cn?: boolean
}

export type WechatChatRequest = {
  message: string
}

export type WechatChatResponse = {
  reply: string
}

export type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string | null
}

export type ChatHistoryResponse = {
  messages: ChatMessage[]
}

// ==================== T4: 晨间报告 ====================
export type MorningReportResponse = {
  target_date: string
  sleep_summary: {
    duration_hours: number | null
    score: number | null
    deep_sleep_hours: number | null
  } | null
  training_load: {
    acwr: number | null
    acwr_status: string | null
    acute_load: number | null
    chronic_load: number | null
  } | null
  readiness: ReadinessScore | null
  ai_morning_advice: string
}

// ==================== T5: 晚间复盘 ====================
export type EveningReviewResponse = {
  target_date: string
  today_activities: Array<{
    type: string
    distance_km: number | null
    duration_min: number | null
    avg_hr: number | null
    avg_pace: string | null
    trimp: number | null
  }>
  recovery_metrics: {
    stress_avg: number | null
    body_battery_end: number | null
    resting_hr: number | null
  } | null
  ai_evening_review: string
}

// ==================== T6: 周度总结 ====================
export type WeeklySummaryResponse = {
  target_date: string
  week_start: string
  week_end: string
  weekly_stats: {
    total_distance_km: number
    run_count: number
    total_duration_min: number
    avg_pace: string | null
    avg_hr: number | null
  } | null
  load_trend: {
    acwr: number | null
    acwr_status: string | null
    weekly_trimp: number | null
  } | null
  confidence_score: {
    score: number
    label: string
    factors: Array<{
      name: string
      score: number
      detail: string
    }>
  } | null
  ai_weekly_summary: string
}

// ==================== T7: 伤病记录 ====================
export type InjuryLog = {
  id: number
  body_part: string
  injury_type: string | null
  severity: number
  description: string | null
  occurred_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type InjuryLogCreateRequest = {
  body_part: string
  injury_type?: string
  severity: number
  description?: string
  occurred_date?: string
}

export type InjuryLogUpdateRequest = {
  severity?: number
  description?: string
  is_active?: boolean
}

// ==================== T8: 教练记忆（运动员档案） ====================
export type CoachProfileResponse = {
  user_id: number
  max_hr: number | null
  rest_hr: number | null
  vo2max: number | null
  lthr: number | null
  ftp: number | null
  injury_history: string | null
  training_preference: string | null
  race_target: string | null
  race_date: string | null
  pb_5k_seconds: number | null
  pb_10k_seconds: number | null
  pb_half_seconds: number | null
  pb_full_seconds: number | null
  weekly_mileage_goal_km: number | null
  target_finish_time_seconds: number | null
  notes: string | null
}

export type CoachProfileUpdateRequest = {
  max_hr?: number
  rest_hr?: number
  vo2max?: number
  lthr?: number
  ftp?: number
  injury_history?: string
  training_preference?: string
  race_target?: string
  race_date?: string
  pb_5k_seconds?: number
  pb_10k_seconds?: number
  pb_half_seconds?: number
  pb_full_seconds?: number
  weekly_mileage_goal_km?: number
  target_finish_time_seconds?: number
  notes?: string
}
