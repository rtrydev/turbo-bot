'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { navItems } from '@/lib/nav';
import { useConnectionStatus } from '@/lib/status';
import { Icon } from '@/components/ui/Icon';

export default function Sidebar() {
  const pathname = usePathname();
  const status = useConnectionStatus();
  const connected = status?.connected ?? false;

  return (
    <aside className="hidden h-full w-64 shrink-0 flex-col border-r border-white/[0.06] bg-zinc-950/70 backdrop-blur-2xl lg:flex">
      <div className="px-5 pb-5 pt-6">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 shadow-lg shadow-fuchsia-500/25">
            <Icon name="bolt" className="h-5 w-5 text-white" />
            <span className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-white/25" />
          </div>
          <div className="min-w-0">
            <h1 className="text-[15px] font-semibold leading-tight tracking-tight text-white">
              Turbo{' '}
              <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
                Bot
              </span>
            </h1>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Admin console
            </p>
          </div>
        </div>
      </div>

      <div className="mx-5 h-px bg-white/[0.06]" />

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
          Navigation
        </p>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-white/[0.07] text-white ring-1 ring-white/[0.08]'
                  : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-gradient-to-b from-violet-400 to-fuchsia-500" />
              )}
              <Icon
                name={item.icon}
                className={`h-[18px] w-[18px] transition-colors ${
                  isActive ? 'text-violet-300' : 'text-zinc-500 group-hover:text-zinc-300'
                }`}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4">
        <div className="flex items-center gap-2.5 rounded-xl bg-white/[0.03] px-3.5 py-3 ring-1 ring-white/[0.06]">
          <span className="relative flex h-2 w-2 shrink-0">
            {connected && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
            )}
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                connected ? 'bg-emerald-400' : 'bg-red-400'
              }`}
            />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-zinc-200">
              {connected ? (status?.channel_name || 'Connected') : 'Disconnected'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
