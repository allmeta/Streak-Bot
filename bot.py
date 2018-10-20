import discord
from discord.ext import commands
import asyncio
import json
import io
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3

with open("config.json") as f:
    config = json.loads(f.read())

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

client = commands.Bot(command_prefix='.')
scheduler = None
conn = None


@client.command(pass_context=True)  # nani
async def recent(ctx):
    # !recent @member
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    member = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    c.execute("SELECT LASTJOINED FROM USERS WHERE (ID = ? AND SERVERID = ?)",
              (member.id, member.server.id,))

    await client.say(f"Last joined: {c.fetchone()[0]}")
    if g:
        conn.close()
        conn = None
    # write message data["servers"][]...


@client.command(pass_context=True)
async def top(ctx, *args):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()

    lval = ["total", "highest"]
    leaderboard = "current"

    if args:
        if args[0] in lval:
            leaderboard = args[0]
        else:
            await client.say("Usage: `!top --[total | highest]`")
            return

    c.execute(f"SELECT ID, {leaderboard.upper()} FROM USERS WHERE SERVERID = ?",
              (ctx.message.author.server.id,))
    x = c.fetchall()

    sortedUsers = [(k[0], k[1]) for k in x]
    sortedUsers.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title=f"TOP {leaderboard.upper()} STREAKS:",
        colour=discord.Colour.gold()
    )
    embed.set_footer(text="Spaghetti code by All Meta@2540 and Qwikk@2929")
    embed.set_author(name="Streak Bot", icon_url=client.user.avatar_url)
    emotes = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    eIndex = 0
    for i in range(min(len(sortedUsers), 5)):
        if sortedUsers[i][1] != sortedUsers[max(
                0, i-1)][1]:
            eIndex += 1
        embed.add_field(name=f"#{eIndex+1}",
                        value=emotes[eIndex], inline=True)
        embed.add_field(name=f"> {ctx.message.author.server.get_member(sortedUsers[i][0]).name}",
                        value=f"{sortedUsers[i][1]} 🔥", inline=True)

    embed.set_thumbnail(
        url='https://www.shareicon.net/download/2016/08/19/817655_podium_512x512.png')
    await client.say(embed=embed)
    if g:
        conn.close()
        conn = None


@client.command(pass_context=True)
async def streak(ctx, *args):
    # it works so wont check for conn == None etc
    lval = ["TOTAL", "HIGHEST"]
    which = args[0] if args and args[0].upper() in lval else "CURRENT"
    user = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    if(not memberExists(user)):
        await addMember(user)
    await client.say("{} has {}🔥".format(user.name, getInfoStreak(user.id, user.server.id, which)))


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name, client.user.id)
    await updateStreaks()
    return await client.change_presence(game=discord.Game(name='.help'))


@client.event
async def on_voice_state_update(before, after):
    b, a = before.voice.voice_channel, after.voice.voice_channel
    if (not b and a or b and not a):

        if(not memberExists(after)):
            await addMember(after)

        updateLastJoined(after)

        if not hasDaily(after):
            giveStreak(after)

        await changeNickname(after.server.id,
                             after.id)


@client.event
async def on_member_update(before, after):
    b, a = before.nick, after.nick
    if(b != a and memberExists(after)):
        await changeNickname(after.server.id, after.id)


def getCurrentStreak(id, serverid):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT CURRENT FROM USERS WHERE (ID = ? AND SERVERID = ?)",
              (id, serverid,))
    d = c.fetchone()[0]
    if g:
        conn.close()
        conn = None
    return d


def getInfoStreak(id, serverid, which):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute(f"SELECT {which.upper()} FROM USERS WHERE (ID = ? AND SERVERID = ?)",
              (id, serverid,))
    d = c.fetchone()[0]
    if g:
        conn.close()
        conn = None
    return d


async def updateStreaks():
    # check date
    global conn, scheduler
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT DATE FROM TODAY")
    if getTodayStr() != c.fetchone()[0]:
        print("Day changed, updating streaks!")
        c.execute("SELECT ID, SERVERID, DAILY, CURRENT FROM USERS")
        users = c.fetchall()
        for user in users:
            member = client.get_server(user[1]).get_member(user[0])
            if member != None:
                if member.voice.voice_channel == None:
                    c.execute(
                        "UPDATE USERS SET DAILY = 0 WHERE (ID = ? AND SERVERID = ?)", (user[0], user[1],))
                else:
                    giveStreak(member)

                if user[2] == 0 and user[3] > 0:
                    c.execute(
                        "UPDATE USERS SET CURRENT = 0 WHERE (ID = ? AND SERVERID = ?)", (user[0], user[1],))
                    try:
                        await client.change_nickname(
                            member, ''.join(member.nick.split('🔥 ')[1:]))
                        print(f"RESET STREAK: {member.name}")
                    except discord.errors.Forbidden:
                        print(
                            f'RESET STREAK FORBIDDEN: nickname of {member.name} in {member.server.name}')
                else:
                    await changeNickname(user[1], user[0])
            else:
                print(user[0], user[1])
                c.execute(
                    "DELETE FROM USERS WHERE (ID = ? AND SERVERID = ?)", (user[0], user[1],))

        c.execute("UPDATE TODAY SET DATE = ?", (getTodayStr(),))
        conn.commit()
        conn.close()
        conn = None
    else:
        print("Day hasn't changed")
    # resub for next day
    if(scheduler != None):
        i = datetime.now()
        print(f"New job executes in {24-i.hour} hours")
        scheduler.add_job(updateStreaks, 'date',
                          run_date=date(i.year, i.month, i.day+1))
    else:
        await subscribeToTimeout()


async def changeNickname(serverid, userid):
    strk = getCurrentStreak(userid, serverid)
    if strk > 0:
        try:
            userobj = client.get_server(serverid).get_member(userid)
            nick = userobj.nick
            if nick != None and '🔥 ' in nick:
                nick = ''.join(userobj.nick.split('🔥 ')[1:])
            elif nick == None:
                nick = userobj.name
            try:
                await client.change_nickname(
                    userobj, f"{strk}🔥 {nick}")
            except discord.errors.HTTPException as e:
                print(
                    f"{e} when setting nickname of {userobj.name} to {strk}🔥 {nick}")
        except discord.errors.Forbidden:
            print(
                f'FORBIDDEN: nickname of {userobj.name} in {userobj.server.name}')


async def subscribeToTimeout():
    global scheduler
    # timer to update streaks
    i = datetime.now()
    scheduler = AsyncIOScheduler()
    scheduler.start()
    # scheduler.add_job(updateStreaks, 'interval', seconds=10)
    print(f"New job executes in {24-i.hour} hours")
    scheduler.add_job(updateStreaks, 'date',
                      run_date=date(i.year, i.month, i.day+1))


def getTodayStr():
    i = datetime.now()
    return "%s/%s/%s" % (i.day, i.month, i.year)


def updateLastJoined(member):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("UPDATE USERS SET LASTJOINED = ? WHERE (ID = ? AND SERVERID = ?)",
              (datetime.now().ctime(), member.id, member.server.id,))
    conn.commit()
    if g:
        conn.close()
        conn = None


def memberExists(member):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM USERS WHERE (ID = ? AND SERVERID = ?)",
              (member.id, member.server.id,))
    d = c.fetchone()
    if g:
        conn.close()
        conn = None
    return True if d != None else False


async def addMember(member):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("INSERT INTO USERS VALUES (?,?,?,?,?,?,?)",
              (member.id, member.server.id, datetime.now().ctime(), 0, 0, 0, 0,))
    conn.commit()
    if g:
        conn.close()
        conn = None
# if done daily


def hasDaily(member):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute('SELECT DAILY FROM USERS WHERE (ID = ? AND SERVERID = ?)',
              (member.id, member.server.id,))
    d = c.fetchone()[0]
    if g:
        conn.close()
        conn = None
    return d == 1


def giveStreak(member):
    global conn
    g = True if conn == None else False
    if g:
        conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT CURRENT, TOTAL, HIGHEST FROM USERS WHERE (ID = ? AND SERVERID = ?)",
              (member.id, member.server.id,))
    cur, tot, hi = c.fetchone()
    c.execute("UPDATE USERS SET DAILY = 1, CURRENT = ?, TOTAL = ?, Highest = ? WHERE (ID = ? AND SERVERID = ?)",
              (cur+1, tot+1, max(cur+1, hi), member.id, member.server.id,))
    conn.commit()
    if g:
        conn.close()
        conn = None


client.run(config['token'])
