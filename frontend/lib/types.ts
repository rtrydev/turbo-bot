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
