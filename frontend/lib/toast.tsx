'use client';

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import { Icon, type IconName } from '@/components/ui/Icon';

export type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

let toastId = 0;

const toastMeta: Record<ToastType, { icon: IconName; cls: string }> = {
  success: { icon: 'check', cls: 'bg-emerald-500/[0.15] text-emerald-300' },
  error: { icon: 'alert', cls: 'bg-red-500/[0.15] text-red-300' },
  info: { icon: 'info', cls: 'bg-violet-500/[0.15] text-violet-300' },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = `toast-${++toastId}`;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, removeToast }}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex w-[22rem] max-w-[calc(100vw-2.5rem)] flex-col gap-2">
        {toasts.map((toast) => (
          <button
            key={toast.id}
            onClick={() => removeToast(toast.id)}
            className="pointer-events-auto flex animate-toast-in items-center gap-3 rounded-xl bg-zinc-900/90 px-4 py-3 text-left shadow-2xl shadow-black/50 ring-1 ring-white/[0.1] backdrop-blur-xl"
          >
            <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${toastMeta[toast.type].cls}`}>
              <Icon name={toastMeta[toast.type].icon} className="h-3.5 w-3.5" />
            </span>
            <span className="flex-1 text-sm text-zinc-100">{toast.message}</span>
            <Icon name="x" className="h-3.5 w-3.5 shrink-0 text-zinc-600" />
          </button>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
