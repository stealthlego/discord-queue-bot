#Sports bot

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import sports

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()
bot = commands.Bot(command_prefix='?')

@bot.command(name='today', help='Responds if there is a hockey game today')
async def sport_today(ctx, sport):
    #match = sports.get_match(sports.HOCKEY, 'islanders', 'flyers')

    checking_msg = await ctx.send('Let me check...')

    #need to parse input for specific sport

    all_matches = sports.get_sport(sports.HOCKEY)
    match_list = []
    sorting_msg = await ctx.send(f'Sorting through {len(all_matches)} matches...')
    for match in all_matches:
        #print(f'Match day: {match.match_date.day}')
        #print(f'Date day: {datetime.today().day}')
        #print(str(match.league))
        if match.match_date.day == datetime.today().day and 'USA' in match.league:
            match_list.append(match)

    embed = discord.Embed(
        title = 'Games Today',
        description = f'List of {sport} games today',
        color = discord.Color.blue()
    )

    for game in match_list:
        time_string = game.match_date.strftime('%H:%M')
        embed.add_field(
            name=f'Game {match_list.index(game)+1} @ {time_string}', 
            value=f'{game.home_team} V {game.away_team}',
            inline=False
        )

    #paste embed
    await ctx.send(embed=embed)
    #cleanup
    await checking_msg.delete()
    await sorting_msg.delete()


'''
@client.event
async def on_ready():
    #for guild in client.guilds:
        

    print(f'{client.user} has connected to Discord!')
    print(f'{client.guilds[0]}(id: {client.guilds[0].id})')'''

bot.run(TOKEN)