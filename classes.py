DEFAULT_TIMEOUT = 10

class Player:
    def __init__(self, name):
        self.name = name
        self.is_alive = True
        self.is_mafia = False

    def set_alive_status(status):
        self.is_alive = status

    def set_mafia_status(status):
        self.is_mafia = status

    def check():
        return {"name": self.name,
                "is_alive": self.is_alive,
                "is_mafia": self.is_mafia}

class Game:
    def __init__(self, accepting_timeout=DEFAULT_TIMEOUT):
        self.is_accepting = False
        self.is_ongoing = False
        self.timeout = accepting_timeout
        self.players = []
        self.day_num = 1
        self.day_phase = "Night"

    def stop_accepting(self):
        self.is_accepting = False

    def add_player(self, player_name):
        self.players.append(Player(player_name))

    def start_game(self):
        self.is_accepting = True
        self.is_ongoing = True
        self.players = []
        print("Game has started!")

    def end_game(self):
        self.is_accepting = False
        self.is_ongoing = False
        self.players = []
        self.timeout = DEFAULT_TIMEOUT
        print("Game has ended!")
