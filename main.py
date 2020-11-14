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
mod = 'wolfcam-rtcw'
demos_folder = f'{wolf_path}\\{mod}\\demos'
screenshots_folder = f'{wolf_path}\\{mod}\\screenshots'
wolf_path = 'F:\\Rtcw\\'
main_folder = f'{wolf_path}\\main'
config_file = 'record.cfg'


def ensure_dir(folder):
    total = os.path.join(path, folder)
    try:
        shutil.rmtree(total)
    except:
        pass
    os.mkdir(total)


def get_hs_sprees_and_cut_demos(bullet_event_df, demo_df, demos_dct, maxtime, minspree, offset_start=5, offset_end=5):
    output_folder_name = f'hs_spree_output_{minspree}hs_{maxtime}seconds'
    ensure_dir(output_folder_name)
    df_hs = get_headshot_sprees(bullet_event_df, demo_df, maxtime_secs=maxtime, minspree=minspree, pov_sprees_only=True)
    return cut_demos(path, demos_dct, df_hs, offset_start=offset_start, offset_end=offset_end, demo_type='hs',
                  output_folder=output_folder_name)

def get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime, minspree ,offset_start=5, offset_end=5, exclude_weapons=[], include_weapon_filter=None):
    if not include_weapon_filter:
        output_folder_name = f'kill_spree_output_{minspree}spree_{maxtime}seconds'
    else:
        weps = '-'.join([weapon for weapon in include_weapon_filter])
        output_folder_name = f'kill_spree_output_{minspree}spree_{maxtime}seconds{weps}'
    ensure_dir(output_folder_name)
    df_spree = get_kill_sprees(obituary_df, demo_df, maxtime_secs=maxtime, minspree=minspree, pov_sprees_only=True,
                               exclude_weapon_filter=exclude_weapons, include_weapon_filter=include_weapon_filter)
    return cut_demos(path, demos_dct, df_spree, offset_start=offset_start, offset_end=offset_end, output_folder=output_folder_name)



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

    demos = []
    #demos += get_hs_sprees_and_cut_demos(bulletevent_df, demo_df, demos_dct, maxtime=1, minspree=3)
    #demos += get_hs_sprees_and_cut_demos(bulletevent_df, demo_df, demos_dct, maxtime=10, minspree=4)
    demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=10, minspree=4, exclude_weapons=['panzerfaust', 'merlinator'])
    #demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=8, minspree=3, exclude_weapons=['panzerfaust'])
    demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=30, minspree=5, exclude_weapons=['panzerfaust', 'merlinator'])
    #demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=8, minspree=3, include_weapon_filter=['sniper'])
    #demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=20, minspree=3,
    #                                        include_weapon_filter=['knife'])
    #demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=8, minspree=1,
                                            #include_weapon_filter=['knife'])
    # demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=60, minspree=2,
#                                           include_weapon_filter=['knife'])
    # demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=15, minspree=5,
    #                                        include_weapon_filter=['panzerfaust', 'grenade'])
    # demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=15, minspree=4,
    #                                        include_weapon_filter=['panzerfaust', 'grenade'])
    # demos += get_kill_sprees_and_cut_demos(obituary_df, demo_df, demos_dct, maxtime=15, minspree=3,
    #                                        include_weapon_filter=['panzerfaust', 'grenade'])
    copy_demos(demos)
    for demo in demos:
        demo_name = os.path.basename(demo)
        create_script([demo_name], True)
        record_screenshots()
        output_file_name = recording_to_avi(demo, os.path.join(screenshots_folder, demo_name),
                           vdub_output_folder,
                           vdub_exe,
                           vdub_configfile, demo_name, remove_screenshots=True)

        #shutil.copy2(output_file_name, f'\\\\TOWER\\woudaapje\\\\Pim\\\\rtcwclips\\\\{os.path.basename(output_file_name)}')
        #os.remove(output_file_name)



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
    config_file_path =f'{main_folder}\\{config_file}'

    f = open(config_file_path, "w")
    f.write(script)
    f.close()


def copy_demos(demos):
    for demo in demos:
        shutil.copy2(demo, demos_folder)

def record_screenshots():
    os.chdir(wolf_path)
    os.system('WolfDV.exe +set fs_game wolfcam-rtcw +exec mpconfig.cfg +exec record.cfg +set cg_draw2D 0 +set r_fullscreen 0')


if __name__ == '__main__':
    main()
