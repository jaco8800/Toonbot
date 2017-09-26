from discord.ext import commands
import asyncio
import discord
import youtube_dl

class YoutubeSource(discord.FFmpegPCMAudio):
	def __init__(self, url):
		opts = {
			'format': 'webm[abr>0]/bestaudio/best',
			'prefer_ffmpeg': True,
			'quiet': True
		}
		ytdl = youtube_dl.YoutubeDL(opts)
		info = ytdl.extract_info(url, download=False)
		super().__init__(info['url'])

class Music:
	def __init__(self, bot):
		self.bot = bot
		self.current = None
		self.vc = None
		self.skips = set()
		self.songs = asyncio.Queue()
		
	def __unload(self):
		if self.vc is not None:
			self.bot.loop.create_task(self.vc.disconnect())
		self.vc = None

	async def _play(self,next):
		self.skips = {}
		ffm = discord.FFmpegPCMAudio(next)
		await self.vc.play(ffm,after=self._next)
		
	async def _next(self):
		print("[DEBUG]: _next() accessed")
		if self.vc.is_playing():
			self.vc.stop()
		next = await self.songs.get()
		if next is not None:
			await self._play(next)
		else:
			await self.vc.disconnect()
	
	async def get_info(self, query):
		return await self.loop.run_in_executor(None, lambda: YoutubeSource.info(query))
	
	@commands.is_owner()
	@commands.guild_only()
	@commands.command(hidden=True)
	async def music(self,ctx):
		e = discord.Embed()
		e.color = 0xffffff
		e.title = f"{ctx.guild.name} music"
		e.description = "Now Playing: "
	
	@commands.guild_only()
	@commands.is_owner()
	@commands.command(hidden=True)
	async def play(self, ctx, *, query: str):
		""" Join your voice channel and play a song """
		# Check if currently in voice channel
		if self.vc is None:
			# Join author's voice channel.
			if ctx.author.voice:
				cometo = ctx.author.voice.channel
				self.vc = await cometo.connect()
			else:
				await ctx.send("You are not in a voice channel.")
				return
		else:
			if not ctx.author.voice.channel == self.vc.channel:
				others = self.vc.channel.members
				if len(others) > 1:
					await ctx.send(f"{len(others)} people are listening"
								   f"to music in {self.vc.channel.name}.")
					return
				else:
					# Abandon currently playing task if no listeners
					if self.vc.is_playing():
						self.vc.disconnect()
		# Add to Queue
		await self.songs.put(query)
		if not self.vc.is_playing():
			# Play
			await self._next()
			await ctx.send(f"Trying to play {query}")
	
	@commands.guild_only()
	@commands.is_owner()
	@commands.command(hidden=True)
	async def queue(self,ctx):
		await ctx.send(self.songs._queue)
	
	@commands.guild_only()
	@commands.is_owner()
	@commands.command(hidden=True)
	async def skip(self,ctx):
		if ctx.author.id in self.skips:
			await ctx.send("You've already voted to skip",delete_after=3)
			return
		self.skips.add(ctx.author.id)
		ppl = len(self.vc.channel.members) - 1
		needskips = min(2,ppl/2)
		if self.skips >= needskips:
			await self._next()
		else:
			await ctx.send(f"Skip vote added. {self.skips}/{needskips}")
		
	@commands.guild_only()
	@commands.is_owner()
	@commands.command(hidden=True)
	async def stop(self, ctx):
		await self.vc.disconnect()
		self.vc = None
		await ctx.send('Stopped the music.')
		
def setup(bot):
	bot.add_cog(Music(bot))
