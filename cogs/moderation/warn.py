import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import mod_command
import asyncio

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(
        member="The member to warn",
        reason="The reason for the warning"
    )
    @mod_command()
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot warn this user due to role hierarchy.", ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title="Member Warned",
                description=f"{member.mention} has been warned by {interaction.user.mention}",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            
            # DM the warned user
            try:
                dm_embed = discord.Embed(
                    title="Warning Received",
                    description=f"You have received a warning in {interaction.guild.name}",
                    color=discord.Color.yellow(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                if reason:
                    dm_embed.add_field(name="Reason", value=reason)
                await member.send(embed=dm_embed)
            except:
                embed.add_field(name="Note", value="Could not DM user about the warning")

            # Add warning to database
            warning_id = await self.config.add_warning(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                reason
            )

            embed.add_field(name="Warning ID", value=f"#{warning_id}")

            await interaction.response.send_message(embed=embed)

            # Create log embed
            log_embed = discord.Embed(
                description=f"warned {member.mention}",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if reason:
                log_embed.add_field(name="Reason", value=reason)
            log_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            await self.config.send_log(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to warn that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="warns", description="View warnings for a member")
    @app_commands.describe(
        member="The member to view warnings for"
    )
    @mod_command()
    async def warns(self, interaction: discord.Interaction, member: discord.Member):
        try:
            warnings = await self.config.get_warnings(interaction.guild.id, member.id)

            if not warnings:
                embed = discord.Embed(
                    title=f"Warnings for {member.display_name}",
                    description="This member has no warnings.",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await interaction.response.send_message(embed=embed)
                return

            embed = discord.Embed(
                title=f"Warnings for {member.display_name}",
                description=f"Total Warnings: {len(warnings)}",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            for warning_id, mod_id, reason, timestamp in warnings:
                moderator = interaction.guild.get_member(mod_id)
                mod_name = moderator.mention if moderator else "Unknown Moderator"
                
                time_formatted = discord.utils.format_dt(timestamp, style='F')
                time_relative = discord.utils.format_dt(timestamp, style='R')
                
                embed.add_field(
                    name=f"Warning #{warning_id}",
                    value=f"**Reason:** {reason}\n**Moderator:** {mod_name}\n**When:** {time_formatted} ({time_relative})",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="clearwarn", description="Clear a specific warning")
    @app_commands.describe(
        id="The ID of the warning to clear"
    )
    @mod_command()
    async def clearwarn(self, interaction: discord.Interaction, id: int):
        try:
            # Remove warning from database
            if await self.config.remove_warning(interaction.guild.id, id):
                # Send confirmation
                embed = discord.Embed(
                    title="Warning Cleared",
                    description=f"Warning #{id} has been cleared.",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                await interaction.response.send_message(embed=embed)

                # Log the warning clearance
                log_embed = discord.Embed(
                    description=f"cleared warning #{id}",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                log_embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url
                )
                await self.config.send_log(interaction.guild, log_embed)
            else:
                await interaction.response.send_message(f"Warning #{id} not found.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="clearwarns", description="Clear all warnings from a member")
    @app_commands.describe(
        member="The member to clear all warnings from"
    )
    @mod_command()
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        try:
            # Remove all warnings from database
            await self.config.remove_all_warnings(interaction.guild.id, member.id)

            # Send confirmation
            embed = discord.Embed(
                title="All Warnings Cleared",
                description=f"All warnings have been cleared from {member.mention}.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await interaction.response.send_message(embed=embed)

            # Log the warning clearance
            log_embed = discord.Embed(
                title="All Warnings Cleared",
                description=f"{interaction.user.mention} cleared all warnings from {member.mention}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await self.config.send_log(interaction.guild, log_embed)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Warn(bot))
