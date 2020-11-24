from asyncio.tasks import current_task
import os
import random
import time
import datetime
from attr import dataclass

import discord
from discord.ext import commands, tasks
import asyncio

server_handler = {}

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
        self.last_event = datetime.datetime.now()

    async def remove_user(self, user):
        '''removes user from list'''
        self.user_list.remove(user)
        self.last_event = datetime.datetime.now()

    async def next_user(self):
        '''updates list and gets next person'''
        user = self.user_list.pop(0)
        self.user_list.append(user)
        self.last_event = datetime.datetime.now()

        return self.user_list[0].mention
    
    async def shuffle_queue(self):
        '''shuffles list'''
        random.shuffle(self.user_list)
        self.last_event = datetime.datetime.now()
    
    async def whos_up(self):
        '''returns who is currently up'''
        self.last_event = datetime.datetime.now()
        return self.user_list[0]
        
    async def current_queue(self):
        '''returns current list - should not be modified'''
        self.last_event = datetime.datetime.now()
        return self.user_list

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
            self.last_event = datetime.datetime.now()

            return msgs

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_prune.start()

    ### helper functions ###
    async def get_user_list(self, ctx):
        '''returns PlayerQueue for voice channel or new PlayerQueue if new'''
        if server_handler.get(ctx.message.author.voice.channel.id) == None:
            new_queue = PlayerQueue(ctx.message.guild.voice_client, ctx.message.author.voice.channel, ctx.message.channel)
            server_handler[ctx.message.author.voice.channel.id] = new_queue
            return new_queue
        else:
            return server_handler.get(ctx.message.author.voice.channel.id)

    async def msg_cleanup(self, msgs, delay):
        '''deletes messages after given delay'''
        await asyncio.sleep(delay)
        for msg in msgs:
            await msg.delete()

    @tasks.loop(seconds=360)
    async def queue_prune(self):
        '''prunes old queues'''
        key_holder = []
        
        if len(server_handler) != 0:
            print('Checking for stale queues...')
            for key in server_handler:

                time_d = datetime.datetime.now() - server_handler[key].last_event
                if time_d.total_hours() > 1: #1 hour
                    msgs = []

                    text_channel = server_handler[key].text_channel
                    msgs.append(await text_channel.send('Queue timed out, ended queue and disconnected. See you next time!'))

                    key_holder.append(key)

                    #clean up
                    await self.msg_cleanup(msgs, 5)

        for key in key_holder:
            del server_handler[key] 

            await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))

    ### commands ###
    @commands.command(name='create', help='Creates initial queue of users')
    async def create_queue(self, ctx):
        '''Creates initial queue of users'''
        msgs = []

        #checks if user is in voice chat
        try:
            voice_obj = ctx.message.author.voice
            channel = ctx.author.voice.channel
            '''
            try:
                await channel.connect()
            except:
                pass
            '''
        except Exception as e:
            print(str(e))
            #remind user they are not in a voice chat room
            msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

            #clean up
            await self.msg_cleanup(msgs, 5)
            return

        #get user list 
        user_queue = await self.get_user_list(ctx)

        for user in user_queue.voice_channel.members:
            if user.bot:
                pass
            else:
                await user_queue.append_user(user)

        try:
            #create queue and list
            await user_queue.shuffle_queue()
            name_string = user_queue.user_list[0].mention
            msgs.append(await ctx.send(f'Queue Created! First up is {name_string}'))
            await user_queue.print_queue()
            await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))
        except:
            msgs.append(await ctx.send('An error has occurred!. Please re-join  your voice channel and try again'))

        #clean up
        await self.msg_cleanup(msgs, 5)
        
    @commands.command(name='next', help='Moves to next person in the queue')
    async def next_up(self, ctx):
        '''moves to the next person in the queue'''
        msgs = []
        user_queue = await self.get_user_list(ctx)

        #gets new leader and mentions them
        name_string = await user_queue.next_user()
        msgs.append(await user_queue.text_channel.send(f'Next person is {name_string} and the queue is as follows:'))
        await user_queue.print_queue()
        user_queue.last_event = datetime.datetime.now()

        #clean up
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='add', help='Adds a person to the queue')
    async def add(self, ctx):
        '''adds a specific person to the queue'''
        msgs = []
        user_queue = await self.get_user_list(ctx)

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
            await self.msg_cleanup(msgs, 5)

    @commands.command(name='remove', help='Removes a specific person from the queue')
    async def remove(self, ctx, person):
        '''removes specific person from queue'''
        msgs = []
        user_queue = await self.get_user_list(ctx)

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
            await self.msg_cleanup(msgs, 5)

    @commands.command(name='queue', help='Displays current queue')
    async def queue(self, ctx):
        '''Displays a message with the current queue'''
        user_queue = await self.get_user_list(ctx)
        await user_queue.print_queue()
        user_queue.last_event = datetime.datetime.now()

    @commands.command(name='update', help='Updates queue with new users automatically')
    async def force_update(self, ctx):
        '''updates queue automatically'''
        user_queue = await self.get_user_list(ctx)
        msgs = await user_queue.update_queue()
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='shuffle', help='Reshuffles current queue')
    async def shuffle(self, ctx):
        '''reshuffles current queue list'''
        msgs = []
        user_queue = await self.get_user_list(ctx)

        await user_queue.shuffle_queue()

        msgs.append(await user_queue.text_channel.send(f'Queue Shuffled!'))
        await user_queue.print_queue()
        user_queue.last_event = datetime.datetime.now()
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='end', help='Ends current queue and disconnects from voice chat')
    async def end(self, ctx):
        '''ends queue and disconnects'''
        msgs = []
        del server_handler[ctx.message.author.voice.channel.id] 

        #disconnects from voice chat
        server = ctx.message.guild.voice_client
        #await server.disconnect()
        msgs.append(await ctx.send('Ended queue, see you next time!'))
        await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))

        #clean up
        await self.msg_cleanup(msgs, 5)

def setup(bot):
    cog = QueueCog(bot)
    bot.add_cog(cog)