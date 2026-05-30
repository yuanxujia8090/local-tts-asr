import { useState, useEffect } from 'react'
import { useToast } from '../hooks/useToast'

interface CustomVoice {
  id: string
  name: string
  filename: string
  created_at: string
}

function VoiceManager() {
  const [voices, setVoices] = useState<CustomVoice[]>([])
  const [loading, setLoading] = useState(true)
  const { showToast } = useToast()

  const loadVoices = async () => {
    try {
      const resp = await fetch('/v1/custom-voices/voices')
      if (resp.ok) {
        const data = await resp.json()
        setVoices(data)
      }
    } catch {
      showToast('加载音色列表失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadVoices() }, [])

  const handleDelete = async (voice: CustomVoice) => {
    if (!confirm(`确定删除音色 "${voice.name}"？`)) return

    try {
      const resp = await fetch(`/v1/custom-voices/voices/${voice.id}`, {
        method: 'DELETE',
      })
      if (!resp.ok) throw new Error('删除失败')

      setVoices(prev => prev.filter(v => v.id !== voice.id))
      showToast(`音色 "${voice.name}" 已删除`, 'success')
    } catch {
      showToast('删除失败', 'error')
    }
  }

  const handlePlay = async (voice: CustomVoice) => {
    try {
      const resp = await fetch(`/v1/custom-voices/voices/${voice.id}/audio`)
      if (!resp.ok) throw new Error('音频加载失败')

      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)

      audio.onended = () => URL.revokeObjectURL(url)
      audio.onerror = () => {
        showToast('播放失败', 'error')
        URL.revokeObjectURL(url)
      }
      audio.play()
    } catch {
      showToast('播放失败', 'error')
    }
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
      })
    } catch {
      return iso
    }
  }

  if (loading) {
    return <div className="text-gray-400">加载中...</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-cyan-600">自定义音色管理</h2>

      {voices.length === 0 ? (
        <div className="text-gray-400 text-center py-8">
          暂无自定义音色。在 TTS 合成页面上传参考音频后保存。
        </div>
      ) : (
        <div className="space-y-3">
          {voices.map(voice => (
            <div key={voice.id}
                 className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4">
              {/* Play button */}
              <button onClick={() => handlePlay(voice)}
                      className="w-10 h-10 rounded-full bg-cyan-600 hover:bg-cyan-500 flex items-center justify-center shrink-0"
                      title="试听">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
              </button>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{voice.name}</p>
                <p className="text-xs text-gray-500 mt-1">{formatDate(voice.created_at)}</p>
              </div>

              {/* Delete */}
              <button onClick={() => handleDelete(voice)}
                      className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/70 text-red-300 rounded text-sm">
                删除
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Usage hint */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <p className="text-cyan-600 font-medium mb-1">💡 使用提示</p>
        <ul className="list-disc list-inside space-y-1 text-xs">
          <li>在 TTS 合成页面的「内置音色」模式下，下拉列表会包含你保存的自定义音色</li>
          <li>上传参考音频后，点击「💾 保存为自定义音色」按钮即可保存</li>
          <li>保存的音色可在任意合成任务中复用，无需重新上传参考音频</li>
        </ul>
      </div>
    </div>
  )
}

export default VoiceManager
