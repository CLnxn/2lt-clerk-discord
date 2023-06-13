import logging, traceback
from time import sleep
from typing import Any
import internals.api.internals as internals
from internals.enums.enum import InternalMethodTypes
from internals.caching.records import Record
from internals.service_workers.worker_thread import WorkerThread
from internals.service_workers import base_worker

UPDATE_PERIOD_SECONDS = 10

class Worker(base_worker.Worker):
    def __init__(self, state) -> None:
        super().__init__(UPDATE_PERIOD_SECONDS)
        self.state: internals.InternalState = state
        self.mappingRule = self.createMappingRule()
        self.name = "event"

    # deprecated. Will be replaced in the future with a scheduled update db task
    # def onUpdateDBEvent(self, event: NewRecordEvent):
    #     record = event.record
    #     if record.type == InternalMethodTypes.SET or record.type == InternalMethodTypes.UPDATE:
    #         self.state.database.writeToTables(record.data)

    # does not create mapping rules for GET methods
    def createMappingRule(self):
        dbRef = self.state.database
        return {InternalMethodTypes.UPDATE: dbRef.writeToTables, InternalMethodTypes.DELETE: dbRef.deleteFromTables}

    def task(self):
        logging.info(f"{self.name} worker task started.")
        self.updateDatabase()
        logging.info(f"{self.name} worker task ended.")


    def updateDatabase(self):
        try:
            records = self.state.events.flush()
        except Exception as err:
            traceback.print_exc()
            logging.error(err)
            return
        
        grps = self.sortingFactory(records)
        for grp in grps:
            db_func = grp[0]
            
            db_func([rec.data for rec in grp[1]])

    # takes in records, returns an array of the tuple: (db_op_function,list[records])
    def sortingFactory(self, records: list[Record]):
        if not records:
            return []
        record_grps = []
        prev_record_type = records[0].method
        records_blk = (self.mappingRule[prev_record_type], []) 
        for record in records:
            if record.method == prev_record_type:
                records_blk[1].append(record)
                prev_record_type = record.method
                continue
            record_grps.append(records_blk)
            prev_record_type = record.method
            records_blk = (self.mappingRule[prev_record_type],[record])
        
        record_grps.append(records_blk)
        return record_grps


    def validateCacheInfo(self):
        pass
