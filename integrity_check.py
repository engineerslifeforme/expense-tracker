""" Check data """

import streamlit as stl

from db_access import DbAccess

def display_integrity(st: stl, data_db: DbAccess):
    assigned_statements = data_db.statement_transactions.dropna(subset=['taction_id'])
    duplicate_statement_assignments = assigned_statements['taction_id'].duplicated()
    if any(duplicate_statement_assignments):
        st.error('Duplicate Statement Assignments Exists!')
        st.write(data_db.statement_transactions[duplicate_statement_assignments])
    else:
        st.success('No Duplicate Statement Assignments!')