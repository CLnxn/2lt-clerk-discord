import internals.database.database as db
import logging

# decorator fn: origin function must have an arg named csr
def handleDBConnection(func):
    def wrapper(*args, **kwargs):
        cnx = db.Database.cnxpool.get_connection()    
        op = func(*args, **kwargs, csr=cnx.cursor())
        cnx.commit()
        cnx.close()
        return op
    return wrapper