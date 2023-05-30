

class Cache():
    ENTRY_LIMIT = 20
    
    def __init__(self) -> None:

        self.retrieveRecords()

    def update(self, key,value):
        pass

    def retrieveRecords(self):
        """Gets the first ENTRY_LIMIT records from the db and inserts into self.cache"""
        pass