import { useEffect, useState } from 'react'
import { View, Text, Input, Button, Textarea } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Loading from '../../components/Loading'
import Error from '../../components/Error'
import { getCoachProfile, updateCoachProfile } from '../../api/coach'
import type { CoachProfileResponse } from '../../types'

import './index.scss'

// 秒数转 mm:ss 显示
const secondsToDisplay = (seconds: number | null): string => {
  if (seconds == null) return ''
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

// mm:ss 转秒数
const displayToSeconds = (val: string): number | undefined => {
  if (!val) return undefined
  const parts = val.split(':')
  if (parts.length === 2) {
    return Number(parts[0]) * 60 + Number(parts[1])
  }
  return Number(val) || undefined
}

type FormData = {
  max_hr: string
  rest_hr: string
  vo2max: string
  lthr: string
  ftp: string
  race_target: string
  race_date: string
  pb_5k: string
  pb_10k: string
  pb_half: string
  pb_full: string
  weekly_mileage_goal_km: string
  target_finish_time: string
  training_preference: string
  injury_history: string
  notes: string
}

function Profile() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<FormData>({
    max_hr: '', rest_hr: '', vo2max: '', lthr: '', ftp: '',
    race_target: '', race_date: '',
    pb_5k: '', pb_10k: '', pb_half: '', pb_full: '',
    weekly_mileage_goal_km: '', target_finish_time: '',
    training_preference: '', injury_history: '', notes: '',
  })

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data: CoachProfileResponse = await getCoachProfile()
      setForm({
        max_hr: data.max_hr?.toString() ?? '',
        rest_hr: data.rest_hr?.toString() ?? '',
        vo2max: data.vo2max?.toString() ?? '',
        lthr: data.lthr?.toString() ?? '',
        ftp: data.ftp?.toString() ?? '',
        race_target: data.race_target ?? '',
        race_date: data.race_date ?? '',
        pb_5k: secondsToDisplay(data.pb_5k_seconds),
        pb_10k: secondsToDisplay(data.pb_10k_seconds),
        pb_half: secondsToDisplay(data.pb_half_seconds),
        pb_full: secondsToDisplay(data.pb_full_seconds),
        weekly_mileage_goal_km: data.weekly_mileage_goal_km?.toString() ?? '',
        target_finish_time: secondsToDisplay(data.target_finish_time_seconds),
        training_preference: data.training_preference ?? '',
        injury_history: data.injury_history ?? '',
        notes: data.notes ?? '',
      })
    } catch {
      setError('获取档案失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateCoachProfile({
        max_hr: form.max_hr ? Number(form.max_hr) : undefined,
        rest_hr: form.rest_hr ? Number(form.rest_hr) : undefined,
        vo2max: form.vo2max ? Number(form.vo2max) : undefined,
        lthr: form.lthr ? Number(form.lthr) : undefined,
        ftp: form.ftp ? Number(form.ftp) : undefined,
        race_target: form.race_target || undefined,
        race_date: form.race_date || undefined,
        pb_5k_seconds: displayToSeconds(form.pb_5k),
        pb_10k_seconds: displayToSeconds(form.pb_10k),
        pb_half_seconds: displayToSeconds(form.pb_half),
        pb_full_seconds: displayToSeconds(form.pb_full),
        weekly_mileage_goal_km: form.weekly_mileage_goal_km ? Number(form.weekly_mileage_goal_km) : undefined,
        target_finish_time_seconds: displayToSeconds(form.target_finish_time),
        training_preference: form.training_preference || undefined,
        injury_history: form.injury_history || undefined,
        notes: form.notes || undefined,
      })
      Taro.showToast({ title: '已保存', icon: 'success' })
    } catch {
      Taro.showToast({ title: '保存失败', icon: 'none' })
    } finally {
      setSaving(false)
    }
  }

  const updateField = (key: keyof FormData, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchData} />

  return (
    <View className='page profile'>
      <View className='hero'>
        <Text className='title'>运动员档案</Text>
        <Text className='subtitle'>AI 教练根据档案给出更精准的建议</Text>
      </View>

      {/* 生理指标 */}
      <View className='card'>
        <Text className='card-title'>生理指标</Text>
        <View className='form-row'>
          <Text className='form-label'>最大心率</Text>
          <Input className='form-input' type='number' placeholder='如 190'
            value={form.max_hr} onInput={(e) => updateField('max_hr', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>静息心率</Text>
          <Input className='form-input' type='number' placeholder='如 55'
            value={form.rest_hr} onInput={(e) => updateField('rest_hr', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>VO2max</Text>
          <Input className='form-input' type='digit' placeholder='如 50.5'
            value={form.vo2max} onInput={(e) => updateField('vo2max', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>乳酸阈心率</Text>
          <Input className='form-input' type='number' placeholder='如 165'
            value={form.lthr} onInput={(e) => updateField('lthr', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>FTP</Text>
          <Input className='form-input' type='number' placeholder='如 250'
            value={form.ftp} onInput={(e) => updateField('ftp', e.detail.value)} />
        </View>
      </View>

      {/* PB 记录 */}
      <View className='card'>
        <Text className='card-title'>个人最佳 (PB)</Text>
        <View className='form-row'>
          <Text className='form-label'>5K</Text>
          <Input className='form-input' placeholder='mm:ss 如 22:30'
            value={form.pb_5k} onInput={(e) => updateField('pb_5k', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>10K</Text>
          <Input className='form-input' placeholder='mm:ss 如 48:00'
            value={form.pb_10k} onInput={(e) => updateField('pb_10k', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>半马</Text>
          <Input className='form-input' placeholder='mm:ss 如 105:00'
            value={form.pb_half} onInput={(e) => updateField('pb_half', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>全马</Text>
          <Input className='form-input' placeholder='mm:ss 如 225:00'
            value={form.pb_full} onInput={(e) => updateField('pb_full', e.detail.value)} />
        </View>
      </View>

      {/* 比赛目标 */}
      <View className='card'>
        <Text className='card-title'>比赛目标</Text>
        <View className='form-row'>
          <Text className='form-label'>目标赛事</Text>
          <Input className='form-input' placeholder='如 2026 上海马拉松'
            value={form.race_target} onInput={(e) => updateField('race_target', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>比赛日期</Text>
          <Input className='form-input' placeholder='YYYY-MM-DD'
            value={form.race_date} onInput={(e) => updateField('race_date', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>目标成绩</Text>
          <Input className='form-input' placeholder='mm:ss 如 210:00'
            value={form.target_finish_time} onInput={(e) => updateField('target_finish_time', e.detail.value)} />
        </View>
        <View className='form-row'>
          <Text className='form-label'>周目标跑量(km)</Text>
          <Input className='form-input' type='digit' placeholder='如 50'
            value={form.weekly_mileage_goal_km} onInput={(e) => updateField('weekly_mileage_goal_km', e.detail.value)} />
        </View>
      </View>

      {/* 训练偏好 */}
      <View className='card'>
        <Text className='card-title'>其他信息</Text>
        <View className='form-col'>
          <Text className='form-label'>训练偏好</Text>
          <Textarea className='form-textarea' placeholder='如 喜欢晨跑，偏好间歇训练'
            value={form.training_preference} onInput={(e) => updateField('training_preference', e.detail.value)} />
        </View>
        <View className='form-col'>
          <Text className='form-label'>伤病史</Text>
          <Textarea className='form-textarea' placeholder='如 2024年膝盖半月板损伤'
            value={form.injury_history} onInput={(e) => updateField('injury_history', e.detail.value)} />
        </View>
        <View className='form-col'>
          <Text className='form-label'>备注</Text>
          <Textarea className='form-textarea' placeholder='其他需要教练了解的信息'
            value={form.notes} onInput={(e) => updateField('notes', e.detail.value)} />
        </View>
      </View>

      <Button className='save-btn' onClick={handleSave} disabled={saving}>
        {saving ? '保存中...' : '保存档案'}
      </Button>
    </View>
  )
}

export default Profile
