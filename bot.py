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
conn = sqlite3.connect("streakbot.db")
c = conn.cursor()


@client.command(pass_context=True)  # nani
async def recent(ctx):
    # !recent @member
    member = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    t = data["servers"][member.server.id]["streaks"][member.id]["lastJoined"]
    # t = t.replace('T', ' ')[:-7]

    await client.say("Last joined: {}".format(t))
    # write message data["servers"][]...

lval = ["total", "highest"]


@client.command(pass_context=True)
async def top(ctx, *args):
    ###
    leaderboard = "current"
    if args:
        if args[0] in lval:
            leaderboard = args[0]
        else:
            await client.say("`!top --[total | highest]`")
            return

    x = data["servers"][ctx.message.author.server.id]["streaks"]

    sortedUsers = [(k, x[k]) for k in x]
    sortedUsers.sort(key=lambda x: x[1][leaderboard], reverse=True)

    embed = discord.Embed(
        title="TOP {} STREAKS:".format(str.upper(leaderboard)),
        colour=discord.Colour.gold()
    )
    embed.set_footer(text="All Meta@2540 and Qwikk@2929")
    embed.set_author(name="Streak Bot", icon_url=client.user.avatar_url)
    emotes = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    eIndex = 0
    for i in range(min(len(sortedUsers), 5)):
        if sortedUsers[i][1][leaderboard] != sortedUsers[max(
                0, i-1)][1][leaderboard]:
            eIndex += 1
        embed.add_field(name="#{}".format(
            eIndex+1), value=emotes[eIndex], inline=True)  # ❤❤❤❤❤❤
        embed.add_field(name="> {}".format(ctx.message.author.server.get_member(sortedUsers[i][0]).name),
                        value="\t{} 🔥".format(sortedUsers[i][1][leaderboard]), inline=True)

    embed.set_thumbnail(
        url='https://www.shareicon.net/download/2016/08/19/817655_podium_512x512.png')
    await client.say(embed=embed)


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

    s = ctx.message.author.server
    user = ctx.message.mentions[0] if ctx.message.mentions else ctx.message.author
    if(not memberExists(user)):
        await addMember(user)
    await client.say("{} has {}🔥".format(user.name, data["servers"][s.id]["streaks"][user.id]["current"]))


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name, client.user.id)
    await updateStreaks()
    return await client.change_presence(game=discord.Game(name='.help'))


@client.event
async def on_voice_state_update(before, after):
    b, a = before.voice.voice_channel, after.voice.voice_channel
    # can come from another server
    if (not b and a or b and not a):
            # update last joined voice
        if(not serverExists(after.server)):
            addServer(after.server)
        if(not memberExists(after)):
            await addMember(after)
        updateLastJoined(after)
        if not hasDaily(after):
            # add streak
            giveStreak(after)

        await changeNickname(data["servers"][after.server.id]["streaks"][after.id]["current"],
                             after.server.id,
                             after.id)


@client.event
async def on_member_update(before, after):
    b, a = before.nick, after.nick
    if(b != a and memberExists(after)):
        strk = data["servers"][
            after.server.id]["streaks"][after.id]["current"]
        await changeNickname(strk, after.server.id, after.id)


async def updateStreaks():
    # check date
    if getTodayStr() != data["today"]:
        # go through everyone in every server and update streaks
        servers = data["servers"]
        for server, sval in servers.items():
            for user, userval in sval["streaks"].items():

                member = client.get_server(server).get_member(user)
                if not inVoice(member):
                    data["servers"][server]["streaks"][user]["daily"] = False
                else:
                    giveStreak(member)

                if userval["daily"] is False and userval["current"] > 0:
                    data["servers"][server]["streaks"][user]["current"] = 0
                    try:
                        await client.change_nickname(
                            member, ''.join(member.nick.split('🔥 ')[1:]))
                        print("RESET STREAK: %s" % (member.name))
                    except discord.errors.Forbidden:
                        print('RESET STREAK FORBIDDEN: nickname of {} in {}'.format(
                            member.name, member.server.name))
                else:
                    await changeNickname(data["servers"][server]["streaks"][user]["current"], server, user)

        data["today"] = getTodayStr()
    # resub for next day
    if(scheduler):
        scheduler.add_job(updateStreaks, 'date',
                          run_date=date(i.year, i.month, i.day+1))
    else:
        await subscribeToTimeout()


def inVoice(member):
    return member.voice.voice_channel is not None


async def changeNickname(strk, server, user):
    if strk > 0:
        try:
            userobj = client.get_server(server).get_member(user)
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

# meme for å lage command, ikke relevant


def updateLastJoined(member):
    data["servers"][str(member.server.id)]["streaks"][str(
        member.id)]["lastJoined"] = datetime.now().ctime()
    writeToJson()


def serverExists(server):
    return str(server.id) in data["servers"]


def addServer(server):
    data["servers"][str(server.id)] = {"streaks": {}}
    writeToJson()


def memberExists(member):
    return str(member.id) in data["servers"][str(member.server.id)]["streaks"]


async def addMember(member):
    data["servers"][str(member.server.id)]["streaks"][str(member.id)] = {
        "current": 0, "daily": False, "lastJoined": False, "total": 0, "highest": 0}
    writeToJson()
    await changeNickname(0, member.server.id, member.id)
# if done daily


def hasDaily(member):
    return data["servers"][str(member.server.id)]["streaks"][str(member.id)]["daily"]


def giveStreak(member):
    data["servers"][str(member.server.id)]["streaks"][str(
        member.id)]["daily"] = True
    data["servers"][str(member.server.id)
                    ]["streaks"][str(member.id)]["current"] += 1
    data["servers"][str(member.server.id)
                    ]["streaks"][str(member.id)]["total"] += 1
    data["servers"][str(member.server.id)
                    ]["streaks"][str(member.id)]["highest"] = max(data["servers"][str(member.server.id)]["streaks"][str(member.id)]["current"], data["servers"][str(member.server.id)]["streaks"][str(member.id)]["highest"])
    writeToJson()


client.run(config['token'])
