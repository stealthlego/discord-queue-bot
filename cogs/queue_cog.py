from asyncio.tasks import current_task
import datetime
from attr import dataclass
import discord
from discord.ext import commands, tasks
import asyncio
from .player_queue import PlayerQueue

server_handler = {}
reactions = [
    "\U000027A1", 
    "\U00002705", 
    "\U0000274C", 
    "\U0001F504", 
    "\U0001F500", 
    "\U0001F6D1"
]
instructions = [
    "Next player", 
    "Add yourself to the queue", 
    "Remove yourself from the queue", 
    "Force update the queue", 
    "Shuffle queue", 
    "End queue"
]

class QueueCommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_prune.start()

    ### helper functions ###
    async def get_user_list(self, ctx):
        '''returns PlayerQueue for voice channel or new PlayerQueue if new'''
        if server_handler.get(ctx.message.guild.id) == None:
            msgs = []
            msgs.append(await ctx.send('Queue for this server does not exist, try creating one first'))

            #clean up
            await self.msg_cleanup(msgs, 5)
        else:
            return server_handler.get(ctx.message.guild.id)

    async def msg_cleanup(self, msgs, delay):
        '''deletes messages after given delay'''
        await asyncio.sleep(delay)
        for msg in msgs:
            await msg.delete()

    async def generate_embed(self, queue):
        '''prints current queue to text channel'''
        queue_string = ''
        
        for i, member in enumerate(queue.member_list):
            if i == 0:
                queue_string = queue_string + f'{i+1}: {member.mention} is currently up!\n'
            elif i == 1:
                queue_string = queue_string + f'{i+1}: {member.mention} is on deck\n'
            else:
                queue_string = queue_string + f'{i+1}: {member.display_name}\n'

        # add command prompts for reactions
        commands_string = ''

        for i in range(len(reactions)):
            commands_string = commands_string + f'{reactions[i]} = {instructions[i]}\n'

        queue.embed = discord.Embed(
            title = f'{queue.voice.name} Queue',
            #description = queue_string,
            color = discord.Color.blue()
        )

        queue.embed.add_field(name='Queue', value=queue_string)
        queue.embed.add_field(name='Commands', value=commands_string)

    async def update_embed(self, queue):
        '''Updates embed with current queue'''
        await self.generate_embed(queue)

        #paste embed
        if queue.embed_exists == False:
            queue.embed_msg = await queue.text.send(embed=queue.embed)
            queue.embed_exists = True
        else:
            await queue.embed_msg.edit(embed=queue.embed)

        for emoji in reactions: 
            await queue.embed_msg.add_reaction(emoji)
            
    @tasks.loop(seconds=360)
    async def queue_prune(self):
        '''prunes old queues'''
        key_holder = []
        
        if len(server_handler) != 0:
            print('Checking for stale queues...')
            for key in server_handler:

                time_d = datetime.datetime.now() - server_handler[key].last_event
                if time_d.total_seconds() > 3600: #1 hour
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
        msgs.append(ctx.message)

        #checks if user is in voice chat
        try:
            voice_obj = ctx.message.author.voice.channel.id

            if voice_obj != None:
                pass
        except Exception as e:
            print(str(e))
            #remind user they are not in a voice chat room
            msgs.append(await ctx.send('You are not in a voice channel. Please join and try again'))

            #clean up
            await self.msg_cleanup(msgs, 5)
            return

        #check if there is a queue for this voice chat
        if ctx.message.guild.id in server_handler.keys():
            msgs.append(await ctx.send('There is already a queue for this build channel'))
        else:
            #create user list 
            voice = ctx.message.author.voice.channel
            text = ctx.message.channel
            guild= ctx.message.channel.guild
            user_queue = []

            for member in ctx.message.author.voice.channel.members:
                if member.bot:
                    pass
                else:
                    user_queue.append(member)
            
            if len(user_queue) == 0:
                msgs.append(await ctx.send('An error has occurred!. Please re-join  your voice channel and try again'))
            else:
                #add to server handler object for storage
                current_queue = PlayerQueue(guild, voice, text, user_queue)
                server_handler[guild.id] = current_queue
                await current_queue.shuffle_queue()
                await self.update_embed(current_queue)
                await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))

        #clean up
        await self.msg_cleanup(msgs, 5)
        
    #@commands.command(name='next', help='Moves to next person in the queue')
    async def next_up(self, ctx):
        '''moves to the next person in the queue'''
        msgs = []
        msgs.append(ctx.message)
        queue = await server_handler[ctx.message.guild.id]

        #gets new leader and mentions them
        name_string = await queue.next_user()
        msgs.append(await queue.text.send(f'{name_string} is up!'))
        await self.update_embed(queue)

        #clean up
        await self.msg_cleanup(msgs, 5)

    #@commands.command(name='add', help='Adds a person to the queue')
    async def add(self, ctx):
        '''adds a specific person to the queue'''
        msgs = []
        msgs.append(ctx.message)
        queue = await self.get_user_list(ctx.message.channel)

        #gets mentions
        mentions = ctx.message.mentions

        #containers
        added_string = 'Added '
        bot_msg = None

        if len(mentions) == 0:
            #if no mentions cannot remove, post error to chat
            msgs.append(await queue.text.send('Nobody added! Make sure to use the @ symbol when adding or removing'))
        elif len(mentions) == 1 and mentions[0].bot:
            #if the mention is a bot throw and error
            msgs.append(await queue.text.send(f'Cannot add {mentions[0].display_name} because they are a bot'))
        else:
            #add members to queue
            for i, member in enumerate(mentions):
                if member.bot:
                    msgs.append(await queue.text.send(f'Cannot add {member.display_name} because they are a bot'))
                else:
                    await queue.add_user(member)
                    added_string = added_string + f'{member.display_name}'

                    if i+1 < len(mentions):
                        added_string = added_string + ', '

            msgs.append(await queue.text.send(f'{added_string}'))
            await self.update_embed(queue)

        #clean up bot messages
        if len(msgs) != 0:
            await self.msg_cleanup(msgs, 5)

    #@commands.command(name='remove', help='Removes a specific person from the queue')
    async def remove(self, ctx, person):
        '''removes specific person from queue'''
        msgs = []
        msgs.append(ctx.message)
        queue = server_handler(ctx.message.guild.id)

        #get person to remove
        mentions = ctx.message.mentions

        #containers
        removed_list = ''

        if len(mentions) == 0:
            #if no mentions, cannot remove
            msgs.append(await queue.text.send('Nobody removed! Make sure to use the @ symbol when adding or removing'))
        else:
            #remove listed mentions
            for member in mentions:
                if member in await queue.current_queue():
                    await queue.remove_user(member)
                    removed_list += member.display_name

            msgs.append(await queue.text.send(f'Removed {removed_list}'))
        
        #prints current queue
        await self.update_embed(queue)

        #clean up bot messages
        if len(msgs) != 0:
            await self.msg_cleanup(msgs, 5)

    #@commands.command(name='queue', help='Displays current queue')
    async def queue(self, ctx):
        '''Displays a message with the current queue'''
        queue = server_handler.get(ctx.message.guild.id)
        await self.update_embed(queue)

    #@commands.command(name='update', help='Updates queue with new users automatically')
    async def force_update(self, ctx):
        '''updates queue automatically'''
        queue = server_handler.get(ctx.message.guild.id)
        await self.update_embed(queue)

    #@commands.command(name='shuffle', help='Reshuffles current queue')
    async def shuffle(self, ctx):
        '''reshuffles current queue list'''
        msgs = []
        msgs.append(ctx.message)
        queue = server_handler.get(ctx.message.channel.id)

        await queue.shuffle_queue()
        msgs.append(await queue.text.send(f'Queue Shuffled!'))

        await self.update_embed(queue)
        await self.msg_cleanup(msgs, 5)

    @commands.command(name='end', help='Force ends current queue')
    async def end(self, ctx):
        '''ends queue and disconnects'''
        msgs = []
        msgs.append(ctx.message)
        msgs.append(server_handler[ctx.message.author.voice.channel.id].embed_msg)
        del server_handler[ctx.message.guild.id] 

        msgs.append(await ctx.send('Ended queue, see you next time!'))
        await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))

        #clean up
        await self.msg_cleanup(msgs, 5)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, member):
        
        if member.bot:
            return

        emoji = reaction.emoji
        guild = reaction.message.guild
        msgs = []
        queue = server_handler.get(reaction.message.guild.id)

        if emoji == reactions[0]:
            #gets new leader and mentions them
            name_string = await queue.next_user()
            msgs.append(await queue.text.send(f'{name_string} is up!'))
            await self.update_embed(queue)
            queue.last_event = datetime.datetime.now()
            
        elif emoji == reactions[1]:
            #adds user to queue
            await queue.add_user(member)
            added_string = f'Added {member.display_name}'
            msgs.append(await queue.text.send(f'{added_string}'))
            await self.update_embed(queue)

        elif emoji == reactions[2]:
            #removes users from queue
            await queue.remove_user(member)
            removed_string = f'Removed {member.display_name}'
            msgs.append(await queue.text.send(f'{removed_string}'))
            await self.update_embed(queue)

        elif emoji == reactions[3]:
            #forces queue to update based on voice channel
            await self.update_embed(queue)

        elif emoji == reactions[4]:
            #shuffles queue
            await queue.shuffle_queue()
            msgs.append(await queue.text.send(f'Queue Shuffled!'))
            await self.update_embed(queue)

        elif emoji == reactions[5]:
            #deletes queue
            del server_handler[reaction.message.guild.id] 
            msgs.append(await reaction.message.channel.send('Ended queue, see you next time!'))
            await self.bot.change_presence(activity=discord.Game(f"{'{'}help | {len(server_handler)} queues"))
            msgs.append(queue.embed_msg)

        else:
            pass

        #clean up
        await reaction.remove(member)
        if len(msgs) > 0:
            await self.msg_cleanup(msgs, 5)

def setup(bot):
    cog = QueueCommandCog(bot)
    bot.add_cog(cog)