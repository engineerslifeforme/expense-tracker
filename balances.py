""" Balance Page """

import streamlit as st

from newdb_access import DbAccess
import view_translation as vt

def view_balances(db: DbAccess):
    st.markdown('## Balances')

    st.markdown('### Accounts')
    st.write(vt.translate_accounts(db.get_accounts()))

    account_data = db.get_accounts()
    account_names = ['None'] + list(account_data['name'])
    account_name = st.selectbox('Account', options=account_names)

    if account_name == 'None':
        st.markdown('Select account name for detailed log')
        st.stop()
    
    account_id = db.account_translate(account_name, 'id')
    transactions = db.get_transactions(
        account_id=account_id,
    ).sort_values(by='date', ascending=False)
    transactions['balance'] = transactions['amount'].cumsum()
    account_balance = account_data.loc[account_data['id'] == account_id, 'balance'].values[0]
    transactions['balance'] = account_balance - transactions['balance']
    transactions['balance'] = transactions['balance'].shift(periods=1).fillna(account_balance)
    st.write(vt.translate_transactions(transactions))