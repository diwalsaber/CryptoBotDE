import csv
from binance import ThreadedWebsocketManager
import psycopg2

from data_collectors.cryptoutils import Configuration, DBTools, get_symbol_id

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

        # format data to insert it in database (table for real time data)
        symbol_id = get_symbol_id(msg['s'])
        line_db = [content['t'],
                   symbol_id,
                   content['o'],
                   content['h'],
                   content['l'],
                   content['c'],
                   content['v'],
                   content['T'],
                   content['q'],
                   content['n'],
                   content['V'],
                   content['Q']]
        insert_data_table(line_db)


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


def insert_data_table(row):
    """
    Store the klines data coming from the websocket into database (table CandlestickRealTime)
    :param data:
    :return:
    """
    try:
        connection = DBTools.get_connection()
        cur = connection.cursor()
        insert_query = "INSERT INTO CandlestickRealTime VALUES (to_timestamp({}/1000),{},{},{},{},{},{},to_timestamp({}/1000),{},{},{},{})" \
            .format(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
        cur.execute(insert_query)
        cur.close()
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBTools.return_connection(connection)


download_realtime_data()
