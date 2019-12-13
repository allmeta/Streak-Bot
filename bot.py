import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime

config = json.loads(open("config.json").read())
bot = commands.Bot(commands=".")
cogs = ['cogs.streak']


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(bot.command_prefix)
    print('------')
    for cog in cogs:
        bot.load_extension(cog)
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Game(name=".help"))


bot.run(config['token'])