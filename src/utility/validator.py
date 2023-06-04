from dateutil.parser import parse

from commands.exceptions.errors import CommandErrorType
DATE_FORMAT='DD/MM/YYYY'
DATE_SPLIT_TOKEN = '/'
def datestring_validator(date_string, format=DATE_FORMAT, split_token=DATE_SPLIT_TOKEN):
    try:
        date = parse(date_string, dayfirst=True)    
        return (True, date)
    except Exception as e:
        return (False, e)


def isFloat(input):
    try:
        try_float = float(input)
        valid = str(try_float).replace('.','').isdigit()
        if not valid:
            return False, CommandErrorType.INVALID_FORMAT_EXCEPTION
    except:
        return False, CommandErrorType.INVALID_FORMAT_EXCEPTION
    else:
        return True, try_float
    
def isInt(input):
    try:        
        digit = int(input)
        isdigit = str(input).isdigit()
        if not isdigit:
            return False, CommandErrorType.INVALID_FORMAT_EXCEPTION
    except:
        return False, CommandErrorType.INVALID_FORMAT_EXCEPTION
    else:        
        return True, digit