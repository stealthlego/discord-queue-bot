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

user_list = []

### Regular python functions ###

async def print_queue(ctx):
    ''' creates embed and posts it'''
    global user_list
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

### Bot Tasks ###

@tasks.loop(seconds=5)
async def check_users(ctx):
    '''checks to see if somebody new joined the voice chat'''
    await update(ctx)
    #await asyncio.sleep(5)

### Bot Commands ###

@bot.command(name='create', help='Creates initial queue of users')
async def create_queue(ctx):
    '''Creates initial queue of users'''
    global user_list
    msgs = []

    #msgs.append(await ctx.send('Assembling queue...'))
    voice_obj = ctx.message.author.voice

    #checks if user is in voice chat
    try:
        channel = ctx.author.voice.channel
        await voice_obj.channel.connect()

        #asks if user wants to create new queue if one already exists
        if len(user_list) != 0:
            #yes/no response
            #empties out user list since it is creating it from scratch
            user_list = []
        else:
            for user in channel.members:
                if user.bot:
                    await ctx.send(f'Cannot add {user.display_name} since they are a bot')
                else:
                    user_list.append(user)

            random.shuffle(user_list)

            #create queue and list
            name_string = user_list[0].mention
            await ctx.send(f'Queue Create! First up is {name_string}')
            await print_queue(ctx)

            #start monitoring task
            #bot.loop.create_task(check_users(ctx))

            #clean up
            await msg_cleanup(ctx, msgs, 5)
    except:
        #remind user they are not in a voice chat room
        msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

        #clean up
        await msg_cleanup(ctx, msgs, 5)
    
@bot.command(name='next', help='Moves to next person in the queue')
async def next_up(ctx):
    '''moves to the next person in the queue'''
    #moves to next user
    global user_list
    msgs = []

    #moves top user from bottom to top of list
    user = user_list.pop(0)
    user_list.append(user)

    #gets new leader and mentions them
    name_string = user_list[0].mention
    msgs.append(await ctx.send(f'Next person is {name_string} and the queue is as follows:'))
    await print_queue(ctx)

    #clean up
    await msg_cleanup(ctx, msgs, 5)

@bot.command(name='add', help='Adds a person to the queue')
async def add(ctx, person):
    '''adds a specific person to the queue'''
    global user_list
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
                user_list.append(user)
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
    global user_list
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
            if user in user_list:
                user_list.remove(user)
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
    global user_list

    #prints queue
    await print_queue(ctx)

@bot.command(name='update', help='Updates queue with new users automatically')
async def update(ctx):
    '''updates queue automatically'''
    global user_list
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
                user_list.remove(user)

        elif len(user_list) == len(current_members)-1:
            #same number in voice chat, but members are different
            to_add = current_set.difference(user_list)
            to_prune = user_set.difference(current_members)

            for user in to_prune:
                user_list.remove(user)

            for user in to_add:
                if user.bot:
                    await ctx.send(f'Cannot add {user.display_name} since they are a bot')
                else:
                    user_list.append(user)
        else:
            #more members, so add the new ones
            to_add = user_set.difference(current_members)

            for user in to_add:
                if user.bot:
                    await ctx.send(f'Cannot add {user.display_name} since they are a bot')
                else:
                    user_list.append(user)

        #prints updated queue
        msgs.append(await ctx.send(f'Queue updated!'))
        await print_queue(ctx)

        #clean up
        await msg_cleanup(ctx, msgs, 5)

@bot.command(name='end', help='Ends current queue and disconnects from voice chat')
async def end(ctx):
    '''ends queue and disconnects'''
    global user_list
    msgs = []

    #clears list
    user_list = []

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