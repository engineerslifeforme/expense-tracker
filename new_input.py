""" Input page """

from decimal import Decimal

import streamlit as stl

from newdb_access import DbAccess
import view_translation as vt

ZERO = Decimal('0.00')

def show_account_status(st: stl, db: DbAccess, account_name: str):
    balance = db.get_accounts(account_id=db.account_translate(account_name, 'id'))['balance'].values[0]
    st.markdown(f'{account_name} has a balance of {balance}')

def show_budget_status(st: stl, db: DbAccess, category_name: str):
    category_id = db.category_translate(category_name, 'id')
    budget_id = db.get_budget_from_category(category_id)
    budget_name = db.budget_translate(budget_id, 'name')
    balance = db.get_budgets(budget_id=budget_id)['balance'].values[0]
    st.markdown(f'Category {category_name} is budget {budget_name} with balance {balance}')

def show_input(st: stl, db: DbAccess):
    st.markdown('## Expense Input')
    
    input_type = st.radio('Input Type', options=['Transaction', 'Transfer'])

    left, middle, right = st.columns(3)
    reciept = left.checkbox('Receipt?')
    date = middle.date_input('Date')
    description = st.text_input('Description')
    method = right.selectbox('Method', options=db.get_methods()['name'])

    if input_type == 'Transaction':
        left, middle, right = st.columns(3)
        withdraw = left.checkbox('Withdraw', value=True)
        if withdraw:
            multiplier = Decimal('-1.00')
        else:
            multiplier = Decimal('1.00')
        account = middle.selectbox('Account', options=db.get_accounts()['name'])
        sub_item_quantity = int(right.number_input('Sub Items', step=1, value=1))
        sub_list = []
        amount = ZERO
        for index in range(sub_item_quantity):
            left, right = st.columns(2)
            sub_amount = Decimal(str(left.number_input(f'Amount #{index}', step=0.01)))
            category = right.selectbox(f'Category #{index}', options=db.get_categories()['name'])
            sub_list.append((multiplier*sub_amount, category))
            amount += sub_amount 

        if st.button('Add Transaction'):
            st.markdown('Adding Transaction...')
            show_account_status(st, db, account)
            for sub in sub_list:
                show_budget_status(st, db, sub[1])
            db.add_transaction(
                date,
                account,
                method,
                description,
                reciept,
                multiplier*amount,
                sub_list
            )
            st.markdown('After transaction:')
            show_account_status(st, db, account)
            for sub in sub_list:
                show_budget_status(st, db, sub[1])

    elif input_type == 'Transfer':
        left, middle, right = st.columns(3)
        amount = Decimal(str(left.number_input('Amount', step=0.01)))
        withdraw_account = middle.selectbox(
            'Withdraw Account',
            db.get_accounts()['name'],
        )
        deposit_account = right.selectbox(
            'Deposit Account',
            db.get_accounts()['name'],
        )
        if st.button('Add Transfer'):
            st.markdown('Adding Transfer...')
            show_account_status(st, db, withdraw_account)
            show_account_status(st, db, deposit_account)
            db.add_transfer(
                date,
                withdraw_account,
                deposit_account,
                description,
                reciept,
                amount,
            )
            st.markdown('After transactions (withdraw then deposit):')
            show_account_status(st, db, withdraw_account)
            show_account_status(st, db, deposit_account)
            

    if amount != ZERO:
        matches = db.get_transactions(
            amount=amount,
            absolute_value=True,
        )
        if len(matches) > 0:
            st.write(vt.translate_transactions(matches.copy(deep=True)))
        else:
            st.markdown(f'No matches for {amount}')