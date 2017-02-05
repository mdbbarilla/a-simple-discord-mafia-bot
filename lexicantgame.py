import asyncio
import math
import discord
from typing import List

class LexicantGame:
    def __init__(self):
        self.players = []               # type: List[discord.User]
        self.word = ""                  # type: str
        self.current_player = None      # type: discord.User

    def start_game(self):
        pass