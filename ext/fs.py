from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from lxml import html
from datetime import datetime
from discord.ext import commands
import discord
import asyncio
import json

class FS:
	def __init__(self,bot):
		self.bot = bot
		self.fson = True
		self.msglist = {}
		with open('comps.json') as f:
			self.comps = json.load(f)
		self.bot.fs = bot.loop.create_task(self.flash_scores())
	
	def __unload(self):
		self.fson = False
		self.bot.fs.cancel()
		self.driver.quit()
		
	async def save_comps(self):
		print("Save_comps accessed")
		with await self.bot.configlock:
			with open('comps.json',"w",encoding='utf-8') as f:
				json.dump(self.comps,f,ensure_ascii=True,
						  sort_keys=True,indent=4, separators=(',',':'))
				
	async def _save(self):
		with await self.bot.configlock:
			with open('config.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.config,f,ensure_ascii=True,
						  sort_keys=True,indent=4, separators=(',',':'))

	# The core loop.
	async def flash_scores(self):
		# Spawn our driver
		await self.bot.loop.run_in_executor(None,self.mkdrv)
		# Then start the loop.
		while not self.bot.is_closed() and self.fson:
			if not self.fson:
				return
			# Selenium is blocking.
			newdict = await self.bot.loop.run_in_executor(None,self.fetch_fs)
			await self.do_channels(newdict)
			await self.do_ticker(newdict)
			self.olddict = newdict
			# Done for a minute.
			await asyncio.sleep(60)
	
	def mkdrv(self):
		""" Launches the webdriver """
		self.driver = webdriver.PhantomJS()
		self.driver.get("http://www.flashscore.com")
	
	def fetch_fs(self):
		""" Gets the data from flashscores """
		# Let the page load.
		WebDriverWait(self.driver, 5)
		tree = html.fromstring((self.driver.page_source).encode('utf-8'))
		body = tree.xpath('.//div[@id="fsbody"]')
		
		#If no games
		if not body:
			print("FS module Failed to find games.")
			return None
		
		# Now we start parsing.
		tables = body[0].xpath('.//table[@class="soccer"]')
		ol = dict()
		rl = False
		for i in tables:
			ctry,league = i.xpath('.//span[@class="name"]//text()')
			ctry = ctry.strip().strip(':')
			league = league.strip()
			trs = i.xpath('.//tbody/tr')
			id = 0
			if ctry not in ol:
				ol[ctry] = {league:[]}
			else:
				ol[ctry].update({league:[]})
			if league not in ol[ctry]:
				ol[ctry].append({league:[]})
			if ctry not in self.comps:
				self.comps.update({ctry:[league]})
				print(f"Added {ctry}")
				rl = True
			if league not in self.comps[ctry]:
				self.comps[ctry].append(league)
				print(f"{ctry}:{league} added")
				rl = True
			for j in trs:
				ti = "".join(j.xpath('.//td[3]//text()')).strip()
				ko = "".join(j.xpath('.//td[2]//text()'))
				ho = "".join(j.xpath('.//td[4]/span/text()'))
				hr = j.xpath('.//td[4]//span[contains(@class,"rhcard")]')
				hr = "\🔴" * len(hr)
				sc = "".join(j.xpath('.//td[5]//text()'))
				aw = "".join(j.xpath('.//td[6]/span/text()'))
				ar = j.xpath('.//td[6]//span[contains(@class,"rhcard")]')
				ar = "\🔴" * len(ar)
				
				if ti == "":
					op = f"`🕒{ko}`"
				elif ti == "Finished":
					op = "`✅FT`"
				elif ti == "Half Time":
					op = "`⏸HT`"
				elif ti == "FRO":
					op = "`⚽❔`"
				elif ti == "After Pen.":
					op = "`✅Pen`"
					sc = sc.split('(')
					sc = f"{sc[0]} (p. {sc[1]}"
				elif ti == "Cancelled":
					op = "`🚫CC`"
				elif ti == "Awarded":
					op = "`🚫FF`"
				elif ti.split('+')[0].isdigit():
					op = f"`⚽{ti}'`"
				else:
					op = f"{ti}' | {ko}"
				id += 1
				thisentry = [{"Home":f"{hr}{ho}","Score":sc,"Away":f"{aw}{ar}","Status":op}]
				ol[ctry][league] += thisentry
		if rl:
			self.bot.loop.create_task(self.save_comps())
		return ol
	
	@commands.is_owner()
	@commands.guild_only()
	@commands.group(invoke_without_command=True,hidden=True)
	async def fs(self,ctx):
		""" Displays current livescores channel info """
		try:
			ch = self.bot.config[str(ctx.guild.id)]["FS"]["Channel"]
			c = self.bot.get_channel(int(ch)).mention
			await ctx.send(f"Live score channel for {ctx.guild.name} is {c}")
		except KeyError:
			m = ("The live score channel has not been set on this server, use"
			   f" **{self.bot.command_prefix[0]}{ctx.command.name}** channel "
			   "in the desired channel. Please note this will delete messages"
				"in that channel, so it is preferable to create one.")
			await ctx.send(m)
				
	@fs.group(invoke_without_command=True)
	@commands.guild_only()
	@commands.has_permissions(manage_guild=True)
	async def channel(self,ctx):
		""" Set the live score channel for the guild """
		try:
			self.bot.config[str(ctx.guild.id)]["FS"]["Channel"] = f"{ctx.channel.id}"
		except KeyError:
			self.bot.config[str(ctx.guild.id)]["FS"] = {"Channel":f"{ctx.channel.id}"}
		try:
			self.bot.config[str(ctx.guild.id)]["FS"]["ChFilter"]
		except KeyError:
			self.bot.config[str(ctx.guild.id)]["FS"]["ChFilter"] = []
		await self._save()
		await ctx.send("Outputting live scores list to this channel.")
	
	@fs.command()
	@commands.is_owner()
	async def disable(self,ctx):
		self.bot.config[str(ctx.guild.id)]["FS"]["Channel"] = None
		await self._save()
		await ctx.send("Outputting live scores disabled.")
	
	@fs.group(invoke_without_command=True)
	@commands.has_permissions(manage_guild=True)
	async def filter(self,ctx,*,target):
		""" Shows the current filter for live score channel """
		f = ",".join(self.bot.config[str(ctx.guild.id)]["FS"]["ChFilter"])
		out = f"Currently filtered from livescores channel: {f}"
		await ctx.send(out)
		
	@filter.command()
	@commands.has_permissions(manage_guild=True)
	async def list(self,ctx,country = None):
		""" Lists all countries. Use list <country> to 
		display competitinos from that country.
		"""
		if country is None:
			countries = ", ".join(self.comps.keys())
			await ctx.send(f"**Available Countries:**\n{countries}")
			await ctx.send(f"Use list COUNTRY to view leagues from that cuontry.")
		else:
			try:
				comps = ", ".join([i for i in self.comps[country.upper()]])
				out = f"**Available Competitions from {country}:**\n{comps}"
				await ctx.send(out)
			except KeyError:
				await ctx.send("Invalid country speciified.")
	
	async def do_channels(self,newdict):
		# Loop per guild
		for i in self.bot.config:
			# If not turned on, ignore guild.
			try:
				c = self.bot.config[i]["FS"]["Channel"]
				if c is None:
					continue
			except KeyError:
				continue
			c = self.bot.get_channel(int(c))
			await c.trigger_typing()
			t = ("Fixtures, results, and live scores for **%a %d %b %Y**"
				 " (Refreshed at **%H:%M:%S**)\n\n")
			t = datetime.now().strftime(t)
			# Get blocks.
			blocks = [t]
			for ctry in newdict.keys():
				# we skip if blocked.
				try:
					if ctry in self.bot.config[i]["FS"]["ChFilter"]:
						continue
				except KeyError:
					print(f"Key Error: {i}[fs][chfilter]")
				block = f"\n**{ctry}**"
				for comp in newdict[ctry].keys():
					if comp in self.bot.config[i]["FS"]["ChFilter"]:
						continue
					block += f"\n __{comp}__\n\n"
					for match in newdict[ctry][comp]:
						st = match['Status']
						h = match['Home']
						sc = match['Score']
						a = match['Away']
						block += f"{st} {h} {sc} {a}\n"
				blocks.append(block)
			# Minify blocks
			block = ""
			mini = []
			if not blocks:
				continue
			for i in blocks:
				if len(block) + len(i) < 2000:
					block += i
				else:
					mini.append(block)
					block = i
					if len(block) > 2000:
						block1 = block[:1999]
						block2 = block[2000:]
						mini.append(block1)
						mini.append(block2)
						block = ""

			print(f"{len(mini)} Minified blocks.")
			# Output or edit messages
			if f"{c.id}" in self.msglist and len(self.msglist[f"{c.id}"]) == len(mini):
				print("CONDITION 1")
				z = list(zip(self.msglist[f"{c.id}"],mini))
				for a,b in z:
					if a.content != b:
						await a.edit(content=b)
			else:
				if c.id in self.msglist:
					print("CONDITION 3")
				else:
					print("CONDITION 2")
				await c.purge()
				self.msglist[f"{c.id}"] = []
				for i in mini:
					self.msglist[f"{c.id}"].append(await c.send(i))
					
	async def do_ticker(self,newdict):
		pass
		
			
				
		
	
def setup(bot):
	bot.add_cog(FS(bot))