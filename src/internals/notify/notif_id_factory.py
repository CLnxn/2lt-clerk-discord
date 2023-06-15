import uuid
class NotifIDFactory():
    saved = set()
    # might have to optimise if memory is significantly affected in production
    def createUnique():
        id = uuid.uuid4().int

        if id not in NotifIDFactory.saved:
            NotifIDFactory.saved.add(id)
        else:
            id = NotifIDFactory.createUnique()
        return id