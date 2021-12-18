""" DB Access object """

from pathlib import Path
from decimal import Decimal

import sqlite3
import pandas as pd

class DbAccess(object):

    def __init__(self, db_file: Path):
        self.con = sqlite3.connect(db_file)
        self.cursor = self.con.cursor()

    def get_statement_transactions(self, 
        include_assigned: bool = True,
        include_deferred: bool = True) -> pd.DataFrame:
        
        sql = 'SELECT * FROM statement_transactions'
        if not include_assigned or not include_deferred:
            where_list = []
            if not include_assigned:
                where_list.append('taction_id IS NULL')
            if not include_deferred:
                where_list.append('deferred = 0')
            sql += f" WHERE {' AND '.join(where_list)}"
        print(sql)
        data = pd.read_sql_query(
            sql,
            self.con,
            parse_dates=['date'],
            dtype={'amount': str},
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

    #def get_transactions

    def get_subtotals(self):
        sql = 'SELECT * FROM sub'
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'amount': str},
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

