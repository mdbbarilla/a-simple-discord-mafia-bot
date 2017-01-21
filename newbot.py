import asyncio
import discord
import newclasses

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
    if message.content.startswith(":>"):
        if message.content.startswith(":>exit"):
            # Turns off the bot, loging out then killing the process.
            if message.author.name != "Ralphinium":
                await client.send_message(message.channel, "You don't own me!")
                return
            await client.send_message(message.channel, "Goodbye!")
            await client.logout()

        elif message.content.startswith(":>start"):
            if not mafia.is_ongoing:

                mafia.gen_channel = message.channel
                await mafia.start_new_game(message)

mafia = newclasses.MafiaGame()
mafia.client = client

try:
    client.run(get_pass())
except KeyboardInterrupt as e:
    print("Goodbye.")
    client.logout()
