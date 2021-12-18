""" Translate dataframes for better viewing """

import pandas as pd

def translate_statement_transactions(data: pd.DataFrame) -> pd.DataFrame:
    data = data.drop(['statement_month', 'statement_year'], axis='columns')
    data['amount'] = data['amount'].astype(float)
    data = data.style\
        .format(precision=0, subset=['taction_id'])\
        .format(precision=2, subset=['amount'])\
        .hide_index()
    return data