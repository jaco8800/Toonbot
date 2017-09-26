from discord.ext import commands
import discord, asyncio
import aiohttp

class WolframAlpha:
	def __init__(self,bot):
		self.bot = bot
		
	@commands.command()
	async def WA:
		""" Play with Wolfram Alpha """
		

def setup(bot):
	bot.add_cog(WolramAlpha(bot))