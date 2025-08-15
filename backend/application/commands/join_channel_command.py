import asyncio
from dataclasses import dataclass

from discord import VoiceChannel

from backend.application.dtos.join_channel_dto import JoinChannelDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider


@dataclass
class JoinChannelCommand(Request[None], JoinChannelDTO):
    channel: VoiceChannel

    @staticmethod
    def from_dto(schema: JoinChannelDTO) -> 'JoinChannelCommand':
        return JoinChannelCommand(
            channel=schema.channel
        )

class JoinChannelCommandHandler(RequestHandler[JoinChannelCommand, None]):
    __channel_connection_provider: ChannelConnectionProvider

    def __init__(self, channel_connection_provider: ChannelConnectionProvider) -> None:
        self.__channel_connection_provider = channel_connection_provider

    def handle(self, request: JoinChannelCommand) -> None:
        if self.__channel_connection_provider.get_channel_connection() is not None:
            raise RuntimeError('Already connected to a voice channel.')

        asyncio.create_task(
            self.__channel_connection_provider.connect_to_channel(request.channel)
        )
