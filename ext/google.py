from discord.ext import commands
from lxml import html
import aiohttp
import asyncio 
import discord


class google:

	""" Google search """
	def __init__(self,bot):
		self.bot = bot
	
	@commands.command()
	async def g(self,ctx,*,qstr:str):
	
		""" Perform a google search """
		p = {"q":qstr,"safe":"on"}
		h = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'}
		cs = self.bot.session
		async with cs.get('https://www.google.com/search',
						  params=p, headers=h) as resp:
			if resp.status != 200:
				err = f"🚫 Google responded with status code {resp.status}"
				return await ctx.send(err)

			tree = html.fromstring(await resp.text())

			# Generate Base Embed
			e = discord.Embed(colour=0xdb3236)
			th = "http://i.imgur.com/2Ielpqo.png"
			e.set_author(name="Google Search",icon_url=th,url=resp.url)
			
			# Scrape Google Cards
			card = tree.xpath(".//*[contains(@id,'topstuff')]")
			if card:
				card = card[0]
				
				# Calculator
				x = ".//table/tr/td/span[@class='nobr']/h2[@class='r']/text()"
				calc = card.xpath(x)
				if calc:
					e.title = "Calculator"
					e.description = calc[0]
					
				# Unit Conversion
				uc = tree.xpath(".//ol//div[@class='_Tsb']")
				if uc:
					uc = uc[0]
					e.title = '🔄 Unit Conversion'
					e.description = "".join(uc.xpath(".//text()"))
					
				# Currency
				curr = tree.xpath(".//ol/table[@class='std _tLi']/tr/td/h2")
				if curr:
					curr = curr[0]
					e.title = '💷 Currency Conversion'
					e.description = "".join(curr.xpath(".//text()"))
							
				# Definition
				x = ".//ol/div[@class='g']/div[h3[@class='r']/div]"
				defin = tree.xpath(x)
				if defin:
					e.title = '📖 Definition'
					defnode = defin[0]
					texts = defnode.xpath(".//text()")
					e.description = f"**{texts[0]}**\n{texts[1]}"
					deftype = defnode.xpath(".//td/div/text()")[0]
					deflist = defnode.xpath(".//ol/li/text()")
					e.add_field(name=deftype,value="\n".join(deflist))
					
				# Date
				release = tree.xpath(".//div[@id='_vBb']")
				if release:
					
					release = release[0]
					fields = release.xpath(".//text()")
					e.title = f'🗓️ {"".join(fields[1:])}'
					e.description = fields[0]
				
				# Time in Card	
				timein = tree.xpath(".//ol//div[@class='_Tsb _HOb _Qeb']")
				if timein:
					timein = timein[0]
					e.title = f"🕛 {timein.xpath('.//text()')[4].strip()}"
					e.description = "".join(timein.xpath(".//text()")[0:4])
				
				# Weather			
				weather = tree.xpath(".//ol//div[@class='e']")
				if weather:
					weather = weather[0]
					items = weather.xpath('.//text()')
					e.description = items[10]
					e.title = "".join(items[0:3])
					we = {
						"Rain":"🌧️",
						"Cloudy":"☁️️",
						"Clear with periodic clouds":"🌤️",
						"Clear":"🌞","Snow Showers":"🌨️",
						"Mostly Cloudy":"☁️️",
						"Mostly Sunny":"🌤",
						"Partly Cloudy":"🌤️",
						"Sunny":"🌞"
						}
					try:
						e.description = f"{we[e.description]} {e.description}"
					except KeyError:
						await ctx.send(f"Emoji not found for {e.description}")
					e.add_field(name="Temperature",value=items[3])
					e.add_field(name="Humidity",value=items[13][9:])
					e.add_field(name="Wind",value=items[12])
					
				# Translate
				x = (".//ol/div[@class='g'][1]//table[@class='ts']"
					"//h3[@class='r'][1]//text()")
				translate = tree.xpath(x)
				if translate:
					e.title = "Translation"
					e.description = "".join(translate)
				
				# Time Conversion
				timecard = tree.xpath("..//div[@class='_NId']")
				if timecard:
					e.title = '≡ Time Conversion'
					e.description = "".join(timecard.xpath(".//text()"))
				
				# Write to file for debugging.
				# with open('google.html', 'w', encoding='utf-8') as f:
					# f.write(html.tostring(tree).decode('utf-8'))
			
			# Search 
			resultnodes = tree.xpath(".//div[@class='g']")
			res = []
			for i in resultnodes:
				link = i.xpath(".//h3[@class = 'r']/a/@href")
				# if not a proper result node, go to next item.
				if not link or "/search?q=" in link[0]:
					continue
				link = link[0]
				
				# strip irrel.
				if "/url?q=" in link:
					link = link.split("/url?q=")[1]# strip irrel.
				if "&sa" in link:
					link = link.rsplit("&sa")[0]
				link = link.replace(')',"%29")
				title = i.xpath("string(.//h3[@class = 'r']/a)")
				desc = i.xpath("string(.//span[contains(@class,'st')])")
				res.append((link,title,desc))
			if not res:
				await ctx.send("🚫 No results found.")
				return
			if e.description == e.Empty:
				e.title = res[0][1]
				e.url = res[0][0]
				e.description = res[0][2]
				more = f"[{res[1][1]}]({res[1][0]})\n[{res[2][1]}]({res[2][0]})"
			else:
				more = (f"[{res[0][1]}]({res[0][0]})\n"
						f"[{res[1][1]}]({res[1][0]})\n"
						f"[{res[2][1]}]({res[2][0]})")
			e.add_field(name="More Results",value=more)
			await ctx.send(embed=e)
			
def setup(bot):
	bot.add_cog(google(bot))