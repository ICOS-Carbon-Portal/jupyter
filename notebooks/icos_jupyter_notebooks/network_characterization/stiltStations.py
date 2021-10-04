# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 09:07:38 2020
@author: Claudio
"""

import os
import numpy as np
import pandas as pd
from icoscp.station import station as cpstation
import requests

STILTPATH = '/data/stiltweb/stations/'

def getStilt():
    # store all STILT station information in a dictionary 
    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract location from filename of link
    
    #-----  assemble information
    # use directory listing from siltweb data
    allStations = os.listdir(STILTPATH)

    
    # add information on station name (and new STILT station id) from stations.csv file used in stiltweb     
    url="https://stilt.icos-cp.eu/viewer/stationinfo"
    df = pd.read_csv(url)
    
    
    # add ICOS flag to the station
    icosStations = cpstation.getIdList()
    icosStations = list(icosStations['id'][icosStations.theme=='AS'])
    
    #----  dictionary to return
    stations = {}
    countries = {}

    # fill dictionary with ICOS station id, latitude, longitude and altitude
    for ist in sorted(allStations):
  
        if not ist in df['STILT id'].values:
            continue
        
        stations[ist] = {}
        # get filename of link (original stiltweb directory structure) and extract location information
       
        loc_ident = os.readlink(STILTPATH+ist)
        clon = loc_ident[-13:-6]
        lon = np.float(clon[:-1])
        if clon[-1:] == 'W':
            lon = -lon
        clat = loc_ident[-20:-14]
        lat = np.float(clat[:-1])
        if clat[-1:] == 'S':
            lat = -lat
        alt = np.int(loc_ident[-5:])

        stations[ist]['lat']=lat
        stations[ist]['lon']=lon
        stations[ist]['alt']=alt
        stations[ist]['locIdent']=os.path.split(loc_ident)[-1]

        # set the name and id         
        stations[ist]['id'] = df.loc[df['STILT id'] == ist]['STILT id'].item()        
        stationName = str(df.loc[df['STILT id'] == ist]['STILT name'].item())        
        stations[ist]['name'] = __stationName(stations[ist]['id'], stationName, stations[ist]['alt'])        

        # set a flag if it is an ICOS station
        if stations[ist]['id'][0:3].upper() in icosStations:
            stations[ist]['icos'] = True
        else:
            stations[ist]['icos'] = False
        
        
        # set years and month of available data
        years = os.listdir(STILTPATH+'/'+ist)
        stations[ist]['years'] = years
        for yy in sorted(stations[ist]['years']):
            stations[ist][yy] = {}
            months = os.listdir(STILTPATH+'/'+ist+'/'+yy)
            stations[ist][yy]['months'] = months
            stations[ist][yy]['nmonths'] = len(stations[ist][yy]['months'])
            
            
        #added by Ida - countries:

        countries = {'AMS': 'Netherlands', 'AMS_DW': 'Netherlands', 'ARR': 'Norway', 'BAL': 'location in ocean', 'BAN112': 'Switzerland', 'BAN953': 'Switzerland', 'BER': 'Germany', 'BER_DW': 'Germany', 'BER_UW': 'Germany', 'BGU': 'Spain', 'BIK300': 'Poland', 'BIR': 'Norway', 'BOR': 'France', 'BOR_DW': 'France', 'BOR_UW': 'France', 'BRM212': 'Switzerland', 'BRM213': 'Switzerland', 'BSC': 'Romania', 'CBW': 'Netherlands', 'CBW027': 'Netherlands', 'CBW067': 'Netherlands', 'CBW127': 'Netherlands', 'CBW207': 'Netherlands', 'CES020': 'Netherlands', 'CES050': 'Netherlands', 'CES200': 'Netherlands', 'CGR': 'Italy', 'CMN': 'Italy', 'CMN760': 'Italy', 'DAO': 'Switzerland', 'DAV': 'Switzerland', 'DEC': 'Spain', 'DRX': 'France', 'EGH': 'United Kingdom', 'ERERER': 'Sweden', 'FIK': 'Greece', 'FRE': 'Germany', 'GAT030': 'Germany', 'GAT060': 'Germany', 'GAT132': 'Germany', 'GAT344': 'Germany', 'GIF': 'France', 'GIF010': 'France', 'GIF050': 'France', 'GOL': 'Germany', 'HAM': 'Germany', 'HAM_DW': 'Germany', 'HAM_UW': 'Germany', 'HEI': 'Germany', 'HEL': 'Germany', 'HFD': 'United Kingdom', 'HPB010': 'Germany', 'HPB093': 'Germany', 'HPB131': 'Germany', 'HTM030': 'Sweden', 'HTM150': 'Sweden', 'HUN096': 'Hungary', 'IDA': 'Latvia', 'IDS': 'Sweden', 'IPR015': 'Italy', 'IPR100': 'Italy', 'ISEN': 'Germany', 'ISN': 'Germany', 'IZN': 'Spain', 'JENA': 'Germany', 'JFJ': 'Switzerland', 'JFJ960': 'Switzerland', 'JUE': 'Germany', 'KAS': 'Poland', 'KIT030': 'Germany', 'KIT050': 'Germany', 'KIT100': 'Germany', 'KIT200': 'Germany', 'KRE010': 'Czechia', 'KRE125': 'Czechia', 'KRE250': 'Czechia', 'LIL': 'France', 'LIL_DW': 'Belgium', 'LIL_UW': 'France', 'LIN099': 'Germany', 'LMP': 'Italy', 'LPO': 'France', 'LUT': 'Netherlands', 'LUX': 'Luxembourg', 'LUX_DW': 'Germany', 'LUX_UW': 'France', 'LYO': 'France', 'LYO_DW': 'France', 'LYO_UW': 'France', 'MAH': 'Ireland', 'MED-1': 'Spain', 'MED-2': 'location in ocean', 'MED-3': 'location in ocean', 'MED-4': 'location in ocean', 'MED-5': 'location in ocean', 'MHD': 'Ireland', 'MIL': 'Italy', 'MUN': 'Germany', 'MUN_DW': 'Germany', 'MUN_UW': 'Germany', 'NOR100': 'Sweden', 'OES': 'Sweden', 'OPE010': 'France', 'OPE050': 'France', 'OPE120': 'France', 'OPO': 'Portugal', 'OST': 'Denmark', 'OTTA': 'Norway', 'OXK163': 'Germany', 'PAL': 'Finland', 'PAR': 'France', 'PAR_DW': 'France', 'PDM': 'France', 'POING': 'Germany', 'POING5': 'Germany', 'POLAND': 'Poland', 'POTT': 'Germany', 'PRA': 'Czechia', 'PRA_DW': 'Czechia', 'PRS': 'Italy', 'PTL': 'Italy', 'PUI': 'Finland', 'PUY': 'France', 'RGL': 'United Kingdom', 'RIS': 'Denmark', 'RMS': 'France', 'ROM1': 'Romania', 'ROT': 'Netherlands', 'ROT_UW': 'Netherlands', 'RUH': 'Germany', 'RUH_UW': 'Germany', 'SAC060': 'France', 'SAC100': 'France', 'SCHOEN': 'Germany', 'SET': 'Belgium', 'SKK': 'United Kingdom', 'SMR125': 'Finland', 'SMR127': 'Finland', 'SSL': 'Germany', 'STE252': 'Germany', 'STH': 'Sweden', 'STH_DW': 'Sweden', 'STK200': 'Germany', 'STR': 'Italy', 'SVB150': 'Sweden', 'TAC191': 'United Kingdom', 'TEST': 'Norway', 'THRB': 'location in ocean', 'TOH147': 'Germany', 'TRN050': 'France', 'TRN100': 'France', 'TRN180': 'France', 'TST': 'location in ocean', 'TTA050': 'United Kingdom', 'TTA222': 'United Kingdom', 'UTO': 'Finland', 'VIE': 'Austria', 'VIE_DW': 'Austria', 'VIE_UW': 'Austria', 'VND': 'Italy', 'VOI': 'Russia', 'WAO': 'United Kingdom', 'WES': 'Germany', 'ZRK': 'Germany', 'ZSF': 'Austria'}
        
        if ist in countries.keys():
            stations[ist]['country'] = countries[ist]
            
        else:
               
            stations[ist]['country']= 'zzz'
            """ 
            # revers geocoding
            baseurl = 'https://nominatim.openstreetmap.org/reverse?format=json&'
            url = baseurl + 'lat=' + str(stations[ist]['lat']) + '&lon=' + str(stations[ist]['lon']) + '&zoom=3'
            r = requests.get(url=url)
            c = r.json()

            if not 'error' in c.keys():
                country_code = c['address']['country_code']

            if country_code:
                # API to reterive country information using country code. 
                url='https://restcountries.eu/rest/v2/alpha/' + country_code
                resp = requests.get(url=url)
                country_information = resp.json()
                stations[ist]['country']=country_information['name']
            else:
                stations[ist]['country']= 'ZZ location in ocean'
            """

    return stations
            

def __stationName(idx, name, alt):    
    if name=='nan':
        name = idx
    if not (name[-1]=='m' and name[-2].isdigit()):           
        name = name + ' ' + str(alt) + 'm'    
    return name
    
