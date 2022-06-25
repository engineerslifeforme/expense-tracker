""" Budget/Category Management """

from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta

import streamlit as stl
from newdb_access import DbAccess
import pandas as pd
import plotly.express as px

def delta_to_days(delta: datetime.timedelta) -> int:
    return delta / datetime.timedelta(days=1.0)

def get_budget(db: DbAccess, label: str):
    budgets = db.get_budgets()
    options = ['None'] + list(budgets['name'])    
    budget_name = stl.selectbox('Create Profile for Budget', options=options)
    if budget_name == 'None':
        stl.warning('Select a budget!')
        budget_id = None
    else:
        budget_id = db.budget_translate(
            budget_name,
            'id'
        )
        stl.markdown(f'Selected {budget_name} ({budget_id})')
    return budget_name, budget_id

def display_budget_configuration(st: stl, db_data: DbAccess):
    if st.checkbox('Add New Budgets and Categories'):
        add_budget_category(st, db_data)
    if st.checkbox('Check and Update Budgets'):
        update_budgets(db_data)
    if st.checkbox('Adjust Budgets'):
        adjust_budget_balance(db_data)
    if st.checkbox('Adjust Increment'):
        adjust_budget_increment(db_data)
    if st.checkbox('Budget Transfer'):
        budget_transfer(db_data)
    if st.checkbox('Add Budget Profile'):
        add_budget_profile(db_data)
    if st.checkbox('View Profile Status'):
        view_profile_status(db_data)

def view_profile_status(db: DbAccess):
    stl.markdown('## Profile Status')
    budget_name, budget_id = get_budget(db, 'View Profile Status for Budget')
    if budget_id is None:
        return
    
    budget_data = db.get_budgets(budget_id=budget_id)
    current_balance = budget_data['balance'].values[0]
    current_increment = budget_data['increment'].values[0]
    stl.markdown(f'Current balance ${current_balance}')

    budget_profile = db.get_budget_profiles(budget_id=budget_id)
    if len(budget_profile) < 1:
        stl.warning('No profile!')
        return    

    today = datetime.datetime.today().date()
    start_month = today.month
    start_year = today.year
    end_month = start_month + 1
    end_year = start_year
    if end_month > 12:
        end_month = 1
        end_year += 1

    profile_start_date = pd.to_datetime(f'{start_month}/1/{start_year}').date()
    profile_end_date = pd.to_datetime(f'{end_month}/1/{end_year}').date()
    profile_start_balance = budget_profile[f'month_{start_month}'].values[0]
    profile_end_balance = budget_profile[f'month_{end_month}'].values[0]
    stl.markdown(f'Start: Expected balance of ${profile_start_balance} on {profile_start_date}')
    stl.markdown(f'End: Expected balance of ${profile_end_balance} on {profile_end_date}')
    planned_balance_change = profile_end_balance - profile_start_balance
    days_in_period = profile_end_date - profile_start_date
    days_into_period = today - profile_start_date
    expected_balance = Decimal(str(profile_start_balance + planned_balance_change * (days_into_period/days_in_period)))
    stl.write(f'On {today} a balance of ${expected_balance} is expected')
    if current_balance >= profile_start_balance:
        if current_balance <= profile_end_balance:
            stl.info('Budget on track')
        else:
            stl.success(f'Extra money available, ~${current_balance - expected_balance}')
    else:
        if current_balance >= profile_end_balance:
            stl.info('Budget on track')
        else:
            stl.warning(f'Budget running low, ~${expected_balance - current_balance}')
    data = []
    for i in range(1,13):
        data.append({
            'date': pd.to_datetime(f'{i}/1/{today.year}').date(),
            'value': budget_profile[f'month_{i}'].values[0],
            'type': 'profile',
        })
    data.append({
        'date': today,
        'value': expected_balance,
        'type': 'expected',
    })
    data.append({
        'date': today,
        'value': current_balance,
        'type': 'current',
    })
    data_df = pd.DataFrame(data)
    #data_df['float_value'] = data_df['value'].astype(float)
    #stl.write(data_df.drop('value', axis='columns'))
    stl.plotly_chart(px.line(
        data_df,
        x='date',
        y='value',
        color='type',
        title='Current, Expected, and Profile',
        markers=True,
    ))

def add_budget_profile(db: DbAccess):
    budget_name, budget_id = get_budget(db, 'Create Profile for Budget')
    if budget_id is None:
        return
    if len(db.get_budget_profiles(budget_id=budget_id)) > 0:
        stl.warning('A profile already exists for this budget')
    try:
        month_balances = [Decimal(value) for value in stl.text_input(f'Comma separated month start balances (Jan-Dec)').split(',')]
    except:
        stl.error('Must be 12 comma separate decimals')
        return
    if len(month_balances) != 12:
        stl.error('Please provide 12 values, comma separated')
        return
    value_list = []
    for index, value in enumerate(month_balances):
        value_list.append({'month': str(index+1), 'balance': value})
    data = pd.DataFrame(value_list)
    stl.plotly_chart(px.line(
        data,
        x='month',
        y='balance',
        title='Monthly Starting Balance',
    ))
    if stl.button('Add Profile'):
        db.add_budget_profile(budget_id, month_balances)
        stl.markdown(f'Profile added to {budget_name} ({budget_id})')
    

def budget_transfer(db: DbAccess):
    stl.markdown('## Budget Transfer')
    budgets = db.get_budgets()
    options = ['None'] + list(budgets['name'])
    left, right = stl.columns(2)
    withdraw_budget_name = left.selectbox('Budget to Withdraw From', options=options)
    valid_selected_budgets = True
    if withdraw_budget_name == 'None':
        valid_selected_budgets = valid_selected_budgets and False
        stl.warning('Select a valid budget to withdraw from!')
    deposit_budget_name = right.selectbox('Budget to Deposit From', options=options)
    if deposit_budget_name == 'None':
        valid_selected_budgets = valid_selected_budgets and False
        stl.warning('Select a valid budget to deposit from!')
    if valid_selected_budgets:
        withdraw_budget_id = db.budget_translate(
            withdraw_budget_name,
            'id'
        )
        deposit_budget_id = db.budget_translate(
            deposit_budget_name,
            'id'
        )
        withdraw_balance = budgets[budgets['name'] == withdraw_budget_name]['balance'].values[0]
        left.markdown(f'{withdraw_budget_name} Balance: ${withdraw_balance}')
        deposit_balance = budgets[budgets['name'] == deposit_budget_name]['balance'].values[0]
        right.markdown(f'{deposit_budget_name} Balance: ${deposit_balance}')
        amount = Decimal(str(stl.number_input('Amount to transfer', min_value=0.0)))
        if stl.button('Transfer'):
            stl.markdown(f'Transferred {amount}')
            _budget_adjust(
                db, Decimal('-1.00') * amount, withdraw_budget_id, withdraw_budget_name, withdraw_balance
            )
            _budget_adjust(
                db, amount, deposit_budget_id, deposit_budget_name, deposit_balance
            )


def adjust_budget_increment(db: DbAccess):
    stl.markdown('## Adjust Budget Increment')
    options = ['None'] + list(db.get_budgets()['name'])
    budget_name = stl.selectbox('Budget to Adjust', options=options)
    valid_budget = budget_name != 'None'
    if valid_budget:
        budget_id = db.budget_translate(
            budget_name,
            'id'
        )
        selected_budgets = db.get_budgets(budget_id=budget_id)
        current_increment = selected_budgets['increment'].values[0]
        frequency = selected_budgets['frequency'].values[0]
        stl.markdown(f'{budget_name} has a increment of ${current_increment} with frequency {frequency}')
    else:
        stl.markdown('Select a valid budget (not None)')
    increment = Decimal(str(
        stl.number_input('New Increment ($)', step=0.01)
    ))
    if valid_budget:
        if stl.button('Adjust Budget Increment'):
            db.set_budget_increment(increment, budget_id)
            stl.markdown(f'{budget_name} increment set to ${increment}')

def adjust_budget_balance(db: DbAccess):
    stl.markdown('## Adjust Budget Balance')
    options = ['None'] + list(db.get_budgets()['name'])
    budget_name = stl.selectbox('Budget to Adjust', options=options)
    valid_budget = budget_name != 'None'
    if valid_budget:
        budget_id = db.budget_translate(
            budget_name,
            'id'
        )
        current_budget = db.get_budgets(budget_id=budget_id)['balance'].values[0]
        stl.markdown(f'{budget_name} has a balance of ${current_budget}')
    else:
        stl.markdown('Select a valid budget (not None)')
    amount = Decimal(str(
        stl.number_input('Budget Change ($)', step=0.01)
    ))
    if valid_budget:
        if stl.button('Adjust Budget'):
            _budget_adjust(db, amount, budget_id, budget_name, current_budget)

def _budget_adjust(db: DbAccess, amount: Decimal, budget_id: int, budget_name: str, current_budget: Decimal):
    new_id = db.adjust_budget(amount, budget_id)
    stl.markdown(f'{budget_name} adjusted by ${amount}, ID: {new_id}')
    new_budget = db.get_budgets(budget_id=budget_id)['balance'].values[0]
    stl.markdown(f'Old budget: {current_budget}, New budget: {new_budget}')
    

def update_budgets(db: DbAccess):
    stl.markdown('Attempting to update budgets...')
    today = datetime.datetime.today().date()
    last_update = db.get_budget_update_date()
    next_update = last_update + relativedelta(months=1)
    while next_update < today:
        stl.markdown(f'Updating budgets for {next_update}')
        db.update_budgets()
        db.update_budget_update_date(next_update)
        last_update = db.get_budget_update_date()
        next_update = last_update + relativedelta(months=1)        
    stl.markdown('All done updating budgets')

def add_budget_category(st: stl, db_data: DbAccess):
    name = st.text_input('Budget Name')
    left, right = st.columns(2)    
    balance = Decimal(str(left.number_input(
        'Balance',
        step=0.01,
    )))
    purpose = right.selectbox('Purpose', options=['Spending', 'Saving'])
    frequency = left.selectbox(
        'Budget Update Frequency',
        options=['Daily', 'Weekly', 'Monthly', 'Yearly']
    )
    increment = Decimal(str(right.number_input('Update Increment', step=0.01)))
    if st.button('Add New Budget!'):
        new_id = db_data.add_budget(
            name,
            balance,
            purpose,
            frequency[0],
            increment,
        )
        st.write(f'Added new Budget {name} id: {new_id}')
    with st.expander('Current Budgets'):
        st.markdown('### Current Budgets')
        st.write(db_data.get_budgets())

    left, right = st.columns(2)
    category_name = left.text_input('Category Name')
    budget_name = right.selectbox('Assigned Budget', options=db_data.get_budgets()['name'])
    if st.button('Add Category!'):
        new_id = db_data.add_category(category_name, budget_name)
        st.write(f'Added new Category {category_name} id: {new_id}!')        
    with st.expander('Current Categories'):
        st.markdown('### Current Categories')
        categories = db_data.get_categories()
        #categories['budget'] = categories['budget_id'].map(db_data.budget_map)
        st.write(categories)