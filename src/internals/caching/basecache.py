from internals.caching.records import Record
from internals.database.queryfactory import Query
from internals.enums.enum import InternalTypes, InternalMethodTypes, EventType, QueryToken, ApiErrors
from internals.database.database import Database
from copy import deepcopy
import logging, traceback, random

from internals.events.eventbus import EventBus
from internals.events.events import NewRecordEvent

class Cache():
    OPTIMAL_ENTRY_LIMIT = 200 # optimal number of cache entries
    OVERFLOW_FACTOR_LIMIT = 0.2 # the amount of entries exceeding the OPTIMAL_ENTRY_LIMIT that prompts an optimiseCache call
    OPTIMISATION_FACTOR = 0.8 # the percentage of OPTIMAL_ENTRY_LIMIT entries present after optimising cache
    def __init__(self, source: Database) -> None:
        self.cache = {} # shape: {cache_key: {table_name:[{cols:val, ...}, ...], ...}, ...}
        self.database = source
        self.tableEntryMergeRule = None
        self.CACHE_KEY_TYPE = InternalTypes.WILDCARD
    def setCKeyType(self, type: InternalTypes):
        self.CACHE_KEY_TYPE = type

    def subscribeToEventBus(self, eventbus: EventBus):
        eventbus.subscribeToEvent(EventType.NEW_DELETE_RECORD_EVENT, self.onNewDeleteRecord)
        eventbus.subscribeToEvent(EventType.NEW_UPDATE_RECORD_EVENT, self.onNewUpdateRecord)
        
    def _createTableEntryMergeRule(self):
        raise NotImplementedError("_createTableEntryMergeRule is not implemented.")
    
    # records is deepcopied; The original variable passed in is unmodified
    def updateCache(self, records: dict, cache_key: int = None):
        if not records:
            # no op counted as successful 
            return (True, None)
        
        records = deepcopy(records)
        # if InternalTypes.USERS.value in records:
        #     del records[InternalTypes.USERS.value]
        
        # rejects request if default id is valid but not in cache
        if cache_key != None and cache_key not in self.cache:
            return (False, ApiErrors.INVALID_CACHE_KEY_ERROR)
        
        # fill cache with tbl data
        for tbl_key in records:
            # list of objects each with col:val pairs (nullable)
            table = records[tbl_key] 
            self._updateTable(table, tbl_key, cache_key, self.tableEntryMergeRule[tbl_key])

        return (True, None)

    def _updateTable(self, table: list, tbl_key: str, cache_key, merge=False):
        for table_entry in table:
        # use included user_id if present, else use the one provided in the args as default, else if None, continue to next tbl entry
            if self.CACHE_KEY_TYPE.value in table_entry:
                cache_key = table_entry[self.CACHE_KEY_TYPE.value]
                del table_entry[self.CACHE_KEY_TYPE.value]

            elif cache_key == None:
                continue

            try:
                if tbl_key not in self.cache[cache_key]:
                    if merge:

                        self.cache[cache_key][tbl_key]= table_entry
                    else:
                        self.cache[cache_key][tbl_key] = [table_entry]
                    continue

                if merge:
                    # override current duplicate keys with new value + add any new keys into the entry obj
                    self.cache[cache_key][tbl_key].update(table_entry)
                else:
                    self.cache[cache_key][tbl_key].append(table_entry)
            except Exception as err:
                traceback.print_exc()
                logging.critical(f"error in appending to {tbl_key} table for user with id: {cache_key}. Error: {type(err)}, {err}")
                continue

    def initCache(self):
        raise NotImplementedError("initCache is not implemented.")

    def createEntry(self, cache_key):
        if cache_key not in self.cache:
            self.cache[cache_key] = dict()
        
    def _retrieveRecords(self, tables_query:list[str]):
        """returns the first ENTRY_LIMIT records from selected tables from db"""
        db_query = Query()
        db_query.setTableNames(tables_query)
        db_query.setLimit(Cache.OPTIMAL_ENTRY_LIMIT)
        result = self.database.getEntriesFromTables(db_query)

       
            
        logging.info(f"retrieved records: {result}")
        return result
    
    def addCacheKey(self, cache_key: int):
        query = Query(mode='w')
        query.addNewTable(self.CACHE_KEY_TYPE.value)
        column_query = {InternalTypes.ID.value: cache_key}
        query.setTableColumn(self.CACHE_KEY_TYPE.value, column_query)
        self.database.writeToTables([query])

    def onNewDeleteRecord(self, event: NewRecordEvent):
        
        raise NotImplementedError("onNewDeleteRecord is not implemented.")

    def onNewUpdateRecord(self, event: NewRecordEvent):

        raise NotImplementedError("onNewUpdateRecord is not implemented.")


    def getRecord(self, record: Record) -> tuple[dict | None, None | ApiErrors]:
        raise NotImplementedError("getRecord not implemented.")
    
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
        