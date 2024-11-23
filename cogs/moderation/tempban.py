import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio
import datetime
import re

class Tempban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())
        self.check_tempbans.start()

    def cog_unload(self):
        self.check_tempbans.cancel()

    def parse_time(self, time_str: str) -> datetime.timedelta:
        """Convert a time string (e.g., '1d', '2h', '30m') to timedelta"""
        time_units = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks'
        }
        
        match = re.match(r'(\d+)([smhdw])', time_str.lower())
        if not match:
            raise ValueError("Invalid time format. Use a number followed by s/m/h/d/w (e.g., 30m, 24h, 7d)")
        
        amount = int(match.group(1))
        unit = time_units[match.group(2)]
        return datetime.timedelta(**{unit: amount})

    @app_commands.command(name="tempban", description="Temporarily ban a member")
    @app_commands.describe(
        member="The member to temporarily ban",
        duration="Duration in minutes",
        reason="The reason for the ban"
    )
    @mod_command()
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        try:
            # Check role hierarchy
            if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message(
                    "You cannot ban this user as their highest role is above or equal to yours.",
                    ephemeral=True
                )
                return

            # Parse duration
            time_delta = datetime.timedelta(minutes=duration)
            unban_time = datetime.datetime.now(datetime.timezone.utc) + time_delta

            reason_text = reason or "No reason provided"
            full_reason = f"{reason_text} (Temporary ban for {duration} minutes)"

            # Add to database first
            await self.config.add_tempban(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                reason_text,
                unban_time.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
            )

            # Ban the user
            await member.ban(reason=full_reason)

            # Send confirmation
            embed = discord.Embed(
                title="User Temporarily Banned",
                description=f"{member.mention} has been banned until {discord.utils.format_dt(unban_time, style='F')}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="Duration", value=f"{duration} minutes")
            if reason:
                embed.add_field(name="Reason", value=reason)
            await interaction.response.send_message(embed=embed)

            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title=f"You have been temporarily banned from {interaction.guild.name}",
                    description=f"You will be unbanned on {discord.utils.format_dt(unban_time, style='F')}",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                user_embed.add_field(name="Duration", value=f"{duration} minutes")
                if reason:
                    user_embed.add_field(name="Reason", value=reason)
                await member.send(embed=user_embed)
            except discord.Forbidden:
                pass

            # Log the ban
            log_embed = discord.Embed(
                description=f"temporarily banned {member.mention} for {duration} minutes",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.add_field(name="Unban Time", value=discord.utils.format_dt(unban_time))
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_tempbans(self):
        """Check for expired tempbans and unban users"""
        try:
            expired_bans = await self.config.get_active_tempbans()
            
            for guild_id, user_id, mod_id, reason, unban_time, ban_time in expired_bans:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                # Unban the user
                try:
                    await guild.unban(discord.Object(id=user_id), reason="Temporary ban expired")
                    await self.config.deactivate_tempban(guild_id, user_id)

                    # Log the unban
                    log_embed = discord.Embed(
                        description=f"{discord.Object(id=user_id).mention} has been automatically unbanned (temporary ban expired)",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    log_embed.add_field(name="Original Ban Reason", value=reason)
                    log_embed.add_field(name="Ban Duration", value=f"From {discord.utils.format_dt(ban_time, 'F')} to {discord.utils.format_dt(unban_time, 'F')}")
                    log_embed.set_author(
                        name=self.bot.user.display_name,
                        icon_url=self.bot.user.display_avatar.url
                    )
                    await self.config.send_log(guild, log_embed)
                except:
                    continue

        except Exception as e:
            print(f"Error in check_tempbans: {e}")

    @check_tempbans.before_loop
    async def before_check_tempbans(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Tempban(bot))
