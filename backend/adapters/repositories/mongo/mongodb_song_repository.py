from dataclasses import asdict
from typing import Optional

from pymongo import MongoClient

from backend.domain.models.song import Song
from backend.domain.repositories.song_repository import SongRepository


class MongoDBSongRepository(SongRepository):
    __mongo_client: MongoClient

    def __init__(self, mongo_client: MongoClient):
        self.__mongo_client = mongo_client

    def create(self, song: Song) -> None:
        if self.get_by_id(song.id):
            return

        collection = self.__get_collection()
        collection.insert_one(asdict(song))

    def get_by_id(self, _id: str) -> Optional[Song]:
        collection = self.__get_collection()
        song_data = collection.find_one({'id': _id})

        if song_data:
            return Song(
                id=song_data['id'],
                fid=song_data['fid'],
                title=song_data['title'],
                origin=song_data['origin'],
                length=song_data['length']
            )

        return None

    def update(self, song: Song) -> None:
        collection = self.__get_collection()
        collection.update_one({'id': song.id}, {'$set': asdict(song)})

    def __get_collection(self):
        return self.__mongo_client.get_database('turbo-bot').get_collection('songs')