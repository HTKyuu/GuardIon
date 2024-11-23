import discord
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
import asyncio

class SetupEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Handle auto-role
        auto_role_id = await self.config.get_auto_role(member.guild.id)
        if auto_role_id:  # get_auto_role now returns None if disabled
            role = member.guild.get_role(auto_role_id)
            if role and role < member.guild.me.top_role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    pass  # Silently fail if we can't add the role

        # Handle welcome message
        welcome_channel_id = await self.config.get_welcome_channel(member.guild.id)
        is_welcome_enabled = await self.config.is_welcome_enabled(member.guild.id)
        if welcome_channel_id and is_welcome_enabled:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                try:
                    embed = discord.Embed(
                        title="Welcome!",
                        description=f"Welcome {member.mention} to {member.guild.name}! 🎉",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style='R'))
                    embed.set_footer(text=f"Member #{len(member.guild.members)}")
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass  # Silently fail if we can't send the welcome message

        # Log the join
        log_embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} joined the server",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        log_embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style='R'))
        log_embed.set_thumbnail(url=member.display_avatar.url)
        await self.config.send_log(member.guild, log_embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Handle leave message
        welcome_channel_id = await self.config.get_welcome_channel(member.guild.id)
        is_welcome_enabled = await self.config.is_welcome_enabled(member.guild.id)
        if welcome_channel_id and is_welcome_enabled:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                try:
                    embed = discord.Embed(
                        title="Member Left",
                        description=f"**{member}** has left the server 👋",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    if member.joined_at:
                        embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, style='R'))
                    embed.set_footer(text=f"Now at {len(member.guild.members)} members")
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass  # Silently fail if we can't send the leave message

        # Log the leave
        log_embed = discord.Embed(
            title="Member Left",
            description=f"{member.mention} left the server",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if member.joined_at:
            log_embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, style='R'))
        log_embed.set_thumbnail(url=member.display_avatar.url)
        await self.config.send_log(member.guild, log_embed)

async def setup(bot):
    await bot.add_cog(SetupEvents(bot))
