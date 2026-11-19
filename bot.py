import asyncio
import os
import re
from collections import defaultdict

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
BAD_WORDS = {'дума1', 'дума2'}  # Замени с думите, които искаш да филтрираш.

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
queues = defaultdict(asyncio.Queue)

@bot.event
async def on_ready():
    if not getattr(bot, '_synced', False):
        await bot.tree.sync()
        bot._synced = True
    print(f'Влязъл като {bot.user}')

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f'🎉 Добре дошъл/дошла, {member.mention}, в **{member.guild.name}**!')

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    words = set(re.findall(r'\w+', message.content.casefold(), flags=re.UNICODE))
    if words & BAD_WORDS:
        try:
            await message.delete()
            await message.channel.send(f'{message.author.mention}, моля, без нецензурни думи.', delete_after=8)
        except discord.Forbidden:
            pass
    await bot.process_commands(message)

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch', 'extract_flat': False}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def extract_audio(query):
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = next((item for item in info['entries'] if item), None)
        if not info:
            raise ValueError('Не намерих аудио.')
        return info['url'], info.get('title', 'Непозната песен')

async def play_next(guild_id):
    guild = bot.get_guild(guild_id)
    voice = guild.voice_client if guild else None
    if not voice or not voice.is_connected():
        return
    queue = queues[guild_id]
    if queue.empty():
        return
    query = await queue.get()
    try:
        url, title = await asyncio.to_thread(extract_audio, query)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda error: bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(play_next(guild_id))))
        print(f'▶ {title}')
    except Exception as exc:
        print(f'Грешка при пускане: {exc}')
        await play_next(guild_id)

@bot.tree.command(name='play', description='Пусни песен по име или URL')
@app_commands.describe(song='Име на песен или URL')
async def play(interaction: discord.Interaction, song: str):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.voice:
        await interaction.response.send_message('Първо влез в гласов канал.', ephemeral=True)
        return
    await interaction.response.defer()
    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client
    try:
        if voice and voice.channel != channel:
            await interaction.followup.send('Вече съм в друг гласов канал.')
            return
        if not voice:
            voice = await channel.connect()
        await queues[interaction.guild.id].put(song)
        await interaction.followup.send(f'🎶 Добавено в опашката: **{discord.utils.escape_markdown(song)}**')
        if not voice.is_playing() and not voice.is_paused():
            await play_next(interaction.guild.id)
    except Exception as exc:
        await interaction.followup.send(f'Не успях да пусна музика: {exc}')

def same_voice(interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    return bool(voice and isinstance(interaction.user, discord.Member) and interaction.user.voice and interaction.user.voice.channel == voice.channel)

@bot.tree.command(name='skip', description='Пропусни текущата песен')
async def skip(interaction: discord.Interaction):
    if not same_voice(interaction):
        await interaction.response.send_message('Трябва да си в моя гласов канал.', ephemeral=True)
        return
    voice = interaction.guild.voice_client
    if voice.is_playing() or voice.is_paused():
        voice.stop()
        await interaction.response.send_message('⏭ Пропуснато.')
    else:
        await interaction.response.send_message('Няма активна песен.', ephemeral=True)

@bot.tree.command(name='stop', description='Спри музиката и изчисти опашката')
async def stop(interaction: discord.Interaction):
    if not same_voice(interaction):
        await interaction.response.send_message('Трябва да си в моя гласов канал.', ephemeral=True)
        return
    queues[interaction.guild.id] = asyncio.Queue()
    interaction.guild.voice_client.stop()
    await interaction.response.send_message('⏹ Музиката е спряна.')

@bot.tree.command(name='leave', description='Излез от гласовия канал')
async def leave(interaction: discord.Interaction):
    if not same_voice(interaction):
        await interaction.response.send_message('Трябва да си в моя гласов канал.', ephemeral=True)
        return
    queues[interaction.guild.id] = asyncio.Queue()
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message('👋 Излязох от канала.')

if not TOKEN:
    raise RuntimeError('Липсва DISCORD_TOKEN в .env')
bot.run(TOKEN)
