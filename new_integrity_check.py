""" Check database integrity """

import streamlit as stl

from newdb_access import DbAccess
import view_translation as vt

def _delete_entry(db, candidate):
    sql = f'DELETE FROM statement_transactions WHERE id={candidate}'
    stl.markdown(sql)
    db.cursor.execute(sql)
    db.con.commit()

def integrity_check(st: stl, db: DbAccess):
    statement_transactions_all = db.get_statement_transactions()
    statement_transactions = statement_transactions_all.dropna(subset=['taction_id'])
    duplicates = statement_transactions[statement_transactions['taction_id'].duplicated()]
    tactions_with_duplicate_assignment = duplicates['taction_id']
    if len(tactions_with_duplicate_assignment) == 0:
        st.success('No duplicate statement to transaction assignments')
    else:
        st.error('Duplicate statement to transaction assignments')
        duplicate_statements = statement_transactions[statement_transactions['taction_id'].isin(tactions_with_duplicate_assignment)]
        view = vt.translate_statement_transactions(
            duplicate_statements, 
            sort_column='taction_id'
        )
        st.write(view)

        if st.checkbox('Delete Some Entries?'):
            delete_list = []
            with st.form('Delete Form'):
                for taction_id in tactions_with_duplicate_assignment:
                    duplicates = statement_transactions[statement_transactions['taction_id'] == taction_id]
                    st.write(vt.translate_statement_transactions(duplicates))
                    delete_candidate = duplicates['id'].max()
                    if st.checkbox(f'Delete {delete_candidate}'):
                        delete_list.append(delete_candidate)
                if st.form_submit_button('Delete All'):
                    for candidate in delete_list:
                        _delete_entry(db, candidate)
        
        if st.checkbox('Attempt Reassign?'):
            taction_id = st.selectbox(
                'Duplicate Taction', 
                options=tactions_with_duplicate_assignment.astype(int),
            )
            st.markdown('Duplicate statements:')
            statements = statement_transactions[statement_transactions['taction_id'] == taction_id]
            st.write(vt.translate_statement_transactions(statements))
            st.markdown('Amount Transaction Matches:')
            amount_matches = db.get_transactions(amount = statements['amount'].values[0])
            st.write(vt.translate_transactions(amount_matches))

            st.markdown('Reassign:')
            left, right = st.columns(2)
            new_taction = right.selectbox('New Taction', options=amount_matches['taction_id'])
            statement_id = left.selectbox('Statement', options=statements['id'])
            if st.button('Reassign'):
                db.assign_statement_entry(statement_id, new_taction)

        if st.checkbox('Remove Statement Assignment'):
            statement_id = st.selectbox('Statement ID', options=duplicate_statements['id'])
            if st.button('Remove Assignemnt'):
                db.cursor.execute(f'UPDATE statement_transactions SET taction_id=NULL WHERE id={statement_id}')
                db.con.commit()
                st.markdown(f'Assignment on {statement_id} removed!')

    if st.checkbox('Delete Statement Entry?'):
        statement_id = st.number_input('Statement ID', step=1)
        if statement_id != 0:
            st.write(statement_transactions_all[statement_transactions_all['id'] == statement_id])
        if st.button('Delete Statement?'):
            _delete_entry(db, statement_id)
            st.markdown(f'Deleted {statement_id}')