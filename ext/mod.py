from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands
import discord
import asyncio
import json


class Mod:
	''' Guild Moderation Commands '''
	def __init__(self, bot):
		self.bot = bot
		
	async def _save(self):
		with await self.bot.configlock:
			with open('config.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.config,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
	
	@commands.group(invoke_without_command=True)
	@commands.has_permissions(view_audit_logs=True)
	async def logs(self,ctx):
		""" View Audit Logs """
		pass
		
	@logs.command()
	async def bans(self,ctx):
		""" View the most recent bans """
		logs = []
		async for i in ctx.guild.audit_logs(limit=100,action=discord.AuditLogAction.ban):
			logs.append(i)
		await ctx.send(logs)
	
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def say(self, ctx,destin:discord.TextChannel = None,*,tosay):
		""" Say something as the bot in specified channel """
		if destin is None:
			destin = ctx
		await ctx.message.delete()
		print(f"{ctx.author} in {destin}: {tosay}")
		await destin.send(tosay)

	@commands.command(aliases=["pin"])
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def pinthis(self,ctx,*,msg):
		""" Pin a message to the current channel """
		await ctx.message.delete()
		topin = await ctx.send(f":pushpin: {ctx.author.mention}: {msg}")
		await topin.pin()
		
	@commands.command()
	@commands.has_permissions(manage_channel=True)
	@commands.bot_has_permissions(manage_channel=True)
	async def topic(self,ctx,*,topic):
		""" Set the topic for the current channel """
		await ctx.channel.edit(topic=topic)
		await ctx.send(f"Topic changed to: '{topic}'")
	
	@commands.has_permissions(manage_messages=True)
	@commands.command()
	async def mute(self,ctx,member:discord.Member):
		""" Mutes a user in this channel """
		ow = discord.PermissionOverwrite()
		ow.send_messages = False
		try:
			await ctx.channel.set_permissions(member,overwrite=ow)
		except Exception as e:
			await ctx.send(f"Error: {e}")
		else:
			await ctx.send(f"{member.mention} has been muted in " 
						   f"{ctx.channel.mention}")

	@commands.has_permissions(kick_members=True)
	@commands.command()
	async def block(self,ctx,member:discord.Member):
		""" Block a user from this channel """
		ow = discord.PermissionOverwrite()
		# Cannot block from default channel.
		if not ctx.channel.id == ctx.guild.id:
			ow.read_messages = False
		ow.send_messages = False
		try:
			await ctx.channel.set_permissions(member,overwrite=ow)
		except Exception as e:
			await ctx.send(f"Error: {e}")
		else:
			if ctx.guild.id == ctx.channel.id:
				m = (f"Cannot block from guild's default channel"
					 f"muted {member.mention} instead.")
			else:
				m = (f"{member.mention} has been blocked from "
					 f"{ctx.channel.mention}")
			await ctx.send(m)
			
	@commands.has_permissions(kick_members=True)
	@commands.command(aliases=["unmute"])
	async def unblock(self,ctx,member:discord.Member):
		""" Unblocks a user from this channel """
		# Get Members who have overwrites set.
		ows = ctx.channel.overwrites
		ows = [i[0] for i in ows if isinstance(i[0],discord.Member)]
		if member in ows:
			try:
				await ctx.channel.set_permissions(member, overwrite=None)
			except Exception as e:
				await ctx.send(f"Error: {e}")
			else:
				await ctx.send(f"Reset permissions for {member.mention} "
							   f"in {ctx.channel.mention}")
		else:
			await ctx.send(f"{member.mention} had no special permissions set")
			
	@commands.command()
	@commands.has_permissions(manage_nicknames=True)
	async def rename(self,ctx,member:discord.Member,nickname:str):
		""" Rename a member """
		try:
			await member.edit(nick=nickname)
		except discord.Forbidden:
			await ctx.send("⛔ I can\'t change that member's nickname.")
		except discord.HTTPException:
			await ctx.send("❔ Member edit failed.")
		else:
			await ctx.send(f"{member.mention} has been renamed.")
			
	@commands.command(aliases=["lastmsg","lastonline","lastseen"])
	@commands.has_permissions(manage_channel=True)
	async def seen(self,ctx,t : discord.Member = None):
		""" Find the last message from a user in this channel """
		if t == None:
			await ctx.send("No user provided",delete_after=15)
			return
		m = await ctx.send("Searching...")
		async for msg in ctx.channel.history(limit=50000):
			if msg.author.id == t.id:
				if t.id == 178631560650686465:
					c = (f"{t.mention} last seen being a spacker in "
						f" {ctx.channel.mention} at {msg.created_at} "
						f"saying '{msg.content}'")
					await m.edit(content=c)
				else:
					c = (f"{t.mention} last seen in {ctx.channel.mention}"
						 f"at {msg.created_at} saying '{msg.content}'")
					await m.edit(content=c)
				return
		await m.edit(content="Couldn't find a recent message from that user.")
	
	@commands.command()
	@commands.has_permissions(kick_members=True)
	async def kick(self,ctx,user : discord.Member,*,reason = "unspecified reason."):
		""" Kicks the user from the server """
		try:
			await ctx.message.delete()
			await user.kick(reason=f"{ctx.author.name}: {reason}")
		except discord.Forbidden:
			await ctx.send("⛔ I can't kick that member.")
		except discord.HTTPException:
			await ctx.send('❔ Kicking failed.')
		else:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
			if reason == "unspecified reason.":
				await ctx.send(f"👢 {user.mention} was kicked by {ctx.author.display_name}.")
			else:
				await ctx.send(f"👢 {user.mention} was kicked by {ctx.author.display_name} for: \"{reason}\".")
	
	@commands.command()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def ban(self,ctx,member : discord.Member,*,reason="Not specified"):
		""" Bans the member from the server """
		try:
			await ctx.message.delete()
			await member.ban(reason=f"{ctx.author.name}: {reason}")
		except discord.Forbidden:
			await ctx.send(f"⛔ Sorry, I can't ban {member.mention}.")
		except discord.HTTPException:
			await ctx.send("❔ Banning failed.")
		else:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
			if reason == "Not specified":
				await ctx.send(f"☠ {member.mention} was banned by {ctx.author.display_name} (No reason provided)")
			else:
				await ctx.send(f"☠ {member.mention} was banned by {ctx.author.display_name} for {reason}.")
	
	@commands.command()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def hackban(self, ctx, *member_ids: int):
		"""Bans a member via their ID."""
		for member_id in member_ids:
			try:
				await self.bot.http.ban(member_id, ctx.message.server.id)
			except discord.HTTPException:
				pass
		await ctx.send('☠ Did some bans. {ctx.author.mention}')
		await ctx.invoke(self.banlist)
	
	@commands.command()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def unban(self,ctx,*,who):
		""" Unbans a user from the server """
		un,discrim = who.split('#')
		for i in await ctx.guild.bans():
			if i.name == un:
				if i.discriminator == discrim:
					try:
						await self.bot.http.unban(i.user.id, ctx.guild.id)
					except discord.Forbidden:
						await ctx.send("⛔ I can\'t unban that user.")
					except discord.HTTPException:
						await ctx.send("❔ Unban failed.")
					else:
						await ctx.send(f"🆗 {who} was unbanned")
	
	@commands.command(aliases=['bans'])
	async def banlist(self,ctx):
		""" Show the banlist for the server """
		banlist = await ctx.guild.bans()
		banned = ""
		e = discord.Embed(color=0x111)
		n = f"≡ {ctx.guild.name} discord ban list"
		e.set_author(name=n,icon_url=ctx.guild.icon_url)
		e.set_thumbnail(url="https://b.thumbs.redditmedia.com/iVPl7BnL44HwSnX_aKil_NudzWffKQlPiVCZPJZDh4M.png")
		if len(banlist) == 0:
			banned = "☠ No bans found!"
		else:
			for x in banlist:
				a = x.user.name
				b = x.user.discriminator
				banned += f"\💀 {a}#{b}: {x.reason}\n"
		e.add_field(name="User (Reason)",value=banned)
		await ctx.send(embed=e)
		
	@commands.group(invoke_without_command=True)
	@commands.has_permissions(manage_guild=True)
	async def mod(self,ctx):
		""" Shows the status of various mod tools """
		try:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
		except KeyError:
			m =f"Mod channel not set, use {self.bot.command_prefix[0]}mod set"
			return await ctx.send(m)
		e = discord.Embed(color=0x7289DA)
		e.description = f"Mod Channel: {mc.mention}\n"
		e.title = f"Config settings for {ctx.guild.name}"
		for i in ['joins','leaves','bans','unbans']:
			try:
				c[i]
			except KeyError:
				c[i] = "Off"
		e.description += f"Joins: `{c['joins']}`\n"
		e.description += f"Leaves: `{c['leaves']}`\n"
		e.description += f"Bans: `{c['bans']}`\n"
		e.description += f"Unbans: `{c['unbans']}`\n"
		e.set_thumbnail(url=ctx.guild.icon_url)
		await ctx.send(embed=e)
		
	@mod.command(name="set")
	@commands.has_permissions(manage_guild=True)
	async def _set(self,ctx):
		""" Set the moderator channel for this server. """
		if not f"{ctx.guild.id}" in self.bot.config:
			thisserv = {f"{ctx.guild.id}":{"mod":{"channel":f"{ctx.guild.id}"}}}
			self.bot.config.update(thisserv)
			cf = f"Mod Channel for {ctx.guild.id} set to {ctx.channel.name}"
		else:
			self.bot.config[f"{ctx.guild.id}"]["mod"]["channel"] = ctx.channel.id
			cf = f"Mod Channel for {ctx.guild.name} set to {ctx.channel.mention}"
		await ctx.send(cf)
		await self._save()
		
	@commands.has_permissions(manage_guild=True)
	@commands.group(invoke_without_command=True)
	async def joins(self,ctx):
		""" Show or hide Join information <Full|On|Off>"""
		try:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
		except KeyError:
			m =f"Mod channel not set, use {self.bot.command_prefix[0]}mod set"
			return await ctx.send(m)
		try:
			status = c["joins"]
		except KeyError:
			c["joins"] = "Off"
		await ctx.send(f"Join messages are currently set to `{status}`")
		
	@joins.command(name="on")
	@commands.has_permissions(manage_guild=True)
	async def _on(self,ctx):
		""" Display Short "Member has joined" message """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["joins"] = "On"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Short join messages will now be output to {ch}")
		await self._save()
		
	@joins.command(name="full")
	@commands.has_permissions(manage_guild=True)
	async def _full(self,ctx):
		""" Display Full "Member has joined" message with embed """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["joins"] = "full"
		ch = self.bot.get_channel(c['channel']).mention
		op = f"Full join messages with user info will now be output to {ch}"
		await ctx.send(op)
		await self._save()
		
	@joins.command(name="off")
	@commands.has_permissions(manage_guild=True)
	async def _off(self,ctx):
		""" Hides "Member has joined" messages """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["joins"] = "Off"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Join messages will no longer be output to {ch}")
		await self._save()
	
	async def on_member_join(self,mem):
		if mem.guild.id == 332159889587699712:
			main = self.bot.get_channel(332163136239173632)
		try:
			j = self.bot.config[f"{mem.guild.id}"]["mod"]["joins"]
			c = self.bot.config[f"{mem.guild.id}"]["mod"]["channel"]
			c = self.bot.get_channel(c)
		except KeyError:
			return
		if j == "full":
			e = discord.Embed()
			e.color = 0x7289DA
			
			s = sum(1 for m in self.bot.get_all_members() if m.id == mem.id)
			e.set_author(name=str(mem), icon_url=mem.avatar_url)
			e.set_footer(text='Member since').timestamp = mem.joined_at
			status = str(mem.status).title()
			e.add_field(name="Status",value=status,inline=True)
			e.add_field(name='ID', value=mem.id,inline=True)
			e.add_field(name='Servers', value=f'{s} shared',inline=True)
			e.add_field(name="Is bot?",value=mem.bot,inline=True)
			if mem.game is not None:
				e.add_field(name='Game',value=mem.game,inline=True)
			e.add_field(name='Created at', value=mem.created_at,inline=True)
			if mem.avatar:
				e.set_thumbnail(url=mem.avatar_url)
			await c.send(f"{mem.mention} joined the server.",embed=e)
		elif j == "On":
			await c.send(f"{mem.mention} joined the server.")
		else:
			return
			
	@commands.has_permissions(manage_guild=True)
	@commands.group(invoke_without_command=True)
	async def leaves(self,ctx):
		""" Show or hide Join information <Full|On|Off>"""
		try:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
		except KeyError:
			m =f"Mod channel not set, use {self.bot.command_prefix[0]}mod set"
			return await ctx.send(m)
		try:
			status = c["leaves"]
		except KeyError:
			c["leaves"] = "Off"
		await ctx.send(f"Leave messages are currently set to `{status}`")
	
	@leaves.command(name="on")
	@commands.has_permissions(manage_guild=True)
	async def lon(self,ctx):
		""" Display "Member has left" message """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["leaves"] = "On"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Leave messages will now be output to {ch}")
		await self._save()

	@leaves.command(name="off")
	@commands.has_permissions(manage_guild=True)
	async def loff(self,ctx):
		""" Hides "Member has joined" messages """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["leaves"] = "Off"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Leave messages will no longer be output to {ch}")
		await self._save()
	
	async def on_member_remove(self,member):
		try:
			l = self.bot.config[f"{member.guild.id}"]["mod"]["leaves"]
			c = self.bot.config[f"{member.guild.id}"]["mod"]["channel"]
			c = self.bot.get_channel(c)
		except KeyError:
			return
		if l == "On":
			async for i in member.guild.audit_logs(limit=1):
				x = i
				if str(x.target) == str(member):
					if x.action.name == "kick":	
						return await c.send(f"👢 **Kick**: {member.mention} by {x.user.mention} for {x.reason}.")
					else:
						print(dir(x.action))
						print(f"Name: {x.action.name}, Category: {x.action.category}, Target Type: {x.action.target_type}, value: {x.action.value}")
				else:
					print(x.target)
					print(dir(x))
			await c.send(f"{member.mention} left the server.")
			
	@commands.has_permissions(manage_guild=True)
	@commands.group(invoke_without_command=True)
	async def banlog(self,ctx):
		""" Show or hide Ban information <On|Off>"""
		try:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
		except KeyError:
			m =f"Mod channel not set, use {self.bot.command_prefix[0]}mod set"
			return await ctx.send(m)
		try:
			status = c["bans"]
		except KeyError:
			c["bans"] = "Off"
		await ctx.send(f"Ban messages are currently set to `{status}`")
		
	@banlog.command(name="on")
	@commands.has_permissions(manage_guild=True)
	async def bon(self,ctx):
		""" Display "Member has been banned" message """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["bans"] = "On"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Ban messages will now be output to {ch}")
		await self._save()

	@banlog.command(name="off")
	@commands.has_permissions(manage_guild=True)
	async def boff(self,ctx):
		""" Hides "Member has been banned" messages """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["bans"] = "Off"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Ban messages will no longer be output to {ch}")
		await self._save()
			
	@commands.has_permissions(manage_guild=True)
	@commands.group(invoke_without_command=True)
	async def unbanlog(self,ctx):
		""" Show or hide Ban information <On|Off>"""
		try:
			c = self.bot.config[f"{ctx.guild.id}"]["mod"]
			mc = self.bot.get_channel(c["channel"])
		except KeyError:
			m =f"Mod channel not set, use {self.bot.command_prefix[0]}mod set"
			return await ctx.send(m)
		try:
			status = c["unbans"]
		except KeyError:
			c["unbans"] = "Off"
		await ctx.send(f"Unban messages are currently set to `{status}`")
		
	@unbanlog.command(name="on")
	@commands.has_permissions(manage_guild=True)
	async def unbon(self,ctx):
		""" Display "Member has been unbanned" message """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["unbans"] = "On"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Unban messages will now be output to {ch}")
		await self._save()

	@unbanlog.command(name="off")
	@commands.has_permissions(manage_guild=True)
	async def unboff(self,ctx):
		""" Hides "Member has been unbanned" messages """
		c = self.bot.config[f"{ctx.guild.id}"]["mod"]
		j = c["unbans"] = "Off"
		ch = self.bot.get_channel(c['channel']).mention
		await ctx.send(f"Unban messages will no longer be output to {ch}")
		await self._save()
		
	async def on_member_unban(self,guild,member):
		try:
			l = self.bot.config[f"{guild.id}"]["mod"]["unbans"]
			c = self.bot.config[f"{guild.id}"]["mod"]["channel"]
			c = self.bot.get_channel(c)
		except KeyError:
			return
		if l == "On":
			await c.send(f"🆗 {member.mention} was unbanned.")
	
	@commands.command()
	@commands.is_owner()
	async def ignore(self,ctx,user : discord.Member,*,reason="Unspecified"):
		""" Ignore commands from a user (reason opptional)"""
		if user.id in self.bot.ignored:
			await ctx.send(f"User {user.mention} is already being ignored.")
		else:
			self.bot.ignored.update({f"{user.id}":reason})
			with open('ignored.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.ignored,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
			await ctx.zend(f"Ignoring commands from {user.mention}.")
		
	
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	@commands.cooldown(1,360,BucketType.user)
	async def delete_all(self,ctx,number:int=100):
		"""
		Cooldown once n hour, deletes last x 
		messages by anyone in the channel
		"""
		for i in self.bot.config:
			if i['mod']['channel'] == ctx.channel.id:
				await ctx.send("⛔ Not in moderator channels.")
				return
		deleted = await ctx.channel.purge(limit=number)
		dlt = len(deleted)
		who = ctx.author.mention
		await ctx.send(f'♻️ {who} Deleted {dlt} of everybodys message(s)',
					   delete_after=60)
		
def setup(bot):
	bot.add_cog(Mod(bot))