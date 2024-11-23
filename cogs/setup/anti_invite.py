import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import admin_command
import asyncio
import re

class AntiInvite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        self.invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite)/[a-zA-Z0-9]+')
        asyncio.create_task(self.config.init())

    @app_commands.command(name="antiinvite", description="Toggle anti-invite link feature")
    @app_commands.describe(
        enabled="Enable or disable the anti-invite system"
    )
    @admin_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antiinvite(self, interaction: discord.Interaction, enabled: bool):
        try:
            # Update the setting
            await self.config.set_anti_invite(interaction.guild.id, enabled)
            
            # Send confirmation
            status = "enabled" if enabled else "disabled"
            embed = discord.Embed(
                title="Anti-Invite System Updated",
                description=f"The anti-invite system has been **{status}**.",
                color=discord.Color.green() if enabled else discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Create log embed
            log_embed = discord.Embed(
                description=f"{status} the anti-invite system",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore DMs and bot messages
        if not message.guild or message.author.bot:
            return

        try:
            # Check if anti-invite is enabled
            if not await self.config.is_anti_invite_enabled(message.guild.id):
                return

            # Check if user has manage messages permission
            if message.author.guild_permissions.manage_messages:
                return

            # Check for discord invites
            if self.invite_pattern.search(message.content):
                # Delete the message
                await message.delete()

                # Send warning
                warning = await message.channel.send(
                    f"{message.author.mention} Discord invites are not allowed in this server!",
                    delete_after=5
                )

                # Log the invite link removal
                log_embed = discord.Embed(
                    description=f"Removed invite link from {message.author.mention} in {message.channel.mention}",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                log_embed.set_author(
                    name=self.bot.user.display_name,
                    icon_url=self.bot.user.display_avatar.url
                )
                log_embed.add_field(name="Message Content", value=message.content[:1024])
                await self.config.send_log(message.guild, log_embed)

        except Exception as e:
            print(f"Error in anti-invite system: {e}")

async def setup(bot):
    await bot.add_cog(AntiInvite(bot))
