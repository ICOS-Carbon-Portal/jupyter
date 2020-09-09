# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 08:04:31 2020

@author: Ida Storm

Functions to run the station characterization notebook on exploredata.

"""


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
from icoscp.station import station as station_data

#for the widgets
from IPython.core.display import display, HTML 
from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress, GridspecLayout
from IPython.display import clear_output, display

# import required libraries
#%pylab inline
import netCDF4 as cdf
import pickle
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#stations that have footprints as well as year and months with footprints. Also altitude. 


#path to footprints
pathFP='/data/stiltweb/stations/'

#Earth's radius in km (for calculating distances between the station and cells)
R = 6373.8

#saved distances to the 192 000 cells for all the labeled atmospheric stations
#if the selected station is not found in this document, the distances are calculated
approved_stations_distances = pd.read_csv('approved_stations_distances.csv')

#saved degree angles from the stations to all 192 000 cells for all the labeled atmospheric stations
approved_stations_degrees = pd.read_csv('approved_stations_degrees.csv')

#functions from Ute 

#function to read and aggregate footprints for given time range
def read_aggreg_footprints(station, date_range, timeselect='all'):
    
    # loop over all dates and read netcdf files

    # path to footprint files in new stiltweb directory structure
    pathFP='/data/stiltweb/stations/'
    

    # print ('date range: ',date_range)
    fp=[]
    nfp=0
    first = True
    for date in date_range:
        filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')
        #print (filename)
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
        

    else:
        print ('no footprints found')
        

    #print (np.shape(fp))
    #print (np.max(fp))
    title = 'not used'
    #title = (start_date.strftime('%Y-%m-%d')+' - '+end_date.strftime('%Y-%m-%d')+'\n'+
     #        'time selection: '+timeselect)
    
    return nfp, fp, lon, lat, title

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
    
    #new:
    pathStations='/data/stiltweb/stations/'
    #pathStations='/opt/stiltdata/fsicos2/stiltweb/stations/'
    allStations = os.listdir(pathStations)

    # empty dictionary
    available = {}

    # fill dictionary with station name, years and months for each year
    for ist in sorted(list(set(allStations))):
        if os.path.exists(pathStations+'/'+ist):
            #print ('directory '+pathStations+'/'+ist+' exits')
            available[ist] = {}
            years = os.listdir(pathStations+'/'+ist)
            available[ist]['years'] = years
            for yy in sorted(available[ist]['years']):
                available[ist][yy] = {}
                months = os.listdir(pathStations+'/'+ist+'/'+yy)
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

    # print availability
    #for ist in sorted(available):
    #    print ('station:', ist)
    #    for k in available[ist]:
    #        print (k,':', available[ist][k])
    return available

def create_STILT_dictionary():
    # store all STILT station information in a dictionary 

    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract location from filename of link
    
    #UPDATE
    pathStations='/data/stiltweb/stations/'
    #pathStations='/opt/stiltdata/fsicos2/stiltweb/stations/'
    allStations = os.listdir(pathStations)

    # empty dictionary
    stations = {}

    # fill dictionary with ICOS station id, latitude, longitude and altitude
    for ist in sorted(list(set(allStations))):
        stations[ist] = {}
        # get filename of link (original stiltweb directory structure) 
        # and extract location information
        if os.path.exists(pathStations+ist):
            loc_ident = os.readlink(pathStations+ist)
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

    # print dictionary
    #for ist in sorted(stations):
    #    print ('station:', ist)
    #    for k in stations[ist]:
    #        print (k,':', stations[ist][k])

    # write dictionary to pickle file for further use
    pickle.dump( stations, open( "stationsDict.pickle", "wb" ) )

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
    pathFP='/data/stiltweb/stations/'
    new_range=[]
    
    for date in date_range:
        #--> new : pathStations='/data/stiltweb/stations/'
        #pathStations='/opt/stiltdata/fsicos2/stiltweb/stations/'
        if os.path.exists(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/'):
            new_range.append(date)
        #if os.path.exists('/opt/stiltdata/fsicos2/stiltweb/slots/'+stations[station]['locIdent']+'/'+str(zDate.year)+'/'+str(zDate.month).zfill(2)+'/'
         #           +str(zDate.year)+'x'+str(zDate.month).zfill(2)+'x'+str(zDate.day).zfill(2)+'x'+str(zDate.hour).zfill(2)+'/'):
          #  
        
        
        #filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
         #    +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')
        
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

#given the input - create a pandas date range
def date_range_station_char(start_date, end_date, timeselect_list):
    
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
    all_corine_classes= Dataset('all_corine_except_ocean.nc')

    #the "onceans_finalized" dataset is seperate: CORINE class 523 (oceans) did not extend beyond exclusive zone
    #complemented with Natural Earth data.
    #CORINE does not cover the whole area, "nodata" area is never ocean, rather landbased data.
    oceans_finalized= Dataset('oceans_finalized.nc')

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
    pop_data= Dataset('point_with_pop_data.nc')
    fp_pop=pop_data.variables['Sum_TOT_P'][:,:]
    
    return fp_pop

def import_point_source_data():
    #point source:
    point_source_data= Dataset('final_netcdf_point_source_emission.nc')

    #emissions in kg/year in the variable "Sum_Tota_1"
    fp_point_source=point_source_data.variables['Sum_Tota_1'][:,:]

    #different from population data: can translate the emissions within each stilt cell to the effect it will have to the final CO2 concentrations at the stations.
    #just need to get it in the right unit (micromole/m2s) and multiply by the individual or aggregated footprints

    #divide by the molar weight in kg. 12 (C)+16(O)+16(O) =44 0.044 in kg. get number of moles of C this way. Want it in micromole though: 1 mole= 1000000 micromole
    fp_point_source_moles_C=fp_point_source/0.044

    #how many micro-mole is that? multiply by 1000000
    fp_point_source_micromoles_C=fp_point_source_moles_C*1000000

    #a NetCDF file with the grid size calues in m2
    f_gridarea = cdf.Dataset('gridareaSTILT.nc')

    #area stored in "cell_area"
    gridarea = f_gridarea.variables['cell_area'][:]

    fp_point_source_m2= fp_point_source_micromoles_C/gridarea

    #how many micro moles let out per second (have yearly data)
    fp_point_source_m2_s= fp_point_source_m2/31536000
    
    return fp_point_source_m2_s

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

def calculate_initial_compass_bearing(pointA, pointB):
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
    to_degree= 360 + (bin_size/2) + 1

    #the bin_size is the "step". generate an array with all the direction bins
    dir_bins = np.arange(from_degree, to_degree, bin_size)

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

# function to plot maps (show station location if station is provided and zoom in second plot if zoom is provided)
def plot_maps(field, lon, lat, title='', label='', unit='', linlog='linear', station='', zoom='', 
              vmin=0.0001, vmax=None, colors='GnBu',pngfile=''): 

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
    img_extent = (lon.min(), lon.max(), lat.min(), lat.max())
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],crs=ccrs.PlateCarree())
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
    
    plt.title(title)
    
    ax.text(0.01, -0.25, 'min: %.2f' % np.min(field[:,:]), horizontalalignment='left',transform=ax.transAxes)
    ax.text(0.99, -0.25, 'max: %.2f' % np.max(field[:,:]), horizontalalignment='right',transform=ax.transAxes)
    
    #show station location if station is provided
    if station != '':
        station_lon=[]
        station_lat=[]
        station_lon.append(stations[station]['lon'])
        station_lat.append(stations[station]['lat'])
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        
    zoom=str(zoom)
    if zoom != '':
        
        #grid cell index of station 
        ix,jy = lonlat_2_ixjy(stations[zoom]['lon'],stations[zoom]['lat'],lon,lat)
 
        # define zoom area 
        i1 = np.max([ix-35,0])
        i2 = np.min([ix+35,400])
        j1 = np.max([jy-42,0])
        j2 = np.min([jy+42,480])

        lon_z=lon[i1:i2]
        lat_z=lat[j1:j2]

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
            station_lon=[]
            station_lat=[]
            station_lon.append(stations[station]['lon'])
            station_lat.append(stations[station]['lat'])
            ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        plt.title(title)
        ax.text(0.01, -0.25, 'min: %.2f' % np.min(field[j1:j2,i1:i2]), horizontalalignment='left',transform=ax.transAxes)
        ax.text(0.99, -0.25, 'max: %.2f' % np.max(field[j1:j2,i1:i2]), horizontalalignment='right',transform=ax.transAxes)
  
    plt.show()
    if len(pngfile)>0:
        plotdir='figures'
        if not os.path.exists(plotdir):
            os.mkdir(plotdir)
        
        fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=100,bbox_inches='tight')
        
    plt.close()
    
def map_representation_polar_graph(station, date_range, timeselect, bin_size, unit, rose_type='sensitivity', colorbar='gist_heat_r', km_intervals=200, zoom='', title='', save_figs=''):    
    
    #bins in terms of interval and direction
    interval_bins, interval_labels, dir_bins, dir_labels=define_bins_maprose(km_intervals=km_intervals, bin_size=bin_size)
    
    st_lon= stations[station]['lon']
    st_lat= stations[station]['lat']

    #get the aggregated footprint
    nfp, fp, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, date_range, timeselect=timeselect)     

    #if not saved distances to all 192000 cells, calculate it. 
    if station not in approved_stations_distances.columns:

        x = [math.radians(st_lon-lon)*math.cos(math.radians(st_lat+lat)/2) for lat in fp_lat for lon in fp_lon]

        y = [math.radians(st_lat-lat) for lat in fp_lat for lon in fp_lon]

        distance=[math.sqrt((x[index]*x[index])+(y[index]*y[index])) * R for index in range(len(x))]

    #if in the existing list, access it. 
    else:

        distance=approved_stations_distances[station]
        
    #same function used to all three types of map
    if rose_type=='sensitivity':
        
        #only want to look at the aggregated footprint - not multiplied by anciallary datalayer 
        grid_to_display=fp
        
    elif rose_type=='point source contribution':
        
        #import the point source data for multiplication with the aggregated footprint
        fp_point_source_m2_s = import_point_source_data()
        
        grid_to_display=fp*fp_point_source_m2_s
        
    elif rose_type=='population sensitivity':
        
        #import the population data for multiplication with the aggregated footprint
        fp_pop= import_population_data()
        
        grid_to_display=fp*fp_pop
        
    #list with 192000 sens values. same place in list for distance to sttion and degree 
    sens_value=[grid_to_display[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]

    #degrees - calculate at what degree each cell is in case not in saved list 
    if station not in approved_stations_degrees.columns:

        degrees_0_360=[calculate_initial_compass_bearing((st_lat, st_lon), (lat, lon)) for lat in fp_lat for lon in fp_lon]
    else:

        degrees_0_360=approved_stations_degrees[station]

    #putting it into a dataframe - to perform groupby etc
    df_sensitivity_map = pd.DataFrame()
    df_sensitivity_map['distance'] = distance
    df_sensitivity_map['sensitivity'] = sens_value
    df_sensitivity_map['degrees'] = degrees_0_360

    #for % later - sensitivity within certain bin (distance and direction)
    total_sensitivity= sum(df_sensitivity_map['sensitivity'])

    #binning - by the distace intervals and degree intervals. Summarize these. 
    rosedata=df_sensitivity_map.assign(WindSpd_bins=lambda df: pd.cut(df['distance'], bins=interval_bins, labels=interval_labels, right=True))

    rosedata=rosedata.assign(WindDir_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    #the 360 degree are the same as 0:
    rosedata=rosedata.replace({'WindDir_bins': {360: 0}})

    #the combination of the distance and direction columns is used to create a unique column value for all cells
    #with certain direction/distance combination.
    #make it to string to be able to combine.
    rosedata['key']=rosedata['WindDir_bins'].astype(str) +rosedata['WindSpd_bins'].astype(str) 

    #group by the unique combination of direction and distance
    rosedata_grouped_key=rosedata.groupby(by=['key'], as_index=False)['sensitivity'].sum().reset_index()

    #merge between the 192000 cells and the "groupedby" values: each cell in a specific direction and distnace will
    #get the sum of the cells in that same specific bin. Same color on the map corresponing to % or absolute sensitivity.
    #reset_index() creates a column with the original index of the dataframes that are joined. Needed to sort the dataframe
    #in the next spted because default is to sort by the key used. 
    rosedata_merge=rosedata.reset_index().merge(rosedata_grouped_key, left_on='key', right_on='key', sort=False)

    #sort by the original index of the 192000 cells: 
    rosedata_merge=rosedata_merge.sort_values(by=['index_x'])

    #x is the "fist" (rosedata.merge) dataframe that was merged (the 192000 individual cells) 
    #y is the dataframe that is merged to the first. Both columns name "sensitivity". 
    #sensitivity_y is the merged data - the summarized sensitivity value for the whole bin (direction and distance bin)
    rosedata_merge_list=rosedata_merge['sensitivity_y'].tolist()

    #now starts the process of "packing it back up" so that it can be displayed as a map (same format as the netCDF files with 480
    #lists of lists - the first list is all tha values that has "the first" latitude value and all 400 different longitude values)
    #calculate the % sensitivity - can be changed to absolute sensitivity
    if unit=='percent':
        rosedata_merge_list=[(sensitivity_value/total_sensitivity)*100 for sensitivity_value in rosedata_merge_list]

    #the "netcdf simulation" (see text above)
    rosedata_merge_list_of_lists=[]

    index=0
    while index<192000:
        index_to=index+400

        #for each list: need to grab the 400 values that are the combination of the same latitude value
        #but different longitude values
        rosedata_merge_list_of_lists.append(rosedata_merge_list[index:index_to])

        #start at the next 400 in the list in the next turn of the loop:
        index=index+400

    #numpy array works to display in map
    rosedata_merge_list_of_lists_array=np.array(rosedata_merge_list_of_lists) 

    #added
    date_index_number = (len(date_range) - 1)
    
    if title=='yes':
        for_title=('Station: ' + str(station) + '\n' + unit + ' ' + rose_type + ' given direction and distance: ' + '\n' + str(bin_size) + \
                   ' degree bins and ' + str(km_intervals) +' km increments'
                 '\n' + str(date_range[0].year) + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
                + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' + str(date_range[date_index_number].day)+\
              ' Hour(s): ' + timeselect+ '\n')
    else:
        for_title=''

    #font
    matplotlib.rcParams.update({'font.size': 12})

    if unit=='percent':
        unit='%'
    else:
        unit='absolute'


    if save_figs=='yes':
        
        if rose_type=='sensitivity':
            figure_number='_figure_1'
        if rose_type=='point source contribution':
            figure_number='_figure_2'
        if rose_type=='population sensitivity':
            figure_number='_figure_3'
            
        string_fig=station+figure_number
    else:
        string_fig=''


    #use the plot_maps function
    #need two different?
    if unit=='percent':
        plot_maps(rosedata_merge_list_of_lists_array, fp_lon, fp_lat, title=for_title, label=rose_type, 
                  unit=unit, linlog='linear', station=station, 
                  zoom=zoom, colors=colorbar, pngfile=string_fig)

    else:
        plot_maps(rosedata_merge_list_of_lists_array, fp_lon, fp_lat, title=for_title, label=rose_type, 
                  unit=unit, linlog='linear', station=station, 
                  zoom=zoom, colors=colorbar, pngfile=string_fig)


#land cover bar grapg:
def land_cover_bar_graph(station, date_range, timeselect, title='', save_figs=''):
    
    #get all the land cover data
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()
    
    approved_stations_degrees = pd.read_csv('approved_stations_degrees.csv')
    
    st_lon= stations[station]['lon']
    st_lat= stations[station]['lat']

    #selected date_range, aggregated footprint for selected station
    nfp, fp, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, date_range, timeselect=timeselect)
    
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

    #added: out_of_domain
    out_of_domain_values=[out_of_domain_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]

    approved_stations_degrees = pd.read_csv('approved_stations_degrees.csv')
    
    #degrees (no distance bins for land cover):
    if station not in approved_stations_degrees.columns:

        degrees_0_360=[calculate_initial_compass_bearing((st_lat, st_lon), (lat, lon)) for lat in fp_lat for lon in fp_lon]
    else:  
        degrees_0_360=approved_stations_degrees[station]
        
    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_cropland = pd.DataFrame()
    df_cropland['landcover_vals'] = cropland_values
    df_cropland['degrees'] = degrees_0_360
    df_cropland['landcover_type'] = 'Cropland'

    df_urban= pd.DataFrame()
    df_urban['landcover_vals'] = urban_values
    df_urban['degrees'] = degrees_0_360
    df_urban['landcover_type'] = 'Urban'

    df_forests = pd.DataFrame()
    df_forests['landcover_vals'] = forests_values
    df_forests['degrees'] = degrees_0_360
    df_forests['landcover_type'] = 'Forests'

    df_pastures_grassland = pd.DataFrame()
    df_pastures_grassland['landcover_vals'] = pastures_grasslands_values
    df_pastures_grassland['degrees'] = degrees_0_360
    df_pastures_grassland['landcover_type'] = 'Pastures and grassland'

    df_oceans = pd.DataFrame()
    df_oceans['landcover_vals'] = oceans_values
    df_oceans['degrees'] = degrees_0_360
    df_oceans['landcover_type'] = 'Oceans'

    df_others = pd.DataFrame()
    df_others['landcover_vals'] = others_values
    df_others['degrees'] = degrees_0_360
    df_others['landcover_type'] = 'Other'
    
    #out of domain
    df_out_of_domain = pd.DataFrame()
    df_out_of_domain['landcover_vals'] = out_of_domain_values
    df_out_of_domain['degrees'] = degrees_0_360
    df_out_of_domain['landcover_type'] = 'No data'


    #into one dataframe
    #possibly add: df_out_of_domain
    df_all = df_cropland.append([df_urban, df_forests, df_pastures_grassland, df_oceans, df_others, df_out_of_domain])

    #for % later - sensitivity to landcover within certain bin (landcover and direction)
    #how works now when have "no data" also? 
    total_all= sum(df_all['landcover_vals'])
    
    
    ##added - for the matplotlib breakdown
    dir_bins = np.arange(22.5, 383.5, 45)
    #dir_bins = np.asarray(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'])
    
    dir_bins= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5,383.5])
    
    #dir_labels= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5])
    dir_labels= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5])
    #dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2
    
    
    #get columns - for each degree
    rosedata=df_all.assign(WindDir_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    #the 360 degrees are the same as 0:
    #382.5 rather? 
    #not needed now - in the same class (?)
    rosedata=rosedata.replace({'WindDir_bins': {0.0: 337.5}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata=rosedata.groupby(by=['landcover_type', 'WindDir_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata=rosedata.unstack(level='landcover_type')

    #test - sort by totals. 
    total_by_col=[]
    columns=[]
    for column in rosedata.columns:
        columns.append(column)
        total_by_col.append(sum(rosedata[column].values))

    sorted_columns = [x for _,x in sorted(zip(total_by_col,columns), reverse=True)]

    rosedata=rosedata[sorted_columns]

    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    rosedata= rosedata.applymap(lambda x: x / total_all * 100)
    
    
    list_land_cover_name=[]
    list_land_cover_values=[]
    for n, (c1, c2) in enumerate(zip(rosedata.columns[:-1], rosedata.columns[1:])):

        # first column only
        if n == 0:
            list_land_cover_name.append(c1)

            list_land_cover_values.append(rosedata[c1].values)

        list_land_cover_name.append(c2)
        list_land_cover_values.append(rosedata[c2].values)
        
    matplotlib.rcParams.update({'font.size': 14})
    #create the bar graph:
    dictionary_color = {'Urban': {'color': 'red'}, 'Cropland':{'color':'darkgoldenrod'}, 'Oceans':{'color':'blue'}, 
                        'Forests':{'color':'green'}, 'Pastures and grassland':{'color':'yellow'}, 'Other':{'color':'black'}, 'No data':{'color': 'grey'}}

    fig = plt.figure(figsize=(11,10)) 

    ax = fig.add_subplot(1,1,1)

    N = 8

    ind = np.arange(N)  

    width = 0.35       


    p1 = ax.bar(ind, list_land_cover_values[0], width, color=dictionary_color[list_land_cover_name[0]]['color'])
    p2 = ax.bar(ind, list_land_cover_values[1], width, color=dictionary_color[list_land_cover_name[1]]['color'],
                 bottom=list_land_cover_values[0])

    p3 = ax.bar(ind, list_land_cover_values[2], width, color=dictionary_color[list_land_cover_name[2]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1])
    p4 = ax.bar(ind, list_land_cover_values[3], width, color=dictionary_color[list_land_cover_name[3]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2])
    p5 = ax.bar(ind, list_land_cover_values[4], width, color=dictionary_color[list_land_cover_name[4]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3])
    p6 = ax.bar(ind, list_land_cover_values[5], width, color=dictionary_color[list_land_cover_name[5]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+list_land_cover_values[4])
    p7 = ax.bar(ind, list_land_cover_values[6], width, color=dictionary_color[list_land_cover_name[6]]['color'],
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+list_land_cover_values[4]+list_land_cover_values[5])

    #want to reverese the order (ex if oceans at the "bottom" in the graph - ocean label should be furthest down)
    handles=(p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0])

    index=0
    list_labels=[]
    for land_cover_name in list_land_cover_name:

        for_lable= (land_cover_name + ' (' + str("%.1f" % sum(list_land_cover_values[index])) + '%)')
        list_labels.append(for_lable)
        index=index+1

    date_index_number = (len(date_range) - 1)
    if title=='yes':
        for_title=('Station: ' + str(station) + '\n' + 'Land cover within average footprint by direction'+
                 '\n' + str(date_range[0].year) + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
                + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' + str(date_range[date_index_number].day)+\
              ' Hour(s): ' + timeselect+ '\n')
    else:
        for_title=''

    labels=[textwrap.fill(text,20) for text in list_labels]
    #(1,-0.05)
    #1.3, 0.2
    #1,1
    plt.legend(handles[::-1], labels[::-1],bbox_to_anchor=(1, 0.33))
    #leg = ax.legend(labels, bbox_to_anchor=(1, -0.05), ncol=2)

    plt.ylabel('Percent')
    plt.title(for_title)
    
    #first one is not north (in rosedata - rather 22.5 to 67.5 (NE). 
    plt.xticks(ind, ('NE', 'E','SE', 'S', 'SW','W', 'NW', 'N'))

    ax.yaxis.grid(True)
    #plt.grid()

    plt.show()
    
    if save_figs=='yes':
        
        plotdir='figures'
        pngfile=station+'_figure_7'
        fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=100, bbox_inches='tight')

#seasonal variations table
def create_seasonal_table(station, year, save_figs=''):
    
    available_STILT= available_STILT_dictionary()
    
    #check what months available for the year
    months= available_STILT[station][str(year)]['months']

    #need there to be 12 months of data avaiable to move on with the code - create a table for whole year
    #the months + text
    if len(months)==13:
        start_date=dt.datetime(year,1,1,0)

        #can change end date here.
        end_date=dt.datetime(year+1, 12, 31,0)-dt.timedelta(hours=3)

        date_range = pd.date_range(start_date, end_date, freq='3H')


        winter_date_range=pd.date_range(dt.datetime(year,1,1,0), (dt.datetime(year, 4, 1,0)-dt.timedelta(hours=3)), freq='3H')
        spring_date_range=pd.date_range(dt.datetime(year,4,1,0), (dt.datetime(year, 7, 1,0)-dt.timedelta(hours=3)), freq='3H')
        summer_date_range=pd.date_range(dt.datetime(year,7,1,0), (dt.datetime(year, 10, 1,0)-dt.timedelta(hours=3)), freq='3H')
        fall_date_range=pd.date_range(dt.datetime(year,10,1,0), (dt.datetime(year+1, 1, 1,0)-dt.timedelta(hours=3)), freq='3H')

        #always all footprints, irregardless of what selection made. 
        timeselect='0, 3, 6, 9, 12, 15, 18, 21'

        #the average footprints given the selected date range
        #whole year to compare with 
        nfp, fp_whole, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, date_range, timeselect=timeselect)

        nfp, fp_winter, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, winter_date_range, timeselect=timeselect)

        nfp, fp_spring, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, spring_date_range, timeselect=timeselect)

        nfp, fp_summer, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, summer_date_range, timeselect=timeselect)

        nfp, fp_fall, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, fall_date_range, timeselect=timeselect)

        #sensitivity section
        sensitivity_whole=fp_whole[0].sum()

        sensitivity_diff_winter=((fp_winter[0].sum()/sensitivity_whole)*100)-100

        sensitivity_diff_spring=((fp_spring[0].sum()/sensitivity_whole)*100)-100

        sensitivity_diff_summer=((fp_summer[0].sum()/sensitivity_whole)*100)-100

        sensitivity_diff_fall=((fp_fall[0].sum()/sensitivity_whole)*100)-100


        #point source section
        fp_point_source_m2_s = import_point_source_data()

        point_source_whole=(fp_whole*fp_point_source_m2_s)[0].sum()

        pointsource_diff_winter=(((fp_winter*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100

        pointsource_diff_spring=(((fp_spring*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100

        pointsource_diff_summer=(((fp_summer*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100

        pointsource_diff_fall=(((fp_fall*fp_point_source_m2_s)[0].sum()/point_source_whole)*100)-100

        #population section

        fp_pop = import_population_data()
        
        population_whole=(fp_whole*fp_pop)[0].sum()

        population_diff_winter=(((fp_winter*fp_pop)[0].sum()/population_whole)*100)-100

        population_diff_spring=(((fp_spring*fp_pop)[0].sum()/population_whole)*100)-100

        population_diff_summer=(((fp_summer*fp_pop)[0].sum()/population_whole)*100)-100

        population_diff_fall=(((fp_fall*fp_pop)[0].sum()/population_whole)*100)-100

        #GEE
        timeselect_list=[0, 3, 6, 9, 12, 15, 18, 21]
        df_whole = read_stilt_timeseries_upd(station, date_range, timeselect_list)

        df_winter = read_stilt_timeseries_upd(station, winter_date_range, timeselect_list)
        df_spring = read_stilt_timeseries_upd(station, spring_date_range, timeselect_list)
        df_summer = read_stilt_timeseries_upd(station, summer_date_range, timeselect_list)
        df_fall = read_stilt_timeseries_upd(station, fall_date_range, timeselect_list)


        df_whole_mean=df_whole.mean()

        df_winter_mean=df_winter.mean()
        df_spring_mean=df_spring.mean()
        df_summer_mean=df_summer.mean()
        df_fall_mean=df_fall.mean()

        gee_whole=abs(df_whole_mean['co2.bio.gee'])

        gee_diff_winter=((abs(df_winter_mean['co2.bio.gee'])/gee_whole)*100)-100

        gee_diff_spring=((abs(df_spring_mean['co2.bio.gee'])/gee_whole)*100)-100

        gee_diff_summer=((abs(df_summer_mean['co2.bio.gee'])/gee_whole)*100)-100

        gee_diff_fall=((abs(df_fall_mean['co2.bio.gee'])/gee_whole)*100)-100

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



        df_seasonal_table = pd.DataFrame(columns=['Variable', str(year), 'Jan-Mar', 'Apr-Jun', 'Jul-Sep','Oct-Dec', 'Unit'], index=['Sensitivity', 'Population','Point source', 'GEE', 'Respiration', 'Anthropogenic'])


        df_seasonal_table.loc['Sensitivity'] = pd.Series({'Variable': 'Sensitivity', str(year):("%.2f" % sensitivity_whole), 'Jan-Mar':("%.2f" % sensitivity_diff_winter), 'Apr-Jun':("%.2f" % sensitivity_diff_spring), 
                                                              'Jul-Sep':("%.2f" % sensitivity_diff_summer), 'Oct-Dec':("%.2f" % sensitivity_diff_fall), 'Unit': 'ppm / ($\mu$mol / m$^{2}$s)'})

        df_seasonal_table.loc['Population'] = pd.Series({'Variable': 'Population', str(year):("%.0f" % population_whole), 'Jan-Mar':("%.2f" % population_diff_winter), 'Apr-Jun':("%.2f" % population_diff_spring), 
                                                              'Jul-Sep':("%.2f" % population_diff_summer), 'Oct-Dec':("%.2f" % population_diff_fall), 'Unit': 'pop*(ppm / ($\mu$mol / m$^{2}$s))'})

        
        df_seasonal_table.loc['Point source'] = pd.Series({'Variable': 'Point source', str(year):("%.2f" % point_source_whole), 'Jan-Mar':("%.2f" % pointsource_diff_winter), 'Apr-Jun':("%.2f" % pointsource_diff_spring), 
                                                              'Jul-Sep':("%.2f" % pointsource_diff_summer), 'Oct-Dec':("%.2f" % pointsource_diff_fall), 'Unit': 'ppm'})


        df_seasonal_table.loc['GEE'] = pd.Series({'Variable': 'GEE','Unit': 'ppm (uptake)', str(year):("%.2f" % gee_whole), 'Jan-Mar':("%.2f" % gee_diff_winter), 'Apr-Jun':("%.2f" % gee_diff_spring), 
                                                              'Jul-Sep':("%.2f" % gee_diff_summer), 'Oct-Dec':("%.2f" % gee_diff_fall), 'Unit': 'ppm (uptake)'})

        df_seasonal_table.loc['Respiration'] = pd.Series({'Variable': 'Respiration', str(year):("%.2f" % resp_whole), 'Jan-Mar':("%.2f" % resp_diff_winter), 'Apr-Jun':("%.2f" % resp_diff_spring), 
                                                              'Jul-Sep':("%.2f" % resp_diff_summer), 'Oct-Dec':("%.2f" % resp_diff_fall), 'Unit': 'ppm'})


        df_seasonal_table.loc['Anthropogenic'] = pd.Series({'Variable': 'Anthropogenic', str(year):("%.2f" % anthro_whole), 'Jan-Mar':("%.2f" % anthro_diff_winter), 'Apr-Jun':("%.2f" % anthro_diff_spring), 
                                                              'Jul-Sep':("%.2f" % anthro_diff_summer), 'Oct-Dec':("%.2f" % anthro_diff_fall), 'Unit': 'ppm'})


        display(HTML('<p style="font-size:16px;">Seasonal variation during the start year of specified date range </p>'))

        #14 font before
        def render_mpl_table(data, col_width=2, row_height=0.625, font_size=16,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
            if ax is None:
                size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
                fig, ax = plt.subplots(figsize=size)
                ax.axis('off')


            mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, colWidths=[4,2,2,2,2,2,5])
            #else:
            #mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, colWidths=[2,1.5,1.5,1.5,1.5,1.5,4.5])


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
                fig = ax.get_figure()
                plotdir='figures'
                pngfile=station+'_figure_6'

                #.pdf
                fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=100, bbox_inches='tight')

            plt.show(fig)

            
        render_mpl_table(df_seasonal_table, header_columns=0, col_width=2.5)
      
    #if not 12 months:
    else:
        
        display(HTML('<p style="font-size:12px;">Footprints not available for the whole year and therefore no seasonal variations table is shown</p>'))

#land cover polar graph:
def define_bins_landcover_polar_graph(bin_size):
    
    #spd_bins = ['Cropland', 'Urban', 'Forests', 'Pastures and grassland', 'Oceans', 'Others']

    #no need for a fuction for the labels this time.
    #possibly add 'No CORINE data'
    #spd_labels= ['Cropland', 'Urban', 'Forests', 'Pastures and grassland', 'Oceans', 'Others']

    #direction: using the input (degree_bin) to set the bins so that the first bin has "north (0 degrees) in the middle"
    #"from_degree" becomes a negative value (half of the degree value "to the left" of 0)
    from_degree=-(bin_size/2)

    #"to_degree" is a vale to indicate the last bins ending. Must check values all the way to 360 which means the last bin 
    #will go past 360 and later be joined with the "0" bin (replace function in next cell)
    to_degree= 360 + (bin_size/2) + 1

    #the "degree_bin" is the "step".
    dir_bins = np.arange(from_degree, to_degree, bin_size)

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


#similar to polar maps (don't need distance this time, and rather sensitivity one value for each land cover class.)
#group by land cover class rather than distance - sum of sensitivity*individual land cover class
def landcover_polar_graph(station, date_range, timeselect, bin_size, label='', title='', percent_label='', save_figs=''):
    
    #get these first so answer that question right away for user (bin size in degrees)
    
    dir_bins, dir_labels=define_bins_landcover_polar_graph(bin_size=bin_size)
    
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()

    st_lon= stations[station]['lon']
    st_lat= stations[station]['lat']

    #selected date_range, aggregated footprint for selected station
    nfp, fp, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, date_range, timeselect=timeselect)
    
    if nfp==0:
        print('no footprints: go to https://stilt.icos-cp.eu/worker/ to process footprints for desired date range')

    #land cover classes (imported in the land cover section):
    cropland_multiplied=fp*cropland_aggreg
    urban_multiplied=fp*urban_aggreg
    forests_multiplied=fp*forests
    pastures_grasslands_multiplied=fp*pastures_grasslands
    oceans_multiplied=fp*oceans
    other_multiplied=fp*other
    
    #added: out of domain
    out_of_domain_multiplied=fp*out_of_domain

    cropland_values=[cropland_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    urban_values=[urban_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    forests_values=[forests_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    pastures_grasslands_values=[pastures_grasslands_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    oceans_values=[oceans_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]
    others_values=[other_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]

    #added: out_of_domain
    out_of_domain_values=[out_of_domain_multiplied[0][lat_value][lon_value] for lat_value in range(len(fp_lat)) for lon_value in range(len(fp_lon))]

    approved_stations_degrees = pd.read_csv('approved_stations_degrees.csv')
    
    #degrees (no distance bins for land cover):
    if station not in approved_stations_degrees.columns:

        degrees_0_360=[calculate_initial_compass_bearing((st_lat, st_lon), (lat, lon)) for lat in fp_lat for lon in fp_lon]
    else:  
        degrees_0_360=approved_stations_degrees[station]

    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_cropland = pd.DataFrame()
    df_cropland['landcover_vals'] = cropland_values
    df_cropland['degrees'] = degrees_0_360
    df_cropland['landcover_type'] = 'Cropland'

    df_urban= pd.DataFrame()
    df_urban['landcover_vals'] = urban_values
    df_urban['degrees'] = degrees_0_360
    df_urban['landcover_type'] = 'Urban'

    df_forests = pd.DataFrame()
    df_forests['landcover_vals'] = forests_values
    df_forests['degrees'] = degrees_0_360
    df_forests['landcover_type'] = 'Forests'

    df_pastures_grassland = pd.DataFrame()
    df_pastures_grassland['landcover_vals'] = pastures_grasslands_values
    df_pastures_grassland['degrees'] = degrees_0_360
    df_pastures_grassland['landcover_type'] = 'Pastures and grassland'

    df_oceans = pd.DataFrame()
    df_oceans['landcover_vals'] = oceans_values
    df_oceans['degrees'] = degrees_0_360
    df_oceans['landcover_type'] = 'Oceans'

    df_others = pd.DataFrame()
    df_others['landcover_vals'] = others_values
    df_others['degrees'] = degrees_0_360
    df_others['landcover_type'] = 'Other'
    
    #out of domain
    df_out_of_domain = pd.DataFrame()
    df_out_of_domain['landcover_vals'] = out_of_domain_values
    df_out_of_domain['degrees'] = degrees_0_360
    df_out_of_domain['landcover_type'] = 'No data'


    #into one dataframe
    #possibly add: df_out_of_domain
    df_all = df_cropland.append([df_urban, df_forests, df_pastures_grassland, df_oceans, df_others, df_out_of_domain])

    #for % later - sensitivity to landcover within certain bin (landcover and direction)
    #how works now when have "no data" also? 
    total_all= sum(df_all['landcover_vals'])
    
    #already have the different land cover classes in one cell (no need to use "pandas.cut" to generate new column with information for groupby)
    #still need a column with the different direction bins - defined in last cell - to use for the groupby (slice)
    rosedata=df_all.assign(WindDir_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    #the 360 degrees are the same as 0:
    rosedata=rosedata.replace({'WindDir_bins': {360: 0}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata=rosedata.groupby(by=['landcover_type', 'WindDir_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata=rosedata.unstack(level='landcover_type')

    #test - sort by totals. 
    total_by_col=[]
    columns=[]
    for column in rosedata.columns:
        columns.append(column)
        total_by_col.append(sum(rosedata[column].values))

    sorted_columns = [x for _,x in sorted(zip(total_by_col,columns), reverse=True)]

    rosedata=rosedata[sorted_columns]

    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    rosedata= rosedata.applymap(lambda x: x / total_all * 100)
    
    #remove from here (maybe imported as just matplotlib?):
    #import matplotlib as mpl
    
    directions = np.arange(0, 360, bin_size)
    date_index_number = (len(date_range) - 1)
    
    if title=='yes':

        for_title=('Station: ' + str(station) + '\n' + 'Area corresponding to land cover sensitivity (%)' +
                 '\n'  + str(date_range[0].year) + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
                + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' + str(date_range[date_index_number].day)+\
              ' Hour(s): ' + timeselect+ '\n')
    else:
        for_title=''
    
    matplotlib.rcParams.update({'font.size': 14})
    
    #want to be able to run it with input "rosedata" several times without changing the variable
    rosedata_alt= rosedata.copy()
    
    #update with color for out of corine domain optional: 'No CORINE data':{'color':'red'}
    dictionary_color = {'Urban': {'color': 'red'}, 'Cropland':{'color':'darkgoldenrod'}, 'Oceans':{'color':'blue'}, 
                        'Forests':{'color':'green'}, 'Pastures and grassland':{'color':'yellow'}, 'Other':{'color':'black'}, 'No data':{'color': 'grey'}}
    
    colors=[]
    labels=[]
    
    for column in rosedata_alt.columns:
        colors.append(dictionary_color[column]['color'])
        
        #for_title = (station + ' at ' + str(date)+ '\n'+ 'Modelled CO2 concentration: ' + str("%.2f" % df['co2.stilt'][date]))
        #for_lable= (column + ' (' + str("%.1f" % sum_land_cover) + '%)')
        #want to only have the land cover types names. when have the other graph (land_cover_bar_graph)
        for_lable=column
        labels.append(for_lable)
        
    palette=colors
    
    #max 20 characters in lable - if more it will be on a new line
    labels=[textwrap.fill(text,20) for text in labels]
    
    #change the data so that each % values is mapped as area:
    #first step - make the "cumsum" value for each direction.
    #ex if the innermost value represent cropland, that remains, the next class will be that value + the cropland value
    #and so on...
    
    for col_number in range(1,len(rosedata_alt.columns)):
    
        rosedata_alt[rosedata_alt.columns[col_number]]=rosedata_alt[rosedata_alt.columns[col_number-1]].values+rosedata_alt[rosedata_alt.columns[col_number]].values
  
    #the max radius is the max value in the last column (ex the "others" column if that one is the one with the smalles contribution = mapped the furthest from the station)
    max_radius=max(rosedata_alt[rosedata_alt.columns[len(rosedata_alt.columns)-1]].values)
    
    #the area given the "max radius" (area of that slice by dividing it by number of directions)
    area_max=(math.pi*max_radius*max_radius)/len(directions)

    #all other values mapped in relation to this: 
    #first: what is the "area value" for specific class given the max area
    rosedata_alt=rosedata_alt.applymap(lambda x: (x/max_radius)*area_max)
    
    #second: given that area value, what is the radius? (=where it should be placed in the graph)
    rosedata_alt=rosedata_alt.applymap(lambda x: math.sqrt(x / math.pi))
         
    #bar direction and height
    bar_dir, bar_width = _convert_dir(directions)

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    
    #added - takes away the xaxis grid (showing directions- interfereces with the look of the division into slices)
    #ax.xaxis.grid(True,color='b',linestyle=':', linewidth=0)

    
    #can specify a max here (ex needed when compare season maps - make this interactive as optional input to this function):
    #ax.set_ylim(0,10)
    #matplotlib.rcParams.update({'font.size': 12})
    
    def update_yticks(x, pos):
        area=x*x*math.pi
        area_part=area/area_max
        label=max_radius*area_part
        #value=math.sqrt(value/math.pi)
        
        return (str("%.2f" % label) + '%')
    
    def update_yticks_none(x, pos):
        
        return (str(''))
    

    if percent_label=='yes':
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(update_yticks))
        #ax.get_yaxis().set_visible(True)
    else:
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(update_yticks_none))
        #ax.grid(True)
        #ax.set_yticklabels([])
        #ax.set_xticklabels([])
        #ax.get_yaxis().set_visible(False)
        #ax.yaxis.set_yticklabels([])
        
    
    #"the column before" (c1) and "the column after" (c2)
    for n, (c1, c2) in enumerate(zip(rosedata_alt.columns[:-1], rosedata_alt.columns[1:])):

        if n == 0:
            # first column only
            ax.bar(bar_dir, rosedata_alt[c1].values,

                   #bar width always the same --> depending on how many slices. Each slice same size.
                   width=bar_width,
                   #first column, first color
                   color=palette[0],
                   edgecolor='none',
                   label=c1,
                   linewidth=0)

        # all other columns
        ax.bar(bar_dir, (rosedata_alt[c2].values-rosedata_alt
                         [c1].values), 
               width=bar_width, 

               #all the values "leading up" to this one
               #bottom=rosedata_alt.cumsum(axis=1)[c1].values,
               bottom=rosedata_alt[c1].values,
               #n increases for each axis... n+1 is the next color
               color=palette[n+1],
               edgecolor='none',
               #"the one after" - first label is at 0. 
               label=c2,
               linewidth=0)
        

    leg = ax.legend(labels, bbox_to_anchor=(1.9, 0.25), ncol=2)
    xtl = ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

    
    #size = fig.get_size_inches()*fig.dpi
    ax.set_title(for_title)
    
    if save_figs=='yes':
        
        plotdir='figures'
        pngfile=station+'_figure_4'
        fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=100, bbox_inches='tight')
    

    plt.show(fig)
    
#multiple variables graph
    
def compute_values_multiple_variable_graph(all_stations, selected_station, date_range, timeselect_list, save_figs=''):

    stilt_stations=create_STILT_dictionary()
    list_stations=[]
    list_of_lists_all=[]

    list_stations_without_footprints=[]
    
    #need to compute for all stations that will be shown together with the "selected stations"
    for station in all_stations:

        #one list with all values per station
        list_all=[]

        #create aggregated footprint: use for multiplication by ancillary datasets (and get total average sensitivity)
        fp=[]
        nfp=0
        first = True


        #add processing of radiocarbon here 
        for date in date_range:

            filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')


            if os.path.isfile(filename):

                #get this date's foorptins
                f_fp = cdf.Dataset(filename)

                if (first):
                    fp=f_fp.variables['foot'][:,:,:]
                    first = False

                else:
                    fp=fp+f_fp.variables['foot'][:,:,:]
                f_fp.close()
                nfp+=1

        if nfp > 0:
            fp=fp/nfp
            #if "valid" station = append (ex has footprints )
            list_stations.append(station)

        else:
            
            list_stations_without_footprints.append(stilt_stations[station]['name'])
            
            continue 
            
        if nfp!=0:
            percent_footprints=(nfp/len(date_range))*100
            if percent_footprints<75:
                
                #if no name? 
                
                if len(stilt_stations[station]['name'])>0:
                    display(HTML('<p style="font-size:12px;">' + stilt_stations[station]['name'] + ' (' + str(nfp) + '/' + str(len(date_range)) +' footprints)</p>'))
                else: 
                    display(HTML('<p style="font-size:12px;">' + selected_station + ' (' + str(nfp) + '/' + str(len(date_range)) +' footprints)</p>'))
                    

        #total average sensitivity for specific station:
        total=fp[0].sum()

        #total sensitivity
        list_all.append(total)
        
        #read the modelled concentration data - for anthro and bio values
        #using the updated version of read_stilt_timeseries allows for filtering out different hours of the days
        df = read_stilt_timeseries_upd(station, date_range, timeselect_list)

        #averages of the values --> default skip nan
        df_mean=df.mean()


        average_gee=df_mean['co2.bio.gee']
        list_all.append(average_gee)

        average_respiration=df_mean['co2.bio.resp']
        list_all.append(average_respiration)

        #anthro:
        average_anthro=(df_mean['co2.industry']+df_mean['co2.energy']+ df_mean['co2.transport']+ df_mean['co2.others'])
        list_all.append(average_anthro)

        #import point source and population data from netcdf
        fp_pop= import_population_data()
        fp_point_source_m2_s = import_point_source_data()
        
        #point source for specific station 
        fp_pointsource_multiplied=fp*fp_point_source_m2_s
        sum_fp_pointsource_multiplied=fp_pointsource_multiplied.sum()
        list_all.append(sum_fp_pointsource_multiplied)

        #population for specific station
        fp_pop_multiplied=fp*fp_pop
        sum_fp_pop_multiplied=fp_pop_multiplied.sum()
        list_all.append(sum_fp_pop_multiplied)


        list_of_lists_all.append(list_all)
    
    #list the reference stations without footprints
    if len(list_stations_without_footprints)>0:
        
        stations_without_footprints_string = ', '.join(list_stations_without_footprints)
                 
        display(HTML('<p style="font-size:12px;">Reference stations without footprints and not included for the multiple variables graph: ' + stations_without_footprints_string + '</p>'))
       
    #these are returned to the function "multiple_variables_graph"
    return list_of_lists_all, list_stations
    
def multiple_variables_graph(all_stations, selected_station, station_name, date_range, start_date, end_date, timeselect_list, timeselect, title='', save_figs=''):
    
    #if the user selection is to use all footprints of 2017 or 2018, use saved values for all the 
    #reference stations (and a few more- all the stations used in Storm(2020))
    if start_date.year==2018 and start_date.month==1 and start_date.day==1 and end_date.year==2018 and end_date.month==12 and end_date.day==31 and len(timeselect_list)==8:
        df_saved=pd.read_csv('condensed_multiple_values_all_2018.csv')
        predefined=True
        
        
    elif start_date.year==2017 and start_date.month==1 and start_date.day==1 and end_date.year==2017 and end_date.month==12 and end_date.day==31 and len(timeselect_list)==8:
        df_saved=pd.read_csv('condensed_multiple_values_all_2017_upd.csv')
        predefined=True

    #if different date-range, compute these values.
    else:
        #"all_stations" contain all reference stations as well as the selected station (possibly one of the reference stations)
        list_of_lists_all, list_stations= compute_values_multiple_variable_graph(all_stations, selected_station, date_range, timeselect_list, save_figs=save_figs)
        
        predefined=False
           
    #if all of 2017 or all of 2018 - create the list_of_lists_all mainly from the saved dataframes 
    if predefined==True:
        
        #dataframe to list
        lists_from_csv=df_saved.values.tolist()

        #in list_of_lists_all, do not want the station names:
        list_of_lists_all=[list_item[1:] for list_item in lists_from_csv]

        #for the list of stations to loop over - only want the station names in a list
        list_stations=[list_item[0] for list_item in lists_from_csv]
        
        #check so all stations we want (defined in all_stations - not interactive currently)
        #are in the imported csv-file
        for station in all_stations:
            
            #if a station is not in the list with pre-computed data, need to compute it
            if station not in list_stations:
                
                #added "_extra" - don't want to replace the current lists
                list_of_lists_all_extra, list_stations_extra= compute_values_multiple_variable_graph([station],selected_station,date_range, timeselect_list, save_figs=save_figs)
                
                #only one value to append - don't want two lists
                list_stations.append(list_stations_extra[0])
                list_of_lists_all.append(list_of_lists_all_extra[0])
                
        #check so there are not any stations in the csv-file which are not in the all_stations list 
        index=0
        
        list_index_delete=[]
        
        for station_csv_list in list_stations:

            #if a station among the pre-computed values is not in the list of all_stations, it should be removed
            if station_csv_list not in all_stations:

                if station_csv_list!=selected_station[0]:

                    list_index_delete.append(index)
     
            index=index+1

        list_stations = [i for j, i in enumerate(list_stations) if j not in list_index_delete]
        
        list_of_lists_all = [i for j, i in enumerate(list_of_lists_all) if j not in list_index_delete]

    
    #DONE GETTING ALL THE DATA: 
    #now loop that generates the multiple variables graph
    #often only one loop - one graph. 
    for selected_station in selected_station:

        #sensitivity is the first attribut (list_item[0]) in the each of the lists (one list per station)
        min_sens=min([list_item[0] for list_item in list_of_lists_all])
        range_sens=max([list_item[0] for list_item in list_of_lists_all])-min_sens
        
        #these lists (list_sensitivity, list_population, list_point_source) will be used to generate texts 
        #for the station characterization PDFs (if choose to create a PDF)
        #--> hence into list here, and not for GEE, respiration and anthropogenic contribution
        list_sensitivity=[list_item[0] for list_item in list_of_lists_all]

        min_gee=min([abs(list_item[1]) for list_item in list_of_lists_all])
        range_gee=max([abs(list_item[1]) for list_item in list_of_lists_all])-min_gee

        min_resp=min([list_item[2] for list_item in list_of_lists_all])
        range_resp=max([list_item[2] for list_item in list_of_lists_all])-min_resp

        min_anthro=min([list_item[3] for list_item in list_of_lists_all])
        range_anthro=max([list_item[3] for list_item in list_of_lists_all])-min_anthro

        min_pointsource=min([list_item[4] for list_item in list_of_lists_all])
        range_pointsource=max([list_item[4] for list_item in list_of_lists_all])-min_pointsource
        list_point_source=[list_item[4] for list_item in list_of_lists_all]

        min_population=min([list_item[5] for list_item in list_of_lists_all])
        range_population=max([list_item[5] for list_item in list_of_lists_all])-min_population
        list_population=[list_item[5] for list_item in list_of_lists_all]


        list_of_lists_all_normalized=[]
        index=0
        for list_item in list_of_lists_all:

            
            #one list_normalized per station
            list_normalized=[]
            
            #for station x-ticks.
            #first station that is looped over end at the 0% placement on the y-axis
            if index==0:
                list_normalized.append(0)
            #the remaining stations end up gradually higher on the y-axis. Last station end at 100%.
            else:
                list_normalized.append((index/(len(list_of_lists_all)-1))*100)
            
            #for station - extra space (see x-ticks - spanning accross two ticks)
            #same value as above.
            if index==0:
                list_normalized.append(0)
            else:
                list_normalized.append((index/(len(list_of_lists_all)-1))*100)
            
            #if it is the station with the lowest sensitivity out of all reference stations (+selected station)
            #add 0 (the minimum value has 0% of the maximum value)
            if list_item[0]==min_sens:
                list_normalized.append(0)
            else:
                norm_sens=((list_item[0]-min_sens)/range_sens)*100
                list_normalized.append(norm_sens)

            #changed order here because want this order in the graph (list_item[5])
            if list_item[5]==min_population:
                list_normalized.append(0)
            else:
                norm_population=((list_item[5]-min_population)/range_population)*100
                list_normalized.append(norm_population)
                
            if list_item[4]==min_pointsource:
                list_normalized.append(0)
            else:
                norm_pointsource=((list_item[4]-min_pointsource)/range_pointsource)*100
                list_normalized.append(norm_pointsource)
                

            if abs(list_item[1])==min_gee:
                list_normalized.append(0)
            else:
                norm_gee=((abs(list_item[1])-min_gee)/range_gee)*100
                list_normalized.append(norm_gee)

            if list_item[2]==min_resp:
                list_normalized.append(0)
            else:
                norm_resp=((list_item[2]-min_resp)/range_resp)*100
                list_normalized.append(norm_resp)

            if list_item[3]==min_anthro:
                list_normalized.append(0)
            else:
                norm_anthro=((list_item[3]-min_anthro)/range_anthro)*100
                list_normalized.append(norm_anthro)

            list_of_lists_all_normalized.append(list_normalized)
            index=index+1

        list_attributes=['Station', '', 'Sensitivity', 'Population', 'Point source contribution', 'GEE', 'Respiration', 'Anthropogenic contribution']
        
        #max 15 characters in lable
        list_attributes=[textwrap.fill(text,15) for text in list_attributes]

        #create the figure
        matplotlib.rcParams.update({'font.size': 14})
        fig = plt.figure(figsize=(10,9)) 
        ax = fig.add_subplot(111)
        
        #added - get on the right side of the plot
        ax.yaxis.tick_right()

        ax.yaxis.set_label_position("right")
        
        #remove the ticks (lenght 0 - keep the names)
        ax.tick_params(axis='both', which='both', length=0)

        #get correct station information as loop though lists
        index=0
        max_sens_val=[]
        order=len(all_stations)-1
        
        first=True
        
        #add position for station in list_of_lists_all_normalized
        for each_station_list in list_of_lists_all_normalized:

            station=list_stations[index]

            if station==selected_station:
                
                #if at the same index...? Take all the population_sens values and all stations. Sort both. 
                #get what index the selected station is at. 

                plt.plot(list_attributes, each_station_list, linestyle='-', marker='o', lw=3, color= 'black', label=station_name, zorder=len(all_stations))

                max_sens_val.append(each_station_list[0])
                
                ax.text('Station', each_station_list[0]+1, station)

            else:
                if first==True:

                    plt.plot(list_attributes, each_station_list, linestyle=':', lw=0.5,color='blue', zorder=order, label='All other stations')
                    ax.text('Station', each_station_list[0], station)
                    
                else:
                    plt.plot(list_attributes, each_station_list, linestyle=':', lw=0.5,color='blue', zorder=order, label='_nolegend_')
                    ax.text('Station', each_station_list[0], station)

                    
                first=False

                order=order-1

            index=index+1

        handles, labels = ax.get_legend_handles_labels()


        if title=='yes':
            if predefined==False:
                date_index_number = (len(date_range) - 1)
                plt.title(selected_station  + ' relative to max of all atmospheric stations' + '\n' + str(date_range[0].year) \
                        + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
                        + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' + str(date_range[date_index_number].day)\
                        + ', Hour(s): ' + timeselect)
            else:
                plt.title(selected_station  + ' relative to max of all atmospheric stations' + '\n' + 'Year ' + str(start_date.year))

        ax.set_ylabel('% of max')

        ax.tick_params(axis='y')

        list_attributes_upd=list_attributes
        
        list_attributes_upd[0]=''
    
        ax.set_xticklabels(list_attributes_upd, rotation='vertical')
        
        #add text- station
        ax.text(0, -10, 'Station', fontsize=15,weight = 'bold')

        ax.yaxis.grid(True)
        
        #plt.legend()
        plt.show()
        
        if save_figs=='yes':
            
            plotdir='figures'
            pngfile=selected_station + '_figure_5'
            fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=110, bbox_inches='tight')   
            
            #save the texts:
            #values saved in the same order as list_stations
            list_stations_sorted_population = [x for _,x in sorted(zip(list_population,list_stations))]

            list_stations_sorted_sensitivity = [x for _,x in sorted(zip(list_sensitivity,list_stations))]

            list_stations_sorted_point_source = [x for _,x in sorted(zip(list_point_source,list_stations))]

            #ranking of the selected station (index)
            index_station_population=list_stations_sorted_population.index(selected_station)

            index_station_sensitivity=list_stations_sorted_sensitivity.index(selected_station)

            index_station_point_source=list_stations_sorted_point_source.index(selected_station)
            
            #get their ranking in % (lowest to highest)
            percent_population=((index_station_population+1)/len(list_stations))*100

            percent_sensitivity=((index_station_sensitivity+1)/len(list_stations))*100

            percent_point_source=((index_station_point_source+1)/len(list_stations))*100


            if percent_population<25:
                population_text='first quartile'
            elif percent_population>=25 and percent_population<50:
                population_text='second quartile'

            elif percent_population>=50 and percent_population<75:
                population_text='third quartile'
            else:
                population_text='fourth quartile'
            
            #got an error and worked to add this (something like "variable referenced before assigned")
            sensitivity_text=''
            if percent_sensitivity<25:
                sensitivity_text='first quartile'
            elif percent_sensitivity>=25 and percent_sensitivity<50:
                sensitivity_text='second quartile'

            elif percent_sensitivity>=50 and percent_sensitivity<75:
                sensitivity_text='third quartile'
            else:
                sensitivity_text=='fourth quartile'


            if percent_point_source<25:
                point_source_text_1='first quartile'
            elif percent_point_source>=25 and percent_point_source<50:
                point_source_text_1='second quartile'
            elif percent_point_source>=50 and percent_point_source<75:
                point_source_text_1='third quartile'
            else:
                point_source_text_1='fourth quartile'

            #create the text-files:
            file_sensitivity='texts/' + selected_station + '_text_7.txt'
            open_file= open(file_sensitivity, "w")
            open_file.write(sensitivity_text)
            open_file.close() 
 
            file_population='texts/' + selected_station + '_text_8.txt'
            open_file= open(file_population, "w")
            open_file.write(population_text)
            open_file.close() 

            file_point_source_1='texts/' + selected_station + '_text_9.txt'
            open_file= open(file_point_source_1, "w")
            open_file.write(point_source_text_1)
            open_file.close() 
            
# Create widgets for selection (ICOS data only)
def station_characterization_widget_selection():
     
    #for changes in the dropdowns for start- and end date
    stilt_stations = create_STILT_dictionary()
    available_STILT= available_STILT_dictionary()
    
    def change_stn_type(c):
        if station_type.value=='STILT stations':
            
            list_of_name_tuples=[]
            for station in stilt_stations:   
                if len(stilt_stations[station]['name'])>0:
                    
                    #if elevation already in the name, don't want to include it twide. Check is last part of string is 'm' for meter and a digit for the elevation
                    if stilt_stations[station]['name'][-1]=='m' and stilt_stations[station]['name'][-2].isdigit():
                        name_elevation=stilt_stations[station]['name'] 
                        
                    else:
                    
                        name_elevation= stilt_stations[station]['name'] + ' ' + str(stilt_stations[station]['alt']) +'m'
                    
                    name_tuple=(name_elevation, station)
                else:
                    name_elevation= station  + ' ' + str(stilt_stations[station]['alt']) +'m'
                    name_tuple=(name_elevation, station)
                list_of_name_tuples.append(name_tuple)
                
            station_choice.options=list_of_name_tuples
            station_choice.value=None
        else:
            
            station_choice.options=labeled_list_of_name_tuples
            station_choice.value=None
     

    def change_stn(c):
 
        if station_choice.value is not None:
     
            #same as station.value
            selected_station= station_choice.value

            options_station_specific=available_STILT[selected_station]['years']


            for i in range(0, len(options_station_specific)): 
                options_station_specific[i] = int(options_station_specific[i]) 

            options_station_specific=sorted(options_station_specific)


            s_year.options=options_station_specific


            e_year.options=options_station_specific
        

    def change_yr(c):

        #selected_station = [key for (key, value) in stilt_stations.items() if value['name'] == station.value]
        
        selected_station=station_choice.value
                                             
        #str(c['new']) replaced with str(s_year.value)
        months= available_STILT[selected_station][str(s_year.value)]['months']

        months_int=[]
        #last entry in the list of string is not a month
        for i in range(0, (len(months)-1)): 
            months_int.append(int(months[i]))

        months_int=sorted(months_int)

        s_month.options=months_int

        #when change start year - should also update end_year. Not earlier than the selected year

        options_station_specific=available_STILT[selected_station]['years']

        for i in range(0, len(options_station_specific)): 
            options_station_specific[i] = int(options_station_specific[i]) 

        options_station_specific=sorted(options_station_specific)

        #if the e_year value is smaller than the new start year value, it must be updated.
        #check if any of the options are smaller than selected start year
        updated_list=[]
        for item in s_year.options:
                                                 
            #c['new'] replaced with s_year.value 
            if item>=int(s_year.value):

                updated_list.append(item)

        e_year.options=updated_list


    def change_mt(c):

        #the day widget populated depending on what month it is (different number of days)
        #month_days_29=[2]

        month_days_30=[4,6,9,11]

        month_days_31=[1,3,5,7,8,10,12]

        if c['new'] in month_days_31:
            s_day.options=list(range(1,32))

        elif c['new'] in month_days_30:
            s_day.options=list(range(1,31))

        else:
            s_day.options=list(range(1,29))

        #when change start_month - change end month also (if same year)
        if s_year.value==e_year.value or len(e_month.options)==0:

            updated_list=[]
            for item in s_month.options:
                if item>=int(c['new']):

                    updated_list.append(item)

            e_month.options=updated_list

            
        #when change start_month - change end day also (if same year and month OR the first time)
        if s_year.value==e_year.value and s_month.value==e_month.value or len(e_day.options)==0:

            updated_list=[]
            for item in s_day.options:
                if item>=int(s_day.value):

                    updated_list.append(item)


            e_day.options=updated_list


    def change_yr_end(c):

        selected_station = [key for (key, value) in stilt_stations.items() if value['name'] == station_choice.value]

        #changed from c['new']
        if s_year.value==e_year.value:
            
            updated_list=[]

            for item in s_month.options:

                if item>=s_month.value:
                    updated_list.append(item)

            e_month.options=updated_list

        else:

            #available months given specified end year (different from start year) --> then all those months are up for choice!
            
            #changed str(c['new']) to e_year.value
            months= available_STILT[selected_station][str(e_year.value)]['months']

            months_int=[]
            
            #last entry in the list of string is not a month
            for i in range(0, (len(months)-1)): 
                months_int.append(int(months[i]))

            months_int=sorted(months_int)


            #get the available months for given year
            e_month.options=months_int

    def change_day(c):

        #when change the day... if the same month and year (start) - update
        if s_year.value==e_year.value and s_month.value==e_month.value:

            updated_list=[]

            for item in s_day.options:

                if item>=s_day.value:
                    updated_list.append(item)

            e_day.options=updated_list


    def change_month_end(c):

        if s_year.value==e_year.value and e_month.value==s_month.value:

            updated_list=[]

            for item in s_day.options:

                if item>=s_day.value:
                    updated_list.append(item)

            e_day.options=updated_list

        else:

            #month_days_29=[2]

            month_days_30=[4,6,9,11]

            month_days_31=[1,3,5,7,8,10,12]

            if c['new'] in month_days_31:
                e_day.options=list(range(1,32))

            elif c['new'] in month_days_30:
                e_day.options=list(range(1,31))

            else:
                e_day.options=list(range(1,29))


    #get the station codes of all atmospheric stations in the labelling app:
    stationList = station_data.getList(['as'])
    
    list_station_id=[]

    for station in stationList:
        list_station_id.append(station.stationId) 
        
    #which stilt stations have the first three letters mathcing those of the atmospheric stations (often several per height)
    list_labeled_stilt_stations=[]
    for station_id in list_station_id:

        for stilt_station in stilt_stations:
            if stilt_station[0:3]==station_id:
                list_labeled_stilt_stations.append(stilt_station)

    
    labeled_list_of_name_tuples=[]
    
    for station in list_labeled_stilt_stations:   
        if len(stilt_stations[station]['name'])>0:

            #if elevation already in the name, don't want to include it twice. Check is last part of string is 'm' for meter and a digit for the elevation
            if stilt_stations[station]['name'][-1]=='m' and stilt_stations[station]['name'][-2].isdigit():
                name_elevation=stilt_stations[station]['name'] 

            else:

                name_elevation= stilt_stations[station]['name'] + ' ' + str(stilt_stations[station]['alt']) +'m'

            name_tuple=(name_elevation, station)
        else:
            name_elevation= station  + ' ' + str(stilt_stations[station]['alt']) +'m'
            name_tuple=(name_elevation, station)
        labeled_list_of_name_tuples.append(name_tuple)

    
    #make it possible to see whole name in ex the text of a radio button 
    style_bin = {'description_width': 'initial'}
    
    #Create a Dropdown widget with station names:
    #maybe let it be coded (ex GAT344), but shown options 
    
    #added
    station_type=RadioButtons(
            options=['ICOS stations', 'STILT stations'],
            value='ICOS stations',
            description=' ',
            disabled=False)
    
    
    #prev: station_name_code_for_dropdown
    station_choice = Dropdown(options = labeled_list_of_name_tuples,
                       description = 'Station',
                       value=None,
                       disabled= False,)
    
    #Create a Dropdown widget with year values (start year):
    s_year = Dropdown(options = [],
                      description = 'Start Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (start month):
    s_month = Dropdown(options = [],
                       description = 'Start Month',
                       disabled= False,)
    
    #Create a Dropdown widget with year values (end year):
    e_year = Dropdown(options = [],
                      description = 'End Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (end month):
    e_month = Dropdown(options = [],
                       description = 'End Month',
                       disabled= False,)
    
    s_day = Dropdown(options = [],
                    description = 'Start Day',
                    disabled = False,)
    
    e_day = Dropdown(options = [],
                description = 'End Day',
                disabled = False,)
    
    options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]
    
    time_selection= SelectMultiple(
        options=options_time_selection,
        value=[0, 3, 6, 9, 12, 15, 18, 21],
        style=style_bin,
        description='Time of day',
        disabled=False)
    
    
    bin_size = Dropdown(options = [15, 30, 60, 90, 180, 360],
                description = 'Bin size (degrees)', style=style_bin,
                disabled = False,)

    interval = IntText(
            value=100,
            min=50,
            max=500,
            description='Interval (km)',
            disabled=False,
            step=50)
    
    
    #selection percent/absolut: 
    
    unit_value=RadioButtons(
            options=['percent', 'absolute'],
            value='percent',
            style=style_bin,
            disabled=False)
    
    #selection label landcover windrose: 
    
    landcover_windrose_label =RadioButtons(
            options=['yes', 'no'],
            value='yes',
            description='Add labels to the land cover polar graph:',
            style=style_bin,
            disabled=False)

    #selection include titles or not
    include_labels =RadioButtons(
            options=['yes', 'no'],
            value='yes',
            description='Add titles to the figures:',
            style=style_bin,
            disabled=False)
    

    save_figs=RadioButtons(
            options=['yes', 'no'],
            style=style_bin,
            value='no',
            description= 'Do you want to save the figures:',
            disabled=False)
    
    #generate pdf?
    
    #Create a Button widget to control execution:
    update_button = Button(description='Update',
                           disabled=False,
                           button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
    

    #this is just text that is put in a Vbox (vertical box) ABOVE (verticla) the station selection
    #("Select here station and time range")
    header_station = Output()
    with header_station:
        display(HTML('<p style="font-size:15px;font-weight:bold;">Select station: </p>'))
        
    header_date_time = Output()
    
    
    with header_date_time:
        display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date and time: </p>'))
        
    #added
    header_bin_specifications = Output()
    
    with header_bin_specifications:
        display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select bin size and intervals: </p>'))

    
    header_unit = Output()
    
    with header_unit:
        display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Unit: </p><p style="font-size:12px;width: 250px;">\
        Select representation of surface influence in <b>percent</b> for optimal display of a single station or <b>absolute</b> values for \
        intercomparison between stations </p>'))
                 
    header_style = Output()
    
    with header_style:
        display(HTML('<p style="font-size:15px;font-weight:bold;"><br><br></p>'))
        
    header_save_figs = Output()
    
    #to make it align with the other texts.
    with header_save_figs:
        display(HTML('<p style="font-size:15px;font-weight:bold;"><br><br></p>'))
            
    #vertical box with the heading (header_station) and the station dropdown
    station_box = VBox([header_station,station_type,station_choice, header_date_time])
    
    #NOTE vertical - start year above end year
    year_box = VBox([s_year, e_year])
    month_box = VBox([s_month, e_month])
    day_box = VBox([s_day, e_day])

    #the two vertical boxes next to each other in a horizontal box
    #Add both time-related VBoxes to a HBox:
    time_box = HBox([year_box, month_box, day_box])
    
    #added
    bin_box_1 = HBox([bin_size, interval])
    
    h_box_1 = HBox([header_unit, header_style])
    
    
    v_box_1 = VBox([header_unit, unit_value])
    
    v_box_2 = VBox([header_style, include_labels, landcover_windrose_label])
    
    v_box_3 = VBox([header_save_figs, save_figs, update_button])
    
    bin_box_2 = HBox([v_box_1, v_box_2, v_box_3])

    #Add all widgets to a VBox:
    form = VBox([station_box, time_box, time_selection, header_bin_specifications, bin_box_1,bin_box_2])

    #Set font of all widgets in the form:
    station_choice.layout.width = '603px'
    time_box.layout.margin = '25px 0px 10px 0px'
    year_box.layout.margin = '0px 0px 0px 0px'
    update_button.layout.margin = '50px 0px 0px 50px' #top, right, bottom, left
    royal='#4169E1'
    update_button.style.button_color=royal

    #Initialize form output:
    form_out = Output()

    #Initialize results output widgets:
    header_output = Output()
    
    result_sensitivity = Output()
    
    result_population = Output()
    
    result_pointsource = Output()
    
    result_land_cover_bar_graph = Output()
    
    result_seasonal_table = Output()
    
    header_advanced = Output()
    
    result_landcover_windrose = Output()
    
    result_multiple_variables_graph = Output()


    ########OBSERVERS - what happens when change ex. change start year (s_year)
    
    station_type.observe(change_stn_type, 'value')
    
    
    station_choice.observe(change_stn, 'value')


    s_year.observe(change_yr, 'value')


    s_month.observe(change_mt, 'value')


    e_year.observe(change_yr_end, 'value')


    s_day.observe(change_day, 'value')


    e_month.observe(change_month_end, 'value')
    
    
    #Define update function (happends when click the button)
    def update_func(button_c):
        
        #define a function instead - something change, change only in one place. 
        selected_station=station_choice.value
        
        station_code_stripped=selected_station[0:3]
        
        station_info = station_data.get(station_code_stripped)
        
        if station_info.valid==True:
            station_name=station_info.name
        else:
            station_name=stilt_stations[station_code_stripped]['name']
            
        
        start_date=dt.datetime(s_year.value,s_month.value,s_day.value,0)

        end_date=dt.datetime(e_year.value, e_month.value, e_day.value,0)

        timeselect_list=list(time_selection.value)
        
        date_range=date_range_station_char(start_date, end_date, timeselect_list)
        
        timeselect=[str(value) for value in timeselect_list]
        
        timeselect=' '.join(timeselect)
        
         
        #using Claudio's station class to reterive necessary station information that will go
        #in the station characterization PDFs
        if station_info.valid==True:

            station_lat=float(station_info.lat)

            station_lon=float(station_info.lon)

            station_country_code=station_info.country

            station_site_type=station_info.siteType

            if station_country_code is not None:

                #API to reterive country name using country code. 
                url='https://restcountries.eu/rest/v2/alpha/' + station_country_code

                resp = requests.get(url=url)

                country_information=resp.json()

                station_country=country_information['name']

            #text fits into the document. Long text because different with not an ICOS certified station
            #possibly check if not none

            #encapsulate as small as possible... top these are the variables I need. 
            station_class='a class ' + station_info.icosclass + ' ICOS atmospheric station of the type '

        #if not in labeling app - check stilt dictionary.
        else:

            #get what country the station is given latitude and longitude
            #used in reverse geocoding
            station_lat=float(stilt_stations[station_code_stripped]['lat'])

            station_lon=float(stilt_stations[station_code_stripped]['lon'])

            #reverse geocoding API - get country name from lat and lon
            url='https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=' + str(station_lat) + '&longitude=' + str(station_lon) + '12&localityLanguage=en'

            resp = requests.get(url=url)

            country_information=resp.json()

            station_country=country_information['countryName']

            #if not a certified ICOS station - save as empty strings. 
            #need to stay consistent because don't want errors when running latex.
            station_class=''

            station_site_type=''
            
        if save_figs.value=='yes':
            
            #check if folder "texts" exists, else create it. 
            if not os.path.exists('texts'):
                os.mkdir('texts')
            
            #save all the text files
            file_station_name='texts/' + selected_station + '_text_1.txt'
            open_file= open(file_station_name, "w")
            open_file.write(station_name)
            open_file.close() 
            
            file_station_class='texts/' + selected_station + '_text_2.txt'
            open_file= open(file_station_class, "w")
            open_file.write(str(station_class))
            open_file.close() 
    
            file_station_type='texts/' + selected_station + '_text_3.txt'
            open_file= open(file_station_type, "w")
            open_file.write(station_site_type)
            open_file.close() 
        
            file_station_country='texts/' + selected_station + '_text_4.txt'
            open_file= open(file_station_country, "w")
            open_file.write(station_country)
            open_file.close() 
                        
            file_station_lat='texts/' + selected_station + '_text_5.txt'
            open_file= open(file_station_lat, "w")
            open_file.write(str("%.2f" %station_lat))
            open_file.close() 
            
            file_station_lon='texts/' + selected_station + '_text_6.txt'
            open_file= open(file_station_lon, "w")
            open_file.write(str("%.2f" %station_lon))
            open_file.close()        
        

        
        with header_output:
            
            clear_output()
            
            #need to define this again?
            #selected_station=station_choice.value

            #station_code_stripped=selected_station[0:3]

            station_info = station_data.get(station_code_stripped)

            if station_info.valid==True:
                station_name=station_info.name
            else:
                station_name=stilt_stations[station_code_stripped]['name']
                
            degree_sign=u'\N{DEGREE SIGN}'
            
            if station_class!='':
                
                display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name + ' station characterization</p><p style="font-size:18px;"><br>'\
                + station_name + ' is a class ' + str(station_class) + station_site_type.lower() + \
                ' located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) + degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) +\
                degree_sign + 'E).</p>'))
            
            else:
                display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name + ' station characterization</p><p style="font-size:16px;">'\
                + station_name + ' is located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) + degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) +\
                degree_sign + 'E).</p>'))
            
            f = IntProgress(min=0, max=9, description='Loading:')

            display(f) 
            
            f.value += 1
        
        
        with result_sensitivity:
            
            clear_output()
            
            map_representation_polar_graph(selected_station, date_range, timeselect, bin_size=bin_size.value, unit=unit_value.value, 
                                        rose_type='sensitivity', colorbar='gist_heat_r', km_intervals=interval.value, title=include_labels.value,
                                       save_figs=save_figs.value)
            
 
            f.value += 1
            
            
        with result_pointsource:
     
            clear_output()
            
            map_representation_polar_graph(selected_station, date_range, timeselect, bin_size=bin_size.value, unit=unit_value.value, 
                                        rose_type='point source contribution', colorbar='Purples', km_intervals=interval.value, title=include_labels.value,
                                       save_figs=save_figs.value)
    
        
            f.value += 1
            
        with result_population:
     
            clear_output()
            
            map_representation_polar_graph(selected_station, date_range, timeselect, bin_size=bin_size.value, unit=unit_value.value, rose_type='population sensitivity', 
                                        colorbar='Greens', km_intervals=interval.value, title=include_labels.value,
                                       save_figs=save_figs.value)

            f.value += 1
            
            
        with result_land_cover_bar_graph:
            
            clear_output()
            
            land_cover_bar_graph(selected_station, date_range, timeselect, title=include_labels.value, save_figs=save_figs.value)
            
            f.value +=1
            
        with result_seasonal_table:
            clear_output()
            
            #timeselect automatically all hours
            create_seasonal_table(selected_station, s_year.value, save_figs=save_figs.value)
            
            f.value += 1
            
        with header_advanced:
            clear_output()
            
            display(HTML('<p style="font-size:35px;font-weight:bold;">Advanced figures</p><p style="font-size:16px;"><br>\
            We advice careful reading of the specifications before attempting to understand the following figures.</p>'))
            
        with result_landcover_windrose:
                     
            clear_output()

            landcover_polar_graph(selected_station, date_range, timeselect, bin_size=bin_size.value, title=include_labels.value, percent_label=landcover_windrose_label.value, save_figs=save_figs.value)
            
            f.value += 1
            
        with result_multiple_variables_graph:
            clear_output()
            
            #"reference stations" choosen by Ute
            all_stations=['TRN180', 'SVB150', 'TOH147', 'SMR125', 'LUT', 'KRE250', 'IPR100', 'JFJ', 'KIT200', 'GAT344']
            
            #if selected_station not in above list, append it.
            if selected_station not in all_stations:
                all_stations.append(selected_station)
                
            selected_station_list=[]
            selected_station_list.append(selected_station)
            multiple_variables_graph(all_stations, selected_station_list, station_name, date_range, start_date, end_date, timeselect_list, timeselect, title=include_labels.value, save_figs=save_figs.value)
            
            #result_multiple_variables_graph_code(selected_station, start_date, end_date)
            f.value = 9
                
    #Call update-function when button is clicked:
    update_button.on_click(update_func)
        
    #Open form object:
    with form_out:
        

        h_box_1=HBox([header_output])

        grid=GridspecLayout(2, 2)

        grid[0:1, 0:1] = result_sensitivity

        grid[0:1, 1:2] = result_population
        
        grid[1:2, 0:1] = result_pointsource
        
        grid[1:2, 1:2] = result_land_cover_bar_graph

        #table much "thinner" - make HBox rather than in grid 
        h_box_2=HBox([result_seasonal_table])
        
        #grid for the last two:
            
        h_box_3=HBox([header_advanced])
            
        grid_2 = GridspecLayout(1, 4)
        grid_2[0:1, 0:2] = result_landcover_windrose
        grid_2[0:1, 2:4] = result_multiple_variables_graph
        
        
    
        display(form, h_box_1, grid, h_box_2, h_box_3, grid_2)

    #Display form:
    display(form_out)
