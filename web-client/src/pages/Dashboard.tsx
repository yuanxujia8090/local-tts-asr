import { useState } from 'react'
import TTSPanel from './TTSPanel'
import ASRPanel from './ASRPanel'
import VoiceManager from './VoiceManager'
import { SettingsPanel } from '../components/SettingsPanel'

type Tab = 'tts' | 'asr' | 'voices' | 'settings'

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('tts')

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-cyan-400">Qwen3 Voice Service</h1>
        <p className="text-gray-400 mt-1">Local TTS/ASR Processing Center</p>
      </header>

      {/* Tab Navigation */}
      <div className="flex gap-4 mb-6 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('tts')}
          className={`px-4 py-2 font-medium ${activeTab === 'tts' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
        >
          TTS 合成
        </button>
        <button
          onClick={() => setActiveTab('asr')}
          className={`px-4 py-2 font-medium ${activeTab === 'asr' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
        >
          ASR 转录
        </button>
        <button
          onClick={() => setActiveTab('voices')}
          className={`px-4 py-2 font-medium ${activeTab === 'voices' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
        >
          音色管理
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 font-medium ${activeTab === 'settings' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
        >
          设置
        </button>
      </div>

      {/* Tab Content */}
      <div className="bg-gray-800 rounded-lg p-6">
        {activeTab === 'tts' && <TTSPanel />}
        {activeTab === 'asr' && <ASRPanel />}
        {activeTab === 'voices' && <VoiceManager />}
        {activeTab === 'settings' && <SettingsPanel />}
      </div>
    </div>
  )
}

export default Dashboard
