# Player Queue class file
# Author: Alex Anderson
from datetime import datetime
import random
import discord

class PlayerQueue():
    def __init__(self, guild, voice, text, member_list):
        """Creates player queue for particular channel

        Args:
            guild_id (guild_obj): id of guild for current queue
            voice_id (voice_channel): id of voice channel being used to build queue
            text_id (text_channel): text channel id for posting msgs and embeds
            member_list (list): list of members for current queue  (member_obj)
        """
        super().__init__()
        self.last_event = datetime.now()
        self.guild = guild
        self.member_list = member_list
        self.voice = voice
        self.text = text
        self.embed_exists = False
        self.embed = None
        self.embed_msg = None

    ## Internal Functions ##

    def update_event(func):
        """
        updates last event with current time
        """
        async def wrapper(self, *args, **kwargs):
            await func(self, *args, **kwargs)
            self.last_event = datetime.now()
        return wrapper

    @update_event
    async def add_user(self, member):
        """Adds member to queue

        Args:
            user_id (int): user id to identify member
        """
        self.member_list.append(member)

    @update_event
    async def remove_user(self, member):
        """Removes member from queue

        Args:
            member_id (int): member to remove from queue
        """
        self.member_list.remove(member)

    @update_event
    async def next_user(self):
        """Returns next member in queue

        Returns:
            member_obj: member obj for person first in line
        """
        member = self.member_list.pop(0)
        self.member_list.append(member)

        return self.member_list[0]
    
    @update_event
    async def shuffle_queue(self):
        """
        Shuffles current queue of members
        """
        random.shuffle(self.member_list)
    
    @update_event
    async def whos_up(self):
        """Returns who is currently up


        Returns:
            member_obj: member_obj of current person at top of queue
        """
        return self.member_list[0]
        
    @update_event
    async def current_queue(self):
        """returns current list - should not be modified

        Returns:
            list: list of member_objs for current queue
        """
        return self.member_list

    @update_event
    async def update_queue(self, new_member_list):
        """Updates queue based on provided updated member list

        Args:
            new_member_list (list): member id list
        """

        #check to see if the lists have the same contents
        if set(self.member_list) == set(new_member_list):
            #if they have the same contents pass
            pass
        else:
            current_set = set(self.member_list)
            new_set = set(new_member_list)

            new_members = new_set.difference(current_set)
            depreciated_members = current_set.difference(new_set)

            remaining_members = current_set.difference(depreciated_members)
            self.member_list = list(remaining_members.add(new_members))
