""" Batch assignment """

from decimal import Decimal

import streamlit as stl
import pandas as pd

from newdb_access import DbAccess
from ml_statement import predict_category
import view_translation as vt

def batch_assignment(
    st: stl, 
    db: DbAccess,
    default_method: str, 
    entries: list):

    categories = db.get_categories()
    accounts = db.get_accounts()
    methods = db.get_methods()

    batch_type = st.radio('Batch Type', options=['group', 'single'])

    if batch_type == 'single':
        single_index = st.number_input('Single Index', step=1)
        batch_quantity = 1
    elif batch_type == 'group':
        batch_quantity = st.number_input('Batch Quantity', value=25, step=1)
    else:
        st.error(f'Unknown batch type: {batch_type}')
        st.stop()
    with st.form('Assignments'):
        i = 0
        add_list = []
        defer_list = []
        assign_list = []

        while i < min([batch_quantity, len(entries)]):
            if batch_type == 'group':
                entry = entries[i]
            elif batch_type == 'single':
                entry = entries[single_index]
            entry_id = entry['id']

            st.markdown(f'### Entry #{i}')
            left, right = st.columns(2)
            date = left.date_input(f'Date #{i}', value=entry['date'])
            amount = Decimal(str(right.number_input(f'Amount #{i}', value=float(entry['amount']), step=0.01)))
            left, middle, right = st.columns(3)
            category = left.selectbox(
                f'Category #{i}', 
                options=categories['name'],
                index=list(categories['name']).index(db.category_translate(
                    predict_category(entry),
                    'name',
                ))
            )
            method = middle.selectbox(
                f'Method #{i}', 
                options=methods['name'],
                index=list(methods['name']).index(default_method),
            )
            account = right.selectbox(
                f'Account #{i}', 
                options=accounts['name'],
                index=list(accounts['name']).index(
                    db.account_translate(entry['account_id'], 'name')
                )
            )
            description = st.text_input(f'Description #{i}', value=entry['description'])
            action = st.radio(f'Action #{i}', options=['Add', 'Defer', 'Assign', 'Nothing'])

            amount_matches = db.get_transactions(
                amount=entry['amount'],
                account_id=entry['account_id'],
            )

            taction_id = st.selectbox(
                f'Transaction ID #{i}',
                options=amount_matches['taction_id'],
            )
            if action == 'Add':
                add_list.append({
                    'date': date,
                    'account': account,
                    'method': method,
                    'description': description,
                    'amount': amount,
                    'subs': [(amount, category)],
                    'entry_id': entry_id,
                    'deferred': entry['deferred'],
                })
            elif action == 'Defer':
                defer_list.append(entry_id)    
            elif action == 'Assign':
                assign_list.append((entry_id, taction_id))    
            else:
                st.markdown(f'Unknown action: {action}')
                
            st.markdown('#### Amount Matches')
            st.write(vt.translate_transactions(amount_matches.copy(deep=True)))
            i += 1
        if st.form_submit_button('Process'):
            for item in defer_list:
                st.markdown(f'Deferring {item}')
                db.defer_statement(item)
            for statement_id, taction_id in assign_list:
                st.markdown(f'Assigning statement {statement_id} to taction {taction_id}')
                db.assign_statement_entry(statement_id, taction_id)
            for data in add_list:
                st.markdown(f"Creating new transaction for statement {data['entry_id']}")
                taction_id = db.add_transaction(
                    data['date'],
                    data['account'],
                    data['method'],
                    data['description'],
                    False,
                    data['amount'],
                    data['subs'],
                )
                db.assign_statement_entry(data['entry_id'], taction_id)
                if data['deferred'] == 1:
                    db.undefer_statement(data['entry_id'])