# If running on a new setup, install these using
#  pip install -U discord.py
#  pip install asyncio
#  pip install numpy

# Set up a file called roster.txt with the steamID64's of each team member (17 digit ID number), one per line.
# The bot will get logs/demos from the last 24 hours in which 4 or more team members show up, which allows for up to 2 ringers/subs.
# Also set up the bot token and channel IDs for your bot/server on lines 22 and 25

from __future__ import print_function

import discord
from discord.ext import tasks, commands

import asyncio

from datetime import date, datetime, timedelta
import urllib.request, json
import numpy as np

# Set up bot token for your Discord bot
botToken = '[put bot token here]'

# Set up the channel ID for the channel you want to post logs in
logChannelId = 852031278803058688

# The bot automatically checks for logs once a day. You can schedule when this happens by changing the string below
# (based on 24 hour clock in your local time zone)
logPostTime = '20:30'

# You can set a custom prefix for commands here
bot = commands.Bot(command_prefix="!")

class Logs(commands.Cog):
	# for posting logs and demos

	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.auto_logs.start()

	def getLogs(self, numHours):
		listFile = open('roster.txt','r')
		idList = np.array([])
		logMsg = ''

		cutoffTime = date.today() - timedelta(hours=numHours)
		cutoffTime = cutoffTime.strftime('%s')

		for eachline in listFile:
			playerLogUrl = 'https://logs.tf/api/v1/log?player=' + eachline.strip('\n') + '&limit=15'
			url = urllib.request.urlopen(playerLogUrl)
			obj = json.load(url)
			logsList = obj['logs']

			for i in logsList:
				if i['players'] >= 12 and i['date'] > int(cutoffTime):
					logid = str(i['id']) + '-' + i['map']
					idList = np.append(idList, logid)

		for id in idList:
			if np.count_nonzero(idList == id) < 4:
				idList = idList[idList != id]

		idList = np.unique(idList)
		idList[::-1].sort()

		for item in idList:
			logid = item.split('-')[0]
			logMap = item.split('-')[1]
			logUrl = logMap + ' - https://logs.tf/' + logid
			logMsg = logMsg + '\n' + logUrl

		return logMsg

	def getDemos(self, numHours):
		listFile = open('roster.txt','r')
		idList = np.array([])
		logMsg = ''

		cutoffTime = date.today() - timedelta(hours=numHours)
		cutoffTime = cutoffTime.strftime('%s')

		for eachline in listFile:
			playerLogUrl = 'https://api.demos.tf/profiles/' + eachline.strip('\n') + '?after=' + str(int(cutoffTime))
			url = urllib.request.urlopen(playerLogUrl)
			obj = json.load(url)

			for i in obj:
				if i['playerCount'] >= 12:
					logid = str(i['id']) + '-' + i['map']
					idList = np.append(idList, logid)

		for id in idList:
			if np.count_nonzero(idList == id) < 4:
				idList = idList[idList != id]

		idList = np.unique(idList)
		idList[::-1].sort()

		for item in idList:
			logid = item.split('-')[0]
			logMap = item.split('-')[1]
			logUrl = logMap + ' - https://demos.tf/' + logid
			logMsg = logMsg + '\n' + logUrl

		return logMsg

	@commands.command(name='log', help='Gets most recent team logs from logs.tf')
	async def log(self, ctx: commands.Context):
		msg = self.getLogs(24)
		channel = self.bot.get_channel(logChannelId) # Channel to post logs in
		if msg:
			msg = '**Most recent logs**:' + msg
			await channel.send(msg)
		else:
			await ctx.send('No recent team logs found')

	@commands.command(name='demo', help='Gets most recent team demos from demos.tf')
	async def demo(self, ctx: commands.Context):
		msg = self.getDemos(24)
		channel = self.bot.get_channel(logChannelId) # Channel to post logs in
		if msg:
			msg = '**Most recent demos**:' + msg
			await channel.send(msg)
		else:
			await ctx.send('No recent team demos found')

	@tasks.loop(minutes=1440)
	async def auto_logs(self):
		now = datetime.strftime(datetime.now(), '%H:%M')
		postTime = datetime.strptime(logPostTime, '%H:%M')
		waitTime = (postTime - datetime.strptime(now, '%H:%M')).seconds
		await asyncio.sleep(waitTime)

		channel = self.bot.get_channel(logChannelId) # Channel to post logs in
		msg1 = self.getLogs(12)
		if msg1:
			msg1 = '**Most recent logs**:' + msg1
			await channel.send(msg1)
		msg2 = self.getDemos(12)
		if msg2:
			msg2 = '**Most recent demos**:' + msg2
			await channel.send(msg2)

	@auto_logs.before_loop
	async def before_auto_logs(self):
		await self.bot.wait_until_ready()

bot.add_cog(Logs(bot))

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

bot.run(botToken)