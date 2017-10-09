import asyncio
import discord
from discord.ext import commands

import aiohttp

class Tv:
	@commands.command()
	async def tv(self,ctx,*,team = None):
		""" Lookup next televised games for a team """
		with ctx.typing():
			if not team:
				if ctx.guild.id = 332159889587699712:
					team = "Newcastle United"
				else:
					
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



def setup(bot):
	bot.add_cog(Tv(bot))
