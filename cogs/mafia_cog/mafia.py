import asyncio
import math
import random
from functools import wraps
from typing import List, Dict, Union

import discord


from .roles import AbstractRole, TownRole, MafiaRole


green = 2393392


def is_ongoing(fn):
    """
    Checks if the game is ongoing.
    """

    @wraps(fn)
    def wrapped(inst, *args, **kwargs):
        if inst.is_ongoing:
            return fn(inst, *args, **kwargs)
        raise MafiaGameHasNotStartedError("There is no game ongoing!")

    return wrapped


class MafiaGameError(Exception):
    """
    Base class for all exceptions in this module.
    """


class MafiaGameHasNotStartedError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGameHasStartedError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerNotInGameError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerAlreadyInError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerAlreadyDeadError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerCantVoteError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerAlreadyNoLynchError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGamePlayerAlreadyNoVoteError(MafiaGameError):
    def __init__(self, message):
        self.message = message


class MafiaGame:
    """
    Represents the entire Game and its various states.
    """
    def __init__(self):
        self.timeout = 10
        self.is_accepting = False
        self.is_ongoing = False

        self.players = []  # type: List[discord.User]
        self.townies = []  # type: List[discord.User]
        self.mafia = []  # type: List[discord.User]
        self.alive = []  # type: List[discord.User]

        self.roles = {}  # type: Dict[str, AbstractRole]
        self.votes = {}  # type: Dict[discord.User, List[Union(discord.User, str)]]
        self.voted_by = {}  # type: Dict[discord.User, List[discord.User]]

        self.day_num = 0
        self.day_phase = "Night"

        self.no_lynch = 0  # For ease when checking if a no lynch majority vote has occured.
        self.vote_table = {}  # type: Dict[discord.User, int]

    def init_game(self, timeout=10):
        """
        Starts a game of Mafia.

        Initializes the variables of the game and accepts players.
        """
        if self.is_ongoing:
            raise MafiaGameHasStartedError("A game is already ongoing!")
        self.timeout = timeout
        self.is_accepting = True
        self.is_ongoing = True

        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.votes = {}

        self.day_num = 1
        self.day_phase = "Day"

        self.no_lynch = 0
        self.vote_table = {}

    def end_game(self):
        """
        Ends the game.

        Re-initializes all variables and ends the game.
        """
        if not self.is_ongoing:
            raise MafiaGameHasNotStartedError("There is no game ongoing!")
        self.timeout = 10
        self.is_accepting = False
        self.is_ongoing = False

        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.votes = {}

        self.day_num = 0
        self.day_phase = "Night"

        self.no_lynch = 0
        self.vote_table = {}

    @is_ongoing
    def add_player(self, user: discord.User):
        """
        Adds the player to the game
        :param user: The user to be added.
        :returns: True if the player was successfully added, a string containing the error otherwise.
        """
        if user not in self.players:
            self.players.append(user)
            self.alive.append(user)
        else:
            raise MafiaGamePlayerAlreadyInError(f"{user} is already in.")

    @is_ongoing
    def kill_player(self, user: discord.User):
        """
        Kills the player, removing them from the alive list but not from the game.
        :param user: The user to be killed.
        :return: True if the player was successfully killed, a string containing the error otherwise.
        """
        if user not in self.players:
            raise MafiaGamePlayerNotInGameError(f"{user} is not part of the game.")
        elif user not in self.alive:
            raise MafiaGamePlayerAlreadyDeadError(f"{user} is already dead.")
        else:
            self.alive.remove(user)
            if user in self.townies:
                self.townies.remove(user)
            elif user in self.mafia:
                self.mafia.remove(user)
            return True

    @is_ongoing
    def make_vote_table(self):
        """
        Initializes the tables for voting.
        """
        self.votes = dict(zip(self.alive, [None]*len(self.alive)))
        self.vote_table = dict(zip(self.alive, [0]*len(self.alive)))
        self.voted_by = dict(zip(self.alive, [None]*len(self.alive)))
        self.no_lynch = 0

    # ***************************************************************************************
    # Boolean functions for checking.
    # ***************************************************************************************
    @is_ongoing
    def can_player_vote(self, user: discord.User) -> bool:
        """
        Checks if the player can vote.

        A player can vote if and only if he's in the game and alive.
        :param user:
        :return:
        """
        if user not in self.players or user not in self.alive:
            return False
        return True

    @is_ongoing
    def is_valid_voter(self, voter: discord.User) -> bool:
        """
        Checks if the `voter` can actually vote.
        By symmetry, this can also check if the `voter` can be voted.
        :param voter: The user to be checked.
        :return: True if the `voter` can be voted, False otherwise.
        """
        if voter in self.players or voter in self.alive:
            return True
        return False

    # ***************************************************************************************
    # Functions for Voting
    # ***************************************************************************************
    @is_ongoing
    def vote(self, voter: discord.User, votee: discord.User):
        """
        Makes the `voter` vote for the `votee` to be lynched during the day.
        :param voter: User casting the vote.
        :param votee: User being voted.
        :return: Returns true if the vote was successfully cast, returns a string containing the error otherwise.
        """

        # Only valid voters can vote, and if it's night, only valid mafia can vote.
        if not self.is_valid_voter(voter) or (self.day_phase == "Night" and voter not in self.mafia):
            raise MafiaGamePlayerCantVoteError(f"{voter} can not vote!")

        if not self.is_valid_voter(votee):
            raise MafiaGamePlayerNotInGameError(f"{votee} is not part of the game!")

        # If the voter hasn't voted for anyone yet, make a new list for his votes.
        if self.votes[voter] is None:
            self.votes[voter] = []

        # Else, if he voted no lynch previously, take away his no lynch vote.
        elif self.votes[voter][-1] == "No Lynch":
            self.no_lynch -= 1

        # Else, he's already voting for someone and we have to retract that vote.
        else:
            last_vote = self.votes[voter][-1]
            self.vote_table[last_vote] -= 1

        # Append the votee to the list of people the voter is voting for, and increment his number
        # in the vote table.
        self.votes[voter].append(votee)
        self.vote_table[votee] += 1

    @is_ongoing
    def vote_no_lynch(self, voter: discord.User):
        """
        Makes the `voter` vote for no lynch.
        :param voter: The user voting for a no lynch day.
        :return: True if the vote was successfully cast, a string containing the error otherwise.
        """

        # Only valid voters can vote, and if it's night, only valid mafia can vote.
        if not self.is_valid_voter(voter) or (self.day_phase == "Night" and voter not in self.mafia):
            raise MafiaGamePlayerCantVoteError(f"{voter} can not vote!")

        # If the player is already voting no lynch, do nothing.
        if self.votes[voter][-1] == "No Lynch":
            raise MafiaGamePlayerAlreadyNoLynchError(f"{voter} already voting for no lynch!")

        # If the player hasn't voted yet, make a new list for his vote history.
        elif self.votes[voter] is None:
            self.votes[voter] = []

        # If the player has already voted for someone, take away his previous vote.
        else:
            last_vote = self.votes[voter][-1]
            self.vote_table[last_vote] -= 1

        self.votes[voter].append("No Lynch")
        self.no_lynch += 1

    @is_ongoing
    def retract_vote(self, voter: discord.User):
        """
        Retracts the vote of the voter.
        """
        # Only valid voters can vote, and if it's night, only valid mafia can vote.
        if not self.is_valid_voter(voter) or (self.day_phase == "Night" and voter not in self.mafia):
            raise MafiaGamePlayerCantVoteError(f"{voter} can not vote!")

        # If the player is already voting for no one, do nothing.
        if self.votes[voter] is None or self.votes[voter][-1] is None:
            raise MafiaGamePlayerAlreadyNoVoteError(f"{voter} is already not voting!")

        # If the player is voting no lynch, retract that.
        elif self.votes[voter][-1] == "No Lynch":
            self.no_lynch -= 1

        # If the player has already voted for someone, take away his previous vote.
        else:
            last_vote = self.votes[voter][-1]
            self.vote_table[last_vote] -= 1

        self.votes[voter].append(None)
    # ***************************************************************************************
    # Functions for printing the current status of the game.
    # ***************************************************************************************

    @is_ongoing
    def print_vote_history(self) -> discord.Embed:
        """
        Returns an Embed detailing the vote history of the current people alive.
        """
        embed = discord.Embed(title="Vote History", color=green)
        for player, vote_history in self.votes:
            if vote_history:
                for user in vote_history:
                    if user is None:
                        history.append(f"None")
                    elif user == "No Lynch":
                        history.append("No Lynch")
                    else:
                        history.append(f"<@{user.id}>")
            else:
                history = ["None"]
            embed.add_field(name=f"<@{player.id}>", value=" -> ".join(history))
        return embed

    @is_ongoing
    def current_players(self) -> discord.Embed:
        """
        Returns an Embed of the list of players.
        """
        embed = discord.Embed(title="List of Players", color=green)
        if self.players:
            player_list = [f"<@{player.id}>" for player in self.players]
            embed.add_field(name="The players are:", value=", ".join(player_list))
        else:
            embed.add_field(name="The players are:", value="There are no players.")
        return embed
