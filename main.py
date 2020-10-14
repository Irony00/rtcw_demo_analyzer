import os
from src import make_dictionary, fill_db

path = os.path.dirname(os.path.realpath(__file__))

exe_path = os.path.join(path, 'Anders.Gaming.LibTech3.exe')
demos_path = os.path.join(path, 'demos')


def main():
    demos_dct = make_dictionary(demos_path)
    parameters_dct = {'exportPaths': path, 'exportBulletEvents': '1', 'exportPlayers': '1', 'exportDemo': '1',
                      'exportObituaries': '1', 'exportChatMessages': '1', 'exportSQL': '1', 'exportJson': '0',
                      'exportSQLFile': 'out.db'}

    fill_db(path, parameters_dct, demos_dct, demo_folder_name=demos_path)


if __name__ == '__main__':
    main()