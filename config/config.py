from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    output_folder: str|Path = Path("./output")
    fights_folder: str|Path = Path("./data/fights")
    jurors_file: str|Path = Path("./data/jurors.csv")
    state_folder: str|Path = Path("./data/state")
    last_state_file: str|Path = Path("./data/state/last_state.txt")
    
    mode = 'iypt' # may be iynt or iypt. This affects the table printing
