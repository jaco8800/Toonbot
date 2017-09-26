from discord.ext import commands
from .utils import config

class Permissions:
    """Handles the bot's permission system.
    This is how you disable or enable certain commands
    for your server.
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('permissions.json', loop=bot.loop)

    def __check(self, ctx):
        msg = ctx.message
        if checks.is_owner_check(msg):
            return True
        try:
            entry = self.config[msg.guild.id]
        except (KeyError, AttributeError):
            return True
        else:
            name = ctx.command.qualified_name.split(' ')[0]
            return name not in entry

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def disable(self, ctx, *, command: str):
        """Disables a command for this server."""
        command = command.lower()
        if command in ('enable', 'disable'):
            return await ctx.send('Cannot disable that command.')
        if command not in self.bot.commands:
            return await ctx.send('I do not have this command registered.')
        guild_id = ctx.guild.id
        entries = self.config.get(guild_id, {})
        entries[command] = True
        await self.config.put(guild_id, entries)
        await ctx.send('"%s" command disabled in this server.' % command)

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def enable(self, ctx, *, command: str):
        """Enables a command for this server."""
        command = command.lower()
        guild_id = ctx.guild.id
        entries = self.config.get(guild_id, {})
        try:
            entries.pop(command)
        except KeyError:
            await ctx.send('The command does not exist or is not disabled.')
        else:
            await self.config.put(guild_id, entries)
            await ctx.send(f'"{command}" command enabled in this server.')

def setup(bot):
    bot.add_cog(Permissions(bot))