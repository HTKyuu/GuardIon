import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="The reason for the ban",
        delete_messages="Number of days of messages to delete (0-7)"
    )
    @mod_command()
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None, delete_messages: int = 0):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot ban this user due to role hierarchy.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason, delete_message_days=delete_messages)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned by {interaction.user.mention}",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"banned {member.mention}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            if delete_messages > 0:
                log_embed.add_field(name="Messages Deleted", value=f"Last {delete_messages} days")
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ban(bot))
