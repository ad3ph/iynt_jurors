import colorama
from colorama import Fore, Back, Style
from datetime import datetime
get_timestamp = datetime.now
colorama.init(autoreset=True)
from time import sleep

from src.utils import exception_raiser

class Logger:
    def __init__(self, verbose: bool=False, output_file='./output/log.txt'):
        self.storage = []
        self.verbose = verbose
        self.output_file = output_file
    
    def __call__(self, data):
        if self.verbose:
            print(data)
        try:
            data_to_store = str(data)
        except:
            try:
                data_to_store = repr(data)
            except Exception as e:
                print(e)
                raise Exception(exception_raiser('Unable to use logger here'))
        data_to_store = (f'[{get_timestamp().strftime("%H:%M:%S.%f")[:-3]}]', data_to_store)
        self.storage.append(data_to_store)
            
    def __repr__(self) -> str:
        print('____ Begin of logger output ____')
        for timestamp, data in self.storage:
            print(Style.DIM + timestamp + Style.RESET_ALL + " " + data)
        return '_____ End of logger output _____'

    def to_file(self):
        with open(self.output_file, 'a') as f:
            f.write('New launch')

        with open(self.output_file, 'a') as f:
            for timestamp, data in self.storage:
                f.write(timestamp + " " + str(data) if str(data) else repr(data))
                f.write('\n')
