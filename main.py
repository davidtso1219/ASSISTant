from os import getenv
from discord.ext import commands


client = commands.Bot(command_prefix='?')

extensions = [
    'commands.admin',
    # 'commands.assist',
    'commands.server',
    'commands.scrape',
    'commands.stats'
]

if __name__ == '__main__':
    client.remove_command('help')
    for extension in extensions:
        client.load_extension(extension)
    client.run(getenv('TOKEN'))
