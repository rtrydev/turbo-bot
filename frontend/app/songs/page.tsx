'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useBotSocket, setOptimistic } from '@/lib/socket';
import { useToast } from '@/lib/toast';
import type { SongDTO, SongsListResponseDTO } from '@/lib/types';
import { formatDuration } from '@/lib/format';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';

const LIMIT = 25;

export default function SongsPage() {
  const bot = useBotSocket();
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [addingId, setAddingId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<SongDTO | null>(null);
  const [libraryUrl, setLibraryUrl] = useState('');
  const [addingToLibrary, setAddingToLibrary] = useState(false);
  const { showToast } = useToast();

  // Fallback: if the socket never connects, fetch the page directly and push
  // it into the shared socket state so the library still renders.
  useEffect(() => {
    if (bot.hasSnapshot) return;
    let cancelled = false;
    const load = async () => {
      if (cancelled) return;
      try {
        const result = await api.listSongs(query, page, LIMIT);
        if (cancelled) return;
        setOptimistic('library', result);
      } catch {
        // keep skeleton
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [bot.hasSnapshot, query, page]);

  // Derive the visible page from the shared socket state. This is pure and
  // re-runs whenever the library changes (add/delete from any tab) or the
  // user searches / paginates.
  const base: SongsListResponseDTO =
    bot.library ?? { songs: [], total: 0, page: 0, limit: LIMIT };
  const start = page * LIMIT;
  const data: SongsListResponseDTO = {
    songs: base.songs.slice(start, start + LIMIT),
    total: base.total,
    page,
    limit: LIMIT,
  };
  const loading = !bot.hasSnapshot && data.songs.length === 0;

  const totalPages = Math.max(1, Math.ceil(data.total / LIMIT));

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setQuery(searchTerm.trim());
  };

  const handleAdd = async (song: SongDTO) => {
    setAddingId(song.id);
    try {
      await api.addSong(song.origin);
      showToast(`"${song.title}" added to queue`, 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to add song', 'error');
    } finally {
      setAddingId(null);
    }
  };

  const handleAddToLibrary = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!libraryUrl.trim()) return;
    setAddingToLibrary(true);
    // Optimistically drop any active search and reset to page 0 so the new
    // track is the first thing shown the moment the server echoes it.
    setLibraryUrl('');
    setSearchTerm('');
    setQuery('');
    setPage(0);
    try {
      await api.addSongToLibrary(libraryUrl.trim());
      showToast('Track added to library', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to add track', 'error');
    } finally {
      setAddingToLibrary(false);
    }
  };

  const confirmRemove = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    const targetId = confirmDelete.id;
    // Optimistically remove the row and decrement the count so the list
    // updates instantly; the server publishes the new library state which
    // reconciles (or the failure path rolls it back).
    const base = bot.library;
    if (base) {
      setOptimistic('library', {
        ...base,
        songs: base.songs.filter((s) => s.id !== targetId),
        total: Math.max(0, base.total - 1),
      });
    }
    try {
      await api.deleteSong(targetId);
      showToast(`"${confirmDelete.title}" removed`, 'success');
      setConfirmDelete(null);
    } catch (err) {
      // Roll back the optimistic removal on failure.
      if (base) setOptimistic('library', base);
      showToast(err instanceof Error ? err.message : 'Failed to remove song', 'error');
    } finally {
      setDeleting(false);
    }
  };

  if (loading && !data) return <SongsSkeleton />;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Song Library"
        subtitle={data ? `${data.total} ${data.total === 1 ? 'track' : 'tracks'} available` : 'Your saved tracks'}
      />

      <Card className="animate-fade-up p-5">
        <form onSubmit={handleAddToLibrary} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Icon name="link" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={libraryUrl}
              onChange={(e) => setLibraryUrl(e.target.value)}
              placeholder="Paste a YouTube URL…"
              className="h-11 w-full rounded-xl bg-white/[0.04] pl-10 pr-4 text-sm text-white ring-1 ring-white/[0.08] transition-all placeholder:text-zinc-600 focus:bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-violet-500/60"
            />
          </div>
          <Button type="submit" variant="primary" size="lg" icon="plus" loading={addingToLibrary} disabled={!libraryUrl.trim()}>
            Add to library
          </Button>
        </form>
        <p className="mt-3 text-xs text-zinc-500">Saves the track to your library without adding it to the queue.</p>
      </Card>

      <Card className="animate-fade-up p-5" style={{ animationDelay: '70ms' }}>
        <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Icon name="search" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by title…"
              className="h-11 w-full rounded-xl bg-white/[0.04] pl-10 pr-4 text-sm text-white ring-1 ring-white/[0.08] transition-all placeholder:text-zinc-600 focus:bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-violet-500/60"
            />
          </div>
          <Button type="submit" variant="primary" size="lg" icon="search">
            Search
          </Button>
        </form>
      </Card>

      <div className="animate-fade-up" style={{ animationDelay: '140ms' }}>
        <Card className="overflow-hidden">
          {(data?.songs.length ?? 0) > 0 ? (
            <>
              <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  {data!.total} {data!.total === 1 ? 'track' : 'tracks'}
                </p>
                {query && (
                  <button
                    onClick={() => {
                      setQuery('');
                      setSearchTerm('');
                      setPage(0);
                    }}
                    className="flex items-center gap-1.5 text-xs font-medium text-violet-300 transition-colors hover:text-violet-200"
                  >
                    <Icon name="x" className="h-3 w-3" />
                    Clear search
                  </button>
                )}
              </div>
              <div className="divide-y divide-white/[0.05]">
                {data!.songs.map((song, i) => (
                  <SongRow
                    key={song.id}
                    song={song}
                    index={i + 1}
                    onAdd={handleAdd}
                    adding={addingId === song.id}
                    onDelete={() => setConfirmDelete(song)}
                  />
                ))}
              </div>
            </>
          ) : (
            <EmptyState
              icon="search"
              title={query ? 'No matches found' : 'Library is empty'}
              description={
                query
                  ? `Nothing in your library matches "${query}".`
                  : 'Paste a YouTube link above to add your first track.'
              }
            />
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-white/[0.06] px-5 py-3.5">
              <span className="font-mono text-xs text-zinc-500">
                {page + 1} / {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  icon="chevron-left"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  iconRight="chevron-right"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>

      <Modal
        open={confirmDelete !== null}
        tone="danger"
        icon="trash"
        title="Remove this track?"
        description={
          confirmDelete
            ? `"${confirmDelete.title}" will be removed from your library. This cannot be undone.`
            : undefined
        }
        confirmLabel="Remove"
        loading={deleting}
        onConfirm={confirmRemove}
        onClose={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function SongRow({
  song,
  index,
  onAdd,
  adding,
  onDelete,
}: {
  song: SongDTO;
  index: number;
  onAdd: (song: SongDTO) => void;
  adding: boolean;
  onDelete: (song: SongDTO) => void;
}) {
  return (
    <div className="group flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-white/[0.03]">
      <span className="hidden w-6 text-right font-mono text-[11px] text-zinc-600 sm:block">{index}</span>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] ring-1 ring-white/[0.06] transition-colors group-hover:bg-violet-500/[0.12] group-hover:ring-violet-500/20">
        <Icon name="music" className="h-4 w-4 text-zinc-400 transition-colors group-hover:text-violet-300" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-100">{song.title}</p>
        <p className="mt-0.5 truncate text-xs text-zinc-500">{song.origin}</p>
      </div>
      <span className="hidden font-mono text-xs text-zinc-500 md:block">{formatDuration(song.length)}</span>
      <div className="flex shrink-0 items-center gap-1.5 opacity-100 transition-opacity sm:opacity-60 sm:group-hover:opacity-100">
        <Button size="sm" variant="ghost" icon="plus" loading={adding} onClick={() => onAdd(song)}>
          Queue
        </Button>
        <button
          onClick={() => onDelete(song)}
          title="Remove from library"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-500 transition-all hover:bg-red-500/[0.12] hover:text-red-300"
        >
          <Icon name="trash" className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function SongsSkeleton() {
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="space-y-2">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-4 w-56" />
      </div>
      <Skeleton className="h-24 w-full rounded-2xl" />
      <Skeleton className="h-[28rem] w-full rounded-2xl" />
    </div>
  );
}
