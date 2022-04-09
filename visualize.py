""" Visualize data """

from decimal import Decimal
import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from newdb_access import DbAccess
from common import get_category_selection, ZERO

def add_year_month(data: pd.DataFrame) -> pd.DataFrame:
    date_index = pd.DatetimeIndex(data['date'])
    data['year'] = date_index.year
    data['month'] = date_index.month
    return data

def group_by_year_month(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(['year', 'month']).sum().reset_index(drop=False)

def print_statistics(data: pd.DataFrame):
    st.markdown(f"Average Monthly Purchase {data['amount'].mean()}")
    st.markdown(f"Minimum Monthly Purchase {data['amount'].max()}")
    st.markdown(f"Maximum Monthly Purchase {data['amount'].min()}")
    st.markdown(f"Total Purchase {data['amount'].sum()}")
            

def view_visualize_tab(db: DbAccess):
    st.markdown('## Visualization')

    st.markdown('### Budgets')
    if st.checkbox('Show Budget Status'):
        pass

    st.markdown('### Transactions')
    if st.checkbox('Show Transaction Visuals'):
        transactions = db.get_transactions()
        transactions = add_year_month(transactions)
        balance = transactions[['month', 'year', 'amount']].groupby(['year', 'month']).sum().reset_index(drop=False)
        balance['amount'] = balance['amount'].astype(float)
        balance['id'] = (balance['year'] - 2010) * 12 + balance['month'] - 1
        st.plotly_chart(px.line(
            balance,
            x='id',
            y='amount',
        ))
    
    st.markdown('### Subtotals')
    if st.checkbox('Sub Visuals'):
        category_id = get_category_selection(db)
        if category_id is None:
            st.markdown('Select a Category')
        else:
            subs = db.get_subtotals(category_id=category_id)
            subs = add_year_month(subs)
            
            purchases = subs.loc[subs['amount']<ZERO, :]
            grouped_purchases = group_by_year_month(purchases[['year', 'month', 'amount']])
            grouped_purchases['date_id'] = grouped_purchases['year'] * 12 + grouped_purchases['month'] - 1
            complete_index = pd.Index(np.arange(grouped_purchases['date_id'].min(), grouped_purchases['date_id'].max() + 1), name='date_id')
            grouped_purchases = grouped_purchases.set_index('date_id').reindex(complete_index).reset_index(drop=False)
            grouped_purchases['amount'] = grouped_purchases['amount'].fillna(ZERO)
            grouped_purchases['month'] = grouped_purchases['date_id'] % 12
            grouped_purchases['year'] = (grouped_purchases['date_id'] - grouped_purchases['month']) / 12.0
            grouped_purchases['month'] = grouped_purchases['month'] + 1
            st.markdown('#### All-Time Statistics')
            print_statistics(grouped_purchases)
            st.markdown(f"Net {subs['amount'].sum()}")

            st.markdown('#### By Year')
            selected_year = st.number_input('Year', step=1, min_value=2010)
            year_purchase_data = grouped_purchases.loc[grouped_purchases['year'] == selected_year, :]
            print_statistics(year_purchase_data)
            st.markdown(f"Weekly {year_purchase_data['amount'].sum()/Decimal('52.0')}")
            year_data = subs.loc[subs['year'] == selected_year, :]
            st.markdown(f"Net {year_data['amount'].sum()}")
            if st.checkbox('Show Year Data'):
                subs_copy = year_data.copy(deep=True)
                subs_copy['amount'] = subs_copy['amount'].astype(float)
                st.write(subs_copy)
            
            balance = subs[['month', 'year', 'amount']].groupby(['year', 'month']).sum().reset_index(drop=False)
            balance['amount'] = balance['amount'].astype(float)
            balance['id'] = (balance['year'] - 2010) * 12 + balance['month'] - 1
            st.plotly_chart(px.line(
                subs,
                x='id',
                y='amount',
            ))


