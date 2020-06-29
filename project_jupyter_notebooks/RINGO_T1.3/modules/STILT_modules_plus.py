#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
import pandas as pd
import datetime as dt
import netCDF4 as cdf
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, LAKES
import json 
import requests

#Set path to ICOS tools:
sys.path.insert(0,'/data/project/pytools')
#Import ICOS tools:
from icoscp.sparql import sparqls
from icoscp.sparql.runsparql import RunSparql
from icoscp.cpb.cpbinfile import CpBinFile
#from icoscp.cpb.dobj import Dobj

sys.path.insert(1,'modules')
from extra_sparqls import get_station_class, get_icos_stations_atc_samplingheight

# paths --- changed for new JupyterHub instance
path_stiltweb = '/data/stiltweb/'
path_stilt = '/data/stilt/'
path_edgar = '/data/stilt/Emissions/'

#------------------------------------------------------------------------------------------------------------------

# function to read ICOS data from Carbon Portal
def read_icos_data(f_icos,tracer,flag=True):
    
    if (len(f_icos)>0):
        df = CpBinFile(f_icos.dobj.iloc[0]).getColumns()
        df.set_index('TIMESTAMP',inplace=True)
        if flag:
            if (tracer.lower() == 'mto'):
                value_cols =[x.replace('-Flag','') for x in df.columns[df.columns.str.contains('Flag')]]
                for x in value_cols:
                    df[x].loc[df[x+'-Flag']!='O']=np.nan
            else:
                df[tracer.lower()].loc[df['Flag']!='O']=np.nan
                df['Stdev'].loc[df['Flag']!='O']=np.nan
    else:
        df = pd.DataFrame(None)
    return df

#------------------------------------------------------------------------------------

# function to convert station longitude and latitude (slat, slon) to indices of STILT model grid (ix,jy)
def lonlat_2_ixjy(slon,slat,mlon,mlat):
    #slon, slat: longitude and latitude of station
    #mlon, mlat: 1-dim. longitude and latitude of model grid
    ix = (np.abs(mlon-slon)).argmin()
    jy = (np.abs(mlat-slat)).argmin()
    return ix,jy

#------------------------------------------------------------------------------------

# function to read annual mean EDGAR emissions
def read_emissions(filename):
    
    # read EDAGR anthropogenic emissions
    # latitude and longitude are for lower left corner of grid cell
    f = cdf.Dataset(filename)
    #print(f)
    emis=f.variables["emission"][:,:,:] 
    lon_ll=f.variables["lon"][:]
    lat_ll=f.variables["lat"][:]
    time=f.variables["time"][:]

    #shift lat and lon to cell center
    dlon=np.abs(lon_ll[2]-lon_ll[1])
    dlat=np.abs(lat_ll[2]-lat_ll[1])
    emis_lon=lon_ll+0.5*dlon
    emis_lat=lat_ll+0.5*dlat

    unit="["+f.variables["emission"].units+"]"
    
    datetime=cdf.num2date(f.variables["time"][:],units=f.variables["time"].units)
    
    f.close()
    
    return emis, emis_lon, emis_lat, datetime, unit

#------------------------------------------------------------------------------------

def create_STILT_dictionary():
    # store all STILT station information in a dictionary 
    #
    # Dictionary contains information on
    #    STILT station id
    #    Station coordinates (latitude, longitude)
    #    Altitude of tracer release in STILT simultation
    #    STILT location identifier
    #    Station name - if available 
    #
    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract location from filename of link

    path_stations = path_stiltweb+'/stations/'
    all_stations = os.listdir(path_stations)

    # empty dictionary
    stations = {}

    # fill dictionary with ICOS station id, latitude, longitude and altitude
    for ist in sorted(list(set(all_stations))):
        stations[ist] = {}
        # get filename of link (original stiltweb directory structure) 
        # and extract location information
        if os.path.exists(path_stations+ist):
            loc_ident = os.readlink(path_stations+ist)
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

        
    # add information on station name (and new STILT station id) from stations.csv file used in stiltweb 

    url="https://stilt.icos-cp.eu/viewer/stationinfo"
    df = pd.read_csv(url)

    for ist in sorted(list(set(stations))):
        stationName = df.loc[df['STILT id'] == ist]['STILT name']
        if len(stationName.value_counts()) > 0:
            stations[ist]['name'] = stationName.item()
        else:
            stations[ist]['name'] = ''

    # Get list of ICOS class 1 and class 2 stations from Carbon Portal
    #query = sparqls.get_station_class()
    query = get_station_class()
    fmt = 'pandas'
    df_datatable = RunSparql(query, fmt).run()

    # add information if ICOS class 1 or class 2 site
    # add ICOS station name
    for ist in sorted(list(set(stations))):
        stations[ist]['stationClass'] = np.nan
        stations[ist]['icosName'] = ''
        stations[ist]['icosId'] = ''
        stations[ist]['icosLon'] = np.nan
        stations[ist]['icosLat'] = np.nan       
        for istICOS in df_datatable['stationId']:
            ic = int(df_datatable[df_datatable['stationId']==istICOS].index.values)
            if istICOS in ist:
                stations[ist]['stationClass'] = int(df_datatable['stationClass'][ic])
                stations[ist]['icosName'] = df_datatable['longName'][ic]
                stations[ist]['icosId'] = df_datatable['stationId'][ic]
                stations[ist]['icosLon'] = float(df_datatable['lon'][ic])
                stations[ist]['icosLat'] = float(df_datatable['lat'][ic])
                

    # add available sampling heights
    # find all co2 data files for station
    query = get_icos_stations_atc_samplingheight()
    fmt = 'pandas'
    df_datatable_hgt = RunSparql(query, fmt).run()
    for ist in sorted(list(set(stations))):
        stations[ist]['icosHeight'] = np.nan
        if (len(stations[ist]['icosName']) > 0):
            heights = df_datatable_hgt[df_datatable_hgt['stationId']==ist[0:3]]['height'].unique()
            ih = np.nan
            if (len(heights) > 0):
                if (len(ist[3:])==0):
                    ih = int(float(heights[0]))
                else:
                    ih = [int(float(el)) for el in heights if (abs(int(float(el))-int(ist[3:]))<6)]
            if isinstance(ih, list):
                if (len(ih) == 0):
                    stations[ist]['icosHeight'] = np.nan
                else:
                    stations[ist]['icosHeight'] = ih[0]
            else:
                stations[ist]['icosHeight'] = ih

    # print dictionary
    #for ist in sorted(stations):
    #    print ('station:', ist)
    #    for k in stations[ist]:
    #        print (k,':', stations[ist][k])

    # write dictionary to json file for further use
    with open("stationsDict", "w") as outfile:
        json.dump(stations, outfile)

    return stations
    
#---------------------------------------------------------------------------------------------    

def read_STILT_dictionary():
    # read STILT station dictionary from json file

    with open("stationsDict") as jsonfile:
        stations = json.load(jsonfile)

    return stations

#------------------------------------------------------------------------------------------------

def print_STILT_dictionary():
    # read STILT station dictionary from json file
    stations = read_STILT_dictionary()

    # print dictionary
    for ist in sorted(stations):
        print ('station:', ist)
        for k in stations[ist]:
            print (k,':', stations[ist][k])
        print(' ')

#------------------------------------------------------------------------------

# function to read STILT time series with hourly concentrations for RINGO T1.3
def read_stilt_timeseries_RINGO_T13(station,year,loc_ident):
    filename=path_stilt+'Results_RINGO_T1.3/'+station+'/stiltresult'+str(year)+'x'+loc_ident+'.csv'
    df= pd.read_csv(filename,delim_whitespace=True)
    df.date = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    df.name = station
    df.model = 'STILT'
    df['wind.speed']=np.sqrt((df['wind.u']**2)+(df['wind.v']**2))
    df['co2.ff']=df['co2.fuel.coal']+df['co2.fuel.oil']+df['co2.fuel.gas']
    df.set_index(['date'],inplace=True)
    #print(df)
    return df

