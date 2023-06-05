from typing import Any
import discord
import logging
from externals.commands import ord, pay
from discord.flags import Intents
from internals.api.internals import CommandApi
class AppClient(discord.Client):
    def __init__(self, *, intents: Intents, internal_hooks: CommandApi, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.tree = discord.app_commands.CommandTree(self)
        self.api = internal_hooks
        
        self.subscribeCommands()

    def subscribeCommands(self):
        ord.command(self.api).subscribe(self.tree)
        pay.command(self.api).subscribe(self.tree)

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
    
    