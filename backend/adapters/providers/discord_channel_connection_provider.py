from typing import Optional

import discord

from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider


class DiscordChannelConnectionProvider(ChannelConnectionProvider):
    __voice_client: Optional[discord.VoiceClient] = None
    __discord_client: discord.Client

    def __init__(self, discord_client: discord.Client) -> None:
        self.__discord_client = discord_client

    def get_channel_connection(self) -> Optional[discord.VoiceClient]:
        if self.__voice_client is not None and self.__voice_client.is_connected():
            return self.__voice_client

        return None

    async def connect_to_channel(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        if self.__voice_client is not None and self.__voice_client.is_connected():
            return self.__voice_client

        self.__voice_client = await channel.connect()
        return self.__voice_client

    async def disconnect_from_channel(self) -> None:
        if self.__voice_client is not None and self.__voice_client.is_connected():
            await self.__voice_client.disconnect()
            self.__voice_client = None
        else:
            raise RuntimeError('No active voice connection to disconnect from.')
