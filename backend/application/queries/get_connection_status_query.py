from dataclasses import dataclass
from typing import Optional

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider


@dataclass
class ConnectionStatusDTO:
    connected: bool
    channel_name: Optional[str]


@dataclass
class GetConnectionStatusQuery(Request[Optional[ConnectionStatusDTO]]):
    pass


class GetConnectionStatusQueryHandler(RequestHandler[GetConnectionStatusQuery, Optional[ConnectionStatusDTO]]):
    __channel_connection_provider: ChannelConnectionProvider

    def __init__(self, channel_connection_provider: ChannelConnectionProvider) -> None:
        self.__channel_connection_provider = channel_connection_provider

    def handle(self, request: GetConnectionStatusQuery) -> Optional[ConnectionStatusDTO]:
        connection = self.__channel_connection_provider.get_channel_connection()

        if connection is None:
            return ConnectionStatusDTO(connected=False, channel_name=None)

        return ConnectionStatusDTO(
            connected=True,
            channel_name=connection.channel.name if hasattr(connection.channel, 'name') else str(connection.channel)
        )
