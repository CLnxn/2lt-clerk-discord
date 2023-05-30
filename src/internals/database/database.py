import mysql.connector
from mysql.connector import errorcode
from env import DB as config
import logging
query = dict[str,list]

class Database():
    def __init__(self) -> None:
        self.connect()
        self.initialiseDB()
    def connect(self):
        try:
            logging.debug(config)
            self.cnx = mysql.connector.connect(**config)
            
            logging.debug(f"connection: {self.cnx}")
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.warning("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.warning("Database does not exist")
            else:
                logging.warning(err)
        
    def initialiseDB(self):
        cursor = self.cnx.cursor()
        cursor.execute('USE service_bot') # no need to put EOL token
        cursor.execute('SELECT * FROM users')
        for entry in cursor:
            logging.debug(entry)

    def _flushToDB(self):
        self.cnx.commit()
    def updateUsers(self, username: str, columns:query):
        pass
    
    
    def getUsers(self):
        pass

