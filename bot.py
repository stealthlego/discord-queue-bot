#QueueBot
#Author: Alex Anderson

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

STATUS = 'DEPLOY' #use BETA tag when testing
TOKEN = ''
PREFIX = ''

load_dotenv()
if STATUS == 'BETA':
    TOKEN = os.getenv('BETA_TOKEN')
    PREFIX = os.getenv('BETA_PREFIX')
else:
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = os.getenv('PREFIX')

initial_extensions = [
    "cogs.queuecog"
]

bot = commands.Bot(command_prefix=f'{PREFIX}')

#load cogs
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(f"{'{'}help"))
    print(f'Successfully logged in and booted...!')

bot.run(TOKEN, bot=True)


