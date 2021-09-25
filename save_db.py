""" Save DB to server """

from datetime import date
from pathlib import Path
import shutil
import sys

action = sys.argv[1]

SERVER = Path('/Volumes/Media/Expense')
LOCAL_FILE = 'example.db'

if action == 'upload':
    print('Uploading...')
    date_str = date.today().strftime("%Y%m%d")
    new_file = SERVER / f'{date_str}.db'
    shutil.copyfile(LOCAL_FILE, new_file)
elif action == 'download':
    print('Downloading...')
    server_file = next(SERVER.glob('*.db'))
    shutil.copyfile(server_file, LOCAL_FILE)
else:
    print(f'Unknown command {action}')