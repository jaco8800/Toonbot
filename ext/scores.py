import discord
from discord.ext import commands

import asyncio
import aiohttp
from lxml import html

from datetime import datetime
import json
import re

# because fuck it why not.
timedict = {"0":"ðŸ•›","030":"ðŸ•§","1":"ðŸ•", "130":"ðŸ•œ", "2":"ðŸ•‘", "230":"ðŸ•",
			"3":"ðŸ•’", "330":"ðŸ•ž", "4":"ðŸ•“", "430":"ðŸ•Ÿ", "5":"ðŸ•”", "530":"ðŸ• ",
			"6":"ðŸ••", "630":"ðŸ•¡", "7":"ðŸ•–", "730":"ðŸ•¢", "8":"ðŸ•—", "830":"ðŸ•£",
			"9":"ðŸ•˜", "930":"ðŸ•¤", "10":"ðŸ•™", "1030":"ðŸ•¥", "11":"ðŸ•š", "1130":"ðŸ•¦",
			"12":"ðŸ•›", "1230":"ðŸ•§"}

class Live:
	""" Get live scores for leagues worldwide """
	def __init__(self,bot):
		self.bot = bot
		self.scoreson = True
		self.bot.scorechecker = bot.loop.create_task(self.ls())
		self.matchcache = {}
    
	def __unload(self):
		self.scoreson = False
		self.bot.scorechecker.cancel()
	
	# Live Scores task.
	async def ls(self):
		await self.bot.wait_until_ready()
		msglist = []
		numservs = 0
		while self.scoreson:
			# Get date string
			tf = "Fixtures, results, and live scores for "
			tf += "**%a %d %b %Y** (Refreshed at **%H:%M:%S**)"
			today   = datetime.now().strftime(tf)
			
			# If we have nothing in msg list, clean channel, create messages.
			if msglist == []:
				numservs = 0
				for i in self.bot.config:
					if "scorechannel" in self.bot.config[i]:
						ch = self.bot.config[i]["scorechannel"]
						if ch is None:
							continue
						sc = self.bot.get_channel(int(ch))
						await sc.purge()
						numservs += 1
			# Shield from crashes.
			try:
				c = self.bot.session
				url = "http://www.bbc.co.uk/sport/football/scores-fixtures"
				async with c.get(url) as resp:
					if resp.status != 200:
						await asyncio.sleep(60)
						continue
					tree = html.fromstring(await resp.text())
			except Exception as e:
				print(f"Livescore channel: Ignored exception {e}")
				await asyncio.sleep(60)
				continue
			# Get each league parent element
			sections = tree.xpath('.//div[contains(@class,"gel-layout--center")]/div/div[3]/div/div') 
			outcomps = [f"{today}\n"]
			self.matchlist = {}
			for i in sections: # for each league on page
				try:
					comp = i.xpath('.//h3/text()')[0]
				except IndexError:
					comp = prevcomp
				else:
					prevcomp = comp
				group = "".join(i.xpath('.//h4/text()'))
				if group:
					comp = f"**{comp}** ({group})"
				else:
					comp = f"**{comp}**"
				self.matchlist[comp] = {}
				matches = i.xpath('.//li')
				for j in matches:
					url = "".join(j.xpath('.//a/@href'))
					xp = './/abbr[contains(@class,"team-name")]/@title'
					h = j.xpath(xp)[0]
					a = j.xpath(xp)[1]
					notes = j.xpath('.//aside/span//text()')
					time = j.xpath('.//span[contains(@class,"time")]/text()')
					scor = j.xpath('.//span[contains(@class,"number--home")]/text()|.//span[contains(@class,"number--away")]/text()')
					if notes:
						notes = f"`â„¹ {''.join(notes)}`"
					if len(time) == 1: # Fuck it let's be daft and convert the times to the nearest emoji
						time = time[0]
						left,mid,right = time.partition(":")
						left = int(left)
						right = int(right)
						if -1 < right < 15:
							right = ""
						elif 15 < right < 45:
							right = "30"
						else:
							right = ""
							left += 1
						if left > 12:
							left += -12
						newtime = f"{str(left)}{right}"
						precol = f"`{timedict[newtime]}{time}`"
						midcol = "v"
					if len(scor) == 2:
						precol = ""
						midcol = " - ".join(scor)
						if midcol == "P - P":
							precol = "`â›”PP`"
							miodcol = "v"
					if "ET" in notes:
						precol = "`âš½ET`"
						notes.replace("ET","")
					if notes == "`FT`":
						notes = ""
						precol = "`âœ…FT`"
					elif "FT" in notes:
						notes = notes.replace("FT"," ")
						precol = "`âœ…FT`"
					elif "AET" in notes:
						notes = notes.replace("AET"," ")
						precol = "`âš½AET`"
					if "HT" in notes:
						notes = notes.replace("HT","")
						precol = "`â¸HT`"
					if "min" in notes:
						regex = re.search(r"\d+\smins?",notes)
						notes = notes.replace(regex.group(),"")
						if "`âš½ET`" in precol:
							precol = f"`âš½ET {regex.group()}`"
						else:
							precol = f"`âš½{regex.group()}`"
					if "' +" in notes:
						regex = re.search(r"\d+\'\s\+\d+",notes)
						notes = notes.replace(regex.group(),"")
						precol= f"`âš½{regex.group()}`"
					if len(notes) < 6:
						notes = ""
					self.matchlist[comp][h] = {"timenow":precol,"midcol":midcol,"away":a,
											   "notes":notes,"league":comp,"url":url}
			count = 0

			# Send to ticker for update check.
			self.bot.loop.create_task(self.ticker())
			
			for i in self.matchlist:
				outcomp = f"{i}\n"
				for j in self.matchlist[i]:
					count += 1
					outcomp += f"{self.matchlist[i][j]['timenow']} {j} {self.matchlist[i][j]['midcol']} {self.matchlist[i][j]['away']} {self.matchlist[i][j]['notes']}\n"
				outcomp += "\n"
				outcomps.append(outcomp)
			outlist = []
			newchunk = ""
			for i in outcomps:
				if len(i) + len(newchunk) < 2000:
					newchunk += i
				else:
					if len(i) > 2000:
						outlist.append(newchunk)
						outlist.append(i[:1999])
						outlist.append(i[2000:])
						newchunk = ""
					else:
						outlist.append(newchunk)
						newchunk = i
			outlist.append(newchunk)
			# if previous messages exist to edit:
			if msglist != []:
				if (len(outlist) * numservs) != len(msglist):
					print(f"Old: {len(outlist)} New: {len(msglist)}")
					msglist = []
					for i in self.bot.config:
						chan = self.bot.config[i]["scorechannel"]
						ch = self.bot.get_channel(int(chan))
						if ch is not None:
							await ch.purge()
							for j in outlist:
								m = await ch.send(j)
								msglist.append(m)
				else:
					outlist = outlist * numservs
					editlist = list(zip(msglist,outlist))
					for i in editlist:
						# Edit if different.
						if i[0].content != i[1]:
							try:
								await i[0].edit(content=i[1])
							except discord.HTTPException as e:
								print(f"LS edit failed, {e}")
								pass
			else:
				for j in self.bot.config:
					if not "scorechannel" in self.bot.config[j]:
						continue
					id = self.bot.config[j]["scorechannel"]
					if id is None:
						continue
					else:
						print(id)
					sc = self.bot.get_channel(int(id))
					for i in outlist:
						if sc is not None:
							m = await sc.send(i)
							msglist.append(m)
			await asyncio.sleep(60)
	
	# Ticker Task
	async def ticker(self):
		# Filter Down to wanted leagues by checking if 
		# Wanted league is in the dict's keys.
		filtered = {}
		for (k,v) in self.matchlist.items():
			for i in ["Champions League","Premier League"]:
				if i in k: # Change to Premier League
					if "Women" not in k:
						filtered.update({k:v})
		
		# Flatten for iteration.
		flattened = {}
		for k,v in filtered.items():
			flattened.update(v)
		
		# First iteration only stores.
		if not self.matchcache:
			self.matchcache = flattened
			return
		
		# End early if no changes.
		if flattened == self.matchcache:
			return
		
		for i in flattened:
			try:
				if not flattened[i]["midcol"] == self.matchcache[i]["midcol"]:
					out = self.bot.get_channel(332163136239173632)
					e = discord.Embed()
					if "0 - 0" in flattened[i]['midcol']:
						e.title = "Kick Off"
						e.color = 0x00ffff
					else:
						e.title = "Goal"
						e.color = 0x00ff00
					async with self.bot.session.get(f"http://www.bbc.co.uk{flattened[i]['url']}") as resp:
						tree = html.fromstring(await resp.text()) # pls fix?
						hg = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][1]//text()'))
						hg = hg.replace("minutes","").replace(" )",")")
						ag = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][2]//text()'))
						ag = ag.replace("minutes","").replace(" )",")")
						if hg:
							hg = f"*{hg}*"
						if ag:
							ag = f"*{ag}*"
					e.description = f"{i} {flattened[i]['midcol']} {flattened[i]['away']}\n{hg}\n{ag}"
					e.set_footer(text=f"{flattened[i]['timenow']}, {flattened[i]['league']}".replace("*","").replace("`",""))
					if "FT" in flattened[i]['timenow']:
						e.title = "Full Time"
						e.color = 	0x00ffff 
					if "Russian" in flattened[i]['league']:
						self.matchcache = flattened
						return
					if "Welsh" in flattened[i]['league']:
						self.matchcache = flattened
						return
					self.matchcache = flattened
					print(f"Dispatched Ticker Event: {i} {flattened[i]['midcol']} {flattened[i]['away']}\n{hg}\n{ag}")
					await out.send(embed=e)
			except KeyError:
				self.matchcache = ""
				return
		
		# Save for next comparison.
		self.matchcache = flattened
	
	@commands.group(invoke_without_command=True)
	async def scores(self,ctx,*,league="Premier League"):
		""" Get the current scores from a league (default is Premier League)"""
		outcomps = []
		for i in self.matchlist:
			if league.lower() in i.lower():
				outcomp = f"{i}\n"
				for j in self.matchlist[i]:
					outcomp += f"{self.matchlist[i][j]['timenow']} {j} {self.matchlist[i][j]['midcol']} {self.matchlist[i][j]['away']} {self.matchlist[i][j]['notes']}\n"
				outcomp += "\n"
				outcomps.append(outcomp)
		outlist = []
		newchunk = ""
		for i in outcomps:
			if len(i) + len(newchunk) < 2000:
				newchunk += i
			else:
				if len(i) > 2000:
					outlist.append(newchunk)
					outlist.append(i[:1999])
					outlist.append(i[2000:])
					newchunk = ""
				else:
					outlist.append(newchunk)
					newchunk = i
		outlist.append(newchunk)
		if outlist:
			for i in outlist:
				await ctx.send(i)
		else:
			await ctx.send(f"Couldn't find scores for {league}")
	
	@scores.command(name="reload")
	@commands.has_permissions(manage_guild=True)
	async def _reload(self,ctx):
		self.bot.scorechecker.cancel()
		self.bot.scorechecker = self.bot.loop.create_task(self.ls())
		await ctx.send("Restarted score tracker.")
		
	
	@commands.group(invoke_without_command=True,aliases=["ls"])
	@commands.is_owner()
	async def livescores(self,ctx):
		""" Check the status of hte live score channel """
		e = discord.Embed(title="Live Score Channel Status")
		e.set_thumbnail(url=ctx.guild.icon_url)
		if self.scoreson:
			e.description = "```diff\n+ Enabled```"
			e.color=0x00ff00
		else:
			e.description = "```diff\n- Disabled```"
			e.color = 0xff0000

		if "scorechannel" in self.bot.config[str(ctx.guild.id)]:
			ch = self.bot.config[str(ctx.guild.id)]["scorechannel"]
			chan = self.bot.get_channel(ch)
			chanval = chan.mention
		else:
			chanval = "None Set"
			e.color = 0xff0000
		e.add_field(name=f"output Channel",value=chanval,inline=False)
		
		if self.bot.is_owner(ctx.author):
			x =  self.bot.scorechecker._state
			if x == "PENDING":
				v = "âœ… Task running."
			elif x == "CANCELLED":
				e.color = 0xff0000
				v = "âš  Task Cancelled."
			elif x == "FINISHED":
				e.color = 0xff0000
				self.bot.scorechecker.print_stack()
				v = "â‰ Task Finished"
				z = self.bot.scorechecker.exception()
			else:
				v = f"â” `{self.bot.scorechecker._state}`"
			e.add_field(name="Debug Info",value=v,inline=False)
			try:
				e.add_field(name="Exception",value=z,inline=False)
			except NameError:
				pass
		await ctx.send(embed=e)
		
	@livescores.command(name="on")
	@commands.has_permissions(manage_messages=True)
	async def scores_on(self,ctx):
		""" Turn the Live score channel back on """
		if not self.scoreson:
			self.scoreson = True
			await ctx.send("âš½ Live score channel has been enabled.")
			self.bot.scorechecker = bot.loop.create_task(self.ls())
		elif self.bot.scorechecker._state == ["FINISHED","CANCELLED"]:
			await ctx.send(f"âš½ Restarting {self.bot.scorechecker._state} task after exception {self.bot.scorechecker.exception()}.")
			self.bot.scorechecker = bot.loop.create_task(self.ls())
		else:
			await ctx.send("âš½ Live score channel already enabled.")
			
	@livescores.command(name="off")
	@commands.has_permissions(manage_messages=True)
	async def scores_off(self,ctx):	
		""" Turn off the live score channel """
		if self.scoreson:
			self.scoreson = False
			await ctx.send("âš½ Live score channel has been disabled.")
		else:
			await ctx.send("âš½ Live score channel already disabled.")
			
	@livescores.command(name="unset")
	@commands.has_permissions(manage_channels=True)
	async def _unset(self,ctx):
		""" Unsets the live score channel for this server """
		self.bot.config[str(ctx.guild.id)]["scorechannel"] = None
		with await self.bot.configlock:
			with open('config.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.config,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
		await ctx.send(f"Live score channel for {ctx.guild.name} set to None")
		
	@livescores.command(name="set")
	@commands.has_permissions(manage_channels=True)
	async def _set(self,ctx):
		""" Sets the live score channel for this server """
		self.bot.config[f"{ctx.guild.id}"].update({"scorechannel":ctx.channel.id})
		with await self.bot.configlock:
			with open('config.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.config,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
		await ctx.send(f"Live score channel for {ctx.guild.name} set to {ctx.channel.mention}")
	
	async def fetch_game(self,ctx,team):
		async with self.bot.session.get("http://www.bbc.co.uk/sport/football/scores-fixtures") as resp:
			if resp.status != 200:
				await m.edit(content=f"HTTP Error: {resp.status}")
				return None
			# We convert to lower case because fuck "USA".
			mystr = await resp.text()
			mystr = mystr.lower()
			tree = html.fromstring(mystr)
			
			# Search for the team in links.
			node = tree.xpath(f".//li/a[.//abbr[contains(@title,'{team.lower()}')]]")
			if not node:
				await ctx.send("Could not find specified team")
				return
			elif len(node) > 0:
				# If multiple nodes we just take the first cunt.
				node = node[0]
			return f"http://www.bbc.co.uk{node.xpath('./@href')[0]}"

	@commands.command(aliases=["substitutes","bench","lineup","lineups"])
	async def subs(self,ctx,*,team="Newcastle"):
		""" Show subs & lineups for a team (default is Newcastle)'s current game """
		team = team.title()
		m = await ctx.send(f"Searching for lineups for {team}")
		with ctx.typing():
			# Locate Game
			link = await self.fetch_game(ctx,team)
			async with self.bot.session.get(link) as resp:
				if resp.status != 200:
					await m.edit(content=f"HTTP Error accessing {link}: {resp.status}")
					print(resp.status)
					return None
				await m.edit(content=f"Fetching lineups from {link}")
				tree = html.fromstring(await resp.text())
				home = tree.xpath('//abbr/@title')[0]
				away = tree.xpath('//abbr/@title')[1]
				homex = tree.xpath('.//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][1]/li')[:11]
				awayx = tree.xpath('.//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][1]/li')[11:]
				
				async def parse_players(inputlist):
					out = []
					for i in inputlist:
						player = i.xpath('.//span[2]/abbr/span/text()')[0]
						infos  = "".join(i.xpath('.//span[2]/i/@class'))
						infos  = "".join(i.xpath('.//span[2]/i/@class'))
						infotime = "".join(i.xpath('.//span[2]/i/span/text()'))
						infotime = infotime.replace('Booked at ','')
						infotime = infotime.replace('mins','\'')
						infos = infos.replace('sp-c-booking-card sp-c-booking-card--rotate sp-c-booking-card--yellow gs-u-ml','\ðŸ’›')
						infos = infos.replace('booking-card booking-card--rotate booking-card--red gel-ml','\ðŸ”´')
						subinfo = i.xpath('.//span[3]/span//text()')
						subbed = subinfo[1] if subinfo else ""
						subtime = subinfo[3].strip() if subinfo else ""
						if subbed:
							subbed = f"\â™» {subbed} {subtime}"
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
				awayxi = await parse_players(awayx)
								
				# Subs
				subs = tree.xpath('//ul[@class="gs-o-list-ui gs-o-list-ui--top-no-border gel-pica"][2]/li/span[2]/abbr/span/text()')
				sublen = int(len(subs)/2)

				homesubs = [f"*{i}*" for i in subs[:sublen]]
				homesubs = ", ".join(homesubs)
				
				awaysubs = [f"*{i}*" for i in subs[sublen:]]
				awaysubs = ", ".join(awaysubs)
				
				# Generate Embed
				e = discord.Embed()
				e.title = f"Lineups for {home} v {away}"
				e.url = link
				e.color = 0xffdf43
				homesquad = ", ".join(homexi) + f"\n\nSubstitutes:\n{homesubs}"
				awaysquad = ", ".join(awayxi) + f"\n\nSubstitutes:\n{awaysubs}"
				e.add_field(name=f"{home}",value=homesquad)
				e.add_field(name=f"{away}",value=awaysquad)
				e.set_thumbnail(url="http://newsimg.bbc.co.uk/media/images/67165000/jpg/_67165916_67165915.jpg")
				await m.delete()
				await ctx.send(embed=e)
	
	@commands.command(aliases=["livestats"])
	async def stats(self,ctx,*,team="Newcastle"):
		team = team.title()
		""" Get the current stats for a team's game (default is Newcastle) """
		with ctx.typing():
			link = await self.fetch_game(ctx,team)
			m = await ctx.send(f"Found match: <{link}>, parsing...")
			async with self.bot.session.get(link) as resp:
				if resp.status != 200:
					await ctx.send(content=f"HTTP Error accessing this match's page: Code {resp.status}")
				tree = html.fromstring(await resp.text())
				teams = tree.xpath('//abbr/@title')
				try:
					home = self.bot.teams[teams[0]]['shortname']
				except KeyError:
					home = teams[0]
				try:
					away = self.bot.teams[teams[1]]['shortname']
				except KeyError:
					away = teams[1]
				homegoals = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][1]//text()')).replace(" minutes", "")
				awaygoals = "".join(tree.xpath('.//ul[contains(@class,"fixture__scorers")][2]//text()')).replace(" minutes", "")
				time = "".join(tree.xpath('//span[@class="fixture__status-wrapper"]/span/span/text()'))
				time = time.replace(' mins','th minute')
				comp = "".join(tree.xpath('//span[contains (@class,"fixture__title")]/text()'))
				
				statlookup = tree.xpath("//dl[contains(@class,'percentage-row')]")
				homestats = awaystats = stats = ""
				score = " - ".join(tree.xpath("//span[@class='fixture__block']//text()")[0:2])
				for i in statlookup:
					stats += f"{''.join(i.xpath('.//dt/text()'))}\n"
					homestats += f"{''.join(i.xpath('.//dd[1]/span[2]/text()'))}\n"
					awaystats += f"{''.join(i.xpath('.//dd[2]/span[2]/text()'))}\n"
				try:
					homestats += f"[{self.bot.teams[teams[0]]['subreddit'].replace('https://www.reddit.com','')}]({self.bot.teams[teams[0]]['subreddit']})"
					awaystats += f"[{self.bot.teams[teams[1]]['subreddit'].replace('https://www.reddit.com','')}]({self.bot.teams[teams[1]]['subreddit']})"
					stats += "Subreddit"
				except KeyError:
					pass
				e = discord.Embed(title=f"Match Stats Card",url=link,color=0xffdf43)
				e.description = ""
				try:
					ven = self.bot.teams[teams[0]]['stadium']
					vlink = self.bot.teams[teams[0]]['stadlink']
					e.description = f"**Venue:** [{ven}]({vlink})"
				except:
					pass
				if homestats:
					e.add_field(name=home,value=homestats,inline=True)
				else:
					print(homestats)
					e.description += f"\n {home}"
				if stats:
					e.add_field(name=score,value=stats,inline=True)
				else:
					print(stats)
					e.description += f" {score} "
				if awaystats:
					
					e.add_field(name=away,value=awaystats,inline=True)
				else:
					print(awaystats)
					e.description += f"{away}"
				if homegoals:
					e.add_field(name=f"{home} scorers",value=homegoals,inline=False)
				if awaygoals:
					e.add_field(name=f"{away} scorers",value=awaygoals,inline=False)
				e.set_footer(text=f"âš½ {comp}: {time}")
				await m.delete()
				await ctx.send(embed=e)
			
def setup(bot):
	bot.add_cog(Live(bot))
