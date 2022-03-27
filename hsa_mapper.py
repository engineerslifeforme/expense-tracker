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

from newdb_access import DbAccess
from view_translation import translate_transactions, translate_hsa

NEGATIVE_ONE = Decimal('-1.00')

def view_hsa_mapper(db: DbAccess):
    st.markdown('## HSA Mapper')
    if st.checkbox('Entry?'):
        show_entry(db)
    if st.checkbox('Find Unclaimed'):
        show_unclaimed(db)
    if st.checkbox('Table Entries'):
        st.markdown('### HSA Distribution Table Entries')
        entries = db.get_hsa_distributions()
        if st.checkbox('Filter out HSA Debits'):
            entries = entries.loc[entries['hsa_debit'] == 0, :]
        if st.checkbox('Fitler out Dependent Care'):
            entries = entries.loc[entries['dependent_care'] == 0, :]
        if st.checkbox('Show Receipt Assign Dialog'):
            distribution_id = int(st.number_input('Distribution ID', min_value=0, step=1))
            full_path = get_path(db)
            if st.button('Assign'):
                db.assign_hsa_receipt(full_path, distribution_id)
                st.markdown(f'Assigned {full_path} to ID: {distribution_id}')
        st.markdown(f'{len(entries)} Entries')
        st.write(translate_hsa(entries))

def get_path(db: DbAccess):
    dir_map = db.get_hsa_paths()
    file_dir = Path(dir_map[st.selectbox('File Directory', options=list(dir_map.keys()))])
    st.markdown(f'Path: {file_dir}')
    filename = st.selectbox('Filename', options=os.listdir(file_dir))
    full_path = file_dir / filename
    st.markdown(f'Full Path: {full_path}')
    return full_path

def show_unclaimed(db: DbAccess):
    st.markdown('### Unclaimed')
    categories = st.multiselect(
        'Choose Medical Category',
        options=db.get_categories()['name']
    )
    if len(categories) > 0:
        transactions = db.get_transactions()
        first_category_id = db.category_translate(categories[0], 'id')
        subs = db.get_subtotals(category_id=first_category_id)
        transactions = transactions.loc[transactions['taction_id'].isin(subs['taction_id']), :]
        st.markdown(f'{len(transactions)} Transactions prior to filter')
        hsa_entries = db.get_hsa_distributions()
        used_id_list = list(hsa_entries['expense_taction_id']) + list(hsa_entries['distribution_taction_id'])
        st.markdown(f'Filtered {len(used_id_list)} transactions')
        unclaimed = transactions.loc[~transactions['taction_id'].isin(used_id_list), :]
        st.write(translate_transactions(unclaimed))
        st.markdown(f'{len(unclaimed)} Unclaimed Transactions!')
    else:
        st.error('Select a Category!')
        
def show_entry(db: DbAccess):
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
    st.markdown(f'{len(expense_data)} Entries')

    expense_record = expense_data.to_dict(orient='records')
    current_index = int(st.number_input('Inspect Index', min_value=0, max_value=len(expense_record)-1, step=1))
    source_label = st.text_input('Source Label')
    source_id = f'{source_id}-{current_index}'
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
    if st.checkbox('Manual Entry?'):
        selected_expense = int(st.number_input('Expense taction ID', min_value=0, step=1))
        st.write(translate_transactions(db.get_transactions(taction_id_request=selected_expense)))
    else:
        selected_expense = st.selectbox('Selected Expense', options=potential_expenses['taction_id'])

    st.markdown('Potential Distributions:')
    potential_distributions = db.get_transactions(amount=current_record['Submitted Amount'])
    st.write(translate_transactions(potential_distributions))
    selected_distribution = st.selectbox('Selected Distribution', options=potential_distributions['taction_id'])

    
    if st.checkbox('Receipt Exists?', value=True):
        full_path = get_path(db)
    else:
        full_path = None

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
            source_id,
        )
        st.markdown(f'Added HSA Distribution: {new_id}')
    if st.button('Add unknown'):
        new_id = db.add_hsa_distribution(
            date,
            person,
            merchant,
            amount,
            description,
            'NULL',
            'NULL',
            'NULL',
            source_id,
        )
    if st.button('Add Direct HSA Payment'):
        new_id = db.add_hsa_distribution(
            date,
            person,
            merchant,
            amount,
            description,
            'NULL',
            'NULL',
            'NULL',
            source_id,
            hsa_debit=True,
        )
        st.markdown(f'Added HSA Distribution: {new_id}')
    if st.button('Add Dependent Care!'):
        new_id = db.add_hsa_distribution(
            date,
            person,
            merchant,
            amount,
            description,
            'NULL',
            'NULL',
            'NULL',
            source_id,
            hsa_debit=False,
            dependent_care=True,
        )
        st.markdown(f'Added HSA Distribution: {new_id}')

