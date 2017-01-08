import discord
import asyncio
import random
import classes

client = discord.Client()

def get_pass():
    p = None
    with open("secret_token.txt") as f:
        p = f.read()
    return p

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='*>help for help.'))

@client.event
async def on_message(message):
    if message.content.startswith("*>start"):
        #Check if no game is ongoing.
        if not g.is_ongoing:
            #If there is an optional timeout parameter given,
            #set timeout to that.
            arg = message.content.split(" ")
            if len(arg) > 1:
                g.timeout = int(arg[1])

            #Default reminder to all members of the chat at
            #the start of the game.
            await client.send_message(message.channel, "Game has started! "
                "Players who want to join may type '*>join'. "
                "Joining period will last for {} seconds.".format(g.timeout))

            #Starts the game, automatically allowing joining in the game.
            g.start_game()
            await asyncio.sleep(g.timeout)

            #Stop accepting players.
            g.stop_accepting()

            #List all the players in the game.
            await client.send_message(message.channel, "Joining period has "
            "ended. The players are:")
            await client.send_message(message.channel,
                                      ", ".join([p.name for p in g.players]))

            #Start day 1 of the game.
            await client.send_message(message.channel, "PM-ing roles to "
            "the players.")
            await client.send_message(message.channel, "It is "
            "now {} {}.".format(g.day_phase, g.day_num))


        else:
            await client.send_message(message.channel, "A game is "
            "currently ongoing.")

    elif message.content.startswith("*>lynch"):
        if g.is_ongoing and g.day_phase == "Day":
            pass
        elif g.is_ongoing and g.day_phase == "Night":
            await client.send_message(message.channel, "No lynching during "
            "nights. Go sleep!")

    elif message.content.startswith("*>kill"):
        if not message.channel.is_private:
            await client.send_message(message.channel, "You can't just post "
            "who you're killing like that!")
        else:
            await client.send_message(message.channel, "Kill")

    elif message.content.startswith("*>whoami"):
        if g.is_ongoing:
            found = False
            for p in g.players:
                if p.name == message.author.name:
                    found = True
                    if p.is_alive:
                        if p.is_mafia:
                            await client.send_message(message.author, "You are "
                            "a mafia.")
                        else:
                            await client.send_message(message.author, "You are "
                            "a civilian.")
                    else:
                        await client.send_message(message.author, "Sorry {}, "
                        "you are dead.".format(message.author.name))
            if not found:
                await client.send_message(message.channel, "Sorry {}, you "
                "are not part of the game.".format(message.author.name))
        else:
            await client.send_message(message.channel, "No ongoing game.")

    elif message.content.startswith("*>join"):
        if(g.is_ongoing and g.is_accepting):
            await client.send_message(message.channel, "@" +
                                      message.author.name + " has joined!")
            g.add_player(message.author.name)

    elif message.content.startswith("*>exit"):
        print(message.author)
        if message.author.name != "Ralphinium":
            await client.send_message(message.channel, "You don't own me!")
            return
        await client.send_message(message.channel, "Test Mafia bot signing out.")
        await client.logout()

    elif message.content.startswith("*>end_game"):
        await client.send_message(message.channel, "Ending current game. GG!")
        g.end()

    elif message.content.startswith("*>help"):
        await client.send_message(message.author, "- *>start <num_seconds> to "
            "start a game with a given number of seconds for players to join.\n"
            "- *>join to join the game while it is still accepting players.\n"
            "- *>whoami to check your status in-game.\n"
            "- *>end_game ends the current game. (Bot owner only currently.)\n"
            "- *>exit turns the bot off. (Bot owner only currently.)")

print("Starting mafia bot.")

g = classes.Game()

try:
    client.run(get_pass())
except KeyboardInterrupt as e:
    print("Goodbye.")
    client.logout()
