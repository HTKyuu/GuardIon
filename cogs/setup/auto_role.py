import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils.config_manager import ConfigManager
from utils.command_permissions import admin_command
import asyncio

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        asyncio.create_task(self.config.init())

    @app_commands.command(name="setrole", description="Set the role to be given to new members")
    @app_commands.describe(
        role="The role to automatically assign to new members",
        enabled="Whether to enable or disable auto-role"
    )
    @admin_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setrole(self, interaction: discord.Interaction, role: discord.Role = None, enabled: bool = None):
        try:
            if role is None and enabled is None:
                # Check current status
                current_role_id = await self.config.get_auto_role(interaction.guild.id)
                is_enabled = await self.config.is_auto_role_enabled(interaction.guild.id)
                
                current_role = interaction.guild.get_role(current_role_id) if current_role_id else None
                status = f"**Status:** {'🟢 Enabled' if is_enabled else '🔴 Disabled'}\n"
                status += f"**Role:** {current_role.mention if current_role else 'Not set'}"
                
                embed = discord.Embed(
                    title="Auto-Role Status",
                    description=status,
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed)
                return

            if role:
                # Save to config
                await self.config.set_auto_role(interaction.guild.id, role.id)
                
                embed = discord.Embed(
                    title="Auto-Role Set",
                    description=f"Successfully set {role.mention} as the auto-role!",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if enabled is not None:
                await self.config.toggle_auto_role(interaction.guild.id, enabled)
                if not role:  # Only send this message if we haven't already sent a message about setting the role
                    status = "enabled" if enabled else "disabled"
                    embed = discord.Embed(
                        title="Auto-Role Updated",
                        description=f"Auto-role has been {status}!",
                        color=discord.Color.green() if enabled else discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    await interaction.response.send_message(embed=embed)
            
            # Create log embed
            log_embed = discord.Embed(
                description=f"{'Set auto-role to ' + role.mention if role else ''}",
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
                "I don't have permission to manage that role! Please check my permissions.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        auto_role = await self.config.get_auto_role(member.guild.id)
        if auto_role and await self.config.is_auto_role_enabled(member.guild.id):
            try:
                role = member.guild.get_role(auto_role)
                if role:
                    await member.add_roles(role)
            except discord.Forbidden:
                pass  # Bot doesn't have permission to add roles

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
