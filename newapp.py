""" Main app page """

import streamlit as st

from newdb_access import DbAccess
from new_assignment import show_assignment_page
from new_statement_entry import view_statement_entry
from new_input import show_input
from new_integrity_check import integrity_check
from new_search import view_search
from ml_management import ml_management
from delete_tab import display_delete
from budget_managerment import display_budget_configuration

db = DbAccess('example.db')

st.set_page_config(layout="wide")

"""# Expense Tracker"""

task = st.sidebar.radio('Tasks', options=[
    'Input', 
    'Statement Assignment',
    'Statement Entry',
    'Integrity Check',
    'Search',
    'ML Management',
    'Delete',
    'Budget Management',
])

if task == 'Statement Assignment':
    show_assignment_page(st, db)
elif task == 'Input':
    show_input(st, db)
elif task == 'Statement Entry':
    view_statement_entry(st, db)
elif task == 'Integrity Check':
    integrity_check(st, db)
elif task == 'Search':
    view_search(st, db)
elif task == 'ML Management':
    ml_management(st, db)
elif task == 'Delete':
    display_delete(st, db)
elif task == 'Budget Management':
    display_budget_configuration(st, db)
else:
    st.markdown(f'Unknown task {task}')