""" Methods for manipulating statement data """

import pandas as pd

def fix_dates(dates: pd.Series, year: int, year_map: dict) -> pd.Series:
    dates_df = pd.DataFrame(dates)
    dates_df.columns = ['date']
    date_split = dates.str.split('/', expand=True)
    date_split.columns = ['month', 'day']
    dates_df = pd.concat([dates_df, date_split], axis='columns')
    dates_df['year'] = dates_df['month'].map(year_map)
    dates_df['year'] = dates_df['year'].fillna(year)
    dates_df['date'] = pd.to_datetime(dates_df['date'] + '/' + dates_df['year'].astype(int).astype(str))
    return dates_df['date']