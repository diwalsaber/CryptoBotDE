from data_collectors.history_data_collector_api import download_missing_history_data
from data_collectors.realtime_data_collector import download_realtime_data

# start downloading realtime data with websocket
download_realtime_data()

# download today missing data
download_missing_history_data()