from data_collectors.history_data_collector_zip import unzip_all, load_csv, download_history_data

print('start download data batch')
# download history data
download_history_data()
# unzip history data
unzip_all()
# load the history data into the db history table
load_csv()

print('end download data batch')