'use client';

import { useSyncExternalStore } from 'react';
import { resolveWsBase } from '@/lib/api';
import type { BotEvent, ConnectionStatusDTO, QueueStateDTO, SongsListResponseDTO } from '@/lib/types';

/**
 * A single shared websocket to the bot backend.
 *
 * Every page that cares about live state calls :func:`useBotSocket` and
 * receives the latest queue/status/library slices it asks for. The module
 * keeps exactly one socket open per tab and fans messages out to all
 * subscribers, so opening the dashboard, the queue and the library page
 * does not multiply the number of connections.
 *
 * The socket is the *authoritative* live channel:
 *
 * - On connect the server sends a `snapshot` event; the client applies it
 *   so a fresh tab is correct immediately and never waits for the first
 *   mutation.
 * - The server pushes a full `queue` event after **every** queue mutation —
 *   API-driven ones (add, skip, clear, repeat…) and player-driven ones (a
 *   song finishing on its own) — so the local copy always converges to the
 *   real state without any client-side bookkeeping.
 *
 * If the socket drops we reconnect with exponential backoff and re-apply the
 * snapshot when it comes back. Any page can additionally poll the REST API
 * as a last resort (see the pages); such polls are gated on the socket being
 * down, so they never race or fight the pushed events.
 */

type Listener = () => void;

interface BotState {
  connected: boolean;
  lastEventAt: number;
  queue: QueueStateDTO | null;
  status: ConnectionStatusDTO | null;
  library: SongsListResponseDTO | null;
  hasSnapshot: boolean;
}

const initial: BotState = {
  connected: false,
  lastEventAt: 0,
  queue: null,
  status: null,
  library: null,
  hasSnapshot: false,
};

let state: BotState = initial;
const listeners = new Set<Listener>();
let ws: WebSocket | null = null;
let attempt = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

// --- Client-side action feedback ------------------------------------------
//
// A client-side action (play, skip, add-to-queue …) is reflected in the UI
// immediately, before the server round-trips. The server publishes the new
// authoritative state over the socket right after the mutation, which
// overwrites the optimistic value and reconciles the UI. If the request
// fails, the caller re-applies the pre-mutation snapshot to roll the UI back.
type OverrideKey = 'queue' | 'status' | 'library';

export function setOptimistic(key: OverrideKey, value: unknown) {
  setState({ [key]: value } as Partial<BotState>);
}

function emit() {
  for (const l of listeners) l();
}

function setState(patch: Partial<BotState>) {
  state = { ...state, ...patch };
  emit();
}

function applyEvent(raw: string) {
  let msg: BotEvent;
  try {
    msg = JSON.parse(raw) as BotEvent;
  } catch {
    return;
  }

  switch (msg.event) {
    case 'snapshot':
      setState({
        queue: msg.data.queue,
        status: msg.data.status,
        library: msg.data.library,
        hasSnapshot: true,
        lastEventAt: Date.now(),
      });
      break;
    case 'queue':
      // Server state after a mutation (or a song finishing): always
      // authoritative, applied as-is.
      setState({ queue: msg.data, lastEventAt: Date.now() });
      break;
    case 'status':
      setState({ status: msg.data, lastEventAt: Date.now() });
      break;
    case 'library':
      setState({ library: msg.data, lastEventAt: Date.now() });
      break;
    case 'error':
      // Server reported an error; keep whatever we have. No state change.
      break;
    case 'ping':
    default:
      // A ping is proof of life; bump lastEventAt so the client can detect
      // a silent drop even when no real data flows.
      setState({ lastEventAt: Date.now() });
      break;
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = Math.min(30000, 500 * 2 ** attempt) + Math.random() * 250;
  attempt += 1;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    if (!ws || ws.readyState === WebSocket.CLOSED) {
      open();
    }
  }, delay);
}

function open() {
  resolveWsBase().then((base) => {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    let socket: WebSocket;
    try {
      socket = new WebSocket(`${base}/ws`);
    } catch {
      scheduleReconnect();
      return;
    }
    ws = socket;

    socket.onopen = () => {
      attempt = 0;
      setState({ connected: true });
    };

    socket.onmessage = (ev: MessageEvent) => {
      applyEvent(String(ev.data));
    };

    socket.onclose = () => {
      // We may have missed events while disconnected; forget that we ever
      // had a snapshot so the polling fallbacks on the pages kick in and the
      // UI recovers even if the socket never comes back.
      setState({ connected: false, hasSnapshot: false });
      if (listeners.size > 0) {
        scheduleReconnect();
      }
    };

    socket.onerror = () => {
      // onclose follows; nothing to do here.
    };
  });
}

function close() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    try {
      ws.close();
    } catch {
      // ignore
    }
    ws = null;
  }
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  if (listeners.size === 1) {
    open();
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) {
      close();
      setState({ connected: false });
    }
  };
}

function getSnapshot(): BotState {
  return state;
}

/**
 * Subscribe to the shared bot socket. Returns the latest queue/status/library
 * slices plus connection metadata. The socket is shared across all callers, so
 * opening the dashboard, the queue and the library page keeps a single
 * connection open per tab.
 */
export function useBotSocket(): BotState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
