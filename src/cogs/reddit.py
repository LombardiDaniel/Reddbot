from datetime import datetime
import validators
import re

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
        - meme_hour: (int) Time of day in 24h format to send the memes.
    '''

    wednesday_meme_url = 'https://i.imgur.com/uIdY2xe.jpeg'
    weeknd_meme_url = 'https://www.youtube.com/watch?v=V_cnK8Cd6Ag'

    def __init__(self, client):
        self.client = client
        self.region_timers = {}

        # Constants:
        self.hours_period = 0.5
        self.meme_hour = 12

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

        # Does not work since intents are currently disabled.
        usr_num = sum([len(guild.members) for guild in self.client.guilds])

        print(f'Logged-in on {len(self.client.guilds)} servers, at the reach of {usr_num} users')

        await self.client.change_presence(activity=discord.Activity(
            name=' cool memes | __help',
            type=discord.ActivityType.watching
            ))

    @commands.command(name='ping', aliases=["ping server"])
    async def ping(self, ctx):
        '''
        Pings the bot server.
        '''
        await ctx.channel.send(f"Latency: `{round(self.client.latency * 1000)}ms`")

    @commands.command(name='development', aliases=[
        'dev', 'git', 'info', 'status'])
    async def development(self, ctx):
        '''
        Replies with an embed about the current state of development.
        '''
        await ctx.channel.send(embed=MessageFormater.development())

        msg = ""
        msg += "This Bot Project is open-source! "
        msg += "Feel free to take a look at the code, report bugs, or even colaborate!"

        await ctx.channel.send(msg)

    @commands.command(name='help', aliases=['h'])
    async def help(self, ctx):
        '''
        Replies with the help command.
        '''
        await ctx.channel.send(MessageFormater.help_msg())

    @commands.command(name='link', aliases=['url'])
    async def link(self, ctx):
        '''
        Replies with the bot link.
        '''
        await ctx.channel.send("> https://discord.com/oauth2/authorize?client_id=865960918243999784&permissions=3072&scope=bot")

    @tasks.loop(hours=1)
    async def check_day_meme_task(self):
        '''
        Check if it is time to send a meme on the main TextChannel.
        '''

        for guild in self.client.guilds:
            region_str = str(guild.region)

            dt_now = datetime.now()
            guild_now = self.region_timers[region_str]['DateTimeObj']

            # Check if API Call is needed
            call_delta = dt_now - self.region_timers[region_str]['last_call']
            call_delta_hours = call_delta.seconds / 3600
            if call_delta_hours > self.hours_period:
                guild_now = TimeHelper.time_from_region(region_str)
                self.region_timers[region_str]['DateTimeObj'] = guild_now
                self.region_timers[region_str]['last_call'] = dt_now


            # Check the time on the guild server
            # Wednesday
            if guild_now.weekday() == TimeHelper.Weekdays.WEDNESDAY.value:
                if guild_now.now().hour == self.meme_hour:
                    await MessageFormater.send_msg_in_guild(guild, Reddit.wednesday_meme_url)

            # Weeknd
            if guild_now.weekday() == TimeHelper.Weekdays.FRIDAY.value:
                if guild_now.now().hour == self.meme_hour:
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
        for word in re.split('\n|\t|,| |;', message.content):
            if 'r/' in word and not validators.url(word):
                sub_name = word.split('r/')[-1]
                sub_name = sub_name[0:-1] if sub_name.endswith('/') else sub_name

                sub_link = f'https://www.reddit.com/r/{sub_name}/'
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
