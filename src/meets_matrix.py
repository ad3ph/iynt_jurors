import pickle as pkl
import pandas as pd
import colorama
from colorama import Fore, Back, Style

from src.logger import Logger
from .logger import Logger
colorama.init(autoreset=True)

JJ_STATE_FILE_NAME = './data/state/jj_meets_state.pkl'
JT_STATE_FILE_NAME = './data/state/jt_meets_state.pkl'
JURORS_MEETS_IMPORTANCE = 0.1

class MeetsMatrix:
    def __init__(self,
                 jurors: list,
                 teams: list,
                 fight_number: int,
                 log: Logger,
                 create_new: bool=False,
                 ):
        self.log = log
        self.fight_number = fight_number
        
        if self.fight_number == 1 and create_new:
            self.jurors = jurors
            self.teams = teams
            self._construct_zero_matrix()
            self.save_state()

        else:
            self._load_state()

        self.log(f'Successfully initialised {self.__class__.__name__}')

    def _construct_zero_matrix():
        pass

    def get_meets(self, juror_name: str):
        assert juror_name in self.jurors, f'{juror_name} not found in jurors list'
        return self.matrix.loc[juror_name]

    def _set_state_file_name(self):
        self.STATE_FILE_NAME = None

    def _load_state(self):
        self._set_state_file_name()
        try:
            with open(self.STATE_FILE_NAME, 'rb') as f:
                self.old_dict_ = pkl.load(f)
        except:
            raise Exception(Back.RED + '[ERROR]' + Style.RESET_ALL + f' Error reading {self.STATE_FILE_NAME}')
        
        self.teams = self.old_dict_['teams']
        self.jurors = self.old_dict_['jurors']
        self.matrix = self.old_dict_['matrix']

    def save_state(self):
        self._set_state_file_name()
        with open(self.STATE_FILE_NAME, 'wb') as f:
            pkl.dump(self.__dict__, f)

    def update_jurors_list(self, new_list_of_jurors):
        self.log(f'Received new list of juror, checking for updates\n{", ".join(new_list_of_jurors)}')
        if self.jurors == new_list_of_jurors:
            self.log('No changes')
            return
        self.log('Changes found')
        for juror in (set(new_list_of_jurors) - set(self.jurors)):
            if juror not in self.jurors \
                and ((juror not in self.matrix.columns) or (juror not in self.matrix.index)):
                self.jurors.append(juror)
                self.matrix.loc[juror] = [0] * self.matrix.shape[1]
                if self.matrix.columns.intersection(self.teams).tolist() == []:
                    self.matrix[juror] = [0] * self.matrix.shape[0]

    @staticmethod
    def sorter(room_name: str, objects_met, rooms_list, obj_idx, importance=1, log=None, verbose=False):
        '''
        Key function for sorted. 
        Checks how many times in total the juror have seen the objects in this room.
        Pays enormous attention to large numbers by using cubic loss function: 
            1 1 1 meets in room gives output 3,
            2 1 0 meets in room gives output 9,
            3 0 0 meets in room gives 27

        OBJECTS ARE TEAMS OR JURORS
        '''

        try:
            assert room_name in [room[0] for room in rooms_list], f'Sorter got unexpected room name {room_name}'
        except AssertionError as e:
            raise Exception(Back.RED + '[ERROR]' + Style.RESET_ALL + f' {e}')      
        objects_in_room = [room[obj_idx] for room in rooms_list if room[0] == room_name][0]

        weight = importance * sum([objects_met[team]**3 for team in objects_in_room])
        if verbose and log:
            log(f'{weight} sorter returned for room {room_name}')
        return weight
        

class JurorJurorMeets(MeetsMatrix):
    def _set_state_file_name(self):
        self.STATE_FILE_NAME = JJ_STATE_FILE_NAME

    def _construct_zero_matrix(self):
        self.matrix = pd.DataFrame(0, index=self.jurors, columns=self.jurors)
    
    @staticmethod
    def from_file(fight_num, log: Logger=Logger()):
        meets = JurorJurorMeets(jurors=[], teams=[], fight_number=fight_num, log=log)
        with open(JJ_STATE_FILE_NAME, 'rb') as f:
            old_dict = pkl.load(f)
        meets.matrix = old_dict['matrix']
 
        log(f'JJ meets:\n{meets.matrix}')
        return meets

    def update(self, rooms_list):
        # Each element of rooms_list is 
        # (room_name: str, 
        #   teams_list: list[str], 
        #   num_teams: int=len(teams_list), 
        #   jurors_list: list[str])
        for room_name, teams_in_room, _, jurors_in_room in rooms_list:
            for juror in jurors_in_room:
                self.matrix[juror][jurors_in_room] += 1
                self.log(f'Juror {juror} has meets with {", ".join(jurors_in_room)}')
        self.log(f'New matrix state:\n{self.matrix}')


class JurorTeamMeets(MeetsMatrix):
    def _set_state_file_name(self):
        self.STATE_FILE_NAME = JT_STATE_FILE_NAME
    
    def _construct_zero_matrix(self):
        self.matrix = pd.DataFrame(0, index=self.jurors, columns=self.teams)
    
    @staticmethod
    def from_file(fight_num, log: Logger=Logger()):
        meets = JurorTeamMeets(jurors=[], teams=[], fight_number=fight_num, log=log) 
        with open(JT_STATE_FILE_NAME, 'rb') as f:
            old_dict = pkl.load(f)
        meets.matrix = old_dict['matrix']
        log(f'JT meets:\n{meets.matrix}')
        return meets

    def update(self, rooms_list):
        # Each element of rooms_list is 
        # (room_name: str, 
        #   teams_list: list[str], 
        #   num_teams: int=len(teams_list), 
        #   jurors_list: list[str])
        for room_name, teams_in_room, _, jurors_in_room in rooms_list:
            for team in teams_in_room:
                self.matrix[team][jurors_in_room] += 1
                self.log(f'Team {team} has meets with {", ".join(jurors_in_room)}')
        self.log(f'New matrix state:\n{self.matrix}')
