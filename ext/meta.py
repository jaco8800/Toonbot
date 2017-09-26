import discord,os,datetime,re,asyncio,copy,unicodedata,inspect,psutil,sys
from discord.ext.commands.cooldowns import BucketType
from collections import OrderedDict, deque, Counter
from discord.ext import commands
from .utils import formats

class TimeParser:
	def __init__(self, argument):
		compiled = re.compile(r"(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?")
		self.original = argument
		try:
			self.seconds = int(argument)
		except ValueError as e:
			match = compiled.match(argument)
			if match is None or not match.group(0):
				raise commands.BadArgument('Failed to parse time.') from e
			self.seconds = 0
			hours = match.group('hours')
			if hours is not None:
				self.seconds += int(hours) * 3600
			minutes = match.group('minutes')
			if minutes is not None:
				self.seconds += int(minutes) * 60
			seconds = match.group('seconds')
			if seconds is not None:
				self.seconds += int(seconds)
		if self.seconds < 0:
			raise commands.BadArgument('I don\'t do negative time.')

		if self.seconds > 604800: # 7 days
			raise commands.BadArgument('> Implying I\'ll still be online in a week.')
			
class Meta:
	"""Commands for utilities related to the Bot itself."""
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def clean(self,ctx,number : int = 100):
		""" Deletes my messages from last x in channel"""
		def is_me(m):
			return m.author.id == self.bot.user.id or m.content[0] in self.bot.command_prefix
		mc = self.bot.config[str(ctx.guild.id)]['mod']['channel']
		mc = self.bot.get_channel(mc)
		if ctx.channel == mc:
			await ctx.send("🚫 'Clean' has been disabled for the moderator channel.",delete_after=10)
		else:
			deleted = await ctx.channel.purge(limit=number, check=is_me)
			s = "s" if len(deleted) > 1 else ""
			await ctx.send(f'♻️ {ctx.author.mention}: Deleted {len(deleted)} bot and command messages{s}',delete_after=10)
	
	@commands.command()
	@commands.is_owner()
	async def version(self,ctx):
		""" Get Python version """
		await ctx.send(sys.version)
	
	@commands.command()
	async def hello(self,ctx):
		"""Say hello."""
		await ctx.send(f"Hi {ctx.author.mention}, I'm {ctx.me.display_name}, Painezor coded me to do some shit. Type !help to see my commands.")

	@commands.command(aliases=['reminder','remind','remindme'])
	async def timer(self, ctx, time : TimeParser, *, message=''):
		"""Reminds you of something after a certain amount of time.
		The time can optionally be specified with units such as 'h'
		for hours, 'm' for minutes and 's' for seconds. If no unit
		is given then it is assumed to be seconds. You can also combine
		multiple units together, e.g. 2h4m10s.
		"""

		reminder = None
		completed = None
		message = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
		
		human_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=time.seconds)
		human_time = formats.human_timedelta(human_time)
		
		if not message:
			reminder = f"Sound {ctx.author.mention}, I'll give you a shout in {human_time.replace(' ago', '')} seconds"
			completed = f"Here, {ctx.author.mention}. You asked is to remind you about summit"
		else:
			reminder = f"Areet {ctx.author.mention}, I'll give you a shout about '{message}' in {human_time.replace(' ago', '')}"
			completed = f"Here {ctx.author.mention}, ya asked me to remind you about '{message}' mate"
				
		await ctx.send(reminder)
		await asyncio.sleep(time.seconds)
		await ctx.send(completed)

	@timer.error
	async def timer_error(self, error, ctx):
		if type(error) is commands.BadArgument:
			await ctx.send(str(error))

	async def say_permissions(self, ctx, member, channel):
		permissions = channel.permissions_for(member)
		await formats.entry_to_code(ctx, permissions)

	@commands.command(aliases=['setavatar'])
	@commands.is_owner()
	async def picture(self,ctx,newpic : str):
		""" Change the bot's avatar """
		async with self.bot.session.get(newpic) as resp:
			if resp.status != 200:
				await ctx.send(f"HTTP Error: Status Code {resp.status}")
				return None
			profileimg = await resp.read()
			await self.bot.user.edit(avatar=profileimg)
		
	@commands.command()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def permissions(self, ctx, *, member : discord.Member = None):
		"""Shows a member's permissions."""
		if member is None:
			member = ctx.author
		permissions = ctx.channel.permissions_for(member)
		permissions = "\n".join([f"{i[0]} : {i[1]}" for i in permissions])
		await ctx.send(f"```py\n{permissions}```")
		
		
	@commands.command()
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def botpermissions(self, ctx):
		"""Shows the bot's permissions.
		This is a good way of checking if the bot has the permissions needed
		to execute the commands it wants to execute.
		To execute this command you must have Manage Roles permissions or
		have the Bot Admin role. You cannot use this in private messages.
		"""
		channel = ctx.channel
		member = ctx.me
		await self.say_permissions(ctx, member, channel)
		
	@commands.command()
	@commands.has_permissions(manage_nicknames=True)
	async def name(self,ctx,*,newname: str):
		""" Rename the bot """
		await ctx.me.edit(nick=newname)
		
	@commands.command()
	@commands.is_owner()
	async def game(self,ctx,*,game):
		""" Change what the bot is playing """
		await self.bot.change_presence(game=discord.Game(name=game))

	async def on_socket_response(self, msg):
		self.bot.socket_stats[msg.get('t')] += 1

	@commands.command()
	@commands.is_owner()
	async def commandstats(self,ctx):
		p = commands.Paginator()
		counter = self.bot.commands_used
		width = len(max(counter, key=len))
		total = sum(counter.values())

		fmt = '{0:<{width}}: {1}'
		p.add_line(fmt.format('Total', total, width=width))
		for key, count in counter.most_common():
			p.add_line(fmt.format(key, count, width=width))

		for page in p.pages:
			await ctx.send(page)

	@commands.command()
	@commands.is_owner()
	async def socketstats(self,ctx):
		delta = datetime.datetime.utcnow() - self.bot.uptime
		minutes = delta.total_seconds() / 60
		total = sum(self.bot.socket_stats.values())
		cpm = total / minutes

		fmt = '%s socket events observed (%.2f/minute):\n%s'
		await ctx.send(fmt % (total, cpm, self.bot.socket_stats))

	def get_bot_uptime(self):
		delta = datetime.datetime.utcnow() - self.bot.uptime
		h, remainder = divmod(int(delta.total_seconds()), 3600)
		m, s = divmod(remainder, 60)
		d, h = divmod(h, 24)

		fmt = f'{h}h {m}m {s}s'
		if d:
			fmt = f'{d}d {fmt}'

		return fmt

	@commands.command(aliases=['botstats',"uptime"])
	async def about(self,ctx):
		"""Tells you information about the bot itself."""
		e = discord.Embed(colour = 0x111111,timestamp = self.bot.user.created_at)

		owner = self.bot.get_user((await self.bot.application_info()).owner.id)
		e.set_author(name=f"Owner: {owner}", icon_url=owner.avatar_url)
		
		# statistics
		total_members = sum(len(s.members) for s in self.bot.guilds)
		total_online  = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
		voice = sum(len(g.text_channels) for g in self.bot.guilds)
		text = sum(len(g.voice_channels) for g in self.bot.guilds)
		memory_usage = psutil.Process().memory_full_info().uss / 1024**2
		
		members = f"{total_members} Members\n{total_online} Online\n{len(self.bot.users)} unique"
		e.add_field(name='Members', value=members)
		e.add_field(name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')
		e.add_field(name='Servers', value=len(self.bot.guilds))
		e.add_field(name='Uptime', value=self.get_bot_uptime(),inline=False)
		e.add_field(name='Commands Run', value=sum(self.bot.commands_used.values()))
		e.add_field(name='Memory Usage', value='{:.2f} MiB'.format(memory_usage))
		e.add_field(name='Python Version',value=sys.version)
		e.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')

		m = await ctx.send(embed=e)
		await m.edit(content=" ",embed=e)
		time = f"{str((m.edited_at - m.created_at).microseconds)[:3]}ms"
		e.add_field(name="Ping",value=time)
		await m.edit(content=None,embed=e)
		
def setup(bot):
	bot.commands_used = Counter()
	bot.socket_stats = Counter()
	bot.add_cog(Meta(bot))