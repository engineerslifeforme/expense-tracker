""" Budget/Category Management """

from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta

import streamlit as stl
from newdb_access import DbAccess
import pandas as pd
import plotly.express as px

from budget_helper import get_monthly_budget_increment
from common import ZERO

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
    if st.checkbox('Check All Budget Status'):
        view_budget_status(db_data)
    if st.checkbox('View Profile Status'):
        view_profile_status(db_data)
    if st.checkbox('View Budget History'):
        view_budget_history(db_data)

def view_budget_history(db: DbAccess):
    stl.markdown('## Budget History')
    left, right = stl.columns(2)
    budgets = db.get_budgets()
    budget_id = db.budget_translate(left.selectbox('Select budget', options=budgets['name']), "id")
    start_date = pd.to_datetime(right.date_input('Start Date'))
    stl.warning('Some data does not make sense prior to May 2022!')
    category_ids = list(db.get_categories(budget_id=budget_id)['id'].values)
    subtotals_full = pd.concat([db.get_subtotals(category_id=cat, after_date=start_date) for cat in category_ids])
    subtotals = subtotals_full[['amount', 'date']]
    subtotals['source'] = 'sub'
    budget_adjustments_full = db.get_budget_adjustments(budget_id=budget_id, after_date=start_date)
    budget_adjustments = budget_adjustments_full[['date', 'amount']]
    budget_adjustments['source'] = 'bud_adj'
    all_amounts_full = pd.concat([subtotals, budget_adjustments]).sort_values('date', ascending=False)
    all_amounts_full['running_sum'] = all_amounts_full['amount'].cumsum()
    all_amounts = all_amounts_full.drop_duplicates(subset='date', keep='last')
    budget_balance = budgets[budgets['id'] == budget_id]['balance'].values[0]
    stl.write(f"Current Balance for selected budget: ${budget_balance}")
    all_amounts['balance'] = budget_balance - all_amounts['running_sum']
    stl.markdown(f"{len(all_amounts)} Entries")
    vis_all_amounts = all_amounts.copy()
    vis_all_amounts[['amount', 'running_sum', 'balance']] = vis_all_amounts[['amount', 'running_sum', 'balance']].astype(float)
    vis_all_amounts['type'] = 'expense'
    vis_all_amounts.loc[vis_all_amounts['amount'] > 0.0, 'type'] = 'credit'
    #stl.write(vis_all_amounts)
    # # This styles the line
    fig = px.line(
            vis_all_amounts,
            x='date',
            y='balance',
            title='Running balance of Budget',
        )
    fig.update_traces(line=dict(color='red', width=3.0))
    stl.plotly_chart(fig)
    vis_all_amounts_full = all_amounts_full.copy()
    vis_all_amounts_full['amount'] = vis_all_amounts_full['amount'].astype(float)
    vis_all_amounts_full.set_index('date', inplace=True)
    vis_all_amounts_full['type'] = 'expense'
    vis_all_amounts_full.loc[vis_all_amounts_full['amount'] > 0.0, 'type'] = 'credit'
    month_data = vis_all_amounts_full.groupby([
        vis_all_amounts_full.index.year,
        vis_all_amounts_full.index.month,
        'type',
    ]).sum().reset_index(level=0).rename({'date': 'year'}, axis='columns').reset_index().rename({'date': 'month'}, axis='columns')
    month_data['date'] = pd.to_datetime(month_data[['year', 'month']].assign(DAY=1))
    month_data.loc[month_data['amount'] < 0.0, 'amount'] = month_data.loc[month_data['amount'] < 0.0, 'amount'] * -1
    #stl.write(month_data)
    stl.info("Red dashed line is the monthly budget increment")
    fig = px.bar(
        month_data,
        x='date',
        y='amount',
        color='type',
        title='Monthly expenses and credits',
        barmode='group',
    )
    fig.add_hline(budgets.loc[budgets['id'] == budget_id, 'increment'].values[0], line_width=3, line_dash="dash", line_color="red")
    stl.plotly_chart(fig)
    
    if stl.checkbox("Show details"):
        transactions = db.get_transactions(after_date=start_date).sort_values('date', ascending=False)
        transactions = transactions.loc[transactions['taction_id'].isin(subtotals_full['taction_id']), :]
        transactions['amount'] = transactions['amount'].astype(float)
        stl.write(transactions)
        budget_adjustments_full = budget_adjustments_full.sort_values('date', ascending=False)
        budget_adjustments_full['amount'] = budget_adjustments_full['amount'].astype(float)
        stl.write(budget_adjustments_full)



def view_budget_status(db: DbAccess):
    stl.markdown('## All Budget Status')
    budgets = db.get_budgets()
    data = []
    for budget_data in budgets.to_dict(orient='records'):
        state, diff, expected_balance = view_profile_status(db, display=False, budget_id=budget_data['id'])
        data.append({
            'name' : budget_data['name'],
            'current_balance': budget_data['balance'],
            'state': state,
            'month_increment': get_monthly_budget_increment(budget_data),
            'diff': diff,
            'expected_balance': expected_balance,
        })
    data_df = pd.DataFrame(data)
    data_df['current_balance'] = data_df['current_balance'].astype(float)
    data_df['diff'] = data_df['diff'].astype(float)
    data_df['month_increment'] = data_df['month_increment'].astype(float)
    data_df['expected_balance'] = data_df['expected_balance'].astype(float)
    stl.write(data_df)

def view_profile_status(db: DbAccess, display: bool = True, budget_id: int = None):
    if display:
        stl.markdown('## Profile Status')
        _, budget_id = get_budget(db, 'View Profile Status for Budget')
    if budget_id is None:
        return
    
    budget_data = db.get_budgets(budget_id=budget_id)
    current_balance = budget_data['balance'].values[0]
    if display:
        stl.markdown(f'Current balance ${current_balance}')

    budget_profile = db.get_budget_profiles(budget_id=budget_id)
    data = []
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
    if len(budget_profile) < 1:
        if display:
            stl.warning('No profile!')
        monthly_increment = get_monthly_budget_increment(budget_data.to_dict(orient='records')[0])
        for i in range(1, 13):
            data.append({
                'date': pd.to_datetime(f'{i}/1/{today.year}'),
                'value': monthly_increment,
                'type': 'profile',
            })
        profile_start_balance = monthly_increment
        profile_end_balance = ZERO
    else:        
        profile_start_balance = budget_profile[f'month_{start_month}'].values[0]
        profile_end_balance = budget_profile[f'month_{end_month}'].values[0]
        for i in range(1,13):
            data.append({
                'date': pd.to_datetime(f'{i}/1/{today.year}').date(),
                'value': budget_profile[f'month_{i}'].values[0],
                'type': 'profile',
            })
    if display:
        stl.markdown(f'Start: Expected balance of ${profile_start_balance} on {profile_start_date}')
        stl.markdown(f'End: Expected balance of ${profile_end_balance} on {profile_end_date}')
    planned_balance_change = profile_end_balance - profile_start_balance
    days_in_period = profile_end_date - profile_start_date
    days_into_period = today - profile_start_date
    expected_balance = Decimal(str(profile_start_balance + planned_balance_change * Decimal(str((days_into_period/days_in_period)))))
    if display:
        stl.write(f'On {today} a balance of ${expected_balance} is expected')
    state = None
    diff = ZERO
    if current_balance >= profile_start_balance:
        if current_balance <= profile_end_balance:
            state = 'On Track'
            if display:
                stl.info('Budget on track')
        else:
            state = 'Extra'
            diff = current_balance - expected_balance
            if display:
                stl.success(f'Extra money available, ~${diff}')
    else:
        if current_balance >= profile_end_balance:
            state = 'On Track'
            if display:
                stl.info('Budget on track')
        else:
            state = 'Negative'
            diff = current_balance - expected_balance
            if display:
                stl.warning(f'Budget running low, ~${diff}')
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
    if display:
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
    return state, diff, expected_balance

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
    today = datetime.datetime.today().date()
    last_update = db.get_budget_update_date()
    stl.markdown(f"Last update {last_update}")
    next_update = last_update + relativedelta(months=1)
    update_limit = stl.date_input('Update Through', value=next_update)
    if stl.button('Update Budget Balances!'):
        while next_update < update_limit:
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