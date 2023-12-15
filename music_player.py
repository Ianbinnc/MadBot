import discord
import yt_dlp
import asyncio
import random

class MusicPlayer:
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.now_playing = None
        self.voice_client = None
        self.text_channel = None  # Reference to the text channel
        self.now_playing_message = None  # Reference to the 'Now Playing' message
        self.volume = 0.5  # Default volume level (50%)
        self.loop_queue = False
        self.loop_song = False
        self.current_title = None  # Initialize current title

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
            if 'entries' in info_dict:  # It's a playlist
                return [(entry['url'], entry.get('title', 'Unknown Title')) for entry in info_dict['entries']]
            else:  # It's a single video
                audio_url = info_dict.get('url', None)
                title = info_dict.get('title', 'Unknown Title')
                return [(audio_url, title)]

    def change_volume(self, volume_level):
        if 0 <= volume_level <= 100:  # Ensure volume is between 0 and 100
            self.volume = volume_level / 100.0  # Convert to decimal
            if self.voice_client and self.voice_client.source:
                self.voice_client.source.volume = self.volume

    async def play_next(self):
        if self.now_playing_message:
            # Delete the previous 'Now Playing' message
            try:
                await self.now_playing_message.delete()
            except discord.NotFound:
                pass
            self.now_playing_message = None

        if len(self.queue) > 0:
            youtube_url, title = self.queue.pop(0)
            audio_url_list = self.get_audio_url(youtube_url)
            if audio_url_list:
                audio_url, _ = audio_url_list[0]  # Get the first tuple from the list
                self.now_playing = youtube_url
                self.current_title = title

                # Send 'Now Playing' message here and only once
                embed = discord.Embed(title="Now Playing", description=f"[{title}]({youtube_url})", color=0x00ff00)
                if self.text_channel:
                    self.now_playing_message = await self.text_channel.send(embed=embed)

                FFMPEG_OPTIONS = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn',
                }

                # Create the FFmpegPCMAudio source and apply volume control
                audio_source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                audio_source = discord.PCMVolumeTransformer(audio_source, volume=self.volume)
                self.voice_client.play(audio_source, after=self.handle_after)

                if self.loop_queue and not self.loop_song:
                    # Add the song back to the end of the queue if loop_queue is enabled
                    self.queue.append((youtube_url, title))

        else:
            # When queue is empty
            self.now_playing = None
            self.current_title = None
            if self.voice_client and not self.voice_client.is_playing():
                await self.voice_client.disconnect()
                self.voice_client = None


    def handle_after(self, error):
        if error:
            print(f'Error in playback: {error}')
        asyncio.run_coroutine_threadsafe(self.play_next(), self.client.loop)

    async def play(self, voice_channel, search_query, text_channel):
        self.text_channel = text_channel

        is_url = search_query.startswith('http://') or search_query.startswith('https://')
        if not is_url:
            search_query = self.youtube_search(search_query)

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Fetch playlist URLs only
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(search_query, download=False)
                if 'entries' in info_dict:  # It's a playlist
                    playlist_title = info_dict.get('title', 'Unknown Playlist')
                    await self.add_playlist_entries(info_dict['entries'], ydl_opts)
                    await text_channel.send(f"Playlist '{playlist_title}' queued.")
                else:  # It's a single video
                    await self.queue_single_video(info_dict)
            except yt_dlp.utils.DownloadError as e:
                await text_channel.send(f"An error occurred: {e}")

        await self.join_channel(voice_channel)
        if not (self.voice_client.is_playing() or self.voice_client.is_paused()):
            await self.play_next()

    async def add_playlist_entries(self, entries, ydl_opts):
        for entry in entries:
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    video_info = ydl.extract_info(video_url, download=False)
                    if video_info:
                        audio_url = video_info.get('url', None)
                        title = video_info.get('title', 'Unknown Title')
                        self.queue.append((audio_url, title))
            except Exception as e:
                print(f"Skipping unavailable video: {e}")

    async def queue_single_video(self, info_dict):
        audio_url = info_dict.get('url', None)
        title = info_dict.get('title', 'Unknown Title')
        self.queue.append((audio_url, title))

    def youtube_search(self, query):
        ydl_opts = {
            'default_search': 'ytsearch',
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                # Take the first search result
                video_info = info['entries'][0]
                return video_info['webpage_url']  # Return the YouTube URL of the first result

        return None  # Return None if no results were found

    async def skip(self):
        if len(self.queue) > 1 or (self.voice_client and self.voice_client.is_playing()):
            if self.voice_client:
                self.voice_client.stop()
            await self.play_next()
        elif len(self.queue) == 1:
            # If there's only one song, play it directly without stopping
            await self.play_next()
        else:
            # If the queue is empty, just stop
            await self.stop()


    async def shuffle_queue(self):
        if len(self.queue) > 1:
            current_song = self.queue.pop(0)  # Preserve the currently playing song
            random.shuffle(self.queue)
            self.queue.insert(0, current_song)  # Reinsert the currently playing song at the beginning

    def toggle_loop_queue(self):
        self.loop_queue = not self.loop_queue
        return self.loop_queue

    def toggle_loop_song(self):
        self.loop_song = not self.loop_song
        return self.loop_song

    def pause(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            embed = discord.Embed(title="Paused", description="The music has been paused.", color=0xffff00)
            asyncio.create_task(self.text_channel.send(embed=embed))

    def resume(self):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            embed = discord.Embed(title="Resumed", description="The music has resumed playing.", color=0x55ff55)
            asyncio.create_task(self.text_channel.send(embed=embed))

    async def stop(self):
        if self.voice_client:
            self.voice_client.stop()
        self.queue.clear()
        self.now_playing = None

        # Delete 'Now Playing' message when stopping the music
        if self.now_playing_message:
            try:
                await self.now_playing_message.delete()
            except discord.NotFound:
                pass  # The message was already deleted or not found
            self.now_playing_message = None

        # Send a message indicating the music has stopped, if needed
        if self.text_channel:
            embed = discord.Embed(title="Stopped", description="The music has been stopped.", color=0xff0000)
            await self.text_channel.send(embed=embed)


    def format_queue(self):
        if not self.queue:
            return discord.Embed(title="Queue is empty", description="There are no songs in the queue.", color=0xff0000)

        embed = discord.Embed(title="Music Queue", description="Here are the songs in the queue:", color=0x00ff00)
        for idx, (youtube_url, _, title) in enumerate(self.queue, start=1):
            # Integrate the hyperlink directly into the song title
            embed.add_field(name=f'{idx}. [{title}]({youtube_url})', value="\u200b", inline=False)

        return embed

    def delete_from_queue(self, index):
        # Remove a song from the queue by its index
        if 0 <= index < len(self.queue):
            del self.queue[index]

