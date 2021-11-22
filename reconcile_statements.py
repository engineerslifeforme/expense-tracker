""" Reconcile database against statements """

from decimal import Decimal

import streamlit as stl
import pandas as pd

from db_access import DbAccess
from ml_statement import predict_category, train_model

FOURTEEN_DAYS = pd.Timedelta(days=14)

def attempt_statement_assignment(st, data_db, taction_id, entry_id, entry_description, description):
    if taction_id in data_db.statement_transactions['taction_id'].values:
        st.markdown(f'Only match already assigned, statement: {entry_id}, taction: {taction_id}')
    else:
        st.markdown(f'Assigning statement {entry_id} to taction {taction_id}')
        st.markdown(f"Statement description: {entry_description} transaction: {description}")
        data_db.assign_statement_entry(entry_id, taction_id)

def display_reconcile_statements(st: stl, data_db: DbAccess):
    st.markdown('Unassigned statement transactions')
    unassigned_statement_entries = data_db.statement_transactions.loc[
        data_db.statement_transactions['taction_id'].isnull(), :
    ]
    if not st.checkbox('Include Deferred?'):
        unassigned_statement_entries = unassigned_statement_entries.loc[unassigned_statement_entries['deferred'] != 1, :]    
    st.write(f'{len(unassigned_statement_entries)} unassigned statement entries!')
    st.write(unassigned_statement_entries.reset_index())

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
                attempt_statement_assignment(st, data_db, taction_id, entry_id, entry_description, potential_matches['description'].values[0])
            elif match_quantity > 1:
                precise_date_matches = potential_matches[potential_matches['date'] == entry['date']]
                if len(precise_date_matches) == 1:
                    taction_id = precise_date_matches['id'].values[0]
                    attempt_statement_assignment(st, data_db, taction_id, entry_id, entry_description, precise_date_matches['description'].values[0])
                else:
                    st.markdown(f'Multiple matches for {entry_id} | {entry_description}')
                    st.write(potential_matches)

    with st.beta_expander('Manual Addition'):
        left, right = st.beta_columns(2)
        entry_id = left.number_input('Statement Entry ID', min_value=0, step=1)
        taction_id = right.number_input('Taction ID', min_value=0, step=1)
        if entry_id != 0:
            st.write(data_db.statement_transactions[data_db.statement_transactions['id'] == entry_id])
        if taction_id != 0:
            st.write(data_db.transactions[data_db.transactions['id'] == taction_id])
            if taction_id in data_db.statement_transactions['taction_id']:
                st.write('Already mapped!')
        if st.button('Add Assignment'):
            data_db.assign_statement_entry(entry_id, taction_id)
            st.markdown(f'Assigned statement {entry_id} to taction {taction_id}')
            
    with st.beta_expander('Add Non-Matching Statement Entries'):
        entry_list = unassigned_statement_entries.to_dict(orient='records')
        if len(entry_list) > 0:
            try:
                max_entry_index = len(entry_list) - 1
                chosen_entry_index = st.number_input('Unassigned Entry Index', value=max_entry_index, max_value=max_entry_index, min_value=0, step=1)
                chosen_entry = entry_list[chosen_entry_index]
                st.write('#### Auto Populated Data')
                left, middle, right = st.beta_columns(3)
                date = left.date_input('Date', value=chosen_entry['date'])
                amount = Decimal(str(middle.number_input('Amount', value=float(chosen_entry['amount']), step=0.01)))
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
                potential_time_matches =  potential_time_matches.join(data_db.statement_transactions[['id', 'taction_id']].set_index('taction_id'), on='id', rsuffix='_statement')
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
                
                statement_id = chosen_entry['id']
                if st.button('Add Transaction!'):                    
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
                    data_db.assign_statement_entry(statement_id, taction_id)
                    if chosen_entry['deferred'] == 1:
                        self.undefer_statement(statement_id)
                    st.markdown('Added transaction')
                if st.button('Defer Transaction'):
                    data_db.defer_statement(statement_id)
            except ValueError:
                st.write('Failed to Load entry')
        else:
            st.markdown('No entries to be evaluated')

        if st.button('Re-Train Suggestions'):
            train_model(data_db)