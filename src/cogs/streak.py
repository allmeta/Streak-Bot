import discord
from datetime import datetime, timedelta
from pytz import timezone,utc
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
        self.timezone=timezone('Europe/Oslo')
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.update())


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        c=after.channel or before.channel
        opts=(self.conn, member.id, c.guild.id)
        if not before.channel and after.channel: # when joining a channel, not switching
            if not util.user_exists(opts):
                util.user_add(opts)
            if not util.user_has_joined_today(opts):
                util.give_streak(opts)
            await util.user_update_nickname(self.conn, self.bot, self.icons, member, c.guild.id)
            util.user_update_last_joined(opts)

    def connect(self):
        return sqlite3.connect(self.db)

    def subscribe_to_timeout(self):
        tomorrow = datetime.now(self.timezone) + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0,minute=0,second=0,microsecond=0).astimezone(utc)
        if self.scheduler.state != 1:
            self.scheduler.start()
            self.scheduler.add_job(self.update, 'date', run_date=tomorrow)

    async def update(self):
        # check if date has changed
        if util.day_changed(self.conn):
            print('---- Day changed - updating users ----')
            reset_users = await util.update_users(self.conn, self.bot)
            for member in reset_users:
                await util.reset_nickname(self.bot, self.conn, member, self.streak_icon)
            util.update_day(self.conn)
            print('---- finished updating users ----')
        else:
            print('---- Day not changed ----')
        # add another job for next day
        self.subscribe_to_timeout()

    @commands.command()
    async def streak(self, ctx):
        message=ctx.message
        user=(next(iter(message.mentions or []), None)) or ctx.author
        if strk_count:=util.get_current_streak(self.conn, user.id, user.guild.id):
            await ctx.send(f'Current streak for {user.mention} is {strk_count}')
        else:
            await ctx.send('No streak for the weak 😎')

    @commands.command()
    async def scores(self, ctx):
        s=util.get_scores(self.conn, ctx.message.guild.id)
        if not s:
            return await ctx.send("No streaks in the server bro 😩")
        u=await asyncio.gather(*[self.bot.fetch_user(x[0]) for x in s])
        s=[(x,*y[1:]) for x,y in zip(u,s)]


        msg=tabulate(s,headers=["User","Current","Highest","Total"])
        msg=f"```css\n{msg}```"
        await ctx.send(msg)

    @commands.command()
    async def next(self, ctx):
        if n:=self.scheduler.get_jobs()[0].next_run_time:
            return await ctx.send(str(n-datetime.now(self.timezone)))
        await ctx.send("Shit dette funka bad as 😩")



def setup(bot):
    bot.add_cog(Streak(bot))
