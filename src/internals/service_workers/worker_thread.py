import logging
from threading import Thread
from time import sleep
from typing import Any, Callable, Iterable, Mapping


class WorkerThread(Thread):
    def __init__(self, task, delay_seconds, group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = False) -> None:
        super().__init__(group, target, name, args, kwargs)
        self.delay = delay_seconds
        self.task = task   
        self.daemon = daemon # set to true in production, stops when main thread stops
            
    
    def stop(self):
        self.isRunning = False
    def run(self) -> None:
        self.isRunning = True
        while self.isRunning:
            self.task()
            sleep(self.delay)

        logging.info("worker thread finished")
    