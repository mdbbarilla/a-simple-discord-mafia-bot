from abc import ABC, abstractmethod
from typing import Tuple


class AbstractRole(ABC):
    """
    This class abstracts all roles in the game.
    """
    def __init__(self, role_name, game):
        """
        :param role_name: Name of the role.
        :param game: What game this role is in.
        """
        self.role_name = role_name
        self.game = game

    @abstractmethod
    def win_condition(self) -> Tuple[bool, bool]:
        """
        Checks if a player with this role has won the game.
        Players can win without ending the game.
        :return: A pair of booleans, the first one is if the player has won,
        the second one is if the game has to end.
        """
        pass

    def __str__(self):
        return self.role_name


class MafiaRole(AbstractRole):
    """
    Implements the Mafia role.
    """

    def __init__(self, team, game):
        super().__init__("Mafia " + team, game)

    def win_condition(self):
        #TODO
        pass


class TownRole(AbstractRole):
    """
    Implements the Town/Townie/Vanilla role.
    """
    def __init__(self, game):
        super().__init__("Town", game)

    def win_condition(self):
        #TODO
        pass


