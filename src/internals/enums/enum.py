from enum import Enum, IntEnum

class InternalTypes(Enum):
    ID = "id"
    
    CHANNELS = "channels"
    CHANNEL_ID ="channel_id"
    
    USERS = "users"
    USER_ID = "user_id"

    GUILDS = "guilds"
    GUILD_ID = "guild_id"

    NS = "ns"
    NS_DATETIME_FIELD = "ord_date"
    NS_PAY_AMOUNT_FIELD = "pay_amt"
    NS_PAY_DAY_OF_MTH_FIELD = "pay_dom"
    
    REMINDERS = "reminders"
    REMINDERS_CONTENT_FIELD ="content"
    REMINDERS_DATE_DEADLINE_FIELD="date_deadline"
    REMINDERS_DATE_CREATED_FIELD="date_created"
    REMINDERS_SCOPE_FIELD="scope"

    WILDCARD = '*'
class RemindersScope(IntEnum):
    PERSONAL=0 # private user channel
    GUILD=1 # guild channel
    NO_GUILD_CHANNEL=2 # channels not in guilds (chat grps etc.)

class InternalMethodTypes(Enum):
    SET = 'set'
    UPDATE = 'update'
    DELETE = 'delete'
    INSERT = 'insert'
    GET = 'get'
class EventType(Enum):
    GENERIC_EVENT = -1
    NEW_RECORD_EVENT = 0
    NEW_GET_RECORD_EVENT = 1
    NEW_DELETE_RECORD_EVENT = 2
    NEW_UPDATE_RECORD_EVENT = 3
    FLUSH_EVENT = 4

class QueryToken(Enum):
    WILDCARD = '*'


class ApiErrors(Enum):
    INVALID_USER_ID_ERROR=0
    INVALID_CACHE_KEY_ERROR=0
    EMPTY_RECORDS_ERROR=1
    CACHE_MISS_ERROR=2
    LOCK_ERROR = 3