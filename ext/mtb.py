from prawcore.exceptions import RequestException
import praw

import json
import asyncio

import aiohttp
from aiohttp import ServerDisconnectedError
from lxml import html

from discord.ext import commands
import discord
import datetime

class MatchThreads:
	""" MatchThread functions """
	def __init__(self, bot):
		self.bot = bot
		self.stopmatchthread = False
		self.subreddit = "NUFC"
		self.ko = ""
		self.postat = ""
		self.scheduler = True
		self.schedtask = self.bot.loop.create_task(self.mt_scheduler())
	
	def __unload(self):
		self.schedtask.cancel()
		self.scheduler = False
	
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def schedoff(self,ctx):
		self.scheduler = False
		await ctx.send(f"Match thread scheduler disabled.")
		
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def schedon(self,ctx):
		self.scheduler = True
		await ctx.send(f"Match thread scheduler enabled.")
		
	@commands.command()
	async def checkmtb(self,ctx):
		await ctx.send(f"Scheduled for {self.postat}... hopefully.")
		
	async def mt_scheduler(self):
		""" This is the bit that determines when to run a match thread """
		while self.scheduler:
			# Scrape the next kickoff date & time from the fixtures list on r/NUFC
			async with self.bot.session.get("https://www.reddit.com/r/NUFC/") as resp: 
				if resp.status != 200:
					return "Error: {resp.status}","Error {resp.status}"
				tree = html.fromstring(await resp.text())
				fixture = tree.xpath('.//div[@class="titlebox"]//div[@class="md"]//li[5]//table/tbody/tr[1]/td[1]//text()')[-1]
				next = datetime.datetime.strptime(fixture,'%a %d %b %H:%M').replace(year=datetime.datetime.now().year)
				if not next:
					return "No matches found","No matches found"
					await asyncio.sleep(86400) # sleep for a day.
				now = datetime.datetime.now()
				self.ko = next - now
				self.postat = self.ko - datetime.timedelta(minutes=15)
				# Calculate when to post the next match thread
				sleepuntil = (self.postat.days * 86400) + self.postat.seconds
				print(f"Sleeping MT Bot for {sleepuntil} seconds")
				await asyncio.sleep(sleepuntil) # Sleep bot until then.
				await self.bot.loop.create_task(self.automt())
				await asyncio.sleep(180)
				
	async def automt(self):
		""" This is the bit that does the match thread. """
		modch = self.bot.get_channel(306552425144385536)
		async with self.bot.session.get("http://www.bbc.co.uk/sport/football/teams/newcastle-united/scores-fixtures") as resp:
			if resp.status != 200:
				await modch.send(":no_entry_sign: Match Thread Bot Aborted: HTTP Error: attempting to access game listings. {resp.url} returned status {resp.status}")
				return
			tree = html.fromstring(await resp.text())
			link = tree.xpath(".//a[contains(@class,'sp-c-fixture')]/@href")[-1]
			link = f"http://bbc.co.uk{link}"
		prematch = "Not found"
		async with self.bot.session.get("https://www.reddit.com/r/NUFC/") as resp:
			if resp.status != 200:
				await modch.send(content=f"HTTP Error accessing https://www.reddit.com/r/NUFC/ : {resp.status}",delete_after=5)
			else:
				tree = html.fromstring(await resp.text())
				for i in tree.xpath(".//p[@class='title']/a"):
					title = "".join(i.xpath('.//text()'))
					if "match" not in title.lower():
						continue
					if not title.lower().startswith("pre"):
						continue
					else:
						prematch = "".join(i.xpath('.//@href'))
						break
		
		
		async with self.bot.session.get(link) as resp:
			if resp.status != 200:
				await modch.send(f"HTTP Error attempting to retrieve {link}: {resp.status}. Match thread cancelled.")
				return
			tree = html.fromstring(await resp.text())
			if "/live/" in link:
				ko 	= "".join(tree.xpath('//div[@class="fixture_date-time-wrapper"]/time/text()')).title()
				ko = f'{ko}\n\n'
				try:
					kotime = tree.xpath('//span[@class="fixture__number fixture__number--time"]/text()')[0]
					ko = f"[🕒](#icon-clock) **Kickoff**: {kotime} on {ko}"
				except IndexError:
					ko = f"[🕒](#icon-clock) **Kickoff**: {self.ko}"
				print(f"A: {ko}")
				home = tree.xpath('//span[@class="fixture__team-name fixture__team-name--home"]//abbr/@title')[0]
				away = tree.xpath('//span[@class="fixture__team-name fixture__team-name--away"]//abbr/@title')[0]

			else:
				ko 	= "".join(tree.xpath('//div[@class="fixture_date-time-wrapper"]/time/text()')).title()
				ko = f'{ko}\n\n'
				try:
					kotime = tree.xpath('//span[@class="fixture__number fixture__number--time"]/text()')[0]
					ko = f"[🕒](#icon-clock) **Kickoff**: {kotime} on {ko}"
				except IndexError:
					ko = f"[🕒](#icon-clock) **Kickoff**: {ko}"
				teams = tree.xpath('//div[@class="fixture__wrapper"]//abbr/@title')
				home = teams[0]
				away = teams[1]
			try:
				tvlink = tv = f"http://www.livesoccertv.com/teams/england/{self.bot.teams[home]['bbcname']}/"
			except KeyError:
				tv = ""
			if tv != "":
				tv = ""
				async with self.bot.session.get(tvlink) as resp:
					if resp.status != 200:
						pass
					else:
						btree = html.fromstring(await resp.text())
						for i in btree.xpath(".//table[@class='schedules'][1]//tr"):
							if away in "".join(i.xpath('.//td[5]//text()')).strip():
								fnd = i.xpath('.//td[6]//a/@href')[-1]
								fnd = f"http://www.livesoccertv.com/{fnd}"
								tv = f"[📺](#icon-tv)[Television Coverage]({fnd})\n\n"
			hreddit = self.bot.teams[home]['subreddit']
			hicon = self.bot.teams[home]['icon']
			areddit = self.bot.teams[away]['subreddit']
			aicon = self.bot.teams[away]['icon']
			venue = f"[{self.bot.teams[home]['stadium']}]({self.bot.teams[home]['stadlink']})"
			ground = f"[🥅](#icon-net) **Venue**: {venue}\n\n"
			archive = "[Match Thread Archive](https://www.reddit.com/r/NUFC/wiki/archive)\n\n"
			try:
				ref  = tree.xpath('//dd[@class="description-list__description"]/text()[1]')[0]
				ref = f"[ℹ](#icon-whistle) **Referee**: {ref}\n\n"
			except IndexError:
				ref = ""
	
		# Update loop.
		async def update(prematch):
			print("Loop.")
			try:
				async with self.bot.session.get(link) as resp:
					if resp.status != 200:
						return "skip","skip","skip"
					tree = html.fromstring(await resp.text())
			except:
				return "skip","skiP","skip"
			homex = tree.xpath('.//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][1]/li')[:11]
			awayx = tree.xpath('.//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][1]/li')[11:]
			hgoals = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][1]//text()'))
			if hgoals != "":
				hgoals = f"{hicon}[⚽](#icon-ball) {hgoals}\n\n"
			agoals = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][2]//text()'))
			if agoals != "":
				agoals = f"{aicon}[⚽](#icon-ball) {agoals}\n\n"
			goals = f"{hgoals}{agoals}".replace(" minutes","")
			score = " - ".join(tree.xpath("//section[@class='fixture fixture--live-session-header']//span[@class='fixture__block']//text()")[0:2])
			if score == "":
				score = "v"
			if len(tree.xpath('//dd[@class="description-list__description"]/text()')) == 2:
				attenda  = tree.xpath('//dd[@class="description-list__description"]/text()')[1]
				attenda = f'**Attendance**: {attenda}\n\n'
			else:
				attenda = "**Attendance**: Not announced yet\n\n"
			async def parse_players(inputlist):
				out = []
				for i in inputlist:
					player = i.xpath('.//span[2]/abbr/span/text()')[0]
					infos  = "".join(i.xpath('.//span[2]/i/@class'))
					infos  = "".join(i.xpath('.//span[2]/i/@class'))
					infotime = "".join(i.xpath('.//span[2]/i/span/text()'))
					infotime = infotime.replace('Booked at ','')
					infotime = infotime.replace('mins','\'')
					infos = infos.replace('sp-c-booking-card sp-c-booking-card--rotate sp-c-booking-card--yellow gs-u-ml','💛')
					infos = infos.replace('booking-card booking-card--rotate booking-card--red gel-ml','🔴')
					subinfo = i.xpath('.//span[3]/span//text()')
					subbed = subinfo[1] if subinfo else ""
					subtime = subinfo[3].strip() if subinfo else ""
					if subbed:
						subbed = f"♻ {subbed} {subtime}"
					if infos:
						if subbed:
							thisplayer = f"**{player}** ({infos}{infotime}, {subbed})"
						else:
							thisplayer = f"**{player}** ({infos}{infotime})"
					else:
						if subbed:
							thisplayer = f"**{player}** ({subbed})"
						else:
							thisplayer = f"**{player}**"
					out.append(thisplayer)
				return out
				
			homexi = await parse_players(homex)
			homexi = ", ".join(homexi)
			awayxi = await parse_players(awayx)
			awayxi = ", ".join(awayxi)
			
			subs = tree.xpath('//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][2]/li/span[2]/abbr/span/text()')
			sublen = int(len(subs)/2)

			
			homesubs = [f"*{i}*" for i in subs[:sublen]]
			homesubs = ", ".join(homesubs)
			
			awaysubs = [f"*{i}*" for i in subs[sublen:]]
			awaysubs = ", ".join(awaysubs)
				
			statlookup = tree.xpath("//dl[@class='percentage-row']")
			stats = f"\n{home}|v|{away}\n:--|:--:|--:\n"
			for i in statlookup:
				stat = "".join(i.xpath('.//dt/text()'))
				dd1 = "".join(i.xpath('.//dd[1]/span[2]/text()'))
				dd2 = "".join(i.xpath('.//dd[2]/span[2]/text()'))
				statline = f"{dd1} | {stat} | {dd2}\n"
				stats += statline
			stats += "\n"
			dsc = f"[](#icon-discord)[Come join us on Discord](https://discord.gg/RtbyUQTV)\n\n\n\n"	
			headerline = f"# {hicon} [{home}]({hreddit}) {score} [{away}]({areddit}) {aicon}\n\n"
			if prematch == "Not found":
				pass
			else:
				prematch = f"[Pre-Match Thread]({prematch})\n\n"
			quickstats = f"{ko}{ground}{ref}{attenda}{prematch}{tv}{archive}"
			quickstats += "[📻 Radio Commentary](https://www.nufc.co.uk/liveAudio.html)\n\n---\n\n"
			lineups = f"{hicon} XI: {homexi}\n\nSubs: {homesubs}\n\n{aicon} XI: {awayxi}\n\nSubs: {awaysubs}\n\n"
			threadname = f"Match Thread: {home} v {away}"
			bbcheader = f"##MATCH UPDATES (COURTESY OF [](#icon-bbc)[BBC]({link}))\n\n"

			toptext = headerline+quickstats+lineups+goals+stats+dsc+bbcheader
			ticker = tree.xpath(".//div[@class='lx-stream__feed']/article")
			return toptext,threadname,ticker
		
		print("Trying to run update function.")
		# Generate Reddit post
		toptext,threadname,ticker = await update(prematch)

		post = await self.bot.loop.run_in_executor(None,self.makepost,threadname,toptext)

		await modch.send(content=post.url)
		tickids = []
		ticker = ""
		stop = False
		while self.stopmatchthread == False:
			toptext,threadname,newticks = await update(prematch)
			if toptext == "skip":
				pass
			else:
				newticks.reverse()
				for i in newticks:
					tickid = "".join(i.xpath("./@id"))
					if tickid in tickids:
						continue
					tickids.append(tickid)
					header = "".join(i.xpath('.//h3//text()')).strip()
					time = "".join(i.xpath('.//time//span[2]//text()')).strip()
					content = "".join(i.xpath('.//p//text()'))
					content = content.replace(home,f"{hicon} {home}")
					content = content.replace(away,f"{aicon} {away}").strip()
					if "Goal!" in header:
						if "Own Goal" in content:
							header = f"[⚽](#icon-OG) **OWN GOAL** "
						else:
							header = f"[⚽](#icon-ball) **GOAL** "
						time = f"**{time}**"
						content = f"**{content.replace('Goal! ','').strip()}**"
					if "Substitution" in header:
						header = f"[🔄](#icon-sub) **SUB**"
						team,subs = content.replace("Substitution, ","").split('.',1)
						on,off = subs.split('replaces')
						content = f"**{team} [🔺](#icon-up){on} [🔻](#icon-down){off}**"
						time = f"**{time}**"
					if content.lower().startswith("corner"):
						content = f"[](#icon-corner) {content}"
					if "Booking" in header:
						header = f"[YC](#icon-yellow)"
					if "Dismissal" in header:
						if "second yellow" in content.lower():
							header = f"[OFF!](#icon-2yellow) **RED**"
						else:
							header = f"[OFF!](#icon-red) **RED**"
						content = f"**{content}**"
					if "injury" in content.lower() or "injured" in content.lower():
						content = f"[🚑](#icon-injury) {content}"
					if "Full Time" in header:
						stop = True
						score = " - ".join(tree.xpath("//section[@class='fixture fixture--live-session-header']//span[@class='fixture__block']//text()")[0:2])
						ticker += f"# FULL TIME: {time} {hicon} [{home}]({hreddit}) {score} [{away}]({areddit}) {aicon}\n\n"
					else:
						ticker += f"{header} {time}: {content}\n\n"
				if newticks:
					newcontent = toptext+ticker
					upd = await self.bot.loop.run_in_executor(None,self.editpost,post,newcontent)
				if stop:
					# Final update when the match thread ends.
					newcontent = toptext+ticker
					upd = await self.bot.loop.run_in_executor(None,self.editpost,post,newcontent)
					await modch.send("Match thread ended, submitting post-match thread.")
					
					print(f"Headerline: {headerline}")
					print(f"matchurl: {post.url}")
					print(f"quickstats: {quickstats}")
					print(f"lineups: {lineups}")
					print(f"goals: {goals}")
					print(f"stats: {stats}")
					print(f"home: {home}")
					print(f"away: {away}")
					print(f"score: {score}")
					# Post post-match thread.
					matchurl = f"[Match Thread]({post.url})\n\n"

					posttext = headerline+quickstats+matchurl+lineups+goals+stats
					threadname = f"Post-Match Thread: {home} {score} {away}"
					post = await self.bot.loop.run_in_executor(None,self.makepost,threadname,posttext)
					await modch.send(content=post.url)
					print("Loop Concluded")
					self.stopmatchthread = True
					break
			await asyncio.sleep(120)
	
	def makepost(self,threadname,toptext):
		print(f"Entered MakePost: {threadname}")
		try:
			post = self.bot.reddit.subreddit(f"{self.subreddit}").submit(threadname,selftext=toptext)
		except RequestException:
			self.makepost(threadname,toptext)
		return post
		
	def editpost(self,post,newcontent):
		try:
			post.edit(newcontent)
		except:
			self.editpost(post,newcontent)
		return
		
def setup(bot):
	bot.add_cog(MatchThreads(bot))
