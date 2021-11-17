""" Edit tab """

import streamlit as stl
from db_access import DbAccess

def display_edit(st: stl, db_data:DbAccess):
    left, right = st.beta_columns(2)
    selected_table = left.selectbox(
        'Table',
        options=[
            'account',
            'sub',
            'taction',
            'method',
            'category',
            'budget',
            'statement_transactions',
        ]
    )
    id_to_change = right.number_input(
        'Entry ID to change',
        min_value=0,
    )
    selected_table_data = db_data.get_data(selected_table)
    st.write(selected_table_data[selected_table_data['id'] == id_to_change])
    left, right = st.beta_columns(2)
    field_to_change = left.selectbox(
        'Field',
        options = list(selected_table_data.columns)
    )
    new_value = right.text_input(
        'New Value',
        value='0'
    )
    use_quotes = st.checkbox('New Value is String?')
    if st.button('Edit Entry!'):
        db_data._update(
            selected_table,
            field_to_change,
            new_value,
            id_to_change,
            use_quotes=use_quotes,
        )
        st.markdown(f'Edited `{selected_table}` entry id `{id_to_change}`')
        st.markdown(f'Changed field `{field_to_change}` to new value `{new_value}`')
        st.write(selected_table_data[selected_table_data['id'] == id_to_change])