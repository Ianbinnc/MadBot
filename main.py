import discord
from music_player import MusicPlayer
from config import TOKEN


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.music_player = MusicPlayer(self)

    async def on_message(self, message):
        # Ignore messages sent by the bot
        if message.author == self.user:
            return

        # Join the voice channel and play music
        if message.content.startswith('!play'):
            if message.author.voice:
                channel = message.author.voice.channel

                # Send a loading embed message
                loading_embed = discord.Embed(
                    title="Loading...",
                    description="Your song is being processed. Please wait.",
                    color=discord.Color.blue()
                )
                loading_message = await message.channel.send(embed=loading_embed)

                # Process the play command
                await self.music_player.play(channel, message.content.split(' ', 1)[1], message.channel)

                # delete loading embed and user message
                await loading_message.delete()
                await message.delete()
            else:
                await message.channel.send("You are not in a voice channel.")

        # Pause music
        elif message.content.startswith('!pause'):
            self.music_player.pause()

        # Skip music
        elif message.content.startswith('!skip'):
            await self.music_player.skip()

        if message.content.startswith('!volume'):
            args = message.content.split()
            if len(args) == 2:
                try:
                    volume_level = int(args[1])  # Convert the second argument to an integer
                    self.music_player.change_volume(volume_level)

                    # Create and send an embed message for volume confirmation
                    embed = discord.Embed(title="Volume Changed", description=f"Volume set to {volume_level}%.", color=0x00ff00)
                    await message.channel.send(embed=embed)

                except ValueError:
                    # Send an embed message for invalid volume level
                    embed = discord.Embed(title="Invalid Volume", description="Please provide a valid volume level (0-100).", color=0xff0000)
                    await message.channel.send(embed=embed)

            else:
                # Send an embed message for incorrect usage
                embed = discord.Embed(title="Volume Command Usage", description="Usage: !volume [0-100]", color=0xff5500)
                await message.channel.send(embed=embed)

        # Resume music
        elif message.content.startswith('!resume'):
            self.music_player.resume()

        # Stop music and clear the queue
        elif message.content.startswith('!stop'):
            await self.music_player.stop()

        # Queue Command
        if message.content.startswith('!queue'):
            args = message.content.split()
            # Handles deleting songs from queue
            if len(args) >= 3 and args[1] == 'delete':
                # Assuming the user provides the index to delete
                index_to_delete = int(args[2]) - 1
                self.music_player.delete_from_queue(index_to_delete)
                # Confirmation message
                await message.channel.send(f"Deleted song #{index_to_delete + 1} from the queue.")
            else:
                # Format and send queue
                queue_embed = self.music_player.format_queue()
                await message.channel.send(embed=queue_embed)  # Send the embed directly

        # Shuffle Command
        if message.content.startswith('!shuffle'):
            await self.music_player.shuffle_queue()
            # Embed message when shuffled in blue
            embed = discord.Embed(title="Queue Shuffled", description="The queue has been shuffled.", color=0x0000FF)
            await message.channel.send(embed=embed)


        # Loop Command
        if message.content.startswith('!loop'):
            if 'song' in message.content:
                loop_status = self.music_player.toggle_loop_song()
                loop_type = "song" if loop_status else "disabled"
            else:
                loop_status = self.music_player.toggle_loop_queue()
                loop_type = "queue" if loop_status else "disabled"

            await message.channel.send(f"Loop {loop_type}.")

        # Help Command
        if message.content.startswith('!help'):
            embed = discord.Embed(title="Help", description="Commands for the bot", color=0x00ff00)
            embed.add_field(name="!play", value="Plays a song", inline=False)
            embed.add_field(name="!pause", value="Pauses the song", inline=False)
            embed.add_field(name="!resume", value="Resumes the song", inline=False)
            embed.add_field(name="!stop", value="Stops the song", inline=False)
            embed.add_field(name="!skip", value="Skips the song", inline=False)
            embed.add_field(name="!volume", value="Changes the volume", inline=False)
            embed.add_field(name="!queue", value="Shows the queue", inline=False)
            embed.add_field(name="!shuffle", value="Shuffles the queue", inline=False)
            embed.add_field(name="!loop", value="Loops the queue", inline=False)
            embed.add_field(name="!loop song", value="Loops the song", inline=False)
            embed.add_field(name="!help", value="Shows the help menu", inline=False)
            await message.channel.send(embed=embed)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(TOKEN)


