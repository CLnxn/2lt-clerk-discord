
import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from externals.commands.commands import base
from externals.utility.validator import validateDate
import externals.ui.modals.modals as modals 
import logging
from datetime import datetime
class command(base):
    ACTIONS_TIMEOUT = 60.0
    def subscribe(self, tree: CommandTree):
        super().subscribe(tree)
        
        @tree.command(name="ord", description="When do you ord?")
        @describe(actions="What should I do?")
        @choices(actions=[
            Choice(name='when', value=1),
            Choice(name='set', value=2),
            Choice(name='who', value=3)

        ])
        @checks.cooldown(2.0,1.0)
        async def ord(interaction: discord.Interaction, actions: Choice[int]):
            
            channel = interaction.channel
            if actions.name == 'when':
                # call to /when endpoints to retrieve data
                date: datetime = self.api.getORD(interaction.user.id)
                if type(date) != datetime:
                    await interaction.response.send_message("Looks like you have not set your ord date.")
                else:
                    dateStr = "{0}/{1}/{2}".format(date.day,date.month,date.year)
                    remaining_days = (date - datetime.now()).days
                    if remaining_days > 0:
                        await interaction.response.send_message(f"You will ord in {remaining_days} days on: {dateStr}!")
                    elif remaining_days == 0:
                        await interaction.response.send_message(f"{remaining_days} days to ord! ORDLO")
                    else:
                        await interaction.response.send_message(f"You orded {-remaining_days} days ago on: {dateStr}!")                    


            elif actions.name == 'set':

                ordmodal = modals.OrdModal()
                ordmodal.addSubmitHook(self._handleSet)
                await interaction.response.send_modal(ordmodal)
                
            elif actions.name == 'who':
                await interaction.response.send_message("Who's ord date are you curious about?")

    async def _handleSet(self, interaction: discord.Interaction, value):
        logging.debug(f"date val: {value}")
        validated, obj = validateDate(value)
        if not validated:
            await interaction.response.send_message("Oops! The date format seems incorrect. Do check again.")
            return
        # call to /set endpoint to set data
        self.api.setORD(interaction.user.id, obj)

        await interaction.response.send_message("ORD Date set!")