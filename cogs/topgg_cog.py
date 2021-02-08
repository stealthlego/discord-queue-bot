import os
import dbl
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DBL_TOKEN = os.getenv('TOP_GG_TOKEN')

class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = DBL_TOKEN # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post(self):
        print("Server count posted successfully")

    #@commands.command(name='count', help='Gets server count')
    async def end(self, ctx):
        '''ends queue and disconnects'''
        await ctx.send(await self.dblpy.get_guild_count())

def setup(bot):
    bot.add_cog(TopGG(bot))