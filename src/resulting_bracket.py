import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)
from copy import deepcopy
import pickle as pkl
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .logger import Logger
from .utils import exception_raiser
import os
from pathlib import Path

GET_SAVE_STATE_PATH = './data/state/bracket_fight_{}.pkl'.format
TEMPLATE_PATH = './templates'
HTML_OUTPUT_PATH = './output'
Path(HTML_OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

class Bracket:
    '''
    Class to save and edit the results in convenient way
    '''
    def __init__(self, rooms_list: list, fight_num: int, showmode: str, log):
        self.log = log
        self.fight_num = fight_num 
        self.showmode = showmode

        self.rooms_list = [(*room, []) for room in rooms_list]
        # Each element of list is 
        # (room_name: str, 
        #   teams_list: list[str], 
        #   num_teams: int=len(teams_list), 
        #   jurors_list: list[str])

        self.ACTIONS = {
            # x = (juror_index_or_name, room_from_index, room_to_index)
            'move': (lambda x: self.rooms_list[x[2]][3].append(self.rooms_list[x[1]][3].pop(x[0]))),
            'delete': (lambda x: self.rooms_list[x[1]][3].pop(x[0])),
            'add': (lambda x: self.rooms_list[x[2]][3].append(x[0]))
        }

        self.log(f'Bracket for {len(rooms_list)} rooms successfully created')

    @staticmethod
    def from_file(fight_num: int, log: Logger=Logger(), showmode='iynt'):
        bracket = Bracket([], fight_num, showmode, log)
        
        with open(GET_SAVE_STATE_PATH(fight_num), 'rb') as f:
            state_dict = pkl.load(f)
        assert state_dict.get(fight_num), f'Fight #{fight_num} not found in file {GET_SAVE_STATE_PATH(fight_num)}'
        bracket.rooms_list = state_dict.get(fight_num)
        log(f'Loaded file {GET_SAVE_STATE_PATH(fight_num)}, this is the bracket:\n{bracket.rooms_list}')
        return bracket
        
        
    def get_all_jurors(self):
        all_jurors = []
        for room in self.rooms_list:
            all_jurors.extend(room[3])
        return all_jurors

    def add_juror_to_room(self, juror_name: str, room_name: str):
        [room[3].append(juror_name) for room in self.rooms_list if room[0] == room_name]
        self.log(f'Added juror {juror_name} to room {room_name}')

    def show(self):
        max_teams = 4 if self.showmode.lower() == 'iypt' else 3
        print(Fore.GREEN + Style.BRIGHT + f'Jurors bracket for fight #{self.fight_num}' + Fore.RESET, end='')
        
        #rooms_list_printable is a list for string-by-string table printing
        self.rooms_list_printable = []
        max_jurors = 0

        self.rooms_list_printable = deepcopy([[x[i] for x in deepcopy(self.rooms_list)] for i in range(len(deepcopy(self.rooms_list[0])))])

        [x.append('') for x in self.rooms_list_printable[1] if len(x) < max_teams]
        teams_list = self.rooms_list_printable.pop(1)
        [self.rooms_list_printable.insert(1, [x[i] for x in teams_list]) for i in range(max_teams)]
        self.rooms_list_printable[1:max_teams + 1] = self.rooms_list_printable[max_teams:0:-1]

    
        jur_idx = max_teams + 2
        max_jurors = max([len(a) for a in self.rooms_list_printable[jur_idx]]) + 1
        for x in self.rooms_list_printable[jur_idx]:
            while len(x) <= max_jurors:
                x.append('')
        jurors_list = self.rooms_list_printable.pop(jur_idx)
        [self.rooms_list_printable.insert(jur_idx, [x[i] for x in jurors_list]) for i in range(max_jurors)]
        self.rooms_list_printable[jur_idx:] = self.rooms_list_printable[-1:jur_idx-1:-1]
        self.rooms_list_printable.pop(jur_idx-1)

        self.rooms_list_printable = self.rooms_list_printable
        max_str_lens = [max([len(y) for y in jurors_list[i]] + [len(y) for y in teams_list[i]] ) for i in range(len(jurors_list))] 

        for i, info_per_room in enumerate(self.rooms_list_printable):
            print(Style.BRIGHT + '\n|', end='')
            for room_idx, room_info in enumerate(info_per_room):
                if i in (0, max_teams + 1):
                    print(Style.BRIGHT + f' {room_info.ljust(max_str_lens[room_idx]) } ', end='|')
                else:
                    print(f' {room_info.ljust(max_str_lens[room_idx])} ' ,end='|')
        print('\n')

    def _save_to_html(self):
        env = Environment(
            loader=FileSystemLoader(TEMPLATE_PATH),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('result.html')

        max_jurors = max(len(x[3]) for x in self.rooms_list)

        items = [dict(zip(['room_name', 'teams', 'chair', 'jurors'], \
                          [x[0], x[1], f"1. {x[3][0]}", [f"{i}. {a}" for i, a in enumerate(x[3][1:], start=2)]])) \
                            for x in deepcopy(self.rooms_list)]

        rendered_page = template.render(items=items, max_jurors=max_jurors, fight_num=self.fight_num)

        with open(f'./output/fight{self.fight_num}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)

    def save(self):
        self.log('Saving the bracket...')
        save_path = GET_SAVE_STATE_PATH(self.fight_num)
        with open(save_path, 'wb') as f:
            pkl.dump({self.fight_num: self.rooms_list}, f)
        self.log('Pkl saved')
        self._save_to_html()
        self.log('HTML saved')

    def _chairpersons_to_top(self, chairpersons: list):
        for i, room in enumerate(self.rooms_list):
            room = list(room)
            room[3] = sorted(room[3], key=lambda x: x in chairpersons, reverse=True)
            self.rooms_list[i] = tuple(room)

    def edit(self, command: str, 
             juror: str|int, 
             room_from_index: str='', 
             room_to_index: str='',
             jurors_db=None):
        
        command = command.lower()

        try:
            assert command in ('move', 'delete', '', 'add', 'q')
        except:
            print(Back.RED + '[ERROR]' + Style.RESET_ALL + f' Command {command} not recognized')
            return True
        
        if command == '':
            return 0
        if command == 'q':
            return 0
        
        if command == 'add':
            assert isinstance(juror, str), exception_raiser('Not a str value passed to add')
            jurors_db.add_juror(juror, self.fight_num)

        try:
            self.ACTIONS[command]((juror, room_from_index, room_to_index))
            self.log(f'Performed action {command.upper()} in room {room_from_index} to the room {room_to_index} with juror {juror}')
        except Exception as e:
            raise Exception(exception_raiser(f'{e}'))
        
        self._chairpersons_to_top(jurors_db.chairpersons)
        return True
