import datetime
from threading import Thread

import psycopg2
from binance.client import Client

from data_collectors import cryptoutils
from data_collectors.cryptoutils import Configuration, DBTools

api_key = ''
api_secret = ''
header = ['open_time','open_price','high_price','low_price',
          'close_price','base_volume','close_time','quote_volume',
          'number_trades','taker_buy_base','taker_buy_quote','ignore']

def download_history_data():
    """
    Start downloading the klines history data configured in the configuration_file using the binance api
    :param configuration_file:
    :return:
    """
    conf = Configuration.get_instance()
    threads = []
    for pair_conf in conf.pairs_conf:
        thread = Thread(target=download_symbol_data,
                        args=(pair_conf.destination_dir, pair_conf.start_datetime,
                              pair_conf.end_datetime, pair_conf.symbol, pair_conf.interval))
        thread.start()
        threads.append(thread)
    # wait the end of all threads
    for thread in threads:
        thread.join()


def download_symbol_data(destination_data_dir, start_date, end_date, symbol, interval):
    client = Client(api_key, api_secret)
    file = open((destination_data_dir+'/{}_{}.csv').format(symbol, interval), "w")
    #write header
    file.write(','.join(str(h) for h in header) + '\n')
    #write rows
    for kline in client.get_historical_klines_generator(symbol=symbol,
                                                        interval=interval,
                                                        start_str=str(int(start_date.timestamp()*1000)),
                                                        end_str=str(int(end_date.timestamp()*1000)),
                                                        limit=1000):
        file.write(','.join(str(e) for e in kline)+'\n')

def download_missing_history_data():
    """
    Start downloading the klines history data configured in the configuration_file using the binance api
    :return:
    """
    conf = Configuration.get_instance()
    threads = []
    for configuration in conf.pairs_conf:
        thread = Thread(target=download_missing_symbol_data,
                        args=(configuration.destination_dir, configuration.symbol, configuration.interval))
        thread.start()
        threads.append(thread)
    # wait the end of all threads
    for thread in threads:
        thread.join()

def download_missing_symbol_data(destination_data_dir, symbol, interval):
    try:
        client = Client(api_key, api_secret)
        file = open((destination_data_dir+'/{}_{}.csv').format(symbol, interval), "w")
        #write header
        connection = DBTools.get_connection()
        cursor = connection.cursor()
        symbolId = cryptoutils.get_symbol_id(symbol)
        file.write(','.join(str(h) for h in header) + '\n')
        now = datetime.datetime.now()
        start_datetime = datetime.datetime(now.year, now.month, now.day, tzinfo=None)
        end_datetime = start_datetime + datetime.timedelta(days=1)
        #write rows
        for kline in client.get_historical_klines_generator(symbol=symbol,
                                                            interval=interval,
                                                            start_str=str(int(start_datetime.timestamp()*1000)),
                                                            end_str=str(int(end_datetime.timestamp()*1000)),
                                                            limit=1000):
            file.write(','.join(str(e) for e in kline)+'\n')
        file.close()
        cursor.execute("DROP TABLE IF EXISTS TMP")
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS TMP (
                    open_time bigint,
                    open_price FLOAT,
                    high_price FLOAT,
                    low_price FLOAT,
                    close_price FLOAT,
                    base_volume FLOAT,
                    close_time bigint,
                    quote_volume FLOAT,
                    number_trades FLOAT,
                    taker_buy_base FLOAT,
                    taker_buy_quote FLOAT,
                    ignore FLOAT
                    );
                """)
        with open((destination_data_dir+'/{}_{}.csv').format(symbol, interval), "r") as file:
            cursor.copy_expert("""COPY TMP (open_time,open_price,high_price,low_price,close_price,base_volume,
                close_time,quote_volume,number_trades,taker_buy_base,taker_buy_quote,ignore) 
                FROM STDIN WITH csv HEADER""",file)
        connection.commit()
        cursor.execute("""INSERT INTO CandleStickHistorical 
                                    (select distinct to_timestamp(open_time/1000),{},open_price,high_price,low_price,
                                    close_price,base_volume,to_timestamp(close_time/1000),quote_volume,
                                    number_trades,taker_buy_base,taker_buy_quote from tmp 
                                        where to_timestamp(open_time/1000) 
                                            not IN (select opentime from CandleStickHistorical 
                                                    where opentime >  (select max(opentime) from CandleStickHistorical WHERE  opentime < current_timestamp - interval '2 DAYS')))""".format(symbolId))
        cursor.execute("DROP TABLE IF EXISTS TMP")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBTools.return_connection(connection)


