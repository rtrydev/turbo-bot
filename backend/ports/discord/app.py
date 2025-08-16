import os

import discord

from backend.application.commands.add_song_to_queue_command import AddSongToQueueCommand
from backend.application.commands.create_song_command import CreateSongCommand
from backend.application.commands.join_channel_command import JoinChannelCommand
from backend.application.commands.leave_channel_command import LeaveChannelCommand
from backend.application.commands.pause_song_command import PauseSongCommand
from backend.application.commands.resume_song_command import ResumeSongCommand
from backend.application.commands.skip_song_in_queue_command import SkipSongInQueueCommand
from backend.application.commands.start_queue_playback_command import StartQueuePlaybackCommand
from backend.application.commands.toggle_repeat_command import ToggleRepeatCommand
from backend.service.application_service import get_mediator
from backend.service.dependency_injection import container

mediator = get_mediator(discord_connect=True)
client: discord.Client = container.resolve(discord.Client)
tree_cls = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'Logged in to the guild as {client.user}')
    await tree_cls.sync(guild=discord.Object(id=os.environ.get('DISCORD_GUILD_ID')))
    print(f'Available commands: {", ".join([cmd.name for cmd in tree_cls.get_commands()])}')

@tree_cls.command(name='add', description='Add a song to the queue by providing a URL.')
async def add(interaction: discord.Interaction, url: str):
    await interaction.response.defer(ephemeral=True)

    try:
        mediator.send(CreateSongCommand(origin=url))
        mediator.send(AddSongToQueueCommand(origin=url))

        await interaction.followup.send('Song added successfully!')
    except Exception as e:
        await interaction.followup.send(f'Error adding song: {str(e)}')

@tree_cls.command(name='join', description='Join a voice channel.')
async def join(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message('You need to be in a voice channel to use this command.')
        return

    channel = interaction.user.voice.channel

    try:
        mediator.send(JoinChannelCommand(channel=channel))
        await interaction.response.send_message(f'Joined {channel.name}.')
    except Exception as e:
        await interaction.response.send_message(f'Error joining channel: {str(e)}')

@tree_cls.command(name='leave', description='Leave the current voice channel.')
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        await interaction.response.send_message('I am not connected to a voice channel.')
        return

    try:
        mediator.send(LeaveChannelCommand())
        await interaction.response.send_message(f'Left the channel.')
    except Exception as e:
        await interaction.response.send_message(f'Error leaving channel: {str(e)}')

@tree_cls.command(name='start', description='Start playing the song from the queue.')
async def start(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        mediator.send(StartQueuePlaybackCommand())
        await interaction.followup.send('Playing song from queue.')
    except Exception as e:
        await interaction.followup.send(f'Error starting playback: {str(e)}')

@tree_cls.command(name='pause', description='Pause the current playback.')
async def pause(interaction: discord.Interaction):
    try:
        mediator.send(PauseSongCommand())
        await interaction.response.send_message('Paused playback.')
    except Exception as e:
        await interaction.response.send_message(f'Error pausing playback: {str(e)}')

@tree_cls.command(name='resume', description='Resume the current playback.')
async def resume(interaction: discord.Interaction):
    try:
        mediator.send(ResumeSongCommand())
        await interaction.response.send_message('Resumed playback.')
    except Exception as e:
        await interaction.response.send_message(f'Error resuming playback: {str(e)}')

@tree_cls.command(name='skip', description='Skip the current song and play the next one in the queue.')
async def skip(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        mediator.send(SkipSongInQueueCommand())
        await interaction.followup.send('Skipped to the next song in the queue.')
    except Exception as e:
        await interaction.followup.send(f'Error skipping song: {str(e)}')

@tree_cls.command(name='repeat', description='Toggle repeat mode for the current song.')
async def repeat(interaction: discord.Interaction):
    try:
        mediator.send(ToggleRepeatCommand())
        await interaction.response.send_message('Toggled repeat mode.')
    except Exception as e:
        await interaction.response.send_message(f'Error toggling repeat mode: {str(e)}')

if __name__ == '__main__':
    client.run(token=os.environ.get('DISCORD_TOKEN'))
