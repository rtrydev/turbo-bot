import type { ConnectionStatusDTO, QueueStateDTO, SongDTO, SongsListResponseDTO } from '@/lib/types';

let apiBase = '';
let wsBase = '';

async function resolveApiBase(): Promise<string> {
  if (apiBase) return apiBase;
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    apiBase = data.apiUrl || 'http://localhost:8080';
    wsBase = data.wsUrl || apiBase.replace(/^http/, 'ws');
  } catch {
    apiBase = 'http://localhost:8080';
    wsBase = 'ws://localhost:8080';
  }
  return apiBase;
}

/** Resolve the websocket base URL (e.g. `ws://host:8080`). */
export async function resolveWsBase(): Promise<string> {
  if (!wsBase) await resolveApiBase();
  return wsBase;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = await resolveApiBase();
  const res = await fetch(`${base}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  getStatus: () => fetchAPI<ConnectionStatusDTO>('/api/status'),
  getQueue: () => fetchAPI<QueueStateDTO>('/api/queue'),
  listSongs: (query?: string, page = 0, limit = 25) =>
    fetchAPI<SongsListResponseDTO>(`/api/songs?q=${encodeURIComponent(query || '')}&page=${page}&limit=${limit}`),
  deleteSong: (id: string) =>
    fetchAPI<Record<string, unknown>>(`/api/songs/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  addSongToLibrary: (origin: string) =>
    fetchAPI<SongDTO>('/api/songs', { method: 'POST', body: JSON.stringify({ origin }) }),

  addSong: (origin: string) =>
    fetchAPI<Record<string, unknown>>('/api/queue/add', { method: 'POST', body: JSON.stringify({ origin }) }),
  addRandomSongs: (count = 10) =>
    fetchAPI<Record<string, unknown>>('/api/queue/random', { method: 'POST', body: JSON.stringify({ count }) }),
  clearQueue: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/clear', { method: 'POST' }),
  startPlayback: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/play', { method: 'POST' }),
  pausePlayback: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/pause', { method: 'POST' }),
  resumePlayback: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/resume', { method: 'POST' }),
  skipSong: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/skip', { method: 'POST' }),
  toggleRepeat: () =>
    fetchAPI<Record<string, unknown>>('/api/queue/repeat', { method: 'POST' }),
};
