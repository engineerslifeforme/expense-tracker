""" Statement Entry """

import streamlit as stl
import pandas as pd

from db_access import DbAccess

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

        if upload_is_csv:
            statement_transactions = pd.read_csv(uploaded_file)
            st.write(f'{len(statement_transactions)} Transactions Found!')
            
            if account_id in [0, 1, 8]: # Citi accounts 
                statement_transactions = statement_transactions.fillna(0.0)
                statement_transactions['amount'] = (statement_transactions['Credit'] - statement_transactions['Debit']).astype(float)
                statement_transactions['date'] = pd.to_datetime(statement_transactions['Date'])
                statement_transactions['description'] = statement_transactions['Description']
            elif account_id in [6, 7]:
                statement_transactions['amount'] = statement_transactions['Amount']
                statement_transactions['date'] = pd.to_datetime(statement_transactions['Transaction Date'])
                statement_transactions['description'] = statement_transactions['Description']
            
            st.write(statement_transactions)

        existing_transactions = data_db.statement_transactions.loc[
            (data_db.statement_transactions['statement_month'] == month) &
            (data_db.statement_transactions['statement_year'] == year) &
            (data_db.statement_transactions['account_id'] == account_id),
            :
        ]

        if len(existing_transactions) == 0:
            add_transactions = st.button('Add Transactions to Database')
            if add_transactions:
                for index, item in enumerate(statement_transactions.to_dict(orient='records')):
                    st.progress(float(index) / float(len(statement_transactions)))
                    data_db.add_statement_transaction(
                        item['date'],
                        month,
                        year,
                        account_id,
                        item['amount'],
                        description=item['description'],
                    )
        else:
            st.write('Statement has already been added')