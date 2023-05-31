import typing
from internals.database.database import Database
from internals.database.queryfactory import Query
from internals.eventbus import EventBus
from internals.service_workers.event_worker import Worker 
from internals.caching.cache import Cache
from internals.api.hooks import Command_Internal_Hooks


class InternalState():
    def __init__(self) -> None:
        self.database = Database()
        self.cache = Cache()
        self.events = EventBus()
    def expose_command_hooks(self):
        return Command_Internal_Hooks(self.events)


    def start(self):
        self.cache.retrieveRecords(self.database)
        self.cache.populateCache()
        # self.worker = Worker()

