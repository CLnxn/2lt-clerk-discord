
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
LATENCY_GRACE_PERIOD_SECONDS = 5 # determines how late a reminder's dateline can be before it is rejected 
class Notifiable():
    def __init__(self, data, id, call_date, has_temp_id=False) -> None:
        self.data = data
        self.type = InternalTypes.REMINDERS
        self.id = id
        self.call_date: datetime = call_date
        self.cancelled = False
        self.has_temp_id = has_temp_id
        
class NotifiableController():
    def __init__(self, state) -> None:
        self.state: internals.InternalState = state
        self.worker = Worker(self, state.database)
        self.notif_table = {} #id:notif_obj
        self.futures_table = {} # id:fut
        self.hooks = []
        self.scheduler = concurrent.futures.ThreadPoolExecutor()
        self.last_queried_timestamp: float = datetime.now().timestamp() # represents datetime of the most recent notif_worker task 
        self.lock = Lock()
    def start(self):
        self.worker.start()
    
    def tryCancelTask(self, id):
        """Returns a bool representing if this operation was successful.
           This method removes the future reference from memory.
        """
        logging.debug("tryCancelTask start")
        self.lock.acquire()
        logging.debug("in tryCancelTask lock")

        fut: Future | None = self.futures_table.pop(id, None)
        logging.debug(f"popped future with id {id} for {fut}")
        try:

            if not fut:
                self.lock.release()
                return False
            
            fut: Future
            if fut.done():
                self.notif_table.pop(id, None)
                self.lock.release()
                return True
            
            res = fut.cancel()
            logging.debug(f"cancelled future with result: {res}")
            if not res:
                logging.debug(f"failed to cancel future {fut}")
                # manually cancel after future resolves through the attached callback 
                # future is still running
                self.notif_table[id].cancelled = True
            
            self.lock.release()
            return res
        except Exception as err:
            # might throw key error due to unsafe access
            logging.error(f"Exception in cancelling task {err}")
            self.lock.release()
            return False
        
    def updateNotification(self, notif_id, new_notif: Notifiable):
        if notif_id in self.notif_table:
            self.tryCancelTask(notif_id)
            self.notif_table[notif_id] = new_notif
            
            self.schedule(notif_id)
            
            return True
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
        # logging.debug(f"notif iterable: {notifs_ref}. \n Length: {len(notifs)}")
        self.scheduleTasks(notifs_ref)
        

    def scheduleTasks(self, iterables):
        for id in iterables:
            self.schedule(id)


    def scheduleTaskDirect(self, notif: Notifiable):
        if not notif.id:
            # logging.debug("notif id is null")
            return False
        # logging.debug("called at scheduleTaskDirect")
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
        ts = now.timestamp()
        logging.debug(f"ts: {ts}")
        notif.ts__ = ts
        seconds_left = (call_date - now).total_seconds()
         
        # logging.debug(f"time to notifs: {seconds_left} seconds. \n Notif id: {notif.id}")
        if seconds_left < 0 and seconds_left > -LATENCY_GRACE_PERIOD_SECONDS:
            return {"id": notif_id, "ts": ts}

        time.sleep(seconds_left)
        return {"id": notif_id, "ts": ts}
    
    def notifyCallbacks(self, notif_Future: Future[typing.Any | None]):

        self.lock.acquire()
        if not notif_Future:
            self.lock.release()
            return
        result = notif_Future.result()
        # logging.debug(f"notify callback: {result}")
        if not isinstance(result, dict):
            self.lock.release()
            return
        id = result.get("id", None)
        ts = result.get("ts", None)
        # logging.debug(f"hello is called")

        if not id or not ts:
            self.lock.release()
            return
        
        # logging.debug(f"notifying id: {id}")
        # removes from local cache
        f = self.futures_table.pop(id, None)
        notif: Notifiable | None = self.notif_table.get(id, None)
        # skip if notifiable is not present or cancelled
        if not notif:
            logging.debug(f"notif with id {id} is empty")
            self.lock.release()
            return
        if notif.cancelled == True:
            logging.debug(f"notif with id {id} is cancelled")
            del self.notif_table[id]
            self.lock.release()
            return
        # if not cancelled but timestamp has been updated (due to updated notif), skip current
        if not notif.ts__ == ts:
            logging.debug(f"notif with id {id} does not have the same timestamp. {notif.ts__} {ts}")
            self.lock.release()
            return
        
        for hook in self.hooks:
            # logging.debug(f"calling hooks: {hook}")
            hook(notif)
        self.lock.release()