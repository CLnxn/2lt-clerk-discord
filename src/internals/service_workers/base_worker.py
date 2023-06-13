import logging, traceback
import internals.api.internals as internals
from internals.service_workers.worker_thread import WorkerThread

UPDATE_PERIOD_SECONDS = 10

class Worker():
    def __init__(self, work_period = UPDATE_PERIOD_SECONDS, isDaemon=True) -> None:
        self.workerthread = WorkerThread(self.task, work_period, daemon=isDaemon)
        self.name = "base"
    def start(self):
        logging.info(f"{self.name} worker is starting")
        self.workerthread.start()
        
    def stop(self):
        self.workerthread.stop()
        logging.warning(f"{self.name} worker is stopping")

    def task(self):
        raise NotImplementedError(f"{self.name} worker does not have any tasks!")

