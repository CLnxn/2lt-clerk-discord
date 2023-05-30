from collections.abc import Callable, Iterable, Mapping
import logging
from threading import Thread
from time import sleep
from typing import Any
UPDATE_PERIOD_SECONDS = 3
class Worker():
    def __init__(self) -> None:
        self.workerthread = WorkerThread(self.work_task, UPDATE_PERIOD_SECONDS)
        self.counter = 0
    def start_working(self):
        self.workerthread.start()
        logging.info("service worker is starting")
        
    def stop_working(self):
        self.workerthread.isRunning = False
        logging.warning("service worker is stopping")

    def work_task(self):
        self.updateDB()

    def updateDB(self):
        logging.info("Commencing Scheduled Write to Database.")
    
    def validateCacheInfo(self):
        pass

class WorkerThread(Thread):
    def __init__(self, task, delay_seconds = 10, group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.delay = delay_seconds
        self.task = task    
        
    def run(self) -> None:
        self.isRunning = True
        while self.isRunning:
            sleep(self.delay)
            self.task()
        logging.info("worker thread finished")
logging.basicConfig(level=logging.DEBUG)
worker = Worker()
worker.start_working()
