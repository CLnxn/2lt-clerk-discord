from enum import Enum

class InternalTypes(Enum):
    USER_ID = "user_id"
    USERS = "users"
    NS = "ns"
    NS_DATETIME_FIELD = "ord_date"
    NS_PAY_AMOUNT_FIELD = "pay_amt"
    NS_PAY_DAY_OF_MTH_FIELD = "pay_dom"
    REMINDERS = "reminders"
    DEFAULT_TABLES = ['ns','users','reminders']

class InternalMethodTypes(Enum):
    SET = 'set'
    UPDATE = 'update'
    DELETE = 'delete'
    INSERT = 'insert'
    GET = 'get'