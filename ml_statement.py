""" ML statement capes """

import pandas as pd
from joblib import dump, load
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import numpy as np

from newdb_access import DbAccess

SVC_MODEL = load('statement_to_category_model.joblib')
SCALER = load('statement_scaler.joblib')
WORD_LIST = load('word_list.joblib')

def add_word_data(statement_df: pd.DataFrame) -> pd.DataFrame:
    for word in WORD_LIST:
        try:
            statement_df[f'{word}_present'] = statement_df['description'].str.contains(word)
        except:
            print(f'Could not do {word}')
    return statement_df

def predict_category(statement_entry: dict) -> int:
    statement_df = pd.DataFrame([statement_entry])
    statement_df = add_word_data(statement_df)
    statement_df = statement_df.set_index('taction_id')
    #statement_df = statement_df.drop(['id', 'date', 'statement_month', 'statement_year', 'description', 'taction_id'], axis='columns')
    statement_df = statement_df.drop(['id', 'date', 'statement_month', 'statement_year', 'description'], axis='columns')
    print([item for item in list(statement_df.columns) if '_present' not in item])
    scaled_data = SCALER.transform(statement_df)
    return SVC_MODEL.predict(scaled_data)[0]

def train_model(db: DbAccess):
    global SVC_MODEL
    global SCALER
    global WORD_LIST
    
    word_counts = {}
    statement_transactions = db.get_statement_transactions()
    for text in statement_transactions['description'].values:
        for word in text.split(' '):
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
    # Words that do not occur more than once are not very unique
    keys_to_remove = []
    for key in word_counts:
        if word_counts[key] == 1:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        word_counts.pop(key)

    statement_data = statement_transactions.copy()
    statement_data = statement_data.loc[~statement_data['taction_id'].isna(), :]
    taction_assignments = statement_data['taction_id']
    word_list = []
    for word in word_counts:
        word_list.append(word)
        try:
            statement_data[f'{word}_present'] = statement_data['description'].str.contains(word)
        except:
            print(f'Could not do {word}')

    statement_data = statement_data.drop(['id', 'date', 'statement_month', 'statement_year', 'description'], axis='columns')

    subs = db.get_subtotals().copy()
    matching_subs = subs.loc[subs['taction_id'].isin(taction_assignments), :]
    # We can only learn from transactions with single category
    count_map = matching_subs['taction_id'].value_counts().to_dict()
    matching_subs['occurrences'] = matching_subs['taction_id'].map(count_map)
    filtered_subs = matching_subs.loc[matching_subs['occurrences'] == 1, :]
    statement_data = statement_data.loc[statement_data['taction_id'].isin(filtered_subs['taction_id']), :]

    statement_data = statement_data.set_index('taction_id').sort_index()
    filtered_subs = filtered_subs.set_index('taction_id').sort_index()

    scaler = StandardScaler().fit(statement_data)
    scaled_statement_data = scaler.transform(statement_data)
    svc_model = SVC()
    svc_model.fit(scaled_statement_data, np.ravel(filtered_subs['category_id']))
    dump(svc_model, 'statement_to_category_model.joblib') 
    SVC_MODEL = svc_model

    words = pd.DataFrame()
    words['words'] = word_list
    words.to_csv('statement_word_list.csv')
    WORD_LIST = word_list
    dump(word_list, 'word_list.joblib')

    dump(scaler, 'statement_scaler.joblib')
    SCALER = scaler