from collections import deque
from internals.caching.records import Record
import math
import logging

from internals.caching.records import Record
from internals.enums.enum import InternalMethodTypes, EventType
from internals.events.events import NewRecordEventHooks, NewRecordEvent

EVENTBUS_MAXSIZE = 10
class EventBus():
    def __init__(self, maxLen: int =EVENTBUS_MAXSIZE) -> None:
        self.queue: deque[Record] = deque() 
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
        self.hooks[self.eventsMap[event.record.type]].fireEvent(event.record)

    def subscribeToEvent(self, eventType: EventType, handler):
        self.hooks[eventType].subscribe(handler)
            
    def addRecord(self, record: Record):    
        self.queue.appendleft(record)
        self.hooks[EventType.NEW_RECORD_EVENT].fireEvent(record)

    # returns the first flush_amt number of Records. 
    # If this number is more than the current queue length, the queue is emptied with the pop entries returned
    # currently not thread safe
    def flush(self):
        return [self.queue.pop() for i in range(min(self.flush_amt,len(self.queue)))]



