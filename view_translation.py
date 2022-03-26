""" Translate dataframes for better viewing """

import pandas as pd

from newdb_access import DbAccess

def translate_statement_transactions(data: pd.DataFrame, sort_column: str = 'date') -> pd.DataFrame:
    data = data.drop(['statement_month', 'statement_year'], axis='columns')
    data['amount'] = data['amount'].astype(float)
    data = data.sort_values(sort_column, ascending=False)
    data = data.style\
        .format(precision=0, subset=['taction_id'])\
        .format(precision=2, subset=['amount'])\
        .hide_index()
    return data

def translate_transactions(data: pd.DataFrame, db: DbAccess = None) -> pd.DataFrame:
    data['not_real'] = data['not_real'].fillna(0).astype(int)
    data['amount'] = data['amount'].astype(float)
    if 'balance' in data.columns:
        data['balance'] = data['balance'].astype(float)
    if db is not None:
        data['account_id'] = data['account_id'].apply(db.account_translate, args=('name',))
        data['method_id'] = data['method_id'].apply(db.method_translate, args=('name',))
        subs = db.get_subtotals()
        filtered_subs = subs.loc[subs['taction_id'].isin(data['taction_id']), :]
        filtered_subs['category'] = filtered_subs['category_id'].apply(db.category_translate, args=('name',))
        grouped = filtered_subs[['taction_id', 'category']].groupby('taction_id')['category'].apply(','.join)
        data = data.join(grouped, on='taction_id', how='left')
    data = data.sort_values('date', ascending=False)
    styled_data = data.style\
        .format(precision=2, subset=['amount'])\
        .hide_index()
    return styled_data

def translate_accounts(data: pd.DataFrame) -> pd.DataFrame:
    data['balance'] = data['balance'].astype(float)
    return data

def translate_hsa(data: pd.DataFrame) -> pd.DataFrame:
    data['amount'] = data['amount'].astype(float)
    return data