import discord
import asyncio

with open("config.json") as f:
    config = json.loads(f.read())

client = discord.Client()
channels = {}


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    # gen channel
    for k, v in config.servers:
        s = get_server(k)
        for k1, v1 in v.allowed_channels:


@client.event
async def on_group_join(channel, user):
    if channel.name in channels:
        name = channel.name.split(" ")[1]
        numb = channel.name[-1]


client.run(config.token)
