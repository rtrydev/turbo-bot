export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-shimmer rounded-xl bg-[linear-gradient(110deg,rgba(255,255,255,0.03)_40%,rgba(255,255,255,0.09)_50%,rgba(255,255,255,0.03)_60%)] bg-[length:200%_100%] ${className}`}
    />
  );
}
