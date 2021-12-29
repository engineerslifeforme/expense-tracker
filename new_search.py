""" Search """

from decimal import Decimal

import streamlit as stl

from newdb_access import DbAccess
import view_translation as vt

def view_search(st: stl, db: DbAccess):
    st.markdown('## Search')
    amount = Decimal(str(st.number_input(
        'Amount',
        step=0.01
    )))
    if amount == Decimal('0.00'):
        amount = None
    categories = st.multiselect(
        'Categories',
        options=db.get_categories()['name']
    )
    taction_id = st.number_input('Taction ID', step=1)
    if taction_id == 0:
        taction_id = None

    if st.checkbox('Transactions'):
        transactions = db.get_transactions(amount=amount)
        st.markdown(str(len(transactions)))

        if len(categories) > 0:
            first_category_id = db.category_translate(categories[0], 'id')
            subs = db.get_subtotals(category_id=first_category_id)
            transactions = transactions.loc[transactions['taction_id'].isin(subs['taction_id']), :]
        st.write(vt.translate_transactions(transactions, db=db))

        #view_data = vt.translate_transactions(transactions)
    if st.checkbox('Statements'):
        statements = db.get_statement_transactions(amount=amount, request_taction_id=taction_id)
        st.write(vt.translate_statement_transactions(statements))
        


