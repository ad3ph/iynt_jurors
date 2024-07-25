from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)
from src.data_handlers import JurorsData, FightData
from src.meets_matrix import JurorJurorMeets, JurorTeamMeets, MeetsMatrix
from src.resulting_bracket import Bracket
from src.utils import clean_old_files, room_filling_sorter, exception_raiser
from src.logger import Logger
from random import sample
LOG = Logger(verbose=False)
from config.config import Settings
settings = Settings()

GET_FIGHT_DATA_PATH = 'data/fights/fight{}.csv'.format
JURORS_DATA_PATH = 'data/jurors.csv'

def create_bracket(fight_num: int):
    jurors = JurorsData(JURORS_DATA_PATH, file_type='csv', log=LOG)
    fight = FightData(GET_FIGHT_DATA_PATH(fight_num), file_type='csv', log=LOG)
    bracket = fight.get_bracket(showmode=settings.mode)
    jj_meets = JurorJurorMeets(jurors.list_names, fight.teams_list, fight.number, log=LOG, create_new=(fight_num == 1))
    jt_meets = JurorTeamMeets(jurors.list_names, fight.teams_list, fight.number, log=LOG, create_new=(fight_num == 1))

    jurors.db['Suitable_rooms'] = 0
    modes = {'chairpersons': jurors.chairpersons, 'other jurors': jurors.not_chairpersons}

    rooms_filling = dict(zip([x[0] for x in fight.rooms_list], [0]*len(fight.rooms_list)))
    
    for commentary, jurors_list in modes.items():
        jurors_list = sample(jurors_list, len(jurors_list)) # Randomizing jurors order
        LOG(f'{commentary.capitalize()}: {", ".join(jurors_list)}')
        LOG(f'Assigning {commentary}...')
        
        assert len(jurors_list) >= len(fight.rooms_list), exception_raiser('Not enough chairpersons for rooms')

        for juror_name in jurors_list:
            if not jurors.db.loc[juror_name, f'Fight_{fight.number}']:
                LOG(f'{juror_name} does not participate in fight {fight.number}')
                continue

            teams_met = jt_meets.get_meets(juror_name)

            suitable_rooms = []
            for room_name, teams_in_room, num_teams in fight.rooms_list:
                if not set(jurors.db.loc[juror_name, 'Conflicts']).isdisjoint(teams_in_room):
                    continue
                suitable_rooms.append(room_name)

            jurors.db['Suitable_rooms'][juror_name] = \
                [(room, MeetsMatrix.sorter(room, teams_met, fight.rooms_list, obj_idx=1, log=LOG)) for room in suitable_rooms]
            
            jurors.db['Suitable_rooms'][juror_name] = sorted(jurors.db['Suitable_rooms'][juror_name], key=lambda x: x[1])

        jurors_priority = []
        for juror_name in jurors_list:
            if not jurors.db.loc[juror_name, f'Fight_{fight.number}']:
                continue
            best_rooms = [room[0] for room in jurors.db['Suitable_rooms'][juror_name] if room[1] <= jurors.db['Suitable_rooms'][juror_name][0][1]+5]
            jurors_priority.append((juror_name, best_rooms))

        jurors_priority = sorted(jurors_priority, key=lambda x: len(x[1]))

        for juror_name, best_rooms in jurors_priority:
            if not jurors.db.loc[juror_name, f'Fight_{fight.number}']:
                continue
            LOG(f'Suitable for {juror_name} are {jurors.db["Suitable_rooms"][juror_name]}')
            LOG(f'Best rooms for {juror_name} are {best_rooms}')

            jurors_met = jj_meets.get_meets(juror_name)

            best_rooms = sorted(best_rooms, \
                key=lambda x: MeetsMatrix.sorter(x, jurors_met, bracket.rooms_list, obj_idx=3, importance=0.75, log=LOG, verbose=False) + room_filling_sorter(x, rooms_filling, log=LOG, verbose=False))
            if len(best_rooms):
                bracket.add_juror_to_room(juror_name, best_rooms[0])
                rooms_filling[best_rooms[0]] += 1
    
    bracket.show()
    
    editing = input('Make corrections? ') in ('Yes', 'yes', 'y', 'Y', 'da', 'True', '1') 
    while editing:
        command = input('Command to edit (possible: move, delete, add, q to finish editing): ')
        juror_to_edit = ''
        room_from = 0
        room_to = 0
        if command != 'q':
            juror_to_edit = input('Juror (either index in list or name if command = add): ')
            juror_to_edit = int(juror_to_edit) if juror_to_edit.isnumeric() else juror_to_edit
            
            try:
                room_from = int(input('Room from - index (starting at 0): '))
            except:
                print('Bad input, only digits accepted')
                room_from = int(input('Room from - index (starting at 0): '))
            
            try:
                room_to = int(input('Room to - index (starting at 0): '))
            except:
                print('Bad input, only digits accepted')
                room_to = int(input('Room to - index (starting at 0): '))
        
        editing = bracket.edit(command,
                               juror_to_edit,
                               room_from,
                               room_to,
                               jurors)

        bracket.show()
    
    bracket.save()

def update_meets_matrices(fight_num):
    # Fight #{fight_num} just passed
    used_bracket = Bracket.from_file(fight_num, log=LOG, showmode=settings.mode)
    all_jurors = used_bracket.get_all_jurors()

    jj_meets = JurorJurorMeets.from_file(fight_num, log=LOG)
    jt_meets = JurorTeamMeets.from_file(fight_num, log=LOG)
    
    jj_meets.update_jurors_list(all_jurors)
    jt_meets.update_jurors_list(all_jurors)

    jj_meets.update(used_bracket.rooms_list)
    jt_meets.update(used_bracket.rooms_list)

    jj_meets.save_state()
    jt_meets.save_state()
    
    LOG('Done updating matrices')
    

def run_by_request(mode, fight_num):
    LOG(f"Launch options: {['creating bracket', 'updating matrices'][mode]}, fight #{fight_num}")

    if mode == 0:
        if fight_num == 1:
            clean_old_files()
        create_bracket(fight_num)

    if mode == 1:
        update_meets_matrices(fight_num)
    
    settings.last_state_file.write_text(f'{["creating bracket", "updating matrices"][mode]}, {fight_num}')
    LOG.to_file()
    #print(LOG)


if __name__ == '__main__':
    mode = int(input('0: You are going to create a bracket before fight, 1: you are going to update meets matrices after fight: '))
    fight_num = input('Fight number before/after which you are working now: ')

    assert mode in (0, 1), exception_raiser('Bad mode, only 0 and 1 are available')

    try:
        fight_num = int(fight_num)
    except:
        raise Exception(f'Bad fight_num, please use only fight number')

    run_by_request(mode, fight_num)

