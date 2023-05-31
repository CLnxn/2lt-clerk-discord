
from internals.database.queryfactory import Query


class Record():
    def __init__(self, method, owner_id, data: Query) -> None:
        self.method = method # update, set, delete, add
        self.data: Query = data # {tablename: {col:data, col2:data, ...}}
        self.owner_id = owner_id # same as user_id
