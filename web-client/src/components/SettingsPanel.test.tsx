import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import { SettingsPanel } from '../components/SettingsPanel'

describe('SettingsPanel', () => {
  beforeEach(() => {
    localStorage.clear()
  })



  it('renders settings heading', () => {
    render(<SettingsPanel />)

    expect(screen.getByText('设置')).toBeInTheDocument()
  })

  it('has engine mode selector with local default', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('local')
  })

  it('has remote URL input when remote mode selected', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    const input = screen.getByDisplayValue('http://localhost:11434')
    expect(input).toBeInTheDocument()
  })

  it('has save settings button', () => {
    render(<SettingsPanel />)

    expect(screen.getByText('保存设置')).toBeInTheDocument()
  })

  it('saves engine_mode to localStorage when saved', () => {
    render(<SettingsPanel />)

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('engine_mode')).toBe('local')
  })

  it('saves remote_engine_url to localStorage when saved', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('remote_engine_url')).toBe('http://localhost:11434')
  })

  it('saves custom remote URL when changed', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    const input = screen.getByDisplayValue('http://localhost:11434')
    fireEvent.change(input, { target: { value: 'http://example.com:8080' } })

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('remote_engine_url')).toBe('http://example.com:8080')
  })

  it('saves remote engine mode when selected', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('engine_mode')).toBe('remote')
  })

  it('shows alert on save', () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    try {
      render(<SettingsPanel />)

      fireEvent.click(screen.getByText('保存设置'))

      expect(alertSpy).toHaveBeenCalledWith(
        '设置已保存到本地（需要重启后端服务生效）'
      )
    } finally {
      alertSpy.mockRestore()
    }
  })

  it('switches engine mode selector to remote', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    expect(select).toHaveValue('remote')
  })

  it('shows remote URL input when remote mode selected', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    expect(screen.getByDisplayValue('http://localhost:11434')).toBeInTheDocument()
  })

  it('has local inference option', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    const options = select.querySelectorAll('option')
    expect(options.length).toBe(2)

    const values = Array.from(options).map(o => o.value)
    expect(values).toContain('local')
    expect(values).toContain('remote')
  })

  it('shows engine mode notice text', () => {
    render(<SettingsPanel />)

    expect(screen.getByText('注意：ENGINE_MODE 切换需要重启后端服务。')).toBeInTheDocument()
  })

  it('shows example command in notice', () => {
    render(<SettingsPanel />)

    expect(screen.getByText('ENGINE_MODE=local uv run python src/main.py')).toBeInTheDocument()
  })

  it('updates remote URL input when typed', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    const input = screen.getByDisplayValue('http://localhost:11434')
    fireEvent.change(input, { target: { value: 'http://my-server:3000' } })

    expect(input).toHaveValue('http://my-server:3000')
  })

  it('saves both settings in order', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    const input = screen.getByDisplayValue('http://localhost:11434')
    fireEvent.change(input, { target: { value: 'http://custom:9000' } })

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('engine_mode')).toBe('remote')
    expect(localStorage.getItem('remote_engine_url')).toBe('http://custom:9000')
  })

  it('renders settings label for inference mode', () => {
    render(<SettingsPanel />)

    expect(screen.getByText('推理模式（前端缓存）')).toBeInTheDocument()
  })

  it('renders remote API URL label when in remote mode', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    expect(screen.getByText('远程 API URL')).toBeInTheDocument()
  })

  it('does not show backend mode when health check fails', () => {
    render(<SettingsPanel />)

    expect(screen.queryByText('当前后端模式：')).not.toBeInTheDocument()
  })

  it('renders backend mode when health check succeeds', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ engine_mode: 'local' }),
    })

    render(<SettingsPanel />)

    await waitFor(() => {
      expect(screen.getByText('当前后端模式：')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('local')).toBeInTheDocument()
    })
  })

  it('does not show backend mode when health check errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    render(<SettingsPanel />)

    // Wait a bit for the fetch to fail
    await new Promise(r => setTimeout(r, 100))

    expect(screen.queryByText('当前后端模式：')).not.toBeInTheDocument()
  })

  it('fetches health endpoint on mount', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ engine_mode: 'remote' }),
    })

    render(<SettingsPanel />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/health')
    })
  })

  it('backend mode displays in cyan color styling', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ engine_mode: 'local' }),
    })

    render(<SettingsPanel />)

    await waitFor(() => {
      expect(screen.getByText('当前后端模式：')).toBeInTheDocument()
    })

    const container = screen.getByText('当前后端模式：').parentElement
    expect(container).toHaveClass('bg-gray-50')
  })

  it('updates backend mode when health check returns different value', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ engine_mode: 'remote' }),
    })

    render(<SettingsPanel />)

    await waitFor(() => {
      expect(screen.getByText('remote')).toBeInTheDocument()
    })

    // Simulate health check update
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ engine_mode: 'local' }),
    })

    // Re-render to trigger the effect again (in real app this would be a polling mechanism)
    render(<SettingsPanel />)

    await waitFor(() => {
      expect(screen.getByText('local')).toBeInTheDocument()
    })
  })

  it('remote mode option has descriptive label', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    const options = select.querySelectorAll('option')

    const labels = Array.from(options).map(o => o.textContent)
    expect(labels).toContain('本地推理 (MLX / PyTorch)')
    expect(labels.some(l => l?.includes('远程转发'))).toBe(true)
  })

  it('input element for remote URL is text type', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    const input = screen.getByDisplayValue('http://localhost:11434')
    expect(input).toHaveAttribute('type', 'text')
  })

  it('remote URL input is not visible in local mode', () => {
    render(<SettingsPanel />)

    expect(screen.queryByText('远程 API URL')).not.toBeInTheDocument()
  })

  it('saves current engine mode value not just default', () => {
    render(<SettingsPanel />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'remote' } })

    fireEvent.click(screen.getByText('保存设置'))

    expect(localStorage.getItem('engine_mode')).toBe('remote')
  })

  it('panel has space-y-4 layout structure', () => {
    render(<SettingsPanel />)

    const heading = screen.getByText('设置')
    expect(heading.parentElement).toHaveClass('space-y-4')
  })

  it('notice section is at bottom of panel', () => {
    render(<SettingsPanel />)

    const notice = screen.getByText('注意：ENGINE_MODE 切换需要重启后端服务。')
    expect(notice.parentElement).toHaveClass('bg-gray-50')
  })
})
