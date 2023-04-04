import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import requests
import yaml
from yaml.loader import SafeLoader
from os.path import exists
import os
import calendar
from threading import Thread

klines_baseurl = 'https://data.binance.vision/data/spot/{}/klines/'
daily_base_url = klines_baseurl.format('daily')
monthly_base_url = klines_baseurl.format('monthly')
destination_data_dir = 'data'


def read_configuration(configuration_file):
    if exists(configuration_file):
        with open(configuration_file) as f:
            return yaml.load(f, Loader=SafeLoader)
    else:
        raise Exception("Configuration file not found! " + configuration_file)


def download_history_data(configuration_file, destination_data_dir):
    yaml_content = read_configuration(configuration_file)
    threads = []
    for configuration in yaml_content.get('Configurations'):
        interval = configuration.get('Interval')
        pair = configuration.get('Pair')
        start_date = configuration.get('HistoryStartDate')
        end_date = configuration.get('HistoryEndDate')
        if end_date == 'yesterday':
            end_date = date.today() - timedelta(days=1)
        thread = Thread(target=download_period_pair_data,
                        args=(destination_data_dir, (start_date, end_date), pair, interval))
        thread.start()
    # wait the end of all threads
    for thread in threads:
        thread.join()


def download_monthly_pair_data(destination_base_dir, pair, year, month, interval):
    """downloads into destination_dir the monthly history data for the given pair and interval"""
    filename = pair + "-{}-{}-{:02d}.zip".format(interval, year, month)
    destination_dir = destination_base_dir + "/" + pair
    file_destination_path = destination_dir + "/" + filename
    # create dir if not exists
    if not exists(destination_dir):
        os.makedirs(destination_dir)
    if exists(file_destination_path):
        print("Skip existing file:" + file_destination_path)
    else:
        file_url = monthly_base_url + pair + "/" + interval + "/" + filename
        file_download_status_code = download_url(file_url, file_destination_path)
        if file_download_status_code == 200:
            # delete daily files if any
            delete_month_daily_files(file_destination_path, pair, year, month, interval)
        if file_download_status_code == 404:
            # monthly data not yet ready, so download its daily data if not very old month
            days_in_month = calendar.monthrange(year, month)[1]
            delta = relativedelta.relativedelta(datetime.now(),
                                  datetime.combine(date(year, month, days_in_month), datetime.min.time()))
            day = 1
            while day <= days_in_month and delta.months <= 2 and delta.years == 0:
                download_daily_pair_data(destination_base_dir, pair, year, month, day, interval)
                day += 1


def download_daily_pair_data(destination_base_dir, pair, year, month, day, interval):
    """downloads into destination_dir the daily history data for the given pair and interval"""
    filename = pair + "-{}-{}-{:02d}-{:02d}.zip".format(interval, year, month, day)
    destination_dir = destination_base_dir+"/"+pair
    file_destination_path = destination_dir + "/" + filename
    #create dir if not exists
    if not exists(destination_dir):
        os.makedirs(destination_dir)
    if exists(file_destination_path):
        print("Skip existing file:" + file_destination_path)
    else:
        file_url = daily_base_url + pair + "/" + interval + "/" + filename
        download_url(file_url, file_destination_path)


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


def download_period_pair_data(destination_dir, period, pair, interval):
    """download pair history data for the given period"""
    today = date.today()
    start_date = period[0]
    end_date = period[1]
    if end_date > today:
        end_date = today
    while start_date <= end_date:
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        end_of_month_date = date(start_date.year, start_date.month, days_in_month)
        if end_of_month_date <= end_date:
            if start_date.day == 1:
                # download full month
                download_monthly_pair_data(destination_dir, pair, start_date.year, start_date.month, interval)
            else:
                # download daily data
                day = start_date.day
                while day <= days_in_month:
                    download_daily_pair_data(destination_dir, pair, start_date.year, start_date.month, day, interval)
                    day += 1
        else:
            day = start_date.day
            while day <= end_date.day:
                download_daily_pair_data(destination_dir, pair, start_date.year, start_date.month, day, interval)
                day += 1
        # start_date = 1st day of next month
        start_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1)


def delete_month_daily_files(destination_dir, pair, year, month, interval):
    daysInMonth = calendar.monthrange(year, month)[1]
    day = 1
    while day < daysInMonth:
        filename = pair + "-{}-{}-{:02d}-{:02d}.zip".format(interval, year, month, day)
        file_destination_path = destination_dir + "/" + filename
        if exists(file_destination_path):
            os.remove(file_destination_path)
            print("removed daily file:", file_destination_path)
        day += 1


download_history_data('config.yml', destination_data_dir)
