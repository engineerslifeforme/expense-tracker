""" Plotting tab """

import streamlit as stl
import plotly.express as px

from db_access import DbAccess

def display_plot(st: stl, db_data:DbAccess):
    with st.expander('Total'):
        real_transactions = db_data.transactions.loc[db_data.transactions['valid'] == 1, :]
        real_transactions = real_transactions.loc[real_transactions['transfer'] == 0, :]
        real_transactions['month_year'] = real_transactions['date'].dt.to_period('M').astype(str)
        st.plotly_chart(
            px.bar(
                real_transactions.groupby(by='month_year').sum().reset_index(drop=False),
                x='month_year',
                y='amount',
                title='Net Transactions',
            )
        )
        st.plotly_chart(
            px.bar(
                real_transactions[real_transactions['amount'] < 0.0].groupby(by='month_year').sum().reset_index(drop=False),
                x='month_year',
                y='amount',
                title='Expenses'
            )
        )
    with st.expander('Budget Analysis'):
        budget = st.selectbox(
            'Budget',
            options=list(db_data.budgets['name'])
        )
        budget_data = db_data.subview[db_data.subview['budget'] == budget]
        budget_data['month_year'] = budget_data['date'].dt.to_period('M').astype(str)
        grouped = budget_data.groupby(by='month_year').sum().reset_index(drop=False)
        st.plotly_chart(
            px.bar(
                grouped,
                x='month_year',
                y='amount',
                title=f'Monthly {budget}',
            )
        )
        