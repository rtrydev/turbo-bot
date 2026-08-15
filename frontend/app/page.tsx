'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { ConnectionStatusDTO, QueueStateDTO } from '@/lib/types';
import { formatDuration } from '@/lib/format';
import { PageHeader } from '@/components/PageHeader';
import { playbackState } from '@/components/NowPlaying';
import { TransportBar } from '@/components/TransportBar';
import { Card } from '@/components/ui/Card';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Equalizer } from '@/components/ui/Equalizer';
import { StatusPill } from '@/components/ui/StatusPill';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';

export default function Dashboard() {
  const [queue, setQueue] = useState<QueueStateDTO | null>(null);
  const [status, setStatus] = useState<ConnectionStatusDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [q, s] = await Promise.all([api.getQueue(), api.getStatus()]);
        if (!cancelled) {
          setQueue(q);
          setStatus(s);
        }
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

  if (loading) return <DashboardSkeleton />;

  const song = queue?.currently_playing ?? null;
  const state = playbackState(queue);

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Dashboard"
        subtitle="Live overview of your bot"
        action={<ConnectionChip status={status} />}
      />

      {song ? (
        <Card className="relative animate-fade-up overflow-hidden p-6" style={{ animationDelay: '60ms' }}>
          <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-violet-600/[0.18] blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-fuchsia-600/[0.12] blur-3xl" />
          <div className="relative flex flex-col items-center gap-5 sm:flex-row sm:gap-6">
            <div className="relative shrink-0">
              <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-600 shadow-2xl shadow-fuchsia-500/25">
                <Icon name="music" className="h-10 w-10 text-white/90" />
              </div>
              <span className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-white/20" />
            </div>
            <div className="min-w-0 flex-1 text-center sm:text-left">
              <div className="flex items-center justify-center gap-3 sm:justify-start">
                <span className={state === 'playing' ? 'text-violet-300' : 'text-zinc-600'}>
                  <Equalizer active={state === 'playing'} />
                </span>
                <StatusPill state={state} />
              </div>
              <h3 className="mt-2.5 truncate text-xl font-semibold tracking-tight text-white">
                {song.title}
              </h3>
              <p className="mt-1 truncate text-sm text-zinc-400">
                {song.origin}
                <span className="mx-1.5 text-zinc-600">·</span>
                <span className="font-mono text-zinc-500">{formatDuration(song.length)}</span>
              </p>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="animate-fade-up" style={{ animationDelay: '60ms' }}>
          <EmptyState
            icon="music"
            title="Nothing is playing"
            description="Add a song to the queue to get the music going."
            action={
              <Button href="/queue" variant="primary" icon="plus">
                Open queue
              </Button>
            }
          />
        </Card>
      )}

      <div className="animate-fade-up" style={{ animationDelay: '120ms' }}>
        <TransportBar queue={queue} />
      </div>

      <div className="grid animate-fade-up gap-4 sm:grid-cols-3" style={{ animationDelay: '180ms' }}>
        <StatCard
          icon="wifi"
          label="Connection"
          value={
            status?.connected
              ? status.channel_name ?? 'Online'
              : 'Disconnected'
          }
          tone={status?.connected ? 'good' : 'bad'}
        />
        <StatCard
          icon="list"
          label="Queue depth"
          value={`${queue?.songs.length ?? 0} ${queue?.songs.length === 1 ? 'song' : 'songs'}`}
        />
        <StatCard
          icon="repeat"
          label="Repeat"
          value={queue?.repeat_enabled ? 'Enabled' : 'Disabled'}
          tone={queue?.repeat_enabled ? 'accent' : 'muted'}
        />
      </div>

      <div className="animate-fade-up" style={{ animationDelay: '240ms' }}>
        <UpNextCard queue={queue} />
      </div>
    </div>
  );
}

function ConnectionChip({ status }: { status: ConnectionStatusDTO | null }) {
  const connected = status?.connected ?? false;
  return (
    <div
      className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ${
        connected
          ? 'bg-emerald-500/[0.08] text-emerald-300 ring-emerald-500/25'
          : 'bg-red-500/[0.08] text-red-300 ring-red-500/25'
      }`}
    >
      <span className="relative flex h-1.5 w-1.5">
        {connected && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
        )}
        <span className={`relative h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
      </span>
      {connected ? (status?.channel_name ?? 'Online') : 'Offline'}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  tone = 'muted',
}: {
  icon: IconName;
  label: string;
  value: string;
  tone?: 'good' | 'bad' | 'accent' | 'muted';
}) {
  const toneCls = {
    good: 'text-emerald-300',
    bad: 'text-red-300',
    accent: 'text-violet-300',
    muted: 'text-zinc-100',
  }[tone];

  return (
    <Card className="flex items-center gap-3.5 p-4">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.05] ring-1 ring-white/[0.08]">
        <Icon name={icon} className={`h-4 w-4 ${toneCls}`} />
      </span>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">{label}</p>
        <p className={`mt-0.5 truncate text-sm font-medium ${toneCls}`}>{value}</p>
      </div>
    </Card>
  );
}

function UpNextCard({ queue }: { queue: QueueStateDTO | null }) {
  const songs = queue?.songs ?? [];

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between px-5 pb-3 pt-4">
        <div className="flex items-center gap-2.5">
          <h3 className="text-sm font-semibold text-white">Up next</h3>
          <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] font-medium text-zinc-300 ring-1 ring-white/[0.06]">
            {songs.length}
          </span>
        </div>
        <Link
          href="/queue"
          className="group flex items-center gap-1 text-xs font-medium text-violet-300 transition-colors hover:text-violet-200"
        >
          Open queue
          <Icon name="chevron-right" className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      {songs.length > 0 ? (
        <>
          <div className="divide-y divide-white/[0.05]">
            {songs.slice(0, 5).map((song, i) => (
              <div key={song.id} className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-white/[0.03]">
                <span className="w-5 text-right font-mono text-[11px] text-zinc-600">{i + 1}</span>
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] ring-1 ring-white/[0.06]">
                  <Icon name="music" className="h-3.5 w-3.5 text-zinc-400" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-zinc-100">{song.title}</p>
                  <p className="truncate text-xs text-zinc-500">{song.origin}</p>
                </div>
                <span className="font-mono text-xs text-zinc-500">{formatDuration(song.length)}</span>
              </div>
            ))}
          </div>
          {songs.length > 5 && (
            <div className="border-t border-white/[0.06] px-5 py-2.5">
              <p className="text-xs text-zinc-600">+ {songs.length - 5} more in queue</p>
            </div>
          )}
        </>
      ) : (
        <div className="px-5 pb-5 pt-2">
          <p className="text-sm text-zinc-500">
            Queue is empty — add a song from the{' '}
            <Link href="/queue" className="text-violet-300 transition-colors hover:text-violet-200">
              queue page
            </Link>
            .
          </p>
        </div>
      )}
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="space-y-2">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-4 w-64" />
      </div>
      <Skeleton className="h-40 w-full rounded-2xl" />
      <Skeleton className="h-24 w-full rounded-2xl" />
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-[76px] rounded-2xl" />
        <Skeleton className="h-[76px] rounded-2xl" />
        <Skeleton className="h-[76px] rounded-2xl" />
      </div>
    </div>
  );
}
