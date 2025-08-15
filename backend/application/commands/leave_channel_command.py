import asyncio
from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider


@dataclass
class LeaveChannelCommand(Request[None]):
    pass

class LeaveChannelCommandHandler(RequestHandler[LeaveChannelCommand, None]):
    __channel_connection_provider: ChannelConnectionProvider

    def __init__(self, channel_connection_provider: ChannelConnectionProvider) -> None:
        self.__channel_connection_provider = channel_connection_provider

    def handle(self, request: LeaveChannelCommand) -> None:
        asyncio.create_task(
            self.__channel_connection_provider.disconnect_from_channel()
        )
