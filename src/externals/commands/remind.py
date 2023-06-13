import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from externals.commands.commands import base
class command(base):
    def subscribeTo(self, tree: discord.app_commands.CommandTree):
        super().subscribeTo(tree)
        @tree.command(name="remind", description="What are your reminders?")
        @describe(actions="What should I do?")
        @choices(actions=[
            Choice(name='list', value=1),
            Choice(name='recent', value=2),
            Choice(name='set', value=3),
        ])
        @checks.cooldown(2.0,1.0)
        def remind(interaction: discord.Interaction, actions: Choice[int]):
            channel = interaction.channel
            if actions.name == 'list':
                pass