from discord.ext import commands
import discord

import asyncio

import aiohttp
from lxml import html

import pycountry

ed = {"a":"🇦","b":"🇧","c":"🇨","d":"🇩","e":"🇪","f":"🇫","g":"🇬","h":"🇭","i":"🇮",
	  "j":"🇯","k":"🇰","l":"🇱","m":"🇲","n":"🇳","o":"🇴","p":"🇵","q":"🇶","r":"🇷",
	  "s":"🇸","t":"🇹","u":"🇺","v":"🇻","w":"🇼","x":"🇽","y":"🇾","z":"🇿"}
nd = {"0":"0⃣","1":"1⃣","2":"2⃣","3":"3⃣","4":"4⃣",
	  "5":"5⃣","6":"6⃣","7":"7⃣","8":"8⃣","9":"9⃣"}
cd = {"Wales":"gb","England":"gb","Scotland":"gb","Northern Ireland":"gb",
	  "Cote d'Ivoire":"ci","Venezuela":"ve","Macedonia":"mk","Kosovo":"xk",
	  "Faroe Island":"fo","Trinidad and Tobago":"tt","Congo DR":"cd",
	  "Moldova":"md","Korea, South":"kr","Korea, North":"kp", "Bolivia":"bo",
	  "Iran":"ir","Hongkong":"hk","Tahiti":"fp","Vietnam":"vn",
	  "Chinese Taipei (Taiwan)":"tw","Russia":"ru","N/A":"x",
	  "Cape Verde":"cv","American Virgin Islands":"vi",
	  "Turks- and Caicosinseln":"tc","Czech Republic":"cz","CSSR":"cz",
	  "Neukaledonien":"nc","St. Kitts &Nevis":"kn","Palästina":"ps",
	  "Osttimor":"tl","Bosnia-Herzegovina":"ba","Laos":"la","The Gambia":"gm",
	  "Botsuana":"bw","St. Louis":"lc","Tanzania":"tz",
	  "St. Vincent & Grenadinen":"vc","Cayman-Inseln":"ky",
	  "Antigua and Barbuda":"ag","British Virgin Islands":"vg",
	  "Mariana Islands":"mp","Sint Maarten":"sx",
	  "Federated States of Micronesia":"fm","Netherlands Antilles":"nl"}