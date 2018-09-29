import discord
import asyncio
import json

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
    for c in config['allowed_channels']:
        channels[getSplitName(client.get_channel(c))]={
            'members':[len(client.get_channel(c).voice_members)],
            'entries':[c]}


@client.event
async def on_voice_state_update(before, after):
    b,a=before.voice.voice_channel,after.voice.voice_channel
    if b!=a:
        if b and channels[getSplitName(b)]:
            print(str(b))
            await decrement(b)
        if a and channels[getSplitName(a)]:
            await increment(a)
        
        
    
def getSplitName(a):
    return str(a).split("#")[-2]
def getSplitNum(a):
    return str(a).split("#")[-1]
async def decrement(a):
    channels[getSplitName(a)]['members'][int(getSplitNum(a))-1]-=1
    if a.id not in config['allowed_channels'] and channels[getSplitName(a)]['members']<1:
        #purge channel
        await client.delete_channel(a)
        #rename channels if necessary
        entries=channels[getSplitName(a)]['entries']
        entries.pop(int(getSplitNum(a))-1)
        #lazy
        entries=channels[getSplitName(a)]['entries']
        entries.insert(int(getSplitNum(a))-1, entries.pop(-1))
        #moved last element to deleted index, so no need to update all
        #now to rename said channel
        #also need to move channel afterwards 
        entries=channels[getSplitName(a)]['entries']
        await client.edit_channel(client.get_channel(entries[int(getSplitNum(a)-1)], {'name':a.name}))
        #move channel
        await client.move_channel(client.get_channel(entries[int(getSplitNum(a)-1)]),client.get_channel(entries[0]).position+int(getSplitNum(a)) - 1)

async def increment(a):
    channels[getSplitName(a)]['members'][int(getSplitNum(a))-1]+=1
    if (channels[getSplitName(a)]['members'][int(getSplitNum(a))-1]==1):
        #create new channel and append to end of list
        x=await client.create_channel(a.server, getSplitName(a)+"#"+str(len(channels[getSplitName(a)]['entries'])+1), type=discord.ChannelType.voice)
        channels[getSplitName(a)]['entries'].append(x.id)
        #move new channel
        await client.move_channel(x, client.get_channel(channels[getSplitName(a)]['entries'][0]).position+int(getSplitNum(a))-1)
        


client.run(config['token'])
