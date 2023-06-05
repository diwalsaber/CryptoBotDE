import datetime
import json
from datetime import datetime

import psycopg2
from psycopg2 import pool
import yaml
from yaml.loader import SafeLoader
from os.path import exists

configuration_file = 'config.yml'
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Configuration(metaclass=Singleton):
    def __init__(self):
        self.data_db_conf = None
        self.app_db_conf = None
        if exists(configuration_file):
            with open(configuration_file) as f:
                configuration = yaml.load(f, Loader=SafeLoader)
                self.data_db_conf = DataBaseConfiguration(configuration.get('DataDatabase').get('instance_name'),
                                                configuration.get('DataDatabase').get('host'),
                                                configuration.get('DataDatabase').get('port'),
                                                configuration.get('DataDatabase').get('username'),
                                                configuration.get('DataDatabase').get('password'))
                self.app_db_conf = DataBaseConfiguration(configuration.get('AppDatabase').get('instance_name'),
                                                          configuration.get('AppDatabase').get('host'),
                                                          configuration.get('AppDatabase').get('port'),
                                                          configuration.get('AppDatabase').get('username'),
                                                          configuration.get('AppDatabase').get('password'))

        else:
            raise Exception("Configuration file not found! " + configuration_file)
    @staticmethod
    def get_instance():
        return Configuration()


class DBConnector(metaclass=Singleton):
    def __init__(self):
        self.data_db_config = Configuration.get_instance().data_db_conf
        self.app_db_config = Configuration.get_instance().app_db_conf
        self.data_db_connection_pool = pool.SimpleConnectionPool(1, 5, user=self.data_db_config.username,
                                                                 password=self.data_db_config.password,
                                                                 host=self.data_db_config.host,
                                                                 port=f"{self.data_db_config.port}",
                                                                 database=self.data_db_config.instance_name)
        self.app_db_connection_pool = pool.SimpleConnectionPool(1, 5, user=self.app_db_config.username,
                                                                 password=self.app_db_config.password,
                                                                 host=self.app_db_config.host,
                                                                 port=f"{self.app_db_config.port}",
                                                                 database=self.app_db_config.instance_name)


    @staticmethod
    def get_data_instance_name():
        return DBConnector().data_db_config.instance_name


    @staticmethod
    def get_app_instance_name():
        return DBConnector().app_db_config.instance_name
    @staticmethod
    def get_data_db_connection():
        return DBConnector().data_db_connection_pool.getconn()

    @staticmethod
    def return_data_db_connection(connection):
        if connection:
            DBConnector().data_db_connection_pool.putconn(connection)


    @staticmethod
    def get_app_db_connection():
        return DBConnector().app_db_connection_pool.getconn()

    @staticmethod
    def return_app_db_connection(connection):
        if connection:
            DBConnector().app_db_connection_pool.putconn(connection)



class DataBaseConfiguration:
    def __init__(self, instance_name, host, port, username, password):
        self.instance_name = instance_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class CryptoConfiguration:
    """
    Class used to store the symbols configuration
    """

    def __init__(self, name, symbol, interval, description, start_datetime, end_datetime='now', destination_dir='data'):
        self.name = name
        self.symbol = symbol
        self.interval = interval
        self.start_datetime = start_datetime
        self.description = description
        if end_datetime == None:
            self.end_datetime = 'now'
        else:
            self.end_datetime = end_datetime
        self.destination_dir = destination_dir


def get_symbol_id(symbol):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        query = f"select symbolid from Symbol where name ='{symbol}'"
        cursor.execute(query)
        record = cursor.fetchone()
        id = record[0]
        cursor.close()
        connection.commit()
        return id
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBConnector.return_data_db_connection(connection)


