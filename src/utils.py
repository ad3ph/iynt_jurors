import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)
import os
from glob import glob
from config.config import Settings
settings = Settings()

def clean_old_files():
    to_rm = glob('./data/state/*') + \
        glob('./output/fight?.html') + \
            ['./output/log.txt'] + \
                glob('./output/*.csv') + \
                    glob('./output/*.png')
    for file in to_rm:
        if os.path.exists(file):
            os.remove(file)

def exception_raiser(text: str) -> str:
    raise Exception(Back.RED + '[ERROR]' + Style.RESET_ALL + f' {text}')

def room_filling_sorter(room_name, room_filling_dict, importance=1, log=None, verbose=False):
    ans = importance * room_filling_dict.get(room_name, 0)
    if verbose and log:
        log(f'{ans} room filling sorter returned for room {room_name}')
    return ans

def get_last_state():
    try:
        with open(settings.last_state_file, 'r') as f:
            last_mode, last_fight_num = f.read().split(", ")
        return last_mode, last_fight_num
    except:
        return 'unknown', 'unknown'
