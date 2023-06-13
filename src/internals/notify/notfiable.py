
import logging
import time
import typing, concurrent.futures
from concurrent.futures import Future
import internals.api.internals as internals
from datetime import datetime
from internals.service_workers.notify_worker import Worker
from collections import deque
from internals.enums.enum import InternalTypes
class Notifiable():
    def __init__(self, data, id, call_date) -> None:
        self.data = data
        self.type = InternalTypes.REMINDERS
        self.id = id
        self.call_date: datetime = call_date

class NotifiableController():
    def __init__(self, state) -> None:
        self.state: internals.InternalState = state
        self.worker = Worker(self, state.database)
        self.notif_table = {} #id:notif_obj
        self.futures_table = {} # id:fut
        self.hooks = []
        self.scheduler = concurrent.futures.ThreadPoolExecutor()
    def start(self):
        self.worker.start()
    
    def pushNotifications(self, notifs: deque[(str,datetime,typing.Any)]):
        """pushes notifs into scheduler. This method modifies notifs by removing duplicate entries."""
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
        logging.debug(f"notif iterable: {notifs_ref}. \n Length: {len(notifs)}")
        self.scheduleTasks(notifs_ref)

    def scheduleTasks(self, iterables):
        for id in iterables:
            fut = self.scheduler.submit(self.scheduleFuture,id)
            self.futures_table[id] = fut # overwrites duplicate futures without cancelling. Assumes stored futures each have unique id 
            fut.add_done_callback(self.notifyCallbacks)

    def onReminderRecords(self):
        pass
    def subscribe(self, callback: typing.Callable[[Notifiable], None]):
        self.hooks.append(callback)
    #TODO: Abstract into a scheduler class
    def scheduleFuture(self, notif_id):
        if notif_id not in self.notif_table:
            return None
        notif: Notifiable = self.notif_table[notif_id]

        call_date = notif.call_date
        seconds_left = (call_date - datetime.now()).total_seconds()
        logging.debug(f"time to notifs: {seconds_left} seconds. \n Notif id: {notif.id}")
        time.sleep(seconds_left)

        return notif_id
    
    def notifyCallbacks(self, notif_id: Future[typing.Any | None]):
        logging.debug(f"notifying id: {notif_id.result()}")
        if notif_id not in self.notif_table:
            return
        
        notif: Notifiable = self.notif_table[notif_id]
        
        del self.notif_table[notif.id]

        
        for hook in self.hooks:
            hook(notif)