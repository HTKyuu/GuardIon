import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="The reason for the kick"
    )
    @mod_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot kick this user due to role hierarchy.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked by {interaction.user.mention}",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"kicked {member.mention}",
                color=discord.Color.red(),
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
            await interaction.response.send_message("I don't have permission to kick that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Kick(bot))
