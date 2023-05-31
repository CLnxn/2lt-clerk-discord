
class Query():
    
    def __init__(self, mode='r') -> None:
        """ Builds a query sorted by insertion order\n
        Args:
            mode (str): 'r', 'w' or 'd', represents read, write and delete query respectively.
        Fields:
            self.query: {
                            "first_n": int | None (defaults to 1 for r mode):\n
                                First n entries of each table to return. Returns the min(n,table entry size) of entries.\n
                            "tables": list[str] | None (defaults to []):\n
                                Specifies the tables in which to return entries from.\n
                            "columns": 
                                In r mode, {tablename:[column1,...]} | None (defaults to {tablename1:*, tablename2:*, ...}):\n 
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
            self.mode: refer to Args
        """
        self.query = {}
        self.matcher:dict[str,dict] = {}
        self.mode = mode
        self._init_defaults()
    def _init_defaults(self):
        if self.mode == 'r':
            self.query["first_n"] = 1
            self.query["tables"] = []
            self.query["columns"] = {'ns':'*'}
        elif self.mode == 'w' or self.mode == 'd':
            self.query["tables"] = []
            self.query["columns"] = {}

    def add_matcher(self, table:str, cols: dict[str,str]):
        if not self.matcher[table]:
            self.matcher[table] = cols
            return 
        for key in cols:
            self.matcher[table][key] = cols[key]
    
    def set_first_n(self, n: int):
        # illegal n
        if n <= 0:
            return
        self.query["first_n"] = n
    
    def set_tables(self, tables: list[str]):
        # ignore empty tables
        if tables == []:
            return
        self.query["tables"] = tables
        self.update_columns()

    def add_table(self, table: str):
        if table not in self.query["tables"]:
            self.query["tables"].append(table) 
            self.set_columns_for_table(table)

    def update_columns(self):
        for table_name in self.query["tables"]:
            self.set_columns_for_table(table_name)


    def set_columns_for_table(self, table:str, columns: list[str] | dict[str,str]=None):
        if not columns:
            if self.mode == 'r':
                columns = '*'
            elif self.mode == 'w':
                columns = {}
            else: 
                columns = '*'
        self.query["columns"][table] = columns
    
    def get_tables(self) -> list[str]:
        return self.query["tables"]
    def get_first_n(self) -> int:
        return self.query["first_n"]
    
    def get_as_READ_SQL_queries(self) -> list | None:
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
                cols = _build_columns_sql_query(cols)
            # building {2}
            match_component = ''
            if self.matcher[table]:
                match_component += 'WHERE '
                for match_col in self.matcher[table]:
                    match_component += '{0}={1} AND '.format(match_col, self.matcher[table][match_col])
                match_component = match_component[:-5]

            sqlstring = sqlstring.format(cols, table, match_component, self.query["first_n"])
            sqls.append((table, sqlstring))

        return sqls
    # In the future might want to figure out a way to group queries of the same value size together without messing up insertion order
    # Allows for bulk insertions which are less costly
    def get_as_WRITE_SQL_queries(self) -> list | None:
        if self.mode != 'w':
            return None
        for table in self.query["tables"]:
            sqlstring = "INSERT INTO {0} {1} VALUES {2} ON DUPLICATE KEY UPDATE {3}"

            # build {1}
            cols_vals: dict[str,str] = self.query["columns"][table]
            cols = _build_columns_sql_query(cols_vals, wrap=True)

            # build {2}
            vals = _build_columns_sql_query(cols_vals.values(), wrap=True)
            
            # build {3}
            

def _build_columns_sql_query(cols: list[str], wrap=False, wrap_tokens='()'):
    colstr = ''
    for col in cols:
        if type(col) == str:
            colstr += '\''+ col + '\'' + ','
        else:
            colstr += col + ','
    colstr = colstr[:-1]

    if wrap:
        return wrap_tokens[0] + colstr + wrap_tokens[1]
    
    return colstr