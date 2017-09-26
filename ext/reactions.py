import discord
from discord.ext import commands
import random
import datetime

reactdict = {
			"brighton":["🍾"],
			"cous cous":["🇲🇦"],
			"digi":[":digi:332195917157629953"],
			"gamez":["✝"],
			"gayle":[":windmill:332195722864885761"],
			"mackem":["💩"],
			"mbemba":[":mbemba:332196308825931777"],
			"mitro":["🚒"],
			"ritchie":["✨","🎩"],
			"shelvey":["🇲🇦"],
			"shola":["🚴🏿","🍏"],
			"sunderland":["💩"],
			"voldermort":["🇲🇦"],
			"yedlin":["🇺🇸"],
			}

class Reactions:
	def __init__(self, bot):
		self.bot = bot
		with open('girlsnames.txt',"r") as f:
			self.bot.girls = f.read().splitlines()
	
	async def on_member_update(self,before,after):
		if not before.id == 178631560650686465:
			return
		if before.nick != after.nick:
			async for i in before.guild.audit_logs(limit=1):
				if i.user.id == 178631560650686465:
					await after.edit(nick=random.choice(self.bot.girls).title())	
					
	async def on_member_join(self,member):
		if not member.id == 178631560650686465:
			return
		await member.edit(nick=random.choice(self.bot.girls).title())
		
	async def on_message_delete(self,message):
		if not message.guild.id == 332159889587699712:
			return
		if message.author.bot:
			return
		for i in message.author.roles:
			if i.name == "Moderators":
				return
		for i in self.bot.command_prefix:
			if message.content.startswith(i):
				return
		delchan = self.bot.get_channel(id=335816981423063050)
		e = discord.Embed(title="Deleted Message")
		e.description = f"'{message.content}'"
		e.set_author(name=message.author.name)
		e.add_field(name="User ID",value=message.author.id)
		e.add_field(name="Channel",value=message.channel.mention)
		e.set_thumbnail(url=message.author.avatar_url)
		e.timestamp = datetime.datetime.now()
		e.set_footer(text=f"Created: {message.created_at}")
		e.color = message.author.color
		if message.attachments:
			att = message.attachments[0]
			if hasattr(att,"height"):
				e.add_field(name=f"Attachment info {att.filename} ({att.size} bytes)",value=f"{att.height}x{att.width}")
				e.set_image(url=att.proxy_url)
		await delchan.send(embed=e)
	
	async def on_message(self,m):
		c = m.content.lower()
		# ignore bot messages
		if m.author.bot:
			if c.startswith("/r/") or c.startswith("r/"):
				lf = f"New item in modqueue: <http://www.reddit.com/{m.content}>"
				await m.channel.send(lf)
				await m.delete()
			return
		if m.author.id in self.bot.ignored:
			return
		# Emoji reactions
		if m.guild and m.guild.id == 332159889587699712:
			if "😡✊" in c:
				await m.delete()
			if "toon toon" in c:
				await m.channel.send("**Black and white army.**")
			for string,reactions in reactdict.items():
				if string in c:
					for emoji in reactions:
						await m.add_reaction(emoji)
			autokicks = ["make me a mod","make me mod","give me mod"]
			for i in autokicks:
				if i in c:
					try:
						await m.author.kick(reason="Asked to be made a mod.")
					except:
						return await m.channel.send(f"Done. {m.author.mention} is now a moderator.")
					await m.channel.send(f"{m.author} was auto-kicked.")
					mod = self.bot.get_channel(id=332167195339522048)
					ak = f"{m.author.mention} Auto-kicked: asked to be made a mod"
					await mod.send(f"Auto-kicked {m.author.mention} for asking to be a mod.")
			if "https://www.reddit.com/r/" in c and "/comments/" in c:
				if not "nufc" in c:
					rm = ("*Reminder: Please do not vote on submissions or "
						  "comments in other subreddits.*")
					await m.channel.send(rm)
			
		
def setup(bot):
	bot.add_cog(Reactions(bot))