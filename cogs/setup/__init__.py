from discord.ext import commands

async def setup(bot):
    # Import all setup cogs
    from .log_channel import LogChannel
    from .welcome_channel import WelcomeChannel
    from .auto_role import AutoRole
    from .events import SetupEvents
    from .setup_info import SetupInfo
    from .anti_invite import AntiInvite

    # Add all cogs to the bot
    await bot.add_cog(LogChannel(bot))
    await bot.add_cog(WelcomeChannel(bot))
    await bot.add_cog(AutoRole(bot))
    await bot.add_cog(SetupEvents(bot))
    await bot.add_cog(SetupInfo(bot))
    await bot.add_cog(AntiInvite(bot))
