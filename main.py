import discord
from music_player import MusicPlayer

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.music_player = MusicPlayer(self)

    async def on_message(self, message):
        # Ignore messages sent by the bot
        if message.author == self.user:
            return
        #Testing----------------------------------------------------------------
        if message.content == '!test':
            await message.channel.send('Test successful!')

        # Join the voice channel and play music
        if message.content.startswith('!play'):
            if message.author.voice:
                channel = message.author.voice.channel
                await self.music_player.play(channel, message.content.split(' ', 1)[1])

        # Pause music
        elif message.content.startswith('!pause'):
            self.music_player.pause()

        # Resume music
        elif message.content.startswith('!resume'):
            self.music_player.resume()

        # Stop music and clear the queue
        elif message.content.startswith('!stop'):
            await self.music_player.stop()

        # Add other commands as needed

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('OTc0MTMwNTQ2NjU5NzEzMDg2.GTBooE.RDWECyRya8GXwfI9tvNKuQVilI0AD54_DoGaw8')


