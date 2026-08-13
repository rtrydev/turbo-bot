'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast';
import type { SongDTO, SongsListResponseDTO } from '@/lib/types';

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function SongsPage() {
  const [data, setData] = useState<SongsListResponseDTO | null>(null);
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [addingId, setAddingId] = useState<string | null>(null);
  const { showToast } = useToast();

  const limit = 25;

  const fetchData = async () => {
    try {
      const result = await api.listSongs(query, page, limit);
      setData(result);
    } catch {
      // Silently handle errors
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [query, page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setQuery(searchTerm);
  };

  const handleAddToQueue = async (song: SongDTO) => {
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

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  if (loading && !data) return <div className="text-slate-400">Loading...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-white">Song Library</h2>

      {/* Search */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search songs by title..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Results Info */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          {data?.total || 0} songs found
        </p>
        {query && (
          <button
            onClick={() => { setQuery(''); setSearchTerm(''); setPage(0); }}
            className="text-sm text-indigo-400 hover:text-indigo-300"
          >
            Clear search
          </button>
        )}
      </div>

      {/* Songs List */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        {(data?.songs.length ?? 0) > 0 ? (
          <div className="divide-y divide-slate-700">
            {data!.songs.map((song) => (
              <SongRow key={song.id} song={song} onAdd={handleAddToQueue} isAdding={addingId === song.id} />
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-center py-12">No songs found</p>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-slate-400 px-4">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function SongRow({ song, onAdd, isAdding }: { song: SongDTO; onAdd: (song: SongDTO) => void; isAdding: boolean }) {
  return (
    <div className="flex items-center gap-4 p-4 hover:bg-slate-700/50 transition-colors">
      <svg className="w-10 h-10 text-indigo-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate">{song.title}</p>
        <p className="text-xs text-slate-400 truncate mt-0.5">{song.origin}</p>
      </div>
      <span className="text-sm text-slate-400 flex-shrink-0">{formatDuration(song.length)}</span>
      <button
        onClick={() => onAdd(song)}
        disabled={isAdding}
        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex-shrink-0"
      >
        {isAdding ? '...' : 'Queue'}
      </button>
    </div>
  );
}
