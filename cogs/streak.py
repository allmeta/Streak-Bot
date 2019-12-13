import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
import util
import debug


class Streak(commands.cfg):
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

    def connect(self):
        return sqlite3.connect(self.db)

    async def subscribe_to_timeout(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.scheduler.start()
        self.scheduler.add_job(self.update,
                               'date',
                               run_date=datetime.date(tomorrow.year,
                                                      tomorrow.month,
                                                      tomorrow.day))

    async def update(self):
        # check if date has changed
        if util.day_changed(self.conn):
            users = util.update_users(self.conn, self.bot)
            for user in users:
                util.reset_nickname(self.bot, self.conn, self.user,
                                    self.streak_icon)
        else:
            debug.info('Day not changed')
        # add another job for next day
        self.subscribe_to_timeout()

    # events
    @client.event
    async def on_voice_state_update(before, after):
        if bool(before.voice.voice_channel) != bool(after.voice.voice_channel):
            if not util.user_exists(self.conn, after.id, after.server.id):
                util.add_user(self.conn, after.id, after.server.id)
            if not util.has_joined_today(self.conn, after.id, after.server.id):
                util.give_streak(self.conn, after.id, after.server.id)
            util.user_update_nickname(self.conn, self.bot, self.icons,
                                      after.id, after.server.id)
            util.user_update_last_joined(self.conn, after.id, after.server.id)
