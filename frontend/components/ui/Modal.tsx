'use client';

import { useEffect } from 'react';
import { Button } from './Button';
import { Icon, type IconName } from './Icon';

export interface ModalProps {
  open: boolean;
  title: string;
  description?: string;
  icon?: IconName;
  tone?: 'primary' | 'danger';
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function Modal({
  open,
  title,
  description,
  icon,
  tone = 'primary',
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  loading,
  onConfirm,
  onClose,
}: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 animate-fade-in bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-sm animate-scale-in rounded-2xl bg-zinc-900/95 p-5 shadow-2xl shadow-black/60 ring-1 ring-white/[0.1]">
        <div className="flex items-start gap-3.5">
          {icon && (
            <span
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                tone === 'danger'
                  ? 'bg-red-500/[0.12] text-red-300 ring-1 ring-red-500/25'
                  : 'bg-violet-500/[0.12] text-violet-300 ring-1 ring-violet-500/25'
              }`}
            >
              <Icon name={icon} className="h-5 w-5" />
            </span>
          )}
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-white">{title}</h3>
            {description && <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{description}</p>}
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2.5">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={tone === 'danger' ? 'danger' : 'primary'}
            size="sm"
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
