import asyncio
import math

import discord

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
            # Check if no game is ongoing.
            if not mafia.is_ongoing:
                # If there is an optional timeout parameter given,
                # set timeout to that.
                arg = message.content.split(" ")
                if len(arg) > 1:
                    mafia.timeout = int(arg[1])

                # Default reminder to all members of the chat at
                # the start of the game.
                await client.send_message(message.channel, "Game has started! Players who want to join may type "
                                                           "'*>join'. Joining period will last for {} "
                                                           "seconds.".format(mafia.timeout))

                # Starts the game, automatically allowing joining in the game.
                mafia.start_game()
                mafia.set_channel(message.channel)
                await asyncio.sleep(mafia.timeout)

                # Stop accepting players.
                mafia.stop_accepting()

                if len(message.mentions) >= 1:
                    for m in message.mentions:
                        mafia.add_player(m)
                # List all the players in the game.
                await client.send_message(message.channel, "Joining period has "
                                                           "ended. The players are:")
                await client.send_message(message.channel,
                                          ", ".join([p.name for p in mafia.players]))

                # Assign roles to players.
                await client.send_message(message.channel, "Assigning roles.")
                mafia.give_roles()
                await client.send_message(message.channel, "PM-ing roles to "
                                                           "the players.")
                for p in mafia.players:
                    await client.send_message(p.user, "You are a {}.".format(p.role))

                # Notify the mafias of the other mafias.
                for m in mafia.mafias:
                    await client.send_message(m.user, "Your teammates are: ")
                    await client.send_message(m.user, " ".join([m.name for m in mafia.mafias]))

                # Start game proper.
                await client.send_message(message.channel, "It is "
                                                           "now {} {}.".format(mafia.day_phase, mafia.day_num))

                # if mafia.are_mafias_winning():
                #     await client.send_message(message.channel, "Mafias won!")
                #     mafia.end_game()
                # Since it is now day, create  a vote table.
                mafia.make_vote_table()
            else:
                await client.send_message(message.channel, "A game is "
                                                           "currently ongoing.")

        elif message.content.startswith("*>vote"):
            # Check if sender is part of the game.
            if message.author.name not in [p.name for p in mafia.players]:
                await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
                return

            # Check if the game is ongoing and it is currently day phase.
            if mafia.is_ongoing and mafia.day_phase == "Day":
                # Get the lynched person.
                lynching = message.mentions[0]

                # Check if the lynched person is part of the game.
                if mafia.user_to_player[lynching] not in mafia.vote_table:
                    await client.send_message(message.channel, "You can't lynch someone who isn't in the game!")

                else:
                    lyncher = mafia.user_to_player[message.author]
                    lynched = mafia.user_to_player[lynching]
                    # Check if lyncher is alive.
                    if not lyncher.is_alive:
                        await client.send_message(message.channel, "You're dead!")
                        return

                    if lyncher.is_no_lynch:
                        mafia.no_lynch -= 1
                        lyncher.is_no_lynch = False

                    # Check if lynched person is alive.
                    if lynched.is_alive:
                        # Check if the lyncher has already voted.
                        if lyncher.votes_for is None:
                            await client.send_message(message.channel,
                                                      "{} voted for {}!".format(message.author.name, lynching.name))
                        else:
                            await client.send_message(message.channel,
                                                      "{} has changed their vote to {}!".format(message.author.name,
                                                                                                lynching.name))
                            mafia.vote_table[lyncher.votes_for] -= 1

                        # Update the vote table.
                        mafia.vote_table[lynched] += 1
                        lyncher.votes_for = lynched

                        # Print out votes.
                        await client.send_message(mafia.gen_channel, "The votes currently are: ")
                        current_table = ""
                        for player, votes in mafia.vote_table.items():
                            current_table += "{}({}) - ".format(player.user.name, votes)
                            voted_by = []
                            for p in mafia.vote_table:
                                if p.votes_for == player:
                                    voted_by.append(p.user.name)
                            current_table += ", ".join(voted_by)
                            current_table += "\n"
                        current_table += "No lynch({})".format(mafia.no_lynch)
                        await client.send_message(mafia.gen_channel, current_table)

                        # Check if death happens.
                        if mafia.vote_table[mafia.user_to_player[lynching]] >= math.floor(
                                        len(mafia.vote_table) / 2) + 1:
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
                                                                       "now {} {}.".format(mafia.day_phase,
                                                                                           mafia.day_num))
                    else:
                        await client.send_message(message.channel, "{} is already dead!".format(lynched.name))

            elif mafia.is_ongoing and mafia.day_phase == "Night":
                await client.send_message(message.channel, "No lynching during "
                                                           "nights. Go sleep!")

        elif message.content.startswith("*>nolynch"):
            # Check if sender is part of the game.
            if message.author.name not in [p.name for p in mafia.players]:
                await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
                return

            # Check if the game is ongoing and it is currently day phase.
            if mafia.is_ongoing and mafia.day_phase == "Day":
                lyncher = mafia.user_to_player[message.author]

                if not lyncher.is_alive:
                    await client.send_message(mafia.gen_channel, "You're dead!")
                    return

                if lyncher.votes_for:
                    mafia.vote_table[lyncher.votes_for] -= 1

                if lyncher.is_no_lynch:
                    return

                lyncher.votes_for = None
                lyncher.is_no_lynch = True
                mafia.no_lynch += 1

                await client.send_message(mafia.gen_channel, "<@{}> votes no lynch!".format(message.author.id))
                await client.send_message(mafia.gen_channel, "The votes currently are: ")
                current_table = ""
                for player, votes in mafia.vote_table.items():
                    current_table += "{}({}) - ".format(player.user.name, votes)
                    voted_by = []
                    for p in mafia.vote_table:
                        if p.votes_for == player:
                            voted_by.append(p.user.name)
                    current_table += ", ".join(voted_by)
                    current_table += "\n"
                current_table += "No lynch({})".format(mafia.no_lynch)
                await client.send_message(mafia.gen_channel, current_table)

                if mafia.no_lynch_happens():
                    await client.send_message(mafia.gen_channel, "No lynch!")
                    mafia.make_vote_table()
                    mafia.day_phase = "Night"
                    await client.send_message(message.channel, "It is "
                                                               "now {} {}.".format(mafia.day_phase, mafia.day_num))

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
                alive_mafia = [m.user for m in mafia.mafias if m.is_alive]

                if killer_player.votes_for is None:
                    mafia.vote_table[to_kill_player] += 1
                    for am in alive_mafia:
                        if am != message.author:
                            await client.send_message(am, "<@{}> wants to kill <@{}>!".format(killer.id,
                                                                                              to_kill_player.user.id))

                else:
                    mafia.vote_table[killer_player.votes_for] -= 1
                    mafia.vote_table[to_kill_player] += 1
                    for am in alive_mafia:
                        if am != message.author:
                            await client.send_message(am, "<@{}> now wants to kill <@{}>!".format(killer.id,
                                                                                                  to_kill_player.user.id))

                killer_player.votes_for = to_kill_player
                current_table = ""
                for player, votes in mafia.vote_table.items():
                    current_table += "{}({}) - ".format(player.user.name, votes)
                    voted_by = []
                    for p in mafia.vote_table:
                        if p.votes_for == player:
                            voted_by.append(p.user.name)
                    current_table += ", ".join(voted_by)
                    current_table += "\n"
                for am in alive_mafia:
                    await client.send_message(am, "The votes currently are: ")
                    await client.send_message(am, current_table)

                if mafia.vote_table[to_kill_player] >= len(alive_mafia):
                    mafia.day_phase = "Day"
                    mafia.day_num += 1
                    await client.send_message(mafia.gen_channel, "It is "
                                                                 "now {} {}.".format(mafia.day_phase, mafia.day_num))
                    await client.send_message(mafia.gen_channel, "<@{}> has died! ".format(to_kill_player.user.id))
                    to_kill_player.is_alive = False

                    mafia.make_vote_table()

                    if mafia.are_townies_winning():
                        await client.send_message(mafia.gen_channel, "Townies won!")
                        mafia.end_game()
                        return

                    elif mafia.are_mafias_winning():
                        await client.send_message(mafia.gen_channel, "Mafias won!")
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
                            if p.role == "Mafia":
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
            if (mafia.is_ongoing and mafia.is_accepting):
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

        elif mafia.day_phase == "Night" and message.channel.is_private:
            killer = message.author
            if killer not in mafia.user_to_player:
                await client.send_message(message.channel, "Sorry, you're not in the game, you can't do that.")
                return
            elif mafia.user_to_player[killer].role != "Mafia":
                await client.send_message(message.channel, "Go sleep!")
                return
            else:
                for m in mafia.mafias:
                    if m.is_alive:
                        await client.send_message(m.user, "<@{}>: {}".format(killer.id, message.content[2:]))


mafia = classes.MafiaGame()
lex = classes.LexicantGame()

try:
    client.run(get_pass())
except KeyboardInterrupt as e:
    print("Goodbye.")
    client.logout()
