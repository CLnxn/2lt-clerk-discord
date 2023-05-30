import discord
from commands.commands import base
class command(base):
    def subscribe(self, tree: discord.app_commands.CommandTree):
        super().subscribe(tree)
        @tree.command()
        def ping():
            pass