
import logging
import time
import typing, concurrent.futures
from concurrent.futures import Future
import internals.api.internals as internals
from datetime import datetime
from internals.service_workers.notify_worker import Worker
from collections import deque
from threading import Lock
from internals.enums.enum import InternalTypes
class Notifiable():
    def __init__(self, data, id, call_date) -> None:
        self.data = data
        self.type = InternalTypes.REMINDERS
        self.id = id
        self.call_date: datetime = call_date
        self.cancelled = False
        
class NotifiableController():
    def __init__(self, state) -> None:
        self.state: internals.InternalState = state
        self.worker = Worker(self, state.database)
        self.notif_table = {} #id:notif_obj
        self.futures_table = {} # id:fut
        self.hooks = []
        self.scheduler = concurrent.futures.ThreadPoolExecutor()
        self.last_queried_timestamp: float = 0 # represents datetime of the most recent notif_worker task 
        self.lock = Lock()
    def start(self):
        self.worker.start()
    
    def tryCancelTask(self, id):
        """Returns a bool representing if this operation was successful.
           This method removes the future reference from memory.
        """
        self.lock.acquire()
        fut: Future | None = self.futures_table.pop(id, None)
        
        try:

            if not fut:
                return False
            
            fut: Future
            if fut.done():
                self.notif_table.pop(id, None)
                return True
            
            res = fut.cancel()
            if not res:
                # manually cancel after future resolves through the attached callback 
                self.notif_table[id].cancelled = True
            
            self.lock.release()
            return res
        except Exception as err:
            # might throw key error due to unsafe access
            logging.error(f"Exception in cancelling task {err}")
            self.lock.release()
            return False
        
    def updateNotification(self, notif_id, new_notif: Notifiable):
        self.lock.acquire()
        if notif_id in self.notif_table:
            self.notif_table[notif_id] = new_notif
            self.tryCancelTask(notif_id)
            
            self.schedule(notif_id)
            self.lock.release()
            
            return True
        self.lock.release()
        return False
    def pushNotifications(self, notifs: deque[(str,datetime,typing.Any)]):
        """pushes notifs into scheduler. This method modifies notifs by removing duplicate entries."""
        self.lock.acquire()
        while notifs:
            id, call_date, notif = notifs[0]
            if id in self.notif_table:
                notifs.popleft()
                continue
            # notifs is sorted from earliest to latest. If earliest is no longer present (i.e. called, etc), later notifs will definitely not be present
            #TODO: verify correctness of above when allowing update and delete methods on call_date / date_deadine 
            break
        notifs_ref = [None]*len(notifs)

        for i, (id, call_date, notif) in enumerate(notifs):
            notifiable = Notifiable(notif, id, call_date)
            self.notif_table[id] = notifiable
            notifs_ref[i] = id
        self.lock.release()
        logging.debug(f"notif iterable: {notifs_ref}. \n Length: {len(notifs)}")
        self.scheduleTasks(notifs_ref)
        

    def scheduleTasks(self, iterables):
        for id in iterables:
            self.schedule(id)


    def scheduleTaskDirect(self, notif: Notifiable):
        if not notif.id:
            return False
        id = notif.id
        self.notif_table[id] = notif

        self.schedule(id)
        return True
    
    def schedule(self, id_key):
        """
        Schedules a future which can be referenced by id_key in the futures_table.
        Overwrites duplicate futures without cancelling. Assumes stored futures each have unique id.
        """
        fut = self.scheduler.submit(self.scheduleFuture,id_key)
        self.futures_table[id_key] = fut 
        fut.add_done_callback(self.notifyCallbacks)

    def subscribe(self, callback: typing.Callable[[Notifiable], None]):
        self.hooks.append(callback)
    #TODO: Abstract into a scheduler class
    def scheduleFuture(self, notif_id):
        if notif_id not in self.notif_table:
            return None
        notif: Notifiable = self.notif_table[notif_id]

        call_date = notif.call_date
        now = datetime.now()
        notif.ts__ = now.timestamp()
        seconds_left = (call_date - now).total_seconds()
        logging.debug(f"time to notifs: {seconds_left} seconds. \n Notif id: {notif.id}")
        time.sleep(seconds_left)
        return {"id": notif_id, "ts": now.timestamp()}
    
    def notifyCallbacks(self, notif_Future: Future[typing.Any | None]):
        self.lock.acquire()
        if not notif_Future:
            return
        result = notif_Future.result()
        if not isinstance(result, dict):
            return
        id = result.get("id", None)
        ts = result.get("ts", None)
        if not id or ts:
            return
        
        logging.debug(f"notifying id: {id}")
        # removes from local cache
        f = self.futures_table.pop(id, None)
        notif: Notifiable | None = self.notif_table.get(id, None)
        # skip if notifiable is not present or cancelled
        if not notif:
            return
        if notif.cancelled == True:
            del self.notif_table[id]
            return
        # if not cancelled but timestamp has been updated (due to updated notif), skip current
        if not notif.call_date.timestamp() == ts:
            return
        
        for hook in self.hooks:
            hook(notif)
        self.lock.release()