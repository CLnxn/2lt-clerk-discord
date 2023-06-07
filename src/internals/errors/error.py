
class LockedError(Exception):
    def __init__(self, source="Resource") -> None:

        super().__init__(f"{source} is locked.")

class CacheInitError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
