from abc import ABC, abstractmethod
from typing import Optional

import discord


class ChannelConnectionProvider(ABC):
    @abstractmethod
    def get_channel_connection(self) -> Optional[discord.VoiceClient]:
        pass

    @abstractmethod
    async def connect_to_channel(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        pass

    @abstractmethod
    async def disconnect_from_channel(self) -> None:
        pass
