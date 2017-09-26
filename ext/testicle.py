from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

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

table = "http://www.flashscore.com/soccer/england/premier-league/"
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
print(size)