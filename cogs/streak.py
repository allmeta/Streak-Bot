import discord
from datetime import datetime, timedelta
from discord.ext import commands
import asyncio
import util
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3

client = discord.Client()

class Streak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = None
        self.icons = ['🎃', '⛄', '🔥']
        self.streak_icon = util.get_streak_icon(self.icons)
        self.db = 'streakbot.db'
        self.conn = self.connect()
        self.scheduler = AsyncIOScheduler()

        self.subscribe_to_timeout()
        self.update()
        

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not before.channel and after.channel:
            if not util.user_exists(self.conn, member.id, after.channel.guild.id):
                util.user_add(self.conn, member.id, after.channel.guild.id)
            if not util.user_has_joined_today(self.conn, member.id, after.channel.guild.id):
                util.give_streak(self.conn, member.id, after.channel.guild.id)
            await util.user_update_nickname(self.conn, self.bot, self.icons,
                                      member, after.channel.guild.id)
            util.user_update_last_joined(self.conn, member.id, after.channel.guild.id)

    def connect(self):
        return sqlite3.connect(self.db)

    def subscribe_to_timeout(self):
        tomorrow = datetime.today() + timedelta(days=1)
        if self.scheduler.state != 1:
            self.scheduler.start()
            self.scheduler.add_job(self.update,
                                'date',
                                run_date=datetime.date(tomorrow))

    def update(self):
        # check if date has changed
        if util.day_changed(self.conn):
            users = util.update_users(self.conn, self.bot)
            for user in users:
                util.reset_nickname(self.bot, self.conn, self.user,
                                    self.streak_icon)
        else:
            print('Day not changed')
        # add another job for next day
        self.subscribe_to_timeout()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith('.streak'):
            if util.get_current_streak(self.conn, message.author.id, message.author.guild.id):
                await message.channel.send('Current streak for ' + message.author.nick + ' is ' + str(util.get_current_streak(self.conn, message.author.id, message.author.guild.id)[0]))
            else:
                await message.channel.send('No streak for the weak.')
            await message.delete()

    

def setup(bot):
    bot.add_cog(Streak(bot))
