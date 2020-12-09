from os import getenv

# import discord
from discord.ext import commands

# TODO: do this in a better way
DEVS = [int(x) for x in getenv('DEVS', '').split(',')]


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.author.id in DEVS

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[bot] We have logged in as {self.bot.user}')
        # await self.bot.change_presence(
        #     activity=discord.Activity(
        #         type=discord.ActivityType.watching,
        #         name="$battle, $query STATE, $states"
        #     )
        # )

    @commands.Cog.listener()
    async def before_invoke(self, ctx):
        print(f'[command] "{ctx.author}" invoked "{ctx.command.name}" with "{ctx.message.content}"')

    @commands.command()
    async def reload(self, ctx, ext_name: str = ''):
        if not ext_name:
            await ctx.send('No extension name specified')
            return

        try:
            self.bot.reload_extension(f'commands.{ext_name}')
            await ctx.send('Reloaded!')
        except commands.errors.ExtensionNotLoaded:
            await ctx.send('Extension not loaded')


def setup(bot):
    bot.add_cog(Admin(bot))
