# Read/save settings from/to the file 'appdata/cache.json'
# When saving, previous cache.json is backed up into cache_bak.json 


import json
import os
from datetime import datetime


def _fix_dir(settings_dir):
    # create directory if it does not exist
    if settings_dir not in os.listdir():
        os.mkdir(settings_dir)

        
def read(json_file = None, settings_dir = None):
    if json_file is None:
        json_file = 'cache.json'
    if settings_dir is None:
        settings_dir = 'appdata'
    _fix_dir(settings_dir)
    
    # read cache
    file = settings_dir + '/' + json_file
    try:
        with open(file, 'r') as f:
            cache = json.load(f)
    except:
        cache = dict()
    return cache
    
def _backup(json_file, settings_dir):
    
    # file to backup 
    bak_name = json_file.split('.')
    bak_name = bak_name[0] + '_bak.json' 
    
    # backup previous settings before update
    timestamp = str(datetime.today())
    backup_dic = read(json_file=bak_name, settings_dir=settings_dir)
    latest_dic = read(json_file=json_file, settings_dir=settings_dir)
    
    if latest_dic:
        if isinstance(backup_dic,dict) and 'timestamps' in backup_dic.keys():
            backup_dic['timestamps'].append(timestamp)
        else:
            backup_dic['timestamps'] = [timestamp]
        backup_dic[timestamp] = latest_dic

        with open(settings_dir + '/' + bak_name, 'w') as new_bak_file:
            json.dump(backup_dic, new_bak_file)
    
def write(data, json_file_name, settings_dir):
    
    # Make backup before saving
    _backup(json_file_name, settings_dir)
    
    with open(settings_dir + '/' + json_file_name, 'w') as json_file:
        json.dump(data, json_file)
    