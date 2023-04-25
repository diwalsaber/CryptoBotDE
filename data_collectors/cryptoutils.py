import datetime
from datetime import datetime
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
        self.pairs_conf = []
        self.db_conf = None

        if exists(configuration_file):
            with open(configuration_file) as f:
                configuration = yaml.load(f, Loader=SafeLoader)
                self.db_conf = DataBaseConfiguration(configuration.get('Database').get('instance_name'),
                                                configuration.get('Database').get('host'),
                                                configuration.get('Database').get('port'),
                                                configuration.get('Database').get('username'),
                                                configuration.get('Database').get('password'))
                for configuration in configuration.get('Pairs'):
                    name = list(configuration.keys())[0]
                    content = configuration.get(name)
                    interval = content.get('interval')
                    symbol = content.get('symbol')
                    description = content.get('description')
                    start_date = content.get('history_start_date')
                    zero_time = datetime.min.time()
                    start_datetime = datetime.combine(start_date, zero_time).replace(tzinfo=None)
                    end_date_str = content.get('history_end_date')
                    if end_date_str == 'now':
                        end_datetime = datetime.now().replace(tzinfo=None)
                    else:
                        end_datetime = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=None)
                    self.pairs_conf.append(
                        CryptoConfiguration('', symbol, interval, description, start_datetime, end_datetime))
        else:
            raise Exception("Configuration file not found! " + configuration_file)
    @staticmethod
    def get_instance():
        return Configuration()

class DBTools(metaclass=Singleton):
    def __init__(self):
        self.db_config = Configuration().db_conf
        self.postgreSQL_pool = pool.SimpleConnectionPool(1, 5, user=self.db_config.username,
                                                             password=self.db_config.password,
                                                             host=self.db_config.host,
                                                             port="{}".format(self.db_config.port),
                                                             database=self.db_config.instance_name)
    @staticmethod
    def get_connection():
        return DBTools().postgreSQL_pool.getconn()

    @staticmethod
    def return_connection(connection):
        if connection != None:
            DBTools().postgreSQL_pool.putconn(connection)

    @staticmethod
    def close_all():
        DBTools().close_all()
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


def get_symbol_id(cursor, symbol):
    query = "select symbolid from Symbol where name ='{}'".format(symbol)
    cursor.execute(query)
    record = cursor.fetchone()
    return record[0]

conf1 = Configuration()
Configuration()