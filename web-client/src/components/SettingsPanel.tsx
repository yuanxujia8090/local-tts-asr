import { useState, useEffect } from 'react'

interface HealthInfo {
  status: string
  engine_mode: string
}

export function SettingsPanel() {
  const [engineMode, setEngineMode] = useState('local')
  const [remoteUrl, setRemoteUrl] = useState('http://localhost:11434')
  const [backendMode, setBackendMode] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(r => r.json())
      .then(data => setBackendMode(data.engine_mode))
      .catch(() => {})
  }, [])

  const handleSave = () => {
    localStorage.setItem('engine_mode', engineMode)
    localStorage.setItem('remote_engine_url', remoteUrl)
    alert('设置已保存到本地（需要重启后端服务生效）')
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-cyan-600">设置</h2>

      {backendMode && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded text-sm">
          <span className="text-gray-500">当前后端模式：</span>
          <span className="text-cyan-600 font-medium">{backendMode}</span>
        </div>
      )}

      <div>
        <label className="block text-sm text-gray-500 mb-1">推理模式（前端缓存）</label>
        <select value={engineMode} onChange={(e) => setEngineMode(e.target.value)}
                className="w-full bg-white border border-gray-300 rounded p-2 text-gray-800">
          <option value="local">本地推理 (MLX / PyTorch)</option>
          <option value="remote">远程转发 (Ollama / vLLM)</option>
        </select>
      </div>

      {engineMode === 'remote' && (
        <div>
          <label className="block text-sm text-gray-500 mb-1">远程 API URL</label>
          <input
            type="text"
            value={remoteUrl}
            onChange={(e) => setRemoteUrl(e.target.value)}
            className="w-full bg-white border border-gray-300 rounded p-2 text-gray-800"
          />
        </div>
      )}

      <button onClick={handleSave}
              className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium">
        保存设置
      </button>

      <div className="mt-6 p-4 bg-gray-50 rounded text-sm text-gray-600">
        <p>注意：ENGINE_MODE 切换需要重启后端服务。</p>
        <pre className="mt-2 text-cyan-600">ENGINE_MODE=local uv run python src/main.py</pre>
      </div>
    </div>
  )
}
