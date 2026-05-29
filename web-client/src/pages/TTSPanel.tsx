import { useState } from 'react'
import { useTTS, type TTSRequest } from '../hooks/useTTS'
import { useToast } from '../hooks/useToast'

const SPEAKERS = ['Vivian', 'Serena', 'Uncle_Fu', 'Dylan', 'Eric',
                  'Ryan', 'Aiden', 'Ono_Anna', 'Sohee']

const EMOTIONS = ['happy', 'calm', 'excited', 'sad', 'angry', 'whisper']

const MODES = [
  { value: 'custom_voice', label: '内置音色' },
  { value: 'voice_clone', label: '声音克隆' },
  { value: 'voice_design', label: '声音设计' },
]

function TTSPanel() {
  const [text, setText] = useState('你好，世界！')
  const [mode, setMode] = useState('custom_voice')
  const [voice, setVoice] = useState('Vivian')
  const [emotion, setEmotion] = useState('')
  const [language, setLanguage] = useState('Auto')
  const [refAudio, setRefAudio] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const { synthesize } = useTTS()
  const { showToast } = useToast()

  const handleSynthesize = async () => {
    if (!text.trim()) return
    setLoading(true)
    try {
      const req: TTSRequest = { input: text, mode }

      if (mode === 'custom_voice') {
        req.voice = voice
        if (emotion) req.emotion = emotion
      } else if (mode === 'voice_clone') {
        if (!refAudio) { showToast('请上传参考音频', 'error'); return }
      } else if (mode === 'voice_design') {
        if (!emotion) { showToast('请输入声音描述', 'error'); return }
        req.instruct = emotion
      }

      const blob = await synthesize(req)
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
    } catch (err: any) {
      showToast(err.message || '合成失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-cyan-300">TTS 合成测试</h2>

      {/* Text Input */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">输入文本</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded p-3 text-white resize-none"
          rows={4}
          placeholder="输入要合成的文本..."
        />
      </div>

      {/* Mode Selection */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">合成模式</label>
        <select value={mode} onChange={(e) => setMode(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
          {MODES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
        </select>
      </div>

      {/* Controls based on mode */}
      {mode === 'custom_voice' && (
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">音色</label>
            <select value={voice} onChange={(e) => setVoice(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
              {SPEAKERS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">情绪</label>
            <select value={emotion} onChange={(e) => setEmotion(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
              <option value="">默认</option>
              {EMOTIONS.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">语言</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
              <option>Auto</option><option>Chinese</option><option>English</option>
              <option>Japanese</option><option>Korean</option>
            </select>
          </div>
        </div>
      )}

      {mode === 'voice_design' && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">声音描述</label>
          <input type="text" value={emotion} onChange={(e) => setEmotion(e.target.value)}
                 className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
                 placeholder="例如：温柔的女声，音调偏高" />
        </div>
      )}

      {mode === 'voice_clone' && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">参考音频</label>
          <input type="file" accept="audio/*"
                 onChange={(e) => e.target.files && setRefAudio(e.target.files[0])}
                 className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4
                            file:rounded file:border-0 file:text-sm file:font-semibold
                            file:bg-cyan-600 file:text-white hover:file:bg-cyan-500" />
        </div>
      )}

      {/* Generate Button */}
      <button onClick={handleSynthesize} disabled={loading || !text.trim()}
              className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded font-medium">
        {loading ? '合成中...' : '生成语音'}
      </button>

      {/* Audio Player */}
      {audioUrl && (
        <div className="mt-4">
          <audio controls src={audioUrl} className="w-full" />
        </div>
      )}
    </div>
  )
}

export default TTSPanel
