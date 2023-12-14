import discord
import yt_dlp
import asyncio

class MusicPlayer:
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.now_playing = None
        self.voice_client = None

    async def join_channel(self, voice_channel):
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(voice_channel)
        else:
            self.voice_client = await voice_channel.connect()

    def get_audio_url(self, youtube_url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            audio_url = info_dict.get('url', None)
            return audio_url

    async def play_next(self):
        if len(self.queue) > 0:
            self.now_playing = self.queue.pop(0)
            audio_url = self.get_audio_url(self.now_playing)
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }
            self.voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.client.loop))
        else:
            self.now_playing = None
            if self.voice_client:
                await self.voice_client.disconnect()
                self.voice_client = None

    async def play(self, voice_channel, youtube_url):
        await self.join_channel(voice_channel)
        self.queue.append(youtube_url)
        if not self.voice_client.is_playing() and not self.voice_client.is_paused():
            await self.play_next()

    def pause(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()

    def resume(self):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()

    async def stop(self):
        if self.voice_client:
            self.voice_client.stop()
        self.queue.clear()
        self.now_playing = None

