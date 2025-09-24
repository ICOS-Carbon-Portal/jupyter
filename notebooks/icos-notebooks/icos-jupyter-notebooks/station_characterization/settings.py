# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:09:33 2020

@author: Claudio
"""

import json

def default(stationCode):
    '''
    Parameters
    ----------
    stationCode : STR
        ICOS Stilt Station code as string. Example HTM150

    Returns
    -------
    json
        Default values to populate the UI for station

    '''
    settings={
    	'stationCode':'empty',
    	'startYear': 2018,
    	'startMonth':1,
    	'startDay':1,
    	'endYear':2018,
    	'endMonth': 12,
    	'endDay': 31,
    	'timeOfDay': [0, 3, 6, 9, 12, 15, 18, 21],
    	'binSize':15,
    	'binInterval':200,
    	'unit':'percent',
    	'titles':'no',
    	'labelPolar':'no',
    	'saveFigs':'no'
    	}
    
    # replace the stationCode
    settings['stationCode'] = stationCode
    return json.dumps(settings)
def getDict():
    # return an empty dictionary, keys provided but no value
    settings={
    	'stationCode':'',
    	'startYear':'',
    	'startMonth':'',
    	'startDay':'',
    	'endYear':'',
    	'endMonth': '',
    	'endDay': '',
    	'timeOfDay':'',
    	'binSize':'',
    	'binInterval':'',
    	'unit':'',
    	'titles':'',
    	'labelPolar':'',
    	'saveFigs':''
    	}
    return settings
    
    
    
def write(stationCode):    
    f = open(__fname(stationCode), 'w')
    f.write(default(stationCode))
    f.close()
    

def read(stationCode):
    with open(__fname(stationCode)) as f:
        data = json.load(f)
    return data
    
def __fname(stationCode):
    fname = './settings/' + stationCode + '.json'
    return fname


