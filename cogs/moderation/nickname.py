import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Nickname(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="nickname", description="Change a member's nickname")
    @app_commands.describe(
        member="The member to change nickname for",
        nickname="The new nickname (leave empty to remove)",
        reason="Reason for the nickname change"
    )
    @mod_command()
    async def nickname(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None, reason: str = None):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot change this user's nickname due to role hierarchy.", ephemeral=True)
            return

        try:
            old_nick = member.nick or member.name
            await member.edit(nick=nickname, reason=reason)
            
            embed = discord.Embed(
                title="Nickname Changed",
                description=f"{member.mention}'s nickname has been changed",
                color=discord.Color.blue()
            )
            embed.add_field(name="Old Nickname", value=old_nick)
            embed.add_field(name="New Nickname", value=nickname or "Reset to username")
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"changed {member.mention}'s nickname",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            log_embed.add_field(name="Old Nickname", value=old_nick)
            log_embed.add_field(name="New Nickname", value=nickname or "Reset to username")
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to change that member's nickname.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Nickname(bot))
