import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'
import { MarkdownView } from '../components/MarkdownView'

function MorningReport() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getMorningReport()
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
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">晨间报告</h1>
        <p className="text-gray-600 mt-2">{data.target_date}</p>
      </div>

      {/* 准备度评分 */}
      {readiness && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">今日准备度</h2>
          <div className="flex items-center mb-4">
            <span className="text-4xl font-bold text-blue-600">{readiness.score}</span>
            <span className="text-2xl text-gray-500 ml-2">/10</span>
          </div>
          <p className="text-lg font-medium text-gray-700 mb-4">{readiness.verdict}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {readiness.factors.map((f: any, i: number) => (
              <div key={i} className={`p-4 rounded-lg ${f.status === 'good' ? 'bg-green-50' : f.status === 'warning' ? 'bg-yellow-50' : 'bg-red-50'}`}>
                <p className="font-medium text-gray-800">{f.name}</p>
                <p className="text-gray-600">{f.value}</p>
                {f.change && <p className="text-sm text-gray-500">{f.change}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 睡眠摘要 */}
      {sleep && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">睡眠摘要</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{sleep.duration_hours ?? '-'}</p>
              <p className="text-gray-600">时长(小时)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{sleep.score ?? '-'}</p>
              <p className="text-gray-600">睡眠评分</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{sleep.deep_sleep_hours ?? '-'}</p>
              <p className="text-gray-600">深睡(小时)</p>
            </div>
          </div>
        </div>
      )}

      {/* 训练负荷 */}
      {load && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">训练负荷</h2>
          <div className="flex items-center mb-4">
            <div className={`px-4 py-2 rounded-full ${load.acwr_status === '最佳' || load.acwr_status === 'optimal' ? 'bg-green-100 text-green-800' : load.acwr_status === '偏高' || load.acwr_status === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
              <span className="font-bold">{load.acwr?.toFixed(2) ?? '-'}</span>
              <span className="ml-2">ACWR</span>
            </div>
            <span className="ml-4 text-gray-700">{load.acwr_status ?? '-'}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{load.acute_load?.toFixed(0) ?? '-'}</p>
              <p className="text-gray-600">急性负荷</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{load.chronic_load?.toFixed(0) ?? '-'}</p>
              <p className="text-gray-600">慢性负荷</p>
            </div>
          </div>
        </div>
      )}

      {/* AI 建议 */}
      {data.ai_morning_advice && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">AI 教练建议</h2>
          <MarkdownView content={data.ai_morning_advice} />
        </div>
      )}
    </div>
  )
}

export default MorningReport