import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Softban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="softban", description="Ban and immediately unban a member to clear their messages")
    @app_commands.describe(
        member="The member to softban",
        reason="Reason for the softban",
        days="Number of days of messages to delete (1-7)"
    )
    @mod_command()
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None, days: int = 1):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot softban this user due to role hierarchy.", ephemeral=True)
            return

        if days < 1 or days > 7:
            await interaction.response.send_message("Days must be between 1 and 7.", ephemeral=True)
            return

        try:
            await member.ban(reason=f"Softban: {reason}" if reason else "Softban", delete_message_days=days)
            await member.unban(reason="Softban complete")
            
            embed = discord.Embed(
                title="Member Softbanned",
                description=f"{member.mention} has been softbanned",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Messages Deleted", value=f"Last {days} days")
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"softbanned {member.mention}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.add_field(name="Messages Deleted", value=f"Last {days} days")
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban/unban members.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Softban(bot))
