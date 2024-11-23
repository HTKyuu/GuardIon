import discord
from discord import app_commands
from discord.ext import commands
import datetime

class GuildInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="guildinfo", description="Show information about the server")
    @app_commands.check(lambda interaction: True)
    async def guildinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Get member counts
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        
        embed = discord.Embed(
            title="Server Information",
            description=guild.description or "No description",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # General Information
        embed.add_field(name="Name", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        
        # Member Information
        embed.add_field(name="Members", value=f"""
        👥 Total: {total_members}
        👤 Humans: {humans}
        🤖 Bots: {bots}
        """, inline=True)
        
        # Channel Information
        channels = guild.channels
        text_channels = len([c for c in channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in channels if isinstance(c, discord.CategoryChannel)])
        
        embed.add_field(name="Channels", value=f"""
        💬 Text: {text_channels}
        🔊 Voice: {voice_channels}
        📑 Categories: {categories}
        """, inline=True)
        
        # Server Information
        embed.add_field(name="Server Info", value=f"""
        📅 Created: {guild.created_at.strftime("%Y-%m-%d")}
        🌍 Region: {str(guild.preferred_locale)}
        ✨ Boosts: {guild.premium_subscription_count}
        """, inline=True)
        
        await interaction.response.send_message(embed=embed)
