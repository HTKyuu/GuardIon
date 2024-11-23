import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Bot setup
class ModBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # Prefix won't be used as we're using slash commands
            intents=discord.Intents.all()
        )
        self.initial_extensions = [
            'cogs.moderation',  # This will load all moderation commands
            'cogs.utility',
            'cogs.setup'
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)
        
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Serving {len(self.guilds)} guilds')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over the server"
        ))

# Create bot instance
bot = ModBot()

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))