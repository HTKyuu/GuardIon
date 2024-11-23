import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="unmute", description="Remove timeout from a member")
    @app_commands.describe(
        member="The member to unmute",
        reason="Reason for removing the timeout"
    )
    @mod_command()
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot unmute this user due to role hierarchy.", ephemeral=True)
            return

        try:
            if not member.is_timed_out():
                await interaction.response.send_message("This member is not timed out.", ephemeral=True)
                return

            await member.timeout(None, reason=reason)
            
            embed = discord.Embed(
                title="Member Unmuted",
                description=f"{member.mention} has been unmuted",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"unmuted {member.mention}",
                color=discord.Color.green(),
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
            await interaction.response.send_message("I don't have permission to unmute members.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Unmute(bot))
