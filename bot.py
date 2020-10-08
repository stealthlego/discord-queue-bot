#QueueBot
#Author: Alex Anderson

import os
import random
import time
import datetime

#import dbl
import discord
from discord.ext import commands, tasks
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DBL_TOKEN = os.getenv('DBL_TOKEN')

bot = commands.Bot(command_prefix='{')

server_handler = {}

### PlayerQueue Class ###
class PlayerQueue():
    '''Queue object to maintain queue list and timing'''
    def __init__(self, voice_client, voice, text):
        super().__init__()
        self.user_list = []
        self.last_event = datetime.datetime.now()
        self.voice_client = voice_client
        self.voice_channel = voice
        self.text_channel = text

    ## Internal Functions ##

    async def append_user(self, user):
        '''adds user to user list'''
        self.user_list.append(user)
        self.last_event = time.time()

    async def remove_user(self, user):
        '''removes user from list'''
        self.user_list.remove(user)
        self.last_event = time.time()

    async def next_user(self):
        '''updates list and gets next person'''
        user = self.user_list.pop(0)
        self.user_list.append(user)
        self.last_event = time.time()

        return self.user_list[0].mention
    
    async def shuffle_queue(self):
        '''shuffles list'''
        random.shuffle(self.user_list)
    
    async def whos_up(self):
        '''returns who is currently up'''
        return self.user_list[0]

    async def current_queue(self):
        '''returns current list - should not be modified'''
        return self.user_list
        
    async def check_time(self):
        '''checks how long queue has been running without change'''
        CUTOFF_TIME = 60 * 120
        elapsed_time = round(time.time() - self.last_event, 0)
        if elapsed_time > CUTOFF_TIME:
            return True
        else:
            return False

    async def print_queue(self):
        '''prints current queue to text channel'''
        user_list = await self.current_queue()
        queue_string = ''
        
        for i, user in enumerate(user_list):
            if i == 0:
                queue_string = queue_string + f'{i+1}: {user.mention} is currently choosing\n'
            elif i == 1:
                queue_string = queue_string + f'{i+1}: {user.mention} is on deck\n'
            else:
                queue_string = queue_string + f'{i+1}: {user.display_name}\n'

        embed = discord.Embed(
            title = 'Current Queue',
            description = queue_string,
            color = discord.Color.blue()
        )
        
        #paste embed
        await self.text_channel.send(embed=embed)

    async def update_queue(self):
        '''checks voice channel to see if anything has changed'''
        msgs = []
        user_list = await self.current_queue()
        
        #gets voice channel and creates base for missing members
        current_members = self.voice_channel.members
        user_set = set(user_list)
        current_set = set(current_members)

        #check to see if the lists have the same contents
        if set(user_list) == set(current_members):
            #if they have the same contents pass
            pass
        else:
            if len(user_list) > len(current_members)-1:
                #removes members who are no longer part of the voice chat
                to_prune = user_set.difference(current_members)
                for user in to_prune:
                    await self.remove_user(user)

            elif len(user_list) == len(current_members)-1:
                #same number in voice chat, but members are different
                to_add = current_set.difference(user_list)
                to_prune = user_set.difference(current_members)

                for user in to_prune:
                    await self.remove_user(user)

                for user in to_add:
                    if user.bot:
                        #await self.text_channel.send(f'Cannot add {user.display_name} since they are a bot')
                        pass
                    else:
                        await self.append_user(user)
            else:
                #more members, so add the new ones
                to_add = user_set.difference(current_members)

                for user in to_add:
                    if user.bot:
                        #await self.text_channel.send(f'Cannot add {user.display_name} since they are a bot')
                        pass
                    else:
                        await self.append_user(user)

            #prints updated queue
            msgs.append(await self.text_channel.send(f'Queue updated!'))
            await self.print_queue()

            #clean up
            await msg_cleanup(self.text_channel, msgs, 5)

'''
#Boilerplate example from top gg for automatic server count
class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = DBL_TOKEN # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

async def on_guild_post():
    print("Server count posted successfully")
    '''

### Helper Functions ###

@tasks.loop(seconds=10)
async def queue_prune():
    '''prunes old queues'''
    key_holder = []
    if len(server_handler) != 0:
        for key in server_handler:
            time_diff =  datetime.datetime.now() - server_handler[key].last_event
            if time_diff.total_seconds() > 60*60*1: #1 hour
                msgs = []

                #disconnects from voice chat
                server = server_handler[key].voice_client
                await server.disconnect()
                text_channel = server_handler[key].text_channel
                msgs.append(await text_channel.send('Queue timed out, ended queue and disconnected. See you next time!'))

                key_holder.append(key)

                #clean up
                await msg_cleanup(msgs, 5)

    for key in key_holder:
        del server_handler[key] 

    activity = discord.Activity(type= discord.ActivityType.listening, name=f"to {len(server_handler)} queues")
    await bot.change_presence(status=discord.Status.online, activity=activity)

async def get_user_list(ctx):
    '''returns PlayerQueue for voice channel or new PlayerQueue if new'''
    if server_handler.get(ctx.message.author.voice.channel.id) == None:
        new_queue = PlayerQueue(ctx.message.guild.voice_client, ctx.message.author.voice.channel, ctx.message.channel)
        server_handler[ctx.message.author.voice.channel.id] = new_queue
        return new_queue
    else:
        return server_handler.get(ctx.message.author.voice.channel.id)

async def msg_cleanup(msgs, delay):
    '''deletes messages after given delay'''
    await asyncio.sleep(delay)
    for msg in msgs:
        await msg.delete()

### Bot Functions ###

@bot.command(name='create', help='Creates initial queue of users')
async def create_queue(ctx):
    '''Creates initial queue of users'''
    msgs = []

    #checks if user is in voice chat
    try:
        voice_obj = ctx.message.author.voice
        channel = ctx.author.voice.channel
        try:
            await channel.connect()
        except:
            pass
        
    except Exception as e:
        print(str(e))
        #remind user they are not in a voice chat room
        msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

        #clean up
        await msg_cleanup(msgs, 5)
        return

    #get user list 
    user_queue = await get_user_list(ctx)

    for user in user_queue.voice_channel.members:
        print(user.name)
        if user.bot:
            pass
            #await ctx.send(f'Cannot add {user.display_name} since they are a bot')
        else:
            await user_queue.append_user(user)

    await user_queue.shuffle_queue()

    #create queue and list
    name_string = user_queue.user_list[0].mention
    await user_queue.text_channel.send(f'Queue Created! First up is {name_string}')
    await user_queue.print_queue()

    #start loops
    #await user_queue.update_queue_loop.start()

    #clean up
    await msg_cleanup(msgs, 5)
    
@bot.command(name='next', help='Moves to next person in the queue')
async def next_up(ctx):
    '''moves to the next person in the queue'''
    msgs = []
    user_queue = await get_user_list(ctx)

    #gets new leader and mentions them
    name_string = await user_queue.next_user()
    msgs.append(await user_queue.text_channel.send(f'Next person is {name_string} and the queue is as follows:'))
    await user_queue.print_queue()
    user_queue.last_event = datetime.datetime.now()

    #clean up
    await msg_cleanup(msgs, 5)

@bot.command(name='add', help='Adds a person to the queue')
async def add(ctx):
    '''adds a specific person to the queue'''
    msgs = []
    user_queue = await get_user_list(ctx)

    #gets mentions
    mentions = ctx.message.mentions

    #containers
    added_string = 'Added '
    bot_msg = None

    if len(mentions) == 0:
        #if no mentions cannot remove, post error to chat
        msgs.append(await user_queue.text_channel.send('Nobody added! Make sure to use the @ symbol when adding or removing'))
    elif len(mentions) == 1 and mentions[0].bot:
        #if the mention is a bot throw and error
        msgs.append(await user_queue.text_channel.send(f'Cannot add {mentions[0].display_name} because they are a bot'))
    else:
        #add user to queue
        for i, user in enumerate(mentions):
            if user.bot:
                msgs.append(await user_queue.text_channel.send(f'Cannot add {user.display_name} because they are a bot'))
            else:
                await user_queue.append_user(user)
                added_string = added_string + f'{user.display_name}'

                if i+1 < len(mentions):
                    added_string = added_string + ', '

        await user_queue.text_channel.send(f'{added_string}')
        await user_queue.print_queue()
        user_queue.last_event = datetime.datetime.now()

    #clean up bot messages
    if bot_msg != None:
        await msg_cleanup(msgs, 5)

@bot.command(name='remove', help='Removes a specific person from the queue')
async def remove(ctx, person):
    '''removes specific person from queue'''
    msgs = []
    user_queue = await get_user_list(ctx)

    #get person to remove
    mentions = ctx.message.mentions

    #containers
    removed_list = ''

    if len(mentions) == 0:
        #if no mentions, cannot remove
        msgs.append(await user_queue.text_channel.send('Nobody removed! Make sure to use the @ symbol when adding or removing'))
    else:
        #remove listed mentions
        for user in mentions:
            if user in await user_queue.current_queue():
                await user_queue.remove_user(user)
                removed_list += user.display_name

        await user_queue.text_channel.send(f'Removed {removed_list}')
    
    #prints current queue
    await user_queue.print_queue()
    user_queue.last_event = datetime.datetime.now()

    #clean up bot messages
    if len(msgs) != 0:
        await msg_cleanup(msgs, 5)

@bot.command(name='queue', help='Displays current queue')
async def queue(ctx):
    '''Displays a message with the current queue'''
    user_queue = await get_user_list(ctx)
    await user_queue.print_queue()
    user_queue.last_event = datetime.datetime.now()

@bot.command(name='update', help='Updates queue with new users automatically')
async def force_update(ctx):
    '''updates queue automatically'''
    user_queue = await get_user_list(ctx)
    await user_queue.update_queue()
    user_queue.last_event = datetime.datetime.now()

@bot.command(name='shuffle', help='Reshuffles current queue')
async def shuffle(ctx):
    '''reshuffles current queue list'''
    msgs = []
    user_queue = await get_user_list(ctx)

    await user_queue.shuffle_queue()

    msgs.append(await user_queue.text_channel.send(f'Queue Shuffled!'))
    await user_queue.print_queue()
    user_queue.last_event = datetime.datetime.now()
    await msg_cleanup(msgs, 5)

@bot.command(name='end', help='Ends current queue and disconnects from voice chat')
async def end(ctx):
    '''ends queue and disconnects'''
    msgs = []
    del server_handler[ctx.message.author.voice.channel.id] 

    #disconnects from voice chat
    server = ctx.message.guild.voice_client
    await server.disconnect()
    msgs.append(await ctx.send('Ended queue and disconnected. See you next time!'))

    #clean up
    await msg_cleanup(msgs, 5)

@bot.event
async def on_ready():
    '''Prints message on server connection'''
    print(f'\n{bot.user.name} has connected to Discord!\n')
    activity = discord.Activity(type= discord.ActivityType.playing, name=f"{'help {'} | {len(server_handler)} queues")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    await queue_prune.start()

#bot.add_cog(TopGG(bot))
bot.run(TOKEN)

