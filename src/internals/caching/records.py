
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes

class Record():
    def __init__(self, method: InternalMethodTypes, owner_id, data: Query) -> None:
        self.type = method # update, set, delete, add
        self.data: Query = data # {tablename: {col:data, col2:data, ...}}
        self.owner_id = owner_id # same as user_id
