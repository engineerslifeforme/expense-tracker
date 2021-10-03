""" Budget/Category Management """

import streamlit as stl
from db_access import DbAccess

def display_budget_configuration(st: stl, db_data: DbAccess):
    st.markdown('### Current Budgets')
    st.write(db_data.budgets)
    st.markdown('### Current Categories')
    st.write(db_data.categories)