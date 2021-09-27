import asyncio
from datetime import datetime
from pytz import timezone
import discord
from discord.utils import get
import re

def get_streak_icon(icons):
    d = datetime.today().month
    return {10: icons[0], 12: icons[1]}.get(d, icons[-1]) # gives last icon as default


def format_db_date():
    now = datetime.now(timezone('Europe/Oslo'))
    return f'{now.year}.{now.month}.{now.day}'


def day_changed(conn):
    with conn:
        c = conn.cursor()
        c.execute('select last_date from date')
        return format_db_date() != c.fetchone()[0]

def update_day(conn):
    with conn:
        c = conn.cursor()
        c.execute('update date set last_date = ?', (format_db_date(),))
        conn.commit()


def get_current_streak(conn,userid,serverid):
    with conn:
        c = conn.cursor()
        c.execute(
            'select current_streak from users where (userid=? and serverid=?)', (userid, serverid))
        if f:=c.fetchone():
            return f[0]
        return None


def get_users(conn):
    with conn:
        c = conn.cursor()
        c.execute('select userid,serverid,joined_today,current_streak from users')
        return c.fetchall()


def user_exists(opts):
    conn,userid,serverid=opts
    with conn:
        c = conn.cursor()
        c.execute('select 1 from users where (userid=? and serverid=?)',
                  (userid, serverid))
        return bool(c.fetchone())


def user_add(opts):
    conn,userid,serverid=opts
    with conn:
        c = conn.cursor()
        c.execute('''
            insert into users
                (userid,
                serverid,
                joined_today,
                current_streak,
                total_streak,
                highest_streak,
                last_joined)
            values (?,?,?,?,?,?,?)''',
            (userid, serverid, 0, 0, 0, 0,datetime.now().ctime()))


def user_has_joined_today(opts):
    conn,userid,serverid=opts
    with conn:
        c = conn.cursor()
        c.execute(
            'select joined_today from users where (userid=? and serverid=?)', (userid, serverid))

        has_joined = c.fetchone()[0]
        return has_joined == 1


async def user_update_nickname(conn, bot, icons, member, serverid):
    nick=member.display_name
    current_icon = get_streak_icon(icons)
    current_streak = get_current_streak(conn, member.id, serverid)
    print(f"updating nickname of {nick}")

    if current_streak > 0:
        # checks if they has a nickname, and tries to match on icons
        # same as in reset_nickname
        s=f'^\d+({"|".join(icons)})'
        if (match:=re.compile(s).match(nick)):
            nick = ''.join(nick.split(match.group(1))[1:]).strip()
        nick = f'{current_streak}{current_icon} {nick}'
        print(f"finished updating nickname: {nick}")
        try:
            await member.edit(nick=nick)
        except discord.errors.Forbidden:
            print(f'FORBIDDEN: Change nickname of {member.display_name} in {member.guild.name}')


def user_update_last_joined(opts):
    conn,userid,serverid=opts
    with conn:
        c = conn.cursor()
        c.execute('update users set last_joined=? where (userid=? and serverid=?)',
                  (datetime.now().ctime(), userid, serverid))
        conn.commit()


async def update_user(bot,conn,*args):
    userid,serverid,joined_today,current_streak=args
    r=None
    g = await bot.fetch_guild(serverid)
    member = await g.fetch_member(userid)
    # dont reset if in voice, give streak instead
    # not working fuck discord.py
    if member.voice and member.voice.channel != None:
        print(f"{member.name} in voice, giving streak")
        give_streak((conn, userid, serverid))
    else:
        if joined_today == 0 and current_streak > 0:
            # set streak to 0 if user didn't join yesterday
            r=member
        with conn:
            c = conn.cursor()
            c.execute(
                'update users set joined_today=0 where (userid=? and serverid=?)',
                (userid, serverid))
    return r # return None or member to be reset

async def update_users(conn, bot):
    # asyncio batch job xd
    users=map(lambda x: update_user(bot,conn,*x),get_users(conn))
    reset_users=await asyncio.gather(*users)
    return filter(lambda x: x != None, reset_users)

async def reset_nickname(bot, conn, member, streak_icon):
    nick=member.display_name
    try:
        await member.edit(nick=''.join(nick.split(f'{streak_icon} '[1:])))
    except discord.errors.Forbidden:
        print(f'FORBIDDEN: Change nickname on {member.name} in {member.guild.name}')
    with conn:
        c = conn.cursor()
        c.execute(
            'update users set current_streak=0 where (userid=? and serverid=?)',
            (member.id, member.guild.id))
        conn.commit()

def give_streak(opts):
    conn, userid, serverid=opts
    with conn:
        c = conn.cursor()
        c.execute(
            '''select
                current_streak,
                total_streak,
                highest_streak
               from users
               where (userid=? and serverid=?)''', (userid, serverid))
        cur, tot, hi = c.fetchone()

        c.execute(
            '''update users set
                joined_today=1,
                current_streak=?,
                total_streak=?,
                highest_streak=?
               where (userid=? and serverid=?)''',
            (cur + 1, tot + 1, max(cur + 1, hi), userid, serverid))
        conn.commit()

def get_scores(conn, serverid):
    with conn:
        c=conn.cursor()
        c.execute('''
            select
                userid,
                current_streak,
                highest_streak,
                total_streak
            from users
            where serverid = ?
            order by total_streak desc
            ''',
            (serverid,))
        return c.fetchall()
