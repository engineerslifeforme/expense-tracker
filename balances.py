""" Balance Page """

import streamlit as st

from newdb_access import DbAccess
import view_translation as vt

def view_balances(db: DbAccess):
    st.markdown('## Balances')

    st.markdown('### Accounts')
    st.write(vt.translate_accounts(db.get_accounts()))