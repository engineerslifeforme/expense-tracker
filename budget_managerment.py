""" Budget/Category Management """

import streamlit as stl
from db_access import DbAccess

def display_budget_configuration(st: stl, db_data: DbAccess):
    name = st.text_input('Budget Name')
    left, middle, right = st.beta_columns(3)
    frequency = middle.selectbox(
        'Budget Update Frequency',
        options=['Daily', 'Weekly', 'Monthly', 'Yearly']
    )
    balance = left.number_input(
        'Balance',
        step=0.01,
    )
    purpose = right.selectbox('Purpose', options=['Spending', 'Saving'])
    increment = st.number_input('Update Increment', step=0.01)
    st.button('Add New Budget!')
    with st.beta_expander('Current Budgets'):
        st.markdown('### Current Budgets')
        st.write(db_data.budgets)
    with st.beta_expander('Current Categories'):
        st.markdown('### Current Categories')
        categories = db_data.categories
        categories['budget'] = categories['budget_id'].map(db_data.budget_map)
        st.write(categories)