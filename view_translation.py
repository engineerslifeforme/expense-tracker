""" Translate dataframes for better viewing """

import pandas as pd

def translate_statement_transactions(data: pd.DataFrame) -> pd.DataFrame:
    data = data.drop(['statement_month', 'statement_year'], axis='columns')
    data['amount'] = data['amount'].astype(float)
    data = data.sort_values('date', ascending=False)
    data = data.style\
        .format(precision=0, subset=['taction_id'])\
        .format(precision=2, subset=['amount'])\
        .hide_index()
    return data

def translate_transactions(data: pd.DataFrame) -> pd.DataFrame:
    data['not_real'] = data['not_real'].astype(int)
    data['amount'] = data['amount'].astype(float)
    data = data.sort_values('date', ascending=False)
    data = data.style\
        .format(precision=2, subset=['amount'])\
        .hide_index()
    return data