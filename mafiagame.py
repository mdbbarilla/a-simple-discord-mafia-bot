import asyncio
import math
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Tuple
import discord


class AbstractRole(ABC):
    """
    Abstract class all roles in the game have to inherit from.

    Attributes:
     :param str role_name: name of the role of this object.
     :param MafiaGame game: the game which this class belongs to.
    """

    def __init__(self, role_name, game):
        self.role_name = role_name  # type: str
        self.game = game  # type: MafiaGame

    @abstractmethod
    def win_condition(self) -> Tuple[bool, bool]:
        """
        Checks if this role has won the game.
        Returns a pair of boolean signalling if this role won and if the game should end.
        """
        pass

    def __str__(self):
        return self.role_name


class MafiaRole(AbstractRole):
    """
    Implements the Mafia role, inheriting from `AbstractRole`.

    Attributes:
    :param MafiaGame game: the Game which this class belongs to.
    """

    def __init__(self, name, game):
        super(MafiaRole, self).__init__("Mafia" + name, game)

    def win_condition(self):
        if len(self.game.mafia) >= len(self.game.townies) / 2:
            return True, True
        return False, False


class TownRole(AbstractRole):
    """
    Implements the Mafia role, inheriting from `AbstractRole`.

    Attributes:
    :param MafiaGame game: the Game which this class belongs to.
    """

    def __init__(self, game):
        super(TownRole, self).__init__("Town", game)

    def win_condition(self):
        if len(self.game.mafia) == 0:
            return True, True
        return False, False


class JesterRole(AbstractRole):
    """
    Implements the Jester role, inheriting from `AbstractRole`.

    Attributes:
    :param MafiaGame game: the Game which this class belongs to.
    :param Player player: the Player who is a jester.
    """

    def __init__(self, game, player=None):
        self.player = player  # type: Player
        super(JesterRole, self).__init__("Jester", game)

    def win_condition(self):
        if not self.player.is_alive:
            return True, False
        return False, False

    def set_player(self, player):
        self.player = player


class Player:
    """
    Represents a player in the `MafiaGame`.

    A player consists of the `discord_user` that it is connected to, its `role`,
    its current status (whether dead or alive) and another `Player` that this
    player is currently voting for (to lynch or kill).

    Attributes:
    :param discord.User user: the user this Player represents.
    :param AbstractRole role: this Player's role.
    :param bool is_alive: this Player's status (if is alive in-game or not).
    :param Player votes_for: who this Player is voting for (in lynching
    or killing phases of the game.)
    :param bool is_no_lynch: if the Player is voting for no lynch or not.
    """

    def __init__(self, discord_user):
        self.user = discord_user  # type: discord.User
        self.role = None  # type: AbstractRole
        self.is_alive = True  # type: bool
        self.votes_for = None  # type: Player
        self.is_no_lynch = False  # type: bool


class MafiaGame:
    """
    Represents the entire Game and its various states.

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
    :param int no_lynch: how many no lynch votes are there currently.
    :param Dict[Player, int]: a dictionary that represents the vote tally.
    :param Dict[discord.user, Player]: maps discord users to players that represent them.
    Mainly used to check if a discord user is part of the game.
    :param discord.Channel gen_channel: the channel that game has started on.
    :param discord.Client client: the bot that handles this game.
    """

    def __init__(self):
        self.timeout = 10  # type: int
        self.is_accepting = False  # type: bool
        self.is_ongoing = False  # type: bool
        self.players = []  # type: List[Player]
        self.townies = []  # type: List[Player]
        self.mafia = []  # type: List[Player]
        self.alive = []  # type: List[Player]
        self.roles = {}  # type: Dict[str, AbstractRole]
        self.day_num = 0  # type: int
        self.day_phase = "Night"  # type: str
        self.no_lynch = 0  # type: int
        self.vote_table = {}  # type: Dict[Player, int]
        self.user_to_player = {}  # type: Dict[discord.User, Player]
        self.gen_channel = None  # type: discord.Channel
        self.client = None  # type: discord.Client

    def init_game(self):
        """
        Initializes the game.

        Initializes all variables and automatically starts accepting players.
        """
        self.is_accepting = True
        self.is_ongoing = True
        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.day_num = 0
        self.day_phase = "Night"
        self.vote_table = {}
        self.user_to_player = {}

    def end_game(self):
        """
        Ends the game.

        Initializes all variables and ends the game.
        """
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
        self.townies = []
        self.mafia = []
        self.roles = {}
        self.alive = []
        self.day_num = 0
        self.day_phase = "Night"
        self.vote_table = {}
        self.user_to_player = {}
        self.gen_channel = None

    def add_player(self, discord_user):
        """
        Adds a player to the game.
        :param discord.User discord_user: The user who joined the game.
        """
        new_player = Player(discord_user)
        self.players.append(new_player)
        self.user_to_player[discord_user] = new_player

    def kill_player(self, player: Player):
        """
        Kills a player, removing him from the `alive` list but not from the game.
        :param Player player: The player to be killed.
        """
        self.alive.remove(player)
        if player in self.townies:
            self.townies.remove(player)
        elif player in self.mafia:
            self.mafia.remove(player)
        player.is_alive = False

    def can_player_vote(self, user: discord.User):
        """
        Checks if the player can vote. A player can vote if he's in the game and he's alive.
        """
        if user not in self.user_to_player:
            return False

        player = self.user_to_player[user]  # type:Player
        if not player.is_alive:
            return False

        return True

    def make_vote_table(self):
        """
        Creates the vote table for the current players that are alive.
        """
        zeroes = [0] * len(self.alive)
        self.vote_table = dict(zip(self.alive, zeroes))
        self.no_lynch = 0

    async def check_if_day_should_progress(self, voted: Player = None):
        """
        Checks if the game should progress or not based on the current vote table. First checks if there is a person to
        be lynched or killed, then checks if the number of no_lynch votes is enough for a no lynch result.
        :param Optional[Player] voted: The player that was voted.
        """
        if voted and self.vote_table[voted] >= math.floor(len(self.vote_table) / 2) + 1:
            if self.day_phase == "Day":
                await self.send_message(self.gen_channel, "<@{}> has been lynched!".format(voted.user.id))
            else:
                await self.send_message(self.gen_channel, "<@{}> has been killed!".format(voted.user.id))
            self.kill_player(voted)
            await self.progress_day()
        elif self.no_lynch >= math.ceil(len(self.alive) / 2):
            if self.day_phase == "Day":
                await self.send_message(self.gen_channel, "The town has voted for no lynch!")
            else:
                await self.send_to_all_mafia("The mafia has voted to kill no one!")
            await self.progress_day()

    async def progress_day(self):
        """
        Progresses the day, re-initializing some of the Players' fields, and the game's no_lynch count.
        """
        if self.day_phase == "Day":
            self.day_phase = "Night"
        else:
            self.day_phase = "Day"
            self.day_num += 1
        for players in self.players:  # type: Player
            players.is_no_lynch = False
            players.votes_for = None
        self.no_lynch = 0
        self.make_vote_table()
        await self.send_message(self.gen_channel, "It is now {} {}.".format(self.day_phase, self.day_num))
        # if await self.check_win_conditions():
        #     self.end_game()

    async def check_win_conditions(self):
        for role_name, role in self.roles.items():
            is_win, is_game_end = role.win_condition()
            if is_win:
                await self.send_message(self.gen_channel, "{} won!".format(role))
                return is_game_end

    def print_votes(self):
        """
        Prints out the vote table and no lynch count to the channel.
        """
        ret = "```adoc\n"
        ret += "The votes currently are:\n"
        ret += "========================\n"
        for player, votes in self.vote_table.items():
            ret += "`{}' :({}): - ".format(player.user.name, votes)
            voted_by = []
            for p in self.vote_table:
                if p.votes_for == player:
                    voted_by.append(p.user.name)
            ret += ", ".join(voted_by) + "\n"
        ret += "`No lynch' :({}):".format(self.no_lynch)
        ret += "```"
        return ret

    async def print_alive_players(self):
        """
        Prints out all players who are still alive in the game.
        """
        ret = "The players who are alive are: "
        alive_user_ids = [p.user.id for p in self.alive]
        alive_user_id_strings = list(map("<@{}>".format, alive_user_ids))
        ret += ", ".join(alive_user_id_strings)
        await self.send_message(self.gen_channel, ret)

    async def send_message(self, channel: Union[discord.Channel, discord.User], message):
        """
        Sends a `message` to a `channel`.
        :param Union[discord.Channel, discord.User] channel: The user or channel to send the message to.
        :param str message: The string message to send.
        """
        await self.client.send_message(channel, message)

    async def send_to_all_mafia(self, message: str):
        """
        Sends a `message` to all mafias via direct messages.
        The bot will direct message everyone with the message.
        """
        for m in self.mafia:  # type: Player
            assert m.is_alive  # No, seriously, all players in this list should be alive.
            await self.send_message(m.user, message)

    async def give_roles(self):
        """
        Gives out roles to the players.

        Also handles segregating players into `mafia` and `townies` lists and
        populate the `user_to_player` dictionary.

        Finally, sends a direct message to each discord user about the details
        of their player.
        """
        await self.send_message(self.gen_channel, "Assigning roles to players.")

        self.roles = {'mafia': MafiaRole("", self), 'town': TownRole(self), 'j': JesterRole(self)}

        num_players = len(self.players)
        # num_mafia = round(num_players / 4)
        num_mafia = num_players     # for testing.
        # num_towny = num_players - num_mafia

        mafias = random.sample(self.players, num_mafia)
        townies = list(set(self.players) - set(mafias))

        if mafias:
            for m in mafias:
                m.role = self.roles['mafia']

        if townies:
            for t in townies:
                if t.user.name == "Ralphinium":
                    t.role = self.roles['j']
                    self.roles['j'].set_player(t)
                else:
                    t.role = self.roles['town']

        self.mafia = mafias
        self.townies = townies
        self.alive = self.players

        await self.send_message(self.gen_channel, "PM-ing roles to players.")

        for p in self.players:
            await self.send_message(p.user, "You are a {}.".format(str(p.role)))

        if len(self.mafia) > 1:
            for m in self.mafia:  # type: Player
                allies = self.mafia[:]
                allies.remove(m)
                allies_names = [ally.user.name for ally in allies]
                allies_message = "Your allies are {}".format(", ".join(allies_names))
                await self.send_message(m.user, allies_message)

    async def start_new_game(self, message: discord.Message):
        """
        Starts a new game!

        Takes the initial message to start the game and the channel the game
        was started on.
        """

        if self.is_ongoing:
            await self.send_message(self.gen_channel, "There is a game already ongoing!")
            return

        self.init_game()
        self.gen_channel = message.channel  # type: discord.Channel

        args = message.content.split(" ")
        if len(args) > 1:
            try:
                self.timeout = int(args[1])
            except ValueError:
                self.timeout = 0

        opening_text = 'A Mafia game has started! Players who want to join may type \':>joingame\'. Joining period ' \
                       'will last for {} seconds.'.format(self.timeout)
        await self.send_message(self.gen_channel, opening_text)

        if len(message.mentions) > 0:
            for m in message.mentions:
                if not m.bot:
                    self.add_player(m)

        await asyncio.sleep(self.timeout)  # Wait for `timeout` seconds.
        self.is_accepting = False  # Stop accepting players now.

        end_message = """Joining period has ended! The players are:\n"""
        end_message += ", ".join([p.user.name for p in self.players])
        await self.send_message(self.gen_channel, end_message)

        # if len(self.players) < 3:
        #     await self.send_message(self.gen_channel, "Not enough players!")
        #     self.end_game()
        #     return

        # Assign roles to players and notify them of their roles.
        await self.give_roles()
        await self.progress_day()

    async def vote_to_lynch(self, message: discord.Message):
        """
        Updates the vote table to reflect that `player` is voting for someone.
        :param discord.Message message: The message sent to the bot.
        """
        assert self.is_ongoing is True

        if not message.channel == self.gen_channel:  # Only vote on the channel the game was started on.
            return

        if not self.can_player_vote(message.author):
            return

        player = self.user_to_player[message.author]  # type: Player

        if len(message.mentions) < 1:
            await self.send_message(self.gen_channel, "You have to vote for someone! (Or no-lynch!)")
            return

        user_being_lynched = message.mentions[0]
        if user_being_lynched not in self.user_to_player:
            await self.send_message(self.gen_channel, "That player is not in the game.")
            return

        player_being_lynched = self.user_to_player[user_being_lynched]  # type: Player
        if not player_being_lynched.is_alive:
            await self.send_message(self.gen_channel, "You have to vote for someone alive!")
            return

        if player.is_no_lynch:
            player.is_no_lynch = False
            self.no_lynch -= 1

        if player.votes_for:
            msg = "{} changed their vote to {}!"
            self.vote_table[player.votes_for] -= 1
        else:
            msg = "{} voted for {}!"
        await self.send_message(self.gen_channel, msg.format(message.author.name, user_being_lynched.name))
        self.vote_table[player_being_lynched] += 1
        player.votes_for = player_being_lynched

        await self.send_message(self.gen_channel, self.print_votes())
        await self.check_if_day_should_progress(player_being_lynched)

    async def vote_no_lynch(self, message: discord.Message):
        """
        Updates the no_lynch counter and the player who voted for no lynch
        :param discord.Message message: The message sent to the bot.
        """
        assert self.is_ongoing is True
        print("Here!")
        if self.day_phase == "Day" and not message.channel == self.gen_channel:  # If day, must be on general channel.
            return

        if not self.can_player_vote(message.author):
            return

        player = self.user_to_player[message.author]  # type: Player
        print("Got here!")

        # Only mafia can vote during the night and they should do it using private messages.
        if self.day_phase == "Night":
            if not message.channel.is_private or player not in self.mafia:
                return

        if player.is_no_lynch:
            return

        if player.votes_for:
            self.vote_table[player.votes_for] -= 1
            player.votes_for = None

        player.is_no_lynch = True
        self.no_lynch += 1

        if self.day_phase == "Day":
            await self.send_message(self.gen_channel, "<@{}> votes no lynch!".format(player.user.id))
            await self.send_message(self.gen_channel, self.print_votes())
        else:
            await self.send_to_all_mafia("<@{}> votes no lynch!".format(player.user.id))
            await self.send_to_all_mafia(self.print_votes())

        await self.check_if_day_should_progress()

    async def vote_to_kill(self, message: discord.Message):
        """
        Updates the vote table to reflect that `player` is voting for someone.
        :param discord.Message message: The message sent to the bot.
        """
        assert self.is_ongoing is True
        if not message.channel.is_private:
            # await self.send_message("Shh, it's night time.")
            return

        if not self.can_player_vote(message.author):
            return

        player = self.user_to_player[message.author]  # type: Player

        if player not in self.mafia:
            return

        to_kill_name = message.content.split(" ")
        if len(to_kill_name) < 2:
            await self.send_message(message.author, "You have to vote for someone! (Or no-lynch!)")
            return

        user_to_kill = None
        for user in self.user_to_player:  # type: discord.User
            if user.name == to_kill_name[1]:
                user_to_kill = user

        print("Finding user.")
        if not user_to_kill:
            await self.send_message(message.author, "That player is not in the game.")
            return

        player_to_kill = self.user_to_player[user_to_kill]  # type: Player
        if not player_to_kill.is_alive:
            await self.send_message(message.author, "You have to vote for someone alive!")
            return

        if player.is_no_lynch:
            player.is_no_lynch = False
            self.no_lynch -= 1

        if player.votes_for:
            msg = "{} changed their vote to {}!"
            self.vote_table[player.votes_for] -= 1
        else:
            msg = "{} voted for {}!"
        await self.send_to_all_mafia(msg.format(message.author.name, user_to_kill.name))
        self.vote_table[player_to_kill] += 1
        player.votes_for = player_to_kill

        await self.send_to_all_mafia(self.print_votes())
        await self.check_if_day_should_progress(player_to_kill)

    async def manage(self, message: discord.Message):
        """
        Handles all the logic in the game.
        :param discord.Message message: The message sent by the author.
        """
        if message.content.startswith(":>mafia_start") and not self.is_ongoing:
            await self.start_new_game(message)

        elif message.content.startswith(":>mafia_help"):
            await self.help(message)

        if self.is_ongoing:
            if message.content.startswith(":>mafia_end"):
                self.end_game()
                await self.send_message(message.channel, "GG!")

            elif message.content.startswith(":>mafia_join"):
                if self.is_accepting and message.author not in self.user_to_player:
                    await self.send_message(self.gen_channel, "<@{}> joined the game!".format(message.author.id))
                    self.add_player(message.author)

            elif message.content.startswith(":>mafia_vote"):
                if self.day_phase == "Day":
                    await self.vote_to_lynch(message)
                else:
                    await self.vote_to_kill(message)

            elif message.content.startswith(":>mafia_nolynch"):
                await self.vote_no_lynch(message)

            elif message.content.startswith(":>mafia_alive"):
                await self.print_alive_players()

            elif self.day_phase == "Night" and message.channel.is_private:
                await self.send_to_all_mafia("<@{}>: {}".format(message.author.id, message.content[7:]))

    async def help(self, message):
        with open("help_texts/mafia_help.txt", "r") as help_file:
            help_msg = help_file.readlines()
        help_msg = "".join(help_msg)
        await self.send_message(message.author, help_msg)
