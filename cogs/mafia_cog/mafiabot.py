import asyncio


from discord.ext import commands


from .mafia import *

green = 2393392
red = 0xcc0000


class MafiaGameBot:
    def __init__(self, bot):
        self.bot = bot
        self.game = MafiaGame()     # type: MafiaGame

    # ***************************************************************************************
    # Commands for controlling the game.
    # ***************************************************************************************
    @commands.command(name="mafia_start")
    async def start_game(self, ctx: commands.Context, *, timeout: int):
        try:
            self.game.init_game(timeout)

        except MafiaGameHasStartedError as e:
            embed = discord.Embed(description="There is a game already ongoing! Finish that game first before "
                                              "starting a new game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else: # No error has occurred, so we will continue with the game.
            embed = discord.Embed(description=f"The game has started! There will be a timeout of **{timeout}** seconds "
                                              f"for players to join the game.\n"
                                              f"Players who want to join may type `:>join`.",
                                  color=green)
            await ctx.send(embed=embed)

            # Wait for the timeout.
            await asyncio.sleep(timeout)
            self.game.is_accepting = False

            # Timeout has ended.
            await ctx.send(embed=discord.Embed(description="The joining period has ended.", color=green))

            # List of players.
            players = self.game.current_players()
            await ctx.send(embed=players)

    @commands.command(name="mafia_end")
    @commands.is_owner()
    async def end_game(self, ctx: commands.Context):
        try:
            self.game.end_game()
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"The game has ended!",
                                  color=green)
            await ctx.send(embed=embed)

    # ***************************************************************************************
    # Commands for adding players.
    # ***************************************************************************************
    @commands.command(name="mafia_join", aliases=["join", "enter"])
    async def join_game(self, ctx: commands.Context):
        try:
            user = ctx.author   # type: discord.User
            self.game.add_player(user)
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerAlreadyInError as e:
            print(e)
        else:
            embed = discord.Embed(description=f"<@{user.id}> has joined the game!",
                                  color=green)
            await ctx.send(embed=embed)

    @commands.command(name="force_join", aliases=["fj"])
    async def force_join_game(self, ctx: commands.Context):
        mentions = ctx.message.mentions
        if mentions:
            added = []
            rejected = []
            for mention in mentions:
                try:
                    self.game.add_player(mention)
                except MafiaGameHasNotStartedError as e:
                    embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                          color=red)
                    print(e)
                    await ctx.send(embed=embed)
                    break
                except MafiaGamePlayerAlreadyInError as e:
                    rejected.append(f"<@{mention.id}>")
                    print(e)
                    continue
                else:
                    added.append(f"<@{mention.id}>")

            if len(added) == 1:
                added_embed = discord.Embed(description=", ".join(added) + " has been added to the game!",
                                            color=green)
                await ctx.send(embed=added_embed)
            elif len(added) >= 2:
                added_embed = discord.Embed(description=", ".join(added) + " have been added to the game!",
                                            color=green)
                await ctx.send(embed=added_embed)

            if len(rejected) == 1:
                rejected_embed = discord.Embed(description=", ".join(rejected) + " is already in the game.",
                                               color=red)
                await ctx.send(embed=rejected_embed)

            elif len(rejected) >= 2:
                rejected_embed = discord.Embed(description=", ".join(rejected) + " are already in the game.",
                                               color=red)
                await ctx.send(embed=rejected_embed)

    # ***************************************************************************************
    # Commands for voting in-game.
    # ***************************************************************************************
    @commands.command(name="mafia_vote", aliases=["mafia_lynch", "mafia_kill"])
    async def vote_player(self, ctx: commands.Context, *, votee: discord.User):
        try:
            voter = ctx.author  # type: discord.User
            self.game.vote(voter, votee)
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerCantVoteError as e:
            embed = discord.Embed(description="You can't vote.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerNotInGameError as e:
            embed = discord.Embed(description="You can't vote that user.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"<@{voter.id}> is now voting for <@{votee.id}>!",
                                  color=green)
            await ctx.send(embed=embed)

    @commands.command(name="mafia_nolynch")
    async def vote_no_lynch(self, ctx: commands.Context):
        try:
            voter = ctx.author  # type: discord.User
            self.game.vote_no_lynch(voter)
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerCantVoteError as e:
            embed = discord.Embed(description="You can't vote.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerNotInGameError as e:
            embed = discord.Embed(description="You can't vote that user.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"<@{voter.id}> is now voting no lynch!",
                                  color=green)
            await ctx.send(embed=embed)

    @commands.command(name="mafia_novote")
    async def retract_vote(self, ctx: commands.Context):
        try:
            voter = ctx.author  # type: discord.User
            self.game.retract_vote(voter)
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerCantVoteError as e:
            embed = discord.Embed(description="You can't vote.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        except MafiaGamePlayerNotInGameError as e:
            embed = discord.Embed(description="You can't vote that user.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"<@{voter.id}> is now not voting!",
                                  color=green)
            await ctx.send(embed=embed)

    # ***************************************************************************************
    # Commands for seeing the status of the game.
    # ***************************************************************************************
    @commands.command(name="mafia_players")
    async def list_players(self, ctx: commands.Context):
        try:
            embed = self.game.current_players()
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command(name="mafia_vote_history")
    async def vote_history(self, ctx: commands.Context):
        try:
            embed = self.game.print_vote_history()
        except MafiaGameHasNotStartedError as e:
            embed = discord.Embed(description="There is no game ongoing. Please start a game.",
                                  color=red)
            print(e)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
