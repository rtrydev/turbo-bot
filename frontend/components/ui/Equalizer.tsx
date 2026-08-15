const BAR_HEIGHTS = [55, 90, 45, 100, 60];

export function Equalizer({ active, className = '' }: { active: boolean; className?: string }) {
  return (
    <span className={`flex h-3.5 items-end gap-[2.5px] ${className}`} aria-hidden="true">
      {BAR_HEIGHTS.map((height, i) => (
        <span
          key={i}
          className={`w-[3px] origin-bottom rounded-full bg-current ${active ? 'animate-eq' : ''}`}
          style={{
            height: `${height}%`,
            animationDelay: active ? `${i * 130}ms` : undefined,
            transform: active ? undefined : 'scaleY(0.55)',
          }}
        />
      ))}
    </span>
  );
}
