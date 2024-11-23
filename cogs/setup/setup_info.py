import discord
from discord import app_commands
from discord.ext import commands
import datetime

class SetupInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Shows information on how to setup the bot")
    async def setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Bot Setup Guide",
            description="Follow these steps to set up Guard Ion:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        setup_steps = """
        1️⃣ **Basic Setup**
        • Ensure the bot has administrator permissions
        • Use `/help` to view all available commands
        
        2️⃣ **Configure Logging**
        • Create a channel for logs
        • Use `/setlog #channel enabled` to set the log channel
        
        3️⃣ **Configure Welcome Messages**
        • Create a welcome channel
        • Use `/setwelcome #channel enabled` to set the welcome channel
        
        4️⃣ **Configure Auto-Role**
        • Create a role for new members
        • Use `/setrole @role enabled` to set the default role
        """
        
        embed.add_field(name="Setup Steps", value=setup_steps.strip(), inline=False)
        embed.set_footer(text="For additional help, contact cdnkyuu")
        
        await interaction.response.send_message(embed=embed)
