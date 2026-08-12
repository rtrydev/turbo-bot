import type { ConnectionStatusDTO, QueueStateDTO, SongsListResponseDTO } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
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
