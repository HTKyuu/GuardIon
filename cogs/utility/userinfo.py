import discord
from discord import app_commands
from discord.ext import commands
import datetime

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Show information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        roles = [role.mention for role in member.roles[1:]]  # All roles except @everyone
        roles_str = ", ".join(roles) if roles else "No roles"

        embed = discord.Embed(
            title="User Information",
            color=member.color,
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Name", value=f"{member.name}", inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
        
        if len(roles_str) > 1024:
            roles_str = roles_str[:1021] + "..."
        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str, inline=False)
        
        perms = []
        if member.guild_permissions.administrator:
            perms.append("Administrator")
        if member.guild_permissions.ban_members:
            perms.append("Ban Members")
        if member.guild_permissions.kick_members:
            perms.append("Kick Members")
        if member.guild_permissions.manage_messages:
            perms.append("Manage Messages")
        if member.guild_permissions.manage_roles:
            perms.append("Manage Roles")
        
        key_perms = ", ".join(perms) if perms else "No key permissions"
        embed.add_field(name="Key Permissions", value=key_perms, inline=False)
        
        await interaction.response.send_message(embed=embed)
