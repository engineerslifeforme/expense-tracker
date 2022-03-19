""" HSA Mapper """

# Need to map HSA disbursements to expenses
# map to deposit
# map to expense
# capture receipt path

from io import StringIO
from decimal import Decimal
from pathlib import Path
import os

import streamlit as st
import pandas as pd
import yaml

from newdb_access import DbAccess
from view_translation import translate_transactions

NEGATIVE_ONE = Decimal('-1.00')

def view_hsa_mapper(db: DbAccess):
    st.markdown('## HSA Mapper')
    uploaded_file = st.file_uploader('HSA Expense Statement')

    if uploaded_file is None:
        st.warning('Upload an HSA Statement')
        st.stop()

    expense_data = pd.read_csv(
        StringIO(uploaded_file.getvalue().decode('utf-8')),
        usecols=[
            'Expense Date',
            'Expense',
            'Recipient/Patient',
            'Merchant/Provider',
            'Submitted Amount',
            'Expense Status',
            'Expense Description',
        ],
        parse_dates=['Expense Date'],
        dtype={'Submitted Amount': str}
    )
    expense_data['Submitted Amount'] = expense_data['Submitted Amount'].apply(Decimal)

    expense_record = expense_data.to_dict(orient='records')
    current_index = int(st.number_input('Inspect Index', min_value=0, max_value=len(expense_record)-1, step=1))
    current_record = expense_record[current_index]

    date = current_record['Expense Date']
    person = current_record['Recipient/Patient']
    merchant = current_record['Merchant/Provider']
    amount = current_record['Submitted Amount']
    description = current_record['Expense Description']
    st.markdown(f"""- Date: {date}    
- Person: {person}
- Merchant: {merchant}
- Amount: {amount}
- Description: {description}"""
)

    st.markdown('Already Saved Distributions')
    st.write(db.get_hsa_distributions(amount=current_record['Submitted Amount']))

    st.markdown('Potential Expenses:')
    potential_expenses = db.get_transactions(amount=NEGATIVE_ONE*current_record['Submitted Amount'])
    st.write(translate_transactions(potential_expenses))
    selected_expense = st.selectbox('Selected Expense', options=potential_expenses['taction_id'])

    st.markdown('Potential Distributions:')
    potential_distributions = db.get_transactions(amount=current_record['Submitted Amount'])
    st.write(translate_transactions(potential_distributions))
    selected_distribution = st.selectbox('Selected Distribution', options=potential_distributions['taction_id'])

    try:
        with open('doc_path_map.yaml', 'r') as fh:
            dir_map = yaml.safe_load(fh)
    except:
        st.error("No `doc_path_map.yaml' present.  Cannot continue.")
        st.stop()
    file_dir = Path(dir_map[st.selectbox('File Directory', options=list(dir_map.keys()))])
    st.markdown(f'Path: {file_dir}')
    filename = st.selectbox('Filename', options=os.listdir(file_dir))
    full_path = file_dir / filename
    st.markdown(f'Full Path: {full_path}')

    if st.button('Add Distrubtion!'):
        new_id = db.add_hsa_distribution(
            date,
            person,
            merchant,
            amount,
            description,
            selected_expense,
            selected_distribution,
            full_path,
        )
        st.markdown(f'Added HSA Distribution: {new_id}')