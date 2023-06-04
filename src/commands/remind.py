import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from commands.commands import base
class command(base):
    def subscribe(self, tree: discord.app_commands.CommandTree):
        super().subscribe(tree)
        @tree.command(name="remind", description="What are your reminders?")
        @describe(actions="What should I do?")
        @choices(actions=[
            Choice(name='get', value=1),
            Choice(name='set', value=2),
        ])
        @checks.cooldown(2.0,1.0)
        def remind(interaction: discord.Interaction, actions: Choice[int]):
            pass