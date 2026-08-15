import type { QueueStateDTO } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Icon } from '@/components/ui/Icon';
import { Equalizer } from '@/components/ui/Equalizer';
import { StatusPill, type PlaybackState } from '@/components/ui/StatusPill';

export function playbackState(queue: QueueStateDTO | null): PlaybackState {
  if (!queue) return 'stopped';
  if (queue.is_playing) return 'playing';
  if (queue.is_paused) return 'paused';
  return 'stopped';
}

export function NowPlaying({ queue }: { queue: QueueStateDTO }) {
  const song = queue.currently_playing;
  if (!song) return null;
  const state = playbackState(queue);

  return (
    <Card className="p-5">
      <div className="flex items-center gap-4">
        <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/30 to-fuchsia-500/30 ring-1 ring-white/10">
          <Icon name="music" className="h-5 w-5 text-violet-200" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
            Now playing
          </p>
          <p className="mt-0.5 truncate text-sm font-medium text-white">{song.title}</p>
          <p className="truncate text-xs text-zinc-500">{song.origin}</p>
        </div>
        <span className={state === 'playing' ? 'text-violet-300' : 'text-zinc-600'}>
          <Equalizer active={state === 'playing'} />
        </span>
        <StatusPill state={state} />
      </div>
    </Card>
  );
}
