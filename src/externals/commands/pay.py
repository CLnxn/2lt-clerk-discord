import traceback
import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from externals.commands.commands import base
from externals.exceptions.errors import CommandException, CommandErrorType
import logging
import externals.ui.modals.modals as modals
import externals.utility.datetools as datetools
import externals.utility.validator as validator

from datetime import datetime
class command(base):
    ACTIONS_TIMEOUT = 60.0
    def subscribeTo(self, tree: CommandTree):
        super().subscribeTo(tree)
        
        @tree.command(name="pay", description="When is your pay day?")
        @describe(actions="What should I do?")
        @choices(actions=[
            Choice(name='when', value=1),
            Choice(name='set', value=2)
        ])
        @checks.cooldown(2.0,1.0)
        async def pay(interaction: discord.Interaction, actions: Choice[int]):
            if actions.name == 'when':
                # call to /pay when endpoints to retrieve data
                try:
                    pay, payday = self.api.getPay(interaction.user.id)
                    pay = "{:.2f}".format(pay)
                    now = datetime.now()
                    
                    days_remain = datetools.getRemainingDaysInMonth(now)+payday if now.day > payday else payday-now.day
                    if days_remain == 1:
                        await interaction.response.send_message(f"Your pay of ${pay} is coming Tomorrow!")
                    elif days_remain == 0:
                        await interaction.response.send_message(f"Today is your pay day. Congrats on ${pay}")
                    else:
                        await interaction.response.send_message(f"Your pay of ${pay} is coming in {days_remain} days!")
                    return
                except:
                    await interaction.response.send_message(f"Oops! Looks like there was an error in processing your pay day.")



            elif actions.name == 'set':
                try:
                    paymodal = modals.PayModal()
                    paymodal.addSubmitHook(self._handleSet)
                    await interaction.response.send_modal(paymodal)

                except:
                    traceback.print_exc()
                    logging.error("error in handling /pay set")
                return
            elif actions.name == 'who':
                await interaction.response.send_message("Who's pay day are you curious about?")
    



    async def _handleSet(self, interaction: discord.Interaction, pay_amt, pay_day):
        
        status, obj = datetools.isDayOfMonth(pay_day)

        if not status:
            if obj == CommandErrorType.EXCEED_DAY_OF_MONTH_EXCEPTION:
                await interaction.response.send_message("Oops! Looks like you aren't getting paid this month. Please try again.")
            else:
                await interaction.response.send_message("Oops! The input I received isn't quite right. Please try again.")
            return
        
        status, obj2 = self.isPayAmount(pay_amt)
        
        if not status:
            if obj2 == CommandErrorType.INVALID_FORMAT_EXCEPTION:
                await interaction.response.send_message("Oops! The input I received isn't quite right. Please try again.")
            else:
                # not implemented
                await interaction.response.send_message("Oops! Looks like I am unable to process your input.")
            return
        
        self.api.setPay(interaction.user.id, obj2, obj)
        await interaction.response.send_message("Pay day set!")
        
    
    def isPayAmount(self, input) -> tuple[bool, CommandException | float]:
        return validator.isFloat(input)


    