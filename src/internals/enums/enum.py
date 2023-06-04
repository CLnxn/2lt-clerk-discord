from enum import Enum

class InternalTypes(Enum):
    ID = "id"
    USER_ID = "user_id"
    USERS = "users"
    NS = "ns"
    NS_DATETIME_FIELD = "ord_date"
    NS_PAY_AMOUNT_FIELD = "pay_amt"
    NS_PAY_DAY_OF_MTH_FIELD = "pay_dom"
    REMINDERS = "reminders"

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

class QueryToken(Enum):
    WILDCARD = '*'


class ApiErrors(Enum):
    INVALID_USER_ID_ERROR=0
    EMPTY_RECORDS_ERROR=1
    CACHE_MISS_ERROR=2