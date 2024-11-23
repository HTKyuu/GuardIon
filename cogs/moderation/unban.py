import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="The reason for the unban"
    )
    @mod_command()
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = None):
        try:
            user_id = int(user_id)
            bans = [ban_entry async for ban_entry in interaction.guild.bans()]
            user = discord.utils.get(bans, user__id=user_id)
            
            if user is None:
                await interaction.response.send_message("This user is not banned.", ephemeral=True)
                return

            await interaction.guild.unban(user.user, reason=reason)
            embed = discord.Embed(
                title="User Unbanned",
                description=f"<@{user_id}> has been unbanned by {interaction.user.mention}",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"unbanned <@{user_id}>",
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

        except ValueError:
            await interaction.response.send_message("Please provide a valid user ID.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban users.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Unban(bot))
