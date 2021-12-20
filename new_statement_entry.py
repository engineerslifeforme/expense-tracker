""" Statement Entry """

from decimal import Decimal

import streamlit as stl
import pandas as pd

from newdb_access import DbAccess
from statement_manipulations import fix_dates

def view_statement_entry(st: stl, db: DbAccess):
    st.markdown('## Statement Entry')
    uploaded_file = st.file_uploader('Statement file')

    if uploaded_file is not None:
        st.markdown('Use month = 1 for yearly statements.')
        left, middle, right = st.columns(3)
        month = left.number_input('Statement Ending Month', min_value=1, max_value=12, step=1)
        year = middle.number_input('Statement Ending Year', min_value=2010, max_value=2050, step=1)
        account_id = db.account_translate(right.selectbox(
            'Account',
            db.get_accounts()['name']
        ), 'id')

        month_to_year_map = {}
        if st.checkbox('Map year?'):
            map_entries = st.number_input('# of Maps needed?', min_value=0, step=1)
            for x in range(map_entries):
                left, right = st.columns(2)
                month_to_map = left.number_input(f'({x}) Month to map', min_value=1, max_value=12, step=1)
                year_to_map = right.number_input(f'({x}) Year to map', min_value=2010, max_value=2050, step=1)
                month_to_year_map[str(month_to_map)] = year_to_map
        
        st.markdown('### Raw Data')
        raw_data = pd.read_csv(
            uploaded_file,
            header=None,
            dtype=str,
            index_col=False
        )
        st.write(raw_data)

        st.markdown('### Column Assignment')
        date_column = st.selectbox('Date Column', options=raw_data.columns)
        description_column = st.selectbox('Description Column', options=raw_data.columns)
        amount_column = st.selectbox('Amount Column', options=raw_data.columns)

        formed_data = raw_data
        formed_data = formed_data.loc[~formed_data[date_column].isna(), :]
        formed_data['date'] = fix_dates(
            raw_data[date_column],
            year,
            month_to_year_map,
        )
        formed_data['description'] = raw_data[description_column]
        formed_data['amount'] = raw_data[amount_column].str.replace(',', '').apply(Decimal) * Decimal('-1.00')

        for column in formed_data.columns:
            if column not in ['date', 'amount', 'description']:
                formed_data = formed_data.drop(column, axis='columns')

        view_data = formed_data.copy(deep=True)
        view_data['amount'] = formed_data['amount'].astype(float)

        st.write(view_data)

        current_statements = db.get_statement_transactions()
        if st.button('Add to database'):
            added = 0
            already_exists = 0
            for item in formed_data.to_dict(orient='records'):
                amount = item['amount']
                date = item['date']
                description = item['description']
                if amount == 0.0:
                    continue
                duplicates = current_statements.loc[
                    (current_statements['date'] == date) &
                    (current_statements['account_id'] == account_id) &
                    (current_statements['amount'] == amount) &
                    (current_statements['description'] == description)
                ]
                if len(duplicates) == 0:
                    db.add_statement_transaction(
                        date,
                        month,
                        year,
                        account_id,
                        amount,
                        description=description,
                    )
                    added += 1
                else:
                    st.write(f'{date} - {description} already exists! Aborting...')
                    already_exists += 1
            st.write(f'Added {added}')
            st.write(f'{already_exists} Already Existed')