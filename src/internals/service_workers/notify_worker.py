from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from collections import deque
import logging

from internals.service_workers import base_worker
from internals.enums.enum import InternalTypes
import internals.notify.notfiable as notifiable
import internals.database.database as db
UPDATE_PERIOD_SECONDS = 20 # every 2h
DELETE_GRACE_INTERVAL_SECONDS = 5 # The interval where reminders with deadlines within it but before the delete query datetime are not deleted.   
class Worker(base_worker.Worker):
    def __init__(self, controller, database) -> None:
        super().__init__(UPDATE_PERIOD_SECONDS, isDaemon=True)
        self.controller: notifiable.NotifiableController = controller
        self.database: db.Database = database
        self.name = "notify"
    def task(self):
        # logging.info(f"{self.name} worker task started.")
        reminders = self.queryDatabase()
        queue = deque()
        DEFAULT = None
        # queue shd be sorted by ascending order of date_deadline, (increasing index)  
        for reminder in reminders:
            id = reminder[InternalTypes.ID.value]
            call_date = reminder[InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value]
            obj = {
                InternalTypes.USER_ID.value:reminder.get(InternalTypes.USER_ID.value, DEFAULT),
                InternalTypes.GUILD_ID.value:reminder.get(InternalTypes.GUILD_ID.value, DEFAULT),
                InternalTypes.CHANNEL_ID.value:reminder.get(InternalTypes.CHANNEL_ID.value, DEFAULT),
                InternalTypes.REMINDERS_SCOPE_FIELD.value:reminder.get(InternalTypes.REMINDERS_SCOPE_FIELD.value, DEFAULT),
                InternalTypes.REMINDERS_DATE_CREATED_FIELD.value:reminder.get(InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value, DEFAULT),
                InternalTypes.REMINDERS_CONTENT_FIELD.value:reminder.get(InternalTypes.REMINDERS_CONTENT_FIELD.value, DEFAULT),
                InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value:call_date
            }

            if type(call_date) != datetime:
                call_date = datetime.fromisoformat(call_date)

            queue.append((id, call_date, obj))
        if queue:
            self.controller.pushNotifications(queue)
        else:
            pass
            # logging.debug("queue is empty")
        # delete task
        self.clearDated()
        self.controller.last_queried_timestamp = datetime.now().timestamp()
        
        # logging.info(f"{self.name} worker task ended.")
    def clearDated(self):
        now = datetime.now()
        upper_bound = now - timedelta(seconds=DELETE_GRACE_INTERVAL_SECONDS)
        self.database.deleteDatedReminders(upper_bound)
    def queryDatabase(self):
        now = datetime.now()
        ts = now.timestamp()
        self.controller.last_queried_timestamp = ts
        start = now.isoformat()
        end = (now + timedelta(hours=2,minutes=20)).isoformat()
        return self.database.getDatedReminders(start, end)
        


