from datetime import datetime

from internals.caching.records import Record


class GenericEventHooks():
    def __init__(self) -> None:
        self.hooks: list = []
    def subscribe(self, hook):
        self.hooks.append(hook)
    def fireEvent(self):
        self.created_timestamp = datetime.now().timestamp()
        return
    
class NewRecordEventHooks(GenericEventHooks):
    def __init__(self) -> None:
        super().__init__()

    def fireEvent(self, record: Record):
        super().fireEvent()
        
        for hook_fn in self.hooks:
            hook_fn(NewRecordEvent(record))
           
class NewRecordEvent():
    def __init__(self, record: Record) -> None:
        self.record = record