from discord.ext import commands
import discord, aiohttp, asyncio
from lxml import html
from PIL import Image, ImageDraw, ImageFont
import pycountry
import operator

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}
ctrydict = {"Wales":"gb","England":"gb","Scotland":"gb","Northern Ireland":"gb","Cote d'Ivoire":"ci","Venezuela":"ve","Macedonia":"mk","Kosovo":"xk","Faroe Island":"fo","Trinidad and Tobago":"tt","Congo DR":"cd","Moldova":"md","Korea, South":"kr","Korea, North":"kp", "Bolivia":"bo","Iran":"ir","Hongkong":"hk","Tahiti":"fp","Vietnam":"vn","Chinese Taipei (Taiwan)":"tw","Russia":"ru","N/A":"x","Cape Verde":"cv","American Virgin Islands":"vi","Turks- and Caicosinseln":"tc","Czech Republic":"cz","CSSR":"cz","Neukaledonien":"nc","St. Kitts &Nevis":"kn","Palästina":"ps","Osttimor":"tl","Bosnia-Herzegovina":"ba","Laos":"la","The Gambia":"gm","Botsuana":"bw","St. Louis":"lc","Tanzania":"tz","St. Vincent & Grenadinen":"vc","Cayman-Inseln":"ky","Antigua and Barbuda":"ag","British Virgin Islands":"vg","Mariana Islands":"mp","Sint Maarten":"sx","Federated States of Micronesia":"fm","Netherlands Antilles":"nl"}

numdict = {
	"0":"0⃣","1":"1⃣","2":"2⃣","3":"3⃣","4":"4⃣",
	"5":"5⃣","6":"6⃣","7":"7⃣","8":"8⃣","9":"9⃣"
	}

unidict = {
	"a":"🇦","b":"🇧","c":"🇨","d":"🇩","e":"🇪",
	"f":"🇫","g":"🇬","h":"🇭","i":"🇮","j":"🇯",
	"k":"🇰","l":"🇱","m":"🇲","n":"🇳","o":"🇴",
	"p":"🇵","q":"🇶","r":"🇷","s":"🇸","t":"🇹",
	"u":"🇺","v":"🇻","w":"🇼","x":"🇽","y":"🇾","z":"🇿"
	}

def enumereplace(list):
	for key in numdict:
		list = [x.replace(key,numdict[key]) for x in list]
	return list
	
class Transfers:
	""" Test functions """
	def __init__(self, bot):
		self.bot = bot

	def getFlags(self,list):
		ctryX = []
		for x in list:
			try:					
				x = pycountry.countries.get(name=x.title()).alpha_2
			except KeyError:
				try:
					x = ctrydict[x]
				except KeyError:
					print(f"Fail for: {x}")
			ctryX.append(x)
		ctryX = [x.lower() for x in ctryX]
		for key,value in unidict.items():
			ctryX = [x.replace(key,value) for x in ctryX]
		return ctryX	
		
	async def paginate(self,list,splitat):
		paginated = [list[i:i+splitat] for i in range(0, len(list), splitat)]
		numpages,remainder = divmod(len(list), splitat)
		pages = []
		if remainder != 0:
			numpages += 1
		pcount = 0
		for page in paginated:
			pcount += 1
			pages.append(page)
		return pages,numpages
		
	async def add_reactions(self,m,numpages):
		await m.add_reaction("⏏") # eject
		if numpages > 1:
			if numpages > 2:
				await m.add_reaction("⏮") # first
			await m.add_reaction("◀") # prev
			await m.add_reaction("▶") # next
			if numpages > 2:
				await m.add_reaction("⏭") # last
				
	@commands.group(invoke_without_command=True)
	async def lookup(self,ctx,*,target:str):
		""" Perform a database lookup on transfermarkt """

		p = {"query":target}
		async with self.bot.session.post(f"http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche",params=p) as resp:
			if resp.status != 200:
				return await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
			tree = html.fromstring(await resp.text())
		
		cats = [i.lower() for i in tree.xpath(".//div[@class='table-header']/text()")]
		
		replacelist = ["🇦","🇧",'🇨','🇩','🇪','🇫','🇬']
		
		matches = {
			"players":{"cat":"Players","func":self._player},
			"managers":{"cat":"Managers","func":self._manager},
			"clubs":{"cat":"Clubs","func":self._team},
			"referees":{"cat":"Referees","func":self._ref},
			"to competitions":{"cat":"Competitions","func":self._cup},
			"international":{"cat":"International Competitions","func":self._int},
			"agent":{"cat":"Agents","func":self._agent}
		}
		
		res = {}
		for i in cats:
			# Just give us the number of matches by replacing non-digit characters.
			length = [int(n) for n in i if n.isdigit()][0]
			if length:
				letter = replacelist.pop(0)
				for j in matches:
					if j in i:
						res[letter] = (f"{letter} {length} {matches[j]['cat']}",matches[j]['func'])
		if not res:
			return await ctx.send(f":mag: No results for {target}")
		
		sortedlist = [i[0] for i in sorted(res.values())]

		# If only one category has results, invoke that search.
		if len(sortedlist) == 1:
			return await res["🇦"][1]

			
		res["⏏"] = ("","")
		e = discord.Embed(url = str(resp.url))
		e.title = "View full results on transermarkt"
		e.description = "\n".join(sortedlist)
		e.set_author(name="Select a category using reactions")
		e.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
		m = await ctx.send(embed=e)
		for key in sorted(res.keys()):
			await m.add_reaction(key)

		def check(reaction,user):
			if reaction.message.id == m.id and user == ctx.author:
				e = str(reaction.emoji)
				return e in res.keys()
		
		# Wait for appropriate reaction
		try:
			rea = await self.bot.wait_for("reaction_add",check=check,timeout=120)
		except asyncio.TimeoutError:
			return await m.clear_reactions()
		rea = rea[0]
		if rea.emoji == "⏏": #eject cancels.
			return await m.clear_reactions()
		elif rea.emoji in res.keys():
			# invoke appropriate subcommand for category selection.
			await m.delete()
			return await ctx.invoke(res[rea.emoji][1],target=target)
			

	@lookup.command(name="player",invoke_without_command=True)
	async def _player(self,ctx,*,target:str):
		""" Search transfermarkt for players by query string """
		tquery = target.replace(' ','+')
		page = 1
		async def plookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Spieler_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					if "players" in categories[i - 1]:
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						# Scrape Data
						pname = tree.xpath('//td[@class="hauptlink"]/a[@class="spielprofil_tooltip"]/text()')
						plink = tree.xpath('//a[@class="spielprofil_tooltip"]/@href')
						plink = ["http://transfermarkt.co.uk"+x for x in plink]
						pteam = tree.xpath('//a[@class="vereinprofil_tooltip"]/text()|//a[@title="End of career"]/text()|//a[@title="Unknown"]/text()|//a[@title="---"]/text()|//a[@title="Career break"]/text()|//a[@title="Free agent"]/text()')
						tlink = tree.xpath('//a[@class="vereinprofil_tooltip"]/@href|//a[@title="End of career"]/@href|//a[@title="Unknown"]/@href|//a[@title="---"]/@href|//a[@title="Career break"]/@href|//a[@title="Free agent"]/@href')
						tlink = ["http://transfermarkt.co.uk"+x for x in tlink]
						countrysrch = f'//table[@class="items"][{i}]/tbody/tr/td/img[1]/@title'
						ages  = tree.xpath('//td[@class="zentriert"][3]/text()')
						ppos  = tree.xpath('//td[@class="zentriert"][1]/text()')
						ctry  = tree.xpath(countrysrch)
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)

						# Combine
						plist = list(zip(ctryX,pname,plink,ages,ppos,pteam,tlink))
						markup = '\n'.join('{} [{}]({}) {}, {} [{}]({})'.format(*values) for values in plist)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} players")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await plookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await plookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)
				
	@lookup.command(name="manager",aliases=["staff"])
	async def _manager(self,ctx,*,target):
		""" Lookup a manager """
		tquery = target.replace(' ','+')
		page = 1
		async def mlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Trainer_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "managers" in categories[i-1].lower():
						whattable = f'(//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						# Scrape Data
						pname = subtable.xpath('.//td[@class="hauptlink"]/a/text()')
						plink = subtable.xpath('.//td[@class="hauptlink"]/a/@href')
						plink = ["http://transfermarkt.co.uk"+x for x in plink]
						pteam = subtable.xpath('.//a[@class="vereinprofil_tooltip"]/text()|.//a[@title="End of career"]/text()|.//a[@title="Unknown"]/text()|.//a[@title="---"]/text()|.//a[@title="Career break"]/text()|.//a[@title="Free agent"]/text()')
						tlink = subtable.xpath('.//a[@class="vereinprofil_tooltip"]/@href|.//a[@title="End of career"]/@href|.//a[@title="Unknown"]/@href|.//a[@title="---"]/@href|.//a[@title="Career break"]/@href|.//a[@title="Free agent"]/@href')
						tlink = ["http://transfermarkt.co.uk"+x for x in tlink]
						ages  = subtable.xpath('.//td[@class="zentriert"][2]/text()')
						ppos  = subtable.xpath('.//td[@class="rechts"][1]/text()')
						countrysrch = f'(//table[@class="items"])[{i}]/tbody/tr/td/img[1]/@title'
						ctry  = tree.xpath(countrysrch)
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)
						# Combine
						plist = list(zip(ctryX,pname,plink,ages,ppos,pteam,tlink))
						markup = '\n'.join('{} [{}]({}) {}, {} [{}]({})'.format(*values) for values in plist)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} staff")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await mlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await mlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)
			
	@lookup.command(name="team",aliases=["club"])
	async def _team(self,ctx,*,target):
		""" Lookup a team """
		tquery = target.replace(' ','+')
		page = 1
		async def tlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Verein_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None					
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "clubs" in categories[i - 1].lower():
						whattable = f'(.//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						# Scrape Data
						datasq = subtable.xpath('.//table[@class="inline-table"]')
						teamclub = []
						for j in datasq:
							cname = j.xpath('.//td[@class="hauptlink"]/a/text()')[0]
							clink = j.xpath('.//td[@class="hauptlink"]/a/@href')[0]
							clink = "http://transfermarkt.co.uk"+clink
							leagu = j.xpath('.//tr[2]/td/a/text()')
							lglin = j.xpath('.//tr[2]/td/a/@href')
							if len(leagu) > 0:
								leagu = leagu[0]
								lglin = lglin[0]
								lglin = "http://transfermarkt.co.uk"+lglin
								thisclub = f"[{cname}]({clink}) ([{leagu}]({lglin}))"
							else:
								thisclub = f"[{cname}]({clink})"
							teamclub.append(thisclub)
						ctry = subtable.xpath('.//td/img[@class="flaggenrahmen"]/@title')
						ctry = [x for x in ctry if x != "\xa0"]
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)
						# Combine
						plist = list(zip(ctryX,teamclub))
						markup = '\n'.join('{} {}'.format(*values) for values in plist)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} clubs")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await tlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await tlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)
	
	@lookup.command(name="ref",aliases=["referee"])
	async def _ref(self,ctx,*,target):
		""" Lookup a referee """
		tquery = target.replace(' ','+')
		page = 1
		async def rlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Schiedsrichter_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "referees" in categories[i - 1].lower():
						whattable = f'(.//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						print(numfound)
						# Scrape Data
						refrow = subtable.xpath('./tbody/tr')
						refdata = []
						for j in refrow:
							rname = j.xpath('.//td[@class="hauptlink"]/a/text()')
							rlink = j.xpath('.//td[@class="hauptlink"]/a/@href')
							rage  = j.xpath('.//td[@class="zentriert"]/text()')
							if len(rname) > 0:
								rlink[0] = "http://transfermarkt.co.uk"+rlink[0]
								refdata.append(f"[{rname[0]}]({rlink[0]}) ({rage[0]})")
						ctry = subtable.xpath('.//td/img[@class="flaggenrahmen"]/@title')
						ctry = [x for x in ctry if x != "\xa0"]
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)
						# Combine
						plist = list(zip(ctryX,refdata))
						markup = '\n'.join('{} {}'.format(*values) for values in plist)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} referees")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await rlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await rlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)

	@lookup.command(name="cup",aliases=["competition","league","trophy","tournament"])
	async def _cup(self,ctx,*,target):
		""" Lookup a club competition """
		tquery = target.replace(' ','+')
		page = 1
		async def rlookup(tquery,page):
			query = 'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Wettbewerb_page={}&query={}'.format(page,tquery)
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "to competitions" in categories[i - 1].lower():
						whattable = '(.//table[@class="items"])[{}]'.format(i)
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						print(numfound)
						# Scrape Data
						cuprow = subtable.xpath('./tbody/tr')
						cupdata = []
						for j in cuprow:
							cupname = j.xpath('.//td[2]/a/text()')
							cuplink = j.xpath('.//td[2]/a/@href')
							numclubs = j.xpath('.//td[4]/text()')
							numplayers  = j.xpath('.//td[5]/text()')
							flag = j.xpath('.//td[3]/img/@title')
							ctry = self.getFlags(flag)
							if len(ctry) > 0:
								ctry = ctry[0]
								ctry = ctry.replace("\xa0","")
							else:
								ctry = ":globe_with_meridians:"
							if len(cupname) > 0:
								cuplink[0] = "http://transfermarkt.co.uk"+cuplink[0]
								if numclubs[0].isdigit():
									cupdata.append(f"{ctry} [{cupname[0]}]({cuplink[0]}): {numclubs[0]} clubs, {numplayers[0]} players")
								else:
									cupdata.append(f"{ctry} [{cupname[0]}]({cuplink[0]})")
						# Combine
						markup = '\n'.join(cupdata)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} club competitions")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await rlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await rlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)		

	@lookup.command(name="international",aliases=["int"])
	async def _int(self,ctx,*,target):
		""" Lookup an international competition """
		tquery = target.replace(' ','+')
		page = 1
		async def rlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Wettbewerb_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "international" in categories[i - 1].lower():
						whattable = '(.//table[@class="items"])[{}]'.format(i)
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						print(numfound)
						# Scrape Data
						cuprow = subtable.xpath('./tbody/tr')
						cupdata = []
						for j in cuprow:
							cupname = j.xpath('.//td[2]/a/text()')
							cuplink = j.xpath('.//td[2]/a/@href')
							numclubs = j.xpath('.//td[3]/text()')
							numplayers  = j.xpath('.//td[4]/text()')
							if len(cupname) > 0:
								cuplink[0] = "http://transfermarkt.co.uk"+cuplink[0]
								if numclubs[0].isdigit():
									if int(numclubs[0]) > 0:
										cupdata.append(f"[{cupname[0]}]({cuplink[0]}): {numclubs[0]} clubs, {numplayers[0]} players")
									else:
										cupdata.append(f"[{cupname[0]}]({cuplink[0]})")
								else:
									cupdata.append(f"[{cupname[0]}]({cuplink[0]})")
						# Combine
						markup = '\n'.join(cupdata)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} international competitions")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await rlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await rlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)
			
	@lookup.command(name="agent")
	async def _agent(self,ctx,*,target):
		""" Lookup an agent """
		tquery = target.replace(' ','+')
		page = 1
		async def rlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "agent" in categories[i - 1].lower():
						whattable = f'(.//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						print(numfound)
						# Scrape Data
						agentrow = subtable.xpath('./tbody/tr')
						agents = []
						for j in agentrow:
							company = j.xpath('.//td[2]/a/text()')
							comlink = j.xpath('.//td[2]/a/@href')
							if len(company) > 0:
								comlink[0] = "http://transfermarkt.co.uk"+comlink[0]
								agents.append(f"[{company[0]}]({comlink[0]})")
						# Combine
						markup = '\n'.join(agents)
						em = discord.Embed(title="View full results on transermarkt",url=query,description=markup)
						em.set_author(name=f"Found {numfound} agents")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound
					i += 1
				return None
		try:
			em,numfound = await rlookup(tquery,page)
			m = await ctx.send(embed=em)
			numpages = (numfound // 10) + 1
			await self.add_reactions(m,numpages)
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏'))
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.author)
				if res.emoji == "⏏": #eject
					break
				em,numfound = await rlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					print(len(em.description))
		except TypeError:
			if len(target) < 3:
				await ctx.send(f":mag: {target}: Search queries must be min 3 characters",delete_after=10)
			else:
				await ctx.send(f":mag: No results for {target}",delete_after=10)
			
	@commands.command(aliases=["suspended","injured"])
	async def injuries(self,ctx,*,team):
		""" Get injury data for a team """
		# Do a search by team
		tquery = team.replace(' ','+')
		page = 1
		async def tlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Verein_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "clubs" in categories[i - 1].lower():
						whattable = f'(.//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						# Scrape Data
						datasq = subtable.xpath('.//table[@class="inline-table"]')
						teamclub = []
						linklist = []
						for j in datasq:
							cname = j.xpath('.//td[@class="hauptlink"]/a/text()')[0]
							clink = j.xpath('.//td[@class="hauptlink"]/a/@href')[0]
							clink = "http://transfermarkt.co.uk"+clink
							leagu = j.xpath('.//tr[2]/td/a/text()')
							lglin = j.xpath('.//tr[2]/td/a/@href')
							if len(leagu) > 0:
								leagu = leagu[0]
								lglin = lglin[0]
								lglin = "http://transfermarkt.co.uk"+lglin
								thisclub = f"[{cname}]({clink}) ([{leagu}]({lglin}))"
							else:
								thisclub = f"[{cname}]({clink})"
							linklist.append(clink)
							teamclub.append(thisclub)
						ctry = subtable.xpath('.//td/img[@class="flaggenrahmen"]/@title')
						ctry = [x for x in ctry if x != "\xa0"]
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)
						ctry = list(enumerate(ctryX))
						ctryX = []
						for x,y in ctry:
							ctryX.append(f"{x}{y}")
						ctry = enumereplace(ctryX)
						# Combine
						plist = list(zip(ctry,teamclub))
						markup = '\n'.join('{} {}'.format(*values) for values in plist)
						em = discord.Embed(title="Select a club using reactions",url=query,description=markup)
						em.set_author(name=f"Found {numfound} clubs")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound,linklist
					i += 1
				return None
		em,numfound,linklist = await tlookup(tquery,page)
		
		if len(linklist) > 1:
			m = await ctx.send(embed=em)
			numpages = (numfound // 10)+1
			if numpages > 1:
				if numpages > 2:
					await m.add_reaction("⏮") # first
				await m.add_reaction("◀") # prev
			numlist = []
			for x in em.description.split("\n"):
				emoji = x[:2]
				numlist.append(emoji)
				await m.add_reaction((emoji))			
			if numpages > 1:
				await m.add_reaction("▶") # next
				if numpages > 2:
					await m.add_reaction("⏭") # last
			await m.add_reaction("⏏") # eject
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏')) or e in numlist
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					linktogo = None
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.message.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.message.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.message.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.message.author)
				if res.emoji == "⏏": #eject
					linktogo = None
					break
				else:
					findemoji = [key for key, value in numdict.items() if value == res.emoji][0] # This code is cancer
					linktogo = linklist[int(findemoji)] # get position in dict for id (what an ugly hack)
					break
				em,numfound,linklist = await tlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					await ctx.send("Results list for this page is too long for the embed")
		else:
			linktogo = linklist[0]
		
		# Switch to actual injuries page.
		await m.delete()
		link = linktogo.replace("/startseite/","/sperrenundverletzungen/")
			
		async with self.bot.session.get(link) as resp: #Finally get the actual injured players page for the team
			if resp.status != 200:
				ctx.send(f"HTTP Error trying to access {linktogo}: Code {resp.status}")
				return None
			tree = html.fromstring(await resp.text())
			pname   = tree.xpath('descendant::table[@class="items"][1]/tbody/tr/td/table[@class="inline-table"]/tr/td/a[@class="spielprofil_tooltip"]/text()')
			ppos    = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td/table[@class="inline-table"]/tr/td[1]/text()')
			reason  = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td[3]/text()')
			injdate = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td[4]/text()')
			returns = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td[5]/text()')
			outfor  = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td[6]/a/text()')
			picture = tree.xpath('descendant::div[@id="yw1"]/table[@class="items"][1]/tbody/tr/td/table[@class="inline-table"]/tr/td/img/@src')
			ppos    = [x for x in ppos if x != "\t\t"]
			ppos    = [x for x in ppos if x != "\r\n\t\t\t"]
			injured = list(zip(pname,ppos,reason,injdate,returns,outfor,picture))
			
		paginated,numpages = await self.paginate(injured,1)
		page = 0
		em = discord.Embed(title=f"≡ Injuries and Suspensions for {team}",url=link,color=0x111)
		em.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/toolbar-people/512/user_forbidden_man_male_profile_account_person-512.png")
		async def make_embed(paginated,page):
			field1,field2 = "",""
			for sublist in paginated[page]: # initial population.
				player 		= sublist[0]
				position	= sublist[1]
				type		= sublist[2]
				date		= sublist[3]
				dueback		= sublist[4]
				missed 		= sublist[5]
				picture		= sublist[6]
				em.clear_fields()
				if dueback =="?":
					em.add_field(name=f"{player} ({position})",value=f"{type}\nIncident date: {date}\nGames missed: {missed}\n")
				else:
					em.add_field(name=f"{player} ({position})",value=f"{type}\nIncident date: {date}\nGames missed: {missed}\nDue back: {dueback}")
			if numpages > 1:
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"{ctx.author.display_name}: Page {page + 1} of {numpages}")
		await make_embed(paginated,page)
		m = await ctx.send(embed=em)
		await self.add_reactions(m,numpages)
		def check(reaction,user):
			if reaction.message.id == m.id and user == ctx.author:
				e = str(reaction.emoji)
				return e.startswith(('⏮','◀','▶','⏭','⏏'))
		while True:
			try:
				res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
			except asyncio.TimeoutError:
				await m.clear_reactions()
				break
			res = res[0]
			if res.emoji == "⏮": #first
				page = 0
				await m.remove_reaction("⏮",ctx.author)
			if res.emoji == "◀": #prev
				if page > 0:
					page = page - 1
				await m.remove_reaction("◀",ctx.author)
			if res.emoji == "▶": #next	
				if page < numpages - 1:
					page = page + 1
				await m.remove_reaction("▶",ctx.author)
			if res.emoji == "⏭": #last
				page = numpages - 1
				await m.remove_reaction("⏭",ctx.message.author)
			if res.emoji == "⏏": #eject
				break
			await make_embed(paginated,page)
			await m.edit(embed=em)

	@commands.command()
	async def transfers(self,ctx,*,team):
		""" Get transfers for this window for a team """
		# Do a search by team
		tquery = team.replace(' ','+')
		page = 1
		async def tlookup(tquery,page):
			query = f'http://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?Verein_page={page}&query={tquery}'
			async with self.bot.session.get(query) as resp:
				if resp.status != 200:
					await ctx.send(f"HTTP Error connecting to transfernarkt: {resp.status}")
					return None		
				tree = html.fromstring(await resp.text())
				categories = tree.xpath("descendant::div[@class='table-header']/text()")
				for i in range (1,len(categories)+1):
					# select correct table
					if "clubs" in categories[i - 1].lower():
						whattable = f'(.//table[@class="items"])[{i}]'
						subtable = tree.xpath(whattable)[0]
						length = [int(n) for n in categories[i-1].split() if n.isdigit()]
						numfound = length[0]
						# Scrape Data
						datasq = subtable.xpath('.//table[@class="inline-table"]')
						teamclub = []
						linklist = []
						for j in datasq:
							cname = j.xpath('.//td[@class="hauptlink"]/a/text()')[0]
							clink = j.xpath('.//td[@class="hauptlink"]/a/@href')[0]
							clink = "http://transfermarkt.co.uk"+clink
							leagu = j.xpath('.//tr[2]/td/a/text()')
							lglin = j.xpath('.//tr[2]/td/a/@href')
							if len(leagu) > 0:
								leagu = leagu[0]
								lglin = lglin[0]
								lglin = "http://transfermarkt.co.uk"+lglin
								thisclub = f"[{cname}]({clink}) ([{leagu}]({lglin}))"
							else:
								thisclub = f"[{cname}]({clink})"
							linklist.append(clink)
							teamclub.append(thisclub)
						ctry = subtable.xpath('.//td/img[@class="flaggenrahmen"]/@title')
						ctry = [x for x in ctry if x != "\xa0"]
						ctry = ctry[:10]
						ctryX = self.getFlags(ctry)
						ctry = list(enumerate(ctryX))
						ctryX = []
						for x,y in ctry:
							ctryX.append(f"{x}{y}")
						ctry = enumereplace(ctryX)
						# Combine
						plist = list(zip(ctry,teamclub))
						markup = '\n'.join('{} {}'.format(*values) for values in plist)
						em = discord.Embed(title="Select a club using reactions",url=query,description=markup)
						em.set_author(name=f"Found {numfound} clubs")
						em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
						if numfound > 10:
							em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {1} of {(numfound // 10)+1} ({ctx.author.display_name})")
						return em,numfound,linklist
					i += 1
				return None
		em,numfound,linklist = await tlookup(tquery,page)
		
		if len(linklist) > 1:
			m = await ctx.send(embed=em)
			numpages = (numfound // 10)+1
			if numpages > 1:
				if numpages > 2:
					await m.add_reaction("⏮") # first
				await m.add_reaction("◀") # prev
			numlist = []
			for x in em.description.split("\n"):
				emoji = x[:2]
				numlist.append(emoji)
				await m.add_reaction((emoji))			
			if numpages > 1:
				await m.add_reaction("▶") # next
				if numpages > 2:
					await m.add_reaction("⏭") # last
			await m.add_reaction("⏏") # eject
			def check(reaction,user):
				if reaction.message.id == m.id and user == ctx.author:
					e = str(reaction.emoji)
					return e.startswith(('⏮','◀','▶','⏭','⏏')) or e in numlist
			while True:
				try:
					res = await self.bot.wait_for("reaction_add",check=check,timeout=120)
				except asyncio.TimeoutError:
					await m.clear_reactions()
					linktogo = None
					break
				res = res[0]
				if res.emoji == "⏮": #first
					page = 1
					await m.remove_reaction("⏮",ctx.message.author)
				if res.emoji == "◀": #prev
					await m.remove_reaction("◀",ctx.message.author)
					if page > 1:
						page = page - 1
				if res.emoji == "▶": #next	
					await m.remove_reaction("▶",ctx.message.author)
					if page < numpages:
						page = page + 1
				if res.emoji == "⏭": #last
					page = numpages
					await m.remove_reaction("⏭",ctx.message.author)
				if res.emoji == "⏏": #eject
					linktogo = None
					break
				else:
					findemoji = [key for key, value in emojidict.items() if value == res.emoji][0] # This code is cancer
					sorteddict = sorted(emojidict.items(), key=operator.itemgetter(1))
					linkkey = [y for x,y in enumerate(sorteddict) if y[0] == findemoji] #get index
					linkkey = linkkey[0][0]
					linktogo = linklist[int(linkkey)] # get position in dict for id (what an ugly hack)
					break
				em,numfound,linklist = await tlookup(tquery,page)
				em.set_footer(icon_url="http://pix.iemoji.com/twit33/0056.png",text=f"Page {page} of {numpages} ({ctx.author.display_name})")
				try:
					await m.edit(embed=em)
				except:
					await ctx.send("Results list for this page is too long for the embed")
		else:
			linktogo = linklist[0]
		
		async with self.bot.session.get(linktogo) as resp: # We have the team page. Now let's find current window.
			if resp.status != 200:
				ctx.send(f"HTTP Error trying to access {linktogo}: Code {resp.status}")
				return None
			transferspage = "".join(tree.xpath('.//div[@class="col_3"]/ul/li/a/@href'))
			transferspage = f"http://www.transfermarkt.co.uk{transferspage}"
			
		async with self.bot.session.get(transferspage) as resp: # Finally on the right page...
			if resp.status != 200:
				ctx.send(f"HTTP Error trying to access {linktogo}: Code {resp.status}") # Rip
				return None
			tree = html.fromstring(await resp.text())
			intable = tree.xpath('//div[@class="box"][3]/div[@class="responsive-table"]/table/tbody')[0]
			outtable = tree.xpath('//div[@class="box"][4]/div[@class="responsive-table"]/table/tbody')[0]
			inplayers = intable.xpath('./tr')
			outplayers = outtable.xpath('./tr')
			def parseplayers(plist):
				returnlist = []
				for i in plist:
					pname = i.xpath('.//td/a[@class="spielprofil_tooltip"]/text()')
					plink = i.xpath('.//td/a[@class="spielprofil_tooltip"]/@href')
					plink = f"http://www.transfermarkt.co.uk/{plink[0]}"
					ppos = i.xpath('.//tr[2]/td/text()')
					plage = i.xpath('.//td[3]/text()')
					flag = i.xpath('.//td[5]/img/@title')
					ctry = self.getFlags(flag)
					fee = i.xpath('.//td[7]/a/text()')
					thisplayer = f"{ctry[0]} [{pname[0]}]({plink}) ({plage[0]}): {ppos[0]} ({fee[0]})"
					returnlist.append(thisplayer)
				return returnlist
			inlist = parseplayers(inplayers)
			outlist = parseplayers(outplayers)

			lenin = len(inlist)
			lenout = len(outlist)
			em = discord.Embed(title="Winter Transfers 2017 for NUFC",url="http://www.transfermarkt.co.uk/newcastle-united/transfers/verein/762/saison_id/2016/pos//detailpos/0/w_s/w/plus/1#zugaenge")
			em.set_thumbnail(url="http://combiboilersleeds.com/images/search/search-8.jpg")
			inlist = "\n".join(inlist)
			em.add_field(name="In",value=inlist,inline=False)
			if lenout > 0:
				outlist = "\n".join(outlist)
				em.add_field(name="Out",value=outlist,inline=False)
			em.set_footer(icon_url="http://emojipedia-us.s3.amazonaws.com/cache/61/7d/617dbfd2c46e78eb277eb5509fb85efe.png",text="{} in, {} out".format(lenin,lenout))
			await ctx.send(embed=em)
		
def setup(bot):
	bot.add_cog(Transfers(bot))
