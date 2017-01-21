import math
import random
import asyncio
from abc import ABC, abstractmethod

class AbstractRole(ABC):
    """Abstract class all roles in the game have to inherit from.

    Attributes:
        role_name (str): name of the role of this object.
        game (newclasses.Game): the Game which this class belongs to.
    """

    def __init__(self, role_name, game):
        self.role_name = role_name
        self.game = game
        super(AbstractOperation, self).__init__()

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
        game (newclasses.Game): the Game which this class belongs to.
    """

    def __init__(self, name, game):
        super(MafiaRole,self).__init__("Mafia " + name, game)

    def win_condition(self):
        pass

class TownRole(AbstractRole):
    """Implements the Mafia role, inheriting from `AbstractRole`.

    Attributes:
        game (newclasses.Game): the Game which this class belongs to.
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
        user(discord.User): the user this Player represents.
        role(newclasses.AbstractRole): this Player's role.
        is_alive(bool): this Player's status (if is alive in-game or not).
        votes_for(newclasses.Player): who this Player is voting for (in lynching
        or killing phases of the game.)
    """
    def __init__(self, discord_user):
        self.user = discord_user
        self.role = None
        self.is_alive = True
        self.votes_for = None

class MafiaGame:
    """Represents the entire Game and its various states.

    Attributes:
        accepting_timeout(int): how long the game waits for new players.
        is_accepting(bool): if the game is accepting players or not.
        is_ongoing(bool): if the game is ongoing or not.
        players(list of `Player`): the list of all players in this game.
        townies(list of `Player`): the list of all townies in this game.
        mafia(list of `Player`): the list of all mafias in this game.
        alive(list of `Player`): the list of all alive players in this game.
        roles(dict of `AbstractRole`): list of all roles in this game.
        day_num(int): which day is it in the game.
        day_phase(str): if it is day or night.
        vote_table(dict): a dictionary that represents the vote tally.
        user_to_player(dict): maps discord users to players that represent them.
            mainly used to check if a discord user is part of the game.
        gen_channel(obj): the channel that game has started on.
        client(obj): the bot that handles this game.
    """
    def __init__(self):
        self.timeout = 10
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
        self.townies = []
        self.mafia = []
        self.alive = []
        self.roles = {}
        self.day_num = 1
        self.day_phase = "Day"
        self.vote_table = {}
        self.user_to_player = {}
        self.gen_channel = None
        self.client = None

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
        self.towns = []
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

    async def send_message(channel, message):
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
        self.roles = {'mafia': Mafia(""), 'town': TownRole()}

        num_players = len(self.players)
        num_mafia = round(num_players/4)
        num_towny = num_players - num_mafia

        mafias = random.sample(self.players, num_mafia)
        townie = list(set(self.players) - set(mafias))

        if mafias:
            for m in mafias:
                m.role = self.roles['mafia']

        if townie:
            for t in townie:
                t.role = self.roles['town']

        self.mafia = mafias
        self.townies = townies
        self.alive = self.players
        users = [p.user for p in self.players]
        self.user_to_player = dict(zip(users, self.players))

        for p in self.players:
            await send_message(p.user, "You are a {}.".format(str(p.role)))

        if len(self.mafia) > 1:
            for m in self.mafia:
                allies = self.mafia[:].remove(m)
                allies_message = "Your allies are {}".format(", ".join(allies))
                await send_message(allies_message)

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
            except:
                self.timeout = 0
        await asyncio.sleep(self.timeout)

        end_message = """Joining period has ended! The players are:\n"""
        end_message += ", ".join([p.user.name])
