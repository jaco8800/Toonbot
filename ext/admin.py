from discord.ext import commands
import discord, asyncio
import aiohttp
import inspect
import objgraph
import json

# to expose to the eval command
import datetime
from collections import Counter

class Admin:
	"""Code debug & 1oading of modules"""
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.is_owner()
	async def memleak(self,ctx):
		tst = objgraph.show_most_common_types(limit=10)
		obj = objgraph.by_type('function')[1000]
		objgraph.show_backrefs(obj, max_depth=10)
		
	@commands.command()
	@commands.is_owner()
	async def load(self,ctx, *, module : str):
		"""Loads a module."""
		try:
			self.bot.load_extension(module)
		except Exception as e:
			await ctx.send(f':no_entry_sign: {type(e).__name__}: {e}')
		else:
			await ctx.send(f':gear: Loaded {module}')

	@commands.command()
	@commands.is_owner()
	async def unload(self,ctx, *, module : str):
		"""Unloads a module."""
		try:
			self.bot.unload_extension(module)
		except Exception as e:
			await ctx.send(f':no_entry_sign: {type(e).__name__}: {e}')
		else:
			await ctx.send(f':gear: Unloaded {module}')

	@commands.command(name='reload',aliases=["releoad"])
	@commands.is_owner()
	async def _reload(self,ctx, *, module : str):
		"""Reloads a module."""
		try:
			self.bot.unload_extension(module)
			self.bot.load_extension(module)
		except Exception as e:
			await ctx.send(f':no_entry_sign: {type(e).__name__}: {e}')
		else:
			await ctx.send(f':gear: Reloaded {module}')
		
	@commands.command()
	@commands.is_owner()
	async def debug(self, ctx, *, code : str):
		"""Evaluates code."""
		code = code.strip('` ')
		result = None

		env = {
			'bot': self.bot,
			'ctx': ctx,
			'message': ctx.message,
			'guild': ctx.message.guild,
			'channel': ctx.message.channel,
			'author': ctx.message.author
		}
		env.update(globals())
		try:
			result = eval(code, env)
			if inspect.isawaitable(result):
				result = await result
		except Exception as e:
			await ctx.send(f"```py\n{type(e).__name__}: {str(e)}```")
			return
		
		# Send to gist if too long.
		if len(str(result)) > 2000:
			p = {'scope':'gist'}
			tk = self.bot.credentials["Github"]["gisttoken"]
			h={'Authorization':f'token {tk}'}
			payload={"description":"Debug output.",
					 "public":True,
					 "files":{"Output":{"content":result}}}
			cs = self.bot.session
			async with cs.post("https://api.github.com/gists",params=p,
								headers=h,data=json.dumps(payload)) as resp:
					if resp.status != 201:
						await ctx.send(f"{resp.status} Failed uploading to gist.")
					else:
						await ctx.send("Output too long, uploaded to gist"
									   f"{resp.url}")
		else:
			await ctx.send(f"```py\n{result}```")

	@commands.command(aliases=['logout','restart'])
	@commands.is_owner()
	async def kill(self,ctx):
		"""Restarts the bot"""
		await ctx.send(":gear: Restarting.")
		await self.bot.logout()

def setup(bot):
    bot.add_cog(Admin(bot))