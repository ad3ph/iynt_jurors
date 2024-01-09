# The jury scheduling tool for YPT and YNT

# Table of contents
- [Setting up](#setting-up)
  - [As a python module](#as-a-python-module)
  - [In docker](#in-docker)
  - [As a binary](#as-a-binary)
- [Getting familiar with the folder structure](#getting-familiar-with-the-folder-structure)
- [Usage](#usage)
  - [Jurors table](#jurors-table) 
  - [Fights tables](#fights-tables)
  - [Data examples](#data-examples)
  - [Running the tool](#running-the-tool)
- [Getting the matrices](#getting-the-matrices)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Details](#details)
  - [The algorithm](#the-algorithm)
  - [Contributing](#contributing)
  - [License](#license)
  - [Author](#author)

# Setting up
## As a python module
The tool is written as python project, tested and developed in python 3.11 under Linux.

1. Clone this repository
2. Create a conda environment, venv or install python 3.11 with pip globally
3. Run `pip install -r requirements.txt`

## In docker
_in progress_

## As a binary
_in progress_

# Getting familiar with the folder structure
The data of your tournament is stored in the `data` folder. The `data` folder must contain the following structure:
```bash
data
|-- jurors.csv (or jurors.xlsx)
|fights
|  |-- fight1.csv (or fight1.xlsx)
|  |-- fight2.csv (or fight2.xlsx)
|  |-- ...
|state
|  |-- ...
```
You can use either csv or xlsx files. The xlsx files are recommended, because they are easier to edit and contain more information about the data structure.
The `state` folder is maintained by the tool and contains the current state of the tournament. You can delete it at any time, but you will lose all the progress.

# Usage
## Jurors table
The jurors table must have the following structure:

| Juror    | Chairperson | Fight_1 | Fight_2 | Fight_3 | Fight_4 | Fight_5 | Conflicts           |
|----------|-------------|---------|---------|---------|---------|---------|---------------------|
| John Doe | 1           | 1       | 0       | 1       | 0       | 0       | Russia, Bulgaria    |
| Jane Air | 0           | 0       |  1      | 0       | 1       | 1       | Team Croatia, China |
| ...      | ...         | ...     | ...     | ...     | ...     | ...     | ...                 |

- The `Juror` column contains the names of the jurors. 
- The `Chairperson` column contains the information about whether the juror is a chairperson or not (1 or 0). 
- The `Fight_N` columns contain the information about whether the juror is a juror of the fight N (present/absent) (1 or 0).
- The `Conflicts` column contains the names of teams with whom the juror has conflicts. The tool will never put a juror to see a conflicted team. The team names are separated by commas AND spaces.

You can add jurors to the table before any fight.
But you cannot remove them or change their name. If you want to remove a juror, just place 0 to the corresponding Fight_N presence cell.
You can change the chairperson status of a juror before any fight.
You can change the conflicts of a juror before any fight.

## Fights tables
The fights tables describe the bracket for the tournament. They must have the following structure (the number of columns is 3 for YNT and 4 for YPT):

| Room/Team 1 | Team 2       | Team 3   | Team 4   |
|-------------|--------------|----------|----------|
| Room A      |              |          |          |
| Russia      | Team Croatia | China    | Bulgaria |
|             |              |          |          |
| Room B      |              |          |          |
| France      | Germany      | Uganda 3 |          |
|             |              |          |          |
| ...         |              |          |          |

> **! The teams names must be the same throughout all project !** 
> If you have a team named "Team Croatia" in one fight, you must have the same team named "Team Croatia" in all other fights **AND in Conflicts column in jurors.csv**.
> The best practice is to have a TXT file with the list of teams and copy-paste it to all the fights and to the jurors table.

- First row is the header row. It is ignored by the tool, however you should write it.
- The `Room/Team 1` column contains the names of the rooms or the names of the teams. The tool will automatically detect whether the column contains the names of the rooms or the names of the teams.
- The row after the room name must contain teams names and be followed by an empty row.

Make sure that the number of teams in each fight is the same. If you have a fight with 3 teams, just leave the 4th cell empty. In CSV terms, it will look **EXACTLY** like this:
```csv
Room 315,,,
ИнжеНЭТИк-2,ДИО-ГЕН,SibLab,Физикон 2

Room 316,,,
Ионный ветер,Ом,REGION 42,
```
The best practice is to create and edit fights tables in Excel and then save them as CSV / XLSX files.

## Data examples
Please see the `_test_data` folder for the examples of the data files. It is not used by the tool, just use it as a base for all tables structures. 

## Running the tool
The logic of your work with the tool is the following:
1. Before any fight N you should have the jurors table and the fight table for fight N (it's okay if you don't yet have fight tables for the following fights N+1, N+2, ...).
2. During the preparation or right on the jury briefing you run the tool in mode 0, which will help you schedule the jurors for fight N. You may manually edit the schedule to fulfill any special requirements.
3. After the work in mode 0 is done, the tool gives you a printable schedule (HTML page).
4. It's okay if something happens after the schedule is published and you have to do any manual changes. To correct the tool's state you have to recreate the exact schedule which was used during the fight N. To do this, you **again** run the tool in mode 0 (**BEFORE** using the mode 1), which will help you recreate the schedule.
5. After the fight N successfully happened, please again make sure that the schedule used in fight N is the same as last created by the tool's mode 0 for fight N (see step 4).
6. After the fight N you run the tool in mode 1, which will make the tool remember the state. The tool will return nothing.
7. When it's time to use the tool again for fight N+1, just go to step 1!

How to launch the tool:
1. Open the terminal in the root folder of the project
2. Run `python main.py`
3. Follow the instructions in the terminal. Be careful with manual editing (the indexing of rooms and jurors starts from 0, not from 1).

The detailed logs can be found in the `output/log.txt`.

# Getting the matrices
The tool can also generate the matrices, showing how many times did pairs of jurors meet and how many times did pairs (juror, team) meet. This shows the schedule quality.
To generate the matrices, please run `python get_matrices.py` in the root folder of the project. The matrices are saved in the `output` folder as CSV and PNG.

# Configuration
The tool has a configuration file `config.py` in the root folder of the project. You can change the following parameters:
- Paths to files (not recommended)
- Mode: 'iypt' or 'iynt'. The tool will use the corresponding maximum number of teams for the printing.
You can also edit the `templates/result.html` and `templates/style.css` to change the look of the schedule. If something is broken, you can always restore the original files from the repository.

# Details
## The algorithm
_not written yet, sorry_

## Troubleshooting
_not written yet, sorry_ 

## Author
Artem Golomolzin, Siberia. Please feel free to contact me if you have any questions or suggestions.
You can contact me via Telegram @ad3ph or via email bently0709@gmail.com | a.golomolzin@g.nsu.ru

## License
If you use this software, please mention the author. You are free to modify the software under the same license.
I would be happy to hear from you if you use this software in your tournament. I also provide unlimited support for the software.

## Contributing
If you want to contribute to the project, please contact me or create an issue or a pull request.
