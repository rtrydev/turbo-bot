import asyncio
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import aiohttp
from aiohttp import web

from backend.application.commands.add_random_songs_to_queue_command import AddRandomSongsToQueueCommand
from backend.application.commands.add_song_to_queue_command import AddSongToQueueCommand
from backend.application.commands.clear_queue_command import ClearQueueCommand
from backend.application.commands.create_song_command import CreateSongCommand
from backend.application.commands.delete_song_command import DeleteSongCommand
from backend.application.commands.pause_song_command import PauseSongCommand
from backend.application.commands.resume_song_command import ResumeSongCommand
from backend.application.commands.skip_song_in_queue_command import SkipSongInQueueCommand
from backend.application.commands.start_queue_playback_command import StartQueuePlaybackCommand
from backend.application.commands.toggle_repeat_command import ToggleRepeatCommand
from backend.application.queries.get_connection_status_query import GetConnectionStatusQuery
from backend.application.queries.get_queue_state_query import GetQueueStateQuery
from backend.domain.services.context_manager_service import ContextManagerService
from backend.application.queries.list_songs_query import ListSongsQuery
from backend.application.utils.mediator import Mediator
from backend.ports.api.ws_hub import EVENT_LIBRARY, EVENT_QUEUE, EVENT_STATUS, EVENT_PING, Hub
from backend.service.dependency_injection import container


def serialize(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _queue_listener_factory(app: web.Application) -> Callable[[], None]:
    """Build a queue observer that pushes the fresh state to all WS clients.

    The observer is fired synchronously by the :class:`SongQueue` from the
    thread that mutated it — an aiohttp handler, a Discord command, or the
    audio-player thread — so it hops onto the app's event loop with
    ``run_coroutine_threadsafe`` and never blocks the mutation.
    """
    def listener() -> None:
        # Get the running loop from the current thread's context. If we're
        # already on the event loop (e.g. called from an aiohttp handler),
        # schedule the coroutine directly. If we're on another thread, use
        # run_coroutine_threadsafe.
        try:
            loop = asyncio.get_running_loop()
            asyncio.ensure_future(publish_queue(app), loop=loop)
        except RuntimeError:
            # No running loop on this thread — find the app's loop.
            app_loop = getattr(app, '_loop', None)
            if app_loop is not None:
                asyncio.run_coroutine_threadsafe(publish_queue(app), app_loop)
            # else: app not started or shutting down, nothing to do

    return listener


async def publish_queue(app: web.Application) -> None:
    """Push the current queue state to every subscribed client.

    Failures are swallowed — a transient error reading state must never
    break a websocket fan-out.
    """
    try:
        state = serialize(app['mediator'].send(GetQueueStateQuery()))
    except Exception as exc:  # noqa: BLE001
        print(f'[ws] failed to serialize queue state: {exc}')
        return
    await app['hub'].publish(EVENT_QUEUE, state)


async def publish_status(app: web.Application) -> None:
    try:
        state = serialize(app['mediator'].send(GetConnectionStatusQuery()))
    except Exception as exc:  # noqa: BLE001
        print(f'[ws] failed to serialize status: {exc}')
        return
    await app['hub'].publish(EVENT_STATUS, state)


async def publish_library(app: web.Application) -> None:
    try:
        state = serialize(app['mediator'].send(ListSongsQuery(query='', page=0, limit=25)))
    except Exception as exc:  # noqa: BLE001
        print(f'[ws] failed to serialize library: {exc}')
        return
    await app['hub'].publish(EVENT_LIBRARY, state)


async def cors_middleware(app: web.Application, handler):
    async def middleware_handler(request: web.Request):
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    return middleware_handler


def create_app(mediator: Mediator) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app['mediator'] = mediator
    app['hub'] = Hub()

    # Subscribe the hub to *every* queue mutation — including advances that
    # happen inside the audio player when a song finishes, where no API
    # handler runs. The queue object is process-local (the in-memory context
    # manager), so this covers all mutation paths in one place.
    try:
        context_manager = container.resolve(ContextManagerService)
        context_manager.add_queue_listener(_queue_listener_factory(app))
    except Exception:  # noqa: BLE001 - queue events are a no-op without one
        pass

    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/api/status', get_status)
    app.router.add_get('/api/queue', get_queue)
    app.router.add_post('/api/queue/add', add_song_to_queue)
    app.router.add_post('/api/queue/random', add_random_songs)
    app.router.add_post('/api/queue/clear', clear_queue)
    app.router.add_post('/api/queue/play', start_playback)
    app.router.add_post('/api/queue/pause', pause_playback)
    app.router.add_post('/api/queue/resume', resume_playback)
    app.router.add_post('/api/queue/skip', skip_song)
    app.router.add_post('/api/queue/repeat', toggle_repeat)
    app.router.add_get('/api/songs', list_songs)
    app.router.add_post('/api/songs', add_song_to_library)
    app.router.add_delete('/api/songs/{id}', delete_song)

    return app


async def _send_pings(ws: web.WebSocketResponse, interval: float = 20.0) -> None:
    """Send application-level ping frames to keep idle links alive.

    The aiohttp ``heartbeat`` already exercises the protocol (ping/pong), but
    many intermediaries and the admin UI treat the absence of *application*
    traffic as a sign the socket is dead. Emitting a JSON ping every
    ``interval`` seconds keeps both the client's liveness watchdog and any
    idle-timeout proxies happy without relying on real state changes.
    """
    try:
        while not ws.closed:
            await asyncio.sleep(interval)
            if not ws.closed:
                await ws.send_json({'event': EVENT_PING})
    except (asyncio.CancelledError, Exception):  # noqa: BLE001
        # Cancellation is normal on disconnect; a broken peer is pruned by
        # the hub on the next publish.
        pass


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """Long-lived socket the admin UI subscribes to for live state.

    On connect the server pushes a full snapshot (queue, status, library)
    so a freshly opened tab is immediately correct and does not have to
    wait for the next mutation. Thereafter it receives only change events.

    The socket stays open until the client disconnects. A background task
    sends application-level pings so the connection is never considered idle
    by the client or by an intermediary proxy.
    """
    ws = web.WebSocketResponse(heartbeat=25.0, max_msg_size=2 ** 20)
    await ws.prepare(request)

    hub: Hub = request.app['hub']
    mediator: Mediator = request.app['mediator']
    await hub.register(ws)
    ping_task: asyncio.Task | None = None
    try:
        # Send a snapshot so the client converges without racing the first
        # change event. Errors here are non-fatal: the client will fall back
        # to polling until the next event arrives.
        try:
            snapshot: dict[str, Any] = {}
            try:
                snapshot['queue'] = serialize(mediator.send(GetQueueStateQuery()))
            except Exception:  # noqa: BLE001
                snapshot['queue'] = None
            try:
                snapshot['status'] = serialize(mediator.send(GetConnectionStatusQuery()))
            except Exception:  # noqa: BLE001
                snapshot['status'] = None
            try:
                snapshot['library'] = serialize(mediator.send(ListSongsQuery(query='', page=0, limit=25)))
            except Exception:  # noqa: BLE001
                snapshot['library'] = None
            await ws.send_json({'event': 'snapshot', 'data': snapshot})
        except Exception as exc:  # noqa: BLE001
            await ws.send_json({'event': 'error', 'message': str(exc)})

        # Keep the socket alive until the client disconnects. The aiohttp
        # heartbeat (set on WebSocketResponse) sends protocol-level pings and
        # drops the connection if no pong arrives. The ping task additionally
        # sends application-level frames so idle links are never torn down by
        # a client watchdog or an intermediary.
        ping_task = asyncio.create_task(_send_pings(ws))
        while not ws.closed:
            msg = await ws.receive()
            if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                break
            # Client application frames (e.g. explicit "ping" JSON) are ignored;
            # the admin UI is read-only and the server is the source of truth.
    finally:
        if ping_task is not None:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
        await hub.unregister(ws)
    return ws


async def get_status(request: web.Request) -> web.Response:
    try:
        status = request.app['mediator'].send(GetConnectionStatusQuery())
        return web.json_response(serialize(status))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def get_queue(request: web.Request) -> web.Response:
    try:
        queue_state = request.app['mediator'].send(GetQueueStateQuery())
        return web.json_response(serialize(queue_state))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def add_song_to_queue(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        origin = body.get('origin')

        if not origin:
            return web.json_response({'error': 'origin is required'}, status=400)

        mediator = request.app['mediator']
        mediator.send(CreateSongCommand(origin=origin))
        mediator.send(AddSongToQueueCommand(origin=origin))
        return web.json_response({'message': 'Song added successfully'})
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=404)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def add_random_songs(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        count = body.get('count', 10)

        request.app['mediator'].send(AddRandomSongsToQueueCommand(count=count))
        return web.json_response({'message': f'Added {count} random songs to the queue'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def clear_queue(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(ClearQueueCommand())
        return web.json_response({'message': 'Queue cleared'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def start_playback(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(StartQueuePlaybackCommand())
        return web.json_response({'message': 'Playback started'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def pause_playback(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(PauseSongCommand())
        return web.json_response({'message': 'Playback paused'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def resume_playback(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(ResumeSongCommand())
        return web.json_response({'message': 'Playback resumed'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def skip_song(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(SkipSongInQueueCommand())
        return web.json_response({'message': 'Skipped to next song'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def toggle_repeat(request: web.Request) -> web.Response:
    try:
        request.app['mediator'].send(ToggleRepeatCommand())
        return web.json_response({'message': 'Toggled repeat mode'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def add_song_to_library(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        origin = body.get('origin')

        if not origin:
            return web.json_response({'error': 'origin is required'}, status=400)

        song = request.app['mediator'].send(CreateSongCommand(origin=origin))
        await publish_library(request.app)
        return web.json_response(serialize(song))
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=404)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def list_songs(request: web.Request) -> web.Response:
    try:
        query = request.query.get('q', '')
        page = int(request.query.get('page', '0'))
        limit = int(request.query.get('limit', '25'))

        result = request.app['mediator'].send(ListSongsQuery(query=query, page=page, limit=limit))
        return web.json_response(serialize(result))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def delete_song(request: web.Request) -> web.Response:
    try:
        song_id = request.match_info['id']

        request.app['mediator'].send(DeleteSongCommand(id=song_id))
        await publish_library(request.app)
        return web.json_response({'message': 'Song deleted successfully'})
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=404)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


if __name__ == '__main__':
    from backend.service.application_service import get_mediator
    mediator = get_mediator(discord_connect=True)
    web.run_app(create_app(mediator), host='0.0.0.0', port=8080)
