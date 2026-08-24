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
 * On connect the server sends a `snapshot` event; the client applies it so a
 * fresh tab is correct immediately and never waits for the first mutation.
 * After that, change events keep the local state in sync. If the socket drops
 * we reconnect with exponential backoff, and any page can also poll as a
 * fallback (see the pages) so a broken socket never leaves stale data.
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
let heartbeatTimer: ReturnType<typeof setInterval> | null = null;

// Application-level liveness on top of the browser's automatic protocol pong:
// the server pings every 25s (aiohttp heartbeat) and receives a hard timeout
// if no traffic arrives; if we observe a quiet socket for this window we
// treat it as dead and reconnect.
const HEARTBEAT_TIMEOUT = 40000;

// --- Optimistic updates ----------------------------------------------------
//
// A client-side action (play, skip, add-to-queue …) is reflected in the UI
// immediately, before the server round-trips. The server publishes the new
// authoritative state over the socket right after the mutation, so the socket
// event overwrites the optimistic value and reconciles the UI. If the request
// fails the caller re-applies the pre-mutation snapshot to roll the UI back.
//
// The optimistic value and the socket value live in the same `state` object, so
// subscribers see the optimistic value the moment it is applied and the server
// value the moment it arrives — no separate override bookkeeping needed.
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

function clearHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

function startHeartbeat() {
  clearHeartbeat();
  heartbeatTimer = setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    // No server event recently: the link is likely dead even though the
    // browser still reports OPEN. Force a clean reconnect.
    if (Date.now() - state.lastEventAt > HEARTBEAT_TIMEOUT) {
      try {
        ws.close(4001, 'heartbeat timeout');
      } catch {
        // ignore
      }
    }
  }, 10000);
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
      startHeartbeat();
      setState({ connected: true });
    };

    socket.onmessage = (ev: MessageEvent) => {
      applyEvent(String(ev.data));
    };

    socket.onclose = () => {
      clearHeartbeat();
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
  clearHeartbeat();
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
