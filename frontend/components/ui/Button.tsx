'use client';

import type { ButtonHTMLAttributes, ReactNode } from 'react';
import Link from 'next/link';
import { Icon, type IconName } from './Icon';

type Variant = 'primary' | 'ghost' | 'danger' | 'dangerGhost';
type Size = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  href?: string;
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white shadow-lg shadow-fuchsia-500/20 hover:shadow-fuchsia-500/40 hover:brightness-110',
  ghost:
    'bg-white/[0.04] text-zinc-200 ring-1 ring-white/[0.08] hover:bg-white/[0.09] hover:text-white',
  danger: 'bg-red-600 text-white shadow-lg shadow-red-600/20 hover:bg-red-500',
  dangerGhost:
    'bg-red-500/[0.08] text-red-300 ring-1 ring-red-500/25 hover:bg-red-500/[0.16] hover:text-red-200',
};

const sizeClasses: Record<Size, string> = {
  sm: 'h-8 gap-1.5 rounded-lg px-3 text-xs',
  md: 'h-9 gap-2 rounded-lg px-4 text-sm',
  lg: 'h-11 gap-2 rounded-xl px-5 text-sm',
};

const baseClasses =
  'inline-flex items-center justify-center font-medium transition-all duration-200 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50';

function Content({
  icon,
  iconRight,
  loading,
  children,
}: {
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  children: ReactNode;
}) {
  return (
    <>
      {loading ? (
        <Icon name="loader" className="h-4 w-4 animate-spin" />
      ) : (
        icon && <Icon name={icon} className="h-4 w-4" />
      )}
      {children}
      {iconRight && !loading && <Icon name={iconRight} className="h-4 w-4" />}
    </>
  );
}

export function Button({
  variant = 'ghost',
  size = 'md',
  icon,
  iconRight,
  loading,
  disabled,
  href,
  className = '',
  children,
  ...rest
}: ButtonProps) {
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

  if (href) {
    return (
      <Link href={href} className={classes}>
        <Content icon={icon} iconRight={iconRight} loading={loading}>
          {children}
        </Content>
      </Link>
    );
  }

  return (
    <button disabled={disabled || loading} className={classes} {...rest}>
      <Content icon={icon} iconRight={iconRight} loading={loading}>
        {children}
      </Content>
    </button>
  );
}
