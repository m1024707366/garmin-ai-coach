import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'

function Profile() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<any>(null)
  const [showEditForm, setShowEditForm] = useState(false)
  const [editProfile, setEditProfile] = useState<any>({})

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getCoachProfile()
      setProfile(result)
      setEditProfile(result)
    } catch {
      setError('获取运动员档案失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleUpdateProfile = async () => {
    try {
      await coachApi.updateCoachProfile(editProfile)
      setShowEditForm(false)
      fetchData()
    } catch {
      alert('更新运动员档案失败')
    }
  }

  const handleSyncGarmin = async () => {
    try {
      await coachApi.syncGarminProfile()
      alert('同步成功')
      fetchData()
    } catch {
      alert('同步失败')
    }
  }

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchData} />
  if (!profile) return <Error message='暂无数据' onRetry={fetchData} />

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">运动员档案</h1>
        <p className="text-gray-600 mt-2">管理你的个人训练数据和目标</p>
      </div>

      <div className="mb-6 flex space-x-4">
        <button 
          onClick={() => setShowEditForm(!showEditForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showEditForm ? '取消' : '编辑档案'}
        </button>
        <button 
          onClick={handleSyncGarmin}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          同步 Garmin 数据
        </button>
      </div>

      {showEditForm ? (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">编辑运动员档案</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">最大心率</label>
              <input 
                type="number" 
                value={editProfile.max_hr || ''}
                onChange={(e) => setEditProfile({...editProfile, max_hr: e.target.value ? parseInt(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">静息心率</label>
              <input 
                type="number" 
                value={editProfile.rest_hr || ''}
                onChange={(e) => setEditProfile({...editProfile, rest_hr: e.target.value ? parseInt(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">VO2 Max</label>
              <input 
                type="number" 
                step="0.1"
                value={editProfile.vo2max || ''}
                onChange={(e) => setEditProfile({...editProfile, vo2max: e.target.value ? parseFloat(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">乳酸阈值心率</label>
              <input 
                type="number" 
                value={editProfile.lthr || ''}
                onChange={(e) => setEditProfile({...editProfile, lthr: e.target.value ? parseInt(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">功能阈值功率</label>
              <input 
                type="number" 
                value={editProfile.ftp || ''}
                onChange={(e) => setEditProfile({...editProfile, ftp: e.target.value ? parseInt(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">周跑量目标 (km)</label>
              <input 
                type="number" 
                step="0.1"
                value={editProfile.weekly_mileage_goal_km || ''}
                onChange={(e) => setEditProfile({...editProfile, weekly_mileage_goal_km: e.target.value ? parseFloat(e.target.value) : null})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">比赛目标</label>
              <input 
                type="text" 
                value={editProfile.race_target || ''}
                onChange={(e) => setEditProfile({...editProfile, race_target: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">比赛日期</label>
              <input 
                type="date" 
                value={editProfile.race_date || ''}
                onChange={(e) => setEditProfile({...editProfile, race_date: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-gray-700 mb-2">伤病历史</label>
              <textarea 
                value={editProfile.injury_history || ''}
                onChange={(e) => setEditProfile({...editProfile, injury_history: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            </div>
            <div className="col-span-2">
              <label className="block text-gray-700 mb-2">训练偏好</label>
              <textarea 
                value={editProfile.training_preference || ''}
                onChange={(e) => setEditProfile({...editProfile, training_preference: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            </div>
            <div className="col-span-2">
              <label className="block text-gray-700 mb-2">备注</label>
              <textarea 
                value={editProfile.notes || ''}
                onChange={(e) => setEditProfile({...editProfile, notes: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            </div>
          </div>
          <button 
            onClick={handleUpdateProfile}
            className="mt-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            保存
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">个人信息</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600">最大心率</p>
              <p className="font-medium text-gray-800">{profile.max_hr || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">静息心率</p>
              <p className="font-medium text-gray-800">{profile.rest_hr || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">VO2 Max</p>
              <p className="font-medium text-gray-800">{profile.vo2max || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">乳酸阈值心率</p>
              <p className="font-medium text-gray-800">{profile.lthr || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">功能阈值功率</p>
              <p className="font-medium text-gray-800">{profile.ftp || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">周跑量目标</p>
              <p className="font-medium text-gray-800">{profile.weekly_mileage_goal_km || '-'} km</p>
            </div>
            <div>
              <p className="text-gray-600">比赛目标</p>
              <p className="font-medium text-gray-800">{profile.race_target || '-'}</p>
            </div>
            <div>
              <p className="text-gray-600">比赛日期</p>
              <p className="font-medium text-gray-800">{profile.race_date || '-'}</p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-600">伤病历史</p>
              <p className="font-medium text-gray-800">{profile.injury_history || '-'}</p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-600">训练偏好</p>
              <p className="font-medium text-gray-800">{profile.training_preference || '-'}</p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-600">备注</p>
              <p className="font-medium text-gray-800">{profile.notes || '-'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Profile