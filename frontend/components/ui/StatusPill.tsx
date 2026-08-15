export type PlaybackState = 'playing' | 'paused' | 'stopped';

const PILL: Record<PlaybackState, { label: string; cls: string }> = {
  playing: { label: 'Playing', cls: 'bg-emerald-500/[0.1] text-emerald-300 ring-emerald-500/25' },
  paused: { label: 'Paused', cls: 'bg-amber-500/[0.1] text-amber-300 ring-amber-500/25' },
  stopped: { label: 'Stopped', cls: 'bg-white/[0.05] text-zinc-400 ring-white/[0.1]' },
};

export function StatusPill({ state }: { state: PlaybackState }) {
  const pill = PILL[state];
  return (
    <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ${pill.cls}`}>
      {pill.label}
    </span>
  );
}
