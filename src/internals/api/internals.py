import typing
from internals.database.database import Database
from internals.database.queryfactory import Query
from internals.events.eventbus import EventBus
from internals.service_workers.event_worker import Worker 
from internals.caching.cache import Cache
from internals.api.hooks import Command_Internal_Hooks


class InternalState():
    def __init__(self) -> None:
        self.database = Database()
        self.events = EventBus()
        self.cache = Cache(self.database)
    def expose_command_hooks(self):
        return Command_Internal_Hooks(self.events, self.cache)


    def start(self):
        self.cache.initialiseCache()
        self.cache.subscribeToEventBus(self.events)
        self.worker = Worker(self)
        self.worker.start_working()

