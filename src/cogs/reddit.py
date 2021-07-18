from datetime import datetime, timedelta
import logging

import discord
from discord.ext import commands, tasks

from utils import TimeHelper, MessageFormater # pylint: disable=E0401


class Reddit(commands.Cog):
    '''
    Reddit Cogs.

    For the region_times attribute, the last_call key inside each region is used
    to controll the ammount of API calls. This way, the main dictinoary also works
    as a buffer for itself, data usage.

    Attributes:
        - client: bot client
        - region_timers: (dict) Gets populated on initialization, follows the model:
            {
                'RegionName': {
                    'DateTimeObj': datetime_obj,
                    'last_call': bot server DateTimeObj of last API call.
                }
            }
        - hours_period: (int) Period (T) of hours to make API call.
    '''

    wednesday_meme_url = 'https://i.imgur.com/uIdY2xe.jpeg'
    weeknd_meme_url = 'https://www.youtube.com/watch?v=V_cnK8Cd6Ag'

    def __init__(self, client):
        self.client = client
        self.region_timers = {}

        # Constants:
        self.hours_period = 0.5

        for key in TimeHelper.regions_dict.keys():
            self.region_timers[key] = {
                'DateTimeObj': TimeHelper.time_from_region(key),
                'last_call': datetime.now()
            }

        self.check_day_meme_task.start() # pylint: disable=E1101

    @commands.Cog.listener()
    async def on_ready(self):
        '''
        Used mainly for logging and a greet for the guilds
        '''

        usr_num = sum([len(guild.members) for guild in self.client.guild])

        print(f'Logged-in on {len(self.client.guilds)} servers, at the reach of {usr_num} users')

        await self.client.change_presence(activity=discord.Game(name='tmp'))

    @commands.command(name='ping', aliases=["ping server"])
    async def ping(self, ctx):
        '''
        Pings the bot server.
        '''
        await ctx.channel.send(f"Latency: `{round(self.client.latency * 1000)}ms`")

    @commands.command(name='development', aliases=[
        'dev', 'git', 'info', 'status', '-v', '--version'])
    async def development(self, ctx):
        '''
        Replies with an embed about the current state of development.
        '''
        await ctx.channel.send(embed=MessageFormater.development())

        msg = ""
        msg += "This Bot Project is open-source! "
        msg += "Feel free to take a look at the code, report bugs, or even colaborate!"

        await ctx.channel.send(msg)

    @tasks.loop(hours=1)
    async def check_day_meme_task(self):
        '''
        Check if it is time to send a meme on the main TextChannel
        '''

        for guild in self.client.guilds:
            region_str = str(guild.region)

            dt_now = datetime.now()
            guild_now = self.region_timers[region_str]['DateTimeObj']

            # Check if API Call is needed
            call_delta = dt_now - self.region_timers[region_str]['last_call']
            call_delta_hours = call_delta.seconds//3600
            if call_delta_hours > self.hours_period:
                guild_now = TimeHelper.time_from_region(region_str)
                self.region_timers[region_str]['DateTimeObj'] = guild_now
                self.region_timers[region_str]['last_call'] = dt_now

            # Check the time on the guild server
            # Wednesday
            if guild_now.weekday() == TimeHelper.Weekdays.WEDNESDAY:
                if guild_now.time.hour == 1:
                    await MessageFormater.send_msg_in_guild(guild, Reddit.wednesday_meme_url)

            # Weeknd
            elif guild_now.weekday() == TimeHelper.Weekdays.FRIDAY:
                if guild_now.time.hour == 1:
                    await MessageFormater.send_msg_in_guild(guild, Reddit.weeknd_meme_url)

    # AUTO:
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        '''
        When any member sends a message inside a guild text-channel.
        '''
        # Cancels the request if the sender was a bot.
        if message.author.bot:
            return

        # Check if needs to enter a sub-reddit
        for word in message.content.replace(',', ' ').split(' '):
            if 'r/' in word:
                sub_name = word.split('r/')[-1]

                sub_link = f'https://www.reddit.com/r/{sub_name}'
                await message.reply(sub_link)
                # GET Request was taking too long
                # if MessageFormater.sub_exists(sub_link):
                #     await message.reply(sub_link)
                # else:
                #     await message.reply(MessageFormater.not_found(sub_link))


def setup(client):
    '''
    Cog setup.
    '''
    client.add_cog(Reddit(client))
