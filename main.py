import os
import shutil
from src import make_dictionary, fill_db, sqlite3_connector, add_match_data, feature_extraction_chat, get_kill_sprees, \
    cut_demos, get_headshot_sprees, generate_capture_list, recordings_to_avi, recording_to_avi
from enum import Enum
import json

path = os.path.dirname(os.path.realpath(__file__))

exe_path = os.path.join(path, 'Anders.Gaming.LibTech3release.exe')
demos_path = os.path.join(path, 'demos')
vdub_output_folder = 'F:\\captures\\'
vdub_folder = os.path.join(path, 'vdub')
vdub_exe = os.path.join(vdub_folder, 'vdub64.exe')
vdub_configfile = os.path.join(path, os.path.join('src', 'vdub_settings.vdscript'))
wolf_path = 'F:\\Rtcw\\'
wolf_dv = 'WolfDV.exe'
mod = 'wolfcam-rtcw'
demos_folder = f'{wolf_path}\\{mod}\\demos'
screenshots_folder = f'{wolf_path}\\{mod}\\screenshots'
wolf_path = 'F:\\Rtcw\\'
main_folder = f'{wolf_path}\\main'
config_file = 'record.cfg'
db_file = f'{path}\\out.db'


def ensure_dir(folder):
    total = os.path.join(path, folder)
    if not os.path.exists(total):
        os.makedirs(total)


class Type(Enum):
    KILL_SPREE = 'kill'
    HS_SPREE = 'hs'


class Filter(dict):
    def __init__(self, **kwargs):
        self.min_spree = kwargs['min_spree']
        self.max_time = kwargs['max_time']
        self.type = kwargs['type']
        self.offset_start = kwargs.get('offset_start', 5)
        self.offset_end = kwargs.get('offset_end', 5)
        self.exclude_weapons = kwargs.get('exclude_weapons', [])
        self.include_weapons = kwargs.get('include_weapons', None)
        dict.__init__(self, min_spree=self.min_spree, max_time=self.max_time, type=self.type, offset_start=self.offset_start, offset_end=self.offset_end, exclude_weapons=self.exclude_weapons, include_weapons=self.include_weapons)

    def filter_str(self):
        return f'kill_spree_output_{self.min_spree}spree_{self.max_time}s'




def load_db():
    demos_dct = make_dictionary(demos_path)
    parameters_dct = {'exportPaths': path,
                      'exportBulletEvents': '1',
                      'exportPlayers': '1',
                      'exportDemo': '1',
                      'exportObituaries': '1',
                      'exportChatMessages': '1',
                      'exportJson': '0',
                      'exportSQL': '1',
                      'exportJsonFile': 'out.json',
                      'exportSQLFile': db_file}

    fill_db(path, parameters_dct, demos_dct, demo_folder_name=demos_path)

def main():
    if not os.path.exists(db_file):
        load_db()

    data = Data(db_file, demos_path).load()
    sprees = data.get_moments(Filter(min_spree=5, max_time=30, type='kill'))
    sprees = [sprees[0]]

    cut_demos = [cut_demo(path, spree) for spree in sprees]
    record_cut


def spree_to_json(spree, filename):
    file = open(f'{filename}.json', 'w')
    file.write(json.dumps(spree, indent=4))
    file.close()

def cut_demo(root_path, spree, offset_start = 5, offset_end = 5):
    output_folder = spree['filter'].filter_str()
    output_file = os.path.join(root_path, output_folder, f"{spree['player'].lower()}_{spree['spreecount']}{spree['demo_type']}")
    demo_output_file = f'{output_file}.dm60'

    cmd = f'cut {spree["demo_path"]} {output_file}.dm60 {str(spree["start"] - (offset_start * 1000))} {str(spree["end"] + (offset_end * 1000))} 1 0'
    if os.system(f'{exe_path} {cmd}') > 0:
        return None
    spree_to_json(spree, f'{output_file}.json')

    return demo_output_file

def record(demos):
    for demo in demos:
        shutil.copy2(demo, demos_folder)
    for demo in demos:
        demo_name = os.path.basename(demo)
        create_script([demo_name], True)
        os.chdir(wolf_path)
        os.system(
            'WolfDV.exe +set fs_game wolfcam-rtcw +exec mpconfig.cfg +exec record.cfg +set cg_draw2D 0 +set r_fullscreen 0')
        output_file_name = recording_to_avi(demo, os.path.join(screenshots_folder, demo_name),
                                            vdub_output_folder,
                                            vdub_exe,
                                            vdub_configfile, demo_name, remove_screenshots=True)

def copy_demos(demos):
    for demo in demos:
        shutil.copy2(demo, demos_folder)




if __name__ == '__main__':
    main()
