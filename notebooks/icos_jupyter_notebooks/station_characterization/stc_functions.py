# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 08:04:31 2020

@author: Ida Storm

Functions to run the station characterization notebook on exploredata.

"""

import time
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import math
import numpy as np
from netCDF4 import Dataset
import textwrap
import datetime as dt
import os
import six
import requests


#for the widgets
from IPython.core.display import display, HTML 

# import required libraries

import netCDF4 as cdf

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
warnings.filterwarnings('ignore')

import json

stcDataPath='/data/project/stc/'

#added - not show the figure that I am saving (different size than the one displayed
#for land cover bar graph)
matplotlib.pyplot.ioff()


#path to footprints
pathFP='/data/stiltweb/stations/'

#Earth's radius in km (for calculating distances between the station and cells)
R = 6373.8

dictionary_color = {'Urban': {'color': 'red'}, 'Cropland':{'color':'darkgoldenrod'}, 'Oceans':{'color':'blue'}, 
                    'Forests':{'color':'green'}, 'Pastures and grassland':{'color':'yellow'}, 'Other':{'color':'black'}, 'No data':{'color': 'grey'}}



#function to read and aggregate footprints for given date range
def read_aggreg_footprints(station, date_range):
    
    # loop over all dates and read netcdf files

    # path to footprint files in new stiltweb directory structure
    pathFP='/data/stiltweb/stations/'
    
    fp=[]
    nfp=0
    first = True
    for date in date_range:
        
  
        filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')
 
        if os.path.isfile(filename):
            f_fp = cdf.Dataset(filename)
          
            if (first):
                fp=f_fp.variables['foot'][:,:,:]
                lon=f_fp.variables['lon'][:]
                lat=f_fp.variables['lat'][:]
                first = False
            else:
                fp=fp+f_fp.variables['foot'][:,:,:]
            f_fp.close()
            nfp+=1
        #else:
            #print ('file does not exist: ',filename)
    if nfp > 0:
        fp=fp/nfp
        title = 'not used'
        
        return nfp, fp, lon, lat, title

    else:

        return 0, None, None, None, None

def get_station_class():
    # Query the ICOS SPARQL endpoint for a station list
    # query stationId, class, lng name and country
    # output is an object "data" containing the results in JSON

    url = 'https://meta.icos-cp.eu/sparql'

    query = """
    prefix st: <http://meta.icos-cp.eu/ontologies/stationentry/>
    select distinct ?stationId ?stationClass ?country ?longName
    from <http://meta.icos-cp.eu/resources/stationentry/>
    where{
      ?s a st:AS .
      ?s st:hasShortName ?stationId .
      ?s st:hasStationClass ?stationClass .
      ?s st:hasCountry ?country .
      ?s st:hasLongName ?longName .
      filter (?stationClass = "1" || ?stationClass = "2")
    }
    ORDER BY ?stationClass ?stationId 
    """
    r = requests.get(url, params = {'format': 'json', 'query': query})
    data = r.json()

    # convert the the result into a table
    # output is an array, where each row contains 
    # information about the station

    cols = data['head']['vars']
    datatable = []

    for row in data['results']['bindings']:
        item = []
        for c in cols:
            item.append(row.get(c, {}).get('value'))
        
        datatable.append(item)

    # print the table 
    df_datatable = pd.DataFrame(datatable, columns=cols)
    #df_datatable.head(5)
    return df_datatable

def available_STILT_dictionary():
    # store availability of STILT footprints in a dictionary 

    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract availability from directory structure
    
 
    #pathStations='./data/stiltweb/slots/56.10Nx013.42Ex00030/'    
    #pathStations='/opt/stiltdata/fsicos2/stiltweb/stations/'
    allStations = os.listdir(pathFP)
    

    # empty dictionary
    available = {}

    # fill dictionary with station name, years and months for each year
    for ist in sorted(list(set(allStations))):
        if os.path.exists(pathFP+'/'+ist):
            #print ('directory '+pathStations+'/'+ist+' exits')
            available[ist] = {}
            years = os.listdir(pathFP+'/'+ist)
            available[ist]['years'] = years
            for yy in sorted(available[ist]['years']):
                available[ist][yy] = {}
                months = os.listdir(pathFP+'/'+ist+'/'+yy)
                available[ist][yy]['months'] = months
                available[ist][yy]['nmonths'] = len(available[ist][yy]['months'])
        #else:
        #    print ('directory '+pathStations+'/'+ist+' does not exit')

    # Get list of ICOS class 1 and class 2 stations from Carbon Portal
    df_datatable = get_station_class()

    # add information if ICOS class 1 or class 2 site
    for ist in sorted(available):
        available[ist]['stationClass'] = np.nan
        for istICOS in df_datatable['stationId']:
            ic = int(df_datatable[df_datatable['stationId']==istICOS].index.values)
            if istICOS in ist:
                available[ist]['stationClass'] = df_datatable['stationClass'][ic]
    return available

def create_STILT_dictionary():
    # store all STILT station information in a dictionary 

    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract location from filename of link
    
    #UPDATE
    pathStations='/data/stiltweb/stations/'
    
    allStations = os.listdir(pathStations)

    # empty dictionary
    stations = {}

    # fill dictionary with ICOS station id, latitude, longitude and altitude
    for ist in sorted(list(set(allStations))):
        stations[ist] = {}
        # get filename of link (original stiltweb directory structure) 
        # and extract location information
        if os.path.exists(pathStations+ist):
            #loc_ident = os.readlink(pathStations+ist)
            loc_ident = '56.10Nx013.42Ex00030'
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
    df_datatable = get_station_class()

    # add information if ICOS class 1 or class 2 site
    for ist in sorted(list(set(stations))):
        stations[ist]['stationClass'] = np.nan
        for istICOS in df_datatable['stationId']:
            ic = int(df_datatable[df_datatable['stationId']==istICOS].index.values)
            if istICOS in ist:
                stations[ist]['stationClass'] = df_datatable['stationClass'][ic]

    return stations

#previously up top
stations = create_STILT_dictionary()

#updated --> take the timeselect list and returns the "correct" dataframe
#otherwise - not correct hours!
# function to read STILT concentration time series (new format of STILT results)
def read_stilt_timeseries_upd(station,date_range,timeselect_list):
    url = 'https://stilt.icos-cp.eu/viewer/stiltresult'
    headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}
    # check if STILT results exist
    #pathFP='/data/stiltweb/stations/'
    new_range=[]
    
    for date in date_range:
        if os.path.exists(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/'):
            new_range.append(date)
            
    if len(new_range) > 0:
        date_range = new_range
        fromDate = date_range[0].strftime('%Y-%m-%d')
        toDate = date_range[-1].strftime('%Y-%m-%d')
        columns = ('["isodate","co2.stilt","co2.fuel","co2.bio","co2.bio.gee","co2.bio.resp","co2.fuel.coal","co2.fuel.oil",'+
                   '"co2.fuel.gas","co2.fuel.bio","co2.energy","co2.transport", "co2.industry",'+
                   '"co2.others", "co2.cement", "co2.background",'+
                   '"co.stilt","co.fuel","co.bio","co.fuel.coal","co.fuel.oil",'+
                   '"co.fuel.gas","co.fuel.bio","co.energy","co.transport", "co.industry",'+
                   '"co.others", "co.cement", "co.background",'+
                   '"rn", "rn.era","rn.noah","wind.dir","wind.u","wind.v","latstart","lonstart"]')
        data = '{"columns": '+columns+', "fromDate": "'+fromDate+'", "toDate": "'+toDate+'", "stationId": "'+station+'"}'
        #print (data)
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 500:
            #print (response.json())
            output=np.asarray(response.json())
            df = pd.DataFrame(output[:,:], columns=eval(columns))
            df = df.replace('null',np.NaN)
            df = df.astype(float)
            df['date'] = pd.to_datetime(df['isodate'], unit='s')
            df.set_index(['date'],inplace=True)
            df['name'] = station
            df['model'] = 'STILT'
            df['wind.speed']=np.sqrt((df['wind.u']**2)+(df['wind.v']**2))
            #print (df.columns)
    else:
        df=pd.DataFrame({'A' : []})

    df=df[(df['co2.fuel'].index.hour.isin(timeselect_list))]

    return df

#given the input - create an updated pandas date range with only hours in timeselect_list
def date_range_hour_filtered(start_date, end_date, timeselect_list):
    
    date_range = pd.date_range(start_date, end_date, freq='3H')

    #depending on how many input (max 8 for 0 3 6 9 12 15 18 21), filter to include hours.
    for time_value in timeselect_list:
        if len(timeselect_list)==1:
            date_range = date_range[(timeselect_list[0] == date_range.hour)]
            #df_nine = df.loc[(timeselect_list[count_timeselect] == df.index.hour)]
        if len(timeselect_list)==2:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]
        if len(timeselect_list)==3:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)]

        if len(timeselect_list)==4:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)] | date_range[(timeselect_list[3] == date_range.hour)]

        if len(timeselect_list)==5:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)] | date_range[(timeselect_list[3] == date_range.hour)]\
            | date_range[(timeselect_list[4] == date_range.hour)]

        if len(timeselect_list)==6:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)] | date_range[(timeselect_list[3] == date_range.hour)]\
            | date_range[(timeselect_list[4] == date_range.hour)] | date_range[(timeselect_list[5] == date_range.hour)]

        if len(timeselect_list)==7:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)] | date_range[(timeselect_list[3] == date_range.hour)]\
            | date_range[(timeselect_list[4] == date_range.hour)] | date_range[(timeselect_list[5] == date_range.hour)]\
            | date_range[(timeselect_list[6] == date_range.hour)]
        
        if len(timeselect_list)==8:
            date_range = date_range[(timeselect_list[0] == date_range.hour)] | date_range[(timeselect_list[1] == date_range.hour)]  \
            | date_range[(timeselect_list[2] == date_range.hour)] | date_range[(timeselect_list[3] == date_range.hour)]\
            | date_range[(timeselect_list[4] == date_range.hour)] | date_range[(timeselect_list[5] == date_range.hour)]\
            | date_range[(timeselect_list[6] == date_range.hour)] | date_range[(timeselect_list[7] == date_range.hour)]
          
    #consider return timeselect
    return date_range

def import_landcover():
    all_corine_classes= Dataset(stcDataPath + 'all_corine_except_ocean.nc')

    #the "onceans_finalized" dataset is seperate: CORINE class 523 (oceans) did not extend beyond exclusive zone
    #complemented with Natural Earth data.
    #CORINE does not cover the whole area, "nodata" area is never ocean, rather landbased data.
    oceans_finalized= Dataset(stcDataPath + 'oceans_finalized.nc')

    #access all the different land cover classes in the .nc files:
    fp_111 = all_corine_classes.variables['area_111'][:,:]
    fp_112 = all_corine_classes.variables['area_112'][:,:]
    fp_121 = all_corine_classes.variables['area_121'][:,:]
    fp_122 = all_corine_classes.variables['area_122'][:,:]
    fp_123 = all_corine_classes.variables['area_123'][:,:]
    fp_124 = all_corine_classes.variables['area_124'][:,:]
    fp_131 = all_corine_classes.variables['area_131'][:,:]
    fp_132 = all_corine_classes.variables['area_132'][:,:]
    fp_133 = all_corine_classes.variables['area_133'][:,:]
    fp_141 = all_corine_classes.variables['area_141'][:,:]
    fp_142 = all_corine_classes.variables['area_142'][:,:]
    fp_211 = all_corine_classes.variables['area_211'][:,:]
    fp_212 = all_corine_classes.variables['area_212'][:,:]
    fp_213 = all_corine_classes.variables['area_213'][:,:]
    fp_221 = all_corine_classes.variables['area_221'][:,:]
    fp_222 = all_corine_classes.variables['area_222'][:,:]
    fp_223 = all_corine_classes.variables['area_223'][:,:]
    fp_231 = all_corine_classes.variables['area_231'][:,:]
    fp_241 = all_corine_classes.variables['area_241'][:,:]
    fp_242 = all_corine_classes.variables['area_242'][:,:]
    fp_243 = all_corine_classes.variables['area_243'][:,:]
    fp_244 = all_corine_classes.variables['area_244'][:,:]
    fp_311 = all_corine_classes.variables['area_311'][:,:]
    fp_312 = all_corine_classes.variables['area_312'][:,:]
    fp_313 = all_corine_classes.variables['area_313'][:,:]
    fp_321 = all_corine_classes.variables['area_321'][:,:]
    fp_322 = all_corine_classes.variables['area_322'][:,:]
    fp_323 = all_corine_classes.variables['area_323'][:,:]
    fp_324 = all_corine_classes.variables['area_324'][:,:]
    fp_331 = all_corine_classes.variables['area_331'][:,:]
    fp_332 = all_corine_classes.variables['area_332'][:,:]
    fp_333 = all_corine_classes.variables['area_333'][:,:]
    fp_334 = all_corine_classes.variables['area_334'][:,:]
    fp_335 = all_corine_classes.variables['area_335'][:,:]
    fp_411 = all_corine_classes.variables['area_411'][:,:]
    fp_412 = all_corine_classes.variables['area_412'][:,:]
    fp_421 = all_corine_classes.variables['area_421'][:,:]
    fp_422 = all_corine_classes.variables['area_422'][:,:]
    fp_423 = all_corine_classes.variables['area_423'][:,:]
    fp_511 = all_corine_classes.variables['area_511'][:,:]
    fp_512 = all_corine_classes.variables['area_512'][:,:]
    fp_521 = all_corine_classes.variables['area_521'][:,:]
    fp_522 = all_corine_classes.variables['area_522'][:,:]

    #CORINE combined with natural earth data for oceans:
    fp_523 = oceans_finalized.variables['ocean_ar2'][:,:]

    #have a variable that represents the whole area of the cell,
    #used to get a percentage breakdown of each corine class.
    fp_total_area = all_corine_classes.variables['area_stilt'][:,:]

    #19 aggregated classes (these are used in the current bar graphs but can be updated by each user)
    urban = fp_111+fp_112+fp_141+fp_142
    industrial = fp_131 + fp_133 + fp_121 
    road_and_rail = fp_122 
    ports_and_apirports= fp_123+fp_124
    dump_sites = fp_132
    staple_cropland_not_rice = fp_211 + fp_212 + fp_241 + fp_242 + fp_243
    rice_fields = fp_213
    cropland_fruit_berry_grapes_olives = fp_221 + fp_222 + fp_223
    pastures = fp_231
    broad_leaved_forest = fp_311
    coniferous_forest = fp_312
    mixed_forest = fp_313 + fp_244
    natural_grasslands = fp_321 + fp_322
    transitional_woodland_shrub= fp_323 + fp_324
    bare_natural_areas = fp_331 + fp_332 + fp_333 + fp_334
    glaciers_prepetual_snow = fp_335
    wet_area= fp_411 + fp_412 + fp_421 + fp_422
    inland_water_bodies = fp_423 + fp_511 + fp_512 + fp_521 + fp_522
    oceans = fp_523

    #added: the "missing area" is out of the CORINE domain. Alltogether add upp to "fp_total_area"
    out_of_domain=fp_total_area-oceans-inland_water_bodies-wet_area-glaciers_prepetual_snow-bare_natural_areas-transitional_woodland_shrub-natural_grasslands-mixed_forest-coniferous_forest-broad_leaved_forest-pastures-cropland_fruit_berry_grapes_olives-rice_fields-staple_cropland_not_rice-dump_sites-ports_and_apirports-road_and_rail-industrial-urban

    #further aggregated classes for the land cover wind polar graph and land cover bar graph
    urban_aggreg= urban + industrial + road_and_rail + dump_sites + ports_and_apirports
    cropland_aggreg= staple_cropland_not_rice + rice_fields + cropland_fruit_berry_grapes_olives
    forests= broad_leaved_forest + coniferous_forest + mixed_forest
    pastures_grasslands= pastures + natural_grasslands
    oceans=oceans
    other=transitional_woodland_shrub+bare_natural_areas+glaciers_prepetual_snow +wet_area + inland_water_bodies

    return out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other

def import_population_data():
    pop_data= Dataset(stcDataPath + 'point_with_pop_data.nc')
    fp_pop=pop_data.variables['Sum_TOT_P'][:,:]
    #fp_pop_lat=pop_data.variables['lat'][:]
    #fp_pop_lon=pop_data.variables['lon'][:]
    return fp_pop

def import_point_source_data():
    #point source:
    point_source_data= Dataset(stcDataPath+ 'final_netcdf_point_source_emission.nc')

    #emissions in kg/year in the variable "Sum_Tota_1"
    fp_point_source=point_source_data.variables['Sum_Tota_1'][:,:]

    #different from population data: can translate the emissions within each stilt cell to the effect it will have to the final CO2 concentrations at the stations.
    #just need to get it in the right unit (micromole/m2s) and multiply by the individual or aggregated footprints

    #divide by the molar weight in kg. 12 (C)+16(O)+16(O) =44 0.044 in kg. get number of moles of C this way. Want it in micromole though: 1 mole= 1000000 micromole
    fp_point_source_moles_C=fp_point_source/0.044

    #how many micro-mole is that? multiply by 1000000
    fp_point_source_micromoles_C=fp_point_source_moles_C*1000000

    #a NetCDF file with the grid size calues in m2
    f_gridarea = cdf.Dataset(stcDataPath + 'gridareaSTILT.nc')

    #area stored in "cell_area"
    gridarea = f_gridarea.variables['cell_area'][:]

    fp_point_source_m2= fp_point_source_micromoles_C/gridarea

    #how many micro moles let out per second (have yearly data)
    fp_point_source_m2_s= fp_point_source_m2/31536000
    
    return fp_point_source_m2_s

fp_point_source_m2_s = import_point_source_data()
fp_pop= import_population_data()


def date_and_time_string_for_title(date_range, timeselect_list):
    date_index_number=len(date_range) - 1
    
    timeselect_string=[str(value) for value in timeselect_list]
    timeselect_string=' '.join(timeselect_string)
    date_and_time_string=('\n' + str(date_range[0].year) + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
                + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' \
                + str(date_range[date_index_number].day)+ ', Hour(s): ' + timeselect_string+ '\n')
    return date_and_time_string

#function to generate maps with cells binned by defined intervals and direction
def nondirection_labels(bins, units):   
    labels = []
    
    #for the label - want bin before and after (range)
    for left, right in zip(bins[:-1], bins[1:]):
        
        #if the last object - everything above (>value unit)
        if np.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            
            #how the labels normally look (value - value unit)
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)

def compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def define_bins_maprose(km_intervals, bin_size):
        
    #the number of bins
    number_bins=round((5000/km_intervals),0)
    
    #start at 0 km of the station. Then append to this list
    interval_bins=[0]
    
    #ex 100, 200, 300 if km_intervals=100
    for number in range(1, int(number_bins)):
        interval_bins.append(km_intervals*number)
    
    #the last number is infinity - however far the domain stretches marks the end of the last bin.
    interval_bins.append(np.inf)
    
    #labels: not used in map - but used in the grouping
    interval_labels = nondirection_labels(interval_bins, units='km')

    #direction: using the input (degree_bin) to set the bins so that the first bin has "north (0 degrees) in the middle"
    #"from_degree" becomes a negative value (half of the degree value "to the left" of 0)
    from_degree=-(bin_size/2)

    #"to_degree" is a vale to indicate the last bins ending. Must check values all the way to 360 which means the last bin 
    #will go past 360 and later be joined with the "0" bin (replace function in next cell)
    to_degree= 360 + (bin_size/2) 

    #the bin_size is the "step". generate an array with all the direction bins
    dir_bins = np.arange(from_degree, (to_degree+1), bin_size)

    #the direction bin is the first bin + the next bin divided by two:
    dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2
    
    #return these values to use in the function map_representation_polar_graph
    return interval_bins, interval_labels, dir_bins, dir_labels

# function to convert station longitude and latitude (slat, slon) to indices of STILT model grid (ix,jy)
def lonlat_2_ixjy(slon,slat,mlon,mlat):
    #slon, slat: longitude and latitude of station
    #mlon, mlat: 1-dim. longitude and latitude of model grid
    ix = (np.abs(mlon-slon)).argmin()
    jy = (np.abs(mlat-slat)).argmin()
    return ix,jy



def plot_maps(myStation, field, title='', label='', linlog='linear', zoom='', 
              vmin=0.0001, vmax=None, colors='GnBu',pngfile=''): 

    station=myStation.stationId
    lon=myStation.lon
    lat=myStation.lat
    unit=myStation.settings['unit']
    if unit=='percent':
        unit='%'
    else:
        unit='absolute'

    
    fp_lon=myStation.fpLon
    fp_lat=myStation.fpLat
    
    
    mcolor='m'
    
    # Set scale for features from Natural Earth
    NEscale = '50m'

    # Create a feature for Countries at 1:50m from Natural Earth
    countries = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale=NEscale,
        facecolor='none')

    fig = plt.figure(figsize=(18,10))

    # set up a map
    ax = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
    img_extent = (fp_lon.min(), fp_lon.max(), fp_lat.min(), fp_lat.max())
    ax.set_extent([fp_lon.min(), fp_lon.max(), fp_lat.min(), fp_lat.max()],crs=ccrs.PlateCarree())
    ax.add_feature(countries, edgecolor='black', linewidth=0.3)

    cmap = plt.get_cmap(colors)
    
    cmap.set_under(color='white')  
    
    if linlog == 'linear':
        
        im = ax.imshow(field[:,:],interpolation=None,origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        cbar.set_label(label+'  '+unit)

    else:
        
        im = ax.imshow(np.log10(field)[:,:],interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        cbar.set_label(label+'  log$_{10}$ '+unit)
    
    #plt.title(title)
    
    ax.text(0.01, -0.25, 'min: %.2f' % np.min(field[:,:]), horizontalalignment='left',transform=ax.transAxes)
    ax.text(0.99, -0.25, 'max: %.2f' % np.max(field[:,:]), horizontalalignment='right',transform=ax.transAxes)
    
    #show station location if station is provided
    if station != '':

        ax.plot(lon,lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        
    zoom=str(zoom)
    if zoom != '':
        
        #grid cell index of station 
        ix,jy = lonlat_2_ixjy(lon,lat,fp_lon,fp_lat)
 
        # define zoom area 
        i1 = np.max([ix-35,0])
        i2 = np.min([ix+35,400])
        j1 = np.max([jy-42,0])
        j2 = np.min([jy+42,480])

        lon_z=fp_lon[i1:i2]
        lat_z=fp_lat[j1:j2]

        field_z=field[j1:j2,i1:i2]

        # set up a map
        ax = plt.subplot(1, 2, 2, projection=ccrs.PlateCarree())
        img_extent = (lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max())
        ax.set_extent([lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()],crs=ccrs.PlateCarree())
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)
    
        if linlog == 'linear':
            im = ax.imshow(field_z,interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
            cbar.set_label(label+'  '+unit)
        else:
            im = ax.imshow(np.log10(field_z),interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
            cbar.set_label(label+'  log$_{10}$ '+unit)

        #show station location if station is provided
        if station != '':
            ax.plot(lon,lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        #removed
        #plt.title(title)
        ax.text(0.01, -0.25, 'min: %.2f' % np.min(field[j1:j2,i1:i2]), horizontalalignment='left',transform=ax.transAxes)
        ax.text(0.99, -0.25, 'max: %.2f' % np.max(field[j1:j2,i1:i2]), horizontalalignment='right',transform=ax.transAxes)

    if len(pngfile)>0:        
        output_folder = myStation.settings['output_folder']        
        fig.savefig(output_folder + '/' + pngfile + '.pdf',dpi=100,bbox_inches='tight')
        
    return fig 
    
#or min_lat, max_lat, step (in degrees)    
def distances_from_point_to_grid_cells(station_lat, station_lon, grid_lat, grid_lon):
    
    x = [math.radians(station_lon-lon)*math.cos(math.radians(station_lat+lat)/2) for lat in grid_lat for lon in grid_lon]

    y = [math.radians(station_lat-lat) for lat in grid_lat for lon in grid_lon]

    distance=[math.sqrt((x[index]*x[index])+(y[index]*y[index])) * R for index in range(len(x))]
    
    #return list with distances.
    return distance

def degrees_from_point_to_grid_cells(station_lat, station_lon, grid_lat, grid_lon):
    
    degrees_0_360=[compass_bearing((station_lat, station_lon), (lat, lon)) for lat in grid_lat for lon in grid_lon]
        
    #return list with degrees
    return degrees_0_360


def polar_graph(myStation, rose_type, colorbar='gist_heat_r', zoom=''):   
    
    """
    function contained - can make shorter. not global. 
    """
    
    interval_bins=myStation.intervalBins
    interval_labels=myStation.intervalLabels
    dir_bins=myStation.dirBins
    dir_labels=myStation.dirLabels
    fp=myStation.fp
    unit=myStation.settings['unit']
    save_figs=myStation.settings['saveFigs']
    station_id=myStation.stationId
    
    #same function used to all three types of map
    if rose_type=='sensitivity':
        
        #only want to look at the aggregated footprint - not multiplied by anciallary datalayer 
        grid_to_display=fp
        
    elif rose_type=='point source contribution':
        
        grid_to_display=fp*fp_point_source_m2_s
        
    elif rose_type=='population sensitivity':
        
        grid_to_display=fp*fp_pop
        
    sens_value = []
    for sublist in grid_to_display[0].tolist():
        sens_value.extend(sublist)


    #putting it into a dataframe - to perform groupby etc
    df_sensitivity_map = pd.DataFrame()
    df_sensitivity_map['distance'] = myStation.distances
    df_sensitivity_map['sensitivity'] = sens_value
    df_sensitivity_map['degrees'] = myStation.degrees

    #for % later - sensitivity within certain bin (distance and direction)
    total_sensitivity= df_sensitivity_map['sensitivity'].sum()
    
    #binning - by the distace intervals and degree intervals. Summarize these. 
    rosedata_distance_binned=df_sensitivity_map.assign(Interval_bins=lambda df: pd.cut(df['distance'], bins=interval_bins, labels=interval_labels, right=True))

    rosedata_distance_degrees_binned=rosedata_distance_binned.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))
   
    #the 360 degree are the same as 0:
    rosedata_distance_degrees_binned=rosedata_distance_degrees_binned.replace({'Degree_bins': {360: 0}})

    #the combination of the distance and direction columns is used to create a unique column value for all cells
    #with certain direction/distance combination.
    #make it to string to be able to combine.
    rosedata_distance_degrees_binned['key']=rosedata_distance_degrees_binned['Interval_bins'].astype(str) + ' ' + rosedata_distance_degrees_binned['Degree_bins'].astype(str) 

    #group by the unique combination of direction and distance
    rosedata_distance_degrees_binned_unique_combo=rosedata_distance_degrees_binned.groupby(by=['key'], as_index=False)['sensitivity'].sum().reset_index()

    #merge between the 192000 cells and the "groupedby" values: each cell in a specific direction and distance will
    #get the sum of the cells in that same specific bin. Same color on the map corresponing to % or absolute sensitivity.
    #reset_index() creates a column with the original index of the dataframes that are joined. Needed to sort the dataframe
    #in the next spted because default is to sort by the key used. 
    rosedata_distance_degrees_binned_unique_combo_join=rosedata_distance_degrees_binned.reset_index().merge(rosedata_distance_degrees_binned_unique_combo, left_on='key', right_on='key', sort=False)

    #sort by the original index of the 192000 cells: 
    rosedata_distance_degrees_binned_unique_combo_join_sorted=rosedata_distance_degrees_binned_unique_combo_join.sort_values(by=['index_x'])

    #x is the "fist" (rosedata.merge) dataframe that was merged (the 192000 individual cells) 
    #y is the dataframe that is merged to the first. Both columns name "sensitivity". 
    #sensitivity_y is the merged data - the summarized sensitivity value for the whole bin (direction and distance bin)
    rosedata_distance_degrees_binned_unique_combo_join_sorted_list=rosedata_distance_degrees_binned_unique_combo_join_sorted['sensitivity_y'].tolist()

    #now starts the process of "packing it back up" so that it can be displayed as a map (same format as the netCDF files with 480
    #lists of lists - the first list is all tha values that has "the first" latitude value and all 400 different longitude values)
    #calculate the % sensitivity - can be changed to absolute sensitivity
    if unit=='percent':
        rosedata_distance_degrees_binned_unique_combo_join_sorted_list=[(sensitivity_value/total_sensitivity)*100 for sensitivity_value in rosedata_distance_degrees_binned_unique_combo_join_sorted_list]

    #the "netcdf simulation" (see text above)
    rosedata_distance_degrees_binned_unique_combo_join_sorted_list_of_lists=[]

    index=0
    while index<192000:
        index_to=index+400

        #for each list: need to grab the 400 values that are the combination of the same latitude value
        #but different longitude values
        rosedata_distance_degrees_binned_unique_combo_join_sorted_list_of_lists.append(rosedata_distance_degrees_binned_unique_combo_join_sorted_list[index:index_to])

        #start at the next 400 in the list in the next turn of the loop:
        index=index+400

    #numpy array works to display in map
    rosedata_distance_degrees_binned_unique_combo_join_sorted_list_of_lists_array=np.array(rosedata_distance_degrees_binned_unique_combo_join_sorted_list_of_lists) 

    if save_figs=='yes':
        
        if rose_type=='sensitivity':
            figure_number='_figure_1'
        if rose_type=='point source contribution':
            figure_number='_figure_2'
        if rose_type=='population sensitivity':
            figure_number='_figure_3'
            
        string_fig=station_id+figure_number
        
    else:
        string_fig=''
        
    caption=(unit.capitalize() + ' ' + rose_type + ' given direction and distance')
          
    polar_map=plot_maps(myStation, rosedata_distance_degrees_binned_unique_combo_join_sorted_list_of_lists_array, title=caption, label=rose_type, 
                   linlog='linear', zoom='', vmin=0.0001, vmax=None, colors=colorbar,pngfile=string_fig)
        
    return polar_map, caption

def land_cover_bar_graph_upd(myStation):
    
    station=myStation.stationId
    fp_lon=myStation.fpLon
    fp_lat=myStation.fpLat
    degrees=myStation.degrees
    fp=myStation.fp
    save_figs=myStation.settings['saveFigs']

    
    #get all the land cover data from netcdfs 
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()
    
    #land cover classes (imported in the land cover section):
    cropland_multiplied=fp*cropland_aggreg
    urban_multiplied=fp*urban_aggreg
    forests_multiplied=fp*forests
    pastures_grasslands_multiplied=fp*pastures_grasslands
    oceans_multiplied=fp*oceans
    other_multiplied=fp*other
    out_of_domain_multiplied=fp*out_of_domain
    
    cropland_values=[cropland_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    urban_values=[urban_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    forests_values=[forests_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    pastures_grasslands_values=[pastures_grasslands_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    oceans_values=[oceans_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    others_values=[other_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    out_of_domain_values=[out_of_domain_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
        
    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_cropland = pd.DataFrame({'landcover_vals': cropland_values,
                               'degrees': degrees,
                               'landcover_type':'Cropland'})
    
    df_urban = pd.DataFrame({'landcover_vals': urban_values,
                           'degrees': degrees,
                           'landcover_type':'Urban'})
    
    df_forests = pd.DataFrame({'landcover_vals': forests_values,
                           'degrees': degrees,
                           'landcover_type':'Forests'})
    
    df_pastures_grassland = pd.DataFrame({'landcover_vals': pastures_grasslands_values,
                           'degrees': degrees,
                           'landcover_type':'Pastures and grassland'})
    
    df_oceans = pd.DataFrame({'landcover_vals': oceans_values,
                           'degrees': degrees,
                           'landcover_type':'Oceans'})
    
    df_others = pd.DataFrame({'landcover_vals':  others_values,
                           'degrees': degrees,
                           'landcover_type':'Other'})
    
    df_out_of_domain = pd.DataFrame({'landcover_vals':  out_of_domain_values,
                           'degrees': degrees,
                           'landcover_type':'No data'})
    

    #into one dataframe
    df_all = df_cropland.append([df_urban, df_forests, df_pastures_grassland, df_oceans, df_others, df_out_of_domain])

    #not change with user input
    dir_bins = np.arange(22.5, 383.5, 45)
    dir_bins= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5,383.5])
    dir_labels= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5])

    #get columns - for each degree
    rosedata=df_all.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    rosedata=rosedata.replace({'Degree_bins': {0.0: 337.5}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata=rosedata.groupby(by=['landcover_type', 'Degree_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata=rosedata.unstack(level='landcover_type')

    #want to sort the dataframe so that the land cover the station is the most
    #sensitive to is first. 
    rosedata_sum=rosedata.sum() 
    rosedata_sum_sorted=rosedata_sum.sort_values(ascending=False)
    list_land_cover_names_sorted=list(rosedata_sum_sorted.index)
    rosedata=rosedata[list_land_cover_names_sorted]    

    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    total_all=sum(rosedata_sum)

    rosedata= rosedata.applymap(lambda x: x / total_all * 100)
     
    list_land_cover_values=[]
    for land_cover_type in list_land_cover_names_sorted:
        list_land_cover_values.append(rosedata[land_cover_type].values)
     
    matplotlib.rcParams.update({'font.size': 20})
    fig = plt.figure(figsize=(11,13)) 
    ax = fig.add_subplot(1,1,1)
    N = 8
    ind = np.arange(N)  
    width = 0.35       

    p1 = ax.bar(ind, list_land_cover_values[0], width, color=dictionary_color[list_land_cover_names_sorted[0]]['color'])
    p2 = ax.bar(ind, list_land_cover_values[1], width, color=dictionary_color[list_land_cover_names_sorted[1]]['color'],
                 bottom=list_land_cover_values[0])
    p3 = ax.bar(ind, list_land_cover_values[2], width, color=dictionary_color[list_land_cover_names_sorted[2]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1])
    p4 = ax.bar(ind, list_land_cover_values[3], width, color=dictionary_color[list_land_cover_names_sorted[3]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2])
    p5 = ax.bar(ind, list_land_cover_values[4], width, color=dictionary_color[list_land_cover_names_sorted[4]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3])
    p6 = ax.bar(ind, list_land_cover_values[5], width, color=dictionary_color[list_land_cover_names_sorted[5]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4])
    p7 = ax.bar(ind, list_land_cover_values[6], width, color=dictionary_color[list_land_cover_names_sorted[6]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5])

    #want to reverese the order (ex if oceans at the "bottom" in the graph - ocean label should be furthest down)
    handles=(p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0])

    index=0
    list_labels=[]
    for land_cover_name in list_land_cover_names_sorted:

        for_lable= (land_cover_name + ' (' + str("%.1f" % sum(list_land_cover_values[index])) + '%)')
        list_labels.append(for_lable)
        index=index+1

    labels=[textwrap.fill(text,20) for text in list_labels]

    plt.legend(handles[::-1], labels[::-1],bbox_to_anchor=(1, 0.4))
 
    plt.ylabel('Percent')
    
    
    #first one is not north (in rosedata - rather 22.5 to 67.5 (NE). 
    plt.xticks(ind, ('NE', 'E','SE', 'S', 'SW','W', 'NW', 'N'))

    ax.yaxis.grid(True)

    #the land cover bar graph going into the PDF has different dimensions
    if save_figs=='yes':
        
        output_folder = myStation.settings['output_folder']
        
        plt.ioff()
        #different figsize here for the PDF, all else the same as outout figure
        fig.set_size_inches(12, 11)
        pngfile=station+'_figure_7'
        fig.savefig(output_folder +'/'+pngfile+'.pdf',dpi=100, bbox_inches='tight')
        
    for_caption=('Land cover within average footprint aggregated by direction')


    fig.set_size_inches(11, 13)
    return fig, for_caption



#14 font before
def render_mpl_seasonal_table(myStation, data, station, save_figs, col_width=2, row_height=0.625, font_size=16,
             header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
             bbox=[0, 0, 1, 1], header_columns=0, 
             ax=None):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, colWidths=[3,2,2,2,2,2,4])

    mpl_table.auto_set_font_size(True)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])

    if save_figs=='yes':
        
        output_folder = myStation.settings['output_folder']

        pngfile=station+'_figure_6'
        fig.savefig(output_folder +'/' + pngfile + '.pdf',dpi=100, bbox_inches='tight')

    return fig

       
#seasonal variations table
def seasonal_table(myStation):

    #station_id
    station=myStation.stationId
    date_range=myStation.dateRange
    year=min(date_range).year
    save_figs=myStation.settings['saveFigs']
    
    #update here - already have this information in mystation
    #get the stilt information from stationChar class - to be updated.
    available_STILT= available_STILT_dictionary()

    #check what months available for the year (and December the year before - seasons rather than full year)
    months= available_STILT[station][str(year)]['months']
    years=available_STILT[station]['years']
    
    if str(year-1) in years:
        months_year_before = available_STILT[station][str(year-1)]['months'] 
    else:
        months_year_before=''
   
    #need there to be 12 months of data avaiable to move on with the code - create a table for whole year
    #the months + text
    if len(months)==13 and '12' in months_year_before:

        #all hours for the date ranges... could update with date_range_hour_filtered
        winter_date_range=pd.date_range(dt.datetime(year-1,12,1,0), (dt.datetime(year, 3, 1,0)-dt.timedelta(hours=3)), freq='3H')
        spring_date_range=pd.date_range(dt.datetime(year,3,1,0), (dt.datetime(year, 6, 1,0)-dt.timedelta(hours=3)), freq='3H')
        summer_date_range=pd.date_range(dt.datetime(year,6,1,0), (dt.datetime(year, 9, 1,0)-dt.timedelta(hours=3)), freq='3H')
        fall_date_range=pd.date_range(dt.datetime(year,9,1,0), (dt.datetime(year, 12, 1,0)-dt.timedelta(hours=3)), freq='3H')

        #the average footprints given the selected date range
        nfp_winter, fp_winter, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, winter_date_range)
        nfp_spring, fp_spring, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, spring_date_range)
        nfp_summer, fp_summer, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, summer_date_range)
        nfp_fall, fp_fall, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, fall_date_range)
        
        #want also the whole year - get from the footprints of the seasons.
        nfp_total = nfp_winter + nfp_spring + nfp_summer + nfp_fall
        
        part_winter = nfp_winter/nfp_total
        part_spring = nfp_spring/nfp_total
        part_summer = nfp_summer/nfp_total
        part_fall = nfp_fall/nfp_total
 
        
        fp_whole=(fp_winter*part_winter)+ (fp_spring*part_spring)+(fp_summer*part_summer)+(fp_fall*part_fall)
        
        sensitivity_whole = fp_whole[0].sum()
        
        sensitivity_diff_winter=((fp_winter[0].sum()/sensitivity_whole)*100)-100
        sensitivity_diff_spring=((fp_spring[0].sum()/sensitivity_whole)*100)-100
        sensitivity_diff_summer=((fp_summer[0].sum()/sensitivity_whole)*100)-100
        sensitivity_diff_fall=((fp_fall[0].sum()/sensitivity_whole)*100)-100

        #point source section
        point_source_whole=(fp_whole*fp_point_source_m2_s)[0].sum()

        pointsource_diff_winter=(((fp_winter*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100
        pointsource_diff_spring=(((fp_spring*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100
        pointsource_diff_summer=(((fp_summer*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100
        pointsource_diff_fall=(((fp_fall*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100

        #population section
        population_whole=(fp_whole*fp_pop)[0].sum()
        population_diff_winter=(((fp_winter*fp_pop)[0].sum()/population_whole)*100)-100
        population_diff_spring=(((fp_spring*fp_pop)[0].sum()/population_whole)*100)-100
        population_diff_summer=(((fp_summer*fp_pop)[0].sum()/population_whole)*100)-100
        population_diff_fall=(((fp_fall*fp_pop)[0].sum()/population_whole)*100)-100

        #get the modelled concentration values
        timeselect_list=[0, 3, 6, 9, 12, 15, 18, 21]
        df_winter = read_stilt_timeseries_upd(station, winter_date_range, timeselect_list)
        df_spring = read_stilt_timeseries_upd(station, spring_date_range, timeselect_list)
        df_summer = read_stilt_timeseries_upd(station, summer_date_range, timeselect_list)
        df_fall = read_stilt_timeseries_upd(station, fall_date_range, timeselect_list)

        #averages of the modelled concentration values.
        df_winter_mean=df_winter.mean()
        df_spring_mean=df_spring.mean()
        df_summer_mean=df_summer.mean()
        df_fall_mean=df_fall.mean()
        

        df_whole_mean=(df_winter_mean*part_winter)+(df_spring_mean*part_spring)+(df_summer_mean*part_summer)+(df_fall_mean*part_fall)
       
        
        gee_whole=df_whole_mean['co2.bio.gee']

        gee_diff_winter=((df_winter_mean['co2.bio.gee']/gee_whole)*100)-100
        gee_diff_spring=((df_spring_mean['co2.bio.gee']/gee_whole)*100)-100
        gee_diff_summer=((df_summer_mean['co2.bio.gee']/gee_whole)*100)-100
        gee_diff_fall=((df_fall_mean['co2.bio.gee']/gee_whole)*100)-100
        

        #respiration
        resp_whole=df_whole_mean['co2.bio.resp']

        resp_diff_winter=((df_winter_mean['co2.bio.resp']/resp_whole)*100)-100
        resp_diff_spring=((df_spring_mean['co2.bio.resp']/resp_whole)*100)-100
        resp_diff_summer=((df_summer_mean['co2.bio.resp']/resp_whole)*100)-100
        resp_diff_fall=((df_fall_mean['co2.bio.resp']/resp_whole)*100)-100

        #anthropogenic

        anthro_whole=df_whole_mean['co2.industry']+df_whole_mean['co2.energy']+ df_whole_mean['co2.transport']+ df_whole_mean['co2.others']

        anthro_diff_winter=(((df_winter_mean['co2.industry']+df_winter_mean['co2.energy']+ df_winter_mean['co2.transport']+ df_winter_mean['co2.others'])/anthro_whole)*100)-100
        anthro_diff_spring=(((df_spring_mean['co2.industry']+df_spring_mean['co2.energy']+ df_spring_mean['co2.transport']+ df_spring_mean['co2.others'])/anthro_whole)*100)-100
        anthro_diff_summer=(((df_summer_mean['co2.industry']+df_summer_mean['co2.energy']+ df_summer_mean['co2.transport']+ df_summer_mean['co2.others'])/anthro_whole)*100)-100
        anthro_diff_fall=(((df_fall_mean['co2.industry']+df_fall_mean['co2.energy']+ df_fall_mean['co2.transport']+ df_fall_mean['co2.others'])/anthro_whole)*100)-100


        year_var='Annual'
        df_seasonal_table = pd.DataFrame(columns=['Variable', year_var, 'Dec-Feb', 'Mar-May', 'Jun-Aug','Sep-Nov', 'Unit'], index=['Sensitivity', 'Population','Point source', 'GEE', 'Respiration', 'Anthropogenic'])
        

        df_seasonal_table.loc['Sensitivity'] = pd.Series({'Variable': 'Sensitivity', year_var:("%.2f" % sensitivity_whole), 'Dec-Feb':("%+.2f" % sensitivity_diff_winter+ '%'), 'Mar-May':("%+.2f" % sensitivity_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % sensitivity_diff_summer + '%'), 'Sep-Nov':("%+.2f" % sensitivity_diff_fall+ '%'), 'Unit': 'ppm / ($\mu$mol / m$^{2}$s)'})

        df_seasonal_table.loc['Population'] = pd.Series({'Variable': 'Population', year_var:("%.0f" % population_whole), 'Dec-Feb':("%+.2f" % population_diff_winter+ '%'), 'Mar-May':("%+.2f" % population_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % population_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % population_diff_fall+ '%'), 'Unit': 'pop*(ppm / ($\mu$mol / m$^{2}$s))'})

        
        df_seasonal_table.loc['Point source'] = pd.Series({'Variable': 'Point source', year_var:("%.2f" % point_source_whole), 'Dec-Feb':("%+.2f" % pointsource_diff_winter+ '%'), 'Mar-May':("%+.2f" % pointsource_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % pointsource_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % pointsource_diff_fall+ '%'), 'Unit': 'ppm'})


        df_seasonal_table.loc['GEE'] = pd.Series({'Variable': 'GEE','Unit': 'ppm (uptake)', year_var:("%.2f" % gee_whole), 'Dec-Feb':("%+.2f" % gee_diff_winter+ '%'), 'Mar-May':("%+.2f" % gee_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % gee_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % gee_diff_fall+ '%'), 'Unit': 'ppm (uptake)'})

        df_seasonal_table.loc['Respiration'] = pd.Series({'Variable': 'Respiration', year_var:("%.2f" % resp_whole), 'Dec-Feb':("%+.2f" % resp_diff_winter+ '%'), 'Mar-May':("%+.2f" % resp_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % resp_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % resp_diff_fall+ '%'), 'Unit': 'ppm'})


        df_seasonal_table.loc['Anthropogenic'] = pd.Series({'Variable': 'Anthropogenic', year_var:("%.2f" % anthro_whole), 'Dec-Feb':("%+.2f" % anthro_diff_winter+ '%'), 'Mar-May':("%+.2f" % anthro_diff_spring+ '%'), 
                                                              'Jun-Aug':("%+.2f" % anthro_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % anthro_diff_fall+ '%'), 'Unit': 'ppm'})


        caption = 'Seasonal variation during the start year of specified date range (including December of the year before to show meteorological seasons)'
        seasonal_table=render_mpl_seasonal_table(myStation, df_seasonal_table, station, save_figs, header_columns=0, col_width=2.5)
      
        return seasonal_table, caption
    #if not 12 months:
    else:        
        seasonal_table = None
        caption = 'No seasonal table, footprints are not available for the whole year'
        return seasonal_table, caption 
        
#land cover polar graph:
def define_bins_landcover_polar_graph(bin_size):
    
   
    #direction: using the input (bin_size) to set the bins so that the first bin has "north (0 degrees) in the middle"
    #"from_degree" becomes a negative value (half of the degree value "to the left" of 0)
    from_degree=-(bin_size/2)

    #"to_degree" is a vale to indicate the last bins ending. Must check values all the way to 360 which means the last bin 
    #will go past 360 and later be joined with the "0" bin (replace function in next cell)
    to_degree= 360 + (bin_size/2) 

    #the "degree_bin" is the "step".
    dir_bins = np.arange(from_degree, (to_degree+1), bin_size)

    #the direction bin is the first bin + the next bin divided by two:
    dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2
    
    return dir_bins, dir_labels

#given the directions (and number of them), get the direction of the bars and their width
#function used in the final step of generating a graph
def _convert_dir(directions, N=None):
    if N is None:
        N = directions.shape[0]
    barDir = directions * np.pi/180. - np.pi/N
    barWidth = 2 * np.pi / N
    return barDir, barWidth

def landcover_polar_graph(myStation):
    
    #station, date_range, timeselect, bin_size, label='', title='', percent_label='', save_figs=''
    station=myStation.stationId
    fp_lon=myStation.fpLon
    fp_lat=myStation.fpLat
    fp=myStation.fp
    save_figs=myStation.settings['saveFigs']
    bin_size=myStation.settings['binSize']
    degrees=myStation.degrees
    polargraph_label= myStation.settings['labelPolar']
    #get these first so answer that question right away for user (bin size in degrees)
    dir_bins, dir_labels=define_bins_landcover_polar_graph(bin_size=bin_size)
    
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()

    #land cover classes (imported in the land cover section):
    cropland_multiplied=fp*cropland_aggreg
    urban_multiplied=fp*urban_aggreg
    forests_multiplied=fp*forests
    pastures_grasslands_multiplied=fp*pastures_grasslands
    oceans_multiplied=fp*oceans
    other_multiplied=fp*other
    out_of_domain_multiplied=fp*out_of_domain

    cropland_values=[cropland_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    urban_values=[urban_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    forests_values=[forests_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    pastures_grasslands_values=[pastures_grasslands_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    oceans_values=[oceans_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    others_values=[other_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    out_of_domain_values=[out_of_domain_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]

   #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_cropland = pd.DataFrame({'landcover_vals': cropland_values,
                               'degrees': degrees,
                               'landcover_type':'Cropland'})
    
    df_urban = pd.DataFrame({'landcover_vals': urban_values,
                           'degrees': degrees,
                           'landcover_type':'Urban'})
    
    df_forests = pd.DataFrame({'landcover_vals': forests_values,
                           'degrees': degrees,
                           'landcover_type':'Forests'})
    
    df_pastures_grassland = pd.DataFrame({'landcover_vals': pastures_grasslands_values,
                           'degrees': degrees,
                           'landcover_type':'Pastures and grassland'})
    
    df_oceans = pd.DataFrame({'landcover_vals': oceans_values,
                           'degrees': degrees,
                           'landcover_type':'Oceans'})
    
    df_others = pd.DataFrame({'landcover_vals':  others_values,
                           'degrees': degrees,
                           'landcover_type':'Other'})
    
    df_out_of_domain = pd.DataFrame({'landcover_vals':  out_of_domain_values,
                           'degrees': degrees,
                           'landcover_type':'No data'})


    #into one dataframe
    df_all = df_cropland.append([df_urban, df_forests, df_pastures_grassland, df_oceans, df_others, df_out_of_domain])

    #already have the different land cover classes in one cell (no need to use "pandas.cut" to generate new column with information for groupby)
    #still need a column with the different direction bins - defined in last cell - to use for the groupby (slice)
    rosedata=df_all.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    #the 360 degrees are the same as 0:
    rosedata=rosedata.replace({'Degree_bins': {360: 0}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata=rosedata.groupby(by=['landcover_type', 'Degree_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata=rosedata.unstack(level='landcover_type')

    #want to sort the dataframe so that the land cover the station is the most
    #sensitive to is first. 
    rosedata_sum_per_class=rosedata.sum() 
    rosedata_sum_per_class_sorted=rosedata_sum_per_class.sort_values(ascending=False)
    list_land_cover_names_sorted=list(rosedata_sum_per_class_sorted.index)
    rosedata=rosedata[list_land_cover_names_sorted]    

    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    total_all=sum(rosedata_sum_per_class_sorted)
    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    rosedata= rosedata.applymap(lambda x: x / total_all * 100)
       
    directions = np.arange(0, 360, bin_size)

        
    matplotlib.rcParams.update({'font.size': 18})
    
    #want to be able to run it with input "rosedata" several times without changing the variable
    rosedata_alt= rosedata.copy()
    
    #change the data so that each % values is mapped as area:
    #first step - make the "cumsum" value for each direction.
    #ex if the innermost value represent cropland, that remains, the next class 
    #will be that value + the cropland valueand so on...
    index=0
    #loop over all land cover classes except the fitst one (nothing to add to)
    for land_cover_class in list_land_cover_names_sorted[1:]:
        land_cover_before = list_land_cover_names_sorted[index]
        index=index+1
        rosedata_alt[land_cover_class]=rosedata_alt[land_cover_before].values + rosedata_alt[land_cover_class].values
        
    #the max radius is the max value in the last column (ex the "others" column 
    #if that one is the one with the smalles contribution = mapped the furthest 
    #from the station)
    max_radius=max(rosedata_alt[list_land_cover_names_sorted[-1]].values)

    #the area given the "max radius" (area of that slice by dividing it by number of directions)
    area_max=(math.pi*max_radius*max_radius)/len(directions)

    #all other values mapped in relation to this: 
    #first: what is the "area value" for specific class given the max area
    rosedata_alt=rosedata_alt.applymap(lambda x: (x/max_radius)*area_max)
    
    #second: given that area value, what is the radius? (=where it should be placed in the graph)
    rosedata_alt=rosedata_alt.applymap(lambda x: math.sqrt(x / math.pi))
         
    #bar direction and height
    bar_dir, bar_width = _convert_dir(directions)

    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(polar=True))
    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    
    def update_yticks(x, pos):
        area=x*x*math.pi
        area_part=area/area_max
        label=max_radius*area_part
        #value=math.sqrt(value/math.pi)
        
        return (str("%.2f" % label) + '%')
    
    def update_yticks_none(x, pos):
        
        return (str('')) 
    
    if polargraph_label=='yes':
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(update_yticks))

    #need this, else the labels will show up
    else:
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(update_yticks_none))

    labels=list_land_cover_names_sorted  
    #max 20 characters in lable - if more it will be on a new line
    labels=[textwrap.fill(text,20) for text in labels]
    
    first=True
    index=0
    #loop over all except the last one. 
    for land_cover_class in list_land_cover_names_sorted[:-1]:
        land_cover_after = list_land_cover_names_sorted[index+1]
        index=index+1
        
        if first:
            ax.bar(bar_dir, rosedata_alt[land_cover_class].values,
                   #bar width always the same --> depending on how many slices. Each slice same size.
                   width=bar_width,
                   color=dictionary_color[land_cover_class]['color'],
                   label=land_cover_class,
                   linewidth=0)
            first=False
        
        #values are accumulated
        ax.bar(bar_dir, (rosedata_alt[land_cover_after].values-rosedata_alt[land_cover_class].values), 
               width=bar_width, 
               #all the values "leading up" to this one. then add "the different (see above) on top
               bottom=rosedata_alt[land_cover_class].values,
               color=dictionary_color[land_cover_after]['color'],
               label=land_cover_after,
               linewidth=0)
       
    
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

    
    if save_figs=='yes':
        output_folder = myStation.settings['output_folder']
        
        ax.legend(labels, bbox_to_anchor=(1.9, 0.25), ncol=2)
        pngfile=station+'_figure_4'
        fig.savefig(output_folder + '/' + pngfile + '.pdf',dpi=100, bbox_inches='tight')

    for_caption=('Area corresponding to land cover sensitivity (%)')

    
    #different from the saved legend
    ax.legend(labels, bbox_to_anchor=(1.4, 0), ncol=1, loc=4)
    return fig, for_caption
    
    
#multiple variables graph

def compute_values_multiple_variable_graph_upd(all_stations, selected_station, date_range, timeselect_list, df_saved):

    df_new_values = pd.DataFrame(columns=['Station','Sensitivity','GEE','Respiration','Anthro','Point source','Population'])


    list_stations_without_footprints=[]
    index=0
    #need to compute for all stations that will be shown together with the "selected stations"
    for station in all_stations:
        
        #could use aggregated station footprint.
        #lon, lat, title not needed
        nfp, fp_station, lon, lat, title = read_aggreg_footprints(station, date_range)
        
        if nfp > 0:

            percent_footprints=(nfp/len(date_range))*100
            
            if percent_footprints<75:
 
                display(HTML('<p style="font-size:12px;">' + selected_station + ' (' + str(nfp) + '/' + str(len(date_range)) +' footprints)</p>'))       

            #total average sensitivity for specific station:
            average_sensitivity=fp_station[0].sum()

            #read the modelled concentration data - for anthro and bio values
            #using the updated version of read_stilt_timeseries allows for filtering out different hours of the days
            df_modelled_concentrations = read_stilt_timeseries_upd(station, date_range, timeselect_list)

            #averages of the values --> default skip nan
            df_mean=df_modelled_concentrations.mean()

            average_gee=df_mean['co2.bio.gee']

            average_respiration=df_mean['co2.bio.resp']

            #anthro:
            average_anthro=(df_mean['co2.industry']+df_mean['co2.energy']+ df_mean['co2.transport']+ df_mean['co2.others'])

            #point source for specific station 
            fp_pointsource_multiplied=fp_station*fp_point_source_m2_s
            average_pointsource=fp_pointsource_multiplied.sum()

            #population for specific station
            fp_pop_multiplied=fp_station*fp_pop
            average_population=fp_pop_multiplied.sum()
            
            df_new_values.loc[index] = [station, average_sensitivity, average_gee, average_respiration, average_anthro, average_pointsource, average_population]
            
            index=index+1
        
        else:
            
            list_stations_without_footprints.append(station)
            
            continue 

    #list the reference stations without footprints
    if len(list_stations_without_footprints)>0:
        
        stations_without_footprints_string = ', '.join(list_stations_without_footprints)
                 
        display(HTML('<p style="font-size:12px;">Reference stations without footprints and not included for the multiple variables graph: ' + stations_without_footprints_string + '</p>'))
        
    df_saved=pd.concat([df_saved, df_new_values], ignore_index=True)
    
    #these are returned to the function "multiple_variables_graph"
    return df_saved

      
def compute_normalized(df_saved_for_normalized, station, column, min_value, range_value):

    value=df_saved_for_normalized.loc[df_saved_for_normalized['Station'] == station, column]

    value=value.values[0]

    if value==min_value:
        value_normalized=0
        df_saved_for_normalized.loc[df_saved_for_normalized['Station'] == station, column]=0
    else:
        #min and range in dictionary to column? 
        #min GEE is the value with the highest contirubtion to co2. 
        if column=='GEE':
            
            value_normalized = ((abs(value)-abs(min_value))/range_value)*100
           
        else:
            
            value_normalized=((value-min_value)/range_value)*100
        df_saved_for_normalized.loc[df_saved_for_normalized['Station'] == station, column]=value_normalized

        
    return df_saved_for_normalized
            
def multiple_variables_graph(myStation):
    
    selected_station=myStation.stationId
    station_name=[myStation.stationName]
    timeselect_list=myStation.settings['timeOfDay']
    save_figs=myStation.settings['saveFigs']
    date_range=myStation.dateRange
    

    all_stations=['TRN180', 'SVB150', 'TOH147', 'SMR125', 'LUT', 'KRE250', 'IPR100', 'JFJ', 'KIT200', 'GAT344']
    
    if selected_station not in all_stations:
        all_stations.append(selected_station)
        
    start_date=min(date_range)
    end_date=max(date_range)

    #if the user selection is to use all footprints of 2017 or 2018, use saved values for all the 
    #reference stations (and a few more- all the stations used in Storm(2020))
    if start_date==pd.Timestamp(2018, 1, 1, 0) and end_date==pd.Timestamp(2018,12,31,0) and len(timeselect_list)==8:
        df_saved=pd.read_csv(stcDataPath + 'condensed_multiple_values_all_2018.csv')
        predefined=True
        
    elif start_date==pd.Timestamp(2017, 1, 1, 0) and end_date==pd.Timestamp(2017,12,31,0) and len(timeselect_list)==8:
        df_saved=pd.read_csv(stcDataPath + 'condensed_multiple_values_all_2017_upd.csv')
        predefined=True

    #if different date-range, need to compute variable values for all.
    else:
        
        #what would have gotten from saved file. Here create empty datafram which
        #will be appended to in compute_values_multiple_varaible_graph_upd
        df_saved=pd.DataFrame(columns=['Station','Sensitivity','GEE','Respiration','Anthro','Point source','Population'])
        
        #"all_stations" contains all reference stations as well as the selected station (possibly one of the reference stations). Selected station needed seperate also. 
        df_saved= compute_values_multiple_variable_graph_upd(all_stations, selected_station, date_range, timeselect_list, df_saved)
        
        predefined=False
           
    #if all of 2017 or all of 2018 (predefined) - create the list_of_lists_all mainly from the saved dataframes 
    if predefined:

        list_stations_from_saved=df_saved['Station'].tolist() 
  
        #check so all stations we want. defined in all_stations (+selected station if not in there)
        for station in all_stations:
            
            #if a station is not in the list with pre-computed data, need to compute it
            if station not in list_stations_from_saved:
                
                #also update df_saved... used for 1st, 2nd, 3rd quartile
                df_saved= compute_values_multiple_variable_graph_upd([station],selected_station,date_range, timeselect_list, df_saved)
          
    #only the selected station (and later append selected station if not already among the saved. 
    df_saved_upd = df_saved[df_saved['Station'].isin(all_stations)]
    
    #DONE GETTING ALL THE DATA: 
    #sensitivity is the first attribut (list_item[0]) in the each of the lists (one list per station)
    min_sens=min(df_saved_upd['Sensitivity'])
    range_sens=max(df_saved_upd['Sensitivity'])-min_sens

    #these lists (list_sensitivity, list_population, list_point_source) will be used to generate texts 
    #for the station characterization PDFs (if choose to create a PDF)
    #--> hence into list here, and not for GEE, respiration and anthropogenic contribution
    

    min_gee=max(df_saved_upd['GEE'])
    range_gee=abs(min_gee-min(df_saved_upd['GEE']))

    min_resp=min(df_saved_upd['Respiration'])
    range_resp=max(df_saved_upd['Respiration'])-min_resp
        
    min_anthro=min(df_saved_upd['Anthro'])
    range_anthro=max(df_saved_upd['Anthro'])-min_anthro
    
    min_pointsource=min(df_saved_upd['Point source'])
    range_pointsource=max(df_saved_upd['Point source'])-min_pointsource
    
    min_population=min(df_saved_upd['Population'])
    range_population=max(df_saved_upd['Population'])-min_population

    df_saved_for_normalized=df_saved_upd.copy()

    #for station in all_stations:
        
    for station in df_saved_for_normalized['Station']:
        
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Sensitivity', min_sens, range_sens)
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'GEE', min_gee, range_gee)
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Respiration', min_resp, range_resp)

        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Anthro', min_anthro, range_anthro)
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Point source', min_pointsource, range_pointsource)
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Population', min_population, range_population)

    #create the figure
    matplotlib.rcParams.update({'font.size': 14})
    fig = plt.figure(figsize=(10,9)) 
    ax = fig.add_subplot(111)

    #added - get on the right side of the plot
    ax.yaxis.tick_right()

    ax.yaxis.set_label_position("right")

    #remove the ticks (lenght 0 - keep the names)
    ax.tick_params(axis='both', which='both', length=0)
    
    #what will go as labels along the x-axis. Blank space next to station for more room. 
    list_attributes=['Station', '', 'Sensitivity', 'Population', 'Point source contribution', 'GEE (uptake)', 'Respiration', 'Anthropogenic contribution']

    #max 15 characters in lable
    list_attributes=[textwrap.fill(text,15) for text in list_attributes]

    #incremented for each station.. 0, 10, 20... etc. Where station name and "line" should start along the y-axis. 
    place_on_axis=0
    for station in df_saved_for_normalized['Station']:
        
        #get all the values for station (row in dataframe)
        station_values=df_saved_for_normalized.loc[df_saved_for_normalized['Station'] == station]

        #place them in the order we want them in the graph. List that will be used for the line. (one per station)
        station_values_list =[place_on_axis, place_on_axis, station_values['Sensitivity'].values[0], 
                              station_values['Population'].values[0], station_values['Point source'].values[0],
                              station_values['GEE'].values[0], station_values['Respiration'].values[0], 
                              station_values['Anthro'].values[0]]
        
        if station==selected_station:

            plt.plot(list_attributes, station_values_list, linestyle='-', marker='o', lw=3, color= 'black', label=station_name)
            
            #on 'Stationä position (along the x-axis). 
            #station_values_list[0] --> where on y-axis (place_on_axis). +1 for selected_station (bold text, need more room)
            ax.text('Station', station_values_list[0]+1, station)
            
        else:
            plt.plot(list_attributes, station_values_list, linestyle=':', lw=0.6, color= 'blue', label=station_name)
                  
            ax.text('Station', station_values_list[0], station)
        
        place_on_axis=place_on_axis+10

    ax.set_ylabel('% of max')

    ax.tick_params(axis='y')

    #vertical labels except "station" which also has different font
    list_attributes_upd=list_attributes
    list_attributes_upd[0]=''
    ax.set_xticklabels(list_attributes_upd, rotation='vertical')

    #label for station (furthest to the left in graph
    ax.text(0, -10, 'Station', fontsize=15,weight = 'bold')

    ax.yaxis.grid(True)


    if save_figs=='yes':
        
        output_folder = myStation.settings['output_folder']
        pngfile=station + '_figure_5'
        fig.savefig(output_folder+'/'+pngfile+'.pdf',dpi=100, bbox_inches='tight')
        
        columns_need_quartiles=['Sensitivity','Population','Point source']
        
        for column in columns_need_quartiles:
            
            #df saved - the original values. 
            quartile_df=df_saved[column].quantile([0.25,0.5,0.75])

            q1=quartile_df[0.25]
            q2=quartile_df[0.5]
            q3=quartile_df[0.75]
            
            value_selected_station = df_saved.loc[df_saved['Station'] == selected_station, column]
            value_selected_station= value_selected_station.values[0]
            
            if value_selected_station<q1:
                pdf_text='first quartile'
            elif value_selected_station>=q1 and value_selected_station<q2:
                pdf_text='second quartile'
            elif value_selected_station>=q2 and value_selected_station<q3:
                pdf_text='third quartile'
            else:
                pdf_text='fourth quartile'

            myStation.settings[column] = pdf_text

        settings_dict = myStation.settings
        
        settings_json = json.dumps(settings_dict, indent = 4)
        
        file_settings = output_folder + '/' + selected_station + '_settings.json'
        
        open_file= open(file_settings, "w")
        open_file.write(settings_json)
        open_file.close()
        
    caption=('Selected station relative to reference atmospheric stations')

    return fig, caption
