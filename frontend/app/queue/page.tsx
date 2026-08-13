'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast';
import type { QueueStateDTO, SongDTO } from '@/lib/types';

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

async function safeAction(fn: () => Promise<unknown>, successMsg: string) {
  try {
    await fn();
    return true;
  } catch (err) {
    console.error(err);
    return false;
  }
}

export default function QueuePage() {
  const [queue, setQueue] = useState<QueueStateDTO | null>(null);
  const [url, setUrl] = useState('');
  const [randomCount, setRandomCount] = useState(10);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const { showToast } = useToast();

  const fetchData = async () => {
    try {
      const q = await api.getQueue();
      setQueue(q);
    } catch {
      // Silently handle errors for polling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
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
    try {
      await api.addRandomSongs(randomCount);
      showToast(`Added ${randomCount} random songs`, 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to add random songs', 'error');
    }
  };

  const handleAction = async (fn: () => Promise<unknown>, successMsg: string) => {
    const ok = await safeAction(fn, successMsg);
    showToast(ok ? successMsg : 'Action failed', ok ? 'success' : 'error');
  };

  if (loading) return <div className="text-slate-400">Loading...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-white">Queue Management</h2>

      {/* Add Song Form */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <p className="text-sm text-slate-400 mb-4">Add a Song</p>
        <form onSubmit={handleAddSong} className="flex gap-3">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste YouTube URL..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={adding || !url.trim()}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            {adding ? 'Adding...' : 'Add'}
          </button>
        </form>

        <div className="flex gap-3 mt-4">
          <input
            type="number"
            value={randomCount}
            onChange={(e) => setRandomCount(parseInt(e.target.value) || 1)}
            min={1}
            max={50}
            className="w-24 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleAddRandom}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg font-medium transition-colors"
          >
            Add Random Songs
          </button>
        </div>
      </div>

      {/* Playback Controls */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <p className="text-sm text-slate-400 mb-4">Playback Controls</p>
        <div className="flex gap-3 flex-wrap">
          <QueueButton onClick={() => handleAction(api.startPlayback, 'Playback started')} label="Play" icon="M8 5v14l11-7z" />
          <QueueButton
            onClick={() => handleAction(
              queue?.is_playing ? api.pausePlayback : api.resumePlayback,
              queue?.is_playing ? 'Playback paused' : 'Playback resumed'
            )}
            label={queue?.is_playing ? 'Pause' : 'Resume'}
            icon="M6 4h4v16H6V4zm8 0h4v16h-4V4z"
          />
          <QueueButton onClick={() => handleAction(api.skipSong, 'Skipped to next song')} label="Skip" icon="M5 4l10 8-10 8V4zM16 4h2v16h-2V4z" />
          <QueueButton
            onClick={() => handleAction(api.toggleRepeat, `Repeat ${queue?.repeat_enabled ? 'disabled' : 'enabled'}`)}
            label={`Repeat: ${queue?.repeat_enabled ? 'ON' : 'OFF'}`}
            icon="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"
            active={queue?.repeat_enabled}
          />
          <QueueButton onClick={() => handleAction(api.clearQueue, 'Queue cleared')} label="Clear Queue" icon="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" danger />
        </div>
      </div>

      {/* Now Playing */}
      {queue?.currently_playing && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <p className="text-sm text-slate-400 mb-3">Now Playing</p>
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              queue.is_playing ? 'bg-indigo-600' : queue.is_paused ? 'bg-yellow-600' : 'bg-slate-600'
            }`}>
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                {queue.is_playing ? (
                  <path d="M8 5v14l11-7z" />
                ) : queue.is_paused ? (
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                ) : (
                  <path d="M12 3C6.48 3 2 7.48 2 13s4.48 10 10 10 10-4.48 10-10S17.52 3 12 3zm-2 14.5v-9l6 4.5-6 4.5z" />
                )}
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium truncate">{queue.currently_playing.title}</p>
              <p className="text-sm text-slate-400">{formatDuration(queue.currently_playing.length)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Queue List */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-slate-400">Queue</p>
          <span className="px-3 py-1 bg-indigo-600/20 text-indigo-400 rounded-full text-xs font-medium">
            {queue?.songs.length || 0} songs
          </span>
        </div>
        {(queue?.songs.length ?? 0) > 0 ? (
          <div className="space-y-2 max-h-96 overflow-auto">
            {queue!.songs.map((song, i) => (
              <SongItem key={song.id} song={song} index={i + 1} />
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-center py-8">Queue is empty. Add some songs!</p>
        )}
      </div>
    </div>
  );
}

function QueueButton({ onClick, label, icon, active, danger }: { onClick: () => void; label: string; icon: string; active?: boolean; danger?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        danger
          ? 'bg-red-600/20 text-red-400 hover:bg-red-600/30'
          : active
            ? 'bg-indigo-600 text-white'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
      }`}
    >
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d={icon} />
      </svg>
      {label}
    </button>
  );
}

function SongItem({ song, index }: { song: SongDTO; index: number }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors">
      <span className="text-sm text-slate-400 w-6 text-right">{index}</span>
      <svg className="w-8 h-8 text-indigo-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm truncate">{song.title}</p>
        <p className="text-xs text-slate-400 truncate">{song.origin}</p>
      </div>
      <span className="text-xs text-slate-400 flex-shrink-0">{formatDuration(song.length)}</span>
    </div>
  );
}
