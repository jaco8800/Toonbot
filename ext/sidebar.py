from discord.ext import commands
import datetime
from PIL import Image
from lxml import html
from io import BytesIO
from prawcore.exceptions import RequestException
import aiohttp
import asyncio
import discord
import math
import praw
import json
import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class Sidebar:
	def __init__(self, bot):
		self.bot = bot
		self.sidebaron = True
		self.nextrun = "Not defined"
		self.subreddit = "NUFC"
		self.sidetask = bot.loop.create_task(self.looptask())
		with open('teams.json') as f:
			self.bot.teams = json.load(f)
		
	def __unload(self):
		self.sidetask.cancel()
		self.sidebaron = False
	
	def nufccheck(message):
		return message.guild.id in [238704683340922882,250252535699341312,306552425144385536,332159889587699712]
	
	@commands.group(invoke_without_command=True)
	@commands.has_permissions(manage_messages=True)
	@commands.check(nufccheck)
	async def sidebar(self,ctx):
		""" Show the status of the sidebar updater, or use sidebar manual """
		e = discord.Embed(title="Sidebar Updater Status",color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images/b/"
			  "b5/Reddit-The-Official-App-Icon.png")
		e.set_thumbnail(url=th)
		if self.sidebaron:
			e.description = "```diff\n+ Enabled```"
			ttn = self.nextrun - datetime.datetime.now()
			ttn = str(ttn).split(".")[0]
			e.set_footer(text=f"Next update in: {ttn}")
		else:
			e.description = "```diff\n- Disabled```"
		
		e.add_field(name="Target Subreddit",value=self.subreddit)
		
		if self.bot.is_owner(ctx.author):
			x =  self.sidetask._state
			if x == "PENDING":
				v = "✅ No problems reported."
			elif x == "CANCELLED":
				v = "```diff\n- Loop aborted.```"
				e.color = 0xff0000
			elif x == "FINISHED":
				v = "```diff\n- Loop finished with error.```"
				z = self.sidetask.exception()
				e.color = 0xff0000
			else:
				v = f"❔ `{self.sidetask._state}`"
			e.add_field(name="Debug Info",value=v,inline=False)
			try:
				e.add_field(name="Reported Error",value=z,inline=False)
			except NameError:
				pass
		await ctx.send(embed=e)

	@sidebar.command()
	@commands.has_permissions(manage_messages=True)
	@commands.check(nufccheck)
	async def manual(self,ctx):
		""" Manually force a sidebar update """
		m = await ctx.send("Getting data...")
		await ctx.trigger_typing()
		# Get Data
		sb,table,fixtures,res,lastres,threads = await self.get_data(m)
		sb = (f"{sb}{table}{fixtures}")
		lastres = lastres + threads
		thetime = datetime.datetime.now().strftime('%a %d %b at %H:%M')
		ts = f"\n#####Sidebar auto-updated {thetime}\n"
		await m.edit(content="Got data. Converting to markup.")
		
		# Get length, iterate results to max length.
		dc = "\n\n[](https://discord.gg/R6mG76J)"
		sb += "* Previous Results\n"
		pr = "\n W|Home|-|Away\n--:|--:|:--:|:--\n"
		
		outlen = 0
		bufferlen = len(pr)
		outblocks = []
		count = 0
		for i in res:
			if count % 20 == 0:
				bufferlen += len(pr)
			totallen = (len(sb + i + ts + lastres + dc) +
					   bufferlen + outlen + 14)
			if totallen < 10220:
				outblocks.append(i)
				outlen += len(i)
				count += 1

		numblocks = (len(outblocks) // 20) + 1
		blocklen = math.ceil(len(outblocks)/numblocks)
		
		reswhead = []
		for i in range(0, len(outblocks), blocklen):
			reswhead.append(outblocks[i:i+blocklen])
		
		reswhead.reverse()

		outlist = ""
		for i in reswhead:
			outlist += pr
			outlist += "".join(i)
			if len(i) < blocklen:
				outlist += ("||||.\n")
		sb += outlist
		
		# Build end of sidebar.
		sb += dc
		sb += ts
		sb += lastres
		# Post
		l = self.bot.loop
		await l.run_in_executor(None,self.post_sidebar,sb)	
		e = discord.Embed(color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
			  "/b/b5/Reddit-The-Official-App-Icon.png")
		e.set_author(icon_url=th,name="Sidebar updater")
		e.description = (f"Sidebar for http://www.reddit.com/r/"
						 f"{self.subreddit} manually updated.")
		e.timestamp = datetime.datetime.now()
		e.set_footer(text=f"{len(sb)} / 10240 Characters")
		await m.edit(content="",embed=e)
		
	@sidebar.command(name="off")
	@commands.has_permissions(manage_messages=True)
	@commands.check(nufccheck)
	async def _off(self,ctx):
		""" Disable sidebar auto-updating """
		if self.tweetson:
			self.tweetson = False
			await ctx.send("Reddit sidebar updater has been disabled.")
		else:
			await ctx.send("Reddit sidebar updater already disabled.")

	@sidebar.command(name="on")
	@commands.has_permissions(manage_messages=True)
	@commands.check(nufccheck)
	async def _on(self,ctx):
		""" Enable Reddit sidebar auto-updating """
		if not self.sidebaron:
			self.sidebaron = True
			await ctx.send("Reddit sidebar updater has been enabled.")
			self.sidetask = self.bot.loop.create_task(self.looptask())
		elif self.sidetask._state in ["FINISHED","CANCELLED"]:
			await ctx.send(f"Restarting {self.sidetask._state} task after"
							"exception {self.sidetask.exception()}.")
			self.sidetask = self.bot.loop.create_task(self.looptask())
		else:
			await ctx.send("Reddit sidebar updater already enabled.")
	
	async def looptask(self):
		while self.sidebaron and not self.bot.is_closed():
			mc = self.bot.get_channel(306552425144385536)
			nowt = datetime.datetime.now()
			if nowt.hour < 18:
				self.nextrun = nowt.replace(hour=18,minute=0,second=0)
			elif 17 < nowt.hour < 22:
				self.nextrun = nowt.replace(hour=22,minute=0,second=0)
			else:
				self.nextrun = nowt.replace(hour=18,minute=0,second=0)
				self.nextrun += datetime.timedelta(days=1)
			runin = self.nextrun - nowt
			await asyncio.sleep(runin.seconds)
			
			m = await mc.send("Sidebar auto-updater task started.")
			sb,table,fixtures,res,lastres,threads = await self.get_data(m)
			sb = (f"{sb}{table}{fixtures}")
			lastres = lastres + threads
			thetime = datetime.datetime.now().strftime('%a %d %b at %H:%M')
			ts = f"\n#####Sidebar auto-updated {thetime}\n"
			
			# Get length, iterate results to max length.
			dc = "\n\n[](https://discord.gg/R6mG76J)"
			sb += "* Previous Results\n"
			pr = "\n W|Home|-|Away\n--:|--:|:--:|:--\n"
			
			outlen = 0
			bufferlen = len(pr)
			outblocks = []
			count = 0
			for i in res:
				if count % 20 == 0:
					bufferlen += len(pr)
				totallen = (len(sb + i + ts + lastres + dc) +
						   bufferlen + outlen + 14)
				if totallen < 10220:
					outblocks.append(i)
					outlen += len(i)
					count += 1

			numblocks = (len(outblocks) // 20) + 1
			blocklen = math.ceil(len(outblocks)/numblocks)
			
			reswhead = []
			for i in range(0, len(outblocks), blocklen):
				reswhead.append(outblocks[i:i+blocklen])
			
			reswhead.reverse()

			outlist = ""
			for i in reswhead:
				outlist += pr
				outlist += "".join(i)
				if len(i) < blocklen:
					outlist += ("||||.\n")
			sb += outlist
			
			# Build end of sidebar.
			sb += ts
			sb += lastres
			sb += dc
			# Post
			l = self.bot.loop
			await l.run_in_executor(None,self.post_sidebar,sb)	
			
			e = discord.Embed(color=0xff4500)
			th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
				  "/b/b5/Reddit-The-Official-App-Icon.png")
			e.set_author(icon_url=th,name="Sidebar updater")
			e.description = (f"Sidebar for http://www.reddit.com/r/"
							 f"{self.subreddit} auto-updated.")
			e.timestamp = datetime.datetime.now()
			e.set_footer(text=f"{len(sb)} / 10240 Characters")
			await m.edit(content="",embed=e)

	@sidebar.command(aliases=["captext","text"])
	@commands.has_permissions(manage_messages=True)
	async def caption(self,ctx,*,captext):
		await ctx.trigger_typing()
		s = await self.bot.loop.run_in_executor(None,self.get_current_sidebar)
		wk = await self.bot.loop.run_in_executor(None,self.get_sidebar)
		captext = f"---\n\n> {captext}\n\n---"
		wk = re.sub(r'\-\-\-.*?\-\-\-',captext,wk,flags=re.DOTALL)
		s = re.sub(r'\-\-\-.*?\-\-\-',captext,s,flags=re.DOTALL)
		await self.bot.loop.run_in_executor(None,self.post_wiki,wk)
		await self.bot.loop.run_in_executor(None,self.post_sidebar,s)
		e = discord.Embed(color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
			  "/b/b5/Reddit-The-Official-App-Icon.png")
		e.set_author(icon_url=th,name="Sidebar updater")
		e.description = (f"Sidebar caption for http://www.reddit.com/r/"
						 f"{self.subreddit} updated.")
		e.timestamp = datetime.datetime.now()
		e.set_footer(text=f"{len(s)} / 10240 Characters")
		await ctx.send(embed=e)
		
	def get_current_sidebar(self):
		try:
			s = self.bot.reddit.subreddit(f'{self.subreddit}')
			s = s.description
			return s
		except RequestException:
			print("Failed at get_sidebar, retrying.")
			if not self.bot.is_closed():
				s = self.get_sidebar()
				return s
		else:
			return s
	
	@sidebar.command()
	@commands.has_permissions(manage_messages=True)
	async def image(self,ctx,*,link=""):
		if not ctx.message.attachments:
			print("No attachments.")
			if not link:
				return await ctx.send("Upload the image with the command, or provide a link to the image.")
			async with self.bot.session.get(link) as resp:
				if resp.status != 200:
					return await ctx.send(f"{link} returned error status {resp.status}")
				image = await resp.content.read()
		else:	
			async with self.bot.session.get(ctx.message.attachments[0].url) as resp:
				if resp.status != 200:
					return await ctx.send("Something went wrong retrieving the image from discord.")
				image = await resp.content.read()
		im = Image.open(BytesIO(image))
		im.save('sidebar.png')
		s = self.bot.reddit.subreddit(f'{self.subreddit}')
		try:
			s.stylesheet.upload('sidebar', 'sidebar.png')
		except:
			return await ctx.send("Failed. File too large?")
		style = s.stylesheet().stylesheet
		s.stylesheet.update(style,reason="Update sidebar image")
		await ctx.send(f"Sidebar image changed on http://www.reddit.com/r/{self.subreddit}")
		

	def post_wiki(self,newside):
		print("Post_wiki ACCESSED.")
		try:
			s = self.bot.reddit.subreddit(f'{self.subreddit}')
			s.wiki['sidebar'].edit(newside,reason="SideCaption")
		except RequestException as e:
			print(e)
			print("Failed at post_wiki, retrying.")
			if not self.bot.is_closed():
				self.post_wiki(newside)
			
	def get_sidebar(self):
		try:
			s = self.bot.reddit.subreddit(f'{self.subreddit}')
			s = s.wiki['sidebar'].content_md
			return s
		except RequestException:
			print("Failed at get_sidebar, retrying.")
			if not self.bot.is_closed():
				s = self.get_sidebar()
				return s
		else:
			return s
	
	def post_sidebar(self,sidebar):
		keyColor = self.bot.reddit.subreddit(f"{self.subreddit}").key_color
		try:
			s = self.bot.reddit.subreddit(f"{self.subreddit}")
			s.mod.update(description=sidebar,key_color=keyColor)
		except RequestException:
			print("Failed at post_sidebar")
			if not self.bot.is_closed():
				self.post_sidebar(sidebar)
				
	async def get_data(self,m):
		if self.sidebaron:
			table=fixtures=results=threads="Retry"
			sb = await self.bot.loop.run_in_executor(None,self.get_sidebar)
			while "Retry" in [table,fixtures,results]:
				if not self.sidebaron:
					return None
				if table == "Retry":
					table = await self.table()
					await m.edit(content="Got table, getting fixtures...")
				if fixtures == "Retry":
					fixtures = await self.bot.loop.run_in_executor(None,self.fixtures)
					await m.edit(content="Got fixtures getting results...")
				if results == "Retry":
					results,lastres,lastop = await self.bot.loop.run_in_executor(None,self.results)
					await m.edit(content="Got results, finding pre/post/match threads....")
				if threads == "Retry":
					threads = await self.bot.loop.run_in_executor(None,self.threads,lastop)
				if "Retry" in [table,fixtures,results]:
					time.sleep(5)
			return sb,table,fixtures,results,lastres,threads
		else:
			return None
	
	def threads(self,lastop):
		trds = []
		lastop = lastop.split(" ")[0]
		toappend = "#"
		for submission in self.bot.reddit.subreddit('NUFC').search('flair:"Pre-match thread"', sort="new", limit=10,syntax="lucene"):
			if lastop in submission.title:
				toappend = submission.url
				break
		trds.append(toappend)
		toappend = "#"
		for submission in self.bot.reddit.subreddit('NUFC').search('flair:"Match thread"', sort="new", limit=10,syntax="lucene"):
			if not submission.title.startswith("Match"):
				continue
			if lastop in submission.title:
				toappend = submission.url
				break
		trds.append(toappend)
		toappend = "#"
		for submission in self.bot.reddit.subreddit('NUFC').search('flair:"Post-match thread"', sort="new", limit=10,syntax="lucene"):
			if lastop in submission.title:
				toappend = submission.url
				break
		trds.append(toappend)
		pre = "Pre" if trds[0] == "#" else f"[Pre]({trds[0].split('?ref=')[0]})"
		match = "Match" if trds[1] == "#" else f"[Match]({trds[1].split('?ref=')[0]})"
		post = "Post" if trds[2] == "#" else f"[Post]({trds[2].split('?ref=')[0]})"
		threads = f"\n\n### {pre} - {match} - {post}"
		return threads
	
	async def table(self):
		cs = self.bot.session
		url = 'http://www.bbc.co.uk/sport/football/premier-league/table'
		async with cs.get(url) as resp:
			if resp.status != 200:
				return "Retry"
			tree = html.fromstring(await resp.text())
		xp = './/table[contains(@class,"gs-o-table")]//tbody/tr'
		tablerows = tree.xpath(xp)[:20]
		table = ("\n\n* Premier League Table"
		         "\n\n Pos.|Team *click to visit subreddit*|P|W|D|L|GD|Pts"
				 "\n--:|:--|:--:|:--:|:--:|:--:|:--:|:--:\n")
		for i in tablerows:
			p = i.xpath('.//td//text()')
			r = p[0].strip() # Ranking
			m = p[1].strip() # Movement
			m = m.replace("team hasn't moved",'[](#icon-nomove)')
			m = m.replace('team has moved up','[](#icon-up)')
			m = m.replace('team has moved down','[](#icon-down)')
			t = p[2]		 # Team
			t = f"[{t}]({self.bot.teams[t]['subreddit']})"
			pd = p[3]		 # Played
			w = p[4]         # Wins
			d = p[5]	     # Drawn
			l = p[6]		 # Lost
			gf = p[7]        # Goals For
			ga = p[8]        # Goals Against
			gd = p[9]        # GoalDiff
			pts = p[10]      # Points
			form = p[11]
			table += f"{r} {m}|{t}|{pd}|{w}|{d}|{l}|{gd}|{pts}\n"
		return table

	async def scorers(self):
		cs = self.bot.session
		url = ("http://www.bbc.co.uk/sport/football/teams/"
			   "newcastle-united/top-scorers")
		async with cs.get(url) as resp:
			if resp.status != 200:
				return "Retry"
			tree = html.fromstring(await resp.text(encoding="utf-8"))
		scorerrows = tree.xpath('.//div[@id="top-scorers"]/ol/li')
		scorers = ("\n* Top Scorers\n\n"
				   " Player|Goals|Assists"
				   "\n:--|:--:|:--:\n")
		for i in scorerrows:
			p = './/h2[contains(@class,"top-player-stats__name")]/text()'
			p = "".join(i.xpath(p))
			g = './/span[contains(@class,"goals-scored-number")]/text()'
			g = "".join(i.xpath(g))
			a = './/span[contains(@class,"stats__assists-number")]/text()'
			a = "".join(i.xpath(a)).strip(" Assists")
			scorers += f"{p}|{g}|{a}\n"
		return scorers
			
	def fixtures(self):	
		fixblock = []
		driver = webdriver.PhantomJS()
		driver.get("http://www.flashscore.com/team/newcastle-utd/"
			   "p6ahwuwJ/fixtures/")
		driver.implicitly_wait(2)
		url = "http://www.livesoccertv.com/teams/england/newcastle-united/"

		xp = ".//div[@id='fs-fixtures']/table"
		tables = driver.find_elements_by_xpath(xp)
		for table in tables:
			comp = './/span[@class="tournament_part"]'
			comp = table.find_element_by_xpath(comp).text
			comp = "PL" if comp == "Premier League" else comp
			comp = "*FRDLY*" if comp == "Club Friendly" else comp
			comp = "CHSP" if comp == "Championship" else comp
			matches = './/tbody/tr'
			matches = table.find_elements_by_xpath(matches)
			for match in matches:
				matchid = match.get_attribute("id").split("_")[2]
				lnk = f"http://www.flashscore.com/match/{matchid}/#h2h;overall"
				dt = match.find_element_by_class_name("time").text
				d,t = dt.split(" ")
				d = datetime.datetime.strptime(d,"%d.%m.").replace(year=datetime.datetime.now().year)
				d = d.replace(year=d.year+1) if d < datetime.datetime.now() else d
				d = datetime.datetime.strftime(d,"%a %d %b")
				ht = match.find_element_by_class_name("padr").text.strip()
				if " (" in ht:
					ht = ht.split(" (")[0]
				at = match.find_element_by_class_name("padl").text.strip()
				if " (" in at:
					at = at.split(" (")[0]
				ic = "[](#icon-home)" if "Newcastle" in ht else "[](#icon-away)"
				op = ht if "Newcastle" in at else at
				op = "Preston North End" if op == "Preston (Eng)" else op
				try:
					op = f"{self.bot.teams[op]['icon']}{self.bot.teams[op]['shortname']}"
				except KeyError:
					print(f"No db entry for: {op}")
				fixblock.append(f"[{d} {t}]({lnk})|{ic}|{op}|{comp}\n")
		
		fixmainhead = "\n* Upcoming fixtures"
		fixhead = "\n\n Date & Time|at|Opponent|Comp\n:--:|:--:|:--:|:--|--:\n"
		
		numblocks = (len(fixblock) // 20) + 1
		blocklen = math.ceil(len(fixblock)/numblocks)
		chunks = [fixblock[i:i+blocklen] for i in range(0, len(fixblock), blocklen)]
		chunks.reverse()
		for i in chunks:
			if len(i) < blocklen:
				i.append("|||||")
		chunks = ["".join(i) for i in chunks]
		chunks = fixmainhead + fixhead + fixhead.join(chunks)
		driver.close()
		return chunks
			
	def results(self):
		driver = webdriver.PhantomJS()
		driver.get("http://www.flashscore.com/team/newcastle-utd/"
			   "p6ahwuwJ/results/")
		driver.implicitly_wait(2)
			
		xp = ".//div[@id='fs-results']/table"
		scores = driver.find_elements_by_xpath(xp)
		resultlist = []
		lastres = ""
		lastop = ""
		for table in scores:
			comp = './/span[@class="tournament_part"]'
			# Fetch Competition Name & Shorten
			comp = table.find_element_by_xpath(comp).text
			comp = "PL" if comp == "Premier League" else comp
			comp = "FRDLY" if comp == "Club Friendly" else comp
			comp = "CHSP" if comp == "Championship" else comp
			
			# Fetch all match rows.
			matches = './/tbody/tr'
			matches = table.find_elements_by_xpath(matches)
			for match in matches:
				matchid = match.get_attribute("id").split("_")[2]
				
				# Hack together link.
				lnk = f"http://www.flashscore.com/match/{matchid}/#match-summary"
				split = match.find_element_by_class_name("score").text.split(":")
				if "\n" in split[1]:
					split,resplit = match.find_element_by_class_name("score").text.split("\n")
					split = split.split(":")
					sc = f"[{split[0]} - {split[1]} *{resplit.replace(':','-')}*]({lnk})"
				else:
					sc = f"[{split[0]} - {split[1]}]({lnk})"
				# Normalise Dates
				dt = match.find_element_by_class_name("time").text
				if ":" in dt:
					d = dt.split(" ")[0] + f"{datetime.datetime.now().year}"
				else:
					d = dt
				d = datetime.datetime.strptime(d,"%d.%m.%Y")
				d = datetime.datetime.strftime(d,"%a %d %b")
				
				# Get home and away teams.
				ht = match.find_element_by_class_name("padr").text.strip()
				at = match.find_element_by_class_name("padl").text.strip()
				if not lastop:
					# Fetch badge if required
					def get_badge(link,team):
						badgegetter = webdriver.PhantomJS()
						badgegetter.get(link)
						badgegetter.implicitly_wait(2)
						frame = badgegetter.find_element_by_class_name(f"tlogo-{team}")
						img = frame.find_element_by_xpath(".//img").get_attribute('src')
						self.bot.loop.create_task(self.fetch_badge(img))
						badgegetter.close()						
						
					lastop = at if "Newcastle" in ht else ht
					if at in self.bot.teams.keys():
						lasta = (f"[{self.bot.teams[at]['shortname']}]"
							    f"({self.bot.teams[at]['subreddit']})")
					else:
						get_badge(lnk,"away")
						lasta = f"[{at}](#temp/)"
						print(f"lasta: {lasta}")
					if ht in self.bot.teams.keys():
						lasth = (f"[{self.bot.teams[ht]['shortname']}]"
							    f"({self.bot.teams[ht]['subreddit']}/)")
					else:
						get_badge(lnk,"home")
						lasth = F"[{ht}](#temp)"
					lastres = f"> {lasth} {sc} {lasta}"
				if ht in self.bot.teams.keys():
					ht = (f"{self.bot.teams[ht]['icon']}"
						f"{self.bot.teams[ht]['shortname']}")
				if at in self.bot.teams.keys():
					at = (f"{self.bot.teams[at]['shortname']}"
						f"{self.bot.teams[at]['icon']}")
				ic = "[](#icon-home)" if "Newcastle" in ht else "[](#icon-away)"
				split = [i.strip() for i in split]
				if "Newcastle" in ht:
					if split[0] > split[1]:
						resultlist.append(f"[W](#icon-win)|{ht}|{sc}|{at}\n")
					elif split[0] == split[1]:
						resultlist.append(f"[D](#icon-draw)|{ht}|{sc}|{at}\n")
					else:
						resultlist.append(f"[L](#icon-loss)|{ht}|{sc}|{at}\n")
				else:
					if split[0] > split[1]:
						resultlist.append(f"[L](#icon-loss)|{ht}|{sc}|{at}\n")
					elif split[0] == split[1]:
						resultlist.append(f"[D](#icon-draw)|{ht}|{sc}|{at}\n")
					else:
						resultlist.append(f"[W](#icon-win)|{ht}|{sc}|{at}\n")
		driver.close()
		return resultlist,lastres,lastop
	
	async def fetch_badge(self,src):
		async with self.bot.session.get(src) as resp:
			if resp.status != 200:
				print("Error {resp.status} downloading image.")
			image = await resp.content.read()
		self.bot.loop.run_in_executor(None,self.upload_badge,image)
		
	def upload_badge(self,image):
		im = Image.open(BytesIO(image))
		im.save('badge.png')
		s = self.bot.reddit.subreddit(f'{self.subreddit}')
		s.stylesheet.upload('temp', 'badge.png')
		style = s.stylesheet().stylesheet
		s.stylesheet.update(style,reason="Update temprorary badge image")
		
def setup(bot):
	bot.add_cog(Sidebar(bot))