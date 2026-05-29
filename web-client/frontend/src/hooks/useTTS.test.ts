import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useTTS } from '../hooks/useTTS'

describe('useTTS', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.stubGlobal('Blob', class Blob {})
  })

  it('sends POST request with correct JSON body on synthesize', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())

    await result.current.synthesize({
      input: 'hello',
      voice: 'Vivian',
      mode: 'custom_voice',
    })

    expect(global.fetch).toHaveBeenCalledWith('/v1/audio/speech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input: 'hello',
        voice: 'Vivian',
        mode: 'custom_voice',
      }),
    })
  })

  it('returns a Blob on success', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())
    const blob = await result.current.synthesize({ input: 'test' })

    expect(blob).toBeInstanceOf(Blob)
  })

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('TTS engine error: model not loaded'),
    })

    const { result } = renderHook(() => useTTS())

    await expect(result.current.synthesize({ input: 'hello' }))
      .rejects.toThrow('TTS API error: TTS engine error: model not loaded')
  })

  it('passes mode field when provided', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())
    await result.current.synthesize({
      input: 'hello',
      mode: 'voice_design',
      instruct: '温柔的女声',
    })

    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as string)
    expect(body.mode).toBe('voice_design')
    expect(body.instruct).toBe('温柔的女声')
  })

  it('passes language field when provided', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())
    await result.current.synthesize({
      input: 'hello',
      language: 'English',
    })

    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as string)
    expect(body.language).toBe('English')
  })

  it('passes emotion field when provided', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())
    await result.current.synthesize({
      input: 'hello',
      emotion: 'happy',
    })

    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as string)
    expect(body.emotion).toBe('happy')
  })

  it('passes ref_audio field when provided', async () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    const { result } = renderHook(() => useTTS())
    await result.current.synthesize({
      input: 'hello',
      mode: 'voice_clone',
      ref_audio: '/path/to/ref.wav',
    })

    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as string)
    expect(body.ref_audio).toBe('/path/to/ref.wav')
  })
})
