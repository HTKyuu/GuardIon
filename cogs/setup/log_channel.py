import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import admin_command
import asyncio

class LogChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="setlog", description="Set the channel for logging moderation actions")
    @app_commands.describe(
        channel="The channel to use for logs",
        enabled="Whether to enable or disable logging"
    )
    @admin_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setlog(self, interaction: discord.Interaction, channel: discord.TextChannel = None, enabled: bool = None):
        try:
            if channel is None and enabled is None:
                # Check current status
                current_channel_id = await self.config.get_log_channel(interaction.guild.id)
                is_enabled = await self.config.is_logging_enabled(interaction.guild.id)
                
                current_channel = interaction.guild.get_channel(current_channel_id) if current_channel_id else None
                status = f"**Status:** {'🟢 Enabled' if is_enabled else '🔴 Disabled'}\n"
                status += f"**Channel:** {current_channel.mention if current_channel else 'Not set'}"
                
                embed = discord.Embed(
                    title="Log Channel Status",
                    description=status,
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed)
                return

            if channel:
                # Test if bot can send messages in the channel
                await channel.send("🔧 Testing log channel permissions...", delete_after=1)
                
                # Save to config
                await self.config.set_log_channel(interaction.guild.id, channel.id)
                
                embed = discord.Embed(
                    title="Log Channel Set",
                    description=f"Successfully set {channel.mention} as the log channel!",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Send test log
                log_embed = discord.Embed(
                    title="Log Channel Active",
                    description="This channel has been set as the log channel. You will see moderation logs here.",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await channel.send(embed=log_embed)
            
            if enabled is not None:
                await self.config.toggle_logging(interaction.guild.id, enabled)
                if not channel:  # Only send this message if we haven't already sent a message about setting the channel
                    status = "enabled" if enabled else "disabled"
                    embed = discord.Embed(
                        title="Log Channel Updated",
                        description=f"Logging has been {status}!",
                        color=discord.Color.green() if enabled else discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send messages in that channel! Please check my permissions.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
