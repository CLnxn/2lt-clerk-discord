from collections import deque
import math
import logging

from internals.caching.records import Record
from internals.enums.enum import InternalMethodTypes, EventType
from internals.events.events import NewRecordEventHooks, FlushEventHooks
from internals.events.events import NewRecordEvent, FlushEvent
from internals.errors.error import LockedError


EVENTBUS_MAXSIZE = 10
class EventBus():
    def __init__(self, maxLen: int =EVENTBUS_MAXSIZE) -> None:
        self.queue: deque[Record] = deque() 
        self.isLocked = False
        self.eventsMap = self.createEventMap()
        self.hooks = self.createHookMap()
        self.registerDefaultHandlers()
        self.maxlen= maxLen
        self.flush_factr = 0.2
        self.flush_amt = math.ceil(self.flush_factr*self.maxlen)

    def createHookMap(self):
        return {
            EventType.NEW_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_GET_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_DELETE_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_UPDATE_RECORD_EVENT: NewRecordEventHooks(),
            EventType.FLUSH_EVENT: FlushEventHooks()
            }
    def createEventMap(self):
        return {
            InternalMethodTypes.GET: EventType.NEW_GET_RECORD_EVENT,
            InternalMethodTypes.DELETE: EventType.NEW_DELETE_RECORD_EVENT,
            InternalMethodTypes.UPDATE: EventType.NEW_UPDATE_RECORD_EVENT,
            }
    
    def registerDefaultHandlers(self):
        self.hooks[EventType.NEW_RECORD_EVENT].subscribe(self._onNewRecordEvent)
    
    # event chaining without additional event inheritance overhead
    def _onNewRecordEvent(self, event: NewRecordEvent):
        self.hooks[self.eventsMap[event.record.method]].fireEvent(event.record)

    def subscribeToEvent(self, eventType: EventType, handler):
        self.hooks[eventType].subscribe(handler)
            
    def post(self, record: Record):    
        if self.isLocked:
            raise LockedError(self.__class__.__name__)
        
        self.queue.appendleft(record)
        self.hooks[EventType.NEW_RECORD_EVENT].fireEvent(record)

    def lock(self):
        self.isLocked = True

    def unlock(self):
        self.isLocked = False
    # returns the first flush_amt number of Records. 
    # If this number is more than the current queue length, the queue is emptied with the pop entries returned
    # 
    def flush(self):
        if self.isLocked:
            raise LockedError(self.__class__.__name__)
        
        self.lock()
        flushed = [self.queue.pop() for i in range(min(self.flush_amt,len(self.queue)))]
        self.hooks[EventType.FLUSH_EVENT].fireEvent(FlushEvent(self))
        self.unlock()
        return flushed


