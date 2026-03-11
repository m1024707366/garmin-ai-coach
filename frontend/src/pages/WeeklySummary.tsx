import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'
import { MarkdownView } from '../components/MarkdownView'

function WeeklySummary() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getWeeklySummary()
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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">周度总结</h1>
        <p className="text-gray-600 mt-2">{data.target_date}</p>
      </div>

      {/* 周度统计 */}
      {data.week_stats && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">周度统计</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{data.week_stats.run_count ?? '-'}</p>
              <p className="text-gray-600">跑步次数</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{data.week_stats.distance_km ?? '-'}</p>
              <p className="text-gray-600">总跑量(km)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{data.week_stats.avg_speed_kmh ?? '-'}</p>
              <p className="text-gray-600">平均速度(km/h)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{data.week_stats.avg_sleep_hours ?? '-'}</p>
              <p className="text-gray-600">平均睡眠(小时)</p>
            </div>
          </div>
        </div>
      )}

      {/* 训练负荷 */}
      {data.training_load && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">训练负荷</h2>
          <div className="flex items-center mb-4">
            <div className={`px-4 py-2 rounded-full ${data.training_load.acwr_status === '最佳' || data.training_load.acwr_status === 'optimal' ? 'bg-green-100 text-green-800' : data.training_load.acwr_status === '偏高' || data.training_load.acwr_status === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
              <span className="font-bold">{data.training_load.acwr?.toFixed(2) ?? '-'}</span>
              <span className="ml-2">ACWR</span>
            </div>
            <span className="ml-4 text-gray-700">{data.training_load.acwr_status ?? '-'}</span>
          </div>
        </div>
      )}

      {/* 睡眠趋势 */}
      {data.sleep_trend && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">睡眠趋势</h2>
          <div className="space-y-2">
            {data.sleep_trend.map((day: any, i: number) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-gray-700">{day.date}</span>
                <span className="font-medium text-gray-800">{day.duration_hours ?? '-'} 小时</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI 周度总结 */}
      {data.ai_weekly_summary && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">AI 周度总结</h2>
          <MarkdownView content={data.ai_weekly_summary} />
        </div>
      )}

      {/* 下周建议 */}
      {data.ai_next_week_advice && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">下周建议</h2>
          <MarkdownView content={data.ai_next_week_advice} />
        </div>
      )}
    </div>
  )
}

export default WeeklySummary