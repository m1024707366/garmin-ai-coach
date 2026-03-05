import { useEffect, useState } from 'react'
import { View, Text, Button, Input, Picker } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Loading from '../../components/Loading'
import Error from '../../components/Error'
import { getInjuryLogs, createInjuryLog, updateInjuryLog } from '../../api/coach'
import type { InjuryLog } from '../../types'

import './index.scss'

const severityLabels = ['', '轻微', '较轻', '中等', '较重', '严重']
const severityColors = ['', '#34c759', '#30d158', '#ff9f0a', '#ff6b6b', '#ff3b30']
const bodyParts = ['膝盖', '脚踝', '小腿', '大腿', '髋部', '腰部', '足底', '跟腱', '肩部', '其他']

function InjuryLogPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<InjuryLog[]>([])
  const [onlyActive, setOnlyActive] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // 表单状态
  const [bodyPartIdx, setBodyPartIdx] = useState(0)
  const [severity, setSeverity] = useState(1)
  const [injuryType, setInjuryType] = useState('')
  const [description, setDescription] = useState('')

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getInjuryLogs(onlyActive)
      setLogs(result)
    } catch {
      setError('获取伤病记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [onlyActive])

  const handleCreate = async () => {
    try {
      await createInjuryLog({
        body_part: bodyParts[bodyPartIdx],
        severity,
        injury_type: injuryType || undefined,
        description: description || undefined,
      })
      Taro.showToast({ title: '已添加', icon: 'success' })
      setShowForm(false)
      resetForm()
      fetchData()
    } catch {
      Taro.showToast({ title: '添加失败', icon: 'none' })
    }
  }

  const handleRecover = async (log: InjuryLog) => {
    try {
      await updateInjuryLog(log.id, { is_active: false })
      Taro.showToast({ title: '已标记恢复', icon: 'success' })
      fetchData()
    } catch {
      Taro.showToast({ title: '操作失败', icon: 'none' })
    }
  }

  const resetForm = () => {
    setBodyPartIdx(0)
    setSeverity(1)
    setInjuryType('')
    setDescription('')
  }

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchData} />

  return (
    <View className='page injury-log'>
      <View className='hero'>
        <Text className='title'>伤病记录</Text>
        <Text className='subtitle'>跟踪与管理伤病恢复</Text>
      </View>

      {/* 筛选 + 新增 */}
      <View className='toolbar'>
        <View
          className={`filter-btn ${onlyActive ? 'filter-active' : ''}`}
          onClick={() => setOnlyActive(!onlyActive)}
        >
          <Text className='filter-text'>{onlyActive ? '仅活跃' : '全部'}</Text>
        </View>
        <Button className='add-btn' onClick={() => setShowForm(true)}>+ 新增</Button>
      </View>

      {/* 伤病列表 */}
      {logs.length > 0 ? (
        <View className='log-list'>
          {logs.map((log) => (
            <View key={log.id} className='log-item'>
              <View className='log-header'>
                <View className='log-part-wrap'>
                  <View
                    className='severity-dot'
                    style={{ backgroundColor: severityColors[log.severity] || '#9aa4b2' }}
                  />
                  <Text className='log-part'>{log.body_part}</Text>
                </View>
                <Text className='log-severity' style={{ color: severityColors[log.severity] || '#9aa4b2' }}>
                  {severityLabels[log.severity] || `${log.severity}级`}
                </Text>
              </View>
              {log.injury_type ? (
                <Text className='log-type'>{log.injury_type}</Text>
              ) : null}
              {log.description ? (
                <Text className='log-desc'>{log.description}</Text>
              ) : null}
              <View className='log-footer'>
                <Text className='log-date'>
                  {log.occurred_date || log.created_at.split('T')[0]}
                </Text>
                {log.is_active ? (
                  <Text className='recover-btn' onClick={() => handleRecover(log)}>标记恢复</Text>
                ) : (
                  <Text className='recovered-tag'>已恢复</Text>
                )}
              </View>
            </View>
          ))}
        </View>
      ) : (
        <View className='empty-card'>
          <Text className='empty-text'>暂无伤病记录 🎉</Text>
        </View>
      )}

      {/* 新增弹窗 */}
      {showForm ? (
        <View className='modal-mask' onClick={() => setShowForm(false)}>
          <View className='modal-content' onClick={(e) => e.stopPropagation()}>
            <Text className='modal-title'>新增伤病</Text>

            <View className='form-group'>
              <Text className='form-label'>部位</Text>
              <Picker
                mode='selector'
                range={bodyParts}
                value={bodyPartIdx}
                onChange={(e) => setBodyPartIdx(Number(e.detail.value))}
              >
                <View className='picker-value'>{bodyParts[bodyPartIdx]}</View>
              </Picker>
            </View>

            <View className='form-group'>
              <Text className='form-label'>严重程度 ({severity}/5)</Text>
              <View className='severity-selector'>
                {[1, 2, 3, 4, 5].map((s) => (
                  <View
                    key={s}
                    className={`severity-option ${severity === s ? 'severity-selected' : ''}`}
                    style={{
                      backgroundColor: severity === s ? severityColors[s] : '#f3f4f6',
                      color: severity === s ? '#ffffff' : '#6b7280',
                    }}
                    onClick={() => setSeverity(s)}
                  >
                    <Text>{s}</Text>
                  </View>
                ))}
              </View>
            </View>

            <View className='form-group'>
              <Text className='form-label'>伤病类型（选填）</Text>
              <Input
                className='form-input'
                placeholder='如：拉伤、劳损、疲劳性骨折'
                value={injuryType}
                onInput={(e) => setInjuryType(e.detail.value)}
              />
            </View>

            <View className='form-group'>
              <Text className='form-label'>描述（选填）</Text>
              <Input
                className='form-input'
                placeholder='症状描述、原因分析等'
                value={description}
                onInput={(e) => setDescription(e.detail.value)}
              />
            </View>

            <View className='form-actions'>
              <Button className='cancel-btn' onClick={() => setShowForm(false)}>取消</Button>
              <Button className='submit-btn' onClick={handleCreate}>确认添加</Button>
            </View>
          </View>
        </View>
      ) : null}
    </View>
  )
}

export default InjuryLogPage
