""" Statement assignment page """

from decimal import Decimal

import streamlit as stl
import pandas as pd

from newdb_access import DbAccess
import view_translation as vt
from batch_assignment import batch_assignment
from auto_assign import auto_assign

FOURTEEN_DAYS = pd.Timedelta(days=14)

def show_assignment_page(st: stl, db: DbAccess):
    st.markdown('## Statement Assignment')
    left, right = st.columns(2)
    include_deferred = right.checkbox('Include Deferred Entries')
    account_list = ['None'] + list(db.get_accounts()['name'])
    account_name = left.selectbox('Account Filter', options=account_list)
    if account_name != 'None':
        account_id = db.account_translate(account_name, 'id')
    else:
        account_id = None

    statement_transactions = db.get_statement_transactions(
        include_assigned=False, 
        include_deferred=include_deferred,
        account_id=account_id,
    )
    st.markdown(f'{len(statement_transactions)} Entries')
    st.write(vt.translate_statement_transactions(statement_transactions.copy(deep=True)))

    entries = statement_transactions.to_dict(orient='records')

    st.markdown('### Assignment Methods')
    st.markdown('#### Auto-Assign')
    if st.checkbox('Attempt Auto-Assign'):
        auto_assign(st, db, entries)
    
    st.markdown('#### Batch Assignment')
    methods = db.get_methods()
    default_method = st.selectbox('Default Method', options=methods['name'])
    if st.checkbox('Assign Statements'):
        batch_assignment(st, db, default_method, entries)