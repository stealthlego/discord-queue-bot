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
#server_handler = {}

### PlayerQueue Class ###
class PlayerQueue(commands.Cog):
    '''Queue object to maintain queue list and timing'''
    def __init__(self, bot):
        super().__init__()
        self.user_list = []
        self.last_event = time.time()
        self.voice_channel = None
        self.text_channel = None

        #self.update_queue.start()

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

    async def msg_cleanup(self, msgs, delay):
        '''deletes messages after given delay'''
        await asyncio.sleep(delay)
        for msg in msgs:
            await msg.delete()

    ## Class Loops ##

    @tasks.loop(seconds=10)
    async def update_queue_loop(self):
        '''checks voice channel to see if anything has changed'''
        self.update_queue()

    ## Commands ##

    @commands.command(name='create', help='Creates initial queue of users')
    async def create_queue(self, ctx):
        '''Creates initial queue of users'''
        msgs = []

        voice_obj = None

        #checks if user is in voice chat
        try:
            voice_obj = ctx.message.author.voice
            channel = ctx.author.voice.channel
            await voice_obj.channel.connect()
        except:
            #remind user they are not in a voice chat room
            msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

            #clean up
            await self.msg_cleanup(ctx, msgs, 5)
            return

        #checks if a queue exists for the current voice channel
        if voice_obj.channel.id in server_handler.keys():
            msgs.append(ctx.send(f'Voice channel already has a queue. Please end before re-creating.'))
            await self.msg_cleanup(ctx, msgs, 5)
            return

        self.voice_channel = voice_obj.channel
        self.text_channel = ctx.message.channel

        for user in channel.members:
            if user.bot:
                pass
                #await ctx.send(f'Cannot add {user.display_name} since they are a bot')
            else:
                await self.append_user(user)

        await self.shuffle_queue()

        #create queue and list
        name_string = self.user_list[0].mention
        await self.text_channel.send(f'Queue Create! First up is {name_string}')
        await self.print_queue()

        #clean up
        await self.msg_cleanup(msgs, 5)
        
    @commands.command(name='next', help='Moves to next person in the queue')
    async def next_up(self, ctx):
        '''moves to the next person in the queue'''
        msgs = []

        #gets new leader and mentions them
        name_string = await self.next_user()
        msgs.append(await self.text_channel.send(f'Next person is {name_string} and the queue is as follows:'))
        await self.print_queue()

        #clean up
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='add', help='Adds a person to the queue')
    async def add(self, ctx):
        '''adds a specific person to the queue'''
        msgs = []

        #gets mentions
        mentions = ctx.message.mentions

        #containers
        added_string = 'Added '
        bot_msg = None

        if len(mentions) == 0:
            #if no mentions cannot remove, post error to chat
            msgs.append(await self.text_channel.send('Nobody added! Make sure to use the @ symbol when adding or removing'))
        elif len(mentions) == 1 and mentions[0].bot:
            #if the mention is a bot throw and error
            msgs.append(await self.text_channel.send(f'Cannot add {mentions[0].display_name} because they are a bot'))
        else:
            #add user to queue
            for i, user in enumerate(mentions):
                if user.bot:
                    msgs.append(await self.text_channel.send(f'Cannot add {user.display_name} because they are a bot'))
                else:
                    await self.append_user(user)
                    added_string = added_string + f'{user.display_name}'

                    if i+1 < len(mentions):
                        added_string = added_string + ', '

            await self.text_channel.send(f'{added_string}')
            await self.print_queue()

        #clean up bot messages
        if bot_msg != None:
            await self.msg_cleanup(msgs, 5)

    @commands.command(name='remove', help='Removes a specific person from the queue')
    async def remove(self, ctx, person):
        '''removes specific person from queue'''
        msgs = []

        #get person to remove
        mentions = ctx.message.mentions

        #containers
        removed_list = ''

        if len(mentions) == 0:
            #if no mentions, cannot remove
            msgs.append(await self.text_channel.send('Nobody removed! Make sure to use the @ symbol when adding or removing'))
        else:
            #remove listed mentions
            for user in mentions:
                if user in await self.current_queue():
                    await self.remove_user(user)
                    removed_list += user.display_name

            await self.text_channel.send(f'Removed {removed_list}')
        
        #prints current queue
        await self.print_queue()

        #clean up bot messages
        if len(msgs) != 0:
            await self.msg_cleanup(msgs, 5)

    @commands.command(name='queue', help='Displays current queue')
    async def queue(self, ctx):
        '''Displays a message with the current queue'''
        await self.print_queue()

    @commands.command(name='update', help='Updates queue with new users automatically')
    async def force_update(self, ctx):
        '''updates queue automatically'''
        await self.update_queue()

    @commands.command(name='shuffle', help='Reshuffles current queue')
    async def shuffle(self, ctx):
        '''reshuffles current queue list'''
        msgs = []

        await self.shuffle_queue()

        msgs.append(await self.text_channel.send(f'Queue Shuffled!'))
        await self.print_queue()
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='end', help='Ends current queue and disconnects from voice chat')
    async def end(self, ctx):
        '''ends queue and disconnects'''
        #del server_handler[ctx.message.author.voice.channel.id]
        msgs = []

        #disconnects from voice chat
        server = ctx.message.guild.voice_client
        await server.disconnect()
        msgs.append(await self.text_channel.send('Ended queue and disconnected. See you next time!'))

        #clean up
        await self.msg_cleanup(msgs, 5)


### Helper Functions ###

@tasks.loop(seconds=120)
async def check_timer():
    '''checks to see if queues have been running without being modified'''
    global server_handler

    for key in server_handler.keys():
        if server_handler[key].check_time() == True:
            del server_handler[key]


@client.event
async def on_ready():
    '''Prints message on server connection'''
    print(f'{client.user} has connected to Discord!')
    check_timer.start()

bot.add_cog(PlayerQueue(bot))
bot.run(TOKEN)

