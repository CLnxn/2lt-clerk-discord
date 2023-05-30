from typing import Any
import discord
import logging
from commands import ord, ping, pay
from discord.flags import Intents

class AppClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.tree = discord.app_commands.CommandTree(self)
        ord.command().subscribe(self.tree)

    def list_loaded_commands(self):
        cmds = self.tree.get_commands()
        
        for cmd in cmds:
            logging.debug(f"{cmd} {cmd.name}")
    async def on_ready(self):
        try:
            await self.tree.sync()
        except:
            logging.warn('Failed to sync tree for ')
        logging.info('Logged on')
    
    