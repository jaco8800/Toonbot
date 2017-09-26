import discord, aiohttp, asyncio
from discord.ext import commands
from lxml import html
import re

class Wikipedia:
	""" Wikipedia Search """
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(aliases=["wikipedia"])
	async def wiki(self,ctx,*,search):
		params = {"search":search}
		async with self.bot.session.get(f"https://en.wikipedia.org/w/index.php",params=params) as resp:
			if resp.status != 200:
				await ctx.send(f"HTTP Error: Wikipedia responded with status code {resp.status}")
				await ctx.send(resp.read)
				return
			tree = html.fromstring(await resp.text())
			e = discord.Embed(color=0xFFFFFF)
			if "https://en.wikipedia.org/w/index.php?search=" in str(resp.url): #Check if search results page
				e.set_author(name=f"{search} - Search results",url=resp.url)
				e.set_footer(text="".join(tree.xpath(".//div[@class='results-info']/strong[2]/text()")))
				desc = ""
				for i in tree.xpath(".//div[@class='searchresults']/ul/li")[:5]: 
					title = "".join(i.xpath(".//a/@title"))
					url = f"http://en.wikipedia.org{i.xpath('.//a/@href')[0]}".replace(")", "%29")
					short = "".join(i.xpath(".//div[@class = 'searchresult']/text()"))
					desc += f"**[{title}]({url})** \n{short}\n"
				if desc == "":
					desc = "There were no results matching the query."
				e.description = desc
				e.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1122px-Wikipedia-logo-v2.svg.png")
			else:
				infobox = tree.xpath(".//table[contains(@class, 'infobox')]")
				print(infobox)
				if infobox != []:
					infobox = infobox[0]
					try:
						th = infobox.xpath(".//img/@src")[0]
						th = f"http:{th}"
						e.set_thumbnail(url=th)
					except IndexError:
						pass
					for i in infobox.xpath(".//tr")[:25]:
						fieldname = "".join(i.xpath(".//th//text()")).strip()
						fieldvalue= "".join(i.xpath(".//td//text()")).strip()
						fieldvalue = re.sub("\\[.*?\\]","",fieldvalue)
						valuelink = i.xpath(".//td//@href")
						try:
							valuelink = valuelink[0]
							if valuelink.startswith("/"): # For links to other wiki pages.
								valuelink = f"http://en.wikipedia.org{valuelink}"
							if valuelink.startswith("#"):
								valuelink = ""
						except:
							valuelink = ""
						if fieldname != "" and fieldvalue != "":
							if valuelink != "":
								fieldvalue = f"[{fieldvalue}]({valuelink.replace(')','%29')})"
								e.add_field(name=fieldname,value=fieldvalue,inline=True)
							else:
								e.add_field(name=fieldname,value=fieldvalue,inline=True)
				else:
					e.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1122px-Wikipedia-logo-v2.svg.png")
					e.set_author(name=f"Wikipedia: {tree.xpath('.//h1//text()')[0]}",url=resp.url)
					e.description = "".join(tree.xpath(".//div[@id = 'mw-content-text']/p[1]//text()"))
					if len(e.description) < 500:
						e.description += "\n"
						e.description += "".join(tree.xpath(".//div[@id = 'mw-content-text']/p[2]//text()"))
					if "may refer to" in e.description.lower():
						refers = tree.xpath(".//ul/li")
						for i in refers[:5]:
							link = "".join(i.xpath('.//text()'))
							try:
								url = i.xpath(".//@href")[0]
								if url.startswith("#"):
									continue
								url = f"http://en.wikipedia.org{url}"
								url.replace(")", "%29")
								e.description += f"[{link}]({url})"
							except IndexError:
								e.description += link
							e.description += "\n"
					extlinks = []
					for i in tree.xpath('.//ul/li/*[a[@class="external text"]]')[:5]: # Get External links
						try:
							link = "".join(i.xpath('.//text()'))
							url = "".join(i.xpath('.//a[@class="external text"]/@href'))
							if url.startswith("//"):
								url = url[-2:]
							url.replace(")", "%29")
							extlinks.append(f"[{link}]({url})")
						except:
							pass
					if extlinks != []:
						e.add_field(name="External Links",value="\n".join(extlinks))
					try:
						img = tree.xpath('.//table[@class="titlebox"]//img/@src')[0]
						imgurl = f"http:{img}"
						e.set_thumbnail(url=imgurl)
						await ctx.send(imgurl)
					except IndexError:
						pass
				
			await ctx.send(embed=e)
	
def setup(bot):
	bot.add_cog(Wikipedia(bot))