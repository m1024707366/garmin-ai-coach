import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'

function InjuryLog() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [injuryLogs, setInjuryLogs] = useState<any[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [newInjury, setNewInjury] = useState({
    body_part: '',
    injury_type: '',
    severity: 5,
    description: '',
    occurred_date: new Date().toISOString().split('T')[0]
  })

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getInjuryLogs()
      setInjuryLogs(result)
    } catch {
      setError('获取伤病记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAddInjury = async () => {
    try {
      await coachApi.createInjuryLog(newInjury)
      setShowAddForm(false)
      setNewInjury({
        body_part: '',
        injury_type: '',
        severity: 5,
        description: '',
        occurred_date: new Date().toISOString().split('T')[0]
      })
      fetchData()
    } catch {
      alert('创建伤病记录失败')
    }
  }

  const handleUpdateInjury = async (id: number, updates: any) => {
    try {
      await coachApi.updateInjuryLog(id, updates)
      fetchData()
    } catch {
      alert('更新伤病记录失败')
    }
  }

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchData} />

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">伤病记录</h1>
        <p className="text-gray-600 mt-2">记录和管理你的伤病情况</p>
      </div>

      <div className="mb-6">
        <button 
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showAddForm ? '取消' : '添加伤病记录'}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">添加伤病记录</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2">身体部位</label>
              <input 
                type="text" 
                value={newInjury.body_part}
                onChange={(e) => setNewInjury({...newInjury, body_part: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">伤病类型</label>
              <input 
                type="text" 
                value={newInjury.injury_type}
                onChange={(e) => setNewInjury({...newInjury, injury_type: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">严重程度 (1-10)</label>
              <input 
                type="number" 
                min="1" 
                max="10" 
                value={newInjury.severity}
                onChange={(e) => setNewInjury({...newInjury, severity: parseInt(e.target.value)})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">描述</label>
              <textarea 
                value={newInjury.description}
                onChange={(e) => setNewInjury({...newInjury, description: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">发生日期</label>
              <input 
                type="date" 
                value={newInjury.occurred_date}
                onChange={(e) => setNewInjury({...newInjury, occurred_date: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <button 
              onClick={handleAddInjury}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              保存
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">伤病记录列表</h2>
        {injuryLogs.length > 0 ? (
          <div className="space-y-4">
            {injuryLogs.map((log) => (
              <div key={log.id} className="border-b border-gray-200 py-4 last:border-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-800">{log.body_part}</h3>
                    <p className="text-gray-600 text-sm">{log.injury_type}</p>
                    <p className="text-gray-600 text-sm mt-1">发生日期: {log.occurred_date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-800">严重程度: {log.severity}/10</p>
                    <p className={`text-sm ${log.is_active ? 'text-red-600' : 'text-green-600'}`}>
                      {log.is_active ? '活跃' : '已恢复'}
                    </p>
                  </div>
                </div>
                {log.description && (
                  <p className="text-gray-600 mt-2">{log.description}</p>
                )}
                <div className="mt-4 flex space-x-2">
                  <button 
                    onClick={() => handleUpdateInjury(log.id, { is_active: !log.is_active })}
                    className={`px-3 py-1 rounded-lg text-sm ${log.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                  >
                    {log.is_active ? '标记为已恢复' : '标记为活跃'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">暂无伤病记录</p>
        )}
      </div>
    </div>
  )
}

export default InjuryLog