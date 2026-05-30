import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TTSPanel from '../pages/TTSPanel'
import { ToastProvider } from '../hooks/useToast'

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>
}

describe('TTSPanel', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', { createObjectURL: () => 'blob:test-url' })
    vi.stubGlobal('Blob', class Blob {})
    // Default fetch mock for custom voices API (returns empty list)
    vi.restoreAllMocks()
  })

  it('renders with default values', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    expect(screen.getByText('TTS 合成测试')).toBeInTheDocument()
    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    expect(textarea).toHaveValue('你好，世界！')

    const modeSelect = screen.getAllByRole('combobox')[0]
    expect(modeSelect).toHaveValue('custom_voice')
  })

  it('renders speaker selection for custom_voice mode', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const voiceSelect = screen.getAllByRole('combobox')[1]
    expect(voiceSelect).toBeInTheDocument()
  })

  it('renders emotion dropdown for custom_voice mode', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const emotionSelect = screen.getAllByRole('combobox')[2]
    expect(emotionSelect).toBeInTheDocument()
  })

  it('renders voice design input for voice_design mode', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('例如：温柔的女声，音调偏高')).toBeInTheDocument()
    })
  })

  it('renders file upload for voice_clone mode', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_clone' } })

    await waitFor(() => {
      expect(screen.getByText('参考音频')).toBeInTheDocument()
    })

    const fileInputs = document.querySelectorAll('input[type="file"]')
    expect(fileInputs.length).toBeGreaterThan(0)
  })

  it('hides speaker/emotion controls when not in custom_voice mode', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    await waitFor(() => {
      expect(screen.queryByPlaceholderText('例如：温柔的女声，音调偏高')).toBeInTheDocument()
    })

    const emotionLabel = screen.queryByText('情绪')
    expect(emotionLabel).not.toBeInTheDocument()
  })

  it('generate button is disabled when text is empty', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: '' } })

    const button = screen.getByText('生成语音')
    expect(button).toBeDisabled()
  })

  it('generate button is enabled when text has content', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'hello' } })

    const button = screen.getByText('生成语音')
    expect(button).toBeEnabled()
  })

  it('shows voice design error when emotion is empty', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('例如：温柔的女声，音调偏高')).toBeInTheDocument()
    })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('请输入声音描述')).toBeInTheDocument()
    })
  })

  it('shows loading state during synthesis', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('合成中...')).toBeInTheDocument()
    })
  })

  it('disables button during loading', async () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(button).toBeDisabled()
    })
  })

  it('shows audio player after successful synthesis', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    vi.stubGlobal('URL', { createObjectURL: () => 'blob:test' })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const audio = document.querySelector('audio')
      expect(audio).toBeInTheDocument()
      expect(audio?.getAttribute('src')).toBe('blob:test')
    })
  })

  it('passes mode in request body', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      expect(speechCalls.length).toBeGreaterThan(0)
      const [url, config] = speechCalls[0]
      expect(url).toBe('/v1/audio/speech')
      const body = JSON.parse(config.body)
      expect(body.mode).toBe('custom_voice')
    })
  })

  it('passes voice in request body for custom_voice mode', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.voice).toBe('Vivian')
    })
  })

  it('passes emotion in request body when selected', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

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
      expect(body.emotion).toBe('happy')
    })
  })

  it('shows error toast on synthesis failure', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: false, text: () => Promise.resolve('Model not found') })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('TTS API error: Model not found')).toBeInTheDocument()
    })
  })

  it('resets loading state after synthesis completes', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'test text' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('合成中...')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('生成语音')).toBeInTheDocument()
    })
  })

  it('all speakers are available in dropdown', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const voiceSelect = screen.getAllByRole('combobox')[1]
    const options = voiceSelect.querySelectorAll('option')
    // 9 builtin speakers (custom voices list is empty)
    expect(options.length).toBeGreaterThanOrEqual(9)

    const speakerNames = Array.from(options).map(o => o.value)
    expect(speakerNames).toContain('Vivian')
    expect(speakerNames).toContain('Serena')
    expect(speakerNames).toContain('Uncle_Fu')
  })

  it('emotion dropdown has default empty option', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const emotionSelect = screen.getAllByRole('combobox')[3]
    const firstOption = emotionSelect.querySelector('option')
    expect(firstOption).toHaveValue('')
  })

  it('language dropdown has all language options', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const languageSelect = screen.getAllByRole('combobox')[2]
    const options = languageSelect.querySelectorAll('option')
    expect(options.length).toBe(5)

    const languages = Array.from(options).map(o => o.value)
    expect(languages).toContain('Auto')
    expect(languages).toContain('Chinese')
    expect(languages).toContain('English')
  })

  it('synthesizes with voice_design mode and emotion', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'design test' } })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    const designInput = screen.getByPlaceholderText('例如：温柔的女声，音调偏高')
    fireEvent.change(designInput, { target: { value: '温柔的女声' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.mode).toBe('voice_design')
    })
  })

  it('does not send voice for voice_design mode', async () => {
    const mockBlob = new Blob(['test'], { type: 'audio/wav' })
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/custom-voices/voices') && !url.includes('/audio')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      }
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(mockBlob) })
    })

    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByPlaceholderText('输入要合成的文本...')
    fireEvent.change(textarea, { target: { value: 'design test' } })

    const modeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(modeSelect, { target: { value: 'voice_design' } })

    const designInput = screen.getByPlaceholderText('例如：温柔的女声，音调偏高')
    fireEvent.change(designInput, { target: { value: '温柔的女声' } })

    const button = screen.getByText('生成语音')
    userEvent.click(button)

    await waitFor(() => {
      const speechCalls = (global.fetch as any).mock.calls.filter(
        (call: any[]) => call[0]?.includes('/audio/speech')
      )
      const [url, config] = speechCalls[0]
      const body = JSON.parse(config.body)
      expect(body.voice).toBeUndefined()
    })
  })

  it('text input is a textarea element', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const textarea = screen.getByRole('textbox')
    expect(textarea.tagName).toBe('TEXTAREA')
  })

  it('mode select has three options', () => {
    render(<TTSPanel />, { wrapper: TestWrapper })

    const modeSelect = screen.getAllByRole('combobox')[0]
    const options = modeSelect.querySelectorAll('option')
    expect(options.length).toBe(3)

    const labels = Array.from(options).map(o => o.textContent)
    expect(labels).toContain('内置音色')
    expect(labels).toContain('声音克隆')
    expect(labels).toContain('声音设计')
  })
})
