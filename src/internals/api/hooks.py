from datetime import datetime
from internals.events.eventbus import EventBus
from internals.caching.records import Record
from internals.caching.cache import Cache
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes, InternalTypes
import logging, traceback
class CommandApi():
    def __init__(self, eventsQueue: EventBus, cache: Cache) -> None:
        self.events = eventsQueue
        self.cache = cache
    def setORD(self, user_id: int, date: datetime):
        datestr = date.isoformat()
        query = Query(mode='w')
        query.add_table(InternalTypes.NS.value)
        column_query = {InternalTypes.USER_ID.value: user_id, 
                        InternalTypes.NS_DATETIME_FIELD.value: datestr}
        
        query.set_columns_for_table(InternalTypes.NS.value, column_query)

        record = Record(InternalMethodTypes.UPDATE, user_id, query)
        self.events.post(record)
    
    def getORD(self, user_id: int):
        query = Query(mode='r', selectAll=False)
        query.add_table(InternalTypes.NS.value)
        column_query = [InternalTypes.NS_DATETIME_FIELD.value]
        query.set_columns_for_table(InternalTypes.NS.value, column_query)
        query.add_matcher(InternalTypes.NS.value, {InternalTypes.USER_ID.value: user_id})

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
        query.add_table(InternalTypes.NS.value)
        column_query = {InternalTypes.USER_ID.value: user_id, 
                        InternalTypes.NS_PAY_AMOUNT_FIELD.value: pay_amt, 
                        InternalTypes.NS_PAY_DAY_OF_MTH_FIELD.value: pay_dom}
        query.set_columns_for_table(InternalTypes.NS.value, column_query)
        record = Record(InternalMethodTypes.UPDATE, user_id, query)
        self.events.post(record)

    def getPay(self, user_id: int) -> tuple[float,int] | None:
        query = Query(mode='r', selectAll=False)
        query.add_table(InternalTypes.NS.value)
        column_query = [InternalTypes.NS_PAY_AMOUNT_FIELD.value,
                        InternalTypes.NS_PAY_DAY_OF_MTH_FIELD.value]
        
        query.set_columns_for_table(InternalTypes.NS.value, column_query)
        query.add_matcher(InternalTypes.NS.value, {InternalTypes.USER_ID.value: user_id})
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

    

    
