import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'
import { MarkdownView } from '../components/MarkdownView'

function EveningReview() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getEveningReview()
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
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">晚间复盘</h1>
        <p className="text-gray-600 mt-2">{data.target_date}</p>
      </div>

      {/* 今日活动列表 */}
      {activities && activities.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">今日活动</h2>
          {activities.map((act: any, i: number) => (
            <div key={i} className="border-b border-gray-200 py-4 last:border-0">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-800">{act.type}</span>
                {act.trimp != null && (
                  <span className="text-sm text-gray-600">TRIMP {act.trimp.toFixed(0)}</span>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {act.distance_km != null && (
                  <div className="text-center">
                    <span className="font-bold text-gray-800">{act.distance_km.toFixed(1)}</span>
                    <span className="text-gray-600 ml-1">km</span>
                  </div>
                )}
                {act.duration_min != null && (
                  <div className="text-center">
                    <span className="font-bold text-gray-800">{act.duration_min.toFixed(0)}</span>
                    <span className="text-gray-600 ml-1">分钟</span>
                  </div>
                )}
                {act.avg_pace && (
                  <div className="text-center">
                    <span className="font-bold text-gray-800">{act.avg_pace}</span>
                    <span className="text-gray-600 ml-1">配速</span>
                  </div>
                )}
                {act.avg_hr != null && (
                  <div className="text-center">
                    <span className="font-bold text-gray-800">{act.avg_hr.toFixed(0)}</span>
                    <span className="text-gray-600 ml-1">心率</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">今日活动</h2>
          <p className="text-gray-600">今天没有记录到活动</p>
        </div>
      )}

      {/* 恢复指标 */}
      {recovery && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">恢复指标</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{recovery.stress_avg ?? '-'}</p>
              <p className="text-gray-600">压力均值</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{recovery.body_battery_end ?? '-'}</p>
              <p className="text-gray-600">体能电量</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{recovery.resting_hr ?? '-'}</p>
              <p className="text-gray-600">静息心率</p>
            </div>
          </div>
        </div>
      )}

      {/* AI 复盘 */}
      {data.ai_evening_review && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">AI 教练复盘</h2>
          <MarkdownView content={data.ai_evening_review} />
        </div>
      )}
    </div>
  )
}

export default EveningReview