from .mafiabot import MafiaGameBot


def setup(bot):
    bot.add_cog(MafiaGameBot(bot))