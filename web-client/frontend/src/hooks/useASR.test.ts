import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useASR } from '../hooks/useASR'

describe('useASR', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends multipart POST with file on transcribe', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve('hello world'),
    })

    const mockFile = new File(['audio data'], 'test.wav', { type: 'audio/wav' })
    const { result } = renderHook(() => useASR())

    await result.current.transcribe(mockFile, 'text')

    expect(global.fetch).toHaveBeenCalledWith('/v1/audio/transcriptions', {
      method: 'POST',
      body: expect.any(FormData),
    })

    const formData = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData
    expect(formData.get('file')).toBe(mockFile)
    expect(formData.get('response_format')).toBe('text')
  })

  it('returns text string for text format', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve('你好世界'),
    })

    const { result } = renderHook(() => useASR())
    const res = await result.current.transcribe(new File(['data'], 'test.wav'), 'text')

    expect(res).toBe('你好世界')
  })

  it('returns ASRResult for verbose_json format', async () => {
    const mockData = {
      text: 'hello world',
      language: 'en',
      duration: 1.5,
      segments: [{ start: 0.1, end: 0.5, word: 'hello' }],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const { result } = renderHook(() => useASR())
    const res = await result.current.transcribe(new File(['data'], 'test.wav'), 'verbose_json')

    expect((res as any).text).toBe('hello world')
    expect((res as any).language).toBe('en')
    expect((res as any).duration).toBe(1.5)
  })

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('ASR engine error'),
    })

    const { result } = renderHook(() => useASR())

    await expect(result.current.transcribe(new File(['data'], 'test.wav')))
      .rejects.toThrow('ASR API error: ASR engine error')
  })

  it('validates verbose_json response has text field', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ language: 'en', duration: 1.0 }),
    })

    const { result } = renderHook(() => useASR())

    await expect(result.current.transcribe(new File(['data'], 'test.wav'), 'verbose_json'))
      .rejects.toThrow('Invalid ASR response: missing text field')
  })

  it('uses text as default format', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve('hello'),
    })

    const { result } = renderHook(() => useASR())
    await result.current.transcribe(new File(['data'], 'test.wav'))

    const formData = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData
    expect(formData.get('response_format')).toBe('text')
  })
})
