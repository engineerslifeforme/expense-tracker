""" Statement Entry """

from decimal import Decimal
from io import StringIO

import streamlit as stl
import pandas as pd

from db_access import DbAccess

def check_csv_format(st: stl, csv_file):
    lines = csv_file.readlines()
    lines = [line.decode('ascii') for line in lines]
    max_count = max([line.count(',') for line in lines])
    new_lines = [line.rstrip() + (',' * (max_count - line.count(','))) for line in lines]
    return '\n'.join(new_lines)

def display_statement_entry(st: stl, data_db: DbAccess):
    uploaded_file = st.file_uploader('Statement file')
    if uploaded_file is not None:
        st.write('Use month = 1 for yearly statements.')
        left, middle, right = st.beta_columns(3)
        month = left.number_input('Statement Ending Month', min_value=1, max_value=12, step=1)
        year = middle.number_input('Statement Ending Year', min_value=2010, max_value=2050, step=1)
        account_id = data_db.account_map_reverse[right.selectbox(
            'Account',
            data_db.accounts['name'],
        )]

        upload_is_csv = uploaded_file.name[-4:].lower() == '.csv'
        if upload_is_csv:
            st.write('CSV file uploaded!')
        else:
            st.write('File type unknown')

        month_to_year_map = {}
        if st.checkbox('Map year?'):
            map_entries = st.number_input('# of Maps needed?', min_value=0, step=1)
            for x in range(map_entries):
                left, right = st.beta_columns(2)
                month_to_map = left.number_input(f'({x}) Month to map', min_value=1, max_value=12, step=1)
                year_to_map = right.number_input(f'({x}) Year to map', min_value=2010, max_value=2050, step=1)
                month_to_year_map[str(month_to_map)] = year_to_map

        if upload_is_csv:
            tabula = st.checkbox('Tabula export?')
            if tabula:
                if st.checkbox('Attempt CSV fixing?'):
                    str_content = check_csv_format(st, uploaded_file)
                else:
                    str_content = uploaded_file.read().decode('ascii')
                if st.checkbox('Filter based on date format'):
                    lines = str_content.split('\n')
                    new_lines = []
                    for line in lines:
                        if '/' in line.split(',')[0]:
                            new_lines.append(line)
                        else:
                            print(f'Removing {line}')
                    st.write(new_lines)
                    str_content = '\n'.join(new_lines)
                # index_col = False, was occasionally using first column as index = bad
                statement_transactions = pd.read_csv(StringIO(str_content), header=None, dtype=str, index_col=False)
                with st.beta_expander('Raw Data'):
                    st.write(statement_transactions)
                bad_rows = statement_transactions[statement_transactions[0].isna()]
                if len(bad_rows) > 0:
                    st.markdown('Removing these rows:')
                    st.write(bad_rows)
                statement_transactions = statement_transactions.loc[~statement_transactions[0].isna(), :]
                column_count = len(statement_transactions.columns)
                if column_count == 3:
                    statement_transactions.columns = ['date', 'description', 'amount']
                    statement_transactions['amount'] = statement_transactions['amount'].str.replace(',', '').apply(Decimal)
                elif column_count == 4:
                    draft_columns = ['date', 'description', 'withdraw', 'deposit']
                    statement_transactions.columns = draft_columns
                    statement_transactions['withdraw'] = statement_transactions['withdraw'].fillna('0.00')
                    statement_transactions['deposit'] = statement_transactions['deposit'].fillna('0.00')
                    statement_transactions['withdraw'] = statement_transactions['withdraw'].str.replace(',', '').apply(Decimal)
                    statement_transactions['deposit'] = statement_transactions['deposit'].str.replace(',', '').apply(Decimal)
                    # -1 will get reversed below
                    statement_transactions['amount'] = (-1 * statement_transactions['deposit']) + statement_transactions['withdraw']
                    statement_transactions = statement_transactions.drop(['withdraw', 'deposit'], axis='columns')
                else:
                    st.error(f'Unexpected number of columns {column_count}')
                
                date_split = statement_transactions['date'].str.split('/', expand=True)
                date_split.columns = ['month', 'day']
                if any(date_split['month'].astype(int) == 12):
                    st.warning('December dates detected, select year carefully')
                statement_transactions = pd.concat([statement_transactions, date_split], axis='columns')
                statement_transactions['year'] = statement_transactions['month'].map(month_to_year_map)
                statement_transactions['year'] = statement_transactions['year'].fillna(year)
                statement_transactions = statement_transactions.dropna(subset=['date'])
                statement_transactions = statement_transactions.loc[statement_transactions['date'].str.contains('/'), :]
                statement_transactions['date'] = pd.to_datetime(statement_transactions['date'] + '/' + statement_transactions['year'].astype(int).astype(str))
                statement_transactions['amount'] = statement_transactions['amount'] * Decimal('-1.00')
            else:
                statement_transactions = pd.read_csv(uploaded_file, converters={'Credit': Decimal, 'Debit': Decimal, 'Amount': Decimal})
            st.write(f'{len(statement_transactions)} Transactions Found!')
            
            if account_id in [0, 1, 8] and not tabula: # Citi accounts 
                zero = Decimal('0.00')
                statement_transactions['Debit'] = statement_transactions['Debit'].fillna(zero)
                statement_transactions['Credit'] = statement_transactions['Credit'].fillna(zero)
                statement_transactions['amount'] = ((Decimal('-1.00') * statement_transactions['Credit']) - statement_transactions['Debit'])
                statement_transactions['date'] = pd.to_datetime(statement_transactions['Date'])
                statement_transactions['description'] = statement_transactions['Description']
            elif account_id in [6, 7] and not tabula:
                statement_transactions['amount'] = statement_transactions['Amount']
                statement_transactions['date'] = pd.to_datetime(statement_transactions['Transaction Date'])
                statement_transactions['description'] = statement_transactions['Description']
            if not any(statement_transactions['amount'].isna()):
                st.success('No NaN amounts!')
            st.write(statement_transactions)

        existing_transactions = data_db.statement_transactions.loc[
            (data_db.statement_transactions['statement_month'] == month) &
            (data_db.statement_transactions['statement_year'] == year) &
            (data_db.statement_transactions['account_id'] == account_id),
            :
        ]

        if len(existing_transactions) == 0:
            pass
        else:
            st.write('Statement may already have been added')
        add_transactions = st.button('Add Transactions to Database')
        if add_transactions:
            added = 0
            already_exists = 0
            for index, item in enumerate(statement_transactions.to_dict(orient='records')):
                amount = item['amount']
                date = item['date']
                description = item['description']
                if amount == 0.0:
                    continue
                duplicates = data_db.statement_transactions.loc[
                    (data_db.statement_transactions['date'] == date) &
                    (data_db.statement_transactions['account_id'] == account_id) &
                    (data_db.statement_transactions['amount'] == amount) &
                    (data_db.statement_transactions['description'] == description)
                ]
                if len(duplicates) == 0:
                    data_db.add_statement_transaction(
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