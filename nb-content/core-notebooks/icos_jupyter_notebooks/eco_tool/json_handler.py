# Read, update and save settings (as dictionary)
# from/to the file '.output/eco_nrt_tool/appdata/<name>.json'
# When saving, previous name.json is backed up into name_bak.json
# with a timestamp key.

from datetime import datetime
import json
import os


def _check_dir(path_to_json_dictionary: str):
    # create directory if it does not exist
    if not os.path.exists(path_to_json_dictionary):
        os.makedirs(path_to_json_dictionary)
    if not os.path.isdir(path_to_json_dictionary):
        raise FileNotFoundError(path_to_json_dictionary)


def _get_backup(path_to_json_file: str = None) -> dict:
    file, _ = os.path.splitext(path_to_json_file)
    if file[-4:] == '_bak':
        file += '.json'
    else:
        file += '_bak.json'
    backup_dict = read(file)
    return backup_dict


def _write_backup(path_to_json_file: str = None):

    latest_dict = read(path_to_json_file)

    if latest_dict:
        file, _ = os.path.splitext(path_to_json_file)
        bak_file = file + '_bak.json'

        # backup previous settings before update
        timestamp = str(datetime.today())
        backup_dict = read(bak_file)
        backup_dict[timestamp] = latest_dict

        with open(bak_file, 'w') as new_bak_file:
            json.dump(backup_dict, new_bak_file)


def get_restore_point(timestamp: str = None,
                      timestamps: list = None,
                      last: bool = None,
                      all: bool = None,
                      path_to_json_file: str = None) -> dict:

    bak_dict = _get_backup(path_to_json_file)

    if isinstance(timestamp, str):
        d = bak_dict[timestamp]
    elif isinstance(timestamps, list):
        d = {k: bak_dict.get(k, {}) for k in timestamps}
    elif isinstance(last, bool) and last:
        d = list(bak_dict.values())[-1]
    elif isinstance(all, bool) and last:
        d = bak_dict
    else:
        d = dict()
    return d


def get_restore_point_timestamps(path_to_json_file: str = None) -> list:
    bak_dict = _get_backup(path_to_json_file)
    restore_points = bak_dict.get('timestamps', [])
    restore_points.reverse()
    return restore_points


def read(path_to_json_file: str = None) -> dict:
    # read json to dict
    # This is where the path to the file is created
    if os.path.isfile(path_to_json_file):
        try:
            with open(path_to_json_file, 'r') as f:
                json_dict = json.load(f)
        except:
            json_dict = dict()
    else:
        json_dict = dict()
        path, file = os.path.split(path_to_json_file)
        _check_dir(path)
    return json_dict


def update(data_piece: dict = None,
           path_to_json_file: str = None):
    data_to_update = read(path_to_json_file)
    data_to_update.update(data_piece)
    write(data=data_to_update,
          path_to_json_file=path_to_json_file)


def write(data: dict,
          path_to_json_file: str):
    # Make backup before saving
    _write_backup(path_to_json_file)

    with open(path_to_json_file, 'w') as json_file:
        json.dump(data, json_file)
