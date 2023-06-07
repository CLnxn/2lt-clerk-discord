from collections.abc import Callable, Iterable, Mapping
import logging, traceback
from threading import Thread, Event
from time import sleep
from typing import Any
import internals.api.internals as internals
from internals.events.events import NewRecordEvent
from internals.enums.enum import InternalMethodTypes
from internals.caching.records import Record

UPDATE_PERIOD_SECONDS = 10

class Worker():
    def __init__(self, state) -> None:
        self.workerthread = WorkerThread(self.task, UPDATE_PERIOD_SECONDS)
        self.state: internals.InternalState = state
        self.counter = 0
        self.mappingRule = self.createMappingRule()
        

    # deprecated. Will be replaced in the future with a scheduled update db task
    # def onUpdateDBEvent(self, event: NewRecordEvent):
    #     record = event.record
    #     if record.type == InternalMethodTypes.SET or record.type == InternalMethodTypes.UPDATE:
    #         self.state.database.writeToTables(record.data)

    # does not create mapping rules for GET methods
    def createMappingRule(self):
        dbRef = self.state.database
        return {InternalMethodTypes.UPDATE: dbRef.writeToTables, InternalMethodTypes.DELETE: dbRef.deleteFromTables}

    def start(self):
        logging.info("service worker is starting")
        self.workerthread.start()
        
    def stop(self):
        self.workerthread.isRunning = False
        logging.warning("service worker is stopping")

    def task(self):
        logging.info("worker task started.")
        self.updateDatabase()
        logging.info("worker task ended.")


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
        prev_record_type = records[0].type
        records_blk = (self.mappingRule[prev_record_type], []) 
        for record in records:
            if record.type == prev_record_type:
                records_blk[1].append(record)
                prev_record_type = record.type
                continue
            record_grps.append(records_blk)
            prev_record_type = record.type
            records_blk = (self.mappingRule[prev_record_type],[record])
        
        record_grps.append(records_blk)
        return record_grps


    def validateCacheInfo(self):
        pass

class WorkerThread(Thread):
    def __init__(self, task, delay_seconds, group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.delay = delay_seconds
        self.task = task   
        self._kill = Event()
        self.daemon = True # set to true in production, stops when main thread stops
        
    def run(self) -> None:
        self.isRunning = True
        while self.isRunning:
            self.task()
            sleep(self.delay)

        logging.info("worker thread finished")
