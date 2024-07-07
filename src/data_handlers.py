from pathlib import Path
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from copy import copy
from src.logger import Logger
from src.utils import exception_raiser
import pickle as pkl
import colorama
from colorama import Fore, Back, Style
from src.resulting_bracket import Bracket
from numpy import nan
import os
colorama.init(autoreset=True)

TEAMS_LIST_FILE_NAME = './data/state/teams_list.pkl'
TEAMS_LIST_DIR = Path(TEAMS_LIST_FILE_NAME).parents[0]

class BaseDataHandler:
    def __init__(self, 
                 file_name: Path|str=None, 
                 file_type: str='csv',
                 csv_sep: str=',',
                 log: Logger=Logger()):
        
        '''
        Valid file_type are 'csv', 'xls' and 'xlsx' 
        '''

        self.data_name = self.__class__.__name__
        self.file_name = copy(file_name)
        
        self.log = log
        self.log(f'Initializing {self.data_name}')

        if not file_name:
            raise Exception(exception_raiser(' Unspecified file for {self.data_name}'))

        file_path = Path(file_name)

        if not file_path.exists():
            raise Exception(exception_raiser(f' File {file_name} does not exist'))

        try:
            assert file_type.lower() == file_name.split('.')[-1].lower()
        except:
            self.log(f'Changing file extension from {file_type.lower()} to {file_name.split(".")[-1].lower()}')
            file_type = file_name.split('.')[-1].lower()

        self.file_type = file_type
        self.read_file = lambda x: pd.read_csv(x, sep=csv_sep) \
                    if file_type.lower() == 'csv' \
                    else lambda x: pd.read_excel(x, )
        
        self.write_file = lambda x: x.to_csv(self.file_name) \
            if self.file_type.lower() == 'csv' \
            else lambda x: x.to_excel(self.file_name)

        try:
            self.db = self.read_file(file_name, )
        except Exception as e:
            print(e)
            raise Exception(exception_raiser(f' Error reading file {file_name} using function pd.{self.read_file.__name__}'))

        csv_sep_str = 'tab' if csv_sep == '\t' else csv_sep
        assert not self.db.shape[1] == 1, exception_raiser(f'Wrong csv separator "{csv_sep_str}"')
        assert isinstance(self.db, pd.DataFrame), exception_raiser(f'Failed to create DataFrame')
        assert not self.db.empty, exception_raiser(f'File is empty')

        self.db.drop(['Unnamed: 0'], errors='ignore')
        self._preprocess_db()

        self.log(f'Successfully initialized {self.data_name}')

    def _preprocess_db(self):
        pass

class JurorsData(BaseDataHandler):
    def _preprocess_db(self):
        # Obtaining the list of jurors
        self.list_names = self.db['Juror'].to_list()
        self.chairpersons = self.db[self.db['Chairperson'] == 1]['Juror'].to_list()
        self.not_chairpersons = list(set(self.list_names) - set(self.chairpersons))
        
        self.db.set_index('Juror', inplace=True)
        
        self.db['Conflicts'] = self.db['Conflicts'].map(lambda x: x.split(', ') if not isinstance(x, float) else [])
        
        self.log(f'Processed conflicts: {self.db["Conflicts"].to_list()}')

        self.log(f'Jurors list:\n{self.list_names}\nChairpersons list:\n{self.chairpersons}')

    def _update_db_file(self, mode, updates):
        #updates is a dict for pandas or int representing the fight number
        juror_name, updates = updates
        
        source = self.read_file(self.file_name)
        source.set_index('Juror', inplace=True)

        if mode == 'add row':
            source.loc[juror_name] = updates
        elif mode == 'change presence':
            source.loc[juror_name, f'Fight_{updates}']
        self.write_file(source)

    def add_juror(self, juror_name: str, fight_num: int):
        self.log(f'Adding juror {juror_name} to database')

        is_chair = input('Can this juror be a chairperson?') in ('y', 'yes', 'Yes', '1', 'True')

        if juror_name in self.db.index:
            self.log(f'Juror {juror_name} is not new')
            self.db.loc[juror_name, f'Fight_{fight_num}'] = 1
            self._update_db_file('change presence')

        else:
            self.log(f'Juror {juror_name} is new')

            fights = [x for x in self.db.columns if x.startswith('Fight_')]

            info_dict = dict(zip(fights, [0]*len(fights)))
            info_dict[f'Fight_{fight_num}'] = 1
            info_dict['Conflicts'] = nan
            info_dict['Chairperson'] = int(is_chair)

            self.log(f'Information about {juror_name}: {info_dict}')
            self._update_db_file('add row', (juror_name, info_dict))
        
        
        self._reload_with_new_db()


    def _reload_with_new_db(self):
        self.log('Reloading...')

        self.log(f'Saving the suitable rooms')
        suitable_rooms = copy(self.db['Suitable_rooms'])        

        self.__init__(self.file_name, self.file_type, log=self.log)
        self.log('Adding suitable rooms to new db')
        self.db['Suitable_rooms'] = suitable_rooms
        self.log(f'Successfully reinitialized jurors database')
        
class FightData(BaseDataHandler):
    def _preprocess_db(self):
        # Extracting fight number from file name
        self.number = [s for s in self.file_name.split('/')[-1] if s.isdigit()][0]
        
        assert len(self.number) == 1, exception_raiser(f'Could not extract a valid fight number from {self.file_name}')
        
        self.number = int(self.number)

        # Detecting teams names
        self.teams_list = []
        self.rooms_list = []
        for i, row in self.db.iterrows():
            if row[0].startswith('Room/'):
                room_name = None
                continue
            if row[0].startswith('Room'):
                room_name = row[0]
                continue
            teams_detected = [x for x in row.tolist() if type(x)==str]
            room_info = (room_name, teams_detected, len(teams_detected))
            self.teams_list.extend(teams_detected)
            self.rooms_list.append(room_info)
        
        assert len(self.teams_list) == sum([x[2] for x in self.rooms_list]), exception_raiser(f'Check the input data, the teams in rooms are incorrectly detected')
        
        self.log(f'Detected teams:\n\t'+ "\n\t".join(self.teams_list))
        self.log(f'Rooms are:\n\t' + "\n\t".join([f'{x[0]}: {", ".join(x[1])} ({x[2]} teams)' for x in self.rooms_list]))
        
        # Save teams before 1st fight, else check integrity 
        if self.number == 1:
            TEAMS_LIST_DIR.mkdir(parents=True, exist_ok=True)
            with open(TEAMS_LIST_FILE_NAME, 'wb') as f:
                pkl.dump(self.teams_list, f)
        
        else:
            try:
                with open(TEAMS_LIST_FILE_NAME, 'rb') as f:
                    teams_saved = pkl.load(f)
            except:
                raise Exception(exception_raiser(' File {TEAMS_LIST_FILE_NAME} not found'))
            
        self.log(f'This is fight #{self.number}')

    def get_bracket(self, showmode: str='iynt'):
        self.log('Creating bracket...')
        bracket = Bracket(rooms_list=self.rooms_list, fight_num=self.number, showmode=showmode, log=self.log)
        return bracket
