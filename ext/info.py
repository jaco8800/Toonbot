from discord.ext import commands
from collections import Counter
import discord
import asyncio
import copy


class Info:
	""" Get information about users or servers. """
	def __init__(self,bot):
		self.bot = bot

	@commands.group(invoke_without_command=True)
	@commands.guild_only()
	async def info(self,ctx,*,member: discord.Member = None):
		"""Shows info about a member.
		This cannot be used in private messages. If you don't specify
		a member then the info returned will be yours.
		"""
		if member is None:
			member = ctx.author

		e = discord.Embed()
		roles = [role.name.replace('@', '@\u200b') for role in member.roles]
		shared = sum(1 for m in self.bot.get_all_members() if m.id == member.id)
		voice = member.voice
		if voice is not None:
			voice = voice.channel
			other_people = len(voice.members) - 1
			voice_fmt = f'{voice.name} with {other_people} others' if other_people else f'{voice.name} alone'
			voice = voice_fmt
		else:
			voice = 'Not connected.'

		e.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
		e.set_footer(text='Member since').timestamp = member.joined_at
		e.add_field(name="Status",value=str(member.status).title(),inline=True)
		e.add_field(name='ID', value=member.id,inline=True)
		e.add_field(name='Servers', value='%s shared' % shared,inline=True)
		e.add_field(name='Voice', value=voice,inline=True)
		e.add_field(name="Is bot?",value=member.bot,inline=True)
		e.add_field(name="Source",value="https://github.com/Painezor/Toonbot",inline=True)
		if member.game is not None:
			e.add_field(name='Game',value=member.game,inline=True)
		e.add_field(name='Created at', value=member.created_at,inline=True)
		e.add_field(name='Roles', value=', '.join(roles),inline=True)
		e.colour = member.colour
		if member.avatar:
			e.set_thumbnail(url=member.avatar_url)
		await ctx.send(embed=e)

	@info.command(name='guild', aliases=["server"])
	@commands.guild_only()
	async def server_info(self, ctx):
		""" Shows information about the server """
		guild = ctx.guild
		roles = [role.name.replace('@', '@\u200b') for role in guild.roles]

		secret_member = copy.copy(guild.me)
		secret_member.roles = [guild.default_role]

		# figure out what channels are 'secret'
		secret_channels = 0
		secret_voice = 0
		text_channels = 0
		for channel in guild.channels:
			perms = channel.permissions_for(secret_member)
			is_text = isinstance(channel, discord.TextChannel)
			text_channels += is_text
			if is_text and not perms.read_messages:
				secret_channels += 1
			elif not is_text and (not perms.connect or not perms.speak):
				secret_voice += 1

		regular_channels = len(guild.channels) - secret_channels
		voice_channels = len(guild.channels) - text_channels
		mstatus = Counter(str(m.status) for m in guild.members)

		e = discord.Embed()
		e.add_field(name="Server Name",value=guild.name)
		e.add_field(name='ID', value=guild.id)
		e.add_field(name='Owner', value=guild.owner)
		e.add_field(name="Owner ID",value=guild.owner.id)
		emojis = ""
		for emoji in guild.emojis:
			emojis += str(emoji)
		e.add_field(name="Custom Emojis",value=emojis)
		e.add_field(name="Region",value=str(guild.region).title())
		e.add_field(name="Verification Level",value=str(guild.verification_level).title())
		if guild.icon:
			e.set_thumbnail(url=guild.icon_url)

		fmt = 'Text %s (%s secret)\nVoice %s (%s locked)'
		e.add_field(name='Channels', value=fmt % (text_channels, secret_channels, voice_channels, secret_voice))

		members = f'Total {guild.member_count} ({mstatus["online"]})\nDND:{mstatus["dnd"]}\nIdle {mstatus["idle"]}'
		e.add_field(name='Members', value=members)
		e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else '%s roles' % len(roles))
		e.set_footer(text='Created').timestamp = guild.created_at
		await ctx.send(embed=e)
		
	@commands.command()
	async def avatar(self,ctx,user:discord.User = None):
		""" Shows a member's avatar """
		if user == None:
			await ctx.send(ctx.author.avatar_url)
		else:
			await ctx.send(user.avatar_url)
		
def setup(bot):
	bot.add_cog(Info(bot))
