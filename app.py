from pathlib import Path

import streamlit as st
import sqlite3
import pandas as pd

from db_access import DbAccess
from transaction_entry import display_transaction_entry
from search_tab import display_search
from delete_tab import display_delete
from plot_tab import display_plot
from edit import display_edit
from account_manage import display_account_management

st.set_page_config(layout="wide")

st.sidebar.markdown('# Expense App')

data_db = DbAccess(Path('example.db'))

modes = [
    'Entry', 
    'Search', 
    'Delete Transaction', 
    'Plotting', 
    'Admin Edit',
    'Account Management',
]
mode = st.sidebar.radio(
    'Mode',
    modes
)

if mode == modes[0]:
    st.markdown('# Transaction Entry')
    display_transaction_entry(st, data_db)
elif mode == modes[1]:
    st.markdown('## Transaction Search')
    display_search(st, data_db)
elif mode == modes[2]:
    st.markdown('## Delete Transaction')
    display_delete(st, data_db)
elif mode == modes[3]:
    st.markdown('## Plotting')
    display_plot(st, data_db)
elif mode == modes[4]:
    st.markdown('## Admin Edit')
    display_edit(st, data_db)
elif mode == modes[5]:
    st.markdown('## Account Management')
    display_account_management(st, data_db)
else:
    st.write(f'Unknown mode {mode}')  