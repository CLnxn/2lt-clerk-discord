import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector import errorcode
from env import DB as config
from internals.database.queryfactory import Query
import internals.database.mixins as mixins
from internals.enums.enum import QueryToken
import logging, traceback

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
            Database.cnxpool = mysql.connector.pooling.MySQLConnectionPool(
                                pool_name = "db_pool",
                                pool_size = 3,
                                pool_reset_session=True,
                                **config)
            
        except mysql.connector.Error as err:
            traceback.print_exc()
            logging.error(err)

    @mixins.handleDBConnection
    def initialiseDB(self, csr: MySQLCursor = None):
        csr.execute('USE service_bot')

    
    @mixins.handleDBConnection
    def deleteFromTables(self, db_queries: list[Query], csr: MySQLCursor=None):
        pass
    @mixins.handleDBConnection
    def writeToTables(self, db_queries: list[Query], csr: MySQLCursor=None):
        for db_query in db_queries:
            sql_queries = db_query.getWriteSQLs()
            logging.info(f"writing queries to DB: {sql_queries}")
            for table, sql_query in sql_queries:
                try:
                    csr.execute(sql_query)
                except mysql.connector.Error as err:
                    logging.critical(f"Error in uploading data. Error: {err}")

    @mixins.handleDBConnection
    def getEntriesFromTables(self, db_query: Query, csr: MySQLCursor=None):
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
        sql_queries = db_query.getReadSQLs()
        results = {}
        logging.info(sql_queries)
        for table, sql_query in sql_queries:
            try:
                csr.execute(sql_query)
                rows = csr.fetchall()
                # reshaping data
                cols = csr.column_names
                ln = len(cols) 
                results[table] = [{cols[i]:row[i] for i in range(ln)} for row in rows]
            except mysql.connector.Error as err:
                logging.critical(f"Error in finding data. Error: {err}")
                return {}
        
        return results

