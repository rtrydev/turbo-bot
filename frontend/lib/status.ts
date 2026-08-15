'use client';

import { useSyncExternalStore } from 'react';
import { api } from '@/lib/api';
import type { ConnectionStatusDTO } from '@/lib/types';

const POLL_INTERVAL = 5000;

type Listener = () => void;

let current: ConnectionStatusDTO | null = null;
let timer: ReturnType<typeof setInterval> | null = null;
const listeners = new Set<Listener>();

function emitChange() {
  for (const listener of listeners) {
    listener();
  }
}

async function poll() {
  try {
    current = await api.getStatus();
  } catch {
    // Silently handle polling errors
  }
  emitChange();
}

function startPolling() {
  if (timer !== null) return;
  void poll();
  timer = setInterval(() => void poll(), POLL_INTERVAL);
}

function stopPolling() {
  if (timer !== null) {
    clearInterval(timer);
    timer = null;
  }
}

function subscribe(listener: Listener) {
  listeners.add(listener);
  startPolling();
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) stopPolling();
  };
}

function getSnapshot() {
  return current;
}

function getServerSnapshot() {
  return null;
}

export function useConnectionStatus(): ConnectionStatusDTO | null {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
