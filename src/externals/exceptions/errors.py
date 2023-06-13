from enum import Enum


class CommandErrorType(Enum):
    DEFAULT_EXCEPTION=0
    EXCEED_DAY_OF_MONTH_EXCEPTION=1
    INVALID_FORMAT_EXCEPTION=2
    INVALID_GUILD_EXCEPTION=3
    INVALID_CHANNEL_EXCEPTION=4
    INVALID_USER_EXCEPTION=5
    
class GenericErrorType(Enum):
    GENERIC_EXCEPTION = 0

class CommandException(Exception):
    def __init__(self, *args: object, code=CommandErrorType.DEFAULT_EXCEPTION, data=None) -> None:
        super().__init__(*args)
        self.code = code
        self.data=data

def error(errorType: CommandErrorType | GenericErrorType, data=None):
    raise CommandException(code=errorType, data=data)