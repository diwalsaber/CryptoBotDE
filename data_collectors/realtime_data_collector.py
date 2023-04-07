from data_collectors import cryptoutils
import csv
from binance import ThreadedWebsocketManager

api_key = ''
api_secret = ''
writers  = {}
files  = {}
configurations = {}


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
            writers[filename] = csv.writer(file)
            files[filename] = file

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
                0]
        writer.writerow(line)
        file.flush()


def download_realtime_data(configuration_file):
    """
    Store the klines data coming from the websocket
    :param configuration_file:
    :return:
    """
    confs = cryptoutils.read_configuration(configuration_file)
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()
    for configuration in confs:
        #save the configuration in the dict and start the socket
        configurations[configuration.symbol+'_'+configuration.interval] = configuration
        twm.start_kline_socket(callback=handle_socket_message, symbol=configuration.symbol, interval=configuration.interval)

    twm.join()
    for file in files:
        file.close()


def make_filename(symbol, interval):
    return '{}/{}_{}_realtime.csv'.format(configurations[symbol+'_'+interval].destination_dir, symbol, interval)


download_realtime_data('config.yml')