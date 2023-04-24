from data_collectors import cryptoutils
import csv
from binance import ThreadedWebsocketManager
import psycopg2

api_key = ''
api_secret = ''
writers  = {}
files  = {}
configurations = {}
header = ['open_time','open_price','high_price','low_price',
          'close_price','base_volume','close_time','quote_volume',
          'number_trades','taker_buy_base','taker_buy_quote','ignore']
symbol_id = {"BTCUSDT": 1, "ETHUSDT": 2, "DOGEUSDT": 3}

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

        # format data to insert it in databse (table for real time data)
        line_db = [content['t'],
                   symbol_id[msg['s']],
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


def insert_data_table(row):
    """
    Store the klines data coming from the websocket into database (table CandlestickRealTime)
    :param data:
    :return:
    """
    try:
        conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres",
        port="5432")

        cur = conn.cursor()

        insert_query = "INSERT INTO CandlestickRealTime VALUES (to_timestamp({}/1000),{},{},{},{},{},{},to_timestamp({}/1000),{},{},{},{})" \
            .format(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
        
        cur.execute(insert_query)

        cur.close()

        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


download_realtime_data('config.yml')
