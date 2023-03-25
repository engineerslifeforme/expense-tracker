from io import StringIO
from decimal import Decimal
from pathlib import Path

import streamlit as st
import pandas as pd

from newdb_access import DbAccess

# CREATE TABLE `hsa_transactions` (`id` text NOT NULL, `date` date, `amount` decimal(10,2), `expense_taction_id` int(11), `distribution_taction_id` int(11), `receipt_path` text, `eob_path` text, `bill_path` text);

def show_hsa_page(db: DbAccess):
    st.markdown("# HSA Management")
    if st.checkbox('Update Entries'):
        update_entries(db)
    if st.checkbox("Show Database Contents:"):
        st.write(db.get_hsa_transactions())
    if st.checkbox("Assign HSA Transactions"):
        assign_hsa_transactions(db)
    if st.checkbox("Find Un-refunded charges"):
        find_charges(db)

def find_charges(db: DbAccess):
    medical_category = db.category_translate(
        st.selectbox("Category", options=db.get_categories()['name']),
        'id',
    )
    subtotals = db.get_subtotals(category_id=medical_category)
    transactions = db.get_transactions()
    st.markdown(f"{len(transactions)} Total Transactions")
    transactions = transactions.loc[transactions['taction_id'].isin(subtotals['taction_id']), :]
    st.markdown(f"{len(transactions)} Transactions Filtered by category")
    hsa_transactions = db.get_hsa_transactions()
    transactions = transactions.loc[~transactions['taction_id'].isin(hsa_transactions['expense_taction_id']), :]
    st.markdown(f"{len(transactions)} Transactions Filtered by already mapped")
    st.write(transactions)

def assign_hsa_transactions(db: DbAccess):
    transactions = db.get_hsa_transactions()
    st.markdown(f"{len(transactions)} entries")
    empty_column = st.selectbox("Column to find empties on", options=['None'] + list(transactions.columns))
    if empty_column != 'None':
        transactions = transactions.loc[transactions[empty_column].isna(), :]
        st.markdown(f"Filtered to {len(transactions)}")
    if st.checkbox('Show Data'):
        st.write(transactions)
    selected_transaction = transactions.to_dict(orient='records')[
        st.number_input("Transaction Index", min_value=0, max_value=len(transactions))
    ]
    st.write(selected_transaction)
    st.markdown('Matching distribution transactions')
    matching_distribution_tactions = db.get_transactions(amount=selected_transaction['amount'])
    st.write(matching_distribution_tactions)
    if st.checkbox('Manually distribution ID selection'):
        selected_distribution_id = st.number_input("Selected Distribution ID", min_value=0, step=1)
        st.write(db.get_transactions(taction_id_request=selected_distribution_id))
    else:
        selected_distribution_id = st.selectbox("Selected Distribution ID", options=matching_distribution_tactions['taction_id'])
    if st.button("Assign Distribution"):
        db.assign_hsa_transaction_distribution(selected_transaction['id'], selected_distribution_id)
    st.markdown('Matching expense transactions')
    matching_expenses = db.get_transactions(amount=selected_transaction['amount'] * Decimal("-1.00"))
    st.write(matching_expenses)
    if st.checkbox('Manually expense ID selection'):
        selected_expense_id = st.number_input("Selected Exepnse ID", min_value=0, step=1)
        st.write(db.get_transactions(taction_id_request=selected_expense_id))
    else:
        selected_expense_id = st.selectbox("Selected Expense ID", options=matching_expenses['taction_id'])
    if st.button("Assign Expense"):
        db.assign_hsa_transaction_expense(selected_transaction['id'], selected_expense_id)
    path_dict = db.get_hsa_paths()
    selected_folder = None
    try:
        selected_folder = path_dict[st.selectbox("Receipt Folder", options=['None'] + list(path_dict.keys()))]
    except KeyError:
        pass
    if st.checkbox('Modify Path'):
        left, right = st.columns(2)
        to_replace = left.text_input("Text to replace")
        new_text = right.text_input("New Text")
        real_folder = selected_folder.replace(to_replace, new_text)
    else:
        real_folder = selected_folder
    st.markdown(f"Path: {real_folder}")
    if real_folder is not None:
        selected_file = st.selectbox("Selected File", options=list(Path(real_folder).iterdir()))
        if st.button("Map Receipt"):
            db.assign_hsa_transaction_receipt(selected_transaction['id'], selected_folder + selected_file.name)


def mirror_data(matching_id: str, db: DbAccess, selected_distribution: dict):
    distribution_id = selected_distribution['distribution_taction_id']
    expense_id = selected_distribution['expense_taction_id']
    receipt_path = selected_distribution['receipt_path']
    if distribution_id is not None:
        db.assign_hsa_transaction_distribution(matching_id, distribution_id)
    if expense_id is not None:
        db.assign_hsa_transaction_expense(matching_id, expense_id)
    if receipt_path is not None:
        db.assign_hsa_transaction_receipt(matching_id, receipt_path)    
        

def update_entries(db: DbAccess):
    st.markdown("## Add HSA Entries")
    uploaded_file = st.file_uploader('HSA Expense Statement')

    if uploaded_file is None:
        st.warning('Upload an HSA Statement')
        st.stop()

    expense_data = pd.read_csv(
        StringIO(uploaded_file.getvalue().decode('utf-8')),
        usecols=[
            'Expense', 
            'Expense Date', 
            'Submitted Amount',
            'Expense Description',
            'Expense Status',
            'Recipient/Patient',
        ],
        parse_dates=['Expense Date'],
        dtype={'Submitted Amount': str}
    )
    expense_data['Submitted Amount'] = expense_data['Submitted Amount'].apply(Decimal)
    st.markdown(f'{len(expense_data)} Entries')
    expense_data = expense_data.loc[(expense_data['Expense Status'] == 'Paid') & (expense_data['Expense Description'].str.contains('Distribution')), :]
    st.markdown(f"Filtered to {len(expense_data)} distributions")
    if st.checkbox('Show Raw Input Data:'):
        st.write(expense_data)
    expense_data['id'] = expense_data['Expense Date'].astype(str) +\
                         expense_data['Expense'].str[0] +\
                         expense_data['Recipient/Patient'].str[0] +\
                         expense_data['Submitted Amount'].astype(str)
    if any(expense_data.duplicated()):
        st.markdown('Removing some duplicates...')
        duplicate_ids = set(expense_data.loc[expense_data.duplicated(), 'id'])
        new_lists = []
        for duplicate_id in duplicate_ids:
            duplicates = expense_data.loc[expense_data['id'] == duplicate_id, :].reset_index()
            duplicates['id'] = duplicates['id'] + duplicates.index.astype(str)
            new_lists.append(duplicates)
        new_lists.append(expense_data.loc[~expense_data['id'].isin(duplicate_ids), :])
        expense_data = pd.concat(new_lists)
    if any(expense_data.duplicated()):
        st.error("All rows not unique")
    else:
        st.success("No duplicates!")
    if st.checkbox('Show Unique Data'):
        st.write(expense_data)
    existing_ids = db.get_hsa_transaction_ids()
    new_entries = expense_data.loc[~expense_data['id'].isin(existing_ids), :]
    st.markdown(f"Adding {len(new_entries)} New Entries")
    for item in new_entries.to_dict(orient='records'):
        db.add_hsa_transaction(item['Expense Date'], item['id'], item['Submitted Amount'])
