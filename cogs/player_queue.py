# Player Queue class file
# Author: Alex Anderson
from datetime import datetime
import random
import discord

class PlayerQueue():
    def __init__(self, guild_id, voice_id, text_id, member_id_list):
        """Creates player queue for particular channel

        Args:
            guild_id (int): id of guild for current queue
            voice_id (int): id of voice channel being used to build queue
            text_id (int): text channel id for posting msgs and embeds
            member_id_list (list): list of user ids for current queue (int)
        """
        super().__init__()
        self.last_event = datetime.now()
        self.guild_id = guild_id
        self.member_list = member_id_list
        self.voice_id = voice_id
        self.text_id= text_id
        self.embed_exists = False
        self.embed = None
        self.embed_msg = None

    ## Internal Functions ##

    async def update_event(self, func):
        """
        updates last event with current time
        """
        def wrapper():
            func()
            self.last_event = datetime.now()
        return wrapper

    @update_event
    async def append_user(self, member_id):
        """Adds member to queue

        Args:
            user_id (int): user id to identify member
        """
        self.member_list.append(member_id)

    @update_event
    async def remove_user(self, member_id):
        """Removes member from queue

        Args:
            member_id (int): member to remove from queue
        """
        self.member_list.remove(member_id)

    @update_event
    async def next_user(self):
        """Returns next member in queue

        Returns:
            int: member id for person first in line
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
            int: member id of current person at top of queue
        """
        return self.member_list[0]
        
    @update_event
    async def current_queue(self):
        """returns current list - should not be modified

        Returns:
            list: list of member ids for current queue
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
