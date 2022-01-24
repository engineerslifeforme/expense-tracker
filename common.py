""" Common Functions """

from decimal import Decimal

import streamlit as st

from newdb_access import DbAccess

ZERO = Decimal('0.00')

def get_category_selection(db: DbAccess, label='Category') -> int:
    options_list = ['None'] + list(db.get_categories()['name'])
    category_name = st.selectbox(label, options=options_list)
    if category_name == 'None':
        return None
    else:
        return db.category_translate(category_name, 'id')