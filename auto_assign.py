""" Automatic assignment of statement to transaction """

from decimal import Decimal

import streamlit as stl
import pandas as pd

import newdb_access as DbAccess
import view_translation as vt

FOURTEEN_DAYS = pd.Timedelta(days=14)

def attempt_assignment(st: stl, db: DbAccess, potential_matches: pd.DataFrame, description: str, entry: dict):
    potential_transaction_id = potential_matches['taction_id'].values[0]
    previous_assignments = db.get_statement_transactions(request_taction_id=potential_transaction_id)
    if len(previous_assignments) > 0:
        st.markdown(f"{description} already assigned")
    else:
        st.markdown(f"Assigning {description}")
        db.assign_statement_entry(entry['id'], potential_transaction_id)

def auto_assign(st: stl, db: DbAccess, entries: list):
    st.markdown('### Auto-Assignment')

    for entry in entries:
        entry_date = entry['date']
        min_date = entry_date - FOURTEEN_DAYS
        max_date = entry_date + FOURTEEN_DAYS
        potential_matches = db.get_transactions(
            amount = entry['amount'],
            after_date = min_date,
            before_date = max_date,
            account_id = entry['account_id'],
        )
        
        description = entry['description']
        if len(potential_matches) == 0:
            st.markdown(f"No matches for {description}")
        elif len(potential_matches) == 1:
            attempt_assignment(st, db, potential_matches, description, entry)
        else:
            precise_potential_matches = db.get_transactions(
                amount = entry['amount'],
                after_date = entry_date,
                before_date = entry_date,
                account_id = entry['account_id'],
            )
            if len(potential_matches) == 1:
                attempt_assignment(st, db, precise_potential_matches, description, entry)
            else:
                st.markdown(f'Multiple matching transactions for {description}')
                st.write(vt.translate_transactions(potential_matches.copy(deep=True)))