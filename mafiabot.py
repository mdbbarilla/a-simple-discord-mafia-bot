import discord
import asyncio
import math
import classes

client = discord.Client()

def get_pass():
    p = None
    with open("secret_token.txt") as f:
        p = f.read()
    return p


async def help(client, author):
    await client.send_message(author, "- *>start <num_seconds> to "
        "start a game with a given number of seconds for players to join.\n"
        "- *>join to join the game while it is still accepting players.\n"
        "- *>whoami to check your status in-game.\n"
        "- *>end_game ends the current game. (Bot owner only currently.)\n"
        "- *>exit turns the bot off. (Bot owner only currently.)")

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='*>help for help.'))

@client.event
async def on_message(message):
    if message.content.startswith("*>"):
        if message.content.startswith("*>start"):
            #Check if no game is ongoing.
            if not mafia.is_ongoing:
                #If there is an optional timeout parameter given,
                #set timeout to that.
                arg = message.content.split(" ")
                if len(arg) > 1:
                    mafia.timeout = int(arg[1])

                #Default reminder to all members of the chat at
                #the start of the game.
                await client.send_message(message.channel, "Game has started! "
                    "Players who want to join may type '*>join'. "
                    "Joining period will last for {} seconds.".format(mafia.timeout))

                #Starts the game, automatically allowing joining in the game.
                mafia.start_game()
                await asyncio.sleep(mafia.timeout)

                #Stop accepting players.
                mafia.stop_accepting()

                if len(message.mentions) >= 1:
                    for m in message.mentions:
                        mafia.add_player(m)
                #List all the players in the game.
                await client.send_message(message.channel, "Joining period has "
                "ended. The players are:")
                await client.send_message(message.channel,
                                          ", ".join([p.name for p in mafia.players]))

                #Assign roles to players.
                await client.send_message(message.channel, "Assigning roles.")
                mafia.give_roles()
                await client.send_message(message.channel, "PM-ing roles to "
                "the players.")
                for p in mafia.players:
                    await client.send_message(p.user, "You are a {}.".format(p.role))

                #Notify the mafias of the other mafias.
                for m in mafia.mafias:
                    await client.send_message(m.user, "Your teammates are: ")
                    await client.send_message(m.user, " ".join([m.name for m in mafia.mafias]))

                #Start game proper.
                await client.send_message(message.channel, "It is "
                "now {} {}.".format(mafia.day_phase, mafia.day_num))

                # if mafia.are_mafias_winning():
                #     await client.send_message(message.channel, "Mafias won!")
                #     mafia.end_game()
                #Since it is now day, create  a vote table.
                mafia.make_vote_table()
            else:
                await client.send_message(message.channel, "A game is "
                "currently ongoing.")

        elif message.content.startswith("*>vote"):
            #Check if sender is part of the game.
            if message.author.name not in [p.name for p in mafia.players]:
                await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
                return

            #Check if the game is ongoing and it is currently day phase.
            if mafia.is_ongoing and mafia.day_phase == "Day":
                #Get the lynched person.
                lynching = message.mentions[0]

                #Check if the lynched person is part of the game.
                if mafia.user_to_player[lynching] not in mafia.vote_table:
                    await client.send_message(message.channel, "You can't lynch someone who isn't in the game!")

                else:
                    #Check if lynched person is alive.
                    if mafia.user_to_player[lynching].is_alive:
                        await client.send_message(message.channel, "{} voted for {}!".format(message.author.name, lynching.name))
                        mafia.vote_table[mafia.user_to_player[lynching]] += 1

                        #Check if death happens.
                        if mafia.vote_table[mafia.user_to_player[lynching]] >= math.floor(len(mafia.vote_table)/2)+1:
                            await client.send_message(message.channel, "<@{}> has been lynched!".format(lynching.id))
                            mafia.user_to_player[lynching].is_alive = False

                            if mafia.are_townies_winning():
                                await client.send_message(message.channel, "Townies won!")
                                mafia.end_game()
                                return

                            elif mafia.are_mafias_winning():
                                await client.send_message(message.channel, "Mafias won!")
                                mafia.end_game()
                                return

                            mafia.make_vote_table()
                            mafia.day_phase = "Night"
                            await client.send_message(message.channel, "It is "
                            "now {} {}.".format(mafia.day_phase, mafia.day_num))
                    else:
                        await client.send_message(message.channel, "{} is already dead!".format(p.name))
            elif mafia.is_ongoing and mafia.day_phase == "Night":
                await client.send_message(message.channel, "No lynching during "
                "nights. Go sleep!")

        elif message.content.startswith("*>kill"):
            killer = message.author
            to_kill_name = message.content.split(" ")

            if len(to_kill_name) < 2:
                await client.send_message(message.channel, "Please specify a target.")

            if not message.channel.is_private:
                await client.send_message(message.channel, "You can't just post "
                "who you're killing like that!")
                return
            if killer not in mafia.user_to_player:
                await client.send_message(killer, "Sorry, you're not in the game, you can't do that.")
                return
            elif to_kill_name[1] not in [p.name for p in mafia.players]:
                await client.send_message(killer, "You can't kill that which is not alive.")
                return

            killer_player = mafia.user_to_player[killer]
            to_kill_player = None
            for p in mafia.players:
                if p.name == to_kill_name[1]:
                    to_kill_player = p

            if not killer_player.is_alive or not killer_player.role == "Mafia":
                await client.send_message(killer, "Sorry, you're dead, you can't do that.")
            elif not to_kill_player.is_alive:
                await client.send_message(killer, "You can't kill that which is not alive.")
            elif mafia.day_phase == "Day":
                await client.send_message(message.channel, "You can only lynch during the day.")
            else:
                mafia.vote_table[to_kill_player] += 1
                alive_mafia = [m.user for m in mafia.players if m.is_alive]
                for am in alive_mafia:
                    await client.send_message(am, "<@{}> wants to kill <@{}>!".format(killer.id, to_kill_player.user.id))

                    if mafia.vote_table[to_kill_player] >= len(alive_mafia):
                        mafia.day_phase = "Day"
                        mafia.day_num += 1
                        await client.send_message(message.channel, "It is "
                        "now {} {}.".format(mafia.day_phase, mafia.day_num))
                        await client.send_message(message.channel, "<@{}> has been died!".format(lynching.id))

                        if mafia.are_townies_winning():
                            await client.send_message(message.channel, "Townies won!")
                            mafia.end_game()
                            return

                        elif mafia.are_mafias_winning():
                            await client.send_message(message.channel, "Mafias won!")
                            mafia.end_game()
                            return

        elif message.content.startswith("*>whoami"):
            if mafia.is_ongoing:
                if message.author.name not in [p.name for p in mafia.players]:
                    await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
                    return
                found = False
                for p in mafia.players:
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
            else:
                await client.send_message(message.channel, "No ongoing game.")

        elif message.content.startswith("*>join"):
            if(mafia.is_ongoing and mafia.is_accepting):
                if message.author.name not in [p.name for p in mafia.players]:
                    await client.send_message(message.channel,
                                              "<@{}> has joined!".format(message.author.id))
                    mafia.add_player(message.author)
                else:
                    await client.send_message(message.channel,
                                              "You're already in the game!")

        elif message.content.startswith("*>exit"):
            if message.author.name != "Ralphinium":
                await client.send_message(message.channel, "You don't own me!")
                return
            await client.send_message(message.channel, "Test Mafia bot signing out.")
            await client.logout()

        elif message.content.startswith("*>end_game"):
            await client.send_message(message.channel, "Ending current game. GG!")
            mafia.end_game()

        elif message.content.startswith("*>help"):
            await help(client, message.author)

        # elif mafia.day_phase == "Night" and message.channel.is_private:
        #     #Mafia is PM-ing bot who to kill
        #     killer = message.author
        #     if killer not in mafia.user_to_player:
        #         await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
        #         return




mafia = classes.MafiaGame()
lex = classes.LexicantGame()

try:
    client.run(get_pass())
except KeyboardInterrupt as e:
    print("Goodbye.")
    client.logout()
