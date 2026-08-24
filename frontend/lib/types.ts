export interface SongDTO {
  id: string;
  title: string;
  length: number;
  origin: string;
}

export interface QueueStateDTO {
  songs: SongDTO[];
  currently_playing: SongDTO | null;
  is_playing: boolean;
  is_paused: boolean;
  repeat_enabled: boolean;
}

export interface ConnectionStatusDTO {
  connected: boolean;
  channel_name: string | null;
}

export interface SongsListResponseDTO {
  songs: SongDTO[];
  total: number;
  page: number;
  limit: number;
}

/** A single live event pushed over the backend websocket. */
export type BotEvent =
  | { event: 'snapshot'; data: { queue: QueueStateDTO | null; status: ConnectionStatusDTO | null; library: SongsListResponseDTO | null } }
  | { event: 'queue'; data: QueueStateDTO }
  | { event: 'status'; data: ConnectionStatusDTO }
  | { event: 'library'; data: SongsListResponseDTO }
  | { event: 'ping'; data: null }
  | { event: 'error'; message: string };
