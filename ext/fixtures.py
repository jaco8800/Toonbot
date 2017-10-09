import asyncio
import discord
from discord.ext import commands

import aiohttp
import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from colorthief import ColorThief
import datetime
from copy import deepcopy

from io import BytesIO

class Fixtures:
	def __init__(self, bot):
		self.bot = bot
	
	# Rebuild DB.
	async def save_comps(self):
		print("Save_comps accessed")
		with await self.bot.configlock:
			with open('compsnew.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.comps,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))

	@commands.command()
	@commands.is_owner()
	async def populate(self,ctx):
		await ctx.send("Attempting to build list")
		await self.bot.loop.run_in_executor(None,self.popteams)
		await ctx.send(ctx.author.mention)
				
	def poplist(self):
		""" Populates a list of competitions """
		driver = webdriver.PhantomJS()
		driver.get("http://www.flashscore.com")
		driver.implicitly_wait(2)
		# Wait for it to load, then parse.
		WebDriverWait(driver, 2)
		xp = './/ul[@class="menu country-list"]/li[contains(@id,"lmenu")]'
		ctrys = driver.find_elements_by_xpath(xp)
		self.comps = {}
		for i in ctrys:
			# Get name and append as key.
			ctry = i.find_element_by_xpath('./a').text
			i.find_element_by_xpath('./a').click()
			self.comps[ctry] = {}
			comps = i.find_elements_by_xpath('.//ul/li/a')
			for j in comps:
				# png = j.screenshot_as_png
				comp = j.text
				link = j.get_property("href")
				# Add subkey.
				self.comps[ctry][comp] = {"link":link}
				self.comps[ctry]["teams"] = {}
				print(f"Added {ctry}: {comp} - {link}")
		self.bot.loop.create_task(self.save_comps())
		driver.quit()
		
	def popteams(self):
		""" Populates teams """
		driver = webdriver.PhantomJS()
		driver.implicitly_wait(2)
		for country in self.comps.keys():
			self.comps[country]["teams"] = {}
			for league in self.comps[country].keys():
				print(league)
				try:
					driver.get(self.comps[country][league]["link"]+"teams")
				except KeyError:
					continue
				tree = html.fromstring(driver.page_source)
				xp = './/div[@id="tournament-page-participants"]//tbody/tr'
				teams = tree.xpath(xp)
				for i in teams:
					name =	"".join(i.xpath('.//td/a/text()'))
					if name in self.comps[country]["teams"]:
						continue
					link = "".join(i.xpath('.//td/a/@href)'))
					self.comps[country]["teams"][name] = link
					print(f"Added {country}: {league} - {name}: {link}")
		self.bot.loop.create_task(self.save_comps())
		driver.quit()
	
	@commands.command()
	async def tv(self,ctx,*,team = None):
		""" Lookup next televised games for a team """
		with ctx.typing():
			if not team:
				if ctx.guild.id = 332159889587699712:
					team = "Newcastle United"
				else:
					return await ctx.send("Please provide a team name for me to search for.")
			found = []
			for i,j in self.bot.teams.items():
				if team.lower() in i.lower():
					found.append(i)
			if len(found) == 0:
				await ctx.send(f"No teams found matching {team}")
				return
			elif len(found) > 1:
				found = [i for i,j in found]
				await ctx.send(f"Multiple teams found, please be more specific ({','.join(found)})")
				return
			else:
				e = discord.Embed()
				e.set_author(name=found[0])
				print(found[0])
				team = found[0]
			td = self.bot.teams[team]
			url = f'http://www.livesoccertv.com/teams/england/{td["bbcname"]}'
			async with self.bot.session.get(url) as resp:
				if resp.status != 200:
					await ctx.send(f"🚫 {resp.url} returned {resp.status}")
					return
				tree = html.fromstring(await resp.text())
			tvlist = []
			for i in tree.xpath(".//table[@class='schedules'][1]//tr"):
				# Discard finished games.
				isdone = "".join(i.xpath('.//td[@class="livecell"]//text()'))
				if isdone in ["FT","Repeat"]:
					continue
				if "".join(i.xpath('.//td[@class="compcell"]/a/text()')) in "PL2":
					continue
				match = "".join(i.xpath('.//td[5]//text()')).strip()
				if "vs" not in match:
					continue
				ml = i.xpath('.//td[6]//a/text()')
				ml = [x for x in ml if x != "nufcTV" and x.strip() != ""]
				if ml == []:
					continue
				else:
					ml = ", ".join(ml)
				date = "".join(i.xpath('.//td[@class="datecell"]//span/text()'))
				date = date.strip()
				time = "".join(i.xpath('.//td[@class="timecell"]//span/text()'))
				time = time.strip()
				# Correct TimeZone offset.
				time = datetime.datetime.strptime(time,'%H:%M')+ datetime.timedelta(hours=5)
				time = datetime.datetime.strftime(time,'%H:%M')
				try:
					link = i.xpath('.//td[6]//a/@href')[-1]
				except IndexError:
					continue
				dt = f"`{date} {time}`"
				lnk= f"http://www.livesoccertv.com/{link}"
				tvlist.append((match,f'{dt} [{ml}]({lnk})'))
			e = discord.Embed()
			e.color = 0x034f76
			e.title = "LiveSoccerTV.com"
			if len(tvlist) > 0:
				e.description = f"Upcoming Televised fixtures for {team}"
			else:
				e.description = f"None on this page, check the website."
			e.url = f"{resp.url}"
			e.set_thumbnail(url='http://cdn.livesoccertv.com/images/logo55.png')
			e.set_footer(text="UK times.")
			for i,j in tvlist:
				e.add_field(name=i,value=j,inline=False)
			await ctx.send(embed=e)
	
	@commands.command(aliases=["sc","topscorers"])
	async def scorers(self,ctx,*,qry = "Newcastle Utd"):
		""" Fetch top scorers for a team or league """
		m = await ctx.send(f"Top scorers: Searching for {qry}, please wait...")
		with ctx.typing():
			l = self.bot.loop
			url = await l.run_in_executor(None,self.get_team,qry)
			if not url:
				url = await l.run_in_executor(None,self.get_league,qry)
				if not url:
					await ctx.send("No Results.")
					return
			if "team" in url:
				url += "/squad/"
			else:
				url += "standings/"
			au = ctx.author.display_name
			pages = await l.run_in_executor(None,self.parse_scorers,url,au)
			await self.paginate(ctx,pages)
			await m.delete()
		
	@commands.command(aliases=["fx"],invoke_without_command=True)
	async def fixtures(self,ctx,*,qry="Newcastle Utd"):
		""" Grab a team's results history from flashscore.
			Navigate using discord reactions.
		"""
		m = await ctx.send(f"Fixtures: Searching for {qry}, please wait...")
		with ctx.typing():
			l = self.bot.loop
			url = await l.run_in_executor(None,self.get_team,qry)
			if not url:
				url = await l.run_in_executor(None,self.get_league,qry)
				if not url:
					await ctx.send("No Results.")
					return
			# Normalise.
			url += "/fixtures/"
			url = url.replace('//','/').replace(":",":/")
			au = ctx.author.display_name
			pages = await l.run_in_executor(None,self.parse_fixtures,url,au)
		await m.delete()
		await self.paginate(ctx,pages)
	
	@commands.group(aliases=["rx"],invoke_without_command=True)
	async def results(self,ctx,*,qry="Newcastle Utd"):
		""" Displays results for the last year for a team.
			Navigate with reactions.
		"""
		m = await ctx.send(f"Results: Searching for {qry}, please wait...")
		with ctx.typing():
			l = self.bot.loop
			url = await l.run_in_executor(None,self.get_team,qry)
			if not url:
				url = await l.run_in_executor(None,self.get_league,qry)
				if not url:
					await ctx.send("No Results.")
					return
			# Normalise.
			url += "/results/"
			url = url.replace('//','/').replace(":",":/")
			au = ctx.author.display_name
			pages = await l.run_in_executor(None,self.parse_results,url,au)
		await m.delete()
		await self.paginate(ctx,pages)
	
	# Synchronous
	def get_team(self,qry):
		m = {}
		for i in self.bot.comps:
			for j in self.bot.comps[i]["teams"]:
				x = self.bot.comps[i]["teams"]
				m.update({h:self.bot.comps[i]["teams"][h] for h in x if qry.lower() in h.lower()})
		if m:
			return m[min(m, key=len)]
		return
	
	def get_league(self,qry):
			spt = qry.split()
			x = spt[0].lower()
			ctrys = [i for i in self.bot.comps.keys() if x in i.lower()]
			if ctrys:
				match = spt[0]
			if not ctrys:
				x = " ".join(spt[1:]).lower()
				ctrys = [i for i in self.bot.comps.keys() if x in i.lower()]
				match = "".join(spt[1:])
			if not ctrys:
				ctrys = [i for i in self.bot.comps.keys()]
				match = ""
			lgs = []
			for i in ctrys:
				tq = qry.replace(match,"")
				tq = tq.replace(i,"").strip().lower()
				lgs += [f"{i}: {c}" for c in self.bot.comps[i] if tq in c.lower()]
			if not lgs:
				return
			if len(lgs) == 1:
				lgs = lgs[0]
				lg,cp = lgs.split(":")
			else:
				e = [s for s in lgs if s.startswith('England')]
				if e:
					lgs = min(e,key=len)
					lg,cp = lgs.split(":")
				else:
					lgs = min(lgs,key=len)
					lg,cp = lgs.split(":")
			return self.bot.comps[lg][cp.strip()]["link"]
	
	def get_html(self,url):
		driver = webdriver.PhantomJS()
		driver.implicitly_wait(5)
		driver.get(url)
		WebDriverWait(driver, 3)
		th = driver.find_element_by_xpath(".//div[contains(@class,'logo')]")
		th = th.value_of_css_property('background-image')
		th = th.strip("url(").strip(")")
		
		e = discord.Embed()
		e.set_thumbnail(url=th)
		e.color = self.get_color(th)
		e.url = url
		
		# Check if "load more" exists, click it.
		while True:
			try:
				driver.find_element_by_link_text("Show more matches").click()
				WebDriverWait(driver, 2)
			except:
				break
		
		# We switch to regular xpath for speed.
		t = html.fromstring(driver.page_source)
		driver.quit()
		return t,e
	
	def get_color(self,url):
		r = requests.get(url)
		r = BytesIO(r.content)
		r.seek(0)
		ct = ColorThief(r)
		rgb = ct.get_color(quality=1)
		# Convert to base 16 int.
		return int('%02x%02x%02x' % rgb,16)
	
	def parse_scorers(self,url,au):
		t,e = self.get_html(url)
		now = datetime.datetime.now()
		
		if "team" in url:
			# For individual Team
			scorerdict = {}
			team = "".join(t.xpath('.//div[@class="team-name"]/text()'))
			e.title = f"≡ Top Scorers for {team}"
			players = t.xpath('.//table[contains(@class,"squad-table")]/tbody/tr')
			for i in players:
				p = "".join(i.xpath('.//td[contains(@class,"player-name")]/a/text()'))
				if not p:
					continue	
				g = "".join(i.xpath('.//td[5]/text()'))
				if g == "0":
					continue
				if not g:
					continue
				l = "".join(i.xpath('.//td[contains(@class,"player-name")]/a/@href'))
				if g in scorerdict.keys():
					scorerdict[g].append(f"[{' '.join(p.split(' ')[::-1])}](http://www.flashscore.com{l})")
				else:
					scorerdict.update({g:[f"[{' '.join(p.split(' ')[::-1])}](http://www.flashscore.com{l})"]})
			sclist = [[f"{k} : {i}" for i in v] for k,v in scorerdict.items()]
			sclist = [i for sublist in sclist for i in sublist]
			tmlist = [f"[{team}]({url})" for i in sclist]
		else:
			# For cross-league.
			sclist = []
			tmlist = []
			comp = "".join(t.xpath('.//div[@class="tournament-name"]/text()'))
			e.title = f"≡ Top Scorers for {comp}"
			# Re-scrape!
			driver = webdriver.PhantomJS()
			driver.implicitly_wait(5)
			driver.get(url)
			WebDriverWait(driver, 2)
			x = driver.find_element_by_link_text("Top Scorers")
			x.click()
			WebDriverWait(driver, 5)
			players = driver.find_element_by_id("table-type-10")
			t = players.get_attribute('innerHTML')
			tree = html.fromstring(t)
			players = tree.xpath('.//tbody/tr')
			for i in players:
				p = "".join(i.xpath('.//td[contains(@class,"player_name")]//a/text()'))
				p = ' '.join(p.split(' ')[::-1])
				if not p:
					continue
				pl = "".join(i.xpath('.//td[contains(@class,"player_name")]/span[contains(@class,"team_name_span")]/a/@onclick'))
				pl = pl.split("'")[1]
				pl = f"http://www.flashscore.com{pl}"
				g = "".join(i.xpath('.//td[contains(@class,"goals_for")]/text()'))
				if g == "0":
					continue
				tm = "".join(i.xpath('.//td[contains(@class,"team_name")]/span/a/text()'))
				tml = "".join(i.xpath('.//td[contains(@class,"team_name")]/span/a/@onclick'))
				tml = tml.split("\'")[1]
				tml = f"http://www.flashscore.com{tml}"
				sclist.append(f"{g} [{p}]({pl})")
				tmlist.append(f"[{tm}]({tml})")
			driver.quit()
		z = list(zip(sclist,tmlist))
		# Make Embeds.
		embeds = []
		p = [z[i:i+10] for i in range(0, len(z), 10)]
		pages = len(p)
		count = 1
		for i in p:
			j = "\n".join([j for j,k in i])
			k = "\n".join([k for j,k in i])
			e.add_field(name="Goals / Player",value=j,inline=True)
			e.add_field(name="Team",value=k,inline=True)
			iu = "http://pix.iemoji.com/twit33/0056.png"
			e.set_footer(text=f"Page {count} of {pages} ({au})",icon_url=iu)
			te = deepcopy(e)
			embeds.append(te)
			e.clear_fields()
			count += 1

		return embeds
			
	def parse_fixtures(self,url,au):
		t,e = self.get_html(url)
		fxtb = t.xpath('.//div[@id="fs-fixtures"]//tbody/tr')
		now = datetime.datetime.now()
				
		dates = []
		games = []
		if "team" in url:
			team = "".join(t.xpath('.//div[@class="team-name"]/text()'))
			e.title = f"≡ Fixtures for {team}"
			for i in fxtb:
				d = "".join(i.xpath('.//td[contains(@class,"time")]//text()'))
				# Skip header rows.
				if not d:
					continue
				d = datetime.datetime.strptime(d,"%d.%m. %H:%M")
				d = d.replace(year=now.year)
				d = datetime.datetime.strftime(d,"%a %d %b: %H:%M")
				dates.append(f"`{d}`")
				tv = i.xpath(".//span[contains(@class,'tv')]")
				if tv:
					tv = i.xpath("./@id")[0].split("_")[-1]
					tv = f" [`📺`](http://www.flashscore.com/match/{tv}/)"
				else:
					tv = ""
				op = "".join(i.xpath('.//span[@class="padr"]/text()'))
				wh = "A"
				if op == team:
					op = "".join(i.xpath('.//span[@class="padl"]/text()'))
					wh = "H"
				games.append(f"`{wh}: {op}`{tv}")
		else:
			comp = "".join(t.xpath('.//div[@class="tournament-name"]/text()'))
			e.title = f"≡ Fixtures for {comp}"
			for i in fxtb:
				d = "".join(i.xpath('.//td[contains(@class,"time")]//text()'))
				# Skip header rows.
				if not d:
					continue
				d = datetime.datetime.strptime(d,"%d.%m. %H:%M")
				d = d.replace(year=now.year)
				d = datetime.datetime.strftime(d,"%a %d %b: %H:%M")
				tv = i.xpath(".//span[contains(@class,'tv')]")
				if tv:
					tv = i.xpath("./@id")[0].split("_")[-1]
					tv = f"[`📺`](http://www.flashscore.com/match/{tv}/)"
				else:
					tv = ""
				dates.append(f"`{d}`{tv}")
				h = "".join(i.xpath('.//span[@class="padr"]/text()'))
				a = "".join(i.xpath('.//span[@class="padl"]/text()'))
				games.append(f"`{h} v {a}`")

		if not games:
			return # Rip
		z = list(zip(dates,games))
		embeds = self.build_embeds(au,e,z,"Fixture")
		return embeds
	
	def parse_results(self,url,au):
		t,e = self.get_html(url)
		rstb = t.xpath('.//div[@id="fs-results"]//tbody/tr')
		now = datetime.datetime.now()
		dates = []
		games = []
		if "/team/" in url:
			team = "".join(t.xpath('.//div[@class="team-name"]/text()'))
			e.title = f"≡ Results for {team}"
			for i in rstb:
				d = "".join(i.xpath('.//td[contains(@class,"time")]//text()'))
				# Skip header rows.
				if not d:
					continue
					
				# Get match date
				try:
					d = datetime.datetime.strptime(d,"%d.%m. %H:%M")
					d = d.replace(year=now.year)
					d = datetime.datetime.strftime(d,"%a %d %b: %H:%M")
				except ValueError:
					# Fix older than a year games.
					d = datetime.datetime.strptime(d,"%d.%m.%Y")
					d = datetime.datetime.strftime(d,"%d/%m/%Y")
				
				# Score
				sc = i.xpath('.//td[contains(@class,"score")]/text()')
				sc = "".join(sc).replace('\xa0','').split(':')
				h = sc[0]
				a = sc[1]
				sc = "-".join(sc)
				# Assume we're playing at home.
				op = "".join(i.xpath('.//span[@class="padr"]/text()')) # PADR IS HOME.
				wh = "A" if team in op else "H"
				w = "L" if h > a else "D" if h == a else "W"
				
				if team in op:
					# if we're actually the away team.
					op = "".join(i.xpath('.//span[@class="padl"]/text()'))
					w = "W" if h > a else "D" if h == a else "L"
				dates.append(f"`{wh}: {d}`")
				games.append(f"`{w}: {sc} v {op}`")
		else:
			comp = "".join(t.xpath('.//div[@class="tournament-name"]/text()'))
			e.title = f"≡ Fixtures for {comp}"
			for i in rstb:
				d = "".join(i.xpath('.//td[contains(@class,"time")]//text()'))
				# Skip header rows.
				if not d:
					continue
				d = datetime.strptime(d,"%d.%m. %H:%M")
				d = d.replace(year=now.year)
				d = datetime.strftime(d,"%a %d %b: %H:%M")
				dates.append(f"`{d}`")
				sc = i.xpath('.//td[contains(@class,"score")]/text()')
				sc = "".join(sc).replace('\xa0','').split(':')
				hos = sc[0]
				aws = sc[1]
				
				
				h = "".join(i.xpath('.//span[@class="padr"]/text()'))
				a = "".join(i.xpath('.//span[@class="padl"]/text()'))
				sc = f"`{hos}-{aws}`"
				games.append(f"{h} {sc} {a}")
		if not games:
			return # Rip
		z = list(zip(dates,games))
		embeds = self.build_embeds(au,e,z,"Result")
		return embeds
	
	def build_embeds(self,au,e,z,type):
		embeds = []
		p = [z[i:i+10] for i in range(0, len(z), 10)]
		pages = len(p)
		count = 1
		for i in p:
			j = "\n".join([j for j,k in i])
			k = "\n".join([k for j,k in i])
			e.add_field(name="Date",value=j,inline=True)
			e.add_field(name=type,value=k,inline=True)
			iu = "http://pix.iemoji.com/twit33/0056.png"
			e.set_footer(text=f"Page {count} of {pages} ({au})",icon_url=iu)
			te = deepcopy(e)
			embeds.append(te)
			e.clear_fields()
			count += 1
		return embeds
	
	async def paginate(self,ctx,pages):
		page = 0
		if not pages:
			await ctx.send("Couldn't find anything")
			return
		numpages = len(pages)
		m = await ctx.send(embed=pages[0])
		if numpages == 1:
			return
		await m.add_reaction("⏮")
		if numpages > 2:
			await m.add_reaction("⬅")
			await m.add_reaction("➡")
		await m.add_reaction("⏭")
		await m.add_reaction("⏏")
		def check(r,u):
			if r.message.id == m.id and u == ctx.author:
				e = str(r.emoji)
				return e.startswith(('⏮','⬅','➡','⏭','⏏'))
		while True:
			try:
				wf = "reaction_add"
				r = await self.bot.wait_for(wf,check=check,timeout=120)
			except asyncio.TimeoutError:
				await m.clear_reactions()
				break
			r = r[0]
			if r.emoji == "⏮": #first
				page = 0
				await m.remove_reaction("⏮",ctx.author)
			if r.emoji == "⬅": #prev
				await m.remove_reaction("⬅",ctx.author)
				if page > 0:
					page = page - 1
			if r.emoji == "➡": #next	
				await m.remove_reaction("➡",ctx.author)
				if page < numpages - 1:
					page = page + 1
			if r.emoji == "⏭": #last
				page = numpages - 1
				await m.remove_reaction("⏭",ctx.author)
			if r.emoji == "⏏": #eject
				return await m.delete()
			await m.edit(embed=pages[page])
			
def setup(bot):
	bot.add_cog(Fixtures(bot))
