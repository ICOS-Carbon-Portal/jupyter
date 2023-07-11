# Read, update and save settings (as dictionary)
# from/to the file 'eco_tool/appdata/name.json'
# When saving, previous name.json is backed up into name_bak.json

from datetime import datetime
import json
import os


def _valid_dir(settings_dir):
    if settings_dir is None:
        settings_dir = 'eco_tool/appdata'

    # create directory if it does not exist
    if not os.path.exists(settings_dir):
        os.mkdir(settings_dir)


def _get_backup(json_file: str = None,
                settings_dir: str = None) -> dict:
    bak_name = json_file.split('.')
    if bak_name[0][-4:] == '_bak':
        bak_name = bak_name[0] + '.json'
    else:
        bak_name = bak_name[0] + '_bak.json'
    backup_dict = read(json_file=bak_name,
                       settings_dir=settings_dir)
    return backup_dict


def _write_backup(json_file: str = None,
                  settings_dir: str = None):
    bak_name = json_file.split('.')
    bak_name = bak_name[0] + '_bak.json'

    # backup previous settings before update
    timestamp = str(datetime.today())
    backup_dict = read(json_file=bak_name, settings_dir=settings_dir)
    latest_dict = read(json_file=json_file, settings_dir=settings_dir)

    if latest_dict:
        if isinstance(backup_dict, dict) and 'timestamps' in backup_dict.keys():
            backup_dict['timestamps'].append(timestamp)
        else:
            backup_dict['timestamps'] = [timestamp]
        backup_dict[timestamp] = latest_dict

        with open(settings_dir + '/' + bak_name, 'w') as new_bak_file:
            json.dump(backup_dict, new_bak_file)


def get_restore_point(timestamps: list = None,
                      json_file: str = None,
                      settings_dir: str = None) -> dict:
    _valid_dir(settings_dir)
    bak_dict = _get_backup(json_file=json_file,
                           settings_dir=settings_dir)
    if isinstance(timestamps,str):
        timestamps = [timestamps]
    return {k: bak_dict.get(k, {}) for k in timestamps}


def get_restore_point_timestamps(json_file: str = None,
                                 settings_dir: str = None) -> list:
    _valid_dir(settings_dir)
    bak_dict = _get_backup(json_file=json_file,
                           settings_dir=settings_dir)
    restore_points = bak_dict.get('timestamps', [])
    restore_points.reverse()
    return restore_points


def read(json_file: str = None,
         settings_dir: str = None) -> dict:

    _valid_dir(settings_dir)

    # read cache
    file = settings_dir + '/' + json_file
    try:
        with open(file, 'r') as f:
            cache = json.load(f)
    except:
        cache = dict()
    return cache


def update(data_piece: dict = None,
           json_file: str = None,
           settings_dir: str = None):
    _valid_dir(settings_dir)
    data_to_update = read(json_file=json_file,
                          settings_dir=settings_dir)
    data_to_update.update(data_piece)
    write(data=data_to_update,
          json_file=json_file,
          settings_dir=settings_dir)


def write(data: dict = None,
          json_file: str = None,
          settings_dir: str = None):
    _valid_dir(settings_dir)
    # Make backup before saving
    _write_backup(json_file, settings_dir)

    with open(settings_dir + '/' + json_file, 'w') as json_file:
        json.dump(data, json_file)
