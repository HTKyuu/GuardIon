import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())
        self.channel_permissions = {}

    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.describe(
        channel="The channel to lock (defaults to current channel)",
        reason="Reason for locking the channel"
    )
    @mod_command()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = None):
        try:
            channel = channel or interaction.channel
            everyone_role = channel.guild.default_role

            # Store current @everyone permissions
            current_overwrite = channel.overwrites_for(everyone_role)
            self.channel_permissions[channel.id] = {
                "send_messages": current_overwrite.send_messages,
                "add_reactions": current_overwrite.add_reactions,
                "create_public_threads": current_overwrite.create_public_threads,
                "create_private_threads": current_overwrite.create_private_threads,
                "send_messages_in_threads": current_overwrite.send_messages_in_threads
            }

            # Lock the channel by setting @everyone permissions
            await channel.set_permissions(everyone_role,
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="Channel Locked",
                description=f"{channel.mention} has been locked.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"locked {channel.mention}",
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
            await interaction.response.send_message("I don't have permission to lock this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(
        channel="The channel to unlock (defaults to current channel)",
        reason="Reason for unlocking the channel"
    )
    @mod_command()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = None):
        try:
            channel = channel or interaction.channel
            everyone_role = channel.guild.default_role

            # Restore original @everyone permissions if they exist
            if channel.id in self.channel_permissions:
                stored_permissions = self.channel_permissions[channel.id]
                
                # Create overwrite object with stored permissions
                overwrite = discord.PermissionOverwrite()
                for perm_name, value in stored_permissions.items():
                    setattr(overwrite, perm_name, value)
                
                # Apply the stored permissions
                await channel.set_permissions(everyone_role, overwrite=overwrite)
                
                # Clear stored permissions
                del self.channel_permissions[channel.id]
            else:
                # If no stored permissions, just remove restrictions
                await channel.set_permissions(everyone_role,
                    send_messages=None,
                    add_reactions=None,
                    create_public_threads=None,
                    create_private_threads=None,
                    send_messages_in_threads=None
                )
            
            # Send confirmation
            embed = discord.Embed(
                title="Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"unlocked {channel.mention}",
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
            await interaction.response.send_message("I don't have permission to unlock this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Lock(bot))
