from typing import Optional
import discord
import logging


class PayView(discord.ui.View):

    @discord.ui.select(options=[discord.SelectOption(label='str')])
    async def payday(self, interaction: discord.Interaction, select: discord.ui.Select):
        if isinstance(select, discord.ui.Select):
            logging.debug("is instance")
        await interaction.response.send_message("payme!")
        

class OrdView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        
        self.add_item()