import discord
from datetime import datetime, timedelta
from discord.ext import commands
import asyncio
import util
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
from tabulate import tabulate

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

    async def update(self):
        # check if date has changed
        if util.day_changed(self.conn):
            users = await util.update_users(self.conn, self.bot)
            for user in users:
                util.reset_nickname(self.bot, self.conn, self.user,
                                    self.streak_icon)
        else:
            print('Day not changed')
        # add another job for next day
        self.subscribe_to_timeout()

    @commands.command()
    async def streak(self, ctx):
        message=ctx.message
        user=(next(iter(message.mentions or []), None)) or ctx.author
        if strk_count:=util.get_current_streak(self.conn, user.id, user.guild.id):
            strk_count=strk_count[0]
            await message.channel.send(f'Current streak for {user.mention} is {strk_count}')
        else:
            await message.channel.send('No streak for the weak.')

    @commands.command()
    async def scores(self, ctx):
        s=util.get_scores(self.conn, ctx.message.guild.id)
        if not s:
            return await ctx.send("No streaks bro")

        s.sort(key=lambda x: -x[-1])
        s=[(await self.bot.fetch_user(i[0]),i[1],i[2],i[3]) for i in s]

        msg=tabulate(s,headers=["User","Current","Highest","Total"])
        msg=f"```css\n{msg}```"
        await ctx.send(msg)



def setup(bot):
    bot.add_cog(Streak(bot))
