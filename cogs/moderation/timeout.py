import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Timeout(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration in minutes",
        reason="The reason for the timeout"
    )
    @mod_command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot timeout this user due to role hierarchy.", ephemeral=True)
            return

        try:
            duration_delta = datetime.timedelta(minutes=duration)
            await member.timeout(duration_delta, reason=reason)
            
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out for {duration} minutes by {interaction.user.mention}",
                color=discord.Color.orange()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"timed out {member.mention} for {duration} minutes",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            log_channel_id = await self.config.get_log_channel(interaction.guild.id)
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Timeout(bot))
