import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta

from dateutil import relativedelta
import requests
from os.path import exists
import os
import calendar
from threading import Thread
import zipfile
from data_collectors import cryptoutils
from data_collectors.cryptoutils import DBTools, Configuration

klines_baseurl = 'https://data.binance.vision/data/spot/{}/klines/'
daily_base_url = klines_baseurl.format('daily')
monthly_base_url = klines_baseurl.format('monthly')

def download_history_data():
    """
        Start downloading the klines history data configured in the configuration_file using the zip files
        :return:
        """
    conf = Configuration.get_instance()
    threads = []
    for pair_conf in conf.pairs_conf:
        thread = Thread(target=download_period_symbol_data,
                        args=(pair_conf.destination_dir, pair_conf.start_datetime, pair_conf.end_datetime,
                              pair_conf.symbol, pair_conf.interval))
        thread.start()
    # wait the end of all threads
    for thread in threads:
        thread.join()


def download_monthly_symbol_data(destination_base_dir, symbol, year, month, interval):
    """downloads into destination_dir the monthly history data for the given symbol and interval"""
    filename = symbol + "-{}-{}-{:02d}.zip".format(interval, year, month)
    file_destination_path = destination_base_dir + "/" + filename
    # create dir if not exists
    if not exists(destination_base_dir):
        os.makedirs(destination_base_dir)
    if exists(file_destination_path):
        print("Skip existing file:" + file_destination_path)
    else:
        file_url = monthly_base_url + symbol + "/" + interval + "/" + filename
        file_download_status_code = download_url(file_url, file_destination_path)
        if file_download_status_code == 200:
            # delete daily files if any
            delete_month_daily_files(file_destination_path, symbol, year, month, interval)
        if file_download_status_code == 404:
            # monthly data not yet ready, so download its daily data if not very old month
            days_in_month = calendar.monthrange(year, month)[1]
            delta = relativedelta.relativedelta(datetime.now(),
                                  datetime.combine(date(year, month, days_in_month), datetime.min.time()))
            day = 1
            while day <= days_in_month and delta.months <= 2 and delta.years == 0:
                download_daily_symbol_data(destination_base_dir, symbol, year, month, day, interval)
                day += 1


def download_daily_symbol_data(destination_base_dir, symbol, year, month, day, interval):
    """downloads into destination_dir the daily history data for the given symbol and interval"""
    filename = symbol + "-{}-{}-{:02d}-{:02d}.zip".format(interval, year, month, day)
    file_destination_path = destination_base_dir + "/" + filename
    #create dir if not exists
    if not exists(destination_base_dir):
        os.makedirs(destination_base_dir)
    if exists(file_destination_path):
        print("Skip existing file:" + file_destination_path)
    else:
        file_url = daily_base_url + symbol + "/" + interval + "/" + filename
        status = download_url(file_url, file_destination_path)


def download_url(url, save_path, chunk_size=1024):
    """downloads into destination_dir the file in the given url"""
    print(url)
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
    else:
        print("File not found:" + url)
    return r.status_code


def download_period_symbol_data(destination_dir, start_datetime, end_datetime, symbol, interval):
    """download symbol history data for the given period"""
    today = datetime.today()
    if end_datetime > today:
        end_datetime = today
    while start_datetime <= end_datetime:
        days_in_month = calendar.monthrange(start_datetime.year, start_datetime.month)[1]
        end_of_month_date = datetime(start_datetime.year, start_datetime.month, days_in_month)
        if end_of_month_date <= end_datetime:
            if start_datetime.day == 1:
                # download full month
                download_monthly_symbol_data(destination_dir, symbol, start_datetime.year, start_datetime.month, interval)
            else:
                # download daily data
                day = start_datetime.day
                while day <= days_in_month:
                    download_daily_symbol_data(destination_dir, symbol, start_datetime.year, start_datetime.month, day, interval)
                    day += 1
        else:
            day = start_datetime.day
            while day <= end_datetime.day:
                download_daily_symbol_data(destination_dir, symbol, start_datetime.year, start_datetime.month, day, interval)
                day += 1
        # start_date = 1st day of next month
        start_datetime = (start_datetime.replace(day=1) + timedelta(days=32)).replace(day=1)


def delete_month_daily_files(destination_dir, symbol, year, month, interval):
    daysInMonth = calendar.monthrange(year, month)[1]
    day = 1
    while day < daysInMonth:
        filename = symbol + "-{}-{}-{:02d}-{:02d}.zip".format(interval, year, month, day)
        file_destination_path = destination_dir + "/" + filename
        if exists(file_destination_path):
            os.remove(file_destination_path)
            print("removed daily file:", file_destination_path)
        day += 1

def unzip_file(file_path, destination_dir):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)
def unzip_all(data_dir):
    entries = os.listdir(data_dir)
    for entry in entries:
        if entry.endswith(".zip"):
            unzip_file(data_dir + '/' + entry, data_dir)

def load_csv(data_dir):
    try:
        connection = DBTools.get_connection()
        cursor = connection.cursor()
        entries = os.listdir(data_dir)
        for entry in entries:
            if entry.endswith(".csv"):
                load_csv_in_db(cursor, data_dir, entry)
                connection.commit()
    finally:
        cursor.close()
        DBTools.return_connection(connection)

def load_csv_in_db(cursor, data_dir, filename):
    filepath = os.path.join(data_dir, filename)
    # Extraire le nom du symbole et l'intervalle à partir du nom de fichier
    symbol, interval = filename.split('-')[:2]
    # Récupérer l'ID du symbole
    symbolId = cryptoutils.get_symbol_id(cursor, symbol)
    print('DB loading file :',filename)
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
            ignore INT
            );
        """)

    # Ouvrir le fichier CSV et créer un objet reader
    with open(filepath, 'r') as file:
        if '2017' in filename:
            cursor.copy_expert("COPY TMP (open_time,open_price,high_price,low_price,close_price,base_volume,close_time,quote_volume,number_trades,taker_buy_base,taker_buy_quote) FROM STDIN WITH csv", file)
        else:
            cursor.copy_expert(
                "COPY TMP (open_time,open_price,high_price,low_price,close_price,base_volume,close_time,quote_volume,number_trades,taker_buy_base,taker_buy_quote,ignore) FROM STDIN WITH csv",
                file)
    cursor.execute("""INSERT INTO CandleStickHistorical 
                                    (select to_timestamp(open_time/1000),{},open_price,high_price,low_price,
                                    close_price,base_volume,to_timestamp(close_time/1000),quote_volume,
                                    number_trades,taker_buy_base,taker_buy_quote from tmp)""".format(symbolId))


download_history_data()

unzip_all('data')
load_csv('data')