from dateutil.parser import parse
import datetime
DATE_FORMAT='DD/MM/YYYY'
DATE_SPLIT_TOKEN = '/'
def datestring_validator(date_string, format=DATE_FORMAT, split_token=DATE_SPLIT_TOKEN):
    try:
        date = parse(date_string)    
        return (True, date)
    except Exception as e:
        return (False, e)
    