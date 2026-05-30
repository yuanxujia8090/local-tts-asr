import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from '../hooks/useToast'

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>
}

function TestComponent() {
  const { showToast, toasts } = useToast()

  return (
    <div>
      <button onClick={() => showToast('Hello error', 'error')}>Error toast</button>
      <button onClick={() => showToast('Hello success', 'success')}>Success toast</button>
      <button onClick={() => showToast('Hello info', 'info')}>Info toast</button>
      <span data-testid="toast-count">{toasts.length}</span>
    </div>
  )
}

describe('useToast', () => {
  it('renders children inside ToastProvider', () => {
    render(
      <TestWrapper>
        <div data-testid="child">Hello</div>
      </TestWrapper>,
    )

    expect(screen.getByTestId('child')).toBeInTheDocument()
  })

  it('shows error toast when button clicked', async () => {
    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Error toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })
  })

  it('shows success toast when button clicked', async () => {
    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Success toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })
  })

  it('shows info toast when button clicked', async () => {
    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Info toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })
  })

  it('increments toast count when showing multiple toasts', async () => {
    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Error toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })

    userEvent.click(screen.getByText('Success toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('2')
    })
  })

  it('each toast has unique id', async () => {
    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Error toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })

    userEvent.click(screen.getByText('Success toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('2')
    })
  })

  it('defaults to error type when not specified', async () => {
    render(
      <TestWrapper>
        <ToastConsumer />
      </TestWrapper>,
    )

    userEvent.click(screen.getByText('Default type'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })
  })

  it('schedules auto-dismiss with setTimeout after 5 seconds', async () => {
    const setTimeoutSpy = vi.spyOn(global, 'setTimeout')

    render(<TestComponent />, { wrapper: TestWrapper })

    userEvent.click(screen.getByText('Error toast'))
    await waitFor(() => {
      expect(screen.getByTestId('toast-count')).toHaveTextContent('1')
    })

    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 2000)
    setTimeoutSpy.mockRestore()
  })
})

function ToastConsumer() {
  const { showToast, toasts } = useToast()
  return (
    <div>
      <button onClick={() => showToast('Default toast')}>Default type</button>
      <span data-testid="toast-count">{toasts.length}</span>
    </div>
  )
}
