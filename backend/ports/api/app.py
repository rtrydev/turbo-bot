from dataclasses import asdict, is_dataclass
from typing import Any

from aiohttp import web

from backend.application.commands.add_random_songs_to_queue_command import AddRandomSongsToQueueCommand
from backend.application.commands.add_song_to_queue_command import AddSongToQueueCommand
from backend.application.commands.clear_queue_command import ClearQueueCommand
from backend.application.commands.create_song_command import CreateSongCommand
from backend.application.commands.pause_song_command import PauseSongCommand
from backend.application.commands.resume_song_command import ResumeSongCommand
from backend.application.commands.skip_song_in_queue_command import SkipSongInQueueCommand
from backend.application.commands.start_queue_playback_command import StartQueuePlaybackCommand
from backend.application.commands.toggle_repeat_command import ToggleRepeatCommand
from backend.application.queries.get_connection_status_query import GetConnectionStatusQuery
from backend.application.queries.get_queue_state_query import GetQueueStateQuery
from backend.application.queries.list_songs_query import ListSongsQuery
from backend.application.utils.mediator import Mediator


def serialize(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


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

    return app


async def get_status(request: web.Request) -> web.Response:
    try:
        status = mediator.send(GetConnectionStatusQuery())
        return web.json_response(serialize(status))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def get_queue(request: web.Request) -> web.Response:
    try:
        queue_state = mediator.send(GetQueueStateQuery())
        return web.json_response(serialize(queue_state))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def add_song_to_queue(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        origin = body.get('origin')

        if not origin:
            return web.json_response({'error': 'origin is required'}, status=400)

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

        mediator.send(AddRandomSongsToQueueCommand(count=count))

        return web.json_response({'message': f'Added {count} random songs to the queue'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def clear_queue(request: web.Request) -> web.Response:
    try:
        mediator.send(ClearQueueCommand())
        return web.json_response({'message': 'Queue cleared'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def start_playback(request: web.Request) -> web.Response:
    try:
        mediator.send(StartQueuePlaybackCommand())
        return web.json_response({'message': 'Playback started'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def pause_playback(request: web.Request) -> web.Response:
    try:
        mediator.send(PauseSongCommand())
        return web.json_response({'message': 'Playback paused'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def resume_playback(request: web.Request) -> web.Response:
    try:
        mediator.send(ResumeSongCommand())
        return web.json_response({'message': 'Playback resumed'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def skip_song(request: web.Request) -> web.Response:
    try:
        mediator.send(SkipSongInQueueCommand())
        return web.json_response({'message': 'Skipped to next song'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def toggle_repeat(request: web.Request) -> web.Response:
    try:
        mediator.send(ToggleRepeatCommand())
        return web.json_response({'message': 'Toggled repeat mode'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def list_songs(request: web.Request) -> web.Response:
    try:
        query = request.query.get('q', '')
        page = int(request.query.get('page', '0'))
        limit = int(request.query.get('limit', '25'))

        result = mediator.send(ListSongsQuery(query=query, page=page, limit=limit))
        return web.json_response(serialize(result))
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


if __name__ == '__main__':
    web.run_app(create_app(), host='0.0.0.0', port=8080)
