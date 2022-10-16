""" DB Access object """

from pathlib import Path
from decimal import Decimal
import datetime

import sqlite3
import pandas as pd
import numpy as np

from budget_helper import get_monthly_budget_increment

ZERO = Decimal('0.00')

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
        include_deferred: bool = True,
        amount: Decimal = None,
        account_id: int = None,
        before_date: np.datetime64 = None,
        after_date: np.datetime64 = None,
        request_taction_id: int = None) -> pd.DataFrame:
        
        sql = 'SELECT * FROM statement_transactions'
        
        where_list = []
        if not include_assigned:
            where_list.append('taction_id IS NULL')
        if not include_deferred:
            where_list.append('deferred = 0')
        if amount is not None:
            where_list.append(f'amount = {amount}')
        if account_id is not None:
            where_list.append(f'account_id = {account_id}')
        if request_taction_id is not None:
            where_list.append(f'taction_id = {request_taction_id}')
        if after_date is not None:
            where_list.append(f"date >= date('{after_date}')")
        if before_date is not None:
            where_list.append(f"date <= date('{before_date}')")
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
        absolute_value: bool = False,
        only_valid: bool = True,
        description_text: str = None,
        taction_id_request: int = None,
        include_statement_links: bool = False):
        
        # amount is the total not the sub
        subs = self.get_subtotals(
            only_valid=only_valid,
        )
        tactions = self.get_tactions(
            after_date=after_date,
            before_date=before_date,
            account_id=account_id,
            only_valid=only_valid,
            id_request=taction_id_request,
            description_text=description_text,
        ).set_index('id')
        sub_totals = subs[['amount', 'taction_id']].groupby('taction_id').sum().reset_index(drop=False)
        if amount is not None:
            if absolute_value:
                sub_totals = sub_totals.loc[sub_totals['amount'].abs()==abs(amount), :]
            else:
                sub_totals = sub_totals.loc[sub_totals['amount']==amount, :]
        transactions = sub_totals.join(tactions, on='taction_id', how='inner', lsuffix='_sub')
        if include_statement_links:
            statements = self.get_statement_transactions(
                amount=amount,
                account_id=account_id,
                request_taction_id=taction_id_request,
            ).set_index('taction_id').rename({'id': 'statement_id'}, axis='columns')
            transactions = transactions.join(statements[['statement_id', 'date']], on='taction_id', how='left', rsuffix='_statement')
        return transactions

    def get_subtotals(self, 
        amount: Decimal = None,
        absolute_value: bool = False,
        category_id: int = None,
        taction_id: int = None,
        in_taction_list: list = None,
        before_date: np.datetime64 = None,
        after_date: np.datetime64 = None,
        only_valid: bool = True,
        only_real: bool = True):
        sql = 'SELECT * FROM sub'

        where_list = []
        if amount is not None:
            if absolute_value:
                where_list.append(f'amount = abs({abs(amount)})')
            else:
                where_list.append(f'amount = {amount}')
        if only_valid:
            where_list.append('valid = 1')
        if only_real:
            where_list.append('not_real = 0')
        if taction_id is not None:
            where_list.append(f'taction_id = {taction_id}')
        if category_id is not None:
            where_list.append(f'category_id = {category_id}')
        if in_taction_list is not None:
            str_list = [str(item) for item in in_taction_list]
            where_list.append(f"taction_id IN ({', '.join(str_list)})")
        if after_date is not None:
            where_list.append(f"date >= date('{after_date}')")
        if before_date is not None:
            where_list.append(f"date <= date('{before_date}')")
        sql += generate_where_statement(where_list)
        #print(sql)

        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'amount': str},
            parse_dates=['date'],
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

    def get_tactions(self, 
        after_date: np.datetime64 = None,
        before_date: np.datetime64 = None,
        only_valid: bool = True,
        account_id: int = None,
        description_text: str = None,
        id_request: int = None) -> pd.DataFrame:
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
        if id_request is not None:
            where_list.append(f'id = {id_request}')
        if description_text is not None:
            where_list.append(f"description LIKE '%{description_text}%'")
        sql += generate_where_statement(where_list)
        print(sql)

        data = pd.read_sql_query(
            sql,
            self.con,
            parse_dates=['date'],
        )
        return data

    def get_categories(self) -> pd.DataFrame:
        return pd.read_sql_query(
            'SELECT * FROM category',
            self.con
        )

    def get_budget_profiles(self, budget_id: int = None) -> pd.DataFrame:
        sql = 'SELECT * FROM budget_profile'
        where_list = []
        if budget_id is not None:
            where_list.append(f'budget_id = {budget_id}')
        sql += generate_where_statement(where_list)
        value_columns = {column_name: str for column_name in self.get_budget_profile_column_names() if 'month' in column_name}
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype=value_columns,
        )
        for column_name in value_columns:
            data[column_name] = data[column_name].apply(Decimal)
        return data

    def get_methods(self) -> pd.DataFrame:
        return pd.read_sql_query(
            'SELECT * from method',
            self.con
        )

    def get_accounts(self, account_id: int = None, only_valid: bool = True, only_visible: bool = True) -> pd.DataFrame:
        sql = 'SELECT * FROM account'
        where_list = []
        if only_valid:
            where_list.append('valid = 1')
        if only_visible:
            where_list.append('visibility = 1')
        if account_id is not None:
            where_list.append(f'id = {account_id}')
        sql += generate_where_statement(where_list)
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'balance': str},
        )
        data['balance'] = data['balance'].apply(Decimal)
        return data

    def get_budgets(self, budget_id: int = None, only_visible: bool = True) -> pd.DataFrame:
        sql = 'SELECT * FROM budget'
        where_list = []
        if budget_id is not None:
            where_list.append(f'id = {budget_id}')
        if only_visible:
            where_list.append('visibility = 1')
        sql += generate_where_statement(where_list)
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'increment': str, 'balance': str}
        )
        data['balance'] = data['balance'].apply(Decimal)
        data['increment'] = data['increment'].apply(Decimal)
        return data

    def get_hsa_distributions(self, amount: Decimal = None, source_id: str = None) -> pd.DataFrame:
        sql = 'SELECT * FROM hsa_distributions'
        where_list = []
        if amount is not None:
            where_list.append(f'amount = {amount}')
        if source_id is not None:
            where_list.append(f"source_id = '{source_id}'")
        sql += generate_where_statement(where_list)
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'amount': str},
            parse_dates=['date'],
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

    def get_budget_adjustments(self, budget_id: int = None) -> pd.DataFrame:
        sql = 'SELECT * FROM budget_adjustments'
        where_list = []
        if budget_id is not None:
            where_list.append(f'budget_id = {budget_id}')
        sql += generate_where_statement(where_list)
        data = pd.read_sql_query(
            sql,
            self.con,
            dtype={'amount': str},
            parse_dates=['date'],
        )
        data['amount'] = data['amount'].apply(Decimal)
        return data

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

    def _insert(self, table: str, fields: list, values: list):
        fields_str = ', '.join(fields)
        str_values = [str(value) for value in values]
        values_str = "\"" + "\", \"".join(str_values) + "\""
        self.cursor.execute(f"INSERT INTO {table} ({fields_str}) VALUES ({values_str})")
        self.con.commit()

    def update_account(self, amount: Decimal, account: str):
        self._update_add(
            'account',
            'balance',
            amount,
            self.account_translate(account, 'id')
        )

    def account_translate(self, account, request: str):
        return self.translate(account, 'account', request)

    def method_translate(self, method, request: str):
        return self.translate(method, 'method', request)

    def category_translate(self, method, request: str):
        return self.translate(method, 'category', request)

    def budget_translate(self, method, request: str):
        return self.translate(method, 'budget', request)

    def translate(self, match: str, name_type: str, request: str) -> int:
        type_map = {
            'account': self.get_accounts,
            'method': self.get_methods,
            'category': self.get_categories,
            'budget': self.get_budgets,
        }
        func = type_map[name_type]
        data = func()
        if request == 'id':
            result = data[data['name'] == match]['id']
        elif request == 'name':
            result = data[data['id'] == match]['name']
        return result.values[0]
    
    def _update_add(self, table_name: str, field_name: str, amount: Decimal, item_id: int):
        self.cursor.execute(f"UPDATE {table_name} SET {field_name}={field_name}+{amount} WHERE id={item_id}")
        self.con.commit()

    def add_transaction(self, date, account: str, method: str, description: str, receipt: bool, amount: Decimal, subs: list, transfer: bool = False):
        new_id = self.add_taction(
            date,
            transfer,
            self.account_translate(account, 'id'),
            self.method_translate(method, 'id'),
            description,
            receipt,
            True,
            False,
        )
        self.update_account(amount, account)
        for sub in subs:
            sub_amount = sub[0]
            category_id = self.category_translate(sub[1], 'id')
            self.add_sub(
                sub_amount,
                category_id,
                new_id,
                True,
                False,
                date,
            )
            self.update_budget(sub_amount, category_id)
        return new_id

    def add_transfer(self, date, withdrawal_account: str, deposit_account: str, description, receipt, amount: Decimal):
        withdraw_amount = Decimal('-1.00') * amount
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

    def get_next_sub_id(self):
        return self.get_subtotals(only_valid=False)['id'].max() + 1

    def add_sub(self, amount: Decimal, category_id: int, taction_id: int, valid: bool, not_real: bool, date):
        fields = [
            'id',
            'amount',
            'category_id',
            'taction_id',
            'valid',
            'not_real',
            'date',
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
            date,
        ])
        return new_id

    def get_next_taction_id(self):
        return self.get_tactions(only_valid=False)['id'].max() + 1

    def get_next_statement_transaction_id(self):
        return self.get_statement_transactions()['id'].max() + 1

    def update_budget(self, amount: Decimal, category_id: int):
        self._update_add(
            'budget',
            'balance',
            amount,
            self.get_budget_from_category(category_id),
        )

    def update_budget_by_budget(self, amount: Decimal, budget_id: int):
        self._update_add(
            'budget',
            'balance',
            amount,
            budget_id,
        )

    def get_budget_from_category(self, category_id: int) -> int:
        categories = self.get_categories()
        return categories[categories['id'] == category_id]['budget_id'].values[0]

    def defer_statement(self, statement_id: int):
        self._update('statement_transactions', 'deferred', 1, statement_id)

    def undefer_statement(self, statement_id: int):
        self._update('statement_transactions', 'deferred', 0, statement_id)

    def assign_statement_entry(self, entry_id: int, taction_id: int):
        self._update(
            'statement_transactions',
            'taction_id',
            taction_id,
            entry_id,
        )

    def _update(self, table_name: str, field_name: str, in_new_value, item_id: int, use_quotes: bool = False, id_field='id'):
        if use_quotes:
            new_value = f"'{in_new_value}'"
        else:
            new_value = in_new_value
        if in_new_value is None:
            self.cursor.execute(f"UPDATE {table_name} SET {field_name} = ? WHERE {id_field}={item_id}", (None,))
        else:
            self.cursor.execute(f"UPDATE {table_name} SET {field_name}={new_value} WHERE {id_field}={item_id}")
        self.con.commit()

    def add_statement_transaction(self, date, month:int, year:int, account_id:int, amount:Decimal, description:str = None):
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

    def delete_transaction(self, transaction_id: int):
        statements = self.get_statement_transactions(request_taction_id=transaction_id)
        for statement_id in list(statements['id']):
            self._update('statement_transactions', 'taction_id', None, statement_id)
            print(f'Reset statement {statement_id}')
        subs = self.get_subtotals(taction_id=transaction_id)
        amount = Decimal('0.00')
        for sub in subs.to_dict(orient='records'):
            if sub['valid'] != 1:
                raise ValueError('Sub was not valid')
            sub_amount = sub['amount']
            amount += sub_amount
            self.update_budget(Decimal('-1.00')*sub_amount, sub['category_id'])
            self._update(
                'sub', 'valid', 0, sub['id']
            )
            print(f"Invalidating sub {sub['id']}")
        account_id = self.get_tactions(id_request=transaction_id)['account_id'].values[0]
        taction_valid = self.get_tactions(id_request=transaction_id)['valid'].values[0]
        if taction_valid != 1:
            raise ValueError('taction was not valid')
        self.update_account(Decimal('-1.00')*amount, self.account_translate(account_id, 'name'))
        self._update(
            'taction', 'valid', 0, transaction_id
        )

    def add_budget(self, name: str, balance: Decimal, purpose: str, update_frequency: str, update_amount: Decimal) -> int:
        new_id = self.get_budgets()['id'].max() + 1
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
        new_id = self.get_categories()['id'].max() + 1
        budget_id = self.budget_translate(budget_name, 'id')
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

    def assign_hsa_receipt(self, receipt_path: str, distribution_id: int):
        self._update('hsa_distributions', 'receipt_path', receipt_path, distribution_id, use_quotes=True)
    
    def add_hsa_distribution(self, date, person: str, merchant: str, amount: Decimal, description: str, expense_taction_id: int, distribution_taction_id: int, receipt_path: str, source_id: str, hsa_debit: bool = False, dependent_care: bool = False):
        new_id = self.get_hsa_distributions()['id'].max() + 1
        if hsa_debit:
            hsa_debit_int = 1
        else:
            hsa_debit_int = 0
        if dependent_care:
            dependent_care_int = 1
        else:
            dependent_care_int = 0
        self._insert(
            'hsa_distributions',
            [
                'id',
                'date',
                'person',
                'Merchant',
                'amount',
                'description',
                'expense_taction_id',
                'distribution_taction_id',
                'receipt_path',
                'hsa_debit',
                'dependent_care',
                'source_id',
            ],
            [
                new_id,
                date,
                person,
                merchant,
                amount,
                description,
                expense_taction_id,
                distribution_taction_id,
                receipt_path,
                hsa_debit_int,
                dependent_care_int,
                source_id
            ]
        )
        return new_id

    def get_budget_profile_column_names(self):
        return ['budget_id'] + [f'month_{i}' for i in range(1,13)]
    
    def add_budget_profile(self, budget_id: int, values: list):        
        column_names = self.get_budget_profile_column_names()
        self._insert(
            'budget_profile',
            column_names,
            [budget_id] + values,
        )

    def get_hsa_paths(self) -> dict:
        sql = 'SELECT * FROM hsa_receipt_paths'
        return pd.read_sql_query(sql, self.con).set_index('name').to_dict()['path']

    def get_budget_update_date(self) -> datetime.date:
        sql = "SELECT * FROM important_dates WHERE name=\"last_budget_update\""
        return datetime.datetime.utcfromtimestamp(int(pd.read_sql_query(sql, self.con, parse_dates=['date'])['date'].values[0])/1e9).date()

    def update_budget_update_date(self, new_date: datetime.date):
        self._update('important_dates', 'date', new_date, "\"last_budget_update\"", use_quotes=True, id_field='name')

    def add_budget_adjustment(self, amount: Decimal, budget_id: int, transfer: bool = False, periodic_update: bool = True) -> int:
        ids = self.get_budget_adjustments()['id'].astype(int)
        if len(ids) < 1:
            new_id = 0
        else:
            new_id = ids.max() + 1
        if transfer:
            transfer_int = 1
        else:
            transfer_int = 0
        if periodic_update:
            periodic_update_int = 1
        else:
            periodic_update_int = 0
        date = datetime.datetime.today().date()
        self._insert(
            'budget_adjustments',
            [
                'id',
                'date',
                'amount',
                'budget_id',
                'transfer',
                'periodic_update',
            ],
            [
                new_id,
                date,
                amount,
                budget_id,
                transfer_int,
                periodic_update_int,
            ]
        )
        return new_id

    def adjust_budget(self, increment: Decimal, budget_id: int):
        new_id = self.add_budget_adjustment(increment, budget_id)
        self.update_budget_by_budget(increment, budget_id)
        return new_id

    def update_budgets(self):
        budget_dicts = self.get_budgets().to_dict(orient='records')
        for budget_info in budget_dicts:
            increment = budget_info['increment']
            if increment != ZERO and budget_info['valid'] == 1:
                budget_id = budget_info['id']
                increment = get_monthly_budget_increment(budget_info)
                self.adjust_budget(increment, budget_id)

    def set_budget_increment(self, increment: Decimal, budget_id: int):
        self._update('budget', 'increment', increment, budget_id)


