from datetime import datetime
from internals.eventbus import EventBus
from internals.caching.records import Record
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes, InternalTypes

class Command_Internal_Hooks():
    def __init__(self, eventsQueue: EventBus) -> None:
        self.events = eventsQueue
    
    def setORD(self, user_id, date: datetime):
        datestr = date.isoformat()
        query = Query(mode='w')
        query.add_table(InternalTypes.NS)
        column_query = {InternalTypes.USER_ID: user_id, InternalTypes.NS_DATETIME_FIELD:datestr}
        query.set_columns_for_table(InternalTypes.NS, column_query)

        record = Record(InternalMethodTypes.UPDATE, user_id, query)
        self.events.addRecord(record)