# If running on a new setup, install these using
#  pip install -U discord.py
#  pip install asyncio
#  pip install numpy pandas

# Set up roster.txt with the steamID64's of each team member (17 digit ID number), one per line. The bot will get logs/demos from the last 24 hours in which 4 or more team members show up, which allows for up to 2 ringers/subs.
# Also set up the bot token and channel IDs for your bot/server on lines 27 and 30

from __future__ import print_function

import discord
from discord.ext import commands

import asyncio

import os
import random

from datetime import date, datetime, timedelta
import urllib.request, json, re
import pandas as pd
import numpy as np

import urllib.parse

# Set up bot token for your Discord bot
botToken = os.environ['botToken']

# Set up the channel ID for the channel you want to post logs in
logChannelId = 852031278803058688

# The bot automatically checks for logs once a day. You can change the hour when this happens by changing the string below
# (based on 24 hour clock in your local time zone, set to a number 0-23)
logPostTime = '20'

def getLogs(numHours):
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

def getDemos(numHours):
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

bot = commands.Bot(command_prefix='!')

# !log
@bot.command(help = 'Gets most recent team logs from logs.tf')
async def log(ctx):
	msg = getLogs(24)
	channel = bot.get_channel(logChannelId) # Channel to post logs in
	if msg:
		msg = '**Most recent logs**:' + msg
		await channel.send(msg)
	else:
		await ctx.send('No recent team logs found')

# !demo
@bot.command(help = 'Gets most recent team demos from demos.tf')
async def demo(ctx):
	msg = getDemos(24)
	channel = bot.get_channel(logChannelId) # Channel to post logs in
	if msg:
		msg = '**Most recent demos**:' + msg
		await channel.send(msg)
	else:
		await ctx.send('No recent team demos found')

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

# Post scheduler
async def time_check():
	await bot.wait_until_ready()
	while True:
		now = datetime.strftime(datetime.now(), '%H')
		if now == logPostTime:
			channel = bot.get_channel(logChannelId) # Channel to post logs in
			msg1 = getLogs(24)
			if msg1:
				msg1 = '**Most recent logs**:' + msg1
				await channel.send(msg1)
			msg2 = getDemos(24)
			if msg2:
				msg2 = '**Most recent demos**:' + msg2
				await asyncio.sleep(5)
				await channel.send(msg2)
			await asyncio.sleep(3600)
		await asyncio.sleep(1800)

bot.loop.create_task(time_check())

bot.run(botToken)
