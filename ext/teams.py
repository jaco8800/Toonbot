from discord.ext import commands
from lxml import html
import discord,json

class Teams:
	def __init__(self,bot):
		self.bot = bot
		
	@commands.command()
	async def team(self,ctx,team="Newcastle"):
		""" Show information about a team """
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
			team = self.bot.teams[found[0]]
		e.color = int(team['color'],16)
		e.url = team['subreddit']
		e.set_thumbnail(url=team['badge'])
		e.description = f"**Stadium:** [{team['stadium']}]({team['stadlink']})\n"
		e.description += f"**Subreddit:** {team['subreddit']}\n"
		bbclink = f"http://www.bbc.co.uk/sport/football/teams/{team['bbcname']}"
		e.description += f"[Upcoming Fixtures]({bbclink}/fixtures)\n"
		e.description += f"[Previous Results]({bbclink}/results)\n"
		if ctx.guild.id == 238704683340922882:
			e.add_field(name="r/NUFC icon",value="f`{team['icon']}`")
		e.add_field(name="BBC Sport Page",value=bbclink)
		async with self.bot.session.get(f"{bbclink}/table") as resp:
			if resp.status != 200:
				await ctx.send(f"{resp.status} error accessing {bbclink}/table")
				await ctx.send(embed=e)
				return
			tree = html.fromstring(await resp.text())
			with open('test.html',"w") as fp:
				fp.write(await resp.text())
		league = tree.xpath('.//span[@class="secondary-nav__link-text"]/text()')[1]
		for i in tree.xpath('.//table[1][@class="table-stats"]/tbody/tr'):
			if found[0].lower() not in i.xpath('.//td[@class="team-name"]//text()')[0].lower():
				continue
			position = "".join(i.xpath('.//span[@class = "position-number"]/text()'))
			played   = "".join(i.xpath('.//td[@class = "played"]/text()'))
			goaldiff = "".join(i.xpath('.//td[@class = "goal-difference"]/text()'))
			points   = "".join(i.xpath('.//td[@class = "points"]/text()'))
			wins     = "".join(i.xpath('.//td[@class = "won"]/span/text()'))
			draws    = "".join(i.xpath('.//td[@class = "drawn"]/text()'))
			lost     = "".join(i.xpath('.//td[@class = "lost"]/text()'))
			gfor     = "".join(i.xpath('.//td[@class = "for"]/text()'))
			gaga     = "".join(i.xpath('.//td[@class = "against"]/text()'))
			form 	 = i.xpath('.//td[@class = "last-10-games"]/ol/li/span/text()')
			form = "".join([i[0] for i in form])
			form = f"**Form:** {form}\n"
			place = f"**#{position} in {league} with {points} points**\n"
			gd = f"**Goal Difference:** {goaldiff} ({gfor}/{gaga})\n"
			pld = f"**Played:** {played}\n**Record:** {wins}-{draws}-{lost}\n"
			fvalue = f"{place}{gd}{pld}{form}"
			e.add_field(name="League Statistics",value=fvalue)
		await ctx.send(embed=e)
		
def setup(bot):
	bot.add_cog(Teams(bot))