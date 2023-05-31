from collections import deque
from internals.caching.cache import Cache
from internals.caching.records import Record
from datetime import datetime

import logging
class EventBus():
    def __init__(self) -> None:
        self.queue: deque[Record] = deque() 
        self.newRecordEventHooks = NewRecordEventHooks()


    
    def addRecord(self, record: Record):    
        self.queue.appendleft(record)
        self.newRecordEventHooks.fireEvent(record)

class GenericEventHooks():
    def __init__(self) -> None:
        self.hooks: list[function] = []
    def subscribe(self, hook: function):
        self.hooks.append(hook)
    def fireEvent(self):
        self.created_timestamp = datetime.now().timestamp()
        return
class NewRecordEventHooks(GenericEventHooks):
    def __init__(self) -> None:
        super().__init__()

    def fireEvent(self, record: Record):
        super().fireEvent()
        class NewRecordEvent():
            def __init__(self, record: Record) -> None:
                self.record = record
                
        for hook_fn in self.hooks:
            hook_fn(NewRecordEvent(record))