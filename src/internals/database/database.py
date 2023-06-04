import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector import errorcode
from env import DB as config
from internals.database.queryfactory import Query
from internals.enums.enum import QueryToken
import logging

query = dict[str,list]

logger = logging.getLogger("mysql.connector")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s- %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

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


    def deleteFromTables(self, db_queries: list[Query]):
        pass
    def writeToTables(self, db_queries: list[Query]):
        csr = self.cnx.cursor()
        for db_query in db_queries:
            sql_queries = db_query.get_as_WRITE_SQL_queries()
            logging.info(f"writing queries to DB: {sql_queries}")
            for table, sql_query in sql_queries:
                try:
                    csr.execute(sql_query)
                except mysql.connector.Error as err:
                    logging.critical(f"Error in uploading data. Error: {err}")

        self.cnx.commit()

    def getEntriesFromTables(self, db_query: Query):
        """ This method call is expensive. Should only be used to initialise internal caches.\n 
        Args:
            db_query (Query): standardised database query
        Returns:
                {"tablename": 
                    [
                        { #entry 1
                            col_name:val, 
                            col2_name:val2, 
                            ...etc
                        },

                        { #entry 2
                            col_name:val, 
                            col2_name:val2, 
                            ...etc
                        },
                        ...
                    ]
                }
        """
        sql_queries = db_query.get_as_READ_SQL_queries()
        csr = self.cnx.cursor()
        results = {}
        logging.info(sql_queries)
        for table, sql_query in sql_queries:
            try:
                csr.execute(sql_query)
                rows = csr.fetchall()
                logging.debug(csr.column_names)
                # reshaping data
                cols = csr.column_names
                ln = len(cols) 
                results[table] = [{cols[i]:row[i] for i in range(ln)} for row in rows]
            except mysql.connector.Error as err:
                logging.critical(f"Error in finding data. Error: {err}")
                return {}
        
        return results

