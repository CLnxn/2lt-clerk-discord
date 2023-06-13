from internals.caching.records import Record
from internals.database.queryfactory import Query, DEFAULT_TABLES
from internals.enums.enum import InternalTypes, InternalMethodTypes, EventType, QueryToken, ApiErrors
from internals.database.database import Database
from copy import deepcopy
import logging, traceback, random

from internals.events.eventbus import EventBus
from internals.events.events import NewRecordEvent
from internals.errors.error import CacheInitError

class Cache():
    OPTIMAL_ENTRY_LIMIT = 200 # optimal number of cache entries
    OVERFLOW_FACTOR_LIMIT = 0.2 # the amount of entries exceeding the OPTIMAL_ENTRY_LIMIT that prompts an optimiseCache call
    OPTIMISATION_FACTOR = 0.8 # the percentage of OPTIMAL_ENTRY_LIMIT entries present after optimising cache
    def __init__(self, source: Database) -> None:
        self.cache = {} # shape: {user_id: {table_name:[{cols:val, ...}, ...], ...}, ...}
        self.database = source
        # map of table-> whether sub entries should be merged or appended (aka if multiple values are allowed) 
        self.tableEntryMergeRule = self._createTableEntryMergeRule() 


    def subscribeToEventBus(self, eventbus: EventBus):
        eventbus.subscribeToEvent(EventType.NEW_DELETE_RECORD_EVENT, self.onNewDeleteRecord)
        eventbus.subscribeToEvent(EventType.NEW_UPDATE_RECORD_EVENT, self.onNewUpdateRecord)
        
    def _createTableEntryMergeRule(self):
        return {
            InternalTypes.NS.value: True, # single entry only,
            InternalTypes.USERS.value: True, # single entry only
            InternalTypes.REMINDERS.value: False, # allows multiple entries
        }
    
    # records is deepcopied; The original variable passed in is unmodified
    def updateCache(self, records: dict, user_id: int = None):
        if not records:
            # no op counted as successful 
            return (True, None)
        
        records = deepcopy(records)
        # if InternalTypes.USERS.value in records:
        #     del records[InternalTypes.USERS.value]
        
        # rejects request if default id is valid but not in cache
        if user_id != None and user_id not in self.cache:
            logging.warn(f"user_id {user_id} not in cache")
            return (False, ApiErrors.INVALID_USER_ID_ERROR)
        
        # fill cache with tbl data
        for tbl_key in records:
            # list of objects each with col:val pairs (nullable)
            table = records[tbl_key] 
            self._updateTable(table, tbl_key, user_id, self.tableEntryMergeRule[tbl_key])

        return (True, None)

    def _updateTable(self, table: list, tbl_key: str, user_id, merge=False):
        for table_entry in table:
        # use included user_id if present, else use the one provided in the args as default, else if None, continue to next tbl entry
            if InternalTypes.USER_ID.value in table_entry:
                user_id = table_entry[InternalTypes.USER_ID.value]
                del table_entry[InternalTypes.USER_ID.value]

            elif user_id == None:
                continue

            try:
                if tbl_key not in self.cache[user_id]:
                    if merge:

                        self.cache[user_id][tbl_key]= table_entry
                    else:
                        self.cache[user_id][tbl_key] = [table_entry]
                    continue

                if merge:
                    # override current duplicate keys with new value + add any new keys into the entry obj
                    self.cache[user_id][tbl_key].update(table_entry)
                else:
                    self.cache[user_id][tbl_key].append(table_entry)
            except Exception as err:
                traceback.print_exc()
                logging.critical(f"error in appending to {tbl_key} table for user with id: {user_id}. Error: {type(err)}, {err}")
                continue

    def initCache(self):
        records = self._retrieveRecords()
        if InternalTypes.USERS.value not in records:
            if records:
                raise CacheInitError()
            logging.info(f"empty cache initialised.")
            return
        # cache entry initialising
        for user in records[InternalTypes.USERS.value]:
            if InternalTypes.ID.value not in user:
                logging.warning(f"user id not in user table for {user} ")
                continue
            user_id = user[InternalTypes.ID.value]

            self.createEntry(user_id)
        
        # update cache with tbl data
        self.updateCache(records)
        logging.info(f"initialised cache: {self.cache}")

    def createEntry(self, user_id):
        if user_id not in self.cache:
            self.cache[user_id] = dict()
        
    def _retrieveRecords(self, tables_query:list[str] = DEFAULT_TABLES):
        """Gets the first ENTRY_LIMIT records from selected tables in db and inserts into self.cache"""
        db_query = Query()
        db_query.setTableNames(tables_query)
        db_query.setLimit(Cache.OPTIMAL_ENTRY_LIMIT)
        result = self.database.getEntriesFromTables(db_query)

       
            
        logging.info(f"retrieved records: {result}")
        return result
    
    def addUserID(self, user_id: int):
        query = Query(mode='w')
        query.addNewTable(InternalTypes.USERS.value)
        column_query = {InternalTypes.ID.value: user_id}
        query.setTableColumn(InternalTypes.USERS.value, column_query)
        self.database.writeToTables([query])

    def onNewDeleteRecord(self, event: NewRecordEvent):
        record = event.record
        logging.info("onNewDeleteRecord")
    def onNewUpdateRecord(self, event: NewRecordEvent):
        record = event.record
        query = record.data
        records = dict(query.getAllTableColumns())
        for key in records:
            records[key] = [records[key]]
        
        status, resObj = self.updateCache(records, record.id_map[self.CACHE_KEY_TYPE])

        if not status:
            if resObj == ApiErrors.INVALID_USER_ID_ERROR:
                # write userid directly to db
                self.addUserID(record.id_map[self.CACHE_KEY_TYPE])


        # logging.debug(f"updated cache: {self.cache}")
        # logging.info("onNewUpdateRecord")
    def getRecord(self, record: Record) -> tuple[dict | None, None | ApiErrors]:
        """Gets a record from cache, or from DB, if there is a cache miss.
        
        Returns a tuple of result, err for the given record arg. result is None if there is an error, and err will be defined.
            If no error, result will have a shape given:
             <result>: {tablename: [{col:val,...},...], unique_tablename: {col:val, ...}, ...}

             unique_tablename represents tables which have a False boolean in TableEntryMergeRule and tablename represents when it is True.
        """
        read_query = record.data
        id = record.id_map[self.CACHE_KEY_TYPE]   
        CACHE_MISS = False
        result = None

        if id not in self.cache:
            self.createEntry(id)
            self.addUserID(id)
            CACHE_MISS = True

        if not CACHE_MISS:
            result = self.getFromCache(id, read_query)
            CACHE_MISS = not result

        if CACHE_MISS:
            # instant read from db
            logging.debug(f"cache missed")
            data = self.getFromDB(read_query)
            logging.debug(f"data from db: {data}")
            status, result_obj  = self.updateCache(data, id)

            if not status:
                return None, result_obj
            result = self.getFromCache(id, read_query)

        if not result:
            return None, ApiErrors.CACHE_MISS_ERROR
        
        return (result, None)
    
    # returns {tablename: [{col:val,...},...], unique_tablename: {col:val, ...}, ...}
    def getFromCache(self, key: str, query: Query) -> dict | None:
        logging.debug('getFromCache() start')
        result = {}
        tbl_col_dict = query.getAllTableColumns()    
        logging.debug(tbl_col_dict)
        for tbl in tbl_col_dict:
            if tbl not in self.cache[key]:
                return None
            # need to check that num of cols for the tbl for that user in cache
            # matches that of table, then return. But this feature isnt going to be used for now
            if tbl_col_dict[tbl] == QueryToken.WILDCARD.value:
                logging.critical("not implemented")
                continue
            result_tbl = []
            # find & filter data from cache based on the input read query, and whether table allows multiple or single entries  
            if not self.tableEntryMergeRule[tbl]:

                for entry in self.cache[key][tbl]:
                    ent = {}
                    for col in tbl_col_dict[tbl]:
                        if col not in entry:
                            return None
                        ent[col] = entry[col]
                    result_tbl.append(ent)
                result[tbl] = result_tbl
            else:
                entry = self.cache[key][tbl]
                ent = {}
                for col in tbl_col_dict[tbl]:
                    if col not in entry:
                        return None
                    ent[col] = entry[col]
                result[tbl] = ent

        return result

    def getFromDB(self, query: Query):
        return self.database.getEntriesFromTables(query)  
        