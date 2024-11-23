import discord
from discord import app_commands
from discord.ext import commands
import datetime

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Guard Ion Commands",
            description="Here are all available commands:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        # Setup Commands
        setup_cmds = """
        `/setup` - View bot setup guide
        `/setlog` - Set the logging channel
        `/setwelcome` - Set the welcome channel
        `/setrole` - Set auto-role for new members
        `/antiinvite` - Toggle anti-invite system
        """
        embed.add_field(name="⚙️ Setup Commands", value=setup_cmds.strip(), inline=False)

        # Mod Commands
        mod_cmds = """
        `/warn` - Warn a member
        `/warns` - View member's warnings
        `/clearwarn` - Clear a specific warning
        `/clearwarns` - Clear all warnings
        `/kick` - Kick a member
        `/ban` - Ban a member
        `/unban` - Unban a user
        `/tempban` - Temporarily ban a member
        `/softban` - Ban and unban to clear messages
        `/timeout` - Timeout a member
        `/unmute` - Remove timeout from a member
        `/clear` - Clear messages
        `/slowmode` - Set channel slowmode
        `/nickname` - Change member nickname
        `/lock` - Lock a channel
        `/unlock` - Unlock a channel
        """
        embed.add_field(name="🛡️ Moderation Commands", value=mod_cmds.strip(), inline=False)

        # Utility Commands
        utility_cmds = """
        `/help` - Show this help message
        `/userinfo` - Show user information
        `/guildinfo` - Show server information
        """
        embed.add_field(name="🔍 Utility Commands", value=utility_cmds.strip(), inline=False)

        # Add permission note
        embed.set_footer(text="Note: Some commands require specific permissions to use. Commands you don't have permission for won't be visible.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
