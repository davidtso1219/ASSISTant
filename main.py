from os import getenv
from discord.ext import commands


client = commands.Bot(command_prefix='?')


# Event handlers
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


extensions = [
    'commands.assist',
    'commands.server',
]

if __name__ == '__main__':
    for extension in extensions:
        client.load_extension(extension)
    client.run(getenv('TOKEN'))