""" Search """

from decimal import Decimal

import streamlit as stl

from newdb_access import DbAccess
import view_translation as vt

def convert_df(df):
   return df.to_csv().encode('utf-8')

def view_search(st: stl, db: DbAccess):
    st.markdown('## Search')
    amount = Decimal(str(st.number_input(
        'Amount',
        step=0.01
    )))
    if amount == Decimal('0.00'):
        amount = None
    categories = st.multiselect(
        'Categories',
        options=db.get_categories()['name']
    )
    accounts = ['None'] + list(db.get_accounts()['name'])
    account_name = st.selectbox('Account', options=accounts)
    if account_name == 'None':
        account_id = None
    else:
        account_id = db.account_translate(account_name, 'id')
    taction_id = st.number_input('Taction ID', step=1)
    if taction_id == 0:
        taction_id = None
    description = st.text_input('Transaction Description Match')
    if description == '':
        description = None
    
    start_date = None
    end_date = None    
    if st.checkbox('Apply Date Filter'):
        left, right = st.columns(2)
        start_date = left.date_input('Start Date')
        end_date = right.date_input('End Date')    

    if st.checkbox('Transactions'):
        only_valid = st.checkbox('Only Valid?', value=True)
        transactions = db.get_transactions(
            amount=amount,
            account_id=account_id,
            after_date=start_date,
            before_date=end_date,
            include_statement_links=True,
            only_valid=only_valid,
            description_text=description,
        )        

        if len(categories) > 0:
            first_category_id = db.category_translate(categories[0], 'id')
            subs = db.get_subtotals(category_id=first_category_id)
            transactions = transactions.loc[transactions['taction_id'].isin(subs['taction_id']), :]

        if st.checkbox('Only unmapped statements'):
            transactions = transactions.loc[transactions['statement_id'].isna(), :]
        
        columns = transactions.columns
        displayed_columns = st.multiselect('Displayed Columns', options=columns, default=list(columns))
        st.markdown(str(len(transactions)))
        if 'amount' in transactions.columns:
            st.markdown(f"Total amount: ${transactions['amount'].sum()}")
        view_frame = vt.translate_transactions(transactions[displayed_columns], db=db)
        st.write(view_frame)
        csv = convert_df(transactions)
        st.download_button(
            "Press to Download",
            csv,
            "searach.csv",
            "text/csv",
            key='download-csv'
        )

        #view_data = vt.translate_transactions(transactions)
    if st.checkbox('Statements'):
        statements = db.get_statement_transactions(
            amount=amount, 
            account_id=account_id,
            request_taction_id=taction_id,
        )
        st.write(vt.translate_statement_transactions(statements))
        


