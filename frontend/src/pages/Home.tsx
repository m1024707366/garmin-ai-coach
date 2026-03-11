import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'
import StatCard from '../components/StatCard'


export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [homeSummary, setHomeSummary] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)
  const [garminEmail, setGarminEmail] = useState('')
  const [garminPassword, setGarminPassword] = useState('')
  const [isCn, setIsCn] = useState(true)
  const [showPeriodModal, setShowPeriodModal] = useState(false)
  const [periodAnalysis, setPeriodAnalysis] = useState<any>(null)
  const [periodLoading, setPeriodLoading] = useState(false)
  const [activePeriod, setActivePeriod] = useState<'week' | 'month'>('week')
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    const [profileResult, summaryResult] = await Promise.allSettled([
      coachApi.getProfile(),
      coachApi.getHomeSummary(),
    ])

    if (profileResult.status === 'fulfilled') {
      setProfile(profileResult.value)
    } else {
      setProfile(null)
    }

    if (summaryResult.status === 'fulfilled') {
      setHomeSummary(summaryResult.value)
    } else {
      setHomeSummary(null)
    }

    if (profileResult.status === 'rejected' || summaryResult.status === 'rejected') {
      setError('获取数据失败')
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleBind = async () => {
    try {
      await coachApi.bindGarmin({
        garmin_email: garminEmail,
        garmin_password: garminPassword,
        is_cn: isCn,
      })
      alert('已提交绑定')
      fetchData()
    } catch (err) {
      alert('绑定失败')
    }
  }

  const handleUnbind = async () => {
    try {
      await coachApi.unbindGarmin()
      alert('已解绑')
      fetchData()
    } catch (err) {
      alert('解绑失败')
    }
  }

  const handleLatestRunClick = () => {
    if (homeSummary?.latest_run?.start_time) {
      const date = homeSummary.latest_run.start_time.split('T')[0]
      navigate(`/analysis/${date}`)
    }
  }

  const handlePeriodStatsClick = async (period: 'week' | 'month') => {
    setActivePeriod(period)
    setPeriodAnalysis(null)
    setShowPeriodModal(true)
    setPeriodLoading(true)
    try {
      const data = await coachApi.getPeriodAnalysis(period)
      setPeriodAnalysis(data)
    } catch (err) {
      alert('获取分析失败')
    } finally {
      setPeriodLoading(false)
    }
  }

  if (loading) {
    return <Loading />
  }

  if (error) {
    return <Error message={error} onRetry={fetchData} />
  }

  const isBound = profile?.has_binding
  const latestRun = homeSummary?.latest_run
  const readiness = homeSummary?.readiness
  const weekStats = homeSummary?.week_stats
  const monthStats = homeSummary?.month_stats
  const aiBrief = homeSummary?.ai_brief

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-orange-50 to-amber-100 p-6 sm:p-8">
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            训练助手
          </h1>
          <p className="mt-2 text-lg text-slate-700">
            今日概览与智能建议
          </p>
        </div>
        <div className="absolute inset-0 -z-10 opacity-20">
          <div className="absolute top-0 left-0 h-40 w-40 rounded-full bg-orange-300 blur-3xl"></div>
          <div className="absolute bottom-0 right-0 h-64 w-64 rounded-full bg-amber-300 blur-3xl"></div>
        </div>
      </div>

      {/* 最近一次跑步 */}
      {latestRun && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">最近一次跑步</h2>
          <div 
            className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={handleLatestRunClick}
          >
            <div className="flex justify-between items-center mb-4">
              <p className="text-gray-700">
                {latestRun.start_time ? latestRun.start_time.replace('T', ' ').slice(0, 16) : '-'}
              </p>
              <p className="text-gray-700">{latestRun.intensity || '-'}</p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-800">{String(latestRun.distance_km)}</p>
                <p className="text-gray-600">km</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-800">{latestRun.avg_pace || '-'}</p>
                <p className="text-gray-600">配速</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-800">{latestRun.duration_min || '-'}</p>
                <p className="text-gray-600">分钟</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 准备度评分卡片 */}
      {readiness && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">今日准备度</h2>
          <div className="flex items-center mb-4">
            <span className="text-4xl font-bold text-blue-600">{readiness.score}</span>
            <span className="text-2xl text-gray-500 ml-2">/10</span>
          </div>
          <p className="text-lg font-medium text-gray-700 mb-4">{readiness.verdict}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {readiness.factors.map((factor: any, idx: number) => (
              <div key={idx} className={`p-4 rounded-lg ${factor.status === 'good' ? 'bg-green-50' : factor.status === 'warning' ? 'bg-yellow-50' : 'bg-red-50'}`}>
                <p className="font-medium text-gray-800">{factor.name}</p>
                <p className="text-gray-600">{factor.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 周/月统计 */}
      {(weekStats || monthStats) && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">周/月统计（点击查看分析）</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {weekStats && (
              <StatCard
                title="本周跑量"
                value={String(weekStats.distance_km)}
                unit="km"
                onClick={() => handlePeriodStatsClick('week')}
              />
            )}
            {weekStats && (
              <StatCard
                title="本周均速"
                value={weekStats.avg_speed_kmh ? String(weekStats.avg_speed_kmh) : '-'}
                unit="km/h"
                onClick={() => handlePeriodStatsClick('week')}
              />
            )}
            {monthStats && (
              <StatCard
                title="本月跑量"
                value={String(monthStats.distance_km)}
                unit="km"
                onClick={() => handlePeriodStatsClick('month')}
              />
            )}
            {monthStats && (
              <StatCard
                title="本月均速"
                value={monthStats.avg_speed_kmh ? String(monthStats.avg_speed_kmh) : '-'}
                unit="km/h"
                onClick={() => handlePeriodStatsClick('month')}
              />
            )}
          </div>
        </div>
      )}

      {/* 教练简评 */}
      {(aiBrief?.week || aiBrief?.month) && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">教练简评</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiBrief?.week && (
              <StatCard title="本周" value={aiBrief.week} />
            )}
            {aiBrief?.month && (
              <StatCard title="本月" value={aiBrief.month} />
            )}
          </div>
        </div>
      )}

      {/* 教练功能入口 */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">教练功能</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { emoji: '🌅', title: '晨间报告', url: '/morning-report' },
            { emoji: '🌙', title: '晚间复盘', url: '/evening-review' },
            { emoji: '📊', title: '周度总结', url: '/weekly-summary' },
            { emoji: '💬', title: 'AI 对话', url: '/chat' },
            { emoji: '🩹', title: '伤病记录', url: '/injury-log' },
            { emoji: '🏃', title: '运动员档案', url: '/profile' },
          ].map((item) => (
            <div
              key={item.title}
              className="border rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(item.url)}
            >
              <p className="text-3xl mb-2">{item.emoji}</p>
              <p className="font-medium text-gray-800">{item.title}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Garmin 绑定 */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {isBound ? (
          <div>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Garmin 已绑定</h2>
            <p className="text-gray-600 mb-4">如需更换账号，请先解绑再重新绑定</p>
            <button
              onClick={handleUnbind}
              className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 transition-colors"
            >
              解绑/重新绑定
            </button>
          </div>
        ) : (
          <div>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">绑定 Garmin 账号</h2>
            <p className="text-gray-600 mb-4">绑定后可同步睡眠，体能电量与压力数据</p>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Garmin 邮箱"
                value={garminEmail}
                onChange={(e) => setGarminEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <input
                type="password"
                placeholder="Garmin 密码"
                value={garminPassword}
                onChange={(e) => setGarminPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={isCn}
                  onChange={(e) => setIsCn(e.target.checked)}
                  className="mr-2"
                />
                <label className="text-gray-700">中国区账号</label>
              </div>
              <button
                onClick={handleBind}
                className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 transition-colors"
              >
                立即绑定
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 周期分析模态框 */}
      {showPeriodModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">
              {activePeriod === 'week' ? '本周' : '本月'}分析
            </h3>
            {periodLoading ? (
              <Loading />
            ) : periodAnalysis ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <p className="text-gray-700">跑步次数：{periodAnalysis.run_count} 次</p>
                  <p className="text-gray-700">总跑量：{periodAnalysis.total_distance_km} km</p>
                  <p className="text-gray-700">平均速度：{periodAnalysis.avg_speed_kmh || '-'} km/h</p>
                  <p className="text-gray-700">睡眠天数：{periodAnalysis.sleep_days} 天</p>
                  <p className="text-gray-700">平均睡眠：{periodAnalysis.avg_sleep_hours || '-'} 小时</p>
                </div>
                {periodAnalysis.ai_analysis && (
                  <div>
                    <p className="font-medium text-gray-800 mb-2">AI 分析：</p>
                    <p className="text-gray-700">{periodAnalysis.ai_analysis}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-600">加载失败</p>
            )}
            <button 
              onClick={() => setShowPeriodModal(false)}
              className="mt-4 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  )
}