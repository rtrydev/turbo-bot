'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast';
import type { QueueStateDTO, ConnectionStatusDTO } from '@/lib/types';

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

export default function Dashboard() {
  const [queue, setQueue] = useState<QueueStateDTO | null>(null);
  const [status, setStatus] = useState<ConnectionStatusDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  const fetchData = async () => {
    try {
      const [q, s] = await Promise.all([api.getQueue(), api.getStatus()]);
      setQueue(q);
      setStatus(s);
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

  if (loading) return <div className="text-slate-400">Loading...</div>;

  const handleAction = async (fn: () => Promise<unknown>, successMsg: string) => {
    const ok = await safeAction(fn, successMsg);
    showToast(ok ? successMsg : 'Action failed', ok ? 'success' : 'error');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-white">Dashboard</h2>

      {/* Status Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">Connection Status</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-3 h-3 rounded-full ${status?.connected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-lg font-semibold text-white">
                {status?.connected ? `Connected to ${status.channel_name}` : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Now Playing Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <p className="text-sm text-slate-400 mb-3">Now Playing</p>
        {queue?.currently_playing ? (
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
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              queue.is_playing ? 'bg-green-500/20 text-green-400' :
              queue.is_paused ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-slate-600/20 text-slate-400'
            }`}>
              {queue.is_playing ? 'Playing' : queue.is_paused ? 'Paused' : 'Stopped'}
            </span>
          </div>
        ) : (
          <p className="text-slate-500">No song playing</p>
        )}
      </div>

      {/* Queue Overview */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-slate-400">Queue</p>
          <span className="px-3 py-1 bg-indigo-600/20 text-indigo-400 rounded-full text-xs font-medium">
            {queue?.songs.length || 0} songs
          </span>
        </div>
        {(queue?.songs.length ?? 0) > 0 ? (
          <div className="space-y-2 max-h-64 overflow-auto">
            {queue!.songs.map((song, i) => (
              <div key={song.id} className="flex items-center gap-3 p-3 bg-slate-700/50 rounded-lg">
                <span className="text-sm text-slate-400 w-6">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm truncate">{song.title}</p>
                </div>
                <span className="text-xs text-slate-400">{formatDuration(song.length)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500">Queue is empty</p>
        )}
      </div>

      {/* Quick Controls */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <p className="text-sm text-slate-400 mb-4">Quick Controls</p>
        <div className="flex gap-3 flex-wrap">
          <ControlButton onClick={() => handleAction(api.startPlayback, 'Playback started')} label="Play" icon="play" />
          <ControlButton
            onClick={() => handleAction(
              queue?.is_playing ? api.pausePlayback : api.resumePlayback,
              queue?.is_playing ? 'Playback paused' : 'Playback resumed'
            )}
            label={queue?.is_playing ? 'Pause' : 'Resume'}
            icon={queue?.is_playing ? 'pause' : 'resume'}
          />
          <ControlButton onClick={() => handleAction(api.skipSong, 'Skipped to next song')} label="Skip" icon="skip" />
          <ControlButton
            onClick={() => handleAction(api.toggleRepeat, `Repeat ${queue?.repeat_enabled ? 'disabled' : 'enabled'}`)}
            label={`Repeat: ${queue?.repeat_enabled ? 'ON' : 'OFF'}`}
            icon="repeat"
            active={queue?.repeat_enabled}
          />
          <ControlButton onClick={() => handleAction(api.clearQueue, 'Queue cleared')} label="Clear Queue" icon="clear" danger />
        </div>
      </div>
    </div>
  );
}

function ControlButton({ onClick, label, icon, active, danger }: { onClick: () => void; label: string; icon: string; active?: boolean; danger?: boolean }) {
  const icons: Record<string, string> = {
    play: 'M8 5v14l11-7z',
    pause: 'M6 4h4v16H6V4zm8 0h4v16h-4V4z',
    resume: 'M8 5v14l11-7z',
    skip: 'M5 4l10 8-10 8V4zM16 4h2v16h-2V4z',
    repeat: 'M4 4v5h5M20 20v-5h-5',
    clear: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
  };

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
        <path d={icons[icon]} />
      </svg>
      {label}
    </button>
  );
}
