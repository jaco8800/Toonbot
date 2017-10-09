import asyncio
import discord
from discord.ext import commands
import datetime

import json
import aiohttp
from lxml import html

class Tv:
	""" Search for live TV matches """
	def __init__(self, bot):
		self.bot = bot
	
	async def save_tv(self):
		print("Save_tv accessed")
		with await self.bot.configlock:
			with open('tv.json',"w",encoding='utf-8') as f:
				json.dump(self.bot.tv,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
	
	@commands.command()
	@commands.is_owner()
	async def poptv(self,ctx):
		""" Repopulate the livescoreTV team Database """
		with ctx.typing():
			await ctx.send("Rebuilding the TV Database...")
			async with self.bot.session.get("http://www.livesoccertv.com/competitions/") as comps:
				compstree = html.fromstring(await comps.text())
				complist = compstree.xpath('.//div[@class="tab_container"]//ul/li/a/@href')
				compname = compstree.xpath('.//div[@class="tab_container"]//ul/li/a//text()')
				comps = zip(complist,compname)
				# Phase 1 :  GET ALL COMPETITION TV LISTINGS
				for i in comps:
					tvdict.update({i[1]:f"http://www.livesoccertv.com{i[0]}"})
			# Phase 2 : Get all teams from competitions.
			for i in {key: value[:] for key, value in tvdict.items()}:
				async with self.bot.session.get(tvdict[i]) as resp:
					tree = html.fromstring(await resp.text())
					# If a table exists, we can grab the teams from it.
					teams = tree.xpath('.//table//table//tr//td/a')
					for i in teams:
						y = "".join(i.xpath('.//text()'))
						z = "".join(i.xpath('.//@href'))
						if y and z:
							print({y:f"http://www.livesoccertv.com{z}"})
							self.bot.tv.update({y:f"http://www.livesoccertv.com{z}"})
			await ctx.send("Done. Saving")
			await self.save_tv()
			await ctx.send("Saved.")
			
	@commands.command()
	async def tv(self,ctx,*,team = None):
		""" Lookup next televised games for a team """
		with ctx.typing():
			if team and not team == "live":
				matches = {i for i in self.bot.tv if team.lower() in i.lower()}
				if not matches:
					return await ctx.send(f"Could not find a matching team/league for {team}.")
				elif len(matches) > 1:
					print(matches)
					await ctx.send(f"{len(matches)} matches found for {team}, please be more specific")
					await ctx.send(f"```{matches}```")
					return

				e = discord.Embed()
				async with self.bot.session.get(self.bot.tv[team]) as resp:
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
				if tvlist:
					e.description = f"Upcoming Televised fixtures for {team}"
				else:
					return await ctx.send("Couldn't find any televised matches happening soon, check online at {self.bot.tv[team]}")
				e.url = f"{resp.url}"
				e.set_thumbnail(url='http://cdn.livesoccertv.com/images/logo55.png')
				e.set_footer(text="UK times.")
				for i,j in tvlist:
					e.add_field(name=i,value=j,inline=False)
				await ctx.send(embed=e)
			else:
				async with self.bot.session.get("http://www.livesoccertv.com/schedules/") as resp:
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
					match = "".join(i.xpath('.//td[3]//text()')).strip()
					ml = i.xpath('.//td[4]//a/text()')
					print
					if ml == []:
						continue
					else:
						ml = ", ".join(ml)
						print(f"{i} {ml}")
						print(isdone)
					date = "".join(i.xpath('.//td[@class="datecell"]//span/text()'))
					date = date.strip()
					time = i.xpath('.//td[@class="timecell"]//span/text()')
					time = time[-1].strip()
					# Correct TimeZone offset.
					if "FT" in time:
						continue
					if len(time) > 3:
						time = datetime.datetime.strptime(time,'%H:%M')+ datetime.timedelta(hours=5)
						time = datetime.datetime.strftime(time,'%H:%M')
					else:
						time = f"LIVE: {time}'"
					try:
						link = i.xpath('.//td[4]//a/@href')[-1]
					except IndexError:
						continue
					dt = f"`{date} {time}`"
					lnk= f"http://www.livesoccertv.com/{link}"
					tvlist.append((match,f'{dt} [{ml}]({lnk})'))
				e = discord.Embed()
				e.color = 0x034f76
				e.title = "LiveSoccerTV.com"
				if tvlist:
					e.description = f"Live Matches"
				else:
					return await ctx.send("Couldn't find any televised matches happening soon, check online at {self.bot.tv[team]}")
				e.url = f"{resp.url}"
				e.set_footer(text="UK times.")
				for i,j in tvlist:
					e.add_field(name=i,value=j,inline=True)
				await ctx.send(embed=e)


def setup(bot):
	bot.add_cog(Tv(bot))
