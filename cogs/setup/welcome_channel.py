import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import admin_command
import asyncio

class WelcomeChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="setwelcome", description="Set the channel for welcome messages")
    @app_commands.describe(
        channel="The channel to use for welcome messages",
        enabled="Whether to enable or disable welcome messages"
    )
    @admin_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel = None, enabled: bool = None):
        try:
            if channel is None and enabled is None:
                # Check current status
                current_channel_id = await self.config.get_welcome_channel(interaction.guild.id)
                is_enabled = await self.config.is_welcome_enabled(interaction.guild.id)
                
                current_channel = interaction.guild.get_channel(current_channel_id) if current_channel_id else None
                status = f"**Status:** {'🟢 Enabled' if is_enabled else '🔴 Disabled'}\n"
                status += f"**Channel:** {current_channel.mention if current_channel else 'Not set'}"
                
                embed = discord.Embed(
                    title="Welcome Channel Status",
                    description=status,
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed)
                return

            if channel:
                # Test if bot can send messages in the channel
                await channel.send("🔧 Testing welcome channel permissions...", delete_after=1)
                
                # Save to config
                await self.config.set_welcome_channel(interaction.guild.id, channel.id)
                
                embed = discord.Embed(
                    title="Welcome Channel Set",
                    description=f"Successfully set {channel.mention} as the welcome channel!",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Send test message
                test_embed = discord.Embed(
                    title="Welcome Channel Active",
                    description="This channel has been set as the welcome channel. New members will be greeted here.",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await channel.send(embed=test_embed)
            
            if enabled is not None:
                await self.config.toggle_welcome(interaction.guild.id, enabled)
                if not channel:  # Only send this message if we haven't already sent a message about setting the channel
                    status = "enabled" if enabled else "disabled"
                    embed = discord.Embed(
                        title="Welcome Channel Updated",
                        description=f"Welcome messages have been {status}!",
                        color=discord.Color.green() if enabled else discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    await interaction.response.send_message(embed=embed)
            
            # Create log embed
            log_embed = discord.Embed(
                description=f"{'Set welcome channel to ' + channel.mention if channel else ''}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )

            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send messages in that channel! Please check my permissions.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeChannel(bot))
