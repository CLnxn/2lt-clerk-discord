import discord
from discord.app_commands import checks, describe
from externals.commands.commands import base
class command(base):
    def subscribeTo(self, tree: discord.app_commands.CommandTree):
        super().subscribeTo(tree)
        @tree.command(name="ord", description="When do you ord?")
        @describe(actions="What should I do?")
        @checks.cooldown(2.0,1.0)
        def subscribe(interaction: discord.Interaction):
            pass