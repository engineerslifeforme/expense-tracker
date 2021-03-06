""" Verifying purchases in period """

from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta

import streamlit as st

from newdb_access import DbAccess
import view_translation as vt

ZERO = Decimal('0.00')

def view_period_verification(db: DbAccess):
    st.markdown('## Period Verification')
    left, right = st.columns(2)
    start_date = datetime.datetime.combine(left.date_input('Start Date'), datetime.datetime.min.time())
    end_date = datetime.datetime.combine(right.date_input(
        'End Date',
        value = start_date+ relativedelta(months=+1) - datetime.timedelta(days=1)
    ), datetime.datetime.min.time())
    account_names = ['None'] + list(db.get_accounts()['name'])
    account_name = st.selectbox('Account', options=account_names)
    ids_to_remove = []
    if st.checkbox('Remove Charges'):
        number_of_remove = st.number_input('Number of Removes?', step=1, value=1)
        for x in range(number_of_remove):
            selected_id = st.number_input(f'Statement ID #{x}', value=0, step=1)
            if selected_id != 0:
                ids_to_remove.append(selected_id)
    remove_fees = Decimal(str(st.number_input('Remove Fees', value=0.00, step=0.01)))

    if account_name == 'None':
        st.markdown('Select an Account')
        st.stop()

    account_id = db.account_translate(account_name, 'id')

    transactions = db.get_transactions(
        account_id=account_id,
        include_statement_links=True,
    )
    transactions.loc[transactions['date_statement'].isna(), 'date_statement'] = transactions.loc[transactions['date_statement'].isna(), 'date']
    transactions = transactions.loc[
        (transactions['date_statement'] >= start_date) & (transactions['date_statement'] <= end_date),
        :
    ]
    purchases = transactions.loc[transactions['amount']<ZERO, :].set_index('taction_id')
    payments = transactions.loc[transactions['amount']>ZERO, :].set_index('taction_id')
    st.markdown('### Transactions')
    st.markdown(f"Purchaes: {purchases['amount'].sum()} ({len(purchases)})")
    st.markdown(f"Payments: {payments['amount'].sum()} ({len(payments)})")
    st.write(vt.translate_transactions(transactions))

    # + 1 day, sql date grab doesn't seem to include date
    # timezone issue?
    statements = db.get_statement_transactions(
        account_id=account_id,
        before_date=end_date + datetime.timedelta(days=1),
        after_date=start_date,
    ).set_index('id')
    statements = statements.drop(ids_to_remove)
    statement_purchases = statements.loc[statements['amount'] < ZERO, :]
    statement_payments = statements.loc[statements['amount'] > ZERO, :]
    st.markdown(f"Purchaes: {statement_purchases['amount'].sum() + remove_fees} ({len(statement_purchases)})")
    st.markdown(f"Payments: {statement_payments['amount'].sum()} ({len(statement_payments)})")
    st.write(vt.translate_statement_transactions(statements))