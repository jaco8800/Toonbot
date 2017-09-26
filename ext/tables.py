from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver


from lxml import html
from datetime import datetime

from discord.ext import commands
import discord

import asyncio
import json
from copy import deepcopy

import requests
from colorthief import ColorThief
from PIL import Image
from io import BytesIO


class Tables:
	def __init__(self,bot):
		self.bot = bot
	
	# Getter functions
	def get_team(self,qry):
		m = {}
		for i in self.bot.comps:
			for j in self.bot.comps[i]["teams"]:
				x = self.bot.comps[i]["teams"]
				m.update({h:self.bot.comps[i]["teams"][h] for h in x if qry in h})
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
			print(lgs)
			lgs = f"{lg}: {cp}"
			return lgs,self.bot.comps[lg][cp.strip()]["link"]
		
	
	@commands.command()
	async def table(self,ctx,*,qry="England Premier"):
		""" Get table for a league """
		with ctx.typing():
			try:
				lgs,table = self.get_league(qry)
			except TypeError:
				return await ctx.send(f"\🚫 Can't find that competition, correct syntax is: ```{ctx.prefix}{ctx.command} <Country> <Competition>```")
			l = self.bot.loop
			p = await l.run_in_executor(None,self.get_table,table)
			if p is None:
				await ctx.send("🚫 No table found on {table}")
			await ctx.send(f"**{lgs} Table**",file=p)

	@commands.command()
	async def bracket(self,ctx,*,qry="Champions League"):
		""" Get bracket for a Tournament """
		with ctx.typing():
			try:
				lgs,brkt = self.get_league(qry)
			except TypeError:
				return await ctx.send("\🚫 Can't find that competition, correct syntax is: ```{ctx.prefix}{ctx.command} <Country> <Competition>```")
			l = self.bot.loop
			p = await l.run_in_executor(None,self.get_bracket,brkt)
			if not p:
				return await ctx.send("\🚫 Can't bracket on {brkt}")
			await ctx.send(f"**{lgs} Bracket**",file=p)
	
	def get_bracket(self,bracket):
		driver = webdriver.PhantomJS()
		driver.implicitly_wait(2)
		driver.get(bracket)
		xp = './/div[@class="viewport"]'
		bkt = driver.find_element_by_xpath(xp)
		location = bkt.location
		size = bkt.size
		im = Image.open(BytesIO(bkt.screenshot_as_png))
		left = location['x']
		top = location['y']
		right = location['x'] + size['width'] + 33
		bottom = location['y'] + size['height']
		im = im.crop((left, top, right, bottom))
		output = BytesIO()
		im.save(output,"PNG")
		output.seek(0)
		df = discord.File(output,filename="bracket.png")
		driver.quit()
		return df
		
	def get_table(self,table):
		driver = webdriver.PhantomJS()
		driver.implicitly_wait(2)
		driver.get(table)
		try:
			z = driver.find_element_by_link_text("Main")
			z.click()
		except NoSuchElementException:
			pass
		xp = './/table[contains(@id,"table-type-")]'
		tbl = driver.find_element_by_xpath(xp)
		location = tbl.location
		size = tbl.size
		im = Image.open(BytesIO(tbl.screenshot_as_png))
		left = location['x']
		top = location['y']
		right = location['x'] + size['width']
		bottom = location['y'] + size['height']
		im = im.crop((left, top, right, bottom))
		output = BytesIO()
		im.save(output,"PNG")
		output.seek(0)
		df = discord.File(output,filename="table.png")
		driver.quit()
		return df

def setup(bot):
	bot.add_cog(Tables(bot))