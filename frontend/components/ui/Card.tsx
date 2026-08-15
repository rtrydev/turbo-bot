import type { HTMLAttributes } from 'react';

export function Card({ className = '', ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-2xl bg-white/[0.03] ring-1 ring-white/[0.07] backdrop-blur-xl ${className}`}
      {...rest}
    />
  );
}
