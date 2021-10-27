""" DB Access object """

from pathlib import Path

import sqlite3
import pandas as pd

class DbAccess(object):

    def __init__(self, path_to_database: Path):
        self.con = sqlite3.connect(path_to_database)
        self.cursor = self.con.cursor()
        self.load_data()
        self.build_maps()
        self.build_views()

    # defining a decorator

    def refresh(func):
    
        def inner1(self, *args, **kwargs):            
            func(self, *args, **kwargs)
            self.load_data()
            self.build_maps()
            self.build_views()
          
        return inner1

    def get_data(self, table_name: str) -> pd.DataFrame:
        if table_name == 'account':
            return self.accounts
        elif table_name == 'sub':
            return self.subs
        elif table_name == 'taction':
            return self.tactions
        elif table_name == 'method':
            return self.methods
        elif table_name == 'category':
            return self.categories
        elif table_name == 'budget':
            return self.budgets
        else:
            return None

    def load_data(self):
        self.accounts = pd.read_sql_query(
            'SELECT * FROM account',
            self.con
        )
        self.subs = pd.read_sql_query(
            'SELECT * FROM sub',
            self.con
        )
        self.tactions = pd.read_sql_query(
            'SELECT * FROM taction',
            self.con
        )
        self.tactions['date'] = pd.to_datetime(self.tactions['date'])
        self.methods = pd.read_sql_query(
            'SELECT * from method',
            self.con
        )
        self.categories = pd.read_sql_query(
            'SELECT * FROM category',
            self.con
        )
        self.budgets = pd.read_sql_query(
            'SELECT * FROM budget',
            self.con
        )
        self.statement_transactions = pd.read_sql_query(
            'SELECT * FROM statement_transactions',
            self.con
        )

        self.max_taction_id = max(self.tactions['id'])
        self.max_sub_id = max(self.subs['id'])
        if len(self.statement_transactions) > 0:
            self.max_statement_transactions_id = max(self.statement_transactions['id'])
        else:
            self.max_statement_transactions_id = -1

    def build_maps(self):
        self.method_map = {item['id']: item['name'] for item in self.methods.to_dict(orient='records')}
        self.method_map_reverse = {item['name']: item['id'] for item in self.methods.to_dict(orient='records')}
        self.category_map = {item['id']: item['name'] for item in self.categories.to_dict(orient='records')}
        self.category_map_reverse = {item['name']: item['id'] for item in self.categories.to_dict(orient='records')}
        self.account_map = {item['id']: item['name'] for item in self.accounts.to_dict(orient='records')}
        self.account_map_reverse = {item['name']: item['id'] for item in self.accounts.to_dict(orient='records')}
        self.budget_map = {item['id']: item['name'] for item in self.budgets.to_dict(orient='records')}
        self.budget_map_reverse = {item['name']: item['id'] for item in self.budgets.to_dict(orient='records')}
        self.category_to_budget_map = {item['id']: item['budget_id'] for item in self.categories.to_dict(orient='records')}

    def build_views(self):
        sub_totals = self.subs[['taction_id', 'amount']].groupby('taction_id').sum().reset_index()
        self.transactions = sub_totals.join(self.tactions.set_index('id', drop=False), on='taction_id', lsuffix='_sub').reset_index().sort_values(by=['date'], ascending=False)
        self.transactions['method'] = self.transactions['method_id'].map(self.method_map)
        self.transactions['account'] = self.transactions['account_id'].map(self.account_map)
        
        self.subview = self.subs.join(self.tactions.set_index('id', drop=False), on='taction_id', lsuffix='_sub').reset_index().sort_values(by=['date'], ascending=False)
        self.subview['budget_id'] = self.subview['category_id'].map(self.category_to_budget_map)
        self.subview['budget'] = self.subview['budget_id'].map(self.budget_map)

    def delete_transaction(self, transaction_id: int):
        subs = self.subs.loc[self.subs['taction_id'] == transaction_id, :]
        amount = 0
        for sub in subs.to_dict(orient='records'):
            if sub['valid'] != 1:
                raise ValueError('Sub was not valid')
            sub_amount = sub['amount']
            amount += sub_amount
            self.update_budget(-1*sub_amount, sub['category_id'])
            self._update(
                'sub', 'valid', 0, sub['id']
            )
        account_id = self.tactions.loc[self.tactions['id'] == transaction_id, 'account_id'].values[0]
        taction_valid = self.tactions.loc[self.tactions['id'] == transaction_id, 'valid'].values[0]
        if taction_valid != 1:
            raise ValueError('taction was not valid')
        self.update_account(-1*amount, self.account_map[account_id])
        self._update(
            'taction', 'valid', 0, transaction_id
        )

    def add_transfer(self, date, withdrawal_account: str, deposit_account: str, description, receipt, amount: float):
        withdraw_amount = -1 * amount
        self.add_transaction(
            date,
            withdrawal_account,
            'Automated',
            description,
            receipt,
            withdraw_amount,
            [(withdraw_amount, 'Transfer')],
            transfer=True,
        )
        self.add_transaction(
            date,
            deposit_account,
            'Automated',
            description,
            receipt,
            amount,
            [(amount, 'Transfer')],
            transfer=True,
        )

    def add_transaction(self, date, account: str, method: str, description: str, receipt: bool, amount: float, subs: list, transfer: bool = False):
        new_id = self.add_taction(
            date,
            transfer,
            self.account_map_reverse[account],
            self.method_map_reverse[method],
            description,
            receipt,
            True,
            False,
        )
        self.update_account(amount, account)
        for sub in subs:
            sub_amount = sub[0]
            category_id = self.category_map_reverse[sub[1]]
            self.add_sub(
                sub_amount,
                category_id,
                new_id,
                True,
                False,
            )
            self.update_budget(sub_amount, category_id)
        return new_id

    def update_account(self, amount: float, account: str):
        self._update_add(
            'account',
            'balance',
            amount,
            self.account_map_reverse[account],
        )

    def update_budget(self, amount: float, category_id: int):
        self._update_add(
            'budget',
            'balance',
            amount,
            self.category_to_budget_map[category_id],
        )

    @refresh
    def _update_add(self, table_name: str, field_name: str, amount: float, item_id: int):
        self.cursor.execute(f"UPDATE {table_name} SET {field_name}={field_name}+{amount} WHERE id={item_id}")
        self.con.commit()

    @refresh
    def _update(self, table_name: str, field_name: str, in_new_value, item_id: int, use_quotes: bool = False):
        if use_quotes:
            new_value = f"'{in_new_value}'"
        else:
            new_value = in_new_value
        self.cursor.execute(f"UPDATE {table_name} SET {field_name}={new_value} WHERE id={item_id}")
        self.con.commit()

    def add_sub(self, amount: float, category_id: int, taction_id: int, valid: bool, not_real: bool):
        fields = [
            'id',
            'amount',
            'category_id',
            'taction_id',
            'valid',
            'not_real',
        ]
        new_id = self.get_next_sub_id()

        if valid:
            valid_int = 1
        else:
            valid_int = 0
        if not_real:
            not_real_int = 1
        else:
            not_real_int = 0

        self._insert('sub', fields, [
            new_id,
            amount,
            category_id,
            taction_id,
            valid_int,
            not_real_int,
        ])
        return new_id

    def get_next_taction_id(self):
        self.max_taction_id += 1
        return self.max_taction_id

    def get_next_sub_id(self):
        self.max_sub_id += 1
        return self.max_sub_id
    
    def add_taction(self, date, transfer: bool, account_id: int, method_id: int, description: str, receipt: bool, valid: bool, not_real: bool):
        fields = [
            'id',
            'date',
            'transfer',
            'account_id',
            'method_id',
            'description',
            'receipt',
            'valid',
            'not_real',
        ]
        new_id = self.get_next_taction_id()

        if transfer:
            transfer_int = 1
        else:
            transfer_int = 0
        if valid:
            valid_int = 1
        else:
            valid_int = 0
        if receipt:
            receipt_int = 1
        else:
            receipt_int = 0
        if not_real:
            not_real_int = 1
        else:
            not_real_int = 0

        self._insert('taction', fields, [
            new_id,
            date,
            transfer_int,
            account_id,
            method_id,
            description,
            receipt_int,
            valid_int,
            not_real_int,
        ])
        return new_id

    def get_next_statement_transaction_id(self):
        self.max_statement_transactions_id += 1
        return self.max_statement_transactions_id

    def add_statement_transaction(self, date, month:int, year:int, account_id:int, amount:float, description:str = None):
        fields = [
            'id',
            'date',
            'statement_month',
            'statement_year',
            'account_id',
            'amount',
        ]
        new_id = self.get_next_statement_transaction_id()
        values = [
            new_id,
            date,
            month,
            year,
            account_id,
            amount
        ]
        if description is not None:
            fields.append('description')        
            values.append(description)
        self._insert('statement_transactions', fields, values)

    @refresh
    def _insert(self, table: str, fields: list, values: list):
        fields_str = ', '.join(fields)
        str_values = [str(value) for value in values]
        values_str = "\"" + "\", \"".join(str_values) + "\""
        self.cursor.execute(f"INSERT INTO {table} ({fields_str}) VALUES ({values_str})")
        self.con.commit()

    def add_account(self, name: str, balance: float, purpose: str):
        new_id = max(self.accounts['id']) + 1
        self._insert(
            'account',
            [
                'id',
                'name',
                'balance',
                'valid',
                'visibility',
                'purpose',
            ],
            [
                new_id,
                name,
                balance,
                1,
                1,
                purpose
            ]
        )

    def add_budget(self, name: str, balance: float, purpose: str, update_frequency: str, update_amount: float) -> int:
        new_id = max(self.budgets['id']) + 1
        self._insert(
            'budget',
            [
                'id',
                'name',
                'balance',
                'visibility',
                'frequency',
                'increment',
                'valid',
                'purpose',
            ],
            [
                new_id,
                name,
                balance,
                1,
                update_frequency,
                update_amount,
                1,
                purpose,
            ]
        )
        return new_id

    def add_category(self, name: str, budget_name: str):
        new_id = max(self.categories['id']) + 1
        budget_id = self.budget_map_reverse[budget_name]
        self._insert(
            'category',
            [
                'id',
                'name',
                'budget_id',
                'valid',
                'no_kid_retire',
                'kid_retire',
            ],
            [
                new_id,
                name,
                budget_id,
                1,
                1,
                1,
            ]
        )
        return new_id

