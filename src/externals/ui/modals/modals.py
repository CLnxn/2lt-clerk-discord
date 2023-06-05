from typing import Optional
import discord
from discord import SelectOption
from discord.interactions import Interaction
from discord.utils import MISSING
from datetime import datetime

import externals.utility.datetools as datetools

import logging, traceback, typing
class PayModal(discord.ui.Modal, title="What is your pay?"):

    def __init__(self,
        *,
        title: str = MISSING,
        timeout: Optional[float] = None,
        custom_id: str = MISSING,) -> None:

        super().__init__(title=title,
                         timeout=timeout,
                         custom_id=custom_id)
        
        self.pay_amt_title = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Enter your pay details",
            required=True,
            placeholder="e.g. 69420.21"
        )
        self.pay_day_title = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Which day of the month are you getting paid?",
            required=True,
            placeholder="1-{0}".format(datetools.get_last_day_of_mth(datetime.now()))
        )
        self.add_item(self.pay_amt_title)
        self.add_item(self.pay_day_title)
        self._submithooks = []
        

    #TODO: abstract hook functionality into a parent class
    def add_submit_hook(self, hook: typing.Callable[[discord.Interaction, typing.Any, typing.Any],None]):
        self._submithooks.append(hook)

    async def on_submit(self, interaction: discord.Interaction):
        for hook in self._submithooks:
            try:
                await hook(interaction, self.pay_amt_title.value, self.pay_day_title.value)
            except:
                traceback.print_exc()
                return
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"Oops! Looks like there was an error in processing your /pay details.")

    
class OrdModal(discord.ui.Modal, title="When do you ORD?"):

  
    def __init__(
        self,
        *,
        title: str = MISSING,
        timeout: Optional[float] = None,
        custom_id: str = MISSING,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

        self.ord_date_title = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Enter your ORD date:",
            required=True,
            placeholder="DD/MM/YYYY"
        )
        
        self.add_item(self.ord_date_title)
        self._submithooks = []
        
    def add_submit_hook(self, hook: typing.Callable[[discord.Interaction, typing.Any],None]):
        self._submithooks.append(hook)

    async def on_submit(self, interaction: discord.Interaction):
        for hook in self._submithooks:
            try:
                await hook(interaction, self.ord_date_title.value)
            except:
                traceback.print_exc()
                return
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logging.error(error)
        await interaction.response.send_message(f"Oops! Looks like there was an error in processing your ORD details.")
    