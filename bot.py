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
with open("data.json") as f:
    data = json.loads(f.read())

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

client = commands.Bot(command_prefix='.')
scheduler = None


@client.command(pass_context=True)  # nani
async def recent(ctx):
    # !recent @member
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    member = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    c.execute("SELECT LASTJOINED FROM USERS WHERE ID = ?", (member.id,))

    await client.say("Last joined: {}".format(c.fetchone()[0]))
    conn.close()
    # write message data["servers"][]...


@client.command(pass_context=True)
async def top(ctx, *args):
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

    c.execute("SELECT ID, {} FROM USERS WHERE SERVERID = ?".format(leaderboard.upper()),
              (ctx.message.author.server.id,))
    x = c.fetchall()

    sortedUsers = [(k[0], k[1]) for k in x]
    sortedUsers.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="TOP {} STREAKS:".format(leaderboard.upper()),
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
        embed.add_field(name="#{}".format(
            eIndex+1), value=emotes[eIndex], inline=True)  # ❤❤❤❤❤❤
        embed.add_field(name="> {}".format(ctx.message.author.server.get_member(sortedUsers[i][0]).name),
                        value="{} 🔥".format(sortedUsers[i][1]), inline=True)

    embed.set_thumbnail(
        url='https://www.shareicon.net/download/2016/08/19/817655_podium_512x512.png')
    await client.say(embed=embed)
    conn.close()


@client.command(pass_context=True)
async def kreft(ctx):
    k = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    for i in range(5):
        await client.say("<@{}>".format(k.id))


@client.command(pass_context=True)
async def karl(ctx):
    for i in range(5):
        await client.say("<@{}>".format(ctx.message.author.server.get_member_named("KarlF#2868").id))


@client.command(pass_context=True)
async def peder(ctx):
    for i in range(5):
        await client.say("<@{}>".format(ctx.message.author.server.get_member_named("Plankiefy#0685").id))


@client.command(pass_context=True)
async def streak(ctx):
    user = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    if(not memberExists(user)):
        await addMember(user)
    await client.say("{} has {}🔥".format(user.name, getCurrentStreak(user.id)))


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


def getCurrentStreak(id):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT CURRENT FROM USERS WHERE ID = ?", (id,))
    d = c.fetchone()[0]
    conn.close()
    return d


async def updateStreaks():
    # check date
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT DATE FROM TODAY")
    if getTodayStr() != c.fetchone()[0]:
        for user in c.execute("SELECT ID, SERVERID, DAILY, CURRENT FROM USERS"):
            member = client.get_server(user[1]).get_member(user[0])
            if member.voice.voice_channel == None:
                c.execute(
                    "UPDATE USERS SET DAILY = 0 WHERE ID = ?", (user[0],))
            else:
                giveStreak(member)

            if user[2] == 0 and user[3] > 0:
                c.execute(
                    "UPDATE USERS SET CURRENT = 0 WHERE ID = ?", (user[0],))
                try:
                    await client.change_nickname(
                        member, ''.join(member.nick.split('🔥 ')[1:]))
                    print("RESET STREAK: %s" % (member.name))
                except discord.errors.Forbidden:
                    print('RESET STREAK FORBIDDEN: nickname of {} in {}'.format(
                        member.name, member.server.name))
            else:
                await changeNickname(user[3], server, user)

        c.execute("UPDATE TODAY SET DATE = ?", (getTodayStr(),))
        conn.commit()
        conn.close()
    # resub for next day
    if(scheduler):
        scheduler.add_job(updateStreaks, 'date',
                          run_date=date(i.year, i.month, i.day+1))
    else:
        await subscribeToTimeout()


async def changeNickname(serverid, userid):
    strk = getCurrentStreak(userid)
    if strk > 0:
        try:
            userobj = client.get_server(serverid).get_member(userid)
            nick = userobj.nick
            if nick and '🔥 ' in nick:
                nick = ''.join(userobj.nick.split('🔥 ')[1:])
            if not nick:
                nick = userobj.name
            else:
                await client.change_nickname(
                    userobj, "{}🔥 {}".format(strk, nick))
        except discord.errors.Forbidden:
            print('FORBIDDEN: nickname of {} in {}'.format(
                userobj.name, userobj.server.name))


async def subscribeToTimeout():
    # timer to update streaks
    i = datetime.now()
    scheduler = AsyncIOScheduler()
    scheduler.start()
    # scheduler.add_job(updateStreaks, 'interval', seconds=10)
    scheduler.add_job(updateStreaks, 'date',
                      run_date=date(i.year, i.month, i.day+1))


def getTodayStr():
    i = datetime.now()
    return "%s/%s/%s" % (i.day, i.month, i.year)


def updateLastJoined(member):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("UPDATE USERS SET LASTJOINED = ? WHERE ID = ?",
              (datetime.now().ctime(), member.id,))
    conn.commit()
    conn.close()


def memberExists(member):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM USERS WHERE ID = ?", (member.id,))
    d = c.fetchone()
    conn.close()
    return True if d != None else False


async def addMember(member):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("INSERT INTO USERS VALUES (?,?,?,?,?,?,?)",
              (member.id, member.server.id, datetime.now().ctime(), 0, 0, 0, 0,))
    conn.commit()
    conn.close()
# if done daily


def hasDaily(member):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute('SELECT DAILY FROM USERS WHERE ID = ?', (member.id,))
    d = c.fetchone()[0]
    conn.close()
    return d == 1


def giveStreak(member):
    conn = sqlite3.connect("streakbot.db")
    c = conn.cursor()
    c.execute("SELECT CURRENT, TOTAL, HIGHEST FROM USERS WHERE ID = ?",
              (member.id,))
    cur, tot, hi = c.fetchone()
    c.execute("UPDATE USERS SET DAILY = 1, CURRENT = ?, TOTAL = ?, Highest = ? WHERE ID = ?",
              (cur+1, tot+1, max(cur, hi), member.id,))
    conn.commit()
    conn.close()


client.run(config['token'])
