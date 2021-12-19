from decimal import Decimal

import streamlit as st
import pandas as pd

from newdb_access import DbAccess
import view_translation as vt
from ml_statement import predict_category

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

categories = db.get_categories()
methods = db.get_methods()
accounts = db.get_accounts()

"""### Assignment Methods"""
#if st.button('Attempt Auto-Assign'):
    #st.markdown('Auto-Assigning...')

default_method = st.selectbox('Default Method', options=methods['name'])

entries = statement_transactions.to_dict(orient='records')
index = st.number_input('Entry Index', step=1)
entry = entries[index]

if st.checkbox('Add Dialog'):
    left, right = st.columns(2)
    date = left.date_input('Date', value=entry['date'])
    amount = Decimal(str(right.number_input('Amount', value=float(entry['amount']), step=0.01)))
    left, middle, right = st.columns(3)
    category = left.selectbox(
        'Category', 
        options=categories['name'],
        index=list(categories['name']).index(db.category_translate(
            predict_category(entry),
            'name',
        ))
    )
    method = middle.selectbox(
        'Method', 
        options=methods['name'],
        index=list(methods['name']).index(default_method),
    )
    account = right.selectbox(
        'Account', 
        options=accounts['name'],
        index=list(accounts['name']).index(
            db.account_translate(entry['account_id'], 'name')
        )
    )
    description = st.text_input('Description', value=entry['description'])
    action = st.radio('Action', options=['Add', 'Defer', 'Nothing'])
    if action == 'Add':
        if st.button('Add'):
            st.markdown('Adding...')
            taction_id = db.add_transaction(
                date,
                account,
                method,
                description,
                False,
                amount,
                [(amount, category)],
            )
            db.assign_statement_entry(entry['id'], taction_id)
            if entry['deferred'] == 1:
                db.undefer_statement(entry['id'])
    elif action == 'Defer':
        if st.button('Defer'):
            st.markdown('Deferring...')
            db.defer_statement(entry['id'])
    
min_date = entry['date'] - FOURTEEN_DAYS
max_date = entry['date'] + FOURTEEN_DAYS
potential_matches = db.get_transactions(
    after_date=min_date,
    before_date=max_date,
    amount=entry['amount'],
    account_id=entry['account_id'],            
)
""" Close Matches """
st.write(potential_matches)
""" Amount matches """
st.write(vt.translate_transactions(db.get_transactions(amount=entry['amount'])))
    # potential_matches = potential_matches.loc[
    #     ~potential_matches['taction_id'].isin(db.get_statement_transactions()['taction_id'])
    # ]
    # potential_matches = data_db.transactions.loc[
    #     (data_db.transactions['date'] > min_date) &
    #     (data_db.transactions['date'] < max_date) &
    #     (data_db.transactions['amount'] == entry['amount']) &
    #     (data_db.transactions['valid'] == 1) &
    #     (data_db.transactions['account_id'] == entry['account_id']) &
    #     (~data_db.transactions['id'].isin(data_db.statement_transactions['taction_id']))
    # ]
    #match_quantity = len(potential_matches)
    
    # entry_description = entry['description']
    #entry_id = entry['id']
    #st.write(f"{entry_id}")
    #st.markdown(f'{match_quantity}')