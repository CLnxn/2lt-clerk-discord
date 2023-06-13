from datetime import datetime
from internals.events.eventbus import EventBus
from internals.caching.records import Record
from internals.caching.usercache import UsersCache
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes, InternalTypes, RemindersScope
import logging, traceback

from internals.api.notifier import Reminder
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

        record = Record(InternalMethodTypes.UPDATE, user_id, query)
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
        record = Record(InternalMethodTypes.UPDATE, user_id, query)
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

    def getUserReminders(self, user_id: int, limit=100):
        query = Query(mode='r', selectAll=False)
        query.setLimit(limit)
        query.addNewTable(InternalTypes.REMINDERS.value)
        col_query = [InternalTypes.REMINDERS_CONTENT_FIELD,
                     InternalTypes.REMINDERS_DATE_CREATED_FIELD,
                     InternalTypes.REMINDERS_DATE_DEADLINE_FIELD,
                     InternalTypes.ID.value]
        
        query.setTableColumn(InternalTypes.REMINDERS.value, col_query)
        matcher = {
                    InternalTypes.USER_ID.value: user_id, 
                    InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL
                    }
        query.addMatcher(InternalTypes.REMINDERS.value, matcher)
        record = Record(InternalMethodTypes.GET, user_id, query)
        result, err = self.cache.getRecord(record)
        if not result:
            logging.error(f"error in getUserReminders: {err}")
            return None
        try:
            reminders = result[InternalTypes.REMINDERS.value]
            reminder_list = []
            for reminder in reminders:
                reminder_list.append(Reminder.fromRaw(reminder))
        except:
            traceback.print_exc()
            logging.error(f"Error in getting pay & pay_day: {err}")
            return None
        else:
            return reminder_list
    def getGuildReminders(self, guild_id: int):
        pass
    def getGuildChannelReminders(self, guild_id, channel_id):
        pass
    def setUserReminders(self, user_id: int, content, call_date_str: str):
        query = Query(mode='w')
        query.addNewTable(InternalTypes.REMINDERS.value)
        column_query = {
            InternalTypes.USER_ID.value: user_id, 
            InternalTypes.REMINDERS_CONTENT_FIELD.value: content,
            InternalTypes.REMINDERS_DATE_CREATED_FIELD.value: datetime.now().isoformat(),
            InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value: call_date_str,
            InternalTypes.REMINDERS_SCOPE_FIELD.value: RemindersScope.PERSONAL,
        }
        query.setTableColumn(InternalTypes.REMINDERS.value, column_query)
        record = Record(InternalMethodTypes.SET, user_id, query)
        try:
            self.events.post(record)
        except Exception as err:
            return False, err
        
    def setGuildReminders(self, user_id: int, guild_id: int):
        pass
    def setGuildChannelReminders(self, guild_id, channel_id):
        pass
    def deleteUserReminder(self, user_id: int, reminder_id: int):
        pass
    
    def deleteUserReminders(self, user_id: int):
        pass
    def updateUserReminders(self, user_id: int, reminder_id, content, new_call_date):
        pass

    
