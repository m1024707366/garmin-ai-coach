import { useEffect, useState } from 'react'
import { coachApi } from '../api/coach'
import Error from '../components/Error'
import Loading from '../components/Loading'
import { MarkdownView } from '../components/MarkdownView'

function Chat() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chatHistory, setChatHistory] = useState<any[]>([])
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)

  const fetchChatHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await coachApi.getChatHistory()
      setChatHistory(result.messages || [])
    } catch {
      setError('获取聊天历史失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchChatHistory()
  }, [])

  const handleSendMessage = async () => {
    if (!message.trim()) return

    setSending(true)
    try {
      const result = await coachApi.chat({ message: message.trim() })
      setChatHistory([...chatHistory, { role: 'user', content: message.trim() }, { role: 'assistant', content: result.reply }])
      setMessage('')
    } catch {
      alert('发送消息失败')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <Loading />
  if (error) return <Error message={error} onRetry={fetchChatHistory} />

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">AI 对话</h1>
        <p className="text-gray-600 mt-2">与 AI 教练进行对话</p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">聊天历史</h2>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {chatHistory.length > 0 ? (
            chatHistory.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-4 rounded-lg ${msg.role === 'user' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                  {msg.role === 'assistant' ? (
                    <MarkdownView content={msg.content} />
                  ) : (
                    <p>{msg.content}</p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-600 text-center py-8">暂无聊天记录</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">发送消息</h2>
        <div className="flex space-x-2">
          <input 
            type="text" 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
            placeholder="输入你的问题..."
            disabled={sending}
          />
          <button 
            onClick={handleSendMessage}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            disabled={sending}
          >
            {sending ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Chat