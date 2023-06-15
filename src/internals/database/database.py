import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector import errorcode
from env import DB as config
from internals.database.queryfactory import Query
import internals.database.mixins as mixins
from internals.enums.enum import QueryToken, InternalTypes
import logging, traceback

query = dict[str,list]

logger = logging.getLogger("mysql.connector")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s- %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)



USERS_REFERENCED_TABLES = ['users','ns','reminders']
GUILDS_REFERENCED_TABLES =['guilds','reminders','channels']

REMINDERS_TABLE_COLUMNS = [InternalTypes.ID.value,
                           InternalTypes.USER_ID.value,
                           InternalTypes.GUILD_ID.value,
                           InternalTypes.CHANNEL_ID.value,
                           InternalTypes.REMINDERS_CONTENT_FIELD.value,
                           InternalTypes.REMINDERS_DATE_CREATED_FIELD.value,
                           InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value,
                           InternalTypes.REMINDERS_REPEATED_FIELD.value,
                           InternalTypes.REMINDERS_SCOPE_FIELD.value,
                           InternalTypes.REMINDERS_CACHE_ID_FIELD.value
                           ]
class Database():
    def __init__(self) -> None:
        result = self.connect()
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
            return False
        return True
    @mixins.handleDBConnection
    def initialiseDB(self, csr: MySQLCursor = None):
        csr.execute('USE service_bot')
        # TESTING PURPOSES:
        csr.execute("INSERT INTO reminders (user_id,content,date_created, date_deadline) VALUES (1,'xd',NOW(), NOW()+ INTERVAL 5 SECOND);")
        csr.execute("INSERT INTO reminders (user_id,content,date_created, date_deadline) VALUES (1,'xd',NOW(), NOW()+ INTERVAL 5 SECOND);")
    
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
    def getDatedReminders(self, datetime_min: str, datetime_max:str, limit=2000, csr: MySQLCursor=None):
        """ Gets all reminders before and equal to the <datetime_max> datetime in string.
            This method is rather expensive & inefficient and should be called infrequently.
            Returns:
                a list of reminder objects, sorted from earliest to latest
        """
        dated_condition = "{0}>='{1}' AND {0}<='{2}'".format(
            InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value,
            datetime_min,
            datetime_max
        )
        query = "SELECT * FROM {0} WHERE {1} ORDER BY {2} ASC LIMIT {3};".format(
            InternalTypes.REMINDERS.value,
            dated_condition,
            InternalTypes.REMINDERS_DATE_DEADLINE_FIELD.value,
            limit
            )
        labeled = []
        try:
            csr.execute(query)
            rows = csr.fetchall()
            cols = csr.column_names
            labeled = self.labelColumns(rows, cols)
        except mysql.connector.Error as err:
            logging.critical(f"Error in retrieving dates. Error: {err}")
        return labeled
    
    @mixins.handleDBConnection
    def getEntriesFromTables(self, db_query: Query, csr: MySQLCursor=None):
        """ This method call is expensive. Should only be used to initialise internal caches/Cache Miss.\n 
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
                cols = csr.column_names
                # reshaping data
                results[table] = self.labelColumns(rows, cols)
            except mysql.connector.Error as err:
                logging.critical(f"Error in finding data. Error: {err}")
                return {}
        
        return results
    
    def labelColumns(self, rows, cols):
        """ helper function to add columns (<cols>: tuple[col_name]) to each column in each datarow in <rows>:  list[{val1,val2,...}]
        
        Returns: 
            List[{col1:val1,...}]
            """
        ln = len(cols) 
        return [{cols[i]:row[i] for i in range(ln)} for row in rows]