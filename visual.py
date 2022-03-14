""" Visual """

import datetime
from decimal import Decimal

import streamlit as st
import pandas as pd
import plotly.express as px

from newdb_access import DbAccess

ZERO = Decimal('0.00')

def visual_tab(db: DbAccess):
    st.markdown('## Visualize')
    today = datetime.datetime.today().date()
    month = today.month
    year = today.year

    if st.checkbox('Current Month?'):
        st.markdown('### Current Month')
        show_month(db, month, year)

    if st.checkbox('Previous Month?'):
        previous_month = month - 1
        previous_year = year
        if previous_month == 0:
            previous_month = 12
            previous_year -= 1
        st.markdown(f'### Previous Month')
        show_month(db, previous_month, previous_year)

    if st.checkbox('Configurable Month?'):
        left, right = st.columns(2)
        month = int(left.number_input('Month (1-12)', value=month, step=1, max_value=12, min_value=1))
        year = int(right.number_input('Year', value=year, step=1, max_value=year, min_value=2010))
        show_month(db, month, year)

    if st.checkbox('Last Year?'):
        show_date_range(db, start_month=month, start_year=year-1, end_month=month, end_year=year)

    if st.checkbox('Year to Date?'):
        show_date_range(db, 1, year, month, year)

    if st.checkbox('Custom Range?'):
        left, right = st.columns(2)
        show_date_range(
            db,
            int(left.number_input('Start Month (1-12)', value=month, step=1, min_value=1, max_value=12)),
            int(right.number_input('Start Year', value=year-1, step=1, min_value=2010, max_value=year)),
            int(left.number_input('End Month (1-12)', value=month, step=1, min_value=1, max_value=12)),
            int(right.number_input('End Year', value=year, step=1, min_value=2010, max_value=year)),
        )

def show_date_range(db: DbAccess, start_month: int, start_year: int, end_month: int, end_year: int):
    st.markdown(f'{start_month}/{start_year} - {end_month}/{end_year}')
    # TODO: end_month needs to be incremented
    transactions = db.get_transactions(
        after_date=pd.to_datetime(f'{start_month}/1/{start_year}'),
        before_date=pd.to_datetime(f'{end_month}/1/{end_year}')
    )
    transactions['month_date'] = transactions['date'].dt.year.astype(str) + '-' +\
                                 transactions['date'].dt.month.astype(str)
                                 
    transactions['group_type'] = 'expenses'
    transactions.loc[transactions['amount'] > ZERO, 'group_type'] = 'incomes'
    transactions['float_amount'] = transactions['amount'].astype(float).abs()
    grouped = transactions.groupby(['month_date', 'group_type']).sum().reset_index(drop=False)
    date_parts = grouped['month_date'].str.split('-', expand=True)
    grouped['month'] = date_parts[1].astype(int)
    grouped['year'] = date_parts[0].astype(int)
    grouped = grouped.sort_values(['year', 'month'], ascending=True)
    grouped['cumsum'] = grouped[['group_type', 'float_amount']].groupby('group_type').cumsum()['float_amount']
    st.plotly_chart(px.scatter(
        grouped,
        x='month_date',
        y = 'cumsum',
        color='group_type',
        #trendline='ols',
        title='Monthly Trend',
    ).update_traces(mode='lines'))

    subs = db.get_subtotals(
        after_date=pd.to_datetime(f'{start_month}/1/{start_year}'),
        before_date=pd.to_datetime(f'{end_month}/1/{end_year}')
    )
    subs['category'] = subs['category_id'].apply(db.category_translate, args=('name',))
    subs['budget_id'] = subs['category_id'].apply(db.get_budget_from_category)
    subs['float_amount'] = subs['amount'].astype(float)
    #st.write(subs)
    grouped_subs = subs.groupby('category').sum().reset_index(drop=False)
    grouped_subs['abs_float_amount'] = grouped_subs['float_amount'].abs()
    grouped_subs = grouped_subs.sort_values('abs_float_amount', ascending=False)
    st.plotly_chart(px.bar(
        grouped_subs,
        y='category',
        x='float_amount',
        orientation='h',
        color='category',
        height=800,
    ))

    months = end_year*12 + (end_month-1) - start_year*12 + (start_month-1)
    show_budget_status(subs, db, months)

def show_month(db: DbAccess, month: int, year: int):
    st.markdown(f'({month}/{year})')
    end_month = month+1
    end_year = year
    if end_month > 12:
        end_month = 1
        end_year = year+1
    transactions = db.get_transactions(
        after_date=pd.to_datetime(f'{month}/1/{year}'),
        before_date=pd.to_datetime(f'{end_month}/1/{end_year}')
    )
    # Should probably add this to the get function
    transactions = transactions.loc[transactions['transfer'] != 1]
    transactions['group_type'] = 'expenses'
    transactions.loc[transactions['amount'] > ZERO, 'group_type'] = 'incomes'
    transactions['float_amount'] = transactions['amount'].astype(float).abs()    
    #st.write(transactions)
    st.plotly_chart(px.bar(
        transactions,
        x='group_type',
        y='float_amount',
        color='group_type',
        custom_data=['description']
    ))

    subs = db.get_subtotals(in_taction_list=transactions['taction_id'].values)
    subs['category'] = subs['category_id'].apply(db.category_translate, args=('name',))
    subs['budget_id'] = subs['category_id'].apply(db.get_budget_from_category)
    #subs['budget'] = subs['budget_id'].apply(db.budget_translate, args=('name',))
    subs['group_type'] = 'expenses'
    subs.loc[subs['amount'] > ZERO, 'group_type'] = 'incomes'
    subs['float_amount'] = subs['amount'].astype(float)
    sub_groups = subs.groupby('category').sum().reset_index(drop=False)
    sub_groups['group_type'] = 'expenses'
    sub_groups.loc[sub_groups['float_amount'] > 0.0, 'group_type'] = 'incomes'
    sub_groups['float_amount'] = sub_groups['float_amount'].abs()
    #st.write(subs)
    st.plotly_chart(px.bar(
        sub_groups,
        x='category',
        y='float_amount',
        color='group_type',
    ))
    show_budget_status(subs, db)

def show_budget_status(subs: pd.DataFrame, db: DbAccess, months: int = 1):
    months_float = float(months)/12.0
    sub_by_budget = subs.groupby('budget_id').sum()
    budgets = db.get_budgets()
    budgets['float_increment'] = budgets['increment'].astype(float)
    budgets['monthly_increment'] = budgets['float_increment']
    frequency_factors = {
        'D': 356.0*months_float,
        'W': 52.0*months_float,
        'Y': 1*months_float,
        'M': 12.0*months_float,
    }
    for frequency_type in frequency_factors:
        budgets.loc[budgets['frequency'] == frequency_type, 'monthly_increment'] = budgets.loc[budgets['frequency'] == frequency_type, 'float_increment']*frequency_factors[frequency_type]
    budgets = budgets.join(sub_by_budget['float_amount'], on='id', how='left')
    budgets['float_amount'] = budgets['float_amount'].fillna(0.0)
    budgets['monthly_remaining'] = ((budgets['monthly_increment'] +  budgets['float_amount']) / budgets['monthly_increment'])*100.0
    budgets['status'] = 'Budget Remaining'
    budgets.loc[budgets['monthly_remaining'] < 0.0, 'status'] = 'Overspent'
    #st.write(budgets)
    st.plotly_chart(px.bar(
        budgets.sort_values('name'),
        x='monthly_remaining',
        y='name',
        orientation='h',
        color='status',
        title='Remaining Monthly Budget',
        height=1200,
    ))
    