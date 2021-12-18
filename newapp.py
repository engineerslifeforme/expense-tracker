import streamlit as st

from newdb_access import DbAccess
import view_translation as vt
import pandas as pd

FOURTEEN_DAYS = pd.Timedelta(days=14)

db = DbAccess('example.db')

st.set_page_config(layout="wide")

"""# Expense Tracker"""
"""## Statement Assignment"""
include_deferred = st.checkbox('Include Deferred Entries')

statement_transactions = db.get_statement_transactions(
    include_assigned=False, 
    include_deferred=False
)
st.markdown(f'{len(statement_transactions)} Entries')
st.write(vt.translate_statement_transactions(statement_transactions))

st.write(statement_transactions['date'].values[0])
st.write(type(statement_transactions['date'].values[0]))

"""### Assignment Methods"""
if st.button('Attempt Auto-Assign'):
    st.markdown('Auto-Assigning...')
    for entry in statement_transactions.to_dict(orient='records'):
        min_date = entry['date'] - FOURTEEN_DAYS
        max_date = entry['date'] + FOURTEEN_DAYS
        # potential_matches = data_db.transactions.loc[
        #     (data_db.transactions['date'] > min_date) &
        #     (data_db.transactions['date'] < max_date) &
        #     (data_db.transactions['amount'] == entry['amount']) &
        #     (data_db.transactions['valid'] == 1) &
        #     (data_db.transactions['account_id'] == entry['account_id']) &
        #     (~data_db.transactions['id'].isin(data_db.statement_transactions['taction_id']))
        # ]
        # match_quantity = len(potential_matches)
        # entry_description = entry['description']
        # entry_id = entry['id']
        # st.write(f"{entry_id}")