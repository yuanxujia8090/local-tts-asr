import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import Dashboard from '../pages/Dashboard'
import { ToastProvider } from '../hooks/useToast'

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>
}

describe('Dashboard', () => {
  it('renders TTS panel by default', () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.getByText('TTS 合成测试')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入要合成的文本...')).toBeInTheDocument()
  })

  it('switches to ASR panel when clicked', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.queryByText('ASR 转录测试')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('ASR 转录'))
    await waitFor(() => {
      expect(screen.getByText('ASR 转录测试')).toBeInTheDocument()
    })
  })

  it('switches to settings panel when clicked', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.queryByText('推理模式（前端缓存）')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.getByText('推理模式（前端缓存）')).toBeInTheDocument()
    })
  })

  it('switches back to TTS panel when clicked', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('ASR 转录'))
    await waitFor(() => {
      expect(screen.getByText('ASR 转录测试')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('TTS 合成'))
    await waitFor(() => {
      expect(screen.getByText('TTS 合成测试')).toBeInTheDocument()
    })
  })

  it('highlights active tab with cyan styling', () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    const buttons = screen.getAllByText(/^(TTS 合成|ASR 转录|设置)$/).filter(
      el => el.tagName === 'BUTTON'
    )

    const ttsButton = buttons[0]
    const asrButton = buttons[1]
    const settingsButton = buttons[2]

    expect(ttsButton).toHaveClass('text-cyan-400')
    expect(asrButton).toHaveClass('text-gray-400')
    expect(settingsButton).toHaveClass('text-gray-400')

    fireEvent.click(asrButton)
    expect(asrButton).toHaveClass('text-cyan-400')
    expect(ttsButton).toHaveClass('text-gray-400')

    fireEvent.click(settingsButton)
    expect(settingsButton).toHaveClass('text-cyan-400')
    expect(asrButton).toHaveClass('text-gray-400')
  })

  it('shows page header', () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.getByText('Qwen3 Voice Service')).toBeInTheDocument()
    expect(screen.getByText('Local TTS/ASR Processing Center')).toBeInTheDocument()
  })

  it('all three tabs are visible', () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.getByText('TTS 合成')).toBeInTheDocument()
    expect(screen.getByText('ASR 转录')).toBeInTheDocument()
    expect(screen.getByText('设置')).toBeInTheDocument()
  })

  it('TTS panel renders with default speaker Vivian', () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    const voiceSelects = screen.getAllByRole('combobox')
    // First combobox is voice select (no mode select anymore, it's tabs)
    const voiceSelect = voiceSelects[0]
    expect(voiceSelect).toHaveValue('Vivian')
  })

  it('ASR panel has file upload input', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('ASR 转录'))
    await waitFor(() => {
      expect(screen.getByText('上传音频')).toBeInTheDocument()
    })

    const fileInputs = document.querySelectorAll('input[type="file"]')
    expect(fileInputs.length).toBeGreaterThan(0)
  })

  it('settings panel has engine mode selector', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.getByText('推理模式（前端缓存）')).toBeInTheDocument()
    })

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('local')
  })

  it('settings panel has save button', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.getByText('保存设置')).toBeInTheDocument()
    })
  })

  it('settings panel shows remote URL input when mode is remote', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.getByText('推理模式（前端缓存）')).toBeInTheDocument()
    })

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    expect(screen.getByDisplayValue('http://localhost:11434')).toBeInTheDocument()
  })

  it('settings panel does not show remote URL in local mode', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.queryByText('远程 API URL')).not.toBeInTheDocument()
    })
  })

  it('settings panel shows engine mode notice', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.getByText('注意：ENGINE_MODE 切换需要重启后端服务。')).toBeInTheDocument()
    })
  })

  it('only one panel visible at a time', async () => {
    render(<Dashboard />, { wrapper: TestWrapper })

    expect(screen.getByText('TTS 合成测试')).toBeInTheDocument()
    expect(screen.queryByText('ASR 转录测试')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('ASR 转录'))
    await waitFor(() => {
      expect(screen.queryByText('TTS 合成测试')).not.toBeInTheDocument()
    })
    expect(screen.getByText('ASR 转录测试')).toBeInTheDocument()

    fireEvent.click(screen.getByText('设置'))
    await waitFor(() => {
      expect(screen.queryByText('ASR 转录测试')).not.toBeInTheDocument()
    })
    expect(screen.getByText('推理模式（前端缓存）')).toBeInTheDocument()
  })
})
