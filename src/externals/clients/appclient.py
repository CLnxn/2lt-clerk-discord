from typing import Any
import discord
import logging
from externals.commands import ord, pay, remind
from discord.flags import Intents
from externals.notifiers.reminder import on_reminder

from internals.api.internals import CommandApi
from internals.api.notifier import Notifier, Reminder
class AppClient(discord.Client):
    def __init__(self, *, intents: Intents, internal_hooks: CommandApi, notifier: Notifier, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.tree = discord.app_commands.CommandTree(self)
        self.notifier = notifier
        self.api = internal_hooks
        
        self.subscribeCommands()

    def subscribeCommands(self):
        ord.command(self.api).subscribeTo(self.tree)
        pay.command(self.api).subscribeTo(self.tree)
        remind.command(self.api).subscribeTo(self.tree)
    def listLoadedCommands(self):
        cmds = self.tree.get_commands()
        
        for cmd in cmds:
            logging.debug(f"{cmd} {cmd.name}")

    def subscribeNotifier(self):
        self.notifier.subscribeListener(self.on_notify)
    async def on_notify(self, obj):
        if isinstance(obj, Reminder):
            on_reminder(self.tree, obj)
    async def on_ready(self):
        try:
            await self.tree.sync()
        except:
            logging.warn('Failed to sync tree for ')
        logging.info('Logged on')
    
    