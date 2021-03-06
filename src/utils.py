from datetime import datetime
from enum import Enum
import validators
import re

import requests

from discord import Embed, Forbidden

class Colours: # pylint: disable=R0903
    '''Colours'''
    blue = 0x0279fd
    bright_green = 0x01d277
    dark_green = 0x1f8b4c
    orange = 0xe67e22
    pink = 0xcf84e0
    purple = 0xb734eb
    soft_green = 0x68c290
    soft_orange = 0xf9cb54
    soft_red = 0xcd6d6d
    yellow = 0xf9f586


class TimeHelper: # pylint: disable=R0903
    '''
    Methods to manage time and the API calls.
    '''
    regions_dict = {
        'amsterdam': 'GMT+2::Europe/amsterdam',
        'brazil': 'GMT-3::America/Sao_Paulo',
        'dubai': 'GMT+4::Asia/Dubai',
        'eu_central': 'GMT+2',
        'eu_west': 'GMT+1',
        'europe': 'GMT+3',
        'frankfurt': 'GMT+1',
        'hongkong': 'GMT+8::Asia/Hong_Kong',
        'india': 'GMT+5',
        'japan': 'GMT+9::Asia/Tokyo',
        'london': 'GMT+1::Europe/London',
        'russian': 'GMT+3::Europe/Moscow',
        'singapore': 'GMT+8::Asia/Singapore',
        'southafrica': 'GMT+2::Africa/Johannesburg',
        'south_korea': 'GMT+9::Asia/Seoul',
        'sydney': 'GMT+10::Australia/Sydney',
        'us_central': 'GMT-6',
        'us_east': 'GMT-5',
        'us_south': 'GMT-7',
        'us_west': 'GMT-8',
    }

    class Weekdays(Enum):
        '''Weekdays to use on compare.'''
        MONDAY          = 0
        TUESDAY         = 1
        WEDNESDAY       = 2
        THURSDAY        = 3
        FRIDAY          = 4
        SATURDAY        = 5
        SUNDAY          = 6


    @staticmethod
    def time_from_region(region: str) -> datetime:
        '''
        Retrieves the time from the specified region.
        Args:
            - region (str): Region string.
        Returns:
            - curr_time (datetime obj): Current time in the region.

        Note:
            datetime_obj.week() returns int where Monday is 0 and Sunday is 6.
        '''

        if region.startswith('vip_'):
            region = region[4:]

        request_url = 'http://worldtimeapi.org/api/timezone/'


        url = request_url + 'Etc/' + TimeHelper.regions_dict[region].split('::')[0]
        response = requests.get(url)

        n_requests = 1
        # don't care for extra info, just want a valid response (e.g. 2xx)
        while not str(response.status_code).startswith('2'):
            n_requests += 1 # to keep count of how many requests were needed to get a valid response
            print(f'\tERROR ON URL: "{url}"')
            print('\tSTATUS CODE: ', response.status_code, "TRY NUMBER: ", n_requests)
            response = requests.get(url)

        datetime_obj = datetime.fromisoformat(response.json()['datetime'])

        return datetime_obj


class MessageFormater:
    '''
    Methods to format messages.
    '''

    @staticmethod
    async def send_msg_in_guild(guild, msg):
        '''
        Sends message in the correct TextChannel in the guild.
        Searches guild channels from top->down until it is able to send a message.
        '''

        for channel in guild.text_channels:
            try:
                await channel.send(msg) # pylint: disable=E1142
                return
            except Forbidden:
                continue

    @staticmethod
    def sub_exists(sub_url: str) -> bool:
        '''
        Checks if a subreddit exists.
        Args:
            sub_url (str): url of the subreddit.
        Returns:
            exists (bool): True if sub exists.
        '''

        r = requests.get(sub_url)

        return r.status_code != 404


    @staticmethod
    def not_found(sub_url: str) -> str:
        '''
        # Checks if a subreddit exists.
        # Args:
        #     sub_url (str): url of the subreddit.
        # Returns:
        #     exists (bool): True if sub exists.
        '''

        msg = ""
        msg += f"I couldn't find a sub with `{'r/' + sub_url.split('r/')[-1]}`"
        return msg

    @staticmethod
    def development() -> str:
        '''
        Uses the request to check for info about the current git version.

        Args:
            None.
        Returns:
            - info (Embed obj.): Embed containing the info about current development
                state of Sebotiao.
        '''

        url = "https://api.github.com/repos/LombardiDaniel/Reddbot"

        request = requests.get(url).json()

        embed_obj = Embed(
            title=request['name'],
            url=request['html_url'],
            description=request['description'],
            color=Colours.orange
        )

        embed_obj.set_thumbnail(
            url="https://raw.githubusercontent.com/LombardiDaniel/Reddbot/master/LOGO.png"
        )

        lst_contributors = requests.get(url + '/contributors').json()
        embed_obj.add_field(
            name='Main contributors:',
            value=", ".join([contributor['login'] for contributor in lst_contributors[0:3]]),
            inline=True)

        date_time_obj = datetime.strptime(request['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        delta = datetime.now() - date_time_obj

        msg = f"{delta.seconds//3600} hours ago" if delta.days < 1 else f"{delta.days} days ago"

        embed_obj.add_field(
            name='Last Update:',
            value=msg,
            inline=True
        )

        releases = requests.get(url + '/releases').json()[0]
        embed_obj.set_footer(text=f"{releases['tag_name']}")

        return embed_obj

    @staticmethod
    def help_msg() -> str:
        '''
        Set custom help command.
        '''

        msg = ""
        msg += "The command prefix is `__` (double underdscore).\n"
        msg += "Commands:\n"
        msg += "> `__dev`  :  Shows development status.\n"
        msg += "> `__link` : Gets the link to add the bot to your server.\n"
        msg += "> `__ping` : Pings the bot server.\n"
        msg += "> `__help` : Shows this message.\n"
        msg += "> Whenever someone send a message containing `r/some_sub_name`, "
        msg += "I will reply with the link to the sub-reddit.\n"
        msg += "> I will also remind the server when it is Wednesday or when the Weeknd arrives.\n"

        return msg


def check_reddit_embed(msg: str) -> list:
    '''
    Checks for subreddits in the message.
    Args:
        msg (str): the message content.
    Returns:
        sub_list (list of str): list containing all subreddit names.
    '''

    msg = repr(msg)
    sub_list = []
    for word in re.split(',| |;|\'', msg.replace('\\', ' ').replace("'", ' ')):
        if 'r/' in word and not validators.url(word):
            sub_name = word.split('r/')[-1]
            sub_name = sub_name[0:-1] if sub_name.endswith('/') else sub_name

            sub_list.append(sub_name)

    return sub_list

memes_dict = {
    TimeHelper.Weekdays.WEDNESDAY.name: 'https://i.imgur.com/uIdY2xe.jpeg',
    TimeHelper.Weekdays.FRIDAY.name: 'https://www.youtube.com/watch?v=V_cnK8Cd6Ag',
    TimeHelper.Weekdays.SUNDAY.name: 'https://www.youtube.com/watch?v=cU1E3Bxo2ww',
}
