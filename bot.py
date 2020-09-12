#Queue Bot
#Author: Alex Anderson

import os
import random
import time

import discord
from discord.ext import commands, tasks
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()
bot = commands.Bot(command_prefix='?')

#user_list = []
server_handler = {}

### PlayerQueue Class ###
class PlayerQueue():
    '''Queue object to maintain queue list and timing'''
    def __init__(self):
        super().__init__()
        self.user_list = []
        self.last_event = time.time()

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
    
    async def shuffle(self):
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

### Regular python functions ###

async def print_queue(ctx):
    ''' creates embed and posts it'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    user_list = await current_queue.current_queue()
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
    await ctx.send(embed=embed)

async def msg_cleanup(ctx, msgs, delay):
    '''deletes messages after given delay'''
    await asyncio.sleep(delay)
    for msg in msgs:
        await msg.delete()

async def update(ctx):
    '''updates queue based on users in a voice chat'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    user_list = await current_queue.current_queue()
    msgs = []

    #gets voice channel and creates base for missing members
    channel = ctx.message.author.voice.channel
    current_members = channel.members
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
                await current_queue.remove_user(user)

        elif len(user_list) == len(current_members)-1:
            #same number in voice chat, but members are different
            to_add = current_set.difference(user_list)
            to_prune = user_set.difference(current_members)

            for user in to_prune:
                await current_queue.remove_user(user)

            for user in to_add:
                if user.bot:
                    await ctx.send(f'Cannot add {user.display_name} since they are a bot')
                else:
                    await current_queue.append_user(user)
        else:
            #more members, so add the new ones
            to_add = user_set.difference(current_members)

            for user in to_add:
                if user.bot:
                    await ctx.send(f'Cannot add {user.display_name} since they are a bot')
                else:
                    await current_queue.append_user(user)

        #prints updated queue
        msgs.append(await ctx.send(f'Queue updated!'))
        await print_queue(ctx)

        #clean up
        await msg_cleanup(ctx, msgs, 5)

### Bot Tasks ###

@tasks.loop(seconds=10)
async def check_users(ctx):
    '''checks to see if somebody new joined the voice chat'''
    await update(ctx)

@tasks.loop(seconds=120)
async def check_timer(ctx):
    '''checks to see if queues have been running without being modified'''
    global server_handler

    for key in server_handler.keys():
        if server_handler[key].check_time() == True:
            del server_handler[key]

### Bot Commands ###

@bot.command(name='create', help='Creates initial queue of users')
async def create_queue(ctx):
    '''Creates initial queue of users'''
    global server_handler
    msgs = []

    voice_obj = ctx.message.author.voice

    #checks if a queue exists for the current voice channel
    if voice_obj.channel.id in server_handler.keys():
        msgs.append(ctx.send(f'Voice channel already has a queue. Please end before re-creating.'))
        await msg_cleanup(ctx, msgs, 5)
        return

    #checks if user is in voice chat
    try:
        channel = ctx.author.voice.channel
        await voice_obj.channel.connect()
    except:
        #remind user they are not in a voice chat room
        msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

        #clean up
        await msg_cleanup(ctx, msgs, 5)
        return

    #creates new playerqueue object and adds it to global list
    new_queue = PlayerQueue()
    server_handler.update({voice_obj.channel.id : new_queue})

    for user in channel.members:
        if user.bot:
            pass
            #await ctx.send(f'Cannot add {user.display_name} since they are a bot')
        else:
            await new_queue.append_user(user)

    await new_queue.shuffle()

    #create queue and list
    name_string = new_queue.user_list[0].mention
    await ctx.send(f'Queue Create! First up is {name_string}')
    await print_queue(ctx)

    #clean up
    await msg_cleanup(ctx, msgs, 5)
    
@bot.command(name='next', help='Moves to next person in the queue')
async def next_up(ctx):
    '''moves to the next person in the queue'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    msgs = []

    #gets new leader and mentions them
    name_string = await current_queue.next_user()
    msgs.append(await ctx.send(f'Next person is {name_string} and the queue is as follows:'))
    await print_queue(ctx)

    #clean up
    await msg_cleanup(ctx, msgs, 5)

@bot.command(name='add', help='Adds a person to the queue')
async def add(ctx, person):
    '''adds a specific person to the queue'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    msgs = []

    #gets mentions
    mentions = ctx.message.mentions

    #containers
    added_string = 'Added '
    bot_msg = None

    if len(mentions) == 0:
        #if no mentions cannot remove, post error to chat
        await ctx.send('Nobody added! Make sure to use the @ symbol when adding or removing')
    elif len(mentions) == 1 and mentions[0].bot:
        #if the mention is a bot throw and error
       msgs.append(await ctx.send(f'Cannot add {mentions[0].display_name} because they are a bot'))
    else:
        #add user to queue
        for i, user in enumerate(mentions):
            if user.bot:
                msgs.append(await ctx.send(f'Cannot add {user.display_name} because they are a bot'))
            else:
                await current_queue.append_user(user)
                added_string = added_string + f'{user.display_name}'

                if i+1 < len(mentions):
                    added_string = added_string + ', '

        await ctx.send(f'{added_string}')
        await print_queue(ctx)

    #clean up bot messages
    if bot_msg != None:
        await msg_cleanup(ctx, msgs, 5)

@bot.command(name='remove', help='Removes a specific person from the queue')
async def remove(ctx, person):
    '''removes specific person from queue'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    msgs = []

    #get person to remove
    mentions = ctx.message.mentions

    #containers
    removed_list = ''

    if len(mentions) == 0:
        #if no mentions, cannot remove
        msgs.append(await ctx.send('Nobody removed! Make sure to use the @ symbol when adding or removing'))
    else:
        #remove listed mentions
        for user in mentions:
            if user in await current_queue.current_queue():
                await current_queue.remove_user(user)
                removed_list += user.display_name

        await ctx.send(f'Removed {removed_list}')
    
    #prints current queue
    await print_queue(ctx)

    #clean up bot messages
    if len(msgs) != 0:
        await msg_cleanup(ctx, msgs, 5)

@bot.command(name='queue', help='Displays current queue')
async def queue(ctx):
    '''Displays a message with the current queue'''
    await print_queue(ctx)

@bot.command(name='update', help='Updates queue with new users automatically')
async def update_queue(ctx):
    '''updates queue automatically'''
    await update(ctx)

@bot.command(name='shuffle', help='Reshuffles current queue')
async def shuffle(ctx):
    '''reshuffles current queue list'''
    global server_handler
    current_queue = server_handler.get(ctx.message.author.voice.channel.id)
    msgs = []

    await current_queue.shuffle()

    msgs.append(await ctx.send(f'Queue Shuffled!'))
    await print_queue(ctx)
    await msg_cleanup(ctx, msgs, 5)

@bot.command(name='end', help='Ends current queue and disconnects from voice chat')
async def end(ctx):
    '''ends queue and disconnects'''
    global server_handler
    del server_handler[ctx.message.author.voice.channel.id]

    msgs = []

    #disconnects from voice chat
    server = ctx.message.guild.voice_client
    await server.disconnect()
    msgs.append(await ctx. send('Ended queue and disconnected. See you next time!'))

    #clean up
    await msg_cleanup(ctx, msgs, 5)

@client.event
async def on_ready():
    '''Prints message on server connection'''
    print(f'{client.user} has connected to Discord!')

bot.run(TOKEN)