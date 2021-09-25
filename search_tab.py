""" Search page """

import streamlit as stl

from db_access import DbAccess

def display_search(st: stl, data_db: DbAccess):
    check, field = st.beta_columns([1,5])
    use_id = check.checkbox('ID?')
    taction_id = field.number_input('ID', min_value=0, step=1)
    check, field = st.beta_columns([1,5])
    use_amount = check.checkbox('Amount?')
    amount = field.number_input('Amount', min_value=0.0)

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
        ]])
    else:
        st.markdown('Enter some data to search')
    
    st.markdown('## Sub Search')

    check, field = st.beta_columns([1,5])
    use_id = check.checkbox('Sub ID?')
    sub_id = field.number_input('Sub ID', min_value=0, step=1)
    check, field = st.beta_columns([1,5])
    use_amount = check.checkbox('Sub Amount?')
    amount = field.number_input('Sub Amount', min_value=0.0)
    check, field = st.beta_columns([1,5])
    use_taction_id = check.checkbox('Taction ID?')
    taction_id = field.number_input('Taction ID', min_value=0)

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
    if show:
        st.write(filtered)
    else:
        st.markdown('Enter some data to search')