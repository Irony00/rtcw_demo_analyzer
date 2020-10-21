import os
import shutil
from src import make_dictionary, fill_db, sqlite3_connector, add_match_data, feature_extraction_chat, get_kill_sprees, cut_demos, get_headshot_sprees, generate_capture_list, recordings_to_avi, recording_to_avi

path = os.path.dirname(os.path.realpath(__file__))

exe_path = os.path.join(path, 'Anders.Gaming.LibTech3release.exe')
demos_path = os.path.join(path, 'demos')
vdub_output_folder = 'F:\\captures\\'
vdub_folder = os.path.join(path, 'vdub')
vdub_exe = os.path.join(vdub_folder, 'vdub64.exe')
vdub_configfile = os.path.join(path, os.path.join('src' ,'vdub_settings.vdscript'))
wolf_path = 'F:\\Rtcw\\'
wolf_dv = 'WolfDV.exe'
mod = 'osp'
demos_folder = f'{wolf_path}\\{mod}\\demos'
screenshots_folder = f'{wolf_path}\\{mod}\\screenshots'
wolf_path = 'F:\\Rtcw\\'
main_folder = f'{wolf_path}\\main'
config_file = 'record.cfg'


def main():
    demos_dct = make_dictionary(demos_path)
    db_file = f'{path}\\out.db'

    if not os.path.exists(db_file):
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

    db = sqlite3_connector(db_file)

    obituary_df = db.get_table_as_df(table_name='obituary')

    demo_df = db.get_table_as_df(table_name='demo')
    player_df = db.get_table_as_df(table_name='player')
    obituary_df = add_match_data(obituary_df, player_df, demos_dct)

    bulletevent_df = db.get_table_as_df(table_name='bulletevent')
    bulletevent_df = add_match_data(bulletevent_df, player_df, demos_dct)

    # chatmessages_df = db.get_table_as_df(table_name='chatmessage')
    # chatmessages_df = add_match_data(chatmessages_df, player_df, demos_dct, what_df='chatmessages_df')
    # chatmessages_df = feature_extraction_chat(chatmessages_df)

    #df_spree = get_kill_sprees(obituary_df, demo_df, maxtime_secs=30,  minspree=5, pov_sprees_only=True)
    #df_hs = get_headshot_sprees(bulletevent_df, demo_df, maxtime_secs=10, minspree=5, pov_sprees_only=True)
    df_spree = get_kill_sprees(obituary_df, demo_df, maxtime_secs=6, minspree=3, pov_sprees_only=True)

    demos = cut_demos(path, demos_dct, df_spree)

    choice =input(f'record {len(demos)} ? ')
    if choice != 'y':
        return

    copy_demos(demos)
    for demo in demos:
        demo_name = os.path.basename(demo)
        create_script([demo_name])
        record_screenshots()
        recording_to_avi(demo, os.path.join(screenshots_folder, demo_name),
                           vdub_output_folder,
                           vdub_exe,
                           vdub_configfile,demo_name, remove_screenshots=True)

def create_script(demo_names):
    script = '''set demo_captureFPS "60"
timescale 1
set demo_recordSound "0"
set demo_blurFrames "0"
set demo_globalConfig ""
set demo_infoWindow "0"
set demo_pngcompression "5"
set demo_saveFrame "1"'''
    demo_counter = 0
    for demo in demo_names:
        script += f'\nset demo_{demo_counter} "demo {os.path.basename(demo)}; cl_avidemo 60; set nextdemo quit"'
        demo_counter += 1

    script += '\nvstr demo_0'
    config_file_path =f'{main_folder}\\{config_file}'

    f = open(config_file_path, "w")
    f.write(script)
    f.close()


def copy_demos(demos):
    for demo in demos:
        shutil.copy2(demo, demos_folder)

def record_screenshots():
    os.chdir(wolf_path)
    os.system('WolfDV.exe +set fs_game osp +exec mpconfig.cfg +exec record.cfg')


if __name__ == '__main__':
    main()
