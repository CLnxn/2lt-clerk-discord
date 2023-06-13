
from internals.database.queryfactory import Query
from internals.enums.enum import InternalMethodTypes, InternalTypes

class Record():
    def __init__(self, method: InternalMethodTypes, owner_id, data: Query, rtype= InternalTypes.USERS) -> None:
        self.method = method # update, set, delete, add
        self.data: Query = data # {tablename: {col:data, col2:data, ...}}
        self.id_map= {rtype:owner_id} # same as user_id or can also be guild_id for guild level storage
        self.rtype = rtype
    # adding will cause rtype to be <InternalTypes.WILDCARD>
    def addIDType(self, id, type: InternalTypes):
        self.id_map[type] = id
        if len(self.id_map) > 1:
            self.rtype = InternalTypes.WILDCARD