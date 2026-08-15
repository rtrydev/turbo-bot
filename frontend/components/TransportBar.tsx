'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast';
import type { QueueStateDTO } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Icon, type IconName } from '@/components/ui/Icon';

interface TransportBarProps {
  queue: QueueStateDTO | null;
}

export function TransportBar({ queue }: TransportBarProps) {
  const { showToast } = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const [clearing, setClearing] = useState(false);

  const run = async (key: string, fn: () => Promise<unknown>, ok: string) => {
    setBusy(key);
    try {
      await fn();
      showToast(ok, 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Action failed', 'error');
    } finally {
      setBusy(null);
    }
  };

  const isPlaying = queue?.is_playing ?? false;
  const isPaused = queue?.is_paused ?? false;
  const queueLength = queue?.songs.length ?? 0;

  const handleMain = () => {
    if (isPlaying) return run('main', api.pausePlayback, 'Playback paused');
    if (isPaused) return run('main', api.resumePlayback, 'Playback resumed');
    return run('main', api.startPlayback, 'Playback started');
  };

  const handleClear = async () => {
    setClearing(true);
    try {
      await api.clearQueue();
      showToast('Queue cleared', 'success');
      setConfirmClear(false);
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to clear queue', 'error');
    } finally {
      setClearing(false);
    }
  };

  return (
    <>
      <Card className="p-5">
        <div className="flex flex-col items-center justify-between gap-5 lg:flex-row">
          <div className="flex items-center gap-5">
            <ControlButton
              icon="skip"
              label="Skip"
              onClick={() => run('skip', api.skipSong, 'Skipped to next song')}
              busy={busy === 'skip'}
            />
            <button
              onClick={handleMain}
              disabled={busy !== null}
              aria-label={isPlaying ? 'Pause' : 'Play'}
              className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white shadow-xl shadow-fuchsia-500/25 transition-all duration-200 hover:shadow-fuchsia-500/45 hover:brightness-110 active:scale-95 disabled:pointer-events-none disabled:opacity-60"
            >
              <span className="pointer-events-none absolute inset-0 rounded-full ring-1 ring-white/25" />
              <Icon name={isPlaying ? 'pause' : 'play'} className={`h-6 w-6 ${isPlaying ? '' : 'translate-x-0.5'}`} />
            </button>
            <ControlButton
              icon="repeat"
              label="Repeat"
              active={queue?.repeat_enabled}
              onClick={() => run('repeat', api.toggleRepeat, queue?.repeat_enabled ? 'Repeat off' : 'Repeat on')}
              busy={busy === 'repeat'}
            />
          </div>

          <div className="hidden h-10 w-px bg-white/[0.07] lg:block" />

          <div className="flex items-center gap-4">
            <div className="text-center lg:text-right">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">Status</p>
              <p className="mt-0.5 text-sm font-medium">
                {isPlaying ? (
                  <span className="text-emerald-300">Playing</span>
                ) : isPaused ? (
                  <span className="text-amber-300">Paused</span>
                ) : (
                  <span className="text-zinc-400">Stopped</span>
                )}
              </p>
            </div>
            <Button
              variant="dangerGhost"
              size="sm"
              icon="trash"
              onClick={() => setConfirmClear(true)}
              disabled={busy !== null || queueLength === 0}
            >
              Clear queue
            </Button>
          </div>
        </div>
      </Card>

      <Modal
        open={confirmClear}
        tone="danger"
        icon="trash"
        title="Clear the queue?"
        description="This removes every queued track. The song that is currently playing keeps playing."
        confirmLabel="Clear queue"
        loading={clearing}
        onConfirm={handleClear}
        onClose={() => setConfirmClear(false)}
      />
    </>
  );
}

function ControlButton({
  icon,
  label,
  onClick,
  active,
  busy,
}: {
  icon: IconName;
  label: string;
  onClick: () => void;
  active?: boolean;
  busy?: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <button
        onClick={onClick}
        disabled={busy}
        className={`flex h-11 w-11 items-center justify-center rounded-full transition-all duration-200 active:scale-95 disabled:pointer-events-none disabled:opacity-60 ${
          active
            ? 'bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white shadow-lg shadow-fuchsia-500/30'
            : 'bg-white/[0.04] text-zinc-300 ring-1 ring-white/[0.08] hover:bg-white/[0.09] hover:text-white'
        }`}
      >
        <Icon name={icon} className="h-[18px] w-[18px]" />
      </button>
      <span className={`text-[10px] font-semibold uppercase tracking-wider ${active ? 'text-violet-300' : 'text-zinc-600'}`}>
        {label}
      </span>
    </div>
  );
}
