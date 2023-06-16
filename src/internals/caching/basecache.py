from internals.caching.records import Record
from internals.database.queryfactory import Query
from internals.enums.enum import InternalTypes, InternalMethodTypes, EventType, QueryToken, ApiErrors
from internals.database.database import REMINDERS_TABLE_COLUMNS, Database
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
        self.tableEntryMergeRule: dict = None
        self.tableEntryIdentifierMap: dict = None
        self.CACHE_KEY_TYPE = InternalTypes.WILDCARD
    def setCKeyType(self, type: InternalTypes):
        self.CACHE_KEY_TYPE = type

    def subscribeToEventBus(self, eventbus: EventBus):
        eventbus.subscribeToEvent(EventType.NEW_DELETE_RECORD_EVENT, self.onNewDeleteRecord)
        eventbus.subscribeToEvent(EventType.NEW_INSERT_RECORD_EVENT, self.onNewInsertRecord)
        eventbus.subscribeToEvent(EventType.NEW_SET_RECORD_EVENT, self.onNewSetRecord)
        eventbus.subscribeToEvent(EventType.NEW_UPDATE_RECORD_EVENT, self.onNewUpdateRecord)
    def _createTableEntryMergeRule(self):
        raise NotImplementedError("_createTableEntryMergeRule is not implemented.")
    
    def _createTableEntryIdentifiers(self):
        raise NotImplementedError("_createTableEntryIdentifiers is not implemented.")

    # records is deepcopied; The original variable passed in is unmodified
    def updateCache(self, tables: dict, cache_key: int = None, append=True):
        if not tables:
            # no op counted as successful 
            return (True, None)
        
        tables = deepcopy(tables)
        # if InternalTypes.USERS.value in records:
        #     del records[InternalTypes.USERS.value]
        
        # rejects request if default id is valid but not in cache
        if cache_key != None and cache_key not in self.cache:
            return (False, ApiErrors.INVALID_CACHE_KEY_ERROR)
        
        # fill cache with tbl data
        for tbl_key in tables:
            # list of objects each with col:val pairs (nullable)
            table = tables[tbl_key] 
            self._updateTable(table, tbl_key, cache_key, self.tableEntryMergeRule[tbl_key], append=append)

        return (True, None)

    def _updateTable(self, table: list, tbl_key: str, cache_key, merge=False, append=True):
        for table_entry in table:
        # use included user_id if present, else use the one provided in the args as default, else if None, continue to next tbl entry
            if self.CACHE_KEY_TYPE.value in table_entry:
                cache_key = table_entry[self.CACHE_KEY_TYPE.value]
                del table_entry[self.CACHE_KEY_TYPE.value]

            elif cache_key == None:
                continue

            try:
                if merge:
                    self._updateMergeableTable(self.cache[cache_key], tbl_key, table_entry)
                else:
                    self._updateNonMergeableTable(self.cache[cache_key], tbl_key, table_entry, append=append)
            except Exception as err:
                traceback.print_exc()
                logging.critical(f"error in appending to {tbl_key} table for user with id: {cache_key}. Error: {type(err)}, {err}")
                continue
    # Replaces existing entry with new_ent (in <cached_table>: a particular table in the cache) if present via entry_id_keys. 
    # Appends if entry was not originally present.
    def _updateNonMergeableTable(self, cached_table: dict, tbl_key, new_ent, append=True):
        entry_id_keys = self.tableEntryIdentifierMap[tbl_key]

        if tbl_key not in cached_table:
            cached_table[tbl_key] = [new_ent]
            return
        if not entry_id_keys:
            if append:
                cached_table[tbl_key].append(new_ent)
            return
        for tbl_ent in cached_table[tbl_key]:
            tbl_ent: dict
            # replace old entry with new if they are equal via any one of the id keys
            if Cache._cmpDictsByIds(tbl_ent, new_ent, entry_id_keys):
                tbl_ent.update(new_ent)
                return
        if append:  
            cached_table[tbl_key].append(new_ent)
    # Replaces/sets existing table with new_ent
    def _updateMergeableTable(self, cached_table: dict, tbl_key, new_ent):
        if tbl_key not in cached_table:
            cached_table[tbl_key]= new_ent
            return
        cached_table[tbl_key].update(new_ent)


    # returns True if both dicts have the same val (!=None) for any id key (non strict mode).
    def _cmpDictsByIds(ent1: dict, ent2: dict, ids, strict=False):
        if not strict:
            for id in ids:
                r = Cache._cmpDictById(ent1, ent2, id)
                if not r:
                    continue    
                return True
            return False
        if strict:
            for id in ids:
                r = Cache._cmpDictById(ent1, ent2, id)
                if not r:
                    return False
            return True
        
    def _cmpDictById(ent1: dict, ent2:dict, id):
        # logging.debug(f"in _cmpDictById: ent1 {ent1} ent2 {ent2} {id}")
        r1 = ent1.get(id, None)
        r2 = ent2.get(id, None)
        # logging.debug(f" r1{r1} r2{r2} {r1==r2}")
        return r1 == r2 and not r1 == None
    
    def deleteEntryFromCache(self, cache_key, tbl_key, rules_map, strict=False):
        cached_table: dict =  self.cache.get(cache_key,None)
        if not cached_table: 
            return
        tbl = cached_table.get(tbl_key, None)
        logging.debug(f"tables: {tbl}")
        if not tbl:
            return
        
        #cRef shd either be a dict or list depending on table
        tbl_t = type(tbl) 
        if tbl_t == list:
            tbl: list
            if not rules_map:
                # removing the key from the cache will trigger a cache miss on getFromCache() call. Hence clear() is used.
                tbl.clear()
                return
            ids = self.tableEntryIdentifierMap.get(tbl_key, None)
            if not ids:
                tbl.clear()
                return
            # pops while traversing from the end
            for i, ent in reversed(list(enumerate(tbl))):
                logging.debug(f"i iterate")
                if Cache._cmpDictsByIds(ent, rules_map, rules_map, strict):
                   tbl.pop(i) 
        elif tbl_t == dict:
            tbl: dict
            tbl.clear()
                    
    def initCache(self):
        raise NotImplementedError("initCache is not implemented.")

    def createEntry(self, cache_key):
        if cache_key not in self.cache:
            self.cache[cache_key] = dict()
        
    def _retrieveRecords(self, tables_query:list[str]):
        """returns the first ENTRY_LIMIT records from selected tables from db"""
        db_query = Query()
        db_query.initTables(tables_query)

        if InternalTypes.REMINDERS.value in tables_query:
            # ignores cache_id field when pulling from reminders table in db.
            reminder_cols = REMINDERS_TABLE_COLUMNS.copy()
            reminder_cols.remove(InternalTypes.REMINDERS_CACHE_ID_FIELD.value)
            db_query.setTableColumn(InternalTypes.REMINDERS.value, reminder_cols)

        db_query.setLimit(Cache.OPTIMAL_ENTRY_LIMIT)
        result = self.database.getEntriesFromTables(db_query)

        
            
        # logging.info(f"retrieved records: {result}")
        return result
    
    def addCacheKey(self, cache_key: int):
        query = Query(mode='w')
        query.addNewTable(self.CACHE_KEY_TYPE.value)
        column_query = {InternalTypes.ID.value: cache_key}
        query.setTableColumn(self.CACHE_KEY_TYPE.value, column_query)
        self.database.writeToTables([query])
    def onNewUpdateRecord(self, event: NewRecordEvent):

        raise NotImplementedError("onNewUpdateRecord is not implemented.")

    def onNewSetRecord(self, event: NewRecordEvent):
        
        raise NotImplementedError("onNewSetRecord is not implemented.")
        
    def onNewDeleteRecord(self, event: NewRecordEvent):
        
        raise NotImplementedError("onNewDeleteRecord is not implemented.")

    def onNewInsertRecord(self, event: NewRecordEvent):

        raise NotImplementedError("onNewInsertRecord is not implemented.")

    def getRecord(self, record: Record) -> tuple[dict | None, None | ApiErrors]:
        raise NotImplementedError("getRecord not implemented.")
    
    # returns {tablename: [{col:val,...},...], unique_tablename: {col:val, ...}, ...}
    def getFromCache(self, key: str, query: Query) -> dict | None:
        # logging.debug('getFromCache() start')
        result = {}
        tbl_col_dict = query.getAllTableColumns()    
        # logging.debug(tbl_col_dict)
        # logging.debug(f"getFromCache: cache: {self.cache}")
        for tbl in tbl_col_dict:
            if tbl not in self.cache[key]:
                # logging.debug(f"getFromCache: {tbl} not in self.cache[key]: {self.cache[key]}")
                return None
            # need to check that num of cols for the tbl for that user in cache
            # matches that of table, then return. But this feature isnt going to be used for now
            if tbl_col_dict[tbl] == QueryToken.WILDCARD.value:
                logging.critical("not implemented")
                continue
            result_tbl = []
            # find & filter data from cache based on the input read query, and whether table allows multiple or single entries  
            if not self.tableEntryMergeRule[tbl]:
                # logging.debug(f"getFromCache: enter loop")
                for entry in self.cache[key][tbl]:
                    ent = {}
                    for col in tbl_col_dict[tbl]:
                        if col not in entry:
                            # logging.debug(f"getFromCache: {col} not in entry: {entry}")
                            # ent[col] = None
                            continue
                        ent[col] = entry[col]
                    result_tbl.append(ent)
                result[tbl] = result_tbl
                # logging.debug(f"getFromCache: result_tbl: {result_tbl}")
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
        tbls = query.getTableNames()
        if InternalTypes.REMINDERS.value in tbls:
            # ignores cache_id field when pulling from reminders table in db.
            query.deleteColumnForTable(InternalTypes.REMINDERS.value, InternalTypes.REMINDERS_CACHE_ID_FIELD.value)

        return self.database.getEntriesFromTables(query)  
        