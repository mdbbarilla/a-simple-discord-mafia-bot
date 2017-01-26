import random
import asyncio
import discord
from abc import ABC, abstractmethod
from typing import List, Dict


class AbstractRole(ABC):
    """Abstract class all roles in the game have to inherit from.

    Attributes:
     :param str role_name: name of the role of this object.
     :param Game game: the Game which this class belongs to.
    """

    def __init__(self, role_name, game):
        self.role_name = role_name  # type: str
        self.game = game            # type: MafiaGame

    @abstractmethod
    def win_condition(self):
        """Checks if this role has won the game.
        """
        pass

    def __str__(self):
        return self.role_name


class MafiaRole(AbstractRole):
    """Implements the Mafia role, inheriting from `AbstractRole`.

    Attributes:
    :param Game game: the Game which this class belongs to.
    """

    def __init__(self, name, game):
        super(MafiaRole, self).__init__("Mafia " + name, game)

    def win_condition(self):
        pass


class TownRole(AbstractRole):
    """Implements the Mafia role, inheriting from `AbstractRole`.

    Attributes:
    :param Game game: the Game which this class belongs to.
    """

    def __init__(self, game):
        super(TownRole, self).__init__("Town", game)

    def win_condition(self):
        pass


class Player:
    """Represents a player in the `Game`.

    A player consists of the `discord_user` that it is connected to, its `role`,
    its current status (whether dead or alive) and another `Player` that this
    player is currently voting for (to lynch or kill).

    Attributes:
    :param discord.User user: the user this Player represents.
    :param AbstractRole role: this Player's role.
    :param bool is_alive: this Player's status (if is alive in-game or not).
    :param Player votes_for: who this Player is voting for (in lynching
    or killing phases of the game.)
    """

    def __init__(self, discord_user):
        self.user = discord_user        # type: discord.User
        self.role = None                # type: AbstractRole
        self.is_alive = True            # type: bool
        self.votes_for = None           # type: Player


class MafiaGame:
    """Represents the entire Game and its various states.

    Attributes:
    :param int timeout: how long the game waits for new players.
    :param bool is_accepting: if the game is accepting players or not.
    :param bool is_ongoing: if the game is ongoing or not.
    :param List[Player] players: the list of all players in this game.
    :param List[Player] townies: the list of all townies in this game.
    :param List[Player] mafia: the list of all mafias in this game.
    :param List[Player] alive: the list of all alive players in this game.
    :param Dict[str, AbstractRole]: list of all roles in this game.
    :param int day_num: which day is it in the game.
    :param str day_phase: if it is day or night.
    :param Dict[Player, int]: a dictionary that represents the vote tally.
    :param Dict[discord.user, Player]: maps discord users to players that represent them.
    Mainly used to check if a discord user is part of the game.
    :param discord.Channel gen_channel: the channel that game has started on.
        client(obj): the bot that handles this game.
    """

    def __init__(self):
        self.timeout = 10               # type: int
        self.is_accepting = False       # type: bool
        self.is_ongoing = False         # type: bool
        self.players = []               # type: List[Player]
        self.townies = []               # type: List[Player]
        self.mafia = []                 # type: List[Player]
        self.alive = []                 # type: List[Player]
        self.roles = {}                 # type: Dict[str, AbstractRole]
        self.day_num = 1                # type: int
        self.day_phase = "Day"          # type: str
        self.vote_table = {}            # type: Dict[Player, int]
        self.user_to_player = {}        # type: Dict[discord.User, Player]
        self.gen_channel = None         # type: discord.Channel
        self.client = None              # type: discord.Client

    def init_game(self):
        """Initializes the game.

        Initializes all variables and automatically starts accepting players.
        """
        self.is_accepting = True
        self.is_ongoing = True
        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.day_num = 1
        self.day_phase = "Day"
        self.vote_table = {}
        self.user_to_player = {}

    def end_game(self):
        """Ends the game.

        Initializes all variables and ends the game.
        """
        self.is_accepting = True
        self.is_ongoing = True
        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.alive = []
        self.day_num = 1
        self.day_phase = "Day"
        self.vote_table = {}
        self.user_to_player = {}
        self.gen_channel = None

    def add_player(self, discord_user):
        self.players.append(Player(discord_user))

    async def send_message(self, channel, message):
        """Sends a `message` to a `channel`.
        """
        await self.client.send_message(channel, message)

    async def give_roles(self):
        """Gives out roles to the players.

        Also handles segregating players into `mafia` and `townies` lists and
        populate the `user_to_player` dictionary.

        Finally, sends a direct message to each discord user about the details
        of their player.
        """
        self.roles = {'mafia': MafiaRole("", self), 'town': TownRole(self)}

        num_players = len(self.players)
        num_mafia = round(num_players / 4)
        # num_towny = num_players - num_mafia

        mafias = random.sample(self.players, num_mafia)
        townies = list(set(self.players) - set(mafias))

        if mafias:
            for m in mafias:
                m.role = self.roles['mafia']

        if townies:
            for t in townies:
                t.role = self.roles['town']

        self.mafia = mafias
        self.townies = townies
        self.alive = self.players
        users = [p.user for p in self.players]
        self.user_to_player = dict(zip(users, self.players))

        for p in self.players:
            await self.send_message(p.user, "You are a {}.".format(str(p.role)))

        if len(self.mafia) > 1:
            for m in self.mafia:
                allies = self.mafia[:]
                allies.remove(m)
                allies_names = [ally.user.name for ally in allies]
                allies_message = "Your allies are {}".format(", ".join(allies_names))
                await self.send_message(self.gen_channel, allies_message)

    async def start_new_game(self, message):
        """ Starts a new game!

        Takes the initial message to start the game and the channel the game
        was started on.
        """
        self.init_game()

        opening_text = """
        A Mafia game has started!
        Players who want to join may type ':>join'.
        Joining period will last for {} seconds.""".format(self.timeout)
        await self.client.send_message(self.gen_channel, opening_text)

        args = message.content.split(" ")
        if len(args) > 1:
            try:
                self.timeout = int(args[1])
            except ValueError:
                self.timeout = 0
        await asyncio.sleep(self.timeout)

        end_message = """Joining period has ended! The players are:\n"""
        end_message += ", ".join([p.user.name for p in self.players])
