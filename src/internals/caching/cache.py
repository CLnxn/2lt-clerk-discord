from internals.caching.records import Record
from internals.database.queryfactory import Query
from internals.enums.enum import InternalTypes, InternalMethodTypes
from internals.database.database import Database
import logging

from internals.eventbus import EventBus
class Cache():
    ENTRY_LIMIT = 20
    def __init__(self) -> None:
        self.cache = {}
    def subscribeToEventBus(self, eventbus: EventBus):
        eventbus.newRecordEventHooks.subscribe(self.onNewRecord)
    def update(self, key,value):
        pass
    def populateCache(self, data):
        self.cache = data
    def retrieveRecords(self, database: Database, tables_query:list[str] = InternalTypes.DEFAULT_TABLES):
        """Gets the first ENTRY_LIMIT records from selected tables in db and inserts into self.cache"""
        db_query = Query()
        db_query.set_tables(tables_query)
        db_query.set_first_n(Cache.ENTRY_LIMIT)
        result = database.getEntriesFromTables(db_query)
        logging.info(result)
        return result
    
    def onNewRecord(self, record: Record):
        if record.method == InternalMethodTypes.GET:
            read_query = record.data
            tbls = read_query.get_tables()
            
            