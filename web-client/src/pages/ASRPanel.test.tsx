import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ASRPanel from '../pages/ASRPanel'
import { ToastProvider } from '../hooks/useToast'

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>
}

describe('ASRPanel', () => {
  beforeEach(() => {
    vi.stubGlobal('Blob', class Blob {})
  })

  it('renders with file upload input', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    expect(screen.getByText('ASR 转录测试')).toBeInTheDocument()
    expect(screen.getByText('上传音频')).toBeInTheDocument()
  })

  it('has start transcription button', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    expect(screen.getByText('开始转录')).toBeInTheDocument()
  })

  it('button is disabled when no file selected', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    const button = screen.getByText('开始转录')
    expect(button).toBeDisabled()
  })

  it('button is enabled when file selected', async () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })

    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })
  })

  it('shows transcription result text', async () => {
    const mockResult = {
      text: '你好世界',
      language: 'zh',
      duration: 3.5,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResult),
    })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('你好世界')).toBeInTheDocument()
    })
  })

  it('shows word-level timestamps when available', async () => {
    const mockResult = {
      text: 'hello world',
      language: 'en',
      duration: 1.5,
      words: [
        { word: 'hello', start: 0.1, end: 0.5 },
        { word: 'world', start: 0.6, end: 1.0 },
      ],
    }

    global.fetch = mockResolvedJson(mockResult)

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('字词级时间戳')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('hello')).toBeInTheDocument()
      expect(screen.getByText('world')).toBeInTheDocument()
    })
  })

  it('shows language and duration info', async () => {
    const mockResult = {
      text: 'test transcription',
      language: 'en',
      duration: 2.34,
    }

    global.fetch = mockResolvedJson(mockResult)

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText(/语言: en/)).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText(/时长:/)).toBeInTheDocument()
    })
  })

  it('shows loading state during transcription', async () => {
    let resolvePromise: (value: any) => void

    global.fetch = vi.fn().mockImplementation(
      () => new Promise(resolve => { resolvePromise = resolve })
    )

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('转录中...')).toBeInTheDocument()
    })

    if (resolvePromise) {
      resolvePromise({
        ok: true,
        json: () => Promise.resolve({ text: 'done', language: 'en', duration: 1.0 }),
      })
    }
  })

  it('disables button during loading', async () => {
    let resolvePromise: (value: any) => void

    global.fetch = vi.fn().mockImplementation(
      () => new Promise(resolve => { resolvePromise = resolve })
    )

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      const button = screen.getByText('转录中...')
      expect(button).toBeDisabled()
    })

    if (resolvePromise) {
      resolvePromise({
        ok: true,
        json: () => Promise.resolve({ text: 'done', language: 'en', duration: 1.0 }),
      })
    }
  })

  it('shows error toast on transcription failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('ASR model error'),
    })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('ASR API error: ASR model error')).toBeInTheDocument()
    })
  })

  it('resets loading state after transcription completes', async () => {
    global.fetch = mockResolvedJson({ text: 'done', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('done')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('开始转录')).toBeInTheDocument()
    })
  })

  it('does not show result before transcription', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    expect(screen.queryByText('转录文本')).not.toBeInTheDocument()
  })

  it('shows transcription label in result', async () => {
    global.fetch = mockResolvedJson({ text: 'hello world', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('转录文本')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('hello world')).toBeInTheDocument()
    })
  })

  it('word timestamps show start and end times with s suffix', async () => {
    const mockResult = {
      text: 'hi',
      words: [
        { word: 'hi', start: 0.123, end: 0.456 },
      ],
    }

    global.fetch = mockResolvedJson(mockResult)

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('0.12s')).toBeInTheDocument()
      expect(screen.getByText('0.46s')).toBeInTheDocument()
    })
  })

  it('does not show word timestamps section when no words', async () => {
    global.fetch = mockResolvedJson({ text: 'hello', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('hello')).toBeInTheDocument()
    })

    expect(screen.queryByText('字词级时间戳')).not.toBeInTheDocument()
  })

  it('file input accepts audio files only', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    expect(fileInput).toHaveAttribute('accept', 'audio/*')
  })

  it('transcribes with verbose_json format', async () => {
    global.fetch = mockResolvedJson({ text: 'test', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
      const [url, config] = (global.fetch as any).mock.calls[0]
      expect(url).toContain('/v1/audio/transcriptions')
      expect(url).toContain('response_format=verbose_json')

      const formData = config.body as FormData
      expect(formData.get('file')).toBeDefined()
    })
  })

  it('handles empty file gracefully', () => {
    render(<ASRPanel />, { wrapper: TestWrapper })

    const button = screen.getByText('开始转录')
    expect(button).toBeDisabled()
  })

  it('result text is displayed in a styled container', async () => {
    global.fetch = mockResolvedJson({ text: 'test result', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('test result')).toBeInTheDocument()
    })

    const textEl = screen.getByText('test result')
    const pEl = textEl.closest('p')
    expect(pEl).toHaveClass('bg-gray-50')
  })

  it('multiple word timestamps render in order', async () => {
    const mockResult = {
      text: 'one two three',
      words: [
        { word: 'one', start: 0.1, end: 0.3 },
        { word: 'two', start: 0.4, end: 0.6 },
        { word: 'three', start: 0.7, end: 1.0 },
      ],
    }

    global.fetch = mockResolvedJson(mockResult)

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('one')).toBeInTheDocument()
      expect(screen.getByText('two')).toBeInTheDocument()
      expect(screen.getByText('three')).toBeInTheDocument()
    })
  })

  it('button text changes to loading during transcription', async () => {
    let resolvePromise: (value: any) => void

    global.fetch = vi.fn().mockImplementation(
      () => new Promise(resolve => { resolvePromise = resolve })
    )

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file = new File(['test audio data'], 'test.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.queryByText('开始转录')).not.toBeInTheDocument()
    })

    expect(screen.getByText('转录中...')).toBeInTheDocument()

    if (resolvePromise) {
      resolvePromise({
        ok: true,
        json: () => Promise.resolve({ text: 'done', language: 'en', duration: 1.0 }),
      })
    }
  })

  it('clears result after new transcription', async () => {
    global.fetch = mockResolvedJson({ text: 'first result', language: 'en', duration: 1.0 })

    render(<ASRPanel />, { wrapper: TestWrapper })

    const fileInput = screen.getByText('上传音频').closest('div')!.querySelector('input[type="file"]')
    const file1 = new File(['audio 1'], 'test1.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file1)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('first result')).toBeInTheDocument()
    })

    // Upload a new file with different result
    global.fetch = mockResolvedJson({ text: 'second result', language: 'en', duration: 2.0 })

    const file2 = new File(['audio 2'], 'test2.wav', { type: 'audio/wav' })
    userEvent.upload(fileInput, file2)

    await waitFor(() => {
      const button = screen.getByText('开始转录')
      expect(button).toBeEnabled()
    })

    userEvent.click(screen.getByText('开始转录'))

    await waitFor(() => {
      expect(screen.getByText('second result')).toBeInTheDocument()
      expect(screen.queryByText('first result')).not.toBeInTheDocument()
    })
  })
})

function mockResolvedJson(data: any) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
  })
}
