import datetime
from threading import Thread
import psycopg2
from binance.client import Client

from cryptobot.common import cryptoutils, DBUtils
from cryptobot.common.cryptoutils import Configuration, DBConnector

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
    threads = []
    for pair_conf in DBUtils.get_history_configs():
        thread = Thread(target=download_symbol_data,
                        args=(pair_conf['dir'], pair_conf['startdate'],
                              datetime.date.today() - datetime.timedelta(days = 1), pair_conf['symbol'], pair_conf['interval']))
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
    threads = []
    for pair_conf in DBUtils.get_history_configs():
        thread = Thread(target=x,
                        args=(pair_conf['dir'], pair_conf['symbol'], pair_conf['interval']))
        thread.start()
        threads.append(thread)
    # wait the end of all threads
    for thread in threads:
        thread.join()

def download_missing_symbol_data2(destination_data_dir, symbol, interval):
    try:
        client = Client(api_key, api_secret)
        file = open((destination_data_dir+'/{}_{}.csv').format(symbol, interval), "w")
        #write header
        connection = DBConnector.get_data_db_connection()
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
        cursor.execute(f"""INSERT INTO CandleStickHistorical 
                                    (select distinct to_timestamp(open_time/1000),{symbolId},open_price,high_price,low_price,
                                    close_price,base_volume,to_timestamp(close_time/1000),quote_volume,
                                    number_trades,taker_buy_base,taker_buy_quote from tmp 
                                        where to_timestamp(open_time/1000) 
                                            not IN (select opentime from CandleStickHistorical 
                                                    where opentime >  (select max(opentime) from CandleStickHistorical WHERE  opentime < current_timestamp - interval '2 DAYS')))""")
        cursor.execute("DROP TABLE IF EXISTS TMP")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBConnector.return_data_db_connection(connection)


def download_all_missing_data():
    for pair_conf in DBUtils.get_history_configs():
        download_missing_symbol_data(pair_conf['symbol'], pair_conf['startdate'], pair_conf['interval'])

def download_missing_symbol_data(symbol, start_datetime, interval):
    try:
        client = Client(api_key, api_secret)
        symbolId = cryptoutils.get_symbol_id(symbol)
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f'''with missing_intervals as (SELECT time_bucket_gapfill('1 hours', opentime, 'UTC', 
        '{start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")}','{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}') AS my_time,
	count(*) as count_in_interval
    FROM candlestickhistorical
    WHERE symbolid = {symbolId}
    GROUP BY my_time)
select * from missing_intervals where count_in_interval is null or count_in_interval < 60 order by 1''')
        rows = cursor.fetchall()
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

        periods = list(map(lambda x: (x[0], x[0]+datetime.timedelta(hours=1)), rows))
        merged_periods = merge_date_ranges(periods)

        for period in merged_periods:
            start = int(period[0].timestamp())
            end = int(period[1].timestamp())
            for kline in client.get_historical_klines_generator(symbol=symbol,
                                                                interval=interval,
                                                                start_str=str(start*1000),
                                                                end_str=str(end*1000),
                                                                limit=1000):
                insert_query = "INSERT INTO TMP VALUES ({}/1000,{},{},{},{},{},{},{}/1000,{},{},{},{})" \
                    .format(kline[0], kline[1], kline[2], kline[3], kline[4], kline[5], kline[6], kline[7], kline[8], kline[9], kline[10],
                            kline[11])
                cursor.execute(insert_query)
            connection.commit()
            query = """INSERT INTO CandleStickHistorical 
                                    (select distinct to_timestamp(open_time/1000) AT TIME ZONE 'UTC',{},open_price,high_price,low_price,
                                    close_price,base_volume,to_timestamp(close_time/1000) AT TIME ZONE 'UTC',quote_volume,
                                    number_trades,taker_buy_base,taker_buy_quote from tmp where open_price is not null) ON CONFLICT DO NOTHING """.format(symbolId)
            cursor.execute(query)
            cursor.execute("TRUNCATE TMP")
            connection.commit()

        cursor.execute("DROP TABLE IF EXISTS TMP")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBConnector.return_data_db_connection(connection)



def interpolate_all_missing_data():
    for pair_conf in DBUtils.get_history_configs():
        interpolate_missing_for_symbol(pair_conf['symbol'])
def interpolate_missing_for_symbol(symbol):
    try:
        symbolId = cryptoutils.get_symbol_id(symbol)
        connection = DBConnector.get_data_db_connection()
        start_datetime = DBUtils.get_min_start_date(symbolId)
        end_datetime = DBUtils.get_min_start_date(symbolId)
        cursor = connection.cursor()
        sql = f'''with missing_intervals as (SELECT time_bucket_gapfill('1 hours', opentime, 'UTC', 
        '{start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")}','{end_datetime.strftime("%Y-%m-%d")}') AS my_time,
        	count(*) as count_by_interval
            FROM candlestickhistorical
            WHERE symbolid = {symbolId}
            GROUP BY my_time)
        select * from missing_intervals where count_by_interval is null or count_by_interval < 60 order by 1'''
        cursor.execute(sql)

        rows = cursor.fetchall()
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

        periods = list(map(lambda x: (x[0], x[0] + datetime.timedelta(hours=1)), rows))
        merged_periods = merge_date_ranges(periods)

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

        for period in merged_periods:
            print('start:',period[0])
            print('end:',period[1])
            sql = f"""WITH TMPTAB as (SELECT
                    time_bucket_gapfill('1 minutes', opentime, 'UTC',
                    to_timestamp('{period[0].strftime("%Y-%m-%d %H:%M:%S")}','YYYY-MM-DD HH24:MI:SS') - INTERVAL '1 day', 
                    to_timestamp('{period[1].strftime("%Y-%m-%d %H:%M:%S")}','YYYY-MM-DD HH24:MI:SS') + INTERVAL '1 day')	as my_open_time,
                    {symbolId} as symbolid,
                    interpolate(AVG(openprice)) AS openprice,
                    interpolate(AVG(highprice)) AS highprice,
                    interpolate(AVG(lowprice)) AS lowprice,
                    interpolate(AVG(closeprice)) AS closeprice,
                    interpolate(AVG(basevolume)) AS basevolume,
                    interpolate(AVG(numbertrades)) AS numbertrades,
                    interpolate(AVG(takerbuybase)) AS takerbuybase,
                    interpolate(AVG(takerbuyquote)) AS takerbuyquote
                   FROM candlestickhistorical
                   WHERE  opentime >= to_timestamp('{period[0].strftime("%Y-%m-%d %H:%M:%S")}','YYYY-MM-DD HH24:MI:SS') - INTERVAL '1 day'
                           AND opentime < to_timestamp('{period[1].strftime("%Y-%m-%d %H:%M:%S")}','YYYY-MM-DD HH24:MI:SS') + INTERVAL '1 day'
                           AND symbolid = {symbolId}
                   GROUP BY my_open_time)
                   INSERT INTO TMP SELECT extract(epoch from my_open_time)*1000,
                        openprice,
                        highprice,
                        lowprice,
                        closeprice,
                        basevolume,
                        extract(epoch from (my_open_time+ INTERVAL '59 SECOND'))*1000,
                        numbertrades,
                        takerbuybase,
                        takerbuyquote
                         from TMPTAB
                        """

            cursor.execute(sql)
            connection.commit()
        query = """INSERT INTO CandleStickHistorical 
                                            (select distinct to_timestamp(open_time/1000) AT TIME ZONE 'UTC',{},open_price,high_price,low_price,
                                            close_price,base_volume,to_timestamp(close_time/1000) AT TIME ZONE 'UTC',quote_volume,
                                            number_trades,taker_buy_base,taker_buy_quote from tmp where open_price is not null) ON CONFLICT DO NOTHING """.format(
            symbolId)
        cursor.execute(query)
        cursor.execute("TRUNCATE TMP")
        connection.commit()
    except Exception as e:
        print(e)
    finally:
        DBConnector.return_data_db_connection(connection)
def merge_date_ranges(data):
    result = []
    if len(data) > 0:
        new_interval = data[0]
        for t in data[1:]:
            if new_interval[1] >= t[0]:  #I assume that the data is sorted already
                new_interval = ((min(new_interval[0], t[0]), max(new_interval[1], t[1])))
            else:
                result.append(new_interval)
                new_interval = t
        else:
            result.append(new_interval)
    return result


download_all_missing_data()
interpolate_all_missing_data()

