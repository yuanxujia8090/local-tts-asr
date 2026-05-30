import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TTSPanel from '../pages/TTSPanel'
import { ToastProvider } from '../hooks/useToast'

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>
}

describe('TTSPanel voice_design instruct field', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', { createObjectURL: () => 'blob:test' })
  })

  const mockFetch = (mockBlob: Blob) => {
    return vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })
  }

  it('sends instruct field in voice_design mode', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = mockFetch(mockBlob)

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'design test' } })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    const designInput = screen.getByPlaceholderText('例如：温柔的女声，音调偏高')
    fireEvent.change(designInput, { target: { value: '温柔的女声，音调偏高' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.mode).toBe('voice_design')
      expect(body.instruct).toBe('温柔的女声，音调偏高')
    })
  })

  it('does not send emotion field in voice_design mode', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = mockFetch(mockBlob)

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'design test' } })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    const designInput = screen.getByPlaceholderText('例如：温柔的女声，音调偏高')
    fireEvent.change(designInput, { target: { value: 'A cheerful voice' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.instruct).toBe('A cheerful voice')
      expect(body.emotion).toBeUndefined()
    })
  })

  it('sends emotion field in custom_voice mode', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = mockFetch(mockBlob)

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const emotionSelect = screen.getAllByRole('combobox')[3]
    fireEvent.change(emotionSelect, { target: { value: 'happy' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.mode).toBe('custom_voice')
      expect(body.emotion).toBe('happy')
      expect(body.instruct).toBeUndefined()
    })
  })
})
