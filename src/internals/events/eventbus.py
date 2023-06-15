from collections import deque
import math
import logging
from threading import Lock
from internals.caching.records import Record
from internals.enums.enum import InternalMethodTypes, EventType
from internals.events.events import NewRecordEventHooks, FlushEventHooks
from internals.events.events import NewRecordEvent, FlushEvent
from internals.errors.error import LockedError


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
        self.lck = Lock()
        
    def createHookMap(self):
        return {
            EventType.NEW_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_GET_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_DELETE_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_INSERT_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_UPDATE_RECORD_EVENT: NewRecordEventHooks(),
            EventType.NEW_SET_RECORD_EVENT: NewRecordEventHooks(),
            EventType.FLUSH_EVENT: FlushEventHooks()
            }
    def createEventMap(self):
        return {
            InternalMethodTypes.GET: EventType.NEW_GET_RECORD_EVENT,
            InternalMethodTypes.DELETE: EventType.NEW_DELETE_RECORD_EVENT,
            InternalMethodTypes.INSERT: EventType.NEW_INSERT_RECORD_EVENT,
            InternalMethodTypes.SET: EventType.NEW_SET_RECORD_EVENT,
            }
    def registerDefaultHandlers(self):
        self.hooks[EventType.NEW_RECORD_EVENT].subscribe(self._onNewRecordEvent)
    
    # event chaining without additional event inheritance overhead
    def _onNewRecordEvent(self, event: NewRecordEvent):
        if event.record.method in self.eventsMap:
            self.hooks[self.eventsMap[event.record.method]].fireEvent(event.record)

    def subscribeToEvent(self, eventType: EventType, handler):
        self.hooks[eventType].subscribe(handler)
            
    def post(self, record: Record):    
        self.lock()
        self.queue.appendleft(record)
        self.hooks[EventType.NEW_RECORD_EVENT].fireEvent(record)
        self.unlock()
        
    def getRecent(self):
        return self.queue[0]
    def popRecent(self):
        self.lock()
        if not self.queue:
            self.unlock()
            return False
        
        self.queue.popleft()
        self.unlock()
        return True
    
    def lock(self):
        self.lck.acquire()

    def unlock(self):
        self.lck.release()
    # returns the first flush_amt number of Records. 
    # If this number is more than the current queue length, the queue is emptied with the pop entries returned
    # 
    def flush(self):
        
        self.lock()
        flushed = [self.queue.pop() for i in range(min(self.flush_amt,len(self.queue)))]
        self.hooks[EventType.FLUSH_EVENT].fireEvent(FlushEvent(self))
        self.unlock()
        return flushed


