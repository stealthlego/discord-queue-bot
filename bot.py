#Queue Bot
#Author: Alex Anderson

import os
import random
import time

import discord
from discord.ext import commands, tasks
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


### Bot Tasks ###

@tasks.loop(seconds=10)
async def check_users():
    '''checks to see if somebody new joined the voice chat'''


### Bot Commands ###

@bot.command(name='create', help='Creates initial queue of users')
async def create_queue(ctx):
    '''Creates initial queue of users'''
    global user_list
    checking_msg = await ctx.send('Assembling queue...')
    voice_obj = ctx.message.author.voice

    #checks if user is in voice chat
    try:
        channel = ctx.message.author.voice.channel

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

            #create queue
            name_string = user_list[0].mention

            await ctx.send(f'Queue Create! First up is {name_string}')
            #cleanup
            await checking_msg.delete()
            await voice_obj.channel.connect()
    except:
        #remind user they are not in a voice chat room
        no_voice_msg = await ctx.send('You are not in a voice channel. Please join and try again')
        time.sleep(3)
        #cleanup
        await checking_msg.delete()
        await no_voice_msg.delete()
    

@bot.command(name='next', help='Moves to next person in the queue')
async def next_up(ctx):
    '''moves to the next person in the queue'''
    #moves to next user
    global user_list
    user = user_list.pop(0)
    user_list.append(user)

    name_string = user_list[0].mention

    up_next_msg = await ctx.send(f'Next person is {name_string} and the queue is as follows:')

    await print_queue(ctx)
    time.sleep(5)
    await up_next_msg.delete()

@bot.command(name='add', help='Adds a person to the queue')
async def add(ctx, person):
    '''adds a specific person to the queue'''
    global user_list

    mentions = ctx.message.mentions
    added_string = 'Added '
    bot_msg = None

    if len(mentions) == 0:
        await ctx.send('Nobody added! Make sure to use the @ symbol when adding or removing')
    elif len(mentions) == 1 and mentions[0].bot:
        bot_msg = await ctx.send(f'Cannot add {mentions[0].display_name} because they are a bot')
    else:
        for i, user in enumerate(mentions):
            if user.bot:
                bot_msg = await ctx.send(f'Cannot add {user.display_name} because they are a bot')
            else:
                user_list.append(user)
                added_string = added_string + f'{user.display_name}'

                if i+1 < len(mentions):
                    added_string = added_string + ', '

        await ctx.send(f'{added_string}')
        await print_queue(ctx)
    #clean up bot messages
    if bot_msg != None:
        time.sleep(5)
        await bot_msg.delete()

@bot.command(name='remove', help='Removes a specific person from the queue')
async def remove(ctx, person):
    '''removes specific person from queue'''
    global user_list

    mentions = ctx.message.mentions
    removed_list = ''
    bot_msg = None

    if len(mentions) == 0:
        bot_msg = await ctx.send('Nobody removed! Make sure to use the @ symbol when adding or removing')
    else:
        for user in mentions:
            if user in user_list:
                user_list.remove(user)
                removed_list += user.display_name

        await ctx.send(f'Removed {removed_list}')
    
    #prints current queue
    await print_queue(ctx)

    #clean up bot messages
    if bot_msg != None:
        time.sleep(5)
        await bot_msg.delete()

@bot.command(name='queue', help='Displays current queue')
async def queue(ctx):
    '''Displays a message with the current queue'''
    global user_list

    await print_queue(ctx)

@bot.command(name='update', help='Updates queue with new users automatically')
async def update(ctx):
    '''updates queue automatically'''
    global user_list

    channel = ctx.message.author.voice.channel

    missing_members = channel.members

    for user in missing_members:
        if user in user_list:
            missing_members.remove(user)

    for user in missing_members:
        if user.bot:
            await ctx.send(f'Cannot add {user.display_name} since they are a bot')
        else:
            user_list.append(user)

    await ctx.send(f'Queue updated!')

    #print_queue(ctx)

@bot.command(name='end', help='Ends current queue and disconnects from voice chat')
async def end(ctx):
    '''ends queue and disconnects'''
    global user_list

    #clears list
    user_list = []

    #disconnects from voice chat
    server = ctx.message.guild.voice_client
    await server.disconnect()
    disconnect_msg = await ctx. send('Ended queue and disconnected. See you next time!')

    time.sleep(5)

    await disconnect_msg.delete()

@client.event
async def on_ready():
    '''Prints message on server connection'''
    print(f'{client.user} has connected to Discord!')

bot.run(TOKEN)