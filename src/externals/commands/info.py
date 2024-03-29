import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from externals.commands.commands import base
class command(base):
    def subscribeTo(self, tree: CommandTree):
        super().subscribeTo(tree)
        @tree.command(name="info", description="When do you ord?")
        @describe(actions="What should I do?")
        @choices(actions=[
            # Choice(name='ord', value=2),
            # Choice(name='pay', value=3),
        ])
        @checks.cooldown(2.0,1.0)
        def info(interaction: discord.Interaction, actions: Choice[int]):
            pass