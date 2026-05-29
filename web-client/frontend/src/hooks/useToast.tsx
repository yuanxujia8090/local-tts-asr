import { useState, createContext, useContext, useCallback } from 'react'

type ToastType = 'error' | 'success' | 'info'

interface Toast {
  id: number
  message: string
  type: ToastType
}

const ToastContext = createContext<{
  toasts: Toast[]
  showToast: (message: string, type?: ToastType) => void
}>({ toasts: [], showToast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

let toastId = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: string, type: ToastType = 'error') => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 5000)
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, showToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded shadow-lg text-sm max-w-md ${
              toast.type === 'error' ? 'bg-red-600 text-white' :
              toast.type === 'success' ? 'bg-green-600 text-white' :
              'bg-blue-600 text-white'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
