from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from collections import deque
import logging

from internals.service_workers import base_worker
from internals.enums.enum import InternalTypes
import internals.notify.notfiable as notifiable
import internals.database.database as db
UPDATE_PERIOD_SECONDS = 5 # every 2h
class Worker(base_worker.Worker):
    def __init__(self, controller, database) -> None:
        super().__init__(UPDATE_PERIOD_SECONDS, isDaemon=True)
        self.controller: notifiable.NotifiableController = controller
        self.database: db.Database = database
        self.name = "notify"
    def task(self):
        logging.info(f"{self.name} worker task started.")
        reminders = self.queryDatabase()
        queue = deque()
        # queue shd be sorted by ascending order of date_deadline, (increasing index)  
        for reminder in reminders:
            id = reminder[InternalTypes.ID.value]
            call_date = reminder[InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value]
            obj = {
                InternalTypes.USER_ID.value:reminder[InternalTypes.USER_ID.value],
                InternalTypes.GUILD_ID.value:reminder[InternalTypes.GUILD_ID.value],
                InternalTypes.CHANNEL_ID.value:reminder[InternalTypes.CHANNEL_ID.value],
                InternalTypes.REMINDERS_SCOPE_FIELD.value:reminder[InternalTypes.REMINDERS_SCOPE_FIELD.value],
                InternalTypes.REMINDERS_DATE_CREATED_FIELD.value:reminder[InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value],
                InternalTypes.REMINDERS_CONTENT_FIELD.value:reminder[InternalTypes.REMINDERS_CONTENT_FIELD.value],
                InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value:call_date
            }

            if type(call_date) != datetime:
                call_date = datetime.fromisoformat(call_date)

            queue.append((id, call_date, obj))
        if queue:
            self.controller.pushNotifications(queue)
        else:
            logging.debug("queue is empty")
        logging.info(f"{self.name} worker task ended.")

    def queryDatabase(self):
        now = datetime.now()
        start = now.isoformat()
        end = (now + timedelta(hours=2,minutes=20)).isoformat()
        return self.database.getDatedReminders(start, end)
        


