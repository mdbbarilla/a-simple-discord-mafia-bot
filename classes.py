import math
import random

DEFAULT_TIMEOUT = 10

class Role():
    def __init__(self, role):
        self._role = role

    @property
    def role(self):
        return self._role

    def win_condition(self):
        pass

class Mafia(Role):
    def __init__(self):
        super(Mafia, self).__init__("Mafia")

class Town(Role):
    def __init__(self):
        super(Town, self).__init__("Townie")

class Player:
    def __init__(self, user):
        self._user = user
        self.is_alive = True
        self._role = None
        self.votes_for = None
        self.is_voting_for = None

    @property
    def name(self):
        return self._user.name

    @property
    def user(self):
        return self._user

    @property
    def role(self):
        return self._role.role

    @role.setter
    def role(self, role):
        self._role = role

class MafiaGame:
    def __init__(self, accepting_timeout=DEFAULT_TIMEOUT):
        self.is_accepting = False
        self.is_ongoing = False
        self.timeout = accepting_timeout
        self.players = []
        self.townies = []
        self.mafias = []
        self.day_num = 1
        self.day_phase = "Day"
        self.vote_table = None
        self.user_to_player = None
        self.gen_channel = None

    def set_channel(self, channel):
        self.gen_channel = channel

    def stop_accepting(self):
        self.is_accepting = False

    def add_player(self, player_user):
        self.players.append(Player(player_user))

    def start_game(self):
        self.is_accepting = True
        self.is_ongoing = True
        self.players = []
        self.townies = []
        self.mafias = []
        self.day_num = 1
        self.day_phase = "Day"
        self.vote_table = None
        self.user_to_player = None
        print("Game has started!")

    def end_game(self):
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
        self.townies = []
        self.mafias = []
        self.alive = []
        self.day_num = 1
        self.day_phase = ""
        self.vote_table = None
        self.user_to_player = None
        self.timeout = DEFAULT_TIMEOUT
        print("Game has ended!")

    def give_roles(self):
        num_players = len(self.players)
        # num_mafia = num_players
        num_mafia = math.ceil(num_players/4)
        num_towny = num_players - num_mafia

        mafias = random.sample(self.players, num_mafia)
        townies = list(set(self.players)-set(mafias))
        if mafias:
            for m in mafias:
                m.role = Mafia()
        if townies:
            for t in townies:
                t.role = Town()

        self.mafias = mafias
        self.townies = townies
        self.players = mafias + townies
        self.alive = self.players
        users = [p.user for p in self.players]
        self.user_to_player = dict(zip(users, self.players))

    def make_vote_table(self):
        alive = [p for p in self.players if p.is_alive]
        zeroes = [0] * len(alive)
        self.vote_table = dict(zip(alive, zeroes))

    def are_townies_winning(self):
        mafia_status = [m.is_alive for m in self.mafias]
        if any(mafia_status):
            return False
        else:
            return True

    def are_mafias_winning(self):
        mafia_status = [m.is_alive for m in self.mafias]
        player_status = [p.is_alive for p in self.players]

        if sum(mafia_status) >= sum(player_status)/2:
            return True
        else:
            return False

class LexicantGame:
    def __init__(self, accepting_timeout=DEFAULT_TIMEOUT):
        self.is_accepting = False
        self.is_ongoing = False
        self.timeout = accepting_timeout
        self.players = []
        self.word = ""

    def start_game(self):
        self.is_accepting = True
        self.is_ongoing = True

    def end_game(self):
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
