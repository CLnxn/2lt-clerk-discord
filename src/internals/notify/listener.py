from datetime import datetime, timedelta
import logging
import internals.notify.notfiable as notifiable
from internals.enums.enum import EventType, InternalTypes
from internals.events.events import NewRecordEvent
from internals.caching.records import Record
from internals.service_workers.notify_worker import UPDATE_PERIOD_SECONDS as NOTIFY_WORKER_PERIOD_SECONDS
from internals.service_workers.event_worker import UPDATE_PERIOD_SECONDS as UPDATE_DB_PERIOD_SECONDS, UPDATE_DURATION_DELAY_SECONDS
class ReminderListener():
    def __init__(self, controller: notifiable.NotifiableController) -> None:
        self.controller = controller
    
    def subscribeToEventBus(self):
        self.controller.state.events.subscribeToEvent(
            EventType.NEW_UPDATE_RECORD_EVENT, 
            self.onReminderUpdateRecord
        )
        self.controller.state.events.subscribeToEvent(
            EventType.NEW_DELETE_RECORD_EVENT,
            self.onReminderDeleteRecord
        )
        self.controller.state.events.subscribeToEvent(
            EventType.NEW_SET_RECORD_EVENT, 
            self.onReminderSetRecord
        )

    def onReminderDeleteRecord(self, event: NewRecordEvent):
        rec = event.record
        if not self._isReminder(rec):
            return
        matcher = rec.data.getMatcherForTable(InternalTypes.REMINDERS.value)
        hasID = InternalTypes.ID.value in matcher
        hasTempID = InternalTypes.REMINDERS_CACHE_ID_FIELD.value in matcher
        if not hasID and not hasTempID:
            logging.error(f"Unable to find reminder ID")
            return  
        logging.debug("in onReminderDeleteRecord")
        id = matcher[InternalTypes.ID.value] if hasID else matcher[InternalTypes.REMINDERS_CACHE_ID_FIELD.value]
        if id in self.controller.notif_table or id in self.controller.futures_table:
            self.controller.tryCancelTask(id)

    def onReminderUpdateRecord(self, event: NewRecordEvent):
        rec = event.record
        if not self._isReminder(rec):
            return
        cols = rec.data.getTableColumn(InternalTypes.REMINDERS.value)
        call_date_str = cols.get(InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value, None)
        if not call_date_str:
            logging.error(f"Unable to find call_date")
            return
        isLive = self.isLiveDate(call_date_str)
        if not isLive:
            return
        id = cols.get(InternalTypes.ID.value, None)
        use_temp_id = False
        # if id not set (not yet written to db), use temp_id instead
        if not id:
            id = cols.get(InternalTypes.REMINDERS_CACHE_ID_FIELD.value, None)
            use_temp_id = True

        notif = notifiable.Notifiable(cols, id, datetime.fromisoformat(call_date_str), has_temp_id=use_temp_id)
        logging.debug(f"in onReminderUpdateRecord, calling updateNofication")
        self.controller.updateNotification(id, notif)

    def onReminderSetRecord(self, event: NewRecordEvent):
        rec = event.record
        if not self._isReminder(rec):
            return
        cols = rec.data.getTableColumn(InternalTypes.REMINDERS.value)
        call_date_str = cols.get(InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value, None)
        tempID = cols.get(InternalTypes.REMINDERS_CACHE_ID_FIELD.value, None)
        if not call_date_str:
            logging.error(f"Unable to find call_date")
            return
        # check if reminder falls within 2 hrs (+edge cases), if yes add to notifiable queue cache, remove from the eventbus queue
        isLive = self.isLiveDate(call_date_str)
        if not isLive:
            return
        # attempt to remove from eventbus, if cannot => notify controller => notify_worker will query to remove from db 
        busRef = self.controller.state.events
        # check is redundant since process shd be called from a thread safe environment (lock is present on post() in eventbus)
        if busRef.getRecent().recordID == rec.recordID:
            logging.debug("record id is at pos 0 of eventbus queue")
            result = busRef.popRecent()
            logging.debug(f"pop result: {result} ")
            #TODO: handler for failed result (shdnt be possible)
            notif = notifiable.Notifiable(cols, tempID, datetime.fromisoformat(call_date_str), has_temp_id=True)
            self.controller.scheduleTaskDirect(notif)
        else:
            logging.error("Error in SET reminder listener. busRef recID not equal")
            return

    def isLiveDate(self, call_date_str: str):
        """ Returns a bool to decide if call_date should be in cache"""
        ts = self.controller.last_queried_timestamp
        last_updated = datetime.fromtimestamp(ts)
        call_date = datetime.fromisoformat(call_date_str)
        now = datetime.now()

        # check if call_date is outdated 
        if call_date < now:
            logging.error("notify deadline date has already expired.")
            return False
        
        logging.debug(f"last_updated: {last_updated} {now}")
        ds = (now - last_updated).seconds
        # implies an error with notify_worker not updating on time.
        if ds > NOTIFY_WORKER_PERIOD_SECONDS:
            raise Exception(f"timestamp interval from now cannot be less than Notify worker period. {ds} {NOTIFY_WORKER_PERIOD_SECONDS}")
        dt = timedelta(seconds=NOTIFY_WORKER_PERIOD_SECONDS)
        next_update = last_updated + dt
        # case 1 call_date in current round
        if next_update >= call_date:
            return True
        
        # case 2 call_date in next round but will not be retrieved by DB if left on the bus.
        remaining_seconds = NOTIFY_WORKER_PERIOD_SECONDS - ds
        # checks if writing to DB takes longer than the next incoming notify_worker update
        isDefaultSlower = remaining_seconds < UPDATE_DB_PERIOD_SECONDS + UPDATE_DURATION_DELAY_SECONDS
        # checks if call_date takes place in the next notify_worker query
        isInNextRound = next_update + dt >= call_date
        logging.debug(f"isLive: {isInNextRound} and {isDefaultSlower}")
        return isInNextRound and isDefaultSlower



    def _isReminder(self, record: Record):
        tables = record.data.getTableNames()
        return InternalTypes.REMINDERS.value in tables
          