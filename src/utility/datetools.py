
from datetime import datetime
import calendar

from commands.exceptions.errors import CommandErrorType
import utility.validator as validator

def get_last_day_of_mth(date: datetime):
        return calendar.monthrange(date.year, date.month)[1]

def getRemainingDaysInMonth(date: datetime):
        return get_last_day_of_mth(date) - date.day


def isDayOfMonth(input) -> tuple[bool, CommandErrorType | int]:

        status, digitOrErrObj = validator.isInt(input)
        if not status:
            return False, digitOrErrObj
        try:
            dom = int(input)
            max_dom = get_last_day_of_mth(datetime.now())
            if dom <=0 or dom > max_dom:
                raise Exception()
        except:
            return False, CommandErrorType.EXCEED_DAY_OF_MONTH_EXCEPTION
        
        return True, digitOrErrObj


