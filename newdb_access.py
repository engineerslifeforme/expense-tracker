""" DB Access object """

from pathlib import Path
from decimal import Decimal

import sqlite3
import pandas as pd
import numpy as np

def generate_where_statement(where_list: list) -> str:
    if len(where_list) > 0:
        return f" WHERE {' AND '.join(where_list)}"
    else:
        return ""

class DbAccess(object):

    def __init__(self, db_file: Path):
        self.con = sqlite3.connect(db_file)
        self.cursor = self.con.cursor()

    def get_statement_transactions(self, 
        include_assigned: bool = True,
        include_deferred: bool = True) -> pd.DataFrame:
        
        sql = 'SELECT * FROM statement_transactions'
        
        where_list = []
        if not include_assigned:
            where_list.append('taction_id IS NULL')
        if not include_deferred:
            where_list.append('deferred = 0')
        sql += generate_where_statement(where_list)
        
        data = pd.read_sql_query(
            sql,
            self.con,
            parse_dates=['date'],
            dtype={'amount': str},
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

    def get_transactions(self,
        amount: Decimal = None,
        after_date: np.datetime64 = None,
        before_date: np.datetime64 = None,
        account_id: int = None,
        only_valid: bool = True):
        
        # amount is the total not the sub
        subs = self.get_subtotals(
            only_valid=only_valid,
        )
        tactions = self.get_tactions(
            after_date=after_date,
            before_date=before_date,
            account_id=account_id,
            only_valid=only_valid,
        ).set_index('id')
        sub_totals = subs[['amount', 'taction_id']].groupby('taction_id').sum().reset_index(drop=False)
        sub_totals = sub_totals.loc[sub_totals['amount']==amount, :]
        transactions = sub_totals.join(tactions, on='taction_id', how='inner', lsuffix='_sub')
        return transactions

    def get_subtotals(self, 
        amount: Decimal = None,
        only_valid: bool = True):
        sql = 'SELECT * FROM sub'

        where_list = []
        if amount is not None:
            where_list.append(f'amount = {amount}')
        if only_valid:
            where_list.append(f'valid = 1')
        sql += generate_where_statement(where_list)
        print(sql)

        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'amount': str},
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

    def get_tactions(self, 
        after_date: np.datetime64 = None,
        before_date: np.datetime64 = None,
        only_valid: bool = True,
        account_id: int = None) -> pd.DataFrame:
        sql = 'SELECT * FROM taction'

        where_list = []
        if after_date is not None:
            where_list.append(f"date >= date('{after_date}')")
        if before_date is not None:
            where_list.append(f"date <= date('{before_date}')")
        if only_valid:
            where_list.append(f'valid = 1')
        if account_id is not None:
            where_list.append(f'account_id = {account_id}')
        sql += generate_where_statement(where_list)
        print(sql)

        data = pd.read_sql_query(
            sql,
            self.con,
            parse_dates=['date'],
        )
        return data
        

