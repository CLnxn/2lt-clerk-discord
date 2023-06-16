from datetime import datetime
from internals.events.eventbus import EventBus
from internals.caching.records import Record
from internals.caching.usercache import UsersCache
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes, InternalTypes, RemindersScope
import logging, traceback, uuid

from internals.api.notifier import Reminder
from internals.notify.notif_id_factory import NotifIDFactory
class CommandApi():
    def __init__(self, eventsQueue: EventBus, cache: UsersCache) -> None:
        self.events = eventsQueue
        self.cache = cache
    def setORD(self, user_id: int, date: datetime):
        datestr = date.isoformat()
        query = Query(mode='w')
        query.addNewTable(InternalTypes.NS.value)
        column_query = {InternalTypes.USER_ID.value: user_id, 
                        InternalTypes.NS_DATETIME_FIELD.value: datestr}
        
        query.setTableColumn(InternalTypes.NS.value, column_query)

        record = Record(InternalMethodTypes.SET, user_id, query)
        try:
            self.events.post(record)
        except Exception as err:
            return False, err
        
    def getORD(self, user_id: int):
        query = Query(mode='r', selectAll=False)
        query.addNewTable(InternalTypes.NS.value)
        column_query = [InternalTypes.NS_DATETIME_FIELD.value]
        query.setTableColumn(InternalTypes.NS.value, column_query)
        query.addMatcher(InternalTypes.NS.value, {InternalTypes.USER_ID.value: user_id})

        record = Record(InternalMethodTypes.GET, user_id, query)
        result, err = self.cache.getRecord(record)  
        try:
            logging.debug(f"result: {result}")
            date: str = result[InternalTypes.NS.value][InternalTypes.NS_DATETIME_FIELD.value] 
            # Manual input into database using mySQL will trigger True for this check. 
            # Regular setORD using discord api will return str
            if type(date) == datetime:
                logging.info("retrieved date is of type datetime.")
                return date
            date = datetime.fromisoformat(date)            
        except Exception as err:
            logging.error(f"Error in retrieving date: {err}")
            return None
        else:
            return date      
        

    def setPay(self, user_id: int, pay_amt: float, pay_dom: int):
        query = Query(mode='w')
        query.addNewTable(InternalTypes.NS.value)
        column_query = {InternalTypes.USER_ID.value: user_id, 
                        InternalTypes.NS_PAY_AMOUNT_FIELD.value: pay_amt, 
                        InternalTypes.NS_PAY_DAY_OF_MTH_FIELD.value: pay_dom}
        query.setTableColumn(InternalTypes.NS.value, column_query)
        record = Record(InternalMethodTypes.SET, user_id, query)
        try:
            self.events.post(record)
        except Exception as err:
            return False, err
        
    def getPay(self, user_id: int) -> tuple[float,int] | None:
        query = Query(mode='r', selectAll=False)
        query.addNewTable(InternalTypes.NS.value)
        column_query = [InternalTypes.NS_PAY_AMOUNT_FIELD.value,
                        InternalTypes.NS_PAY_DAY_OF_MTH_FIELD.value]
        
        query.setTableColumn(InternalTypes.NS.value, column_query)
        query.addMatcher(InternalTypes.NS.value, {InternalTypes.USER_ID.value: user_id})
        record = Record(InternalMethodTypes.GET, user_id, query)
        result, err = self.cache.getRecord(record)

        if not result:
            logging.error(f"error in getPay: {err}")
            return None
        try:
            pay = result[InternalTypes.NS.value][InternalTypes.NS_PAY_AMOUNT_FIELD.value]
            pay_day = result[InternalTypes.NS.value][InternalTypes.NS_PAY_DAY_OF_MTH_FIELD.value]
        except Exception as err:
            traceback.print_exc()
            logging.error(f"Error in getting pay & pay_day: {err}")
            return None
        else:
            return pay, pay_day

    def getUserReminders(self, user_id: int, limit=100) -> list[Reminder] | None:
        query = Query(mode='r', selectAll=False)
        query.setLimit(limit)
        query.addNewTable(InternalTypes.REMINDERS.value)
        col_query = [InternalTypes.REMINDERS_CONTENT_FIELD.value,
                     InternalTypes.REMINDERS_DATE_CREATED_FIELD.value,
                     InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value,
                     InternalTypes.ID.value,
                     InternalTypes.REMINDERS_CACHE_ID_FIELD.value
                     ]
        
        query.setTableColumn(InternalTypes.REMINDERS.value, col_query)
        matcher = {
                    InternalTypes.USER_ID.value: user_id, 
                    InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL.value
                    }
        query.addMatcher(InternalTypes.REMINDERS.value, matcher)
        record = Record(InternalMethodTypes.GET, user_id, query)
        result, err = self.cache.getRecord(record)
        if not result:
            logging.error(f"error in getUserReminders: {err}")
            return None
        try:
            # logging.debug(f"getRecord return val: {result}")
            reminders = result[InternalTypes.REMINDERS.value]
            reminder_list = []
            for reminder in reminders:
                reminder_list.append(Reminder.fromRaw(reminder))
        except:
            traceback.print_exc()
            logging.error(f"Error in getUserReminderList: {err}")
            return None
        else:
            return reminder_list
    def getGuildReminders(self, guild_id: int):
        pass
    def getGuildChannelReminders(self, guild_id, channel_id):
        pass
    def setUserReminders(self, user_id: int, content_sanitised, call_date: str):
        query = Query(mode='w')
        query.addNewTable(InternalTypes.REMINDERS.value)
        column_query = {
            InternalTypes.USER_ID.value: user_id, 
            InternalTypes.REMINDERS_CONTENT_FIELD.value: content_sanitised,
            InternalTypes.REMINDERS_DATE_CREATED_FIELD.value: datetime.now().isoformat(),
            InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value: call_date,
            InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL.value,
            InternalTypes.REMINDERS_CACHE_ID_FIELD.value: NotifIDFactory.createUnique()
        }
        query.setTableColumn(InternalTypes.REMINDERS.value, column_query)
        record = Record(InternalMethodTypes.SET, user_id, query)
        try:
            self.events.post(record)
        except Exception as err:
            logging.debug(f"err in setUserReminders: {err}")
            traceback.print_exc()
            return False, err
        
    def setGuildReminders(self, user_id: int, guild_id: int):
        pass
    def setGuildChannelReminders(self, guild_id, channel_id):
        pass
    def deleteUserReminders(self, user_id: int, reminder_id: int=None, cache_id=None):
        logging.debug("deleteUserReminders start")
        query = Query(mode='d')
        query.addNewTable(InternalTypes.REMINDERS.value)
        # needs a bus cleaner to clean useless delete writes (e.g. no reminder_id ) before writing to db 

        # for bulk delete reminders (both ids are 0)
        if not reminder_id and not cache_id:
            logging.debug("deleteUserReminders call get")

            reminders = self.getUserReminders(user_id)
            logging.debug("deleteUserReminders end call get")

            if not reminders:
                return 
            for reminder in reminders:
                logging.debug(f"reminder: {reminder.id} {reminder.has_temp_id}")
                id = reminder.id
                if not id:
                    return False, Exception("malformed reminders id.")
                try:
                    
                    if reminder.has_temp_id:
                        self.deleteUserReminders(user_id, cache_id=id)
                    else:
                        self.deleteUserReminders(user_id, reminder_id=id)
                except Exception as err:
                    traceback.print_exc()
            return 
        matcher = {
                    InternalTypes.USER_ID.value: user_id, 
                    InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL.value,
                    }
        
        if reminder_id:
            matcher[InternalTypes.ID.value] = reminder_id
        if cache_id:
            matcher[InternalTypes.REMINDERS_CACHE_ID_FIELD.value] = cache_id
        logging.debug(f"matcher: {matcher}")
        query.addMatcher(InternalTypes.REMINDERS.value, matcher)
        record = Record(InternalMethodTypes.DELETE, user_id, query)
        try:
            logging.debug("posting")
            self.events.post(record)
            logging.debug("done")
        except Exception as err:
            logging.debug(f"err in setUserReminders: {err}")
            traceback.print_exc()
            return False, err
        
    def updateUserReminders(self, user_id: int, content_sanitised, new_call_date: str,reminder_id=None, cache_id=None):
        query = Query(mode='u')
        query.addNewTable(InternalTypes.REMINDERS.value)
        if not reminder_id and not cache_id:
            return
        column_query = {
            InternalTypes.USER_ID.value: user_id,
            InternalTypes.REMINDERS_CONTENT_FIELD.value: content_sanitised,
            InternalTypes.REMINDERS_DATE_CREATED_FIELD.value: datetime.now().isoformat(),
            InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value: new_call_date,
            InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL.value,
        }
        if reminder_id:
            column_query[InternalTypes.ID.value] = reminder_id
        if cache_id:
            column_query[InternalTypes.REMINDERS_CACHE_ID_FIELD.value] = cache_id

        query.setTableColumn(InternalTypes.REMINDERS.value, column_query)
        record = Record(InternalMethodTypes.UPDATE, user_id, query)
        try:
            self.events.post(record)
        except Exception as err:
            logging.debug(f"err in setUserReminders: {err}")
            traceback.print_exc()
            return False, err
    
