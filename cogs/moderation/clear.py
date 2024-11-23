import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="clear", description="Clear a specified number of messages from the channel")
    @app_commands.describe(
        amount="Number of messages to clear (1-100)",
        reason="Reason for clearing messages"
    )
    @mod_command()
    async def clear(self, interaction: discord.Interaction, amount: int, reason: str = None):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Please provide a number between 1 and 100.", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="Messages Cleared",
                description=f"{len(deleted)} messages have been cleared from {interaction.channel.mention}",
                color=discord.Color.blue()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Create log embed
            log_embed = discord.Embed(
                description=f"cleared {len(deleted)} messages in {interaction.channel.mention}",
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
            await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Clear(bot))
