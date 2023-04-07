import datetime
from datetime import datetime

import yaml
from yaml.loader import SafeLoader
from os.path import exists


class CryptoConfiguration:
    """
    Class used to store the symbols configuration
    """
    def __init__(self, name, symbol, interval, start_datetime, end_datetime='now', destination_dir='data'):
        self.name = name
        self.symbol = symbol
        self.interval = interval
        self.start_datetime = start_datetime
        if end_datetime == None:
            self.end_datetime = 'now'
        else:
            self.end_datetime = end_datetime
        self.destination_dir = destination_dir

def read_configuration(configuration_file):
    """
    load the configuration file
    :param configuration_file:
    :return: list of CryptoConfiguration
    """
    result = []
    if exists(configuration_file):
        with open(configuration_file) as f:
            configurations = yaml.load(f, Loader=SafeLoader)
            for configuration in configurations:
                name = list(configuration.keys())[0]
                content = configuration.get(name)
                interval = content.get('interval')
                symbol = content.get('symbol')
                start_date = content.get('history_start_date')
                zero_time = datetime.min.time()
                start_datetime = datetime.combine(start_date, zero_time).replace(tzinfo=None)
                end_date_str = content.get('history_end_date')
                if end_date_str == 'now':
                    end_datetime = datetime.now().replace(tzinfo=None)
                else:
                    end_datetime = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=None)
                result.append(CryptoConfiguration('', symbol, interval, start_datetime, end_datetime))
    else:
        raise Exception("Configuration file not found! " + configuration_file)
    return result
