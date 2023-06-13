import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta

import psycopg2
from dateutil import relativedelta
import requests
from os.path import exists
import os
import calendar
from threading import Thread
import zipfile

from cryptobot.common.DBUtils import is_loaded_csv, add_loaded_csv, create_tmp_table
from cryptobot.common import cryptoutils, DBUtils
from cryptobot.common.cryptoutils import DBConnector, Configuration

klines_baseurl = 'https://data.binance.vision/data/spot/{}/klines/'
daily_base_url = klines_baseurl.format('daily')
monthly_base_url = klines_baseurl.format('monthly')

def download_history_data():
    """
        Start downloading the klines history data configured in the configuration_file using the zip files
        :return:
        """
    threads = []
    for pair_conf in DBUtils.get_history_configs():
        thread = Thread(target=download_period_symbol_data,
                        args=(pair_conf['dir'], pair_conf['startdate'], datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days = 1),
                              pair_conf['symbol'], pair_conf['interval']))
        threads.append(thread)
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
    print(f'downloading {url}')
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(save_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)
        else:
            print(f"File not found: {url}")
        return r.status_code
    except Exception as e:
        print(f'Error dowloading {url}:',e)


def download_period_symbol_data(destination_dir:str, start_datetime:datetime, end_datetime:datetime, symbol:str, interval:str):
    """download symbol history data for the given period"""
    today:datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if end_datetime > today :
        end_datetime = today
    if not exists(destination_dir):
        os.makedirs(destination_dir)
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
    print(f'unzip {file_path} into {destination_dir}')
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)
def unzip_all(symbol:str=None, interval:str=None):
    if symbol and interval:
        conf = DBUtils.get_history_config_by_symbol(symbol, interval)
        if conf:
            unzip_files_in_dir(conf['dir'], symbol, interval)
    else:
        for conf in DBUtils.get_history_configs():
            unzip_files_in_dir(conf['dir'], conf['symbol'], conf['interval'])
def unzip_files_in_dir(data_dir, symbol:str=None, interval:str=None):
    entries = os.listdir(data_dir)
    for entry in entries:
        if entry.endswith(".zip"):
            prefix = symbol
            if interval and symbol:
                prefix += '-'+interval
            if prefix:
                if entry.startswith(prefix):
                    unzip_file(data_dir + '/' + entry, data_dir)
            else:
                unzip_file(data_dir + '/' + entry, data_dir)

def load_csv(symbol:str=None, interval:str=None):
    if symbol and interval:
        conf = DBUtils.get_history_config_by_symbol(symbol, interval)
        load_all_csv_in_dir(conf['dir'], symbol, interval)
    else:
        for conf in DBUtils.get_history_configs():
            load_all_csv_in_dir(conf['dir'], conf['symbol'], conf['interval'])
    for conf in DBUtils.get_history_configs():
        load_all_csv_in_dir(conf['dir'])
def load_all_csv_in_dir(data_dir,symbol:str=None, interval:str=None):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        entries = os.listdir(data_dir)
        for entry in entries:
            if entry.endswith(".csv") and not is_loaded_csv(entry):
                prefix = symbol
                if interval and symbol:
                    prefix += '-' + interval
                if prefix:
                    if entry.startswith(prefix):
                        load_csv_in_db(cursor, data_dir, entry)
                        add_loaded_csv(entry)
                else:
                    load_csv_in_db(cursor, data_dir, entry)
                    add_loaded_csv(entry)

                connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cursor.close()
        DBConnector.return_data_db_connection(connection)

def load_csv_in_db(cursor, data_dir, filename):
    filepath = os.path.join(data_dir, filename)
    # Extraire le nom du symbole et l'intervalle à partir du nom de fichier
    symbol, interval = filename.split('-')[:2]
    # Récupérer l'ID du symbole
    symbolId = cryptoutils.get_symbol_id(symbol)
    print('DB loading file :',filename)
    table_name = 'tmp_2'
    create_tmp_table(table_name)

    # Ouvrir le fichier CSV et créer un objet reader
    with open(filepath, 'r') as file:
        cursor.copy_expert(f"""COPY {table_name} (open_time,open_price,high_price,low_price,close_price,base_volume,close_time,
                quote_volume,number_trades,taker_buy_base,taker_buy_quote,ignore) FROM STDIN WITH csv"""
                ,file)
    cursor.execute(f"""INSERT INTO CandleStickHistorical 
                                    (select to_timestamp(open_time/1000),{symbolId},open_price,high_price,low_price,
                                    close_price,base_volume,to_timestamp(close_time/1000),quote_volume,
                                    number_trades,taker_buy_base,taker_buy_quote from {table_name} ) ON CONFLICT DO NOTHING """)
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
