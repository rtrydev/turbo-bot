'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast';
import type { QueueStateDTO, SongDTO } from '@/lib/types';
import { formatDuration } from '@/lib/format';
import { PageHeader } from '@/components/PageHeader';
import { NowPlaying } from '@/components/NowPlaying';
import { TransportBar } from '@/components/TransportBar';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';

export default function QueuePage() {
  const [queue, setQueue] = useState<QueueStateDTO | null>(null);
  const [url, setUrl] = useState('');
  const [randomCount, setRandomCount] = useState(10);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [randomBusy, setRandomBusy] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const q = await api.getQueue();
        if (!cancelled) setQueue(q);
      } catch {
        // Silently handle polling errors
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const handleAddSong = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setAdding(true);
    try {
      await api.addSong(url.trim());
      showToast('Song added to queue', 'success');
      setUrl('');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to add song', 'error');
    } finally {
      setAdding(false);
    }
  };

  const handleAddRandom = async () => {
    setRandomBusy(true);
    try {
      await api.addRandomSongs(randomCount);
      showToast(`Added ${randomCount} random songs`, 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to add random songs', 'error');
    } finally {
      setRandomBusy(false);
    }
  };

  if (loading) return <QueueSkeleton />;

  const songCount = queue?.songs.length ?? 0;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Queue"
        subtitle="Add tracks and control playback"
        action={
          <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-medium text-zinc-300 ring-1 ring-white/[0.08]">
            {songCount} {songCount === 1 ? 'track' : 'tracks'} in queue
          </span>
        }
      />

      <Card className="animate-fade-up p-5">
        <form onSubmit={handleAddSong} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Icon name="link" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a YouTube URL…"
              className="h-11 w-full rounded-xl bg-white/[0.04] pl-10 pr-4 text-sm text-white ring-1 ring-white/[0.08] transition-all placeholder:text-zinc-600 focus:bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-violet-500/60"
            />
          </div>
          <Button type="submit" variant="primary" size="lg" icon="plus" loading={adding} disabled={!url.trim()}>
            Add to queue
          </Button>
        </form>

        <div className="mt-4 flex flex-col gap-3 border-t border-white/[0.06] pt-4 sm:flex-row sm:items-center">
          <p className="flex-1 text-sm text-zinc-400">
            Nothing in mind? Add a batch of{' '}
            <span className="font-medium text-zinc-200">random tracks</span> from your library.
          </p>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              max={50}
              value={randomCount}
              onChange={(e) => setRandomCount(Math.max(1, parseInt(e.target.value) || 1))}
              className="h-9 w-20 rounded-lg bg-white/[0.04] text-center text-sm text-white ring-1 ring-white/[0.08] outline-none transition-all focus:ring-2 focus:ring-violet-500/60"
            />
            <Button variant="ghost" icon="shuffle" loading={randomBusy} onClick={handleAddRandom}>
              Add random
            </Button>
          </div>
        </div>
      </Card>

      <div className="animate-fade-up" style={{ animationDelay: '70ms' }}>
        <TransportBar queue={queue} />
      </div>

      {queue?.currently_playing && (
        <div className="animate-fade-up" style={{ animationDelay: '140ms' }}>
          <NowPlaying queue={queue} />
        </div>
      )}

      <div className="animate-fade-up" style={{ animationDelay: '210ms' }}>
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between px-5 pb-3 pt-4">
            <h3 className="text-sm font-semibold text-white">Up next</h3>
            <span className="font-mono text-xs text-zinc-500">
              {songCount} {songCount === 1 ? 'track' : 'tracks'}
            </span>
          </div>
          {songCount > 0 ? (
            <div className="max-h-[28rem] divide-y divide-white/[0.05] overflow-y-auto">
              {queue!.songs.map((song, i) => (
                <QueueRow key={song.id} song={song} index={i + 1} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon="list"
              title="Queue is empty"
              description="Add a YouTube link above to start the party."
            />
          )}
        </Card>
      </div>
    </div>
  );
}

function QueueRow({ song, index }: { song: SongDTO; index: number }) {
  return (
    <div className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-white/[0.03]">
      <span className="w-6 text-right font-mono text-[11px] text-zinc-600">{index}</span>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] ring-1 ring-white/[0.06]">
        <Icon name="music" className="h-4 w-4 text-zinc-400" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-zinc-100">{song.title}</p>
        <p className="truncate text-xs text-zinc-500">{song.origin}</p>
      </div>
      <span className="font-mono text-xs text-zinc-500">{formatDuration(song.length)}</span>
    </div>
  );
}

function QueueSkeleton() {
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="space-y-2">
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-4 w-64" />
      </div>
      <Skeleton className="h-40 w-full rounded-2xl" />
      <Skeleton className="h-24 w-full rounded-2xl" />
      <Skeleton className="h-96 w-full rounded-2xl" />
    </div>
  );
}
