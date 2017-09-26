from discord.ext import commands
from lxml import html
from datetime import datetime
import discord
import aiohttp
import asyncio

class test:
	def __init__(self,bot):
		self.bot = bot
	
	@commands.command()
	@commands.is_owner()
	async def test(self,ctx):
		await ctx.send("Searching by Match Thread")
		f = await self.bot.loop.run_in_executor(None,self.longsrch)
		await ctx.send(f)
	
	def longsrch(self):
		x = self.bot.reddit.subreddit('NUFC').search('flair:"Match Thread"', sort="new", limit=10,syntax="lucene")
		y = [f"{z.title} <{z.url}>" for z in x if z.title.startswith("Match")]
		return "\n".join(y)
				
def setup(bot):
	bot.add_cog(test(bot))