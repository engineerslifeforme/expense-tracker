""" Search page """

from decimal import Decimal

import streamlit as stl
import datetime as dt
from dateutil.relativedelta import relativedelta
import pandas as pd

from db_access import DbAccess

def display_search(st: stl, data_db: DbAccess):
    taction_id = st.number_input('Taction ID', min_value=0, step=1)
    sub_id = st.number_input('Sub ID', min_value=0, step=1)
    amount = Decimal(str(st.number_input('Amount', min_value=0.0, step=0.01)))
    selected_accounts = st.multiselect('Account Filter:', data_db.accounts['name'])
    apply_date_filter = st.checkbox('Apply Date Filter?')
    category_names = st.multiselect('Category', data_db.categories['name'])
    category_ids = [data_db.category_map_reverse[name] for name in category_names]
    statement_id = st.number_input('statement ID', value=0, min_value=0, step=1)
    if apply_date_filter:
        start_date = dt.date(year=2010,month=1,day=1)  #  I need some range in the past
        end_date = dt.datetime.now().date()
        start_date, end_date = st.slider('Select date', min_value=start_date, value=[start_date, end_date], max_value=end_date)
        st.markdown(f'Filtered from {start_date} to {end_date}')
    
    with st.beta_expander('Transaction Search'):
        filtered = data_db.transactions
        show = False        
        
        if taction_id != 0:
            filtered = filtered[filtered['id'] == taction_id]
            show = True        
        
        if amount != 0.0:
            filtered = filtered[filtered['amount'].abs() == amount]
            show = True
        
        if len(selected_accounts) > 0:
            show = True
            filtered = filtered.loc[filtered['account'].isin(selected_accounts)]

        if apply_date_filter:
            show = True
            filtered = filtered.loc[
                (filtered['date'] >= pd.to_datetime(start_date)) &
                (filtered['date'] <= pd.to_datetime(end_date)),
                :
            ]
        
        if show:
            st.markdown(f'{len(filtered)} Filtered Transactions')
            st.write(filtered[[
                'id',
                'amount',
                'date',
                'description',
                'valid',
                'account',
                'method',
            ]])
        else:
            st.markdown('Enter some data to search')
    
    with st.beta_expander('Sub Search'):
        filtered = data_db.subs
        show = False
        if sub_id != 0:
            filtered = filtered[filtered['id'] == sub_id]
            show = True
        if amount != 0.0:
            filtered = filtered[filtered['amount'].abs() == amount]
            show = True
        if taction_id != 0.0:
            filtered = filtered[filtered['taction_id'].abs() == taction_id]
            show = True
        if len(category_ids) > 0:
            filtered = filtered[filtered['category_id'].isin(category_ids)]
            show = True
        if show:
            st.write(filtered)
        else:
            st.markdown('Enter some data to search')
        st.write(filtered.sort_values(by='id', ascending=False).head(15))

    with st.beta_expander('Statement Search'):
        data_to_show = data_db.statement_transactions

        if taction_id != 0 and not st.checkbox('Disable Taction Filter'):
            data_to_show = data_to_show.loc[data_to_show['taction_id'] == taction_id]        
        
        if statement_id != 0:
            data_to_show = data_to_show.loc[data_to_show['id'] == statement_id]

        if amount != 0.00:
            data_to_show = data_to_show.loc[data_to_show['amount'].abs() == amount]
        st.markdown(f'{len(data_to_show)} Statement Matches')
        st.write(data_to_show)