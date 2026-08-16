'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { navItems } from '@/lib/nav';
import { Icon } from '@/components/ui/Icon';

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className="mobile-tab-bar fixed inset-x-0 bottom-0 z-40 border-t border-white/[0.06] bg-zinc-950/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-2xl lg:hidden"
    >
      <div className="flex items-stretch">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive ? 'page' : undefined}
              className={`relative flex flex-1 flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors ${
                isActive ? 'text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {isActive && (
                <span className="absolute inset-x-5 top-0 h-0.5 rounded-full bg-gradient-to-r from-violet-400 to-fuchsia-500" />
              )}
              <Icon name={item.icon} className={`h-[22px] w-[22px] ${isActive ? 'text-violet-300' : ''}`} />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
