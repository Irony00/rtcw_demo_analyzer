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


class Data:
    def __init__(self, db_file, demos):
        self.path = path
        self.db_file = db_file
        self.demos_dct = make_dictionary(demos)
        self.demo_df = None
        self.player_df = None
        self.obituary_df = None
        self.bullet_event_df = None

    def load(self):
        db = sqlite3_connector(self.db_file)
        self.obituary_df = db.get_table_as_df(table_name='obituary')

        self.demo_df = db.get_table_as_df(table_name='demo')
        self.player_df = db.get_table_as_df(table_name='player')
        self.obituary_df = add_match_data(self.obituary_df, self.player_df, self.demos_dct)

        self.bullet_event_df = db.get_table_as_df(table_name='bulletevent')
        self.bullet_event_df = add_match_data(self.bullet_event_df, self.player_df, self.demos_dct)
        return self

    def get_moments(self, filter):
        if filter.type is Type.KILL_SPREE.value:
            return self.__get_kill_sprees(filter)
        elif filter.type is Type.HS_SPREE.value:
            return self.__get_hs_sprees(filter)
        else:
            raise Exception

    def __get_hs_sprees(self, filter):
        raise NotImplementedError

    def __get_kill_sprees(self, filter):
        df_spree = get_kill_sprees(self.obituary_df, self.demo_df, maxtime_secs=filter.max_time,
                                   minspree=filter.min_spree, pov_sprees_only=True,
                                   exclude_weapon_filter=filter.exclude_weapons,
                                   include_weapon_filter=filter.include_weapons)
        result = []
        for i in range(len(df_spree)):
            ensure_dir(os.path.join(self.path, filter.filter_str()))
            spree = df_spree.iloc[i]
            obj = {'player': spree.player.decode(),
                   'demo_name': spree.demo,
                   'spreecount': int(spree.spreecount),
                   'weapons': spree.weapons,
                   'demo_type': filter.type,
                   'demo_path': os.path.join(os.path.join(demos_path, spree.match), spree.demo),
                   'start': int(spree.start),
                   'end': int(spree.end),
                   'filter': filter}
            result.append(obj)
        return result

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

def record_moments(data, filter):
    return record([cut_demo(path, spree) for spree in data.get_moments(filter)])

def spree_to_json(spree, filename):
    file = open(f'{filename}.json', 'w')
    file.write(json.dumps(spree, indent=4))
    file.close()

def cut_demo(root_path, spree, offset_start = 5, offset_end = 5):
    output_folder = spree['filter'].filter_str()
    output_file = os.path.join(root_path, output_folder, f"{spree['player'].lower()}_{spree['spreecount']}{spree['demo_type']}")
    demo_output_file = f'{output_file}.dm_60'

    cmd = f'cut {spree["demo_path"]} {output_file}.dm_60 {str(spree["start"] - (offset_start * 1000))} {str(spree["end"] + (offset_end * 1000))} 1 0'
    if os.system(f'{exe_path} {cmd}') > 0:
        return None
    spree_to_json(spree, output_file)

    return demo_output_file

def record(demos):
    for demo in demos:
        shutil.copy2(demo, demos_folder)
    for demo in demos:
        demo_name = os.path.basename(demo).rsplit(".", 1)[0]
        create_script([demo_name], True)
        os.chdir(wolf_path)
        os.system(
            'WolfDV.exe +set fs_game wolfcam-rtcw +exec mpconfig.cfg +exec record.cfg +set cg_draw2D 0 +set r_fullscreen 0')
        output_file_name = recording_to_avi(demo, os.path.join(screenshots_folder, demo_name),
                                            vdub_output_folder,
                                            vdub_exe,
                                            vdub_configfile, demo_name, remove_screenshots=True)
        json_path = f'{demo.rsplit(".", 1)[0]}.json'
        shutil.copy2(json_path, vdub_output_folder)

        json_file = os.path.join(vdub_output_folder, os.path.basename(json_path))

        shutil.copyfile(output_file_name, f'\\\\TOWER\\woudaapje\\Pim\\rtcwclips{os.path.basename(output_file_name)}')
        os.remove(output_file_name)
        shutil.copyfile(json_file, f'\\\\TOWER\\woudaapje\\Pim\\rtcwclips{os.path.basename(json_file)}')
        os.remove(json_file)



def create_script(demo_names, record):
    script = '''set demo_captureFPS "60"
                timescale 1
                set demo_recordSound "0"
                set demo_blurFrames "0"
                set demo_globalConfig ""
                set demo_infoWindow "0"
                set demo_pngcompression "5"
                set demo_drawYourFragsOnly "1"
                set demo_saveFrame "1"
                set mm_demoCrosshair "1"                
                set mm_demoPopUp "1"
                set mm_drawYourOwnFragsOnly "1"                
                '''

    demo_counter = 0
    for demo in demo_names:
        avi_demo = ''
        if record:
            avi_demo = 'cl_avidemo 60;'
        script += f'\nset demo_{demo_counter} "demo {os.path.basename(demo)}; {avi_demo} set nextdemo quit"'
        demo_counter += 1

    script += '\nvstr demo_0'
    config_file_path = f'{main_folder}\\{config_file}'

    f = open(config_file_path, "w")
    f.write(script)
    f.close()


def main():
    if not os.path.exists(db_file):
        load_db()

    data = Data(db_file, demos_path).load()
    record_moments(data, Filter(min_spree=5, max_time=30, type='kill', offset_start=5, offset_end=5, exclude_weapons=['merlinator']))
    record_moments(data, Filter(min_spree=4, max_time=30, type='kill', offset_start=5, offset_end=5,
                                exclude_weapons=['merlinator']))
    record_moments(data, Filter(min_spree=3, max_time=20, type='kill', offset_start=5, offset_end=5,exclude_weapons=['merlinator']))



if __name__ == '__main__':
    main()
