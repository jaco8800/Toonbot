import discord
from discord.ext import commands

import asyncio
import sqlite3

# Create database connection
conn = sqlite3.connect('quotes.db')
c = conn.cursor()

class quotedb:
	""" Quote Database module """
	def __init__(self,bot):
		self.bot = bot

	@commands.group(invoke_without_command=True,aliases=["quotes"])
	async def quote(self,ctx,*,member:discord.Member = None):
		""" Show random quote (optionally from specific user). Use ".help quote" to view subcommands. """
		if ctx.invoked_subcommand is None:

			if member is not None: # If member provided, show random quote from member.
				c.execute(f"SELECT rowid, * FROM quotes WHERE userid = {member.id} ORDER BY RANDOM()")
				x = c.fetchone()
				if x == None:
					return await ctx.send(f"No quotes found from user {member.mention}")
			elif member == None: # Display a random quote.
				c.execute("SELECT rowid, * FROM quotes ORDER BY RANDOM()")
				x = c.fetchone()
				if x == None:
					return await ctx.send("Quote DB appears to be empty.")
				else:
					await ctx.send("Displaying random quote:")
		author = await self.bot.get_user_info(x[1])
		if not author:
			author = "Deleted User"
			av = discord.Embed.Empty
		else:
			av = author.avatar_url
			author = author.display_name			
		submitter 	= await self.bot.get_user_info(x[5])
		channel 	= self.bot.get_channel(x[3])
		if not submitter:
			submitter = "Deleted User"
		else:
			submitter = submitter.display_name
		em = discord.Embed(title=f"{author} in #{channel}",description=x[2],color=0x7289DA)
		em.set_author(name=f"Quote #{x[0]}",icon_url=av)
		em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
		em.set_footer(text=f"📅 {x[4]} (Added by {submitter}) ")
		await ctx.send(embed=em)

	@quote.command(aliases=["id"])
	async def get(self,ctx,number):
		""" Get a quote by it's QuoteID number """
		if not number.isdigit():
			return
		c.execute(f"SELECT rowid, * FROM quotes WHERE rowid = {number}")
		x = c.fetchone()
		if x == None:
			await ctx.send(f"Quote {number} does not exist.")
			return
		author = await self.bot.get_user_info(x[1])
		if not author:
			author = "Deleted User"
			av = discord.Embed.Empty
		else:
			av = author.avatar_url
			author = author.display_name
		submitter 	= await self.bot.get_user_info(x[5])
		if not submitter:
			submitter = "Deleted User"
		else:
			submitter = submitter.display_name
		channel 	= self.bot.get_channel(x[3])
		em = discord.Embed(title=f"{author} in #{channel}",description=x[2],color=0x7289DA)
		em.set_author(name=f"Quote #{x[0]}",icon_url=av)
		em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
		em.set_footer(text=f"📅 {x[4]} (Added by {submitter}) ")
		await ctx.send(embed=em)
		return
				
	@quote.command(invoke_without_command=True)
	async def add(self,ctx,target):
		""" Add a quote, either by message ID or grabs the last message a user sent """
		if len(ctx.message.mentions) > 0:
			messages = await ctx.history(limit=123).flatten()
			user = ctx.message.mentions[0]
			if ctx.message.author == user:
				await ctx.send("What kind of sad person would quote themself?")
				return
			lastmsg = discord.utils.get(messages,channel=ctx.channel,author=user)
			if lastmsg == None:
				await ctx.send(f":no_entry_sign: Could not find a recent message from {user.mention}")
				return
			else:
				m = await ctx.send("Attempting to add quote to db...")
				insert_tuple = (lastmsg.author.id,lastmsg.content,lastmsg.channel.id,lastmsg.created_at,ctx.author.id)
				c.execute("INSERT INTO quotes VALUES (?,?,?,?,?)",insert_tuple)
				conn.commit()
				c.execute("SELECT rowid, * FROM quotes ORDER BY rowid DESC")
				x = c.fetchone()
				conn.rollback()
				author  	= ctx.guild.get_member(x[1])
				submitter 	= ctx.guild.get_member(x[5])
				channel 	= self.bot.get_channel(x[3])
				em = discord.Embed(title=f"{author.display_name} in #{channel}",description=x[2],color=0x7289DA)
				em.set_author(name=f"Quote #{x[0]}",icon_url=author.avatar_url)
				em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
				em.set_footer(text=f"📅 {x[4]} (Added by {submitter.display_name})")
				await m.edit(content=":white_check_mark: Successfully added to database",embed=em)
		elif target.isdigit():
			m = await ctx.channel.get_message(int(target))
			if m == None:
				await ctx.send(f":no_entry_sign: Could not find message with id {target}")
				return
			else:
				n = await ctx.send("Attempting to add quote to db...")
				insert_tuple = (m.author.id,m.content,m.channel.id,m.created_at,ctx.author.id)
				c.execute("INSERT INTO quotes VALUES (?,?,?,?,?)",insert_tuple)
				conn.commit()
				c.execute("SELECT rowid, * FROM quotes ORDER BY rowid DESC")
				x = c.fetchone()
				conn.rollback()
				author  	= ctx.guild.get_member(x[1])
				submitter 	= ctx.guild.get_member(x[5])
				channel 	= self.bot.get_channel(x[3])
				em = discord.Embed(title=f"{author.display_name} in #{channel}",description=x[2],color=0x7289DA)
				em.set_author(name=f"Quote #{x[0]}",icon_url=author.avatar_url)
				em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
				em.set_footer(text=f"📅 {x[4]} (Added by {submitter.display_name}) ")
				await n.edit(content=":white_check_mark: Successfully added to database",embed=em)
		else:
			await ctx.send(f":no_entry_sign: {target} is not a valid message ID or member.")
	
	@quote.command()
	async def last(self,ctx,arg : discord.Member = None):
		""" Gets the last saved message (optionally from user) """
		if arg == None:
			c.execute("SELECT rowid, * FROM quotes ORDER BY rowid DESC")
			x = c.fetchone()
			if x == None:
				await ctx.send("No quotes found.")
				return
		else:
			c.execute(f"SELECT rowid, * FROM quotes WHERE userid = {arg.id} ORDER BY rowid DESC")
			x = c.fetchone()
			if x == None:
				await ctx.send(f"No quotes found for user {arg.mention}.")
				return
		conn.rollback()
		author  	= ctx.guild.get_member(x[1])
		submitter 	= ctx.guild.get_member(x[5])
		channel 	= self.bot.get_channel(x[3])
		em = discord.Embed(title=f"{author.display_name} in #{channel}",description=x[2],color=0x7289DA)
		em.set_author(name=f"Quote #{x[0]}",icon_url=author.avatar_url)
		em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
		em.set_footer(text=f"📅 {x[4]} (Added by {submitter.display_name})")
		await ctx.send(embed=em)
	
	@quote.command(name="del")
	@commands.is_owner()
	async def _del(self,ctx,id):
		""" Delete quote by quote ID """
		if not id.isdigit():
			await ctx.send("That doesn't look like a valid ID")
		else:
			c.execute(f"SELECT rowid, * FROM quotes WHERE rowid = {id}")
			x = c.fetchone()
			if x == None:
				await ctx.send(f"No quote found with ID #{id}")
				return
			author = await self.bot.get_user_info(x[1])
			if not author:
				author = "Deleted User"
				av = discord.Embed.Empty
			else:
				av = author.avatar_url
				author = author.display_name
			submitter 	= await self.bot.get_user_info(x[5])
			if not submitter:
				submitter = "Deleted User"
			else:
				submitter = submitter.display_name
			channel 	= self.bot.get_channel(x[3])
			em = discord.Embed(title=f"{author} in #{channel}",description=x[2],color=0x7289DA)
			em.set_author(name=f"Quote #{x[0]}",icon_url=av)
			em.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
			em.set_footer(text=f"📅 {x[4]} (Added by {submitter})")
			m = await ctx.send("Delete this quote?",embed=em)
			await m.add_reaction("👍")
			await m.add_reaction("👎")
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(("👍","👎"))
			try:
				res = await self.bot.wait_for("reaction_add",check=check,timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send("Response timed out after 30 seconds, quote not deleted",delete_after=30)
			res = res[0]
			if res.emoji.startswith("👎"):
				await ctx.send("OK, quote not deleted",delete_after=20)
			elif res.emoji.startswith("👍"):
				conn.rollback()
				c.execute(f"DELETE FROM quotes WHERE rowid = {id}")
				await ctx.send(f"Quote #{id} has been deleted.")
				await m.delete()
				await ctx.message.delete()
				conn.commit()

	@quote.command()
	async def stats(self,ctx,arg:discord.Member = None):
		""" See how many times you've been quoted, and how many quotes you've added"""
		if arg == None:
			arg = ctx.author
		c.execute(f"SELECT COUNT(*) FROM quotes WHERE quoterid = {arg.id}")
		y = c.fetchone()[0]
		conn.rollback()
		c.execute(f"SELECT COUNT(*) FROM quotes WHERE userid = {arg.id}")
		x = c.fetchone()[0]
		conn.rollback()
		await ctx.send(f"{arg.mention} has been quoted {x} times, and has added {y} quotes")
		
def setup(bot):
	bot.add_cog(quotedb(bot))
	
def __unload(bot):	
	conn.close()