from discord.ext import commands

async def setup(bot: commands.Bot):
    # Import all moderation cogs
    from .kick import Kick
    from .ban import Ban
    from .unban import Unban
    from .clear import Clear
    from .timeout import Timeout
    from .unmute import Unmute
    from .warn import Warn
    from .tempban import Tempban
    from .lock import Lock
    from .softban import Softban
    from .slowmode import Slowmode
    from .nickname import Nickname

    # Add all cogs to the bot
    await bot.add_cog(Kick(bot))
    await bot.add_cog(Ban(bot))
    await bot.add_cog(Unban(bot))
    await bot.add_cog(Clear(bot))
    await bot.add_cog(Timeout(bot))
    await bot.add_cog(Unmute(bot))
    await bot.add_cog(Warn(bot))
    await bot.add_cog(Tempban(bot))
    await bot.add_cog(Lock(bot))
    await bot.add_cog(Softban(bot))
    await bot.add_cog(Slowmode(bot))
    await bot.add_cog(Nickname(bot))
