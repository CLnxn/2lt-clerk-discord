from enum import Enum


class CommandErrorType(Enum):
    DEFAULT_EXCEPTION=0
    EXCEED_DAY_OF_MONTH_EXCEPTION=1
    INVALID_FORMAT_EXCEPTION=2

class CommandException(Exception):
    def __init__(self, *args: object, code=CommandErrorType.DEFAULT_EXCEPTION) -> None:
        super().__init__(*args)
        self.code = code