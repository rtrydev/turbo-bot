"""A tiny in-process event hub that fans out server-side state changes to
connected websocket clients.

The hub is deliberately transport-agnostic: any code path that changes
queue / connection / library state (the Discord bot, the REST API, the
download worker) calls :meth:`Hub.publish` and every live client receives
the matching event. The hub never throws from ``publish`` — if a client has
gone away we just drop it.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)

#: Names of the events the frontend understands. Keep these stable — the
#: client branches on this exact string.
EVENT_QUEUE = 'queue'
EVENT_STATUS = 'status'
EVENT_LIBRARY = 'library'
EVENT_PING = 'ping'


class Hub:
    """Registry of open websocket clients plus a fan-out helper.

    A single :class:`Hub` is attached to the aiohttp application under the
    ``app['hub']`` key. Because every event that matters goes through one
    process (the Discord bot and the admin API live in the same Python
    process) a process-local set of sockets is sufficient.
    """

    def __init__(self) -> None:
        self._clients: set[web.WebSocketResponse] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: web.WebSocketResponse) -> None:
        async with self._lock:
            self._clients.add(ws)
        logger.debug('WS client connected (%d total)', len(self._clients))

    async def unregister(self, ws: web.WebSocketResponse) -> None:
        async with self._lock:
            self._clients.discard(ws)
        logger.debug('WS client disconnected (%d total)', len(self._clients))

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def publish(self, event: str, payload: Any) -> None:
        """Send a JSON-encoded event to every live client.

        Clients that fail to accept the message are pruned. ``publish`` is
        safe to call from a synchronous context via ``asyncio.run_coroutine_threadsafe``
        if needed — but in practice it is only called from async handlers.
        """
        message = {'event': event, 'data': payload}
        dead: list[web.WebSocketResponse] = []
        for ws in list(self._clients):
            try:
                if ws.closed:
                    dead.append(ws)
                    continue
                await ws.send_json(message)
            except Exception as exc:  # noqa: BLE001 - intentional broad catch
                logger.debug('WS send failed, dropping client: %s', exc)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)
            logger.debug('WS pruned %d dead client(s)', len(dead))
