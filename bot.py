#Sports bot

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()
bot = commands.Bot(command_prefix='?')

@bot.command(name='create', help='Responds if there is a hockey game today')
async def sport_today(ctx, sport):
    #match = sports.get_match(sports.HOCKEY, 'islanders', 'flyers')

    checking_msg = await ctx.send('Assembling queue...')

    #create queue
    name_string = '@StealthLego'

    await ctx.send(f'Queue Create! First up is {name_string}')
    #cleanup
    await checking_msg.delete()

'''
@client.event
async def on_ready():
    #for guild in client.guilds:
        

    print(f'{client.user} has connected to Discord!')
    print(f'{client.guilds[0]}(id: {client.guilds[0].id})')'''

bot.run(TOKEN)