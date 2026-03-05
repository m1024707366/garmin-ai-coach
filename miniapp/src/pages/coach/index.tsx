import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'

import './index.scss'

const features = [
  {
    emoji: '🌅',
    title: '晨间报告',
    desc: '睡眠分析与今日训练建议',
    url: '/pages/morning-report/index',
  },
  {
    emoji: '🌙',
    title: '晚间复盘',
    desc: '今日训练回顾与恢复评估',
    url: '/pages/evening-review/index',
  },
  {
    emoji: '📊',
    title: '周度总结',
    desc: '本周负荷趋势与比赛信心',
    url: '/pages/weekly-summary/index',
  },
  {
    emoji: '💬',
    title: 'AI 对话',
    desc: '自由提问，教练实时解答',
    url: '/pages/chat/index',
  },
  {
    emoji: '🩹',
    title: '伤病记录',
    desc: '记录与跟踪伤病恢复进度',
    url: '/pages/injury-log/index',
  },
  {
    emoji: '🏃',
    title: '运动员档案',
    desc: '个人指标与比赛目标设置',
    url: '/pages/profile/index',
  },
]

function Coach() {
  const handleNavigate = (url: string) => {
    Taro.navigateTo({ url })
  }

  return (
    <View className='page coach'>
      <View className='hero'>
        <Text className='title'>AI 教练</Text>
        <Text className='subtitle'>专属跑步训练助手</Text>
      </View>

      <View className='feature-grid'>
        {features.map((item) => (
          <View
            key={item.title}
            className='feature-card'
            onClick={() => handleNavigate(item.url)}
          >
            <Text className='feature-emoji'>{item.emoji}</Text>
            <Text className='feature-title'>{item.title}</Text>
            <Text className='feature-desc'>{item.desc}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}

export default Coach
