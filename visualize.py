""" Visualize data """

import streamlit as st
import pandas as pd
import plotly.express as px

from newdb_access import DbAccess

def view_visualize_tab(db: DbAccess):
    st.markdown('## Visualization')

    transactions = db.get_transactions()
    date_index = pd.DatetimeIndex(transactions['date'])
    transactions['year'] = date_index.year
    transactions['month'] = date_index.month
    balance = transactions[['month', 'year', 'amount']].groupby(['year', 'month']).sum().reset_index(drop=False)
    balance['amount'] = balance['amount'].astype(float)
    balance['id'] = (balance['year'] - 2010) * 12 + balance['month'] - 1
    st.write(balance)
    st.plotly_chart(px.line(
        balance,
        x='id',
        y='amount',
    ))

