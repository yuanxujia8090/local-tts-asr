export interface ASRResult {
  text: string
  language?: string
  duration?: number
  words?: Array<{ word: string; start: number; end: number }>
}

export function useASR() {
  const transcribe = async (file: File, format: string = 'text'): Promise<ASRResult | string> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('response_format', format)

    const resp = await fetch('/v1/audio/transcriptions', {
      method: 'POST',
      body: formData,
    })
    if (!resp.ok) {
      const error = await resp.text()
      throw new Error(`ASR API error: ${error}`)
    }

    if (format === 'verbose_json') {
      const data = await resp.json() as Record<string, unknown>
      if (typeof data.text !== 'string') {
        throw new Error('Invalid ASR response: missing text field')
      }
      return data as unknown as ASRResult
    }
    return await resp.text() as Promise<string>
  }

  return { transcribe }
}
