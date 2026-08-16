'use client';

import { useConnectionStatus } from '@/lib/status';
import { Icon } from '@/components/ui/Icon';

export function MobileHeader() {
  const status = useConnectionStatus();
  const connected = status?.connected ?? false;

  return (
    <header className="mobile-header shrink-0 border-b border-white/[0.06] bg-zinc-950/70 backdrop-blur-2xl lg:hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-600 shadow-lg shadow-fuchsia-500/25">
            <Icon name="bolt" className="h-4 w-4 text-white" />
            <span className="pointer-events-none absolute inset-0 rounded-lg ring-1 ring-white/25" />
          </div>
          <p className="truncate text-[15px] font-semibold tracking-tight text-white">
            Turbo{' '}
            <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              Bot
            </span>
          </p>
        </div>

        <span
          className={`flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ${
            connected
              ? 'bg-emerald-500/[0.08] text-emerald-300 ring-emerald-500/25'
              : 'bg-red-500/[0.08] text-red-300 ring-red-500/25'
          }`}
        >
          <span className="relative flex h-1.5 w-1.5">
            {connected && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            )}
            <span className={`relative h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          </span>
          {connected ? 'Online' : 'Offline'}
        </span>
      </div>
    </header>
  );
}
