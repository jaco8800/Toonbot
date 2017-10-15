import discord,aiohttp,asyncio,datetime
from discord.ext import commands
from unidecode import unidecode
from lxml import html
import random

class NUFC:
	""" NUFC.com player profiles """
	def __init__(self, bot):
		self.bot = bot
		print("FUCKING RELOAD.")
		self.bot.streams = []
	
	def nufccheck(ctx):
		if ctx.guild:
			return ctx.guild.id in [238704683340922882,332159889587699712]
	
	async def get_players(self):
		names,pics = await self.gp("https://www.nufc.co.uk/teams/first-team")
		for i in ["under-23s","on-loan","coaching-staff","under-18s"]:
			add1,add2 = await self.gp(f"https://www.nufc.co.uk/teams/{i}")
			names += add1
			pics += add2
		links = names
		names = [x.split('/')[-1].replace('-',' ') for x in names] #strip preleading text
		return dict((z[0],list(z[1:])) for z in zip(names,pics,links))
		
	async def gp(self,source): # get players for page
		async with self.bot.session.get(source,allow_redirects=False) as resp:
			if resp.status != 200:
				return
			tree = html.fromstring(await resp.text())
		players = tree.xpath('.//div[@class="player-card"]/a/@href')
		pictures = tree.xpath('.//div[@class="player-card"]/a/div/div/figure/img/@src')
		return (players,pictures)
	
	@commands.group(invoke_without_command=True,aliases=["stream"])
	async def streams(self,ctx):
		""" List all streams for the match added by users. """
		if not self.bot.streams:
			await ctx.send("Nobody has added any streams yet.")
		output = "**Streams: **\n"
		for c,v in enumerate(self.bot.streams,1):
			output += f"{c}: {v}\n"
		await ctx.send(output)
		
	@streams.command(name="add")
	async def stream_add(self,ctx,*,stream):
		if "http" in stream:
			stream = f"<{stream}>"
		self.bot.streams.append(f"{stream} (added by {ctx.author.name})")
		await ctx.send(f"Added {stream} to stream list.")
		
	@streams.command(name="del")
	async def stream_del(self,ctx,*,num:int):
		num = num+1
		removed = self.bot.streams.pop(num)
		await ctx.send(f"{removed} removed from streams list.")
		
	@streams.command(name="clear")
	@commands.has_permissions(manage_guild=True)
	async def stream_clear(self,ctx):
		self.bot.streams = []
		await ctx.send("Streams cleared.")
	
	@commands.command()
	async def gherkin(self,ctx):
		""" DON'T LET ME GOOOOOO AGAIN"""
		await ctx.send("https://www.youtube.com/watch?v=L4f9Y-KSKJ8")
	
	@commands.command()
	@commands.check(nufccheck)
	async def mbemba(self,ctx):
		""" Mbemba When... """
		facts = [
			"Director of Football Dennis Wise vetoing a cut-price deal for Bastian Schweinsteiger in favour of loaning a player he'd seen on YouTube",
			"German international Dietmar Hamann, in his first season at the club, receiving the secret Santa gift of a copy of Mein Kampf",
			"Alessandro Pistone receiving the secret Santa gift of a sheep's heart because he \"didn't have one of his own\"",
			"Alan Shearer punching, and subsequently knocking out, Keith Gillespie on a club trip to Dublin because Gillespie dropped some cutlery",
			"Alan Pardew blaming a 2-0 defeat away at Chelsea in August 2012 on the Notting Hill Carnival",
			"Alan Pardew blaming a lack of signings in the summer of 2012 on the idea that too many potential players were busy watching the Olympics",
			"Ruud Gullit dropping both Alan Shearer and Duncan Ferguson for the Tyne-Wear Derby in favour of Sunderland supporting Paul Robinson",
			"Joe Kinnear ringing up TalkSport to declare himself Newcastle's new Director of Football and calling our best player \"Yohan Kebab\"",
			"Kevin Keegan convincing Rob Lee to join Newcastle by telling him it was closer to London than Middlesbrough is",
			"Shola Ameobi being asked what his teammates call him and replying \"Shola\" then being asked what Sir Bobby calls him and saying \"Carl Cort\"",
			"Kieron Dyer and Lee Bowyer both being sent off against Aston Villa for fighting each other",
			"Kenny Dalglish selling Les Ferdinand and David Ginola, and replacing them with 35 year old Ian Rush and 33 year old John Barnes",
			"John Barnes being our top scorer with six goals.",
			"Allowing Lomana LuaLua to play against us while he was on loan at Portsmouth. Then him scoring. Then him doing somersaults in celebration",
			"that fan punching a police horse",
			"Nobby Solano withholding his number, ringing up Sir Bobby Robson, and playing his trumpet down the phone to him",
			"Spending nearly £6m on Spanish defender Marcelino and him only making 17 appearances over 4 years because of a broken finger",
			"David Ginola being told he couldn't smoke on the team bus because it was unhealthy, just as the bus pulled up to buy the squad fish & chips",
			"Daryl Janmaat breaking two fingers by punching a wall because he was angry about being substituted after injuring his groin",
			"Andy Carroll receiving a court order that forced him to live with Kevin Nolan",
			"Joe Kinnear going on a scouting trip to Birmingham and coming away impressed by Shane Ferguson, who was on loan there from Newcastle",
			"Alan Pardew headbutting David Meyler in the middle of a match against Hull",
			"Lee Clark, then a Sunderland player, turning up at the 1998 FA Cup final between Arsenal and Newcastle in a \"Sad Mackem BasChampionships\" t-shirt",
			"Clarence Acuna getting pulled over by the police while drunk and dressed as Captain Hook, citing he was too embarrassed to walk in fancy dress",
			"Faustino Asprilla agreeing to join Newcastle because he was told it was by the sea and assuming it would be full of beaches and bikinis",
			"Faustino Asprilla turning up to training 40 mins early rather than his usual 20 mins late because he didn't know the clocks had changed",
			"Alan Pardew being given an eight year contract, which still has another three years to run on it - two years after he left",
			"Kevin Keegan threatening to drop his entire back four of Watson, Peacock, Howey and Beresford after they said they wanted to play safer",
			"Freddy Shepherd and Douglas Hall being caught calling all female Newcastle supporters \"dogs\"",
			"Yohan Cabaye being denied a visa for a preseason tour of America due to an unpaid dentist bill",
			"Steve McClaren requesting players attend home games in suits so Chancel Mbemba and Florian Thauvin arrived in tuxedos",
			"When Steven Taylor was shot by a sniper: https://www.youtube.com/watch?v=vl3HnU0HOhk",
			"Selling Andy Carroll for a club record £35m and replacing him days later with 33 year old Shefki Kuqi on a free transfer",
			"Adjusting our ticketing structure after the fans chanted \"If Sammy Ameobi scores we're on the pitch\". He scored. They went on the pitch",
			"Sammy Ameobi and Demba Ba threatening a noise complaint to a hotel before realising that someone had left a radio on in their wardrobe",
			"Having a kick-off against Leicester delayed for an hour because our newly installed electronic screen nearly blew off in the wind",
			"Shola Ameobi ringing the police because of a suspected break in, then cancelling the call out when he realised his house was just untidy",
			"Patrick Kluivert losing a $4,000 diamond earring in a UEFA Cup match, which was more than our opponents' best paid player earned a week",
			"At closing time, Faustino Asprilla would often invite entire nightclubs of people back to his house to carry on partying",
			"Charles N'Zogbia being forced to hand in a transfer request after Joe Kinnear called him \"Charles Insomnia\" in a post-match interview",
			"Steven Taylor having to have his jaw wired because Andy Carroll punched him and broke it *at the training ground*",
			"NUFC being forced to deny that we were subject to a takeover attempt by WWE owner Vince McMahon",
			"when Laurent Robert decided to do this to Olivier Bernard for reasons unknown. https://www.youtube.com/watch?v=LltnTI7MzIM",
			"Shay Given being awarded man of the match after we lost 5-1 to Liverpool",
			"Laurent Robert throwing literally all his clothing except his Y-fronts into the crowd In his last match",
			"Shola Ameobi appearing on MTV Cribs, and spending most of his time talking about his coffee table",
			"Temuri Ketsbaia scoring against Bolton and throwing his shirt into the crowd, it not being returned so kicking the hoardings until it was",
			"Shay Given being the only Irishman who didn't know where Dublin is https://www.youtube.com/watch?v=3Y0kpT_DD6I",
			"John Carver claiming he was the best coach in the Premier League, after winning 9 points from a possible 48",
			"FIFA refusing to allow Hatem Ben Arfa to move to Nice because he'd made one appearance for Newcastle's reserve side",
			"Barcelona allegedly wanting to sign Steven Taylor, and offering Carles Puyol in exchange",
			"Chancel Mbemba taking to the pitch in the Tyne-Wear derby with \"MBMEMBA\" on the back of his shirt",
			"Newcastle turning down the chance to sign Zinedine Zidane for £1.2m in 1996 by saying he \"wasn't even good enough to play in Division One\"",
			"Blackburn attempting to get 25 year old Alan Shearer to turn down a move to Newcastle by offering him the role of player-manager",
			"Kieron Dyer being injured for a month after poking himself in the eye with a pole during training",
			"Andy Carroll being injured for a month after falling off a bar stool",
			"Uruguayans tweeting abuse such as \"Your mother in a thong\" to Paul Dummett after a tackle on Luis Suarez may have kept him out the World Cup",
			"Joe Kinnear's first official press conference as Newcastle manager beginning with, \"Which one is Simon Bird? You're a cunt.\"",
			"Winning the Intertoto Cup, only to discover it's less of a cup and more of a certificate https://www.shelfsidespurs.com/forum/attachments/toto_plaque2_348x470-jpg.2437/",
			"Then assistant manager John Carver going over to the fans after defeat at Southampton and offering to fight them",
			"Jonathan Woodgate smashing a pint glass over his own head while on holiday in Ibiza",
			"Duncan Ferguson trying to buy Nolberto Solano a live llama as a Christmas present, but not finding anybody that would ship one to Newcastle",
			"Losing the Charity Shield 4-0 against Manchester United, putting out the exact same starting XI for the league fixture and winning 5-0"
		]
		this = random.choice(facts)
		await ctx.send(f"<:mbemba:332196308825931777> Mbemba {this}?")
	
	@commands.command()
	@commands.check(nufccheck)
	async def radio(self,ctx):
		await ctx.send("<:badge:332195611195605003>  Radio Coverage: https://www.nufc.co.uk/liveaudio.html")
	
	@commands.command()
	@commands.check(nufccheck)
	async def rules(self,ctx):
		""" Show the rules for the r/NUFC discord """
		e = discord.Embed(title="= r/NUFC Discord Rules",color=0x111)
		e.description=("**1.** No [brigading](https://www.reddit.com/r/OutOfThe"
			"Loop/comments/36xhxc/what_is_brigading_and_how_do_you_do_it/)\n"
			"**2.** No spam (including bot commands)\n"
			"**3.** No discrimination or harassment\n"
			"In short, don't be a cunt and you won't get banned.")
		e.set_thumbnail(url="https://b.thumbs.redditmedia.com/iVPl7BnL44HwSnX_aKil_NudzWffKQlPiVCZPJZDh4M.png")
		await ctx.send(embed=e)	
	
	@commands.command()
	@commands.check(nufccheck)
	async def faq(self,ctx):
		""" Link the the r/NUFC FAQ """
		await ctx.send("<:NewcastleUnitedBadge:244318116996186112>"
				"**r/NUFC FAQ**: https://www.reddit.com/r/NUFC/wiki/faq")
	
	@commands.command()
	async def hot(self,ctx):
		""" Get the hot posts from r/NUFC """
		posts = await self.bot.loop.run_in_executor(None,self._hot)
		outstring = ""
		count = 1
		for i in posts:
			outstring += f"[{i.title}]({i.url})\n{i.score} pts, *submitted by [/u/{i.author}](https://www.reddit.com/user/{i.author})*\n\n"
			count += 1
		e = discord.Embed(description=outstring,color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
		 "/b/b5/Reddit-The-Official-App-Icon.png")
		e.set_author(name="Hot posts in r/NUFC",icon_url=th)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.timestamp = datetime.datetime.now()
		e.url = "http://www.reddit.com/r/NUFC/hot"
		await ctx.send(embed=e)
	
	def _hot(self):
		return self.bot.reddit.subreddit("NUFC").hot(limit=5)
		
	@commands.command()
	async def top(self,ctx,*,time = "all"):
		""" Get the top posts from r/NUFC (optionally by time period)"""
		if time not in ["all","hour","day","week","month","year","a","h","d","w","m","y"]:
			return await ctx.send("Invalid time specified, valid options are: 'all', 'hour', 'day',  'week', 'month', and 'year'")
		time = "all" if time == "a" else time 
		time = "year" if time == "y" else time
		time = "month" if time == "m" else time
		time = "week" if time == "w" else time 
		time = "day" if time == "d" else time
		time = "hour" if time == "h" else time 
		posts = await self.bot.loop.run_in_executor(None,self._top,time)
		outstring = ""
		count = 1
		for i in posts:
			outstring += f"[{i.title}]({i.url})\n{i.score} pts, *submitted by [/u/{i.author}](https://www.reddit.com/user/{i.author})*\n\n"
			count += 1
		e = discord.Embed(description=outstring,color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
		 "/b/b5/Reddit-The-Official-App-Icon.png")
		time = "all time" if time == "all" else f"this {time}"
		time = "today" if time == "this day" else time
		e.set_author(name=f"Top posts in r/NUFC ({time})",icon_url=th)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.timestamp = datetime.datetime.now()
		e.url = "http://www.reddit.com/r/NUFC/top/"
		await ctx.send(embed=e)
	
	@commands.command()
	async def new(self,ctx):
		""" Get the newest posts from r/NUFC """
		posts = await self.bot.loop.run_in_executor(None,self._new)
		outstring = ""
		count = 1
		for i in posts:
			outstring += f"[{i.title}]({i.url})\n{i.score} pts, *submitted by [/u/{i.author}](https://www.reddit.com/user/{i.author})*\n\n"
			count += 1
		e = discord.Embed(description=outstring,color=0xff4500)
		th = ("http://vignette2.wikia.nocookie.net/valkyriecrusade/images"
		 "/b/b5/Reddit-The-Official-App-Icon.png")
		e.set_author(name=f"Newest posts in r/NUFC",icon_url=th)
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.timestamp = datetime.datetime.now()
		e.url = "http://www.reddit.com/r/NUFC/new"
		await ctx.send(embed=e)
	
	def _hot(self):
		return self.bot.reddit.subreddit("NUFC").hot(limit=5)
		
	def _top(self,time):
		return self.bot.reddit.subreddit("NUFC").top(limit=5,time_filter=time)
	
	def _new(self):
		return self.bot.reddit.subreddit("NUFC").new(limit=5)
	
	@commands.command(aliases=["profile"])
	@commands.check(nufccheck)
	async def player(self,ctx,*,who):
		""" Displays player card with stats. Navigate pages using reactions """
		await ctx.trigger_typing()
		pl = await self.get_players()
		if len(who) < 4:
			await ctx.send(f"🚫 {who} argument length too short"
				" minimum of 4 characters required.")
			return
		else:
			w8 = await ctx.send("Filtering...")
		found = 0
		dicts = []
		for name in pl.keys():
			if unidecode(who.lower()) in unidecode(name):
				found += 1
				await w8.edit(content=f"Found {found}, getting stats...")
				link = pl[name][1]
				team = pl[name][1].split("/")[2].replace("-"," ").title()
				async with self.bot.session.get(f"https://www.nufc.co.uk/{link}") as resp:
					if resp.status != 200:
						await ctx.send(f"HTTP Error getting {name} player card: Status {resp.status}")
						return
					tree = html.fromstring(await resp.text())
				
				# Extract Stats
				dds = tree.xpath('.//dd[//text()][preceding-sibling::dt[//text()]]')
				dts = tree.xpath('.//dt[//text()][following-sibling::dd[//text()]]')
				dd,dt = [],[]
				[dd.append("".join(i.xpath('.//text()'))) for i in dds]
				[dt.append("".join(i.xpath('.//text()'))) for i in dts]
				stats = dict(zip(dt,dd))
				yc = "".join(tree.xpath('.//span[contains(@class,"player-stat-group__yel")]/text()'))
				rc = "".join(tree.xpath('.//span[contains(@class,"player-stat-group__red")]/text()'))
				
				# Clean up oddities.
				if "Height:" in stats:
					stats["Height:"] = f"{stats['Height:']} cm"
				if "Weight:" in stats:
					stats["Weight:"] = f"{stats['Weight:']} kg"
				if "Pass success rate" in stats:
					stats["Pass success rate"] = f"{stats['Pass success rate']}%"
				if "2016/17 First Team Appearances:" in stats:
					stats.pop("2016/17 First Team Appearances:")
				if "Substitute" in stats:
					stats.pop("Substitute")
				for i in "Long Balls","Short Balls":
					if i in stats:
						stats[i] = stats[i].replace(" %","")
				
				# Generate Cover Page
				cover = discord.Embed()
				# Set background
				coverphoto = "".join(tree.xpath('.//figure/img/@data-src')[:-1])
				if coverphoto != "":
					cover.set_image(url=coverphoto)
				cover.description  = "".join(tree.xpath('.//p[@itemprop = "description"]/text()'))
				cover.set_footer(text=f"🖼 {ctx.author.display_name}: react to change pages.")
				
				# Generate Bio Page
				bio = discord.Embed(title="Quick Stats",description="")
				biostats = ["Position:","Squad Number:","Nationality:",
						"Date of birth:","Place of birth:","Height:",
						"Weight:","Date signed:","Debut:","Previous club:"]
				for i in biostats:
					try:
						bio.description += f"**{i}** {stats.pop(i)}\n"
					except KeyError:
						pass
				bio.description.replace('Previous Club','Previous Clubs')
				bio.set_footer(text=f"ℹ {ctx.author.display_name}: react to change pages.")
				
				# Generate Season Stats Page
				season = discord.Embed(title="Season Stats")
				a = '2016/17 First Team Appearances'
				d = ""
				if a in stats:
					d += f"**{a}:** {stats.pop(a)}"
				if 'Started' in stats:
					d += f" ({stats.pop('Started')} started)"
				d += "\n"
				
				if "Win Ratio" in stats:
					d += f"**Win Ratio:** {stats.pop('Win Ratio')}\n"
				if "Goals" in stats:
					goals = stats.pop('Goals')
					d += f"**Goals**: {goals}\n"
				if "Assists" in stats:
					assists = stats.pop('Assists')
					d += f"**Assists**: {assists}\n"
				for i in ["Minutes Played","Touches"]:
					if i in stats:
						d += f"**{i}:** {stats.pop(f'{i}')}\n"
				if "yc" != "":
					d += f"**Yellow Cards**: {rc}\n"
				if "rc" != "":
					d += f"**Red Cards**: {rc}\n"
				
				season.description = d
				season.set_footer(text=f"🗓 {ctx.author.display_name}: react to change pages.")
				
				# Generate Defensive Stats Page
				defen = discord.Embed(title="Defending Stats")
				d = ""
				dlist = ["Tackles Won and lost","Fouls","Interceptions","Clearances",
						"Blocks","Duels Won and Lost","Aerial duels Won / Lost"]
				for i in dlist:
					if i in stats:
						d += f"**{i}:** {stats.pop(f'{i}')}\n"
				defen.description = d.replace("Won and lost","won/lost")
				defen.set_footer(text=f"🛡 {ctx.author.display_name}: react to change pages.")
				
				# Generate Offensive Stats Page
				offen = discord.Embed(title="Attacking Stats")
				d = ""
				if "goals" in locals():
					d += f"**Goals:** {goals}\n"
					glist = ["Left Foot","Right Foot","Head","Penalty"]
					v = ""
					for i in glist:
						if i in stats:
							v += f"**{i}:** {stats.pop(f'{i}')}\n"
					offen.add_field(name="Goals",value=v)
				if "assists" in locals():
					d += f"**Assists:** {assists}\n"
				olist = ["Big Chances","Shots on Target","Shots off Target"]
				for i in olist:
					if i in stats:
						d += f"**{i}:** {stats.pop(f'{i}')}\n"
				offen.description = d
				if "Total Passes" in stats:
					v = f"**Total Passes:** {stats.pop('Total Passes')}\n"
					passlist = ["Pass success rate","Short Balls","Long Balls",
								"Crosses","Key Passses"]
					for i in passlist:
						if i in stats:
							v += f"**{i.title()}:** {stats.pop(f'{i}')}\n"
					v = v.replace('Passses','Passes')
					offen.add_field(name="Passing",value=v)
				offen.set_footer(text=f"⚔ {ctx.author.display_name}: react to change pages.")
				
				# Normalise Embeds
				pname = stats.pop('Full Name:')
				pic = pl[name][0]
				embeds = [cover,bio,season,defen,offen]
				for i in embeds:
					i.set_author(name=f"≡ NUFC {team} profile: {pname}")
					i.url = f"https://www.nufc.co.uk/{link}"
					# Cover has unique Thumbnail
					if i.title == "":
						i.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Newcastle_United_Logo.svg/1017px-Newcastle_United_Logo.svg.png")	
					else:
						i.set_thumbnail(url=f"https://www.nufc.co.uk/{pic}")
					i.color=0x111111
				
				# Generate dict
				valid = {}
				if cover.description != "":
					valid["🖼"]	= cover
				if bio.description != "":
					valid["ℹ"] 	= bio
				if season.description != "":
					valid["🗓"] 	= season
				if defen.description != "":
					valid["🛡"] = defen
				if offen.description != "":
					valid["⚔"]  = offen
				dicts.append(valid)
		await w8.delete()
		async def paginating(self,ctx,m,valid):
			def check(reaction,user):
				if user == ctx.author and reaction.message.id == m.id:
					e = str(reaction.emoji)
					return e in valid.keys()
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					break
				res = res[0]
				await m.edit(embed=valid[res.emoji])
				await m.remove_reaction(res.emoji,ctx.message.author)
			await m.clear_reactions()
		for i in dicts:
			m = await ctx.send(embed=i["🖼"])
			for j in i.keys():
				await m.add_reaction(j)
			self.bot.loop.create_task(paginating(self,ctx,m,i))
		
def setup(bot):
	bot.add_cog(NUFC(bot))
