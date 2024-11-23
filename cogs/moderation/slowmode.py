import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="slowmode", description="Set the slowmode delay for the current channel")
    @app_commands.describe(
        seconds="Slowmode delay in seconds (0 to disable)",
        reason="Reason for changing slowmode"
    )
    @mod_command()
    async def slowmode(self, interaction: discord.Interaction, seconds: int, reason: str = None):
        try:
            if seconds < 0:
                await interaction.response.send_message("Slowmode delay cannot be negative.", ephemeral=True)
                return

            await interaction.channel.edit(slowmode_delay=seconds)
            
            embed = discord.Embed(
                title="Slowmode Updated",
                description=f"Slowmode in {interaction.channel.mention} has been {'disabled' if seconds == 0 else f'set to {seconds} seconds'}",
                color=discord.Color.blue()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"{'disabled' if seconds == 0 else f'set'} slowmode in {interaction.channel.mention} {'to ' + str(seconds) + ' seconds' if seconds > 0 else ''}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to change the slowmode in this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Slowmode(bot))
