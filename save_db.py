""" Save DB to server """

from datetime import date
from pathlib import Path
import shutil
import sys

action = sys.argv[1]

SERVER = Path('/Volumes/Media/Expense')
ASSETS = SERVER / 'assets'
LOCAL_FILE = 'example.db'

ASSET_LIST = [
    'statement_scaler.joblib',
    'statement_to_category_model.joblib',
    'word_list.joblib',
]

if action == 'upload':
    print('Uploading...')
    date_str = date.today().strftime("%Y%m%d")
    new_file = SERVER / f'{date_str}.db'
    print(f'Saving file to {new_file}')
    shutil.copyfile(LOCAL_FILE, new_file)
    for asset_file in ASSET_LIST:
        shutil.copyfile(
            asset_file,
            ASSETS / asset_file
        )
elif action == 'download':
    print('Downloading...')
    server_file_list = list(SERVER.glob('*.db'))
    server_file_list.sort()
    server_file = server_file_list[-1]
    print(f'Copying {server_file}')
    shutil.copyfile(server_file, LOCAL_FILE)
    for asset_file in ASSET_LIST:
        shutil.copyfile(
            ASSETS / asset_file,
            asset_file
        )
else:
    print(f'Unknown command {action}')