""" Budget/Category Management """

from decimal import Decimal

import streamlit as stl
from newdb_access import DbAccess

def display_budget_configuration(st: stl, db_data: DbAccess):
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