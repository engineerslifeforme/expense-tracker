""" Search page """

from decimal import Decimal

import streamlit as stl

from db_access import DbAccess

def display_search(st: stl, data_db: DbAccess):
    with st.beta_expander('Transaction Search'):
        check, field = st.beta_columns([1,5])
        use_id = check.checkbox('ID?')
        taction_id = field.number_input('ID', min_value=0, step=1)
        check, field = st.beta_columns([1,5])
        use_amount = check.checkbox('Amount?')
        amount = Decimal(str(field.number_input('Amount', min_value=0.0, step=0.01)))

        filtered = data_db.transactions
        show = False
        if taction_id != 0 and use_id:
            filtered = filtered[filtered['id'] == taction_id]
            show = True
        if amount != 0.0 and use_amount:
            filtered = filtered[filtered['amount'].abs() == amount]
            show = True
        if show:
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

        check, field = st.beta_columns([1,5])
        use_id = check.checkbox('Sub ID?')
        sub_id = field.number_input('Sub ID', min_value=0, step=1)
        check, field = st.beta_columns([1,5])
        use_amount = check.checkbox('Sub Amount?')
        amount = Decimal(str(field.number_input('Sub Amount', min_value=0.0, step=0.01)))
        check, field = st.beta_columns([1,5])
        use_taction_id = check.checkbox('Taction ID?')
        taction_id = field.number_input('Taction ID', min_value=0)
        check, field = st.beta_columns([1,5])
        use_category = check.checkbox('Category?')
        category_id = data_db.category_map_reverse[field.selectbox('Category', options=data_db.categories['name'])]
        
        filtered = data_db.subs
        show = False
        if sub_id != 0 and use_id:
            filtered = filtered[filtered['id'] == sub_id]
            show = True
        if amount != 0.0 and use_amount:
            filtered = filtered[filtered['amount'].abs() == amount]
            show = True
        if taction_id != 0.0 and use_taction_id:
            filtered = filtered[filtered['taction_id'].abs() == taction_id]
            show = True
        if use_category:
            filtered = filtered[filtered['category_id'] == category_id]
            show = True
        if show:
            st.write(filtered)
        else:
            st.markdown('Enter some data to search')
        st.write(filtered.sort_values(by='id', ascending=False).head(15))

    with st.beta_expander('Statement Search'):
        left, right = st.beta_columns(2)
        taction_filter = right.checkbox('Filter by taction')
        taction_id = left.number_input('taction to filter', value=0, min_value=0, step=1)
        left, right = st.beta_columns(2)
        id_filter = right.checkbox('Filter by ID')
        statement_id = left.number_input('statement ID', value=0, min_value=0, step=1)

        data_to_show = data_db.statement_transactions

        if taction_filter:
            data_to_show = data_to_show.loc[data_to_show['taction_id'] == taction_id]
        if id_filter:
            data_to_show = data_to_show.loc[data_to_show['id'] == statement_id]

        st.write(data_to_show)