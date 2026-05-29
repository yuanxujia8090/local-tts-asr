import { useState, useRef } from 'react'
import { useASR, type ASRResult } from '../hooks/useASR'
import { useToast } from '../hooks/useToast'

function ASRPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<ASRResult | null>(null)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { transcribe } = useASR()
  const { showToast } = useToast()

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await transcribe(file, 'verbose_json') as ASRResult
      setResult(res)
    } catch (err: any) {
      showToast(err.message || '转录失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-cyan-300">ASR 转录测试</h2>

      {/* File Upload */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">上传音频</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={(e) => e.target.files && setFile(e.target.files[0])}
          className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4
                     file:rounded file:border-0 file:text-sm file:font-semibold
                     file:bg-cyan-600 file:text-white hover:file:bg-cyan-500"
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={loading || !file}
        className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded font-medium"
      >
        {loading ? '转录中...' : '开始转录'}
      </button>

      {/* Result Display */}
      {result && (
        <div className="mt-4 space-y-3">
          <div>
            <h3 className="text-sm text-gray-400">转录文本</h3>
            <p className="text-white bg-gray-900 p-3 rounded mt-1">{result.text}</p>
          </div>

          {result.words && result.words.length > 0 && (
            <div>
              <h3 className="text-sm text-gray-400">字词级时间戳</h3>
              <div className="bg-gray-900 rounded p-3 mt-1 max-h-64 overflow-y-auto">
                {result.words.map((w, i) => (
                  <div key={i} className="flex gap-4 text-sm py-1 border-b border-gray-700">
                    <span className="text-cyan-400 font-mono">{w.start.toFixed(2)}s</span>
                    <span className="text-cyan-400 font-mono">{w.end.toFixed(2)}s</span>
                    <span className="text-white flex-1">{w.word}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.language && (
            <p className="text-sm text-gray-500">语言: {result.language} | 时长: {result.duration?.toFixed(2)}s</p>
          )}
        </div>
      )}
    </div>
  )
}

export default ASRPanel
