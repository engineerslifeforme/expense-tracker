""" ML Management """

import streamlit as stl

from newdb_access import DbAccess
from ml_statement import train_model

def ml_management(st: stl, db: DbAccess):
    st.markdown('ML Management')
    if st.button('Re-Train Suggestions'):
        train_model(db)
        st.markdown('Retrain Complete!')