'use client';

import { type ReactNode } from 'react';
import { useBotSocket } from '@/lib/socket';

/**
 * Keeps the shared bot websocket alive for the lifetime of the app.
 *
 * `useBotSocket` is refcounted: the socket opens when the first subscriber
 * mounts and closes when the last unmounts. Page-level subscribers come and
 * go on every client-side navigation, so without this layout-level hook the
 * connection would be torn down between pages. Subscribing here ensures the
 * socket persists across the whole admin console.
 */
export function BotSocketProvider({ children }: { children: ReactNode }) {
  useBotSocket();
  return <>{children}</>;
}
