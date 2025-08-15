from dataclasses import dataclass

from discord import VoiceChannel


@dataclass
class JoinChannelDTO:
    channel: VoiceChannel
