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
    """
    def __init__(self):
        self.accepting_timeout = 10
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
        self.roles = []
