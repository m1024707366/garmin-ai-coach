import { useEffect, useState } from 'react'
import { View, Text } from '@tarojs/components'

import Loading from '../../components/Loading'
import Error from '../../components/Error'
import MarkdownView from '../../components/MarkdownView'
import { getWeeklySummary } from '../../api/coach'
import type { WeeklySummaryResponse } from '../../types'

import './index.scss'

function WeeklySummary() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<WeeklySummaryResponse | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getWeeklySummary()
      setData(result)
    } catch {
      setError('获取周度总结失败')
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

  const stats = data.weekly_stats
  const load = data.load_trend
  const confidence = data.confidence_score

  const getAcwrClass = (status: string | null | undefined): string => {
    if (!status) return 'optimal'
    if (status === '最佳' || status === 'optimal') return 'optimal'
    if (status === '偏高' || status === 'warning') return 'warning'
    return 'danger'
  }

  return (
    <View className='page weekly-summary'>
      <View className='hero'>
        <Text className='title'>周度总结</Text>
        <Text className='subtitle'>{data.week_start} ~ {data.week_end}</Text>
      </View>

      {/* 周跑步统计 */}
      {stats ? (
        <View className='card'>
          <Text className='card-title'>本周跑步</Text>
          <View className='stats-grid'>
            <View className='stat-item'>
              <Text className='stat-big'>{stats.total_distance_km.toFixed(1)}</Text>
              <Text className='stat-label'>总跑量(km)</Text>
            </View>
            <View className='stat-item'>
              <Text className='stat-big'>{stats.run_count}</Text>
              <Text className='stat-label'>跑步次数</Text>
            </View>
            <View className='stat-item'>
              <Text className='stat-big'>{stats.total_duration_min.toFixed(0)}</Text>
              <Text className='stat-label'>总时长(分钟)</Text>
            </View>
            <View className='stat-item'>
              <Text className='stat-big'>{stats.avg_pace ?? '-'}</Text>
              <Text className='stat-label'>平均配速</Text>
            </View>
            <View className='stat-item'>
              <Text className='stat-big'>{stats.avg_hr?.toFixed(0) ?? '-'}</Text>
              <Text className='stat-label'>平均心率</Text>
            </View>
          </View>
        </View>
      ) : null}

      {/* 负荷趋势 */}
      {load ? (
        <View className='card'>
          <Text className='card-title'>负荷趋势</Text>
          <View className='load-row'>
            <View className={`acwr-badge acwr-${getAcwrClass(load.acwr_status)}`}>
              <Text className='acwr-value'>{load.acwr?.toFixed(2) ?? '-'}</Text>
              <Text className='acwr-label'>ACWR</Text>
            </View>
            <View className='load-info'>
              <Text className='load-status'>{load.acwr_status ?? '-'}</Text>
              {load.weekly_trimp != null ? (
                <Text className='load-trimp'>周 TRIMP: {load.weekly_trimp.toFixed(0)}</Text>
              ) : null}
            </View>
          </View>
        </View>
      ) : null}

      {/* 比赛信心评分 */}
      {confidence ? (
        <View className='card'>
          <Text className='card-title'>比赛信心评分</Text>
          <View className='confidence-header'>
            <Text className='confidence-score'>{confidence.score}</Text>
            <Text className='confidence-max'>/100</Text>
            <Text className='confidence-label'>{confidence.label}</Text>
          </View>
          <View className='confidence-factors'>
            {confidence.factors.map((f, i) => (
              <View key={i} className='confidence-factor'>
                <View className='confidence-factor-header'>
                  <Text className='confidence-factor-name'>{f.name}</Text>
                  <Text className='confidence-factor-score'>{f.score}</Text>
                </View>
                <Text className='confidence-factor-detail'>{f.detail}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {/* AI 周报 */}
      {data.ai_weekly_summary ? (
        <View className='card'>
          <Text className='card-title'>AI 教练周报</Text>
          <MarkdownView content={data.ai_weekly_summary} />
        </View>
      ) : null}
    </View>
  )
}

export default WeeklySummary
