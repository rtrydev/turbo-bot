"""End-to-end-ish tests for the admin queue state.

Run with:  venv/bin/python -m backend.tests.test_queue_reliability
"""

import asyncio
import json

import aiohttp

from backend.adapters.services.in_memory_context_manager_service import InMemoryContextManagerService
from backend.application.queries.get_connection_status_query import GetConnectionStatusQuery, GetConnectionStatusQueryHandler
from backend.application.queries.get_queue_state_query import GetQueueStateQuery, GetQueueStateQueryHandler
from backend.application.utils.mediator import Mediator
from backend.domain.models.song import Song
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService
from backend.ports.api.app import create_app
from backend.service.dependency_injection import container
from punq import Scope

BASE = 'http://127.0.0.1:18080'
WS_URL = 'ws://127.0.0.1:18080/ws'


def _mk_song(i: int) -> Song:
    return Song(id=f's{i}', fid=None, title=f'Song {i}', origin=f'https://youtu.be/s{i}', length=100 + i)


class FakePlayer(MediaPlayerService):
    """Stands in for the Discord media player: no channel, so is_playing/
    is_paused are False and next() is a no-op. Queue mutations still fire."""

    def play(self, song): raise RuntimeError('not supported in test')
    def pause(self): raise RuntimeError('not supported in test')
    def resume(self): raise RuntimeError('not supported in test')
    def stop(self): raise RuntimeError('not supported in test')
    def next(self): pass
    def is_playing(self): return False
    def is_paused(self): return False


def _make_app():
    cm = InMemoryContextManagerService()
    container.register(ContextManagerService, lambda: cm, scope=Scope.singleton)
    container.register(MediaPlayerService, lambda: FakePlayer(), scope=Scope.singleton)

    mediator = Mediator()\
        .register(GetQueueStateQuery, GetQueueStateQueryHandler)\
        .register(GetConnectionStatusQuery, GetConnectionStatusQueryHandler)

    return create_app(mediator), cm


async def _wait_for_queue_event(ws, timeout=5.0):
    """Wait for the next 'queue' push (skipping snapshots and pings)."""
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise TimeoutError('timed out waiting for a queue event')
        msg = await asyncio.wait_for(ws.receive(), timeout=remaining)
        if msg.type != aiohttp.WSMsgType.TEXT:
            continue
        ev = json.loads(msg.data)
        if ev.get('event') == 'queue':
            return ev['data']


async def main():
    app, cm = _make_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '127.0.0.1', 18080)
    await site.start()

    try:
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(WS_URL)
        # Consume the initial snapshot first.
        while True:
            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT and json.loads(msg.data).get('event') == 'snapshot':
                break

        q = cm.get_queue_state()

        # --- Scenario 1: queue advance (song end) pushes correct state ----
        q.add(_mk_song(1))
        await _wait_for_queue_event(ws)
        q.add(_mk_song(2))
        await _wait_for_queue_event(ws)

        advanced = q.get_next()
        assert advanced is not None and advanced.id == 's1', f'get_next wrong: {advanced}'
        pushed = await _wait_for_queue_event(ws)
        assert len(pushed['songs']) == 1 and pushed['songs'][0]['id'] == 's2', pushed
        print('scenario 1 OK: advance pushed over WS with correct remaining list')

        # --- Scenario 2: REST agrees with the last push --------------------
        async with session.get(f'{BASE}/api/queue') as resp:
            rest = await resp.json()
        assert rest['songs'] == pushed['songs'], f'REST {rest["songs"]} != WS {pushed["songs"]}'
        print('scenario 2 OK: REST snapshot matches the WS push')

        # --- Scenario 3: repeat honours skip_excluding ---------------------
        q.toggle_repeat()
        await _wait_for_queue_event(ws)
        q.skip_excluding(q.get_last_song())
        again = q.get_next()
        assert again is not None and again.id == 's2', f'skip_excluding failed: {again}'
        print('scenario 3 OK: repeat does not re-play a skipped song')

        # --- Scenario 4: clear pushes ---------------------------------------
        q.add(_mk_song(9))
        await _wait_for_queue_event(ws)  # push for the add
        q.clear()
        # Drain until we see the clear push (empty songs list)
        for _ in range(10):
            cleared = await _wait_for_queue_event(ws)
            if cleared['songs'] == []:
                break
        assert cleared['songs'] == [], cleared
        print('scenario 4 OK: clear pushed over WS')

        await ws.close()
        await session.close()
        print('ALL SCENARIOS PASSED')
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
