import discord
from discord.ext import commands

import random
import re


class SimpleCommands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="echo")
    async def echo(self, ctx, *, message: str):
        await ctx.send(message)

    @commands.command(name="roll")
    async def roll(self, ctx, *, die: str):
        """
        Rolls a die with the format `x`d`y` + `z` where `x` is the number of dice to be rolled,
        `y` is the number of sides of all the dice and `z` is a constant we add to the total of the rolls.
        """
        matches = re.match(r'^(\d*)d(\d+)(?:\s*[+](\d+))?', die)

        if matches:
            num_dice = 1 if not matches.group(1) else int(matches.group(1))
            num_sides = int(matches.group(2))
            add = 0 if not matches.group(3) else int(matches.group(3))
            rolls = [random.randint(1, num_sides) for i in range(num_dice)]
            total = sum(rolls) + add
            embed = discord.Embed(description=f'You rolled the dice! You got **{total}**.')
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"Wrong format: {die}.")


def setup(bot):
    bot.add_cog(SimpleCommands(bot))
