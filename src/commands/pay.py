import traceback
import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from commands.commands import base
from commands.exceptions.errors import CommandException, CommandErrorType
import logging
import utility.validator as validator
import utility.datetools as datetools
from datetime import datetime
import calendar
import numbers
class command(base):
    ACTIONS_TIMEOUT = 60.0
    def subscribe(self, tree: CommandTree):
        super().subscribe(tree)
        
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
                        await interaction.response.send_message(f"Your pay of ${pay} will come in Tomorrow!")
                    elif days_remain == 0:
                        await interaction.response.send_message(f"Today is your pay day. Congrats on ${pay}")
                    else:
                        await interaction.response.send_message(f"Your pay of ${pay} this month will come in {days_remain} days!")
                    return
                except:
                    await interaction.response.send_message(f"Oh no! Looks like there was an error in processing your pay day.")



            elif actions.name == 'set':
                try:
                    await self._handleSet(interaction,tree)
                except:
                    traceback.print_exc()
                    logging.error("error in handling /pay set")
                return
            elif actions.name == 'who':
                await interaction.response.send_message("Who's pay day are you curious about?")
    



    async def _handleSet(self, interaction: discord.Interaction, tree: CommandTree):
        channel = interaction.channel
        await interaction.response.send_message("Which day of the month is your payday? Please give me a number.")
        # message = await interaction.original_response()
        # await message.add_reaction("\N{THUMBS UP SIGN}")

        msg = await tree.client.wait_for(
            'message', 
            timeout=self.ACTIONS_TIMEOUT, 
            check=self.init_msg_check(channel.id,interaction.user))
        
        status, obj = datetools.isDayOfMonth(msg.content)

        if not status:
            if obj == CommandErrorType.EXCEED_DAY_OF_MONTH_EXCEPTION:
                await channel.send("Oops! Looks like you aren't getting paid this month. Please try again.")
            else:
                await channel.send("Oops! The input I received isn't quite right. Please try again.")
            return

        await channel.send("How much are you getting paid? Enter your amount (e.g. 2023.20).")

        msg = await tree.client.wait_for(
            'message', 
            timeout=self.ACTIONS_TIMEOUT, 
            check=self.init_msg_check(channel.id,interaction.user))
        
        status, obj2 = self.isPayAmount(msg.content)
        
        if not status:
            if obj2 == CommandErrorType.INVALID_FORMAT_EXCEPTION:
                await channel.send("Oops! The input I received isn't quite right. Please try again.")
            else:
                # not implemented
                await channel.send("Oops! Looks like I am unable to process your input.")
            return
        self.api.setPay(interaction.user.id, obj2, obj)
        await channel.send("Pay day set!")
        
    
    def isPayAmount(self, input) -> tuple[bool, CommandException | float]:
        return validator.isFloat(input)


    