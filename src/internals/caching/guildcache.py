from internals.caching.records import Record
from internals.database.queryfactory import Query
from internals.enums.enum import InternalTypes, ApiErrors, EventType
from internals.database.database import Database, GUILDS_REFERENCED_TABLES
import logging

from internals.events.events import NewRecordEvent
from internals.errors.error import CacheInitError
from internals.events.eventbus import EventBus 
import internals.caching.basecache as parent
from src.internals.events.events import NewRecordEvent

class GuildsCache(parent.Cache):
    def __init__(self, source: Database) -> None:
        super().__init__(source)
        self.setCKeyType(InternalTypes.GUILDS)
        # map of table-> whether sub entries should be merged or appended (aka if multiple values are allowed) 
        self.tableEntryMergeRule = self._createTableEntryMergeRule() 
    def _createTableEntryMergeRule(self):
        return {
            InternalTypes.GUILDS.value: True, # single entry only,
            InternalTypes.CHANNELS.value: True, # single entry only
            InternalTypes.REMINDERS.value: False, # allows multiple entries
        }
    def _createTableEntryIdentifiers(self):
        return {
            InternalTypes.REMINDERS.value: (InternalTypes.ID, InternalTypes.REMINDERS_CACHE_ID_FIELD)
        }
        
    def initCache(self):
        records = self._retrieveRecords(GUILDS_REFERENCED_TABLES)
        if self.CACHE_KEY_TYPE.value not in records:
            if records:
                raise CacheInitError()
            logging.info(f"empty cache initialised.")
            return
        # cache entry initialising
        for main_entry in records[self.CACHE_KEY_TYPE.value]:
            if InternalTypes.ID.value not in main_entry:
                logging.warning(f"id not in {self.CACHE_KEY_TYPE.value} table for {main_entry} ")
                continue
            cache_key = main_entry[InternalTypes.ID.value]

            self.createEntry(cache_key)
        
        # update cache with tbl data
        self.updateCache(records)
        logging.info(f"initialised cache: {self.cache}")

    def onNewSetRecord(self, event: NewRecordEvent):
        return self.onNewInsertRecord(event)
    def onNewDeleteRecord(self, event: NewRecordEvent):
        record = event.record
        if record.rtype != InternalTypes.WILDCARD and record.rtype != self.CACHE_KEY_TYPE:
            return
        
        logging.info("onNewDeleteRecord")
        self.deleteEntryFromCache()
    def onNewInsertRecord(self, event: NewRecordEvent):
        record = event.record
        # check if cache is compatible
        if record.rtype != InternalTypes.WILDCARD and record.rtype != self.CACHE_KEY_TYPE:
            return
        query = record.data
        records = dict(query.getAllTableColumns())
        for key in records:
            records[key] = [records[key]]
        
        status, resObj = self.updateCache(records, record.id_map[self.CACHE_KEY_TYPE])

        if not status:
            if resObj == ApiErrors.INVALID_CACHE_KEY_ERROR:
                # write userid directly to db
                self.addCacheKey(record.id_map[self.CACHE_KEY_TYPE])


    def getRecord(self, record: Record) -> tuple[dict | None, None | ApiErrors]:
        """Gets a record from cache, or from DB, if there is a cache miss.
        
        Returns a tuple of result, err for the given record arg. result is None if there is an error, and err will be defined.
            If no error, result will have a shape given:
             <result>: {tablename: [{col:val,...},...], unique_tablename: {col:val, ...}, ...}

             unique_tablename represents tables which have a False boolean in TableEntryMergeRule and tablename represents when it is True.
        """
        read_query = record.data
        guild_id = record.id_map[self.CACHE_KEY_TYPE]   
        CACHE_MISS = False
        result = None

        if guild_id not in self.cache:
            self.createEntry(guild_id)
            self.addCacheKey(guild_id)
            CACHE_MISS = True

        if not CACHE_MISS:
            result = self.getFromCache(guild_id, read_query)
            CACHE_MISS = not result

        if CACHE_MISS:
            # instant read from db
            logging.debug(f"cache missed")
            data = self.getFromDB(read_query)
            logging.debug(f"data from db: {data}")
            status, result_obj  = self.updateCache(data, guild_id)

            if not status:
                return None, result_obj
            result = self.getFromCache(guild_id, read_query)

        if not result:
            return None, ApiErrors.CACHE_MISS_ERROR
        
        return (result, None)

        