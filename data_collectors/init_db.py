from datetime import datetime

from cryptobot.common.DBUtils import add_history_config
from cryptobot.common.cryptoutils import Configuration
from data_collectors.create_schema import create_data_db_schema, create_app_db_schema
from data_collectors.history_data_collector_zip import unzip_all, load_csv, download_history_data

#create and init the databases schemas
create_data_db_schema()
add_history_config('BTCUSDT','1m',datetime.strptime('17/07/2017 00:00:00', '%d/%m/%Y %H:%M:%S'),'data')
#add_history_config('ETHUSDT','1m',datetime.strptime('17/07/2017 00:00:00', '%d/%m/%Y %H:%M:%S'),'data')
create_app_db_schema()
# download history data
download_history_data()
# unzip history data
unzip_all()

# load the history data into the db history table
load_csv()