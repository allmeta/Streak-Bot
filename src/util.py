from datetime import datetime
import discord
from discord.utils import get
import re

def get_streak_icon(icons):
    d = datetime.today().month
    return {10: icons[0], 12: icons[1]}.get(d, icons[-1])


def format_db_date():
    now = datetime.today()
    return f'{now.year}.{now.month}.{now.day}'


def day_changed(conn):
    with conn:
        c = conn.cursor()
        c.execute('select last_date from date')
        return format_db_date() == c.fetchone()


def get_current_streak(conn, userid, serverid):
    with conn:
        c = conn.cursor()
        c.execute(
            'select current_streak from users where (userid=? and serverid=?)', (userid, serverid))
        return c.fetchone()


def get_users(conn):
    with conn:
        c = conn.cursor()
        c.execute('select id,serverid,joined_today,current_streak from users')
        return c.fetchall()


def user_exists(conn, userid, serverid):
    with conn:
        c = conn.cursor()
        c.execute('select 1 from users where (userid=? and serverid=?)',
                  (userid, serverid))
        return bool(c.fetchone())


def user_add(conn, userid, serverid):
    with conn:
        c = conn.cursor()
        c.execute('insert into users (userid, serverid, joined_today, current_streak, total_streak, highest_streak, last_joined) values (?,?,?,?,?,?,?)',
                  (userid, serverid, 0, 0, 0, 0,datetime.now().ctime())
                  )


def user_has_joined_today(conn, userid, serverid):
    with conn:
        c = conn.cursor()
        c.execute(
            'select joined_today from users where (userid=? and serverid=?)', (userid, serverid))

        has_joined = c.fetchone()[0]
        return has_joined == 1


async def user_update_nickname(conn, bot, icons, member, serverid):
    nick=member.display_name
    current_icon = get_streak_icon(icons)
    current_streak = get_current_streak(conn, member.id, serverid)[0]

    if current_streak > 0:
        user = bot.get_user(member.id)
        # checks if they has a nickname, and tries to match on icons
        # same as in reset_nickname
        s=f'^\d+({"|".join(icons)})'
        if (match:=re.compile(s).match(nick)):
            nick = ''.join(nick.split(match.group(1))[1:])
        nick = f'{current_streak}{current_icon}{nick}'
        try:
            await member.edit(nick=nick)
        except discord.errors.Forbidden:
            print(
                'Change nickname of {user.display_name} in {user.server.name}')


def user_update_last_joined(conn, userid, serverid):
    with conn:
        c = conn.cursor()
        c.execute('update users set last_joined=? where (userid=? and serverid=?)',
                  (datetime.now().ctime(), userid, serverid))
        conn.commit()


def update_users(conn, bot):
    for (userid, serverid, joined_today, current_streak) in get_users(conn):
        user = bot.get_server(serverid).get_member(userid)
        # dont reset if in voice, give streak instead
        if user.voice.voice_channel:
            give_streak(conn, userid, serverid)
        else:
            with conn:
                c = conn.cursor()
                c.execute(
                    'update users set joined_today=0 where (userid=? and serverid=?)',
                    (userid, serverid))
        # set streak to 0 if user didn't join yesterday
        if joined_today == 0 and current_streak > 0:
            yield user  # yield list of users that should be reset

def reset_nickname(bot, conn, user, streak_icon):
    try:
        serverUser = get(bot.get_all_members(), id=user.userid)
        #serverUser = bot.get_user(user.userid)
        serverUser.edit(nick=''.join(user.nick.split(f'{streak_icon} '[1:])))
        #serverUser.nickname = ''.join(user.nick.split(f'{streak_icon} '[1:]))
        #await serverUser.edit(nick= ''.join(user.nick.split(f'{streak_icon} '[1:])))
    except:
        print(
            f'Change nickname on {user.name} in {user.server.name}')
    with conn:
        c = conn.cursor()
        c.execute(
            'update users set current_streak=0 where (userid=? and serverid=?)',
            (user.id, user.server.id))

def give_streak(conn, userid, serverid):
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
