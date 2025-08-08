from backend.application.commands.create_song_command import CreateSongCommand
from backend.application.queries.get_song_by_id_query import GetSongByIdQuery
from backend.service.application_service import get_mediator

if __name__ == '__main__':
    mediator = get_mediator()

    song = mediator.send(CreateSongCommand(
        origin='https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    ))

    print(song)

    song_from_db = mediator.send(GetSongByIdQuery(
        id=song.id
    ))

    print(song_from_db)
