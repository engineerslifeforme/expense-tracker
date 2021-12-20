""" Main app page """

import streamlit as st

from newdb_access import DbAccess
from new_assignment import show_assignment_page
from new_statement_entry import view_statement_entry
from new_input import show_input

db = DbAccess('example.db')

st.set_page_config(layout="wide")

"""# Expense Tracker"""

task = st.sidebar.radio('Tasks', options=[
    'Input', 
    'Statement Assignment',
    'Statement Entry',
])

if task == 'Statement Assignment':
    show_assignment_page(st, db)
elif task == 'Input':
    show_input(st, db)
elif task == 'Statement Entry':
    view_statement_entry(st, db)
else:
    st.markdown(f'Unknown task {task}')