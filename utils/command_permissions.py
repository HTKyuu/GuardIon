import discord
from discord import app_commands
from discord.ext import commands
from functools import wraps

def admin_command():
    def decorator(func):
        # Set default permissions to require manage server permission
        func.default_permissions = discord.Permissions(manage_guild=True)
        return app_commands.default_permissions(manage_guild=True)(func)
    return decorator

def mod_command():
    def decorator(func):
        # Set default permissions to require moderation permissions
        perms = discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            moderate_members=True
        )
        func.default_permissions = perms
        return app_commands.default_permissions(**{
            "kick_members": True,
            "ban_members": True,
            "manage_messages": True,
            "moderate_members": True
        })(func)
    return decorator

def manager_command():
    def decorator(func):
        # Set default permissions to require channel/role management
        perms = discord.Permissions(
            manage_channels=True,
            manage_roles=True
        )
        func.default_permissions = perms
        return app_commands.default_permissions(
            manage_channels=True,
            manage_roles=True
        )(func)
    return decorator
