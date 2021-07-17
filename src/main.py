import os

from discord.ext import commands


cogs = [filename for filename in os.listdir(
    './cogs') if filename[-3::] == '.py']


client = commands.Bot(command_prefix='__')

client.remove_command('help')


if __name__ == '__main__':

    for filename in cogs:
        client.load_extension(f'cogs.{filename[:-3]}')

    TOKEN = os.environ.get('BOT_TOKEN')

    if not TOKEN:
        print('Error when trying to read BOT_TOKEN env var.')
        raise NameError("Missing env variable: BOT_TOKEN")

    print('Initialization Complete.')

    client.run(TOKEN)
