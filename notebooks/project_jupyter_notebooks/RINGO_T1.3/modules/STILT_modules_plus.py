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
import cartopy
cartopy.config['data_dir'] = '/data/project/cartopy/'
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, LAKES
import json 
import requests

#Import ICOS tools:
from icoscp.cpb.dobj import Dobj


# paths --- changed for new JupyterHub instance
path_stiltweb = '/data/stiltweb/'
path_stilt = '/data/stilt/'
path_edgar = '/data/stilt/Emissions/'
#path_plots = './plots/'

#------------------------------------------------------------------------------------------------------------------

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

#------------------------------------------------------------------------------------------------

def print_STILT_dictionary(stilt_stations):
    
    if not stilt_stations:
        # read STILT station dictionary from json file
        stilt_stations = read_STILT_dictionary()

    # print dictionary
    for ist in sorted(stilt_stations):
        print ('station:', ist)
        for k in stilt_stations[ist]:
            print (k,':', stilt_stations[ist][k])
        print(' ')

#------------------------------------------------------------------------------
# function to read STILT time series with hourly concentrations for RINGO T1.3
def read_stilt_timeseries_RINGO_T13(station,year,loc_ident):
    filename=path_stilt+'Results_RINGO_T1.3_test/'+station+'/stiltresult'+str(year)+'x'+loc_ident+'.csv'
    df= pd.read_csv(filename,delim_whitespace=True)
    df.date = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    df.name = station
    df.model = 'STILT'
    df['wind.speed']=np.sqrt((df['wind.u']**2)+(df['wind.v']**2))
    df['co2.ff']=df['co2.fuel.coal']+df['co2.fuel.oil']+df['co2.fuel.gas']
    df.set_index(['date'],inplace=True)
    #print(df)
    return df

#------------------------------------------------------------------------------
# function to read STILT time series with hourly concentrations for RINGO T1.3, updated with more STILT runs
def read_stilt_timeseries_RINGO_T13_update(station,year,loc_ident):
    filename=path_stilt+'Results_RINGO_T1.3_test/'+station+'/stiltresult'+str(year)+'x'+loc_ident+'.csv'
    df= pd.read_csv(filename,delim_whitespace=True)
    df.date = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    df.name = station
    df.model = 'STILT'
    df['wind.speed']=np.sqrt((df['wind.u']**2)+(df['wind.v']**2))
    df['co2.ff']=df['co2.fuel.coal']+df['co2.fuel.oil']+df['co2.fuel.gas']
    df.set_index(['date'],inplace=True)
    #print(df)
    return df

#------------------------------------------------------------------------------
# function to convert UTC to mean solar time MST
def utc_mst(utc_hour, longitude):
    #convert hours in UTC to mean solar time MST using longitude at location
    #longitude in degree (-180 to 180) or (0 to 360)
    utc_hour = utc_hour % 24
    local_hour = utc_hour + round(np.deg2rad(longitude) / np.pi * 12)
    local_hour = local_hour % 24
    return local_hour
