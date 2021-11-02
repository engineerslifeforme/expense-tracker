""" Reconcile database against statements """

import streamlit as stl
import pandas as pd

from db_access import DbAccess
from ml_statement import predict_category, train_model

FOURTEEN_DAYS = pd.Timedelta(days=14)

def display_reconcile_statements(st: stl, data_db: DbAccess):
    st.markdown('Unassigned statement transactions')
    unassigned_statement_entries = data_db.statement_transactions.loc[
        data_db.statement_transactions['taction_id'].isnull(), :
    ]
    st.write(f'{len(unassigned_statement_entries)} unassigned statement entries!')
    st.write(unassigned_statement_entries)

    if st.button('Attempt Auto-Assign'):
        st.markdown('Auto-assigning...')
        for entry in unassigned_statement_entries.to_dict(orient='records'):            
            min_date = entry['date'] - FOURTEEN_DAYS
            max_date = entry['date'] + FOURTEEN_DAYS
            potential_matches = data_db.transactions.loc[
                (data_db.transactions['date'] > min_date) &
                (data_db.transactions['date'] < max_date) &
                (data_db.transactions['amount'] == entry['amount']) &
                (data_db.transactions['valid'] == 1) &
                (data_db.transactions['account_id'] == entry['account_id']) &
                (~data_db.transactions['id'].isin(data_db.statement_transactions['taction_id']))
            ]
            match_quantity = len(potential_matches)
            entry_description = entry['description']
            entry_id = entry['id']
            if match_quantity == 1:                
                taction_id = potential_matches['id'].values[0]
                if taction_id in data_db.statement_transactions['taction_id'].values:
                    st.markdown(f'Only match already assigned, statement: {entry_id}, taction: {taction_id}')
                else:
                    st.markdown(f'Assigning statement {entry_id} to taction {taction_id}')
                    st.markdown(f"Statement description: {entry_description} transaction: {potential_matches['description'].values[0]}")
                    data_db.assign_statement_entry(entry_id, taction_id)
            elif match_quantity > 1:
                st.markdown(f'Multiple matches for {entry_id} | {entry_description}')
                st.write(potential_matches)

    with st.beta_expander('Add Non-Matching Statement Entries'):
        unassigned_statement_entries = data_db.statement_transactions.loc[
            data_db.statement_transactions['taction_id'].isnull(), :
        ]
        entry_list = unassigned_statement_entries.to_dict(orient='records')
        if len(entry_list) > 0:
            try:
                chosen_entry_index = st.number_input('Unassigned Entry Index', max_value=(len(entry_list) - 1), min_value=0, step=1)
                chosen_entry = entry_list[chosen_entry_index]
                st.write('#### Auto Populated Data')
                left, middle, right = st.beta_columns(3)
                date = left.date_input('Date', value=chosen_entry['date'])
                amount = middle.number_input('Amount', value=chosen_entry['amount'], step=0.01)
                account_name = right.selectbox(
                    'Account',
                    data_db.accounts['name'],
                    index=list(data_db.accounts['id']).index(chosen_entry['account_id'])
                )
                description = st.text_input('Description', value=chosen_entry['description'])
                st.markdown('### Close Transactions')
                min_date = pd.to_datetime(date) - FOURTEEN_DAYS
                max_date = pd.to_datetime(date) + FOURTEEN_DAYS
                potential_time_matches = data_db.transactions.loc[
                    (data_db.transactions['date'] > min_date) &
                    (data_db.transactions['date'] < max_date) &
                    (data_db.transactions['amount'] == amount) &
                    (data_db.transactions['valid'] == 1)
                ]
                st.write(potential_time_matches)
                st.markdown('### Similar Transactions')
                matching_subs = data_db.transactions[data_db.transactions['amount'] == amount]
                if len(matching_subs) > 0:
                    st.write(matching_subs[[
                        'amount', 
                        'date', 
                        'method',
                        'account',
                        'description',
                        'valid',
                    ]])
                else:
                    st.markdown(f'No prevoius transactions of ${amount} found!')
                st.markdown('#### Manual Data')
                left, right = st.beta_columns(2)
                category_options = data_db.categories['name']
                category = left.selectbox(
                    f'Category',
                    category_options,
                    index=list(category_options).index(data_db.category_map[predict_category(chosen_entry)])
                )
                method = right.selectbox(
                    'Method',
                    list(data_db.methods['name']),
                )
                
                if st.button('Add Transaction!'):
                    st.markdown('Added transaction')
                    subs = [(amount, category)]
                    taction_id = data_db.add_transaction(
                        date,
                        account_name,
                        method,
                        description,
                        False,
                        amount,
                        subs,
                    )
                    data_db.assign_statement_entry(chosen_entry['id'], taction_id)
            except ValueError:
                st.write('Failed to Load entry')
        else:
            st.markdown('No entries to be evaluated')

        if st.button('Re-Train Suggestions'):
            train_model(data_db)

    with st.beta_expander('Check if all transactions have a statement match'):
        st.write('TBD')
