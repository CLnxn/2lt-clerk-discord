import typing
from internals.database.database import Database
from internals.database.queryfactory import Query
from internals.events.eventbus import EventBus
from internals.service_workers.event_worker import Worker 
from internals.caching.usercache import UsersCache
from internals.api.hooks import CommandApi
from internals.api.notifier import Notifier
from internals.notify.notfiable import NotifiableController


class InternalState():
    def __init__(self) -> None:
        self.database = Database()
        self.events = EventBus()
        self.cache = UsersCache(self.database)
        self.notifierController = NotifiableController(self)
    def getAPI(self):
        return CommandApi(self.events, self.cache)
    def getNotifier(self):
        return Notifier(self.notifierController)

    def start(self):
        self.cache.initCache()
        self.cache.subscribeToEventBus(self.events)
        self.worker = Worker(self)
        self.worker.start()
        # self.notifierController.start()

