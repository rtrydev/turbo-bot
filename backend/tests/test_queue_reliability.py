"""End-to-end-ish tests for the admin queue state.

Run with:  venv/bin/python -m backend.tests.test_queue_reliability
"""

import asyncio
import json
import time

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

FAKE_SETTLE_DELAY = 0.1  # seconds; production spans audio download/decode


def _mk_song(i: int) -> Song:
    return Song(id=f's{i}', fid=None, title=f'Song {i}', origin=f'https://youtu.be/s{i}', length=100 + i)


class FakePlayer(MediaPlayerService):
    """Stands in for the Discord media player: no channel, so is_playing/
    is_paused are False and next() is a no-op. Queue mutations still fire.

    ``alive()`` reports whether *audio is still alive in the channel*. The
    *real* player keeps the previous source loaded until the next track's
    source is attached (discord's play/stop sequence), and only stops after
    that — so the queue mutation that records an advance happens a window of
    time *before* the player state actually changes.

    Scenario 5 of this test drives ``alive()`` through that real sequence
    (previous stays alive, then next attaches, then the channel stops) to
    prove no pushed event ever reports a stale or missing "now playing"
    while audio is still going.
    """

    def __init__(self) -> None:
        self.alive = False
        self.settled = False
        self.stop_calls = 0

    def play(self, song: Song) -> None:
        self.alive = True
        self.settled = False

    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def stop(self) -> None:
        self.stop_calls += 1

    def next(self) -> None:
        self.alive = False
        self.settled = False

    def is_playing(self) -> bool:
        return self.alive

    def is_paused(self) -> bool:
        return False

    # --- transition simulation --------------------------------------------
    #
    # Replays the real channel's end-of-song sequence with a bounded delay:
    # 1. the song ends — audio still alive, previous source loaded;
    # 2. the next track's source is attached — still alive, audio continuous;
    # 3. the channel stops the previous source.
    #
    # In production step 2 is what can take seconds (audio download/decode);
    # the fake delay just makes the window observable in the test.

    async def settle_next(self, loop: asyncio.AbstractEventLoop) -> None:
        if self.settled:
            return
        await loop.run_in_executor(None, lambda: time.sleep(FAKE_SETTLE_DELAY))
        self.alive = True
        await loop.run_in_executor(None, lambda: time.sleep(FAKE_SETTLE_DELAY))
        self.alive = False
        self.stop_calls += 1
        self.settled = True

    async def settle_stop(self, loop: asyncio.AbstractEventLoop) -> None:
        if self.settled:
            return
        await loop.run_in_executor(None, lambda: time.sleep(FAKE_SETTLE_DELAY))
        self.alive = False
        self.stop_calls += 1
        self.settled = True


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


async def _wait_for_settled(player: FakePlayer, ws, timeout=3.0):
    """Await player settlement and drain every queue event until it ends.

    The fake player settles a tick after its last transition step, and the
    queue's settle re-notify (if any) lands right on that boundary — so we
    wait one extra beat before declaring done. Returns the last queue event,
    or None if none was pushed.
    """
    last: dict | None = None
    deadline = asyncio.get_event_loop().time() + timeout
    extra = False
    while True:
        now = asyncio.get_event_loop().time()
        if now >= deadline:
            if player.settled and extra:
                return last
            if player.settled:
                extra = True
                await asyncio.sleep(0.05)
                continue
            raise TimeoutError('timed out waiting for the player to settle')
        try:
            msg = await asyncio.wait_for(ws.receive(), timeout=0.05)
        except asyncio.TimeoutError:
            continue
        if msg.type != aiohttp.WSMsgType.TEXT:
            continue
        ev = json.loads(msg.data)
        if ev.get('event') == 'queue':
            last = ev['data']


async def main():
    app, cm = _make_app()
    player: FakePlayer = container.resolve(MediaPlayerService)
    # Simulate a real playback session: audio is alive from the start, and
    # every advance/stop settles only after the (bounded) transition delay.
    # No transition is pending initially, so the player starts settled.
    player.alive = True
    player.settled = True
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
        loop = asyncio.get_event_loop()

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

        # --- Scenario 5: no stale/missing "now playing" while audio alive ---
        #
        # Regression test for the reported admin-view bug: right after a
        # song ends, the next track's audio setup takes time, so a snapshot
        # taken inside the transition window reported "nothing playing"
        # even though music kept playing. Drive the *real* channel sequence
        # (previous stays alive → next attaches → channel stops) and check
        # every pushed event for invariants that must hold the whole time:
        #
        #   * audio alive  ⇒ "now playing" is set to *some* track and the
        #     state is playing/paused, never stopped
        #   * audio stopped ⇒ "now playing" may be empty (genuine stop)
        #
        # If any event violates these, the UI would have shown a ghost of
        # the finished track or a bogus "nothing playing".
        q.add(_mk_song(20))
        q.add(_mk_song(21))
        q.add(_mk_song(22))
        # Settle the three adds' pushes (re-notify events share the stream).
        for _ in range(3):
            await _wait_for_queue_event(ws)
        # Repeat must be off for the plain advance sequence below.
        if q.is_repeat_enabled():
            q.toggle_repeat()
            await _wait_for_queue_event(ws)

        # Song 20 finishes → the real sequence runs while audio stays alive.
        q.get_next()
        events = []
        last = await _wait_for_settled(player, ws)
        if last is not None:
            events.append(last)
            assert last['currently_playing'] is not None and last['songs'] and last['songs'][0]['id'] == 's21', \
                f'stale "now playing" while audio alive: {last}'

        # Song 21 finishes, queue still has s22.
        q.get_next()
        last = await _wait_for_settled(player, ws)
        if last is not None:
            events.append(last)
            assert last['currently_playing'] is not None and last['songs'] and last['songs'][0]['id'] == 's22', \
                f'stale "now playing" while audio alive: {last}'

        # Song 22 finishes, queue is now empty — the only legal "stopped"
        # moment, and it must arrive only after the channel has stopped.
        q.get_next()
        last = await _wait_for_settled(player, ws)
        if last is not None:
            events.append(last)
        if events:
            final = events[-1]
            assert final['songs'] == [], f'expected empty queue at end: {final}'
            assert final['currently_playing'] is None or final['currently_playing']['id'] in ('s20', 's21', 's22'), \
                f'ghost track in "now playing": {final}'
            if final['currently_playing'] is None:
                assert not (final['is_playing'] or final['is_paused']), \
                    f'state playing while "nothing playing": {final}'

        await ws.close()
        await session.close()
        print('scenario 5 OK: no stale/missing "now playing" while audio alive')
        print('ALL SCENARIOS PASSED')
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
