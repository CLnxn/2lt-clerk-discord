from internals.enums.enum import QueryToken
import typing
DEFAULT_TABLES = ['ns','users','reminders']
class Query():
    
    def __init__(self, mode: typing.Literal['r','w','d', 'u'] ='r', selectAll=True) -> None:
        """ Builds a query sorted by insertion order\n
        Args:
            mode (str): 'r', 'w', 'd', or 'u' represents read, write, delete & update query respectively.
        Fields:
            self.query: {
                            "first_n": int | None (defaults to 1 for r mode):\n
                                First n entries of each table to return. Returns the min(n,table entry size) of entries.\n
                            "tables": list[str] | None (defaults to []):\n
                                Specifies the tables in which to return entries from.\n
                            "columns": 
                                In r mode, {tablename:[column1,...]} | None (defaults to {}):\n 
                                specifies what columns of each table to return.\n
                                In w mode, this structure is instead: {tablename: {column1:value1,...}} | None (defaults to {}):\n
                                specifies the columns of a table to update with the indicated value.
                        }
            self.matcher: {
                            tablename: {
                                col_name: match_value,...
                            },
                            ...
                        }: Specifies to only return queries for each tablename in the query that match the column values specified in the matcher. 
            self.mode: refer to Args,
            self.selectAll: specifies if all columns of every table should be selected. ('r' mode only)  
        """
        self.query = {}
        self.matcher:dict[str,dict] = {}
        self.mode = mode
        self.selectAll = selectAll
        self._initQueryDefaults()
    def _initQueryDefaults(self):
        if self.mode == 'r':
            self.query["first_n"] = 1
            self.query["tables"] = []
            if self.selectAll:
                self.query["columns"] = {tbl: QueryToken.WILDCARD.value for tbl in DEFAULT_TABLES}
            else:
                self.query["columns"] = {}
        elif self.mode == 'w' or self.mode == 'd' or self.mode=='u':
            self.query["tables"] = []
            self.query["columns"] = {}

    def addMatcher(self, table:str, cols: dict[str,str]):
        if table not in self.matcher:
            self.matcher[table] = cols
            return 
        for key in cols:
            self.matcher[table][key] = cols[key]
    def setLimit(self, n: int):
        # illegal n
        if n <= 0:
            return
        self.query["first_n"] = n
    
    def initTables(self, tables: list[str]):
        """Sets tables as given in args and initialises empty columns for them. No Op if empty list or other datatype is provided."""
        # ignore empty tables
        if tables == [] or type(tables) != list:
            return
        self.query["tables"] = tables
        self.updateColumns()

    def addNewTable(self, table: str):
        """Adds a new table entry into the query. Replaces existing table if present"""
        if table not in self.query["tables"]:
            self.query["tables"].append(table) 
            self.setTableColumn(table)

    def updateColumns(self):
        for table_name in self.query["tables"]:
            self.setTableColumn(table_name)
    def deleteColumnForTable(self, table: str, col_name):
        if col_name in self.query["columns"][table]:
            if self.mode == 'r':
                self.query["columns"][table].remove(col_name)
                # list type
            else:
                del self.query["columns"][table][col_name]
                # dict type


    def setTableColumn(self, table:str, columns: list[str] | dict[str,str]=None):
        if not columns:
            if self.mode == 'r':
                columns = QueryToken.WILDCARD.value
            elif self.mode == 'w':
                columns = {}
            else: 
                columns = QueryToken.WILDCARD.value
        self.query["columns"][table] = columns
    def getMatcherForTable(self, table: str):
        return self.matcher[table]
    def getAllTableColumns(self) -> dict[str, list | str] | dict[str, dict]:
        return self.query["columns"]
    def getTableColumn(self, table:str):
        if table in self.query["columns"]:
            return self.query["columns"][table]
        if self.mode == 'r':
            return []
        elif self.mode == 'w':
            return {}
    def getTableNames(self) -> list[str]:
        return self.query["tables"]
    def getLimit(self) -> int:
        return self.query["first_n"]
    
    def _matcherToSQLForTable(self, table: str):
        """returns an sql WHERE clause for a particular table query based on self.matcher"""
        match_component = ''
        if table in self.matcher:
            match_component += 'WHERE '
            for match_col in self.matcher[table]:
                val = self.matcher[table][match_col]
                if type(val) == str:
                    val = '\''+val+'\''
                match_component += '{0}={1} AND '.format(match_col, val)
            match_component = match_component[:-5]
        return match_component
    def getReadSQLs(self) -> list | None:
        """
        Should only called for self.mode='r'.\n
        Returns:
            a list of tuples (table_name, sqlstring) for each sqlstring query
            OR
            None if query is not in r mode.
        """
        if self.mode !='r':
            return None
        sqls = []
        for table in self.query["tables"]:
            sqlstring = "SELECT {0} FROM {1} {2} LIMIT {3};" # LIMIT is a mysql only statement
            
            cols = self.query["columns"][table] # cols = * in r mode
            # building {0}
            if type(cols) == list:
                cols = _buildSQLQueryColumns(cols, quotes=False)
            # building {2}
            match_component = self._matcherToSQLForTable(table)

            sqlstring = sqlstring.format(cols, table, match_component, self.query["first_n"])
            sqls.append((table, sqlstring))

        return sqls
    # In the future might want to figure out a way to group queries of the same value size together without messing up insertion order
    # Allows for bulk insertions which are less costly
    def getWriteSQLs(self) -> list | None:
        if self.mode != 'w':
            return None
        sqls = []
        # build 
        alias = 'AL1QS'
        for table in self.query["tables"]:
            sqlstring = "INSERT INTO {0} {1} VALUES {2} ON DUPLICATE KEY UPDATE {3};"

            # build {1}
            cols_vals: dict[str,str] = self.query["columns"][table]
            cols = _buildSQLQueryColumns(cols_vals, wrap=True, quotes=False)

            # build {2}
            vals = _buildSQLQueryColumns(cols_vals.values(), wrap=True)
            # build {3}
            rules = _buildSQLRulesForTable(cols_vals, table)
            sqlstring = sqlstring.format(table,cols,vals, rules)
            sqls.append((table,sqlstring))
        return sqls
    

    def getDeleteSQLs(self):
        sqls = []
        for table in self.query["tables"]:
            sqlstring = "DELETE FROM {0} {1};"
            where_clause = self._matcherToSQLForTable(table)

            sqlstring = sqlstring.format(table,where_clause)
            sqls.append((table, sqlstring))
        return sqls
    def getUpdateSQLs(self):
        sqls = []
        for table in self.query["tables"]:
            sqlstring = "UPDATE {0} SET {1} {2};"
            where_clause = self._matcherToSQLForTable(table)
            rules = _buildSQLRulesForTable(self.getTableColumn(table), table)
            sqlstring = sqlstring.format(table, rules, where_clause)
            sqls.append((table, sqlstring))
        return sqls
    

def _buildSQLQueryColumns(cols: list[typing.Any], wrap=False, wrap_tokens='()', quotes=True):
    colstr = ''
    for col in cols:
        if quotes and type(col) == str:
            colstr += '\''+ col + '\'' + ','
        else:
            colstr += str(col) + ','
    colstr = colstr[:-1]

    if wrap:
        return wrap_tokens[0] + colstr + wrap_tokens[1]
    
    return colstr

def _buildSQLRulesForTable(cols, table):
    """Returns an sql string forming the SET clause heading in the UPDATE directive (or the UPDATE clause heading in ON DUPLICATE UPDATE)"""
    rules = ''
    for col in cols:
        rules += table + '.' + col + '=VALUES('+ col +'),' 
    rules = rules[:-1]
    return rules