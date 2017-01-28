import discord
from textwrap import dedent
import mafiagame

client = discord.Client()


def get_pass():
    p = None
    with open("secret_token.txt") as f:
        p = f.read()
    return p

async def help_message(message):
    """
    PMs a list of commands to the player who asked for it.
    """
    help_msg = """Here's the list of commands you can use.
    '**:>startgame *[Optional:int]* *[Optional:mentions]***' (all users): Starts a game. If a number is given, it sets a
    timer to wait for players to join. If members are mentioned, they are automatically added to the game.
    '**:>endgame**' (all users): Ends a game that is ongoing.
    '**:>vote**' (all users): Votes for a player (for lynching during day and killing during nights). Voting during the
    night should be done using PMs to the bot.
    '**:>nolynch**' (all users): Votes for no lynching (during days or killing during nights).
    '**:>alive**' (all users): Prints out a list of players in-game who are still alive.
    """
    await client.send_message(message.author, dedent(help_msg))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='*>help for help.'))


@client.event
async def on_message(message):
    if message.content.startswith(":>"):
        if message.content.startswith(":>exit"):
            # Turns off the bot, logging out then killing the process.
            if message.author.name != "Ralphinium":
                await client.send_message(message.channel, "You don't own me!")
                return
            await client.send_message(message.channel, "Goodbye!")
            await client.logout()

        elif message.content.startswith(':>mafia_help'):
            await help_message(message)

        elif message.content.startswith(":>startgame"):
            if not mafia.is_ongoing:
                await mafia.start_new_game(message)

        if mafia.is_ongoing:
            if message.content.startswith(":>endgame"):
                mafia.end_game()
                await client.send_message(message.channel, "GG!")

            elif message.content.startswith(":>vote"):
                if mafia.day_phase == "Day":
                    await mafia.vote_to_lynch(message)
                else:
                    await mafia.vote_to_kill(message)

            elif message.content.startswith(":>nolynch"):
                await mafia.vote_no_lynch(message)

            elif message.content.startswith(":>alive"):
                await mafia.print_alive_players()

            elif mafia.day_phase == "Night" and message.channel.is_private:
                await mafia.send_to_all_mafia("<@{}>: {}".format(message.author.id, message.content[2:]))

mafia = mafiagame.MafiaGame()
mafia.client = client

try:
    client.run(get_pass())
except KeyboardInterrupt as e:
    print("Goodbye.")
    client.logout()
