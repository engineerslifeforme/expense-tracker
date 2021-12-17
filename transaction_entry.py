""" Transaction Entry pane """

import math
from decimal import Decimal

import streamlit as stl
from db_access import DbAccess

def display_transaction_entry(st: stl, data_db: DbAccess):
    action_types = ['Transaction', 'Transfer']
    action_type = st.radio(
        'Type of Action',
        action_types
    )

    st.markdown(f'## {action_types[0]}')
    
    left, right = st.columns([1,4])
    date = right.date_input('Transaction Date')
    is_receipt = left.checkbox('Receipt?')
    description = st.text_input('Description')
    
    if action_type == action_types[0]:
        left, right = st.columns([1, 3])
        transaction_types = ['Withdraw', 'Deposit']
        transaction_type = left.radio(
            'Type',
            transaction_types
        )
        if transaction_type == transaction_types[0]: # Withdraw
            multiplier = Decimal('-1.00')
        elif transaction_type == transaction_types[1]: # Deposit
            multiplier = Decimal('1.00')
        else:
            st.write(f'Unknown transaction type {transaction_type}')
        sub_quantity = right.number_input(
            'Sub Items',
            min_value=1,
            step=1,
        )
        amount = Decimal('0.00')
        subs = []
        for x in range(sub_quantity):
            label = x + 1
            left, right = st.columns(2)
            sub_amount = Decimal(str(left.number_input(
                f'Amount #{label}',
                min_value = 0.00,
                step=0.01
            )))
            amount += sub_amount
            category = right.selectbox(
                f'Category #{label}',
                data_db.categories['name'],
            )
            subs.append((multiplier*sub_amount, category))
        amount = round(amount, 2)
        st.markdown(f'**Total: ${amount}**')
        left, right = st.columns(2)
        method = left.selectbox(
            'Method',
            list(data_db.methods['name']),
        )
        account = right.selectbox(
            'Account',
            data_db.accounts['name'],
        )
        st.markdown(f'Current Transactions: {date} ${amount} {method} {account}')

        added = st.button('Add')

        if added:
            data_db.add_transaction(
                date,
                account,
                method,
                description,
                is_receipt,
                amount * multiplier,
                subs,
            )
    # Transfer
    elif action_type == action_types[1]:
        left, middle, right = st.columns(3)
        amount = Decimal(str(left.number_input(
            'Amount',
            min_value = 0.00,
            step=0.01
        )))
        withdraw_account = middle.selectbox(
            'Withdraw Account',
            data_db.accounts['name'],
        )
        deposit_account = right.selectbox(
            'Deposit Account',
            data_db.accounts['name'],
        )
        st.markdown(f'Move ${amount} from {withdraw_account} to {deposit_account}')
        add_transfer = st.button('Add')

        if add_transfer:
            data_db.add_transfer(
                date,
                withdraw_account,
                deposit_account,
                description,
                is_receipt,
                amount,
            )


    else:
        st.markdown('Unsupported action type')

    st.markdown('### Similar Transactions')
    st.write()

    if amount != 0.00:
        matching_subs = data_db.transactions[data_db.transactions['amount'].abs() == amount]
        if len(matching_subs) > 0:
            st.write(matching_subs[[
                'amount', 
                'date', 
                'method',
                'account',
                'description',
                'valid',
            ]])
        else:
            st.markdown(f'No prevoius transactions of ${amount} found!')

    st.markdown('### Last Transactions')
    st.write((data_db.transactions.head(5))[[
        'id',
        'amount',
        'date',
        'method',
        'account',
        'description',
        'valid',
    ]])

    #st.markdown('### Last Subs')
    #st.write((data_db.subs.tail(5)).sort_values(by=['id'], ascending=False))

    st.markdown('## Account Status')
    st.write(data_db.accounts)

    
    st.markdown('## Budget Status')
    st.write(data_db.budgets)