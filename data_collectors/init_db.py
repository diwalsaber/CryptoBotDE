from data_collectors.create_schema import create_schema
from data_collectors.create_schema import init_symbols
from data_collectors.history_data_collector_api import download_history_data, download_missing_history_data
from data_collectors.history_data_collector_zip import unzip_all, load_csv
from data_collectors.realtime_data_collector import download_realtime_data

#create and init the database schema
create_schema()
init_symbols()
# download history data
download_history_data()
# unzip history data
unzip_all('data')
# load the history data into the db history table
load_csv('data')