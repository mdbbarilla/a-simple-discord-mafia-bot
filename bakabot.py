import discord
import mafiagame

client = discord.Client()


def get_pass():
    with open("secret_token.txt") as f:
        p = f.read()
    return p

async def send_help(message):
    with open("gen_help.txt", "r") as help_file:
        help_msg = help_file.readlines()
    help_msg = "".join(help_msg)
    await client.send_message(message.author, help_msg)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name=':>mafia_help for help.'))


@client.event
async def on_message(message):
    if message.content.startswith(":>"):
        if message.content.startswith(":>exit") and message.author.name == "Ralphinium":
            await client.send_message(message.channel, "Goodbye!")
            await client.logout()

        elif message.content.startswith(":>help"):
            await client.send_message(message.channel, "I PM'd you a list of commands.")
            await send_help(message)

        elif message.content.startswith(":>mafia"):
            await mafia.manage(message)

if __name__ == "__main__":
    mafia = mafiagame.MafiaGame()
    mafia.client = client

    try:
        client.run(get_pass())
    except KeyboardInterrupt as e:
        print("Goodbye.")
        client.logout()
