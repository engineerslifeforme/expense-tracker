""" Balance Page """

from decimal import Decimal

import streamlit as st
import pandas as pd

from newdb_access import DbAccess
import view_translation as vt

def show_detailed_account(db: DbAccess, account_name: str, account_data: pd.DataFrame):
    reverse_balance = Decimal(str(st.number_input('Reverse Balance Start', step=0.01)))
    
    account_id = db.account_translate(account_name, 'id')
    transactions = db.get_transactions(
        account_id=account_id,
    )
    transactions = transactions.sort_values(by='date')
    transactions['rbalance'] = transactions['amount'].cumsum()
    transactions['rbalance'] = transactions['rbalance'] + reverse_balance
    transactions = transactions.sort_values(by='date', ascending=False)
    transactions['balance'] = transactions['amount'].cumsum()
    account_balance = account_data.loc[account_data['id'] == account_id, 'balance'].values[0]
    transactions['balance'] = account_balance - transactions['balance']
    transactions['balance'] = transactions['balance'].shift(periods=1).fillna(account_balance)
    st.write(vt.translate_transactions(transactions))

def view_balances(db: DbAccess):
    st.markdown('## Balances')

    st.markdown('### Accounts')
    st.write(vt.translate_accounts(db.get_accounts()))

    account_data = db.get_accounts()
    account_names = ['None'] + list(account_data['name'])
    account_name = st.selectbox('Account', options=account_names)

    if account_name == 'None':
        st.markdown('Select account name for detailed log')
    else:
        show_detailed_account(db, account_name, account_data)

    st.markdown('### Budgets')
    st.markdown(f'Last Update: {db.get_budget_update_date()}')
    st.write(vt.translate_budgets(db.get_budgets()))

    