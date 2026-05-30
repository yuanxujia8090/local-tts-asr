export interface TTSRequest {
  model?: string
  input: string
  voice?: string
  emotion?: string
  language?: string
  response_format?: string
  mode?: 'custom_voice' | 'voice_clone' | 'voice_design' | 'custom_saved'
  ref_audio?: string
  ref_text?: string
  instruct?: string
  temperature?: number
  top_p?: number
  max_new_tokens?: number
}

export interface CustomVoice {
  id: string
  name: string
  filename: string
  created_at: string
}

export function useTTS() {
  const synthesize = async (req: TTSRequest, refAudioFile?: File): Promise<Blob> => {
    let resp: Response

    if (req.mode === 'voice_clone' && refAudioFile) {
      // voice_clone needs file upload — use multipart/form-data
      const formData = new FormData()
      formData.append('input', req.input)
      if (req.voice) formData.append('voice', req.voice)
      if (req.emotion) formData.append('emotion', req.emotion)
      if (req.language) formData.append('language', req.language)
      if (req.response_format) formData.append('response_format', req.response_format)
      if (req.mode) formData.append('mode', req.mode)
      if (refAudioFile) formData.append('ref_audio_file', refAudioFile)
      if (req.ref_text) formData.append('ref_text', req.ref_text)
      if (req.instruct) formData.append('instruct', req.instruct)
      if (req.temperature != null) formData.append('temperature', String(req.temperature))
      if (req.top_p != null) formData.append('top_p', String(req.top_p))
      if (req.max_new_tokens != null) formData.append('max_new_tokens', String(req.max_new_tokens))

      resp = await fetch('/v1/audio/speech', { method: 'POST', body: formData })
    } else {
      // Other modes — use JSON
      resp = await fetch('/v1/audio/speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })
    }

    if (!resp.ok) {
      const error = await resp.text()
      throw new Error(`TTS API error: ${error}`)
    }
    return resp.blob()
  }

  const downloadAudio = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return { synthesize, downloadAudio }
}

export function useCustomVoices() {
  const list = async (): Promise<CustomVoice[]> => {
    const resp = await fetch('/v1/custom-voices/voices')
    if (!resp.ok) throw new Error('Failed to list custom voices')
    return resp.json()
  }

  const save = async (name: string, audioFile: File): Promise<CustomVoice> => {
    const formData = new FormData()
    formData.append('name', name)
    formData.append('ref_audio', audioFile)
    const resp = await fetch('/v1/custom-voices/voices', {
      method: 'POST',
      body: formData,
    })
    if (!resp.ok) {
      const error = await resp.text()
      throw new Error(`Failed to save custom voice: ${error}`)
    }
    return resp.json()
  }

  const remove = async (voiceId: string): Promise<void> => {
    const resp = await fetch(`/v1/custom-voices/voices/${voiceId}`, {
      method: 'DELETE',
    })
    if (!resp.ok) throw new Error('Failed to delete custom voice')
  }

  const getAudioUrl = (voiceId: string): string => {
    return `/v1/custom-voices/voices/${voiceId}/audio`
  }

  return { list, save, remove, getAudioUrl }
}
