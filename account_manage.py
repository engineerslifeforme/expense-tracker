""" Account Management """

from decimal import Decimal

import streamlit as stl
from db_access import DbAccess

def display_account_management(st: stl, db_data: DbAccess):
    st.markdown('### Current Accounts')
    st.write(db_data.accounts)
    st.markdown('### Add Account')
    left, middle, right = st.beta_columns(3)
    new_name = left.text_input(
        'New Account Name'
    )
    balance = Decimal(str(middle.number_input(
        'Current Balance',
        step=0.01,
    )))
    purpose = right.selectbox(
        'Account Type',
        options = ['Spending', 'Savings']
    )
    if st.button('Add New Account!'):
        st.write(f'New Account `{new_name}` added of type `{purpose}` with starting balance of `{balance}`')
