export interface TTSRequest {
  model?: string
  input: string
  voice?: string
  emotion?: string
  language?: string
  response_format?: string
  mode?: 'custom_voice' | 'voice_clone' | 'voice_design'
  ref_audio?: string
  ref_text?: string
  instruct?: string
}

export function useTTS() {
  const synthesize = async (req: TTSRequest): Promise<Blob> => {
    const resp = await fetch('/v1/audio/speech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
    if (!resp.ok) {
      const error = await resp.text()
      throw new Error(`TTS API error: ${error}`)
    }
    return resp.blob()
  }

  return { synthesize }
}
