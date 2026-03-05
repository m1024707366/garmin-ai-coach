import { useEffect, useState } from 'react'
import { View, Text } from '@tarojs/components'

import Loading from '../../components/Loading'
import Error from '../../components/Error'
import MarkdownView from '../../components/MarkdownView'
import { getMorningReport } from '../../api/coach'
import type { MorningReportResponse } from '../../types'

import './index.scss'

function MorningReport() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<MorningReportResponse | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getMorningReport()
      setData(result)
    } catch {
      setError('获取晨间报告失败')
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

  const sleep = data.sleep_summary
  const load = data.training_load
  const readiness = data.readiness

  return (
    <View className='page morning-report'>
      <View className='hero'>
        <Text className='title'>晨间报告</Text>
        <Text className='subtitle'>{data.target_date}</Text>
      </View>

      {/* 准备度评分 */}
      {readiness ? (
        <View className='card'>
          <Text className='card-title'>今日准备度</Text>
          <View className='readiness-header'>
            <Text className='readiness-score'>{readiness.score}</Text>
            <Text className='readiness-max'>/10</Text>
          </View>
          <Text className='readiness-verdict'>{readiness.verdict}</Text>
          <View className='readiness-factors'>
            {readiness.factors.map((f, i) => (
              <View key={i} className={`factor factor-${f.status}`}>
                <Text className='factor-name'>{f.name}</Text>
                <Text className='factor-value'>{f.value}</Text>
                {f.change ? <Text className='factor-change'>{f.change}</Text> : null}
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {/* 睡眠摘要 */}
      {sleep ? (
        <View className='card'>
          <Text className='card-title'>睡眠摘要</Text>
          <View className='metric-row'>
            <View className='metric'>
              <Text className='metric-value'>{sleep.duration_hours ?? '-'}</Text>
              <Text className='metric-label'>时长(小时)</Text>
            </View>
            <View className='metric'>
              <Text className='metric-value'>{sleep.score ?? '-'}</Text>
              <Text className='metric-label'>睡眠评分</Text>
            </View>
            <View className='metric'>
              <Text className='metric-value'>{sleep.deep_sleep_hours ?? '-'}</Text>
              <Text className='metric-label'>深睡(小时)</Text>
            </View>
          </View>
        </View>
      ) : null}

      {/* 训练负荷 */}
      {load ? (
        <View className='card'>
          <Text className='card-title'>训练负荷</Text>
          <View className='acwr-badge-wrap'>
            <View className={`acwr-badge acwr-${load.acwr_status === '最佳' || load.acwr_status === 'optimal' ? 'optimal' : load.acwr_status === '偏高' || load.acwr_status === 'warning' ? 'warning' : 'danger'}`}>
              <Text className='acwr-value'>{load.acwr?.toFixed(2) ?? '-'}</Text>
              <Text className='acwr-label'>ACWR</Text>
            </View>
            <Text className='acwr-status'>{load.acwr_status ?? '-'}</Text>
          </View>
          <View className='metric-row'>
            <View className='metric'>
              <Text className='metric-value'>{load.acute_load?.toFixed(0) ?? '-'}</Text>
              <Text className='metric-label'>急性负荷</Text>
            </View>
            <View className='metric'>
              <Text className='metric-value'>{load.chronic_load?.toFixed(0) ?? '-'}</Text>
              <Text className='metric-label'>慢性负荷</Text>
            </View>
          </View>
        </View>
      ) : null}

      {/* AI 建议 */}
      {data.ai_morning_advice ? (
        <View className='card'>
          <Text className='card-title'>AI 教练建议</Text>
          <MarkdownView content={data.ai_morning_advice} />
        </View>
      ) : null}
    </View>
  )
}

export default MorningReport
