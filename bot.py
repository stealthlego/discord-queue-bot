#Sports bot

import os

from discord.ext import commands
from dotenv import load_dotenv
import sports

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')

#client = discord.Client()
bot = commands.Bot(command_prefix='?')

@bot.command(name='today', help='Responds if there is a hockey game today')
async def sport_today(ctx, sport):
    #match = sports.get_match(sports.HOCKEY, 'islanders', 'flyers')

    await ctx.send('Let me check...')

    all_matches = sports.all_matches()
    hockey = all_matches[sport]
    first_game = hockey[0]
    #print(response)
    await ctx.send(f'{first_game.home_team}: {first_game.home_score}\n{first_game.away_team}: {first_game.away_score}')

'''
@client.event
async def on_ready():
    #for guild in client.guilds:
        

    print(f'{client.user} has connected to Discord!')
    print(f'{client.guilds[0]}(id: {client.guilds[0].id})')'''

bot.run(TOKEN)