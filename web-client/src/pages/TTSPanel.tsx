import { useState, useEffect } from 'react'
import { useTTS, type TTSRequest, type CustomVoice } from '../hooks/useTTS'
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
  const [blob, setBlob] = useState<Blob | null>(null)

  // Completion modal
  const [showCompletionModal, setShowCompletionModal] = useState(false)

  // Advanced parameters
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [temperature, setTemperature] = useState(0.9)
  const [topP, setTopP] = useState(1.0)

  // Custom voices
  const [customVoices, setCustomVoices] = useState<CustomVoice[]>([])
  const [savedVoiceId, setSavedVoiceId] = useState('')

  // Save custom voice dialog
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [saveVoiceName, setSaveVoiceName] = useState('')

  // Toast
  const { showToast } = useToast()
  const { synthesize, downloadAudio } = useTTS()

  // Load custom voices on mount
  const loadCustomVoices = async () => {
    try {
      const resp = await fetch('/v1/custom-voices/voices')
      if (resp.ok) {
        const voices = await resp.json()
        setCustomVoices(voices)
      }
    } catch { /* ignore */ }
  }

  useEffect(() => {
    // Only load custom voices if we're in a browser environment with fetch
    if (typeof fetch !== 'undefined') {
      loadCustomVoices()
    }
  }, [])

  const handleSynthesize = async () => {
    if (!text.trim()) return
    setLoading(true)
    // Clear previous audio
    setBlob(null)
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(null)
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

      // Advanced parameters
      req.temperature = temperature
      req.top_p = topP

      const audioBlob = await synthesize(req, refAudio || undefined)
      setBlob(audioBlob)
      const url = URL.createObjectURL(audioBlob)
      setAudioUrl(url)
      showToast('语音合成完成', 'success')
    } catch (err: any) {
      showToast(err.message || '合成失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveCustomVoice = async () => {
    if (!saveVoiceName.trim()) { showToast('请输入音色名称', 'error'); return }
    if (!blob) { showToast('请先生成音频', 'error'); return }

    try {
      // Direct fetch for saving
      const formData = new FormData()
      formData.append('name', saveVoiceName.trim())
      const audioFile = new File([blob], 'voice.wav', { type: blob.type || 'audio/wav' })
      formData.append('ref_audio', audioFile)

      const resp = await fetch('/v1/custom-voices/voices', {
        method: 'POST',
        body: formData,
      })

      if (!resp.ok) {
        const error = await resp.text()
        throw new Error(`保存失败: ${error}`)
      }

      const saved = await resp.json() as CustomVoice
      setCustomVoices(prev => [...prev, saved])
      setShowSaveDialog(false)
      setSaveVoiceName('')
      showToast(`音色 "${saved.name}" 已保存`, 'success')

      // Auto-select the new voice
      setMode('custom_voice')
      setSavedVoiceId(saved.id)
    } catch (err: any) {
      showToast(err.message || '保存失败', 'error')
    }
  }

  const handleDeleteCustomVoice = async (voiceId: string, voiceName: string) => {
    if (!confirm(`确定删除音色 "${voiceName}"？`)) return

    try {
      const resp = await fetch(`/v1/custom-voices/voices/${voiceId}`, {
        method: 'DELETE',
      })
      if (!resp.ok) throw new Error('删除失败')

      setCustomVoices(prev => prev.filter(v => v.id !== voiceId))
      if (savedVoiceId === voiceId) setSavedVoiceId('')
      showToast(`音色 "${voiceName}" 已删除`, 'success')
    } catch {
      showToast('删除失败', 'error')
    }
  }

  const handleDownload = () => {
    if (!blob) return
    downloadAudio(blob, `tts_${Date.now()}.wav`)
  }

  // Determine voice options (built-in + custom)
  const allVoices = [
    ...customVoices.map(v => ({ id: v.id, name: `🎙️ ${v.name}` })),
    ...SPEAKERS.map(s => ({ id: s, name: s })),
  ]

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

      {/* Mode Selection — Tab Switcher */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">合成模式</label>
        <div className="flex gap-2">
          {MODES.map(m => (
            <button
              key={m.value}
              onClick={() => setMode(m.value)}
              className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
                mode === m.value
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Controls based on mode */}
      {mode === 'custom_voice' && (
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">音色</label>
            <select value={savedVoiceId || voice}
                    onChange={(e) => { setSavedVoiceId(''); setVoice(e.target.value); }}
                    className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
              {allVoices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
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

      {/* Emotion - only for built-in speakers */}
      {mode === 'custom_voice' && allVoices.some(v => v.id === voice) && SPEAKERS.includes(voice) && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">情绪</label>
          <select value={emotion} onChange={(e) => setEmotion(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white">
            <option value="">默认</option>
            {EMOTIONS.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
      )}

      {mode === 'voice_design' && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">声音描述</label>
          <textarea
            value={emotion}
            onChange={(e) => setEmotion(e.target.value)}
            rows={6}
            className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white resize-y"
            placeholder="例如：温柔的女声，音调偏高，带一点笑意" />
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

      {/* Advanced Parameters Toggle */}
      <div>
        <button onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-gray-400 hover:text-cyan-300 flex items-center gap-1">
          {showAdvanced ? '▾' : '▸'} 高级参数
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-700">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Temperature ({temperature})</label>
              <input type="range" min={0.1} max={2.0} step={0.05} value={temperature}
                     onChange={(e) => setTemperature(parseFloat(e.target.value))}
                     className="w-full accent-cyan-500" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Top-p ({topP})</label>
              <input type="range" min={0.1} max={1.0} step={0.05} value={topP}
                     onChange={(e) => setTopP(parseFloat(e.target.value))}
                     className="w-full accent-cyan-500" />
            </div>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button onClick={handleSynthesize} disabled={loading || !text.trim()}
              className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded font-medium">
        {loading ? '合成中...' : '生成语音'}
      </button>

      {/* Audio Player + Actions */}
      {audioUrl && blob && (
        <div className="mt-4 space-y-2">
          <audio controls src={audioUrl} className="w-full" />
          <div className="flex gap-3">
            <button onClick={() => setShowSaveDialog(true)}
                    className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm font-medium">
              💾 保存为自定义音色
            </button>
            <button onClick={handleDownload}
                    className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm">
              ⬇ 下载音频
            </button>
          </div>
        </div>
      )}



      {/* Save Custom Voice Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
             onClick={() => setShowSaveDialog(false)}>
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-sm"
               onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">保存自定义音色</h3>
            <input type="text" value={saveVoiceName}
                   onChange={(e) => setSaveVoiceName(e.target.value)}
                   placeholder="输入音色名称"
                   className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white mb-4"
                   onKeyDown={(e) => e.key === 'Enter' && handleSaveCustomVoice()} />
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowSaveDialog(false)}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded">
                取消
              </button>
              <button onClick={handleSaveCustomVoice}
                      className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded font-medium">
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TTSPanel
