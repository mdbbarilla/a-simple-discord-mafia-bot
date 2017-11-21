import discord
from discord.ext import commands

import sys
import traceback

extensions = ['cogs.simple',
              'cogs.owner',
              'cogs.mafia_cog'
              ]


def get_token():
    """
    Returns the bot token for logging in.
    """
    with open("token.txt") as f:
        p = f.read()
    return p


bot = commands.Bot(command_prefix=':>', description="BakaBot!")


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    await bot.change_presence(game=discord.Game(name="BakaBot reporting for duty!", type=1))

    if __name__ == "__main__":
        for extension in extensions:
            try:
                bot.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()
        print(f'Successfully logged in!')


bot.run(get_token(), bot=True, reconnect=True)