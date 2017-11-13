from discord.ext import commands
from peony import PeonyClient
from datetime import datetime
import discord
import asyncio
import json
from lxml import html
import html as htmlc
import traceback
					
class Twitter:
	""" Twitter stream commands """
	def __init__(self, bot):
		self.bot = bot
		self.tweetson = True
		with open("twitter.json") as f:
			self.track = json.load(f)
		self.pclient = PeonyClient(**self.bot.credentials['Twitter'])
		self.bot.twitask = self.bot.loop.create_task(self.twat())
	
	def __unload(self):
		self.tweetson = False
		self.bot.twitask.cancel()

	async def _save(self):
		with await self.bot.configlock:
			with open('twitter.json',"w",encoding='utf-8') as f:
				json.dump(self.track,f,ensure_ascii=True,
				sort_keys=True,indent=4, separators=(',',':'))
	
		
	async def twat(self):
		""" Twitter tracker function """
		await self.bot.wait_until_ready()
		
		# Retrieve list of IDs to track
		ids = ",".join([str(i[1]["id"]) for i in self.track.items()])
		
		footericon = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
		ts = self.pclient.stream.statuses.filter.post(follow=ids)
		
		async with ts as stream:
			print(f"Tracking {len(self.track.items())} twitter users.")
			async for t in stream:
				# Break loop if bot not running.
				if self.bot.is_closed():
					break
					
				# if tweet output is disabled, break the loop.
				if not self.tweetson:
					break
				
				# discard malformed tweets	
				if not hasattr(t,"user"):
					continue 
				
				# Set destination or discard non-tracked
				u = t.user
				if u.id_str in ids:
					s = self.track.items()
					chanid = [i[1]["channel"] for i in s if i[1]["id"] == int(u.id_str)][0]
					destin = self.bot.get_channel(chanid)
				else:
					continue
				
				# discard retweets & adverts		
				if hasattr(t,'retweeted_status') or t.text.startswith(("rt",'ad')):
					continue
				
				# discard replies
				if t["in_reply_to_status_id"] is not None:
					continue 
				
				if t.truncated:
					txt = htmlc.unescape(t.extended_tweet.full_text)
					ents = dict(t.entities)
					ents.update(dict(t.extended_tweet.entities))
				else:
					ents = t.entities
					txt = htmlc.unescape(t.text)
				
				if "coral" in txt:
					continue
				
				if "hashtags" in ents:
					for i in ents["hashtags"]:
						frnt = f"[#{i.text}]"
						bk = f"(https://twitter.com/hashtag/{i.text})"
						rpl = frnt + bk
						txt = txt.replace(f'#{i.text}',rpl)
				if "urls" in ents:
					for i in ents["urls"]:
						txt = txt.replace(i.url,i.expanded_url)
				if "user_mentions" in ents:
					for i in ents["user_mentions"]:
						frnt = f"[@{i.screen_name}]"
						bk = f"(https://twitter.com/{i.screen_name})"
						rpl = frnt+bk
						txt = txt.replace(f'@{i.screen_name}',rpl)
				
				e = discord.Embed(description=txt)
				if hasattr(u,"url"):
					e.url = u.url
				if hasattr(u,"profile_link_color"):
					e.color = int(u.profile_link_color,16)
				
				e.set_thumbnail(url=u.profile_image_url)
				e.timestamp = datetime.strptime(t.created_at,"%a %b %d %H:%M:%S %z %Y")
				e.set_footer(icon_url=footericon,text="Twitter")
				
				lk = f"http://www.twitter.com/{u.screen_name}/status/{t.id_str}"
				e.title = f"{u.name} (@{u.screen_name})"
				e.url = lk

				# Extract entities to lists
				photos = []
				videos = []
				
				def extract_entities(alist):
					for i in alist:
						if i.type in ["photo","animated_gif"]:
							photos.append(i.media_url)
						elif i.type == "video":
							videos.append(i.video_info.variants[1].url)
						else:
							print("Unrecognised TWITTER MEDIA TYPE")
							print(i)
							
				# Fuck this nesting kthx.
				if hasattr(t,"extended_entities") and hasattr (t.extended_entities,"media"):
					extract_entities(t.extended_entities.media)
				if hasattr(t,"quoted_status"):
					if hasattr(t.quoted_status,"extended_entities"):
						if hasattr(t.quoted_status.extended_entities,"media"):
							extract_entities(t.quoted_status.extended_entities.media)
					
				# Set image if one image, else add embed field.
				if len(photos) == 1:
					e.set_image(url=photos[0])
				elif len(photos) > 1:
					en = enumerate(photos,start=1)
					v = ", ".join([f"[{i}]({j})" for i, j in en])
					e.add_field(name="Attached Photos",value=v,inline=True)
				
				# Add embed field for videos
				if videos:
					if len(videos) > 1:
						en = enumerate(videos,start=1)
						v = ", ".join([f"[{i}]({j})" for i, j in en])
						e.add_field(name="Attached Videos",value=v,inline=True)
					else:
						await destin.send(embed=e)
						await destin.send(videos[0])
				else:
					await destin.send(embed=e)

	@commands.group(aliases=["tweet","tweets","checkdelay","twstatus"],invoke_without_command=True)
	@commands.is_owner()
	async def twitter(self,ctx):
		""" Check delay and status of twitter tracker """
		e = discord.Embed(title="Twitter Status",color=0x7EB3CD)
		e.set_thumbnail(url="https://i.imgur.com/jSEtorp.png")
		if self.tweetson:
			e.description = "```diff\n+ ENABLED```"
		else:
			e.description = "```diff\n- DISABLED```"
			e.color = 0xff0000
			footer = "Tweets are not currently being output."
		e.set_footer(text=footer)
		for i in set([i[1]["channel"] for i in self.track.items()]):
			# Get Channel name from ID in JSON
			fname = f"#{self.bot.get_channel(int(i)).name} Tracker"
			# Find all tracks for this channel.
			fvalue = "\n".join([c[0] for c in self.track.items() if c[1]["channel"] == i])
			e.add_field(name=fname,value=fvalue)
		
		if self.bot.is_owner(ctx.author):
			x =  self.bot.twitask._state
			if x == "PENDING":
				v = "✅ Task running."
			elif x == "CANCELLED":
				v = "⚠ Task Cancelled."
			elif x == "FINISHED":
				self.bot.twitask.print_stack()
				v = "⁉ Task Finished"
				z = self.bot.twitask.exception()
			else:
				v = f"❔ `{self.bot.twitask._state}`"
			e.add_field(name="Debug Info",value=v,inline=False)
			try:
				e.add_field(name="Exception",value=z,inline=False)
			except NameError:
				pass
		await ctx.send(embed=e)
	
	@twitter.command(name="on",aliases=["start"])
	@commands.is_owner()
	async def _on(self,ctx):
		""" Turn tweet output on """
		if not self.tweetson:
			self.tweetson = True
			await ctx.send("<:tweet:332196044769198093> Twitter output has been enabled.")
			self.bot.twitask = self.bot.loop.create_task(self.twat())
		elif self.bot.twitask._state in ["FINISHED","CANCELLED"]:
			e = discord.Embed(color=0x7EB3CD)
			e.description = f"<:tweet:332196044769198093> Restarting {self.bot.twitask._state}\
							task after exception {self.bot.twitask.exception()}."
			await ctx.send(embed=e)
			self.bot.twitask = self.bot.loop.create_task(self.twat())
		else:
			await ctx.send("<:tweet:332196044769198093> Twitter output already enabled.")
		
	@twitter.command(name="off",aliases=["stop"])
	@commands.is_owner()
	async def _off(self,ctx):
		""" Turn tweet output off """
		if self.tweetson:
			self.tweetson = False
			await ctx.send("<:tweet:332196044769198093> Twitter output has been disabled.")
		else:
			await ctx.send("<:tweet:332196044769198093> Twitter output already disabled.")
		
	@twitter.command(name="add")
	@commands.is_owner()
	async def _add(self,ctx,username):
		""" Add user to track for this channel """
		params = {"user_name":username,"submit":"GET+USER+ID"}
		async with self.bot.session.get("http://gettwitterid.com/",params=params) as resp:
			if resp.status != 200:
				await ctx.send("🚫 HTTP Error {resp.status} try again later.")
				return
			tree = html.fromstring(await resp.text())
			try:
				id = tree.xpath('.//tr[1]/td[2]/p/text()')[0]
			except IndexError:
				await ctx.send("🚫 Couldn't find user with that name.")
		self.track[username] = {"id":int(id),"channel":ctx.channel.id}
		await self._save()
		await ctx.send(f"<:tweet:332196044769198093> {username} will be tracked in {ctx.channel.mention} from next restart.")
		
	@twitter.command(name="del")
	@commands.is_owner()
	async def _del(self,ctx,username):
		""" Deletes a user from the twitter tracker """
		trk = [{k.lower():k} for k in self.track.keys()]
		if username.lower() in trk:
			self.track.pop(trk[username.lower()])
			await self._save()
		
def setup(bot):	
	bot.add_cog(Twitter(bot))
