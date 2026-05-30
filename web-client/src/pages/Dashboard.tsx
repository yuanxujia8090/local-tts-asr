import { useState } from 'react'
import TTSPanel from './TTSPanel'
import ASRPanel from './ASRPanel'
import VoiceManager from './VoiceManager'
import { SettingsPanel } from '../components/SettingsPanel'

type Tab = 'tts' | 'asr' | 'voices' | 'settings'

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('tts')

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="mx-auto w-[960px] px-4">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-cyan-600">Qwen3 Voice Service</h1>
          <p className="text-gray-500 mt-1">Local TTS/ASR Processing Center</p>
        </header>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-6 border-b border-gray-300">
          <button
            onClick={() => setActiveTab('tts')}
            className={`px-4 py-2 font-medium ${activeTab === 'tts' ? 'text-cyan-600 border-b-2 border-cyan-600' : 'text-gray-500 hover:text-gray-800'}`}
          >
            TTS 合成
          </button>
          <button
            onClick={() => setActiveTab('asr')}
            className={`px-4 py-2 font-medium ${activeTab === 'asr' ? 'text-cyan-600 border-b-2 border-cyan-600' : 'text-gray-500 hover:text-gray-800'}`}
          >
            ASR 转录
          </button>
          <button
            onClick={() => setActiveTab('voices')}
            className={`px-4 py-2 font-medium ${activeTab === 'voices' ? 'text-cyan-600 border-b-2 border-cyan-600' : 'text-gray-500 hover:text-gray-800'}`}
          >
            音色管理
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-2 font-medium ${activeTab === 'settings' ? 'text-cyan-600 border-b-2 border-cyan-600' : 'text-gray-500 hover:text-gray-800'}`}
          >
            设置
          </button>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'tts' && <TTSPanel />}
          {activeTab === 'asr' && <ASRPanel />}
          {activeTab === 'voices' && <VoiceManager />}
          {activeTab === 'settings' && <SettingsPanel />}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
