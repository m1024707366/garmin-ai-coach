import { useEffect, useState } from 'react'
import { View, Text } from '@tarojs/components'

import Loading from '../../components/Loading'
import Error from '../../components/Error'
import MarkdownView from '../../components/MarkdownView'
import { getEveningReview } from '../../api/coach'
import type { EveningReviewResponse } from '../../types'

import './index.scss'

function EveningReview() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<EveningReviewResponse | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getEveningReview()
      setData(result)
    } catch {
      setError('获取晚间复盘失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchData} />
  if (!data) return <Error message='暂无数据' onRetry={fetchData} />

  const activities = data.today_activities
  const recovery = data.recovery_metrics

  return (
    <View className='page evening-review'>
      <View className='hero'>
        <Text className='title'>晚间复盘</Text>
        <Text className='subtitle'>{data.target_date}</Text>
      </View>

      {/* 今日活动列表 */}
      {activities.length > 0 ? (
        <View className='card'>
          <Text className='card-title'>今日活动</Text>
          {activities.map((act, i) => (
            <View key={i} className='activity-item'>
              <View className='activity-header'>
                <Text className='activity-type'>{act.type}</Text>
                {act.trimp != null ? (
                  <Text className='activity-trimp'>TRIMP {act.trimp.toFixed(0)}</Text>
                ) : null}
              </View>
              <View className='activity-stats'>
                {act.distance_km != null ? (
                  <View className='activity-stat'>
                    <Text className='activity-stat-value'>{act.distance_km.toFixed(1)}</Text>
                    <Text className='activity-stat-label'>km</Text>
                  </View>
                ) : null}
                {act.duration_min != null ? (
                  <View className='activity-stat'>
                    <Text className='activity-stat-value'>{act.duration_min.toFixed(0)}</Text>
                    <Text className='activity-stat-label'>分钟</Text>
                  </View>
                ) : null}
                {act.avg_pace ? (
                  <View className='activity-stat'>
                    <Text className='activity-stat-value'>{act.avg_pace}</Text>
                    <Text className='activity-stat-label'>配速</Text>
                  </View>
                ) : null}
                {act.avg_hr != null ? (
                  <View className='activity-stat'>
                    <Text className='activity-stat-value'>{act.avg_hr.toFixed(0)}</Text>
                    <Text className='activity-stat-label'>心率</Text>
                  </View>
                ) : null}
              </View>
            </View>
          ))}
        </View>
      ) : (
        <View className='card'>
          <Text className='card-title'>今日活动</Text>
          <Text className='empty-text'>今天没有记录到活动</Text>
        </View>
      )}

      {/* 恢复指标 */}
      {recovery ? (
        <View className='card'>
          <Text className='card-title'>恢复指标</Text>
          <View className='metric-row'>
            <View className='metric'>
              <Text className='metric-value'>{recovery.stress_avg ?? '-'}</Text>
              <Text className='metric-label'>压力均值</Text>
            </View>
            <View className='metric'>
              <Text className='metric-value'>{recovery.body_battery_end ?? '-'}</Text>
              <Text className='metric-label'>体能电量</Text>
            </View>
            <View className='metric'>
              <Text className='metric-value'>{recovery.resting_hr ?? '-'}</Text>
              <Text className='metric-label'>静息心率</Text>
            </View>
          </View>
        </View>
      ) : null}

      {/* AI 复盘 */}
      {data.ai_evening_review ? (
        <View className='card'>
          <Text className='card-title'>AI 教练复盘</Text>
          <MarkdownView content={data.ai_evening_review} />
        </View>
      ) : null}
    </View>
  )
}

export default EveningReview
