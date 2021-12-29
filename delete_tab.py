""" Delete tab """

import streamlit as stl
from db_access import DbAccess

def display_delete(st: stl, data_db: DbAccess):
    transaction_id = st.number_input(
        'Transaction ID to delete',
        min_value=0,
        step=1,
    )
    if transaction_id != 0:
        matches = data_db.get_tactions(id_request=transaction_id)
        if len(matches) == 0:
            st.write('Invalid transaction ID!')
        else:
            st.write(matches)
    else:
        st.write('Please enter a transaction ID!')
    delete = st.button('Delete!')
    if delete:
        try:
            data_db.delete_transaction(transaction_id)
            st.success(f'Deleted {transaction_id}')
        except ValueError:
            st.error('Item failed to delete')
