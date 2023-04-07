from threading import Thread
from binance.client import Client

from data_collectors import cryptoutils

api_key = ''
api_secret = ''


def download_history_data(configuration_file):
    """
    Start downloading the klines history data configured in the configuration_file using the binance api
    :param configuration_file:
    :return:
    """
    configurations = cryptoutils.read_configuration(configuration_file)
    threads = []
    for configuration in configurations:
        thread = Thread(target=download_symbol_data,
                        args=(configuration.destination_dir, configuration.start_datetime,
                              configuration.end_datetime, configuration.symbol, configuration.interval))
        thread.start()
        threads.append(thread)
    # wait the end of all threads
    for thread in threads:
        thread.join()


def download_symbol_data(destination_data_dir, start_date, end_date, symbol, interval):
    client = Client(api_key, api_secret)
    file = open((destination_data_dir+'/{}_{}.csv').format(symbol, interval), "w")
    for kline in client.get_historical_klines_generator(symbol=symbol,
                                                        interval=interval,
                                                        start_str=str(int(start_date.timestamp()*1000)),
                                                        end_str=str(int(end_date.timestamp()*1000))):
        file.write(','.join(str(e) for e in kline)+'\n')


download_history_data('config.yml')
