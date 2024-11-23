from discord.ext import commands

async def setup(bot: commands.Bot):
    # Import all utility cogs
    from .help import Help
    from .userinfo import UserInfo
    from .guildinfo import GuildInfo

    # Add all cogs to the bot
    await bot.add_cog(Help(bot))
    await bot.add_cog(UserInfo(bot))
    await bot.add_cog(GuildInfo(bot))
