import csv
from binance import ThreadedWebsocketManager

from data_collectors.cryptoutils import Configuration

api_key = ''
api_secret = ''
writers  = {}
files  = {}
configurations = {}
header = ['open_time','open_price','high_price','low_price',
          'close_price','base_volume','close_time','quote_volume',
          'number_trades','taker_buy_base','taker_buy_quote','ignore']

def handle_socket_message(msg):
    symbol = msg['s']
    content = msg['k']
    print(msg)
    if content['x']:
        interval = content['i']
        filename = make_filename(symbol, interval)
        print(filename)
        if writers.get(filename) == None:
            file = open(filename, "w", encoding='UTF8', newline='')
            writer = csv.writer(file)
            writers[filename] = writer
            files[filename] = file
            writer.writerow(header)

        writer = writers[filename]
        file = files[filename]
        line = [content['t'],
                content['o'],
                content['h'],
                content['l'],
                content['c'],
                content['v'],
                content['T'],
                content['q'],
                content['n'],
                content['V'],
                content['Q'],
                content['B']]
        writer.writerow(line)
        file.flush()


def download_realtime_data():
    """
    Store the klines data coming from the websocket
    :return:
    """
    conf = Configuration.get_instance()
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()
    for pair_conf in conf.pairs_conf:
        #save the configuration in the dict and start the socket
        configurations[pair_conf.symbol+'_'+pair_conf.interval] = pair_conf
        twm.start_kline_socket(callback=handle_socket_message, symbol=pair_conf.symbol, interval=pair_conf.interval)

    twm.join()

    for file in files:
        file.close()


def make_filename(symbol, interval):
    return '{}/{}_{}_realtime.csv'.format(configurations[symbol+'_'+interval].destination_dir, symbol, interval)


download_realtime_data()