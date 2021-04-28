import pandas as pd
import netCDF4 as cdf
import os
from netCDF4 import Dataset
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.pyplot as plt
import matplotlib
import requests
import seaborn
import folium
import branca

from bokeh.io import show, output_notebook, reset_output, export_png
from bokeh.plotting import figure as bokeh_figure
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend
from datetime import date as current_date
import datetime as dt
import math

#added (Dobj):
from icoscp.sparql import sparqls
from icoscp.sparql.runsparql import RunSparql
from icoscp.cpb.dobj import Dobj
from datetime import timedelta

#remove later when sparql query from Claudio:
from icoscp.station import station as station_data

#radiocarbon data from CP
from icoscp.sparql.runsparql import RunSparql

import json

import cartopy.feature as cfeature
import cartopy.crs as ccrs

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import stiltStations

folder_w_data = 'radiocarbon'
stiltstations = stiltStations.getStilt()
icoslist = sorted([(v['name'],k) for k,v in stiltstations.items() if v['icos']])

pathFP='/data/stiltweb/stations/'

#parameters used to estimate nuclear contamination.
Aabs = 0.238
#molar mass C in gram
Mc = 12

reset_output()
output_notebook()

from IPython.core.display import display, HTML
display(HTML("<style>.container { width:90% !important; }</style>"))

#GENERAL FUNCTIONS

#function to read and aggregate footprints for given date range
def read_aggreg_footprints(station, date_range):
  
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
                first=False
    
            else: 
                fp=fp+f_fp.variables['foot'][:,:,:]

            f_fp.close()
            nfp+=1

    
    if nfp > 0:
        fp=fp/nfp

        title = 'not used'
        
        return nfp, fp, lon, lat, title

    else:

        return 0, None, None, None, None
    
    
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

def read_stilt_timeseries(station,date_range):
    url = 'https://stilt.icos-cp.eu/viewer/stiltresult'
    headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}
    # check if STILT results exist
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
    return df

#nearest date takes a pandas timestamp (date_to_match) and a pandas date range or a list of timestamps (date_values)
#and return a the date among date_values that is the closest to the date_to_match
def nearest_date(date_values, date_to_match):
    return min(date_values, key=lambda x: abs(x - date_to_match))

    
def odd(n):
    nums = []
    for i in range(1, 2*n, 2):
        nums.append(i)
    return nums

def even(n):

    nums = []
    for i in range(2, ((2*n)+1), 2):
        nums.append(i)

    return nums


# DISPLAY MAPS WITH NUCLEAR FACILITIES AND THEIR EMISSIONS

#the dictionary is not used for the calculation of influence, only for display in maps (used in gui_overview_radiocarbon
#and in the map showing influence by facility - if option selected in gui_stilt)
dictionary_radiocarbon_emissions={(81,74): {'name': 'Almaraz', 'latitude': 39.808056, 'longitude': -5.696944, '2015':103.6, '2016':56.28, '2017': 30.52, '2018':47.88},
(98,124): {'name': 'Asco', 'latitude': 41.2, 'longitude': 0.569444, '2015':63, '2016':97.72, '2017': 121.52, '2018':57.4},
(174,143): {'name': 'Belleville', 'latitude': 47.509722, 'longitude': 2.875, '2015':468, '2016':396, '2017': 398, '2018':292},
(224,100): {'name': 'Berkeley', 'latitude': 51.6925, 'longitude': -2.493611, '2015':0.916, '2016':1.82, '2017': 1.92, '2018':0.514},
(200,187): {'name': 'Biblis A+B', 'latitude': 49.71, 'longitude': 8.415278, '2015':8.064, '2016':17.08, '2017': 46.48, '2018':51.24},
(147,114): {'name': 'Blayais', 'latitude': 45.255833, 'longitude': -0.693056, '2015':133, '2016':162.12, '2017': 154.28, '2018':219.52},
(185,261): {'name': 'Bohunice B', 'latitude': 48.494444, 'longitude': 17.681944, '2015':105.84, '2016':94.92, '2017': 115.92, '2018':138.04},
(221,149): {'name': 'Borssele', 'latitude': 51.430833, 'longitude': 3.718333, '2015':35.84, '2016':42.28, '2017': 43.96, '2018':33.32},
(224,127): {'name': 'Bradwell', 'latitude': 51.741389, 'longitude': 0.896944, '2015':13.7, '2016':30.3, '2017': 21.3, '2018':0.555},
(250,194): {'name': 'Brokdorf', 'latitude': 53.850833, 'longitude': 9.344722, '2015':320, '2016':340, '2017': 300, '2018':340},
(250,193): {'name': 'Brunsbüttel', 'latitude': 53.891667, 'longitude': 9.201667, '2015':0, '2016':2.3, '2017': 5.1, '2018':7.6},
(153,162): {'name': 'Bugey B', 'latitude': 45.798333, 'longitude': 5.270833, '2015':168.56, '2016':98.84, '2017': 122.92, '2018':166.32},
(196,169): {'name': 'Cattenom', 'latitude': 49.415833, 'longitude': 6.218056, '2015':869, '2016':761, '2017': 695, '2018':845},
(135,344): {'name': 'Cernavoda', 'latitude': 44.322222, 'longitude': 28.057222, '2015':475, '2016':332, '2017': 386, '2018':378},
(170,121): {'name': 'Chinon B', 'latitude': 47.2325, 'longitude': 0.1703, '2015':161.28, '2016':156.24, '2017': 152.6, '2018':159.32},
(205,158): {'name': 'Chooz B', 'latitude': 50.09, 'longitude': 4.789444, '2015':138.04, '2016':148.96, '2017': 136.92, '2018':46.76},
(161,125): {'name': 'Civaux', 'latitude': 46.456667, 'longitude': 0.652778, '2015':137.2, '2016':120.4, '2017': 73.36, '2018':61.04},
(74,111): {'name': 'Cofrentes', 'latitude': 39.216667, 'longitude': -1.05, '2015':200, '2016':339, '2017': 301, '2018':310},
(139,158): {'name': 'Cruas', 'latitude': 44.633056, 'longitude': 4.756667, '2015':146.72, '2016':156.52, '2017': 186.48, '2018':226.24},
(176,140): {'name': 'Dampierre', 'latitude': 47.733056, 'longitude': 2.516667, '2015':171.64, '2016':162.4, '2017': 250.04, '2018':238.56},
(193,249): {'name': 'Dukovany', 'latitude': 49.085, 'longitude': 16.148889, '2015':206.64, '2016':161.56, '2017': 177.24, '2018':203.28},
(214,127): {'name': 'Dungeness A+B', 'latitude': 50.913889, 'longitude': 0.963889, '2015':856.353, '2016':1010.284, '2017': 1270.954, '2018':1062.33},
(233,178): {'name': 'Emsland', 'latitude': 52.474231, 'longitude': 7.317858, '2015':84, '2016':56, '2017': 67.2, '2018':75.6},
(178,180): {'name': 'Fessenheim', 'latitude': 47.903056, 'longitude': 7.563056, '2015':304, '2016':199, '2017': 117, '2018':175},
(198,104): {'name': 'Flamanville', 'latitude': 49.536389, 'longitude': -1.881667, '2015':108.08, '2016':131.88, '2017': 92.68, '2018':87.36},
(328,265): {'name': 'Forsmark', 'latitude': 60.403333, 'longitude': 18.166667, '2015':1640, '2016':1620, '2017': 1675, '2018':1730},
(133,126): {'name': 'Golfech', 'latitude': 44.106667, 'longitude': 0.845278, '2015':124.88, '2016':131.88, '2017': 106.12, '2018':89.04},
(203,201): {'name': 'Grafenrheinfeld', 'latitude': 49.984086, 'longitude': 10.184669, '2015':64.4, '2016':15.4, '2017': 1.596, '2018':0.364},
(216,137): {'name': 'Gravelines', 'latitude': 51.015278, 'longitude': 2.136111, '2015':251.16, '2016':209.44, '2017': 280, '2018':313.6},
(228,195): {'name': 'Grohnde', 'latitude': 52.035278, 'longitude': 9.413333, '2015':84, '2016':86.8, '2017': 70, '2018':98},
(186,203): {'name': 'Gundremmingen A+B+C', 'latitude': 48.514722, 'longitude': 10.402222, '2015':850.053, '2016':240.37, '2017': 250.096, '2018':150.04},
(259,110): {'name': 'Hartlepool', 'latitude': 54.635, 'longitude': -1.180833, '2015':1810, '2016':1660, '2017': 2600, '2018':2230},
(252,96): {'name': 'Heysham 1+2', 'latitude': 54.028889, 'longitude': -2.916111, '2015':2730, '2016':3760, '2017': 3390, '2018':3490},
(218,94): {'name': 'Hinkley Point A+B', 'latitude': 51.208739, 'longitude': -3.133743, '2015':1480.457, '2016':1380.38, '2017': 1700.45, '2018':1530.54},
(272,80): {'name': 'Hunterston A+B', 'latitude': 55.722222, 'longitude': -4.89, '2015':1530.0577, '2016':1470.0564, '2017': 1970.0604, '2018':844.0655},
(271,332): {'name': 'Ignalina', 'latitude': 55.604444, 'longitude': 26.56, '2015':4.07, '2016':1.25, '2017': 1.15, '2018':3.82},
(187,218): {'name': 'Isar 1+2', 'latitude': 48.605606, 'longitude': 12.29315, '2015':64.8, '2016':58.1, '2017': 57.7, '2018':42.44},
(193,187): {'name': 'Karlsruhe WAK', 'latitude': 49.098902, 'longitude': 8.429527, '2015':1.5, '2016':3.5, '2017': 86, '2018':41},
(128,310): {'name': 'Kozloduy', 'latitude': 43.746111, 'longitude': 23.770556, '2015':177.8, '2016':190.96, '2017': 162.4, '2018':151.48},
(155,244): {'name': 'Krsko', 'latitude': 45.938333, 'longitude': 15.515556, '2015':22.008, '2016':33.04, '2017': 21.476, '2018':36.96},
(244,203): {'name': 'Krümmel', 'latitude': 53.41, 'longitude': 10.408889, '2015':1.3, '2016':1.2, '2017': 1.9, '2018':1.6},
(200,104): {'name': 'La Hague', 'latitude': 49.726337, 'longitude': -1.93951, '2015':20200, '2016':19100, '2017': 16600, '2018':18200},
(328,330): {'name': 'Loviisa', 'latitude': 60.372222, 'longitude': 26.347222, '2015':116.2, '2016':110.04, '2017': 99.4, '2018':99.68},
(183,267): {'name': 'Mochovce', 'latitude': 48.263889, 'longitude': 18.456944, '2015':441, '2016':356, '2017': 437, '2018':383},
(208,179): {'name': 'Mülheim-Kärlich', 'latitude': 50.408056, 'longitude': 7.49, '2015':0.28, '2016':0.91, '2017': 0.22, '2018':0.12},
(192,193): {'name': 'Neckarwestheim 1+2', 'latitude': 49.041667, 'longitude': 9.175, '2015':222.4, '2016':310.66, '2017': 250.27, '2018':200.22},
(186,148): {'name': 'Nogent', 'latitude': 48.515278, 'longitude': 3.517778, '2015':105.28, '2016':136.64, '2017': 89.04, '2018':90.16},
(196,192): {'name': 'Obrigheim', 'latitude': 49.364444, 'longitude': 9.076389, '2015':2.2, '2016':2, '2017': 0.59, '2018':0.19},
(223,99): {'name': 'Oldbury', 'latitude': 51.648889, 'longitude': -2.570833, '2015':1.9, '2016':0.72, '2017': 4.79, '2018':3.35},
(338,291): {'name': 'Olkiluoto', 'latitude': 61.236944, 'longitude': 21.440833, '2015':1070, '2016':1230, '2017': 1020, '2018':931},
(292,253): {'name': 'Oskarshamn', 'latitude': 57.415556, 'longitude': 16.671111, '2015':858, '2016':904, '2017': 736, '2018':662},
(162,270): {'name': 'Paks', 'latitude': 46.5725, 'longitude': 18.854167, '2015':167.44, '2016':182.84, '2017': 176.96, '2018':190.96},
(202,125): {'name': 'Paluel', 'latitude': 49.858056, 'longitude': 0.635556, '2015':203, '2016':129.92, '2017': 169.4, '2018':161},
(203,129): {'name': 'Penly', 'latitude': 49.976667, 'longitude': 1.211944, '2015':460, '2016':431, '2017': 483, '2018':629},
(195,187): {'name': 'Philippsburg 1+2', 'latitude': 49.2525, 'longitude': 8.436389, '2015':54.2, '2016':55.9, '2017': 60.1, '2018':102.8},
(291,216): {'name': 'Ringhals 1+2', 'latitude': 57.259722, 'longitude': 12.110833, '2015':565.92, '2016':590.88, '2017': 438.8, '2018':619.56},
(257,91): {'name': 'Sellafield', 'latitude': 54.425063, 'longitude': -3.504472, '2015':420, '2016':442, '2017': 416, '2018':427},
(230,132): {'name': 'Sizewell A+B', 'latitude': 52.215, 'longitude': 1.61972, '2015':71.18, '2016':65.51, '2017': 63.48, '2018':61.082},
(148,158): {'name': 'St Alban', 'latitude': 45.404444, 'longitude': 4.755278, '2015':122.36, '2016':114.8, '2017': 52.08, '2018':164.64},
(176,132): {'name': 'St Laurent B', 'latitude': 47.72, 'longitude': 1.5775, '2015':71.12, '2016':81.76, '2017': 92.12, '2018':81.2},
(194,235): {'name': 'Temelin', 'latitude': 49.18, 'longitude': 14.376111, '2015':163.52, '2016':155.68, '2017': 156.52, '2018':140.56},
(275,100): {'name': 'Torness', 'latitude': 55.96799, 'longitude': -2.40908, '2015':1280, '2016':1320, '2017': 1130, '2018':1330},
(239,88): {'name': 'Trawsfynydd', 'latitude': 52.924864, 'longitude': -3.948439, '2015':0.7, '2016':1, '2017': 1.15, '2018':1.09},
(135,157): {'name': 'Tricastin', 'latitude': 44.329722, 'longitude': 4.732222, '2015':167.72, '2016':138.88, '2017': 129.64, '2018':126.84},
(92,99): {'name': 'Trillo', 'latitude': 40.701111, 'longitude': -2.621944, '2015':42.28, '2016':41.72, '2017': 49, '2018':75.04},
(245,187): {'name': 'Unterweser', 'latitude': 53.4277, 'longitude': 8.480197, '2015':0.308, '2016':0.2128, '2017': 0.784, '2018':0.672},
(95,126): {'name': 'Vandellos 2', 'latitude': 40.951389, 'longitude': 0.866667, '2015':36.9600000406, '2016':13.412, '2017': 42.28, '2018':73.08},
(212,101): {'name': 'Winfrith', 'latitude': 50.682, 'longitude': -2.261, '2015':0.129, '2016':0.193, '2017': 0.146, '2018':0.119},
(245,84): {'name': 'Wylfa', 'latitude': 53.417, 'longitude': -4.483, '2015':954, '2016':104, '2017': 1.51, '2018':1.08},
(223,195): {'name': 'Würgassen', 'latitude': 51.639167, 'longitude': 9.391389, '2015':0, '2016':0.045, '2017': 0.046, '2018':0.043}}
            

def plotmap(stations, selected_facility, basemap, d_icon='cloud', icon_col='blue'):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Thu Jun 25 02:00:00 2020
    Last Changed:     Thu Jun 25 02:00:00 2020
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a list of station objects containing info about ICOS Stations
                      the 3-character long station code of a selected station, the basemap type, the
                      marker icon and the marker color as input and returns an interactive Folium Map, with
                      the location of the selected station highlighted in red. 
                      Folium (URL): https://python-visualization.github.io/folium/quickstart.html
                      
    Input parameters: 1. Dataframe with Information regarding ICOS Stations
                         (var_name: 'stations', var_type: List)
                      2. Station 3-character Code
                         (var_name: 'selected_station', var_type: String)
                      3. Type of basemap (e.g. OSM or imagery)
                         (var_name: 'basemap', var_type: String)
                      4. Marker icon name (domain specific)
                         (var_name: 'd_icon', var_type: String)
                      5. Marker color (domain specific)
                         (var_name: 'icon_col', var_type: String)

    Output:           Folium Map (Folium Map Object)
    
    """
    
    #Check what type of basemap is selected:
    if(basemap=='Imagery'):
        
        #Create folium map-object:
        m = folium.Map(location=[50.3785, 14.9706],
               zoom_start=4,
               tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
               attr = 'Esri',
               name = 'Esri Satellite',
               overlay = False,
               control = True)
        
    else:
        #Create folium map-object:
        m = folium.Map(
            location=[50.3785, 14.9706],
            zoom_start=4)

    #Add marker-tooltip:
    tooltip = 'Click to view station info'

    #keep in here since using items passed to the plotmap() function.
    def add_marker(map_obj, marker_txt, marker_color, lat_station, lon_station, name_station):

        #Add popup text:
        popup=folium.Popup(marker_txt,
                           parse_html=True,
                           max_width=400)

        
        #Create marker and add it to the map:
        folium.Marker(location=[lat_station,
                                lon_station],
                      popup=popup,
                      icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_stations.png'), icon_size=(16,25)),
                      tooltip=(name_station + ': station information')).add_to(map_obj)
        
    def add_marker_radiocarbon(map_obj, latitude, longitude, emission, marker_txt, name_facility, big_icon=False):
        
        popup=folium.Popup(marker_txt,
                       parse_html=True,
                       max_width=400)


        if big_icon:
            icon_size = (33,40)
                
        else:
            icon_size = (16.6,20)
        #Create marker and add it to the map:
        folium.Marker(location=[float(latitude),
                                float(longitude)],
                      popup=popup,
                      icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_nuclear_facilities.png'), icon_size=icon_size),
                      tooltip=(name_facility + ': click to see emissions')).add_to(map_obj)


    #Create markers for all stations except selected station:
    for st in stations.iterrows():
        

        #Get station info in html-format and add it to an iframe:
        #station_name and uri
        iframe = branca.element.IFrame(html=html_table_station(station=st[1][1],station_name=st[1][2],uri=st[1][0]), width=300, height=100)
        
    
        #Add marker for current station to map:
        add_marker(m, iframe, icon_col, lat_station=float(st[1][4]), lon_station=float(st[1][5]), name_station=st[1][2])
            
    for dictionary_item in dictionary_radiocarbon_emissions:
        
        #Get station info in html-format and add it to an iframe:
        iframe = branca.element.IFrame(html=html_table_radiocarbon(dictionary_item), width=300, height=200)
        
        
        latitude=dictionary_radiocarbon_emissions[dictionary_item]['latitude']
        
        longitude=dictionary_radiocarbon_emissions[dictionary_item]['longitude']
        
        emissions=dictionary_radiocarbon_emissions[dictionary_item]['2018']
        
        name_facility=dictionary_radiocarbon_emissions[dictionary_item]['name']
        
        if name_facility == selected_facility:
        
            add_marker_radiocarbon(m, latitude, longitude, emissions, iframe, name_facility, big_icon=True)
        else:
            
            add_marker_radiocarbon(m, latitude, longitude, emissions, iframe, name_facility, big_icon=False)

    #Show map:
    display(m)

def plotmap_static(atm_stations, year):
    figure(num=None, figsize=(18, 11), dpi=80, facecolor='w', edgecolor='k')
    NEscale = '50m'
    countries = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale=NEscale,
        facecolor='lightblue')

    #for extent of map:
    radiocarbon_grid = Dataset(os.path.join(folder_w_data, 'radd_data.nc'))
    lon=radiocarbon_grid.variables['lon'][:]
    lat=radiocarbon_grid.variables['lat'][:]

    ax = plt.subplot(1, 1, 1, projection=ccrs.PlateCarree())
    #lon.max()
    img_extent = (min(lon), max(lon), min(lat), max(lat))
    ax.set_extent([min(lon), max(lon), min(lat), max(lat)],crs=ccrs.PlateCarree())
    ax.add_feature(countries, edgecolor='black', linewidth=0.3)

    all_values_list=[]
    all_values_list_sites=[]
    for key in dictionary_radiocarbon_emissions:

        all_values_list.append(dictionary_radiocarbon_emissions[key][year])
        all_values_list_sites.append(dictionary_radiocarbon_emissions[key]['name'])

        if dictionary_radiocarbon_emissions[key][year]<50:
            p1=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=2,alpha=0.7,transform=ccrs.PlateCarree())
        if dictionary_radiocarbon_emissions[key][year]>=50 and dictionary_radiocarbon_emissions[key][year]<100:
            p2=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=4,alpha=0.7,transform=ccrs.PlateCarree())
        if dictionary_radiocarbon_emissions[key][year]>=100 and dictionary_radiocarbon_emissions[key][year]<200:
            p3=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=6,alpha=0.7,transform=ccrs.PlateCarree())    
        if dictionary_radiocarbon_emissions[key][year]>=200 and dictionary_radiocarbon_emissions[key][year]<400:
            p4=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=8,alpha=0.7,transform=ccrs.PlateCarree())      
        if dictionary_radiocarbon_emissions[key][year]>=400 and dictionary_radiocarbon_emissions[key][year]<1000:
            p5=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=10,alpha=0.7,transform=ccrs.PlateCarree())
        if dictionary_radiocarbon_emissions[key][year]>=1000 and dictionary_radiocarbon_emissions[key][year]<2000:
            p6=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=14,alpha=0.7,transform=ccrs.PlateCarree())
        if dictionary_radiocarbon_emissions[key][year]>=2000 and dictionary_radiocarbon_emissions[key][year]<4000:
            p7=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=18,alpha=0.7,transform=ccrs.PlateCarree())
        if dictionary_radiocarbon_emissions[key][year]>=4000:
            p8=ax.plot(dictionary_radiocarbon_emissions[key]['longitude'],dictionary_radiocarbon_emissions[key]['latitude'],'o',color='r',ms=24,alpha=0.7,transform=ccrs.PlateCarree())


    #points for all the ICOS atmospheric stations:
    for atm_station in atm_stations.iterrows():

        p9=ax.plot(float(atm_station[1][5]),float(atm_station[1][4]),'o',color='b',ms=4,transform=ccrs.PlateCarree())  

    matplotlib.rcParams.update({'font.size': 17})

    legend=plt.legend((p1[0], p2[0],p3[0], p4[0],p5[0],p6[0],p7[0], p8[0], p9[0]), ('0 - 50', '50 - 100', '100 - 200', \
                                                                                  '200 - 400', '400 - 1000', '1000 - 2000',\
                                                                                  '2000 - 4000' , '>4000', 'ICOS atm. stations'),\
                                                                                    title="Discharge, GBq/Year", ncol=2)

    legend._legend_box.align = "left"

    plt.title('Radiocarbon ($^1$$^4$CO$_2$) emissions from nuclear facilities year ' + year + ' (RADD)')

    plt.show()

    all_values_list_sorted=[x for _,x in sorted(zip(all_values_list,all_values_list))]
    all_values_list_sites_sorted=[x for _,x in sorted(zip(all_values_list,all_values_list_sites))]

    matplotlib.rcParams.update({'font.size': 17})

    x_pos = np.arange(len(all_values_list_sorted))

    fig, ax = plt.subplots(figsize=(25,10))
    ax.bar(x_pos, all_values_list_sorted,
           align='center',
           alpha=0.5,
           color='green')
    ax.set_ylabel('GBq/year')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(all_values_list_sites_sorted, rotation='vertical')

    ax.set_title('Radiocarbon ($^1$$^4$CO$_2$) emissions from nuclear facilities year ' + year +' (RADD)')

    ax.yaxis.grid(True)

    plt.show()


# what happens when you click on a station (show some info + link that takes user to the station landing page)
def html_table_station(station, station_name, uri):

    #Create and initialize variable to store station info in html table:            
    html_table = """<meta content="text/html; charset=UTF-8">
                    <style>td{padding: 3px;}</style><table>"""

  
    html_table = html_table+'<tr><td>'+ 'StationID:' + '</td><td><b>'+station+'</b></td></tr>'

    if uri!='':
        html_table = html_table+'<tr><td>'+ 'Name:' + '</td><td><b><a href="'+uri+'"target="_blank">'+station_name+'</a></b></td></tr>'   
    else:
        html_table = html_table+'<tr><td>'+ 'Name: ' + '</td><td><b>' + station_name+'</b></td></tr>'            


    #Add html closing tag for table:
    html_table = html_table +'</table>'

    #Return station info as html table:
    return html_table

# what should happen when you click on a nuclear facility in the map. Show in HTML table
def html_table_radiocarbon(dictionary_item):
    
    emission_source_dictioanry=dictionary_radiocarbon_emissions[dictionary_item]

    #Create and initialize variable to store station info in html table:            
    html_table = """<meta content="text/html; charset=UTF-8">
                    <style>td{padding: 3px;}</style><table>"""
    
    info_emission_source=dictionary_radiocarbon_emissions[dictionary_item]
    
    html_table = html_table+'<tr><td>'+'Name: '+'</td><td><b>'+ info_emission_source['name']+'</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Emissions 2015: '+'</td><td><b>'+ str(info_emission_source['2015'])+'</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Emissions 2016: '+'</td><td><b>'+ str(info_emission_source['2016'])+'</b></td></tr>'
    
    if info_emission_source['name']=='Forsmark':
        
            html_table = html_table+'<tr><td>'+'Emissions 2017: '+'</td><td><b>'+ str(info_emission_source['2017'])+'</b> (interpolated bacause 6520 in RADD must be an error)</td></tr>'
    else:
        html_table = html_table+'<tr><td>'+'Emissions 2017: '+'</td><td><b>'+ str(info_emission_source['2017'])+'</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Emissions 2018: '+'</td><td><b>'+ str(info_emission_source['2018'])+'</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Unit: '+'</td><td><b>'+ 'GBq/year'+'</b></td></tr>'
    
    html_table = html_table +'</table>'
    
    #Return station info as html table:
    return html_table

#this is used for the second map that shows the information about nuclar facilities that contribute over the user
#defined threshold. 
def html_table_radiocarbon_contribution_facility(name_facility, date_range, contribution):
    
    date_index_number = (len(date_range) - 1)

    from_to_date=(str(date_range[0].year) + '-' + str(date_range[0].month) + '-' + str(date_range[0].day)\
            + ' to ' + str(date_range[date_index_number].year) + '-' + str(date_range[date_index_number].month) + '-' + str(date_range[date_index_number].day))
    
    #Create and initialize variable to store station info in html table:            
    html_table = """<meta content="text/html; charset=UTF-8">
                    <style>td{padding: 3px;}</style><table>"""
    
    html_table = html_table+'<tr><td>' + 'Date range: ' + '</td><td><b>' + from_to_date + '</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Name: '+'</td><td><b>'+ name_facility +'</b></td></tr>'
    
    html_table = html_table+'<tr><td>'+'Average influence (permil): '+'</td><td><b>'+ str("%.3f" % contribution)+'</b></td></tr>'
    
    html_table = html_table +'</table>'
    
    #Return station info as html table:
    return html_table

#different grid with radiocarbon emissions to import depending on the argument year.
def import_radiocarbon_data(year):
    
    radiocarbon_grid = Dataset(os.path.join(folder_w_data, 'radd_data.nc'))

    fp_radiocarbon = radiocarbon_grid.variables[year][:,:]

    fp_radiocarbon_bq_yr= fp_radiocarbon*1000000000

    #Emission year --> emission per second(365*24*60*60=31536000)
    fp_radiocarbon_bq_s=fp_radiocarbon_bq_yr/31536000

    #Emission distributed evenly within the STILT cell it is emitted: 
    f_gridarea = cdf.Dataset(os.path.join(folder_w_data, 'gridareaSTILT.nc'))
    gridarea = f_gridarea.variables['cell_area'][:]

    fp_radiocarbon_bq_s_m2= fp_radiocarbon_bq_s/gridarea
    
    return fp_radiocarbon_bq_s_m2

#FUNCTIONS TO MODEL delta14C.
def get_background_values_nuclear_corrected(background_filename):
    bg_values= pd.read_csv(os.path.join(folder_w_data, background_filename))

    bg_values.dropna(inplace = True) 

    bg_values_upd = bg_values['DateTime;FIT;Nuclear;CorrectedFIT;ffCO2'].str.split(";", n = 5, expand = True) 

    bg_values["DateTime"]= bg_values_upd[0] 
    bg_values["CorrectedFIT"]= bg_values_upd[3] 
    bg_values["ffCO2"]= bg_values_upd[4] 

    #drop the column where the data is not seperated 
    bg_values.drop(columns =['DateTime;FIT;Nuclear;CorrectedFIT;ffCO2'], inplace = True) 
    
    #convert the column with datetime to pandas datetime
    bg_values['DateTime'] = pd.to_datetime(bg_values['DateTime'])

    #make sure the fit and nuclear components are floats
    bg_values['CorrectedFIT'] = bg_values['CorrectedFIT'].astype(float)
    
    bg_values['ffCO2'] = bg_values['ffCO2'].astype(float)
    
    return bg_values

#which nuclear emission data should be used to calculate the nuclear influence on delta14C?
#only have 2015-2018 currently. Earlier years get data from 2015 and later years get data from 2018
def access_best_nuclear_emission_data(year, display_message=True):
    
    #if not 2015, 2016, 2017 or 2018 --> use to closest we have
    if int(year)<2015:

        radd_year='2015'

        fp_radiocarbon_bq_s_m2 = import_radiocarbon_data('2015')
        
        #warning message printed to the user
        if display_message:
            display(HTML('<p style="font-size:15px;"><b>Warning</b>: used radiocarbon data for year 2015 (to calculate nuclear contamination year ' + str(year) + ')</p>'))

    elif int(year)>2018:

        radd_year='2018'

        fp_radiocarbon_bq_s_m2 = import_radiocarbon_data('2018')
        
        #warning message printed to the user.
        if display_message:
            display(HTML('<p style="font-size:15px;"><b>Warning</b>: used radiocarbon data for year 2018 (to calculate nuclear contamination year ' + str(year) + ')</p>'))

    else:
        
        #for years between 2015-2018, use correct year.
        radd_year=str(year)
        fp_radiocarbon_bq_s_m2 = import_radiocarbon_data(str(year))
 
    return fp_radiocarbon_bq_s_m2, radd_year

#for each footprint, get the influence from each of the facilities.
#later check if they are over the threshold (influence needs to be aggregated over the selected data range)
def list_facilities_nuclear_contrib_specific_date(date, delta_radiocarbon_contribution_grid):
    
    list_values_by_date=[]

    #first column is the date... for df_influence_by_facility_over_threshold
    list_values_by_date.append(date)
    
    list_values_by_date.append(0)
    
    for key in dictionary_radiocarbon_emissions:

        row=key[0]
        col=key[1]

        #the row/col combination makes it possible to see the influence from a particular facility
        #(assuming there is not two different facilities in the same grid - which is true in the case of the data from RADD for 2015-2018)
        list_values_by_date.append(delta_radiocarbon_contribution_grid[0][row][col])
        
    return list_values_by_date


#resample the delta 14C data in the radiocarbonObject to be what the user has specified (monthly or specific number of days)
#this will not happen when resample is set to 0.
#returns dataframes (to radiocarbon_object) with the resampled data that is added to the object that is being created. 
def resampled_modelled_radiocarbon(radiocarbonObject):
    
    resample = radiocarbonObject.settings['resample']
    
    dfDelta14CStation = radiocarbonObject.dfDelta14CStation
    
    dfDelta14CStation = dfDelta14CStation.round(3)
    
    #mean for all values, also a count (get from size - number of footprints/values used to calculate the mean)
    dfDelta14CStation_resample = dfDelta14CStation.set_index('date').resample(resample).agg({'delta14C_nuclear': 'mean',
                                                       'delta14C_background': 'mean',
                                                       'delta14C_modelled': 'mean',
                                                       'nan_for_count': 'sum',
                                                       'delta14C_fossil_fuel': ['mean', 'size']}) 
    
    dfDelta14CStation_resample.columns = dfDelta14CStation_resample.columns.map('_'.join)
    
    dfDelta14CStation_resample = dfDelta14CStation_resample.rename(columns={'delta14C_fossil_fuel_size':'count',
                                                                 'delta14C_nuclear_mean':'delta14C_nuclear',
                                                                 'delta14C_background_mean':'delta14C_background',
                                                                 'delta14C_modelled_mean':'delta14C_modelled',
                                                                 'delta14C_fossil_fuel_mean':'delta14C_fossil_fuel',
                                                                 'nan_for_count_sum':'count_nan'})
   
    dfDelta14CStation_resample=dfDelta14CStation_resample.sort_index()
    
    dfDelta14CStation_resample['date_start'] = dfDelta14CStation_resample.index

    #end date is the next row's date - since end when the next time step begins.
    list_dates = dfDelta14CStation_resample['date_start'].tolist()
    
    list_dates_upd=list_dates[1:]
    
    max_date= max(radiocarbonObject.dateRange)
    
    list_dates_upd.append(max_date)

    dfDelta14CStation_resample['date_end'] = list_dates_upd
    
    radiocarbonObject.dfDelta14CStationResample=dfDelta14CStation_resample

    #make a new dataframe to be used in Bokeh plot with "double entries"... make a straight line over the 
    #resampled time period in the graph
    
    #shift row values one down (date stays the same - just get the values for the "footprint before".
    dfDelta14CStation_resample_shift = dfDelta14CStation_resample.shift(periods=1)
    
    odd_numbers=odd(len(dfDelta14CStation_resample_shift))
    
    dfDelta14CStation_resample_shift=dfDelta14CStation_resample_shift.sort_index()

    dfDelta14CStation_resample_shift['for_index'] = odd_numbers
   
    even_numbers=even(len(dfDelta14CStation_resample))
    
    dfDelta14CStation_resample['for_index'] = even_numbers
   
 
    #add the "shifted dataframe" to the original one. Will have two dates for each resample period and
    #the same value for the start of the resampled period as the end (make for the stright line).
    dfDelta14CStation_bokeh=dfDelta14CStation_resample.append(dfDelta14CStation_resample_shift)
    
    dfDelta14CStation_bokeh=dfDelta14CStation_bokeh.set_index('for_index') 
    
    #sort so that dates are in order (two of each date) - for_index instead of date as index. 
    #does not work to have two index with the same value
    dfDelta14CStation_bokeh=dfDelta14CStation_bokeh.sort_index()
    
    #the date field to use for the x-axis is different then start/end date column:
    #want the two columns used to display the same values (at the start and end of the resampled date range)
    #to have the start and end date of the resampled date range respectivley).
    list_dates = dfDelta14CStation_bokeh['date_start'].tolist()
    list_dates_upd=list_dates[1:]
    list_dates_upd.append(list_dates[-1])
    
    dfDelta14CStation_bokeh['date']=list_dates_upd
    
    #the last date is missing in the avergae dataframe (the row gets the value of the first footprint/date that
    #is used in the average. Want the last line segment to extend through the last daterange used for resampling.
    #hence add the last row again and update the date with the max date of the daterange
    max_date= max(radiocarbonObject.dateRange)
    
    last_row = dfDelta14CStation_bokeh.iloc[-1].tolist()

    last_row[-1]=max_date

    dfDelta14CStation_bokeh.loc[-1] =last_row
    
    #dateframe without first row (nan-values since shifted. Rather added the final row (last_row - see above). 
    dfDelta14CStation_bokeh = dfDelta14CStation_bokeh.iloc[1:]
    
    return dfDelta14CStation_resample, dfDelta14CStation_bokeh
    

#same but for the facilities - update the fields that will be averaged
def resampled_modelled_radiocarbon_facility(radiocarbonObject):
    
    resample = radiocarbonObject.settings['resample']

    dfDelta14CFacility = radiocarbonObject.dfDelta14CFacility
    
    dfDelta14CFacility = dfDelta14CFacility.round(3)
    
    dictionary_columns={}

    column_names=dfDelta14CFacility.columns
    
    last_column=column_names[-1]
    for column in column_names:
        
        if column != 'date':
            
            if column == 'nan_for_count':
                dictionary_columns['nan_for_count'] = 'sum'

            elif column == last_column:

                dictionary_columns[column] = ['mean','size']
            else:
                dictionary_columns[column] = 'mean'
               
            
    dfDelta14CFacility_resample=dfDelta14CFacility.resample(resample, on='date').agg(dictionary_columns)
    
    dfDelta14CFacility_resample.columns = dfDelta14CFacility_resample.columns.map('_'.join)
    list_upd_col_names=[]
    for column in dfDelta14CFacility_resample.columns:
        if column[-5:] =='_mean':
            column = column[:-5]
        list_upd_col_names.append(column)

    dfDelta14CFacility_resample.columns=list_upd_col_names
        

    dfDelta14CFacility_resample = dfDelta14CFacility_resample.rename(columns={(last_column +'_size'):'count',
                                                                             'nan_for_count_sum':'count_nan'})

    dfDelta14CFacility_resample=dfDelta14CFacility_resample.sort_index()
    

    dfDelta14CFacility_resample['date_start'] = dfDelta14CFacility_resample.index

    
    #end date is the next row's date - since end when the next time step begins.
    list_dates = dfDelta14CFacility_resample['date_start'].tolist()


    list_dates_upd=list_dates[1:]
    
    max_date= max(radiocarbonObject.dateRange)
    
    list_dates_upd.append(max_date)

    dfDelta14CFacility_resample['date_end'] = list_dates_upd
    
    radiocarbonObject.dfDelta14CFacilityResample=dfDelta14CFacility_resample

    #make a new dataframe to be used in Bokeh plot with "double entries"... make a straight line over the 
    #resampled time period in the graph
    
    #shift row values one down (date stays the same - just get the values for the "footprint before".
    dfDelta14CFacility_resample_shift = dfDelta14CFacility_resample.shift(periods=1)
   
    
    odd_numbers=odd(len(dfDelta14CFacility_resample_shift))
    
    dfDelta14CFacility_resample_shift=dfDelta14CFacility_resample_shift.sort_index()

    dfDelta14CFacility_resample_shift['for_index'] = odd_numbers
   
    even_numbers=even(len(dfDelta14CFacility_resample))
    
    dfDelta14CFacility_resample['for_index'] = even_numbers
   
 
    #add the "shifted dataframe" to the original one. Will have two dates for each resample period and
    #the same value for the start of the resampled period as the end (make for the stright line).
    dfDelta14CFacility_bokeh=dfDelta14CFacility_resample.append(dfDelta14CFacility_resample_shift)
    
    dfDelta14CFacility_bokeh=dfDelta14CFacility_bokeh.set_index('for_index') 
    
    #sort so that dates are in order (two of each date) - for_index instead of date as index. 
    #does not work to have two index with the same value
    dfDelta14CFacility_bokeh=dfDelta14CFacility_bokeh.sort_index()
    
    #the date field to use for the x-axis is different then start/end date column:
    #want the two columns used to display the same values (at the start and end of the resampled date range)
    #to have the start and end date of the resampled date range respectivley).
    list_dates = dfDelta14CFacility_bokeh['date_start'].tolist()
    list_dates_upd=list_dates[1:]
    list_dates_upd.append(list_dates[-1])
    
    dfDelta14CFacility_bokeh['date']=list_dates_upd
    
    #the last date is missing in the avergae dataframe (the row gets the value of the first footprint/date that
    #is used in the average. Want the last line segment to extend through the last daterange used for resampling.
    #hence add the last row again and update the date with the max date of the daterange
    
    #already defined - remove in above function also 
    #max_date= max(radiocarbonObject.dateRange)
    
    last_row = dfDelta14CFacility_bokeh.iloc[-1].tolist()

    last_row[-1]=max_date

    dfDelta14CFacility_bokeh.loc[-1] =last_row
    
    #dateframe without first row (nan-values since shifted. Rather added the final row (last_row - see above). 
    dfDelta14CFacility_bokeh = dfDelta14CFacility_bokeh.iloc[1:]
   
    return dfDelta14CFacility_resample, dfDelta14CFacility_bokeh
    

#bokeh plot showing the data. Used in both gui_stilt and gui_measured_cp
def plot_radiocarbon_bokhe(radiocarbonObject, include_meas=False):

    station_name = radiocarbonObject.settings['stilt']['name']
    station = radiocarbonObject.stationId
    
    if include_meas:
        source = ColumnDataSource(data = radiocarbonObject.df_for_plot)
        
        #not in the object when processing measured data, hence add it here for the rest of the function to work.
        radiocarbonObject.settings['resample'] = 'None'
        
    else:
    
        if radiocarbonObject.settings['resample'][0] == 'M' or int(radiocarbonObject.settings['resample'][0])>0:

            source = ColumnDataSource(data = radiocarbonObject.dfDelta14CStationResampleBokeh)

        else:
            source = ColumnDataSource(data = radiocarbonObject.dfDelta14CStation)
    
    if station_name!='':
        for_title='∆14C at ' + station_name + ' (' + station + ')'
    else:
        for_title='∆14C at ' + station
    
    #Create a figure object:
    p = bokeh_figure(plot_width=1000,
               plot_height=500,
               x_axis_label='Time (UTC)', 
               y_axis_label='∆14C [‰]',
               x_axis_type='datetime',
               title = for_title,
               tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')

    #Create line glyph:
    nuclear = p.line('date','delta14C_nuclear', source=source, name='nuclear', line_width=1, color='red', legend_label='Nuclear ∆14C') 
    fossil= p.line('date','delta14C_fossil_fuel', source=source, line_width=1, color='black', legend_label='Fossil fuel ∆14C') 
    background =  p.line('date','delta14C_background', source=source, line_width=1, color='darkorange', legend_label='Background ∆14C')
    modelled =  p.line('date','delta14C_modelled', source=source, line_width=3, color='blue', legend_label=('Modelled ∆14C'))
     
    
    if include_meas:
        #maybe update name of this column
        measured =  p.line('date','Measurement_value', source=source, line_width=3, color='green', legend_label=('Measured ∆14C'))
        
    #Set title attributes:
    p.title.align = 'center'
    p.title.text_font_size = '13pt'
    p.title.offset = 15

    #Set label font style:
    p.xaxis.axis_label_text_font_style = 'normal'
    p.yaxis.axis_label_text_font_style = 'normal'
    p.xaxis.axis_label_standoff = 15 #Sets the distance of the label from the x-axis in screen units
    p.yaxis.axis_label_standoff = 15 #Sets the distance of the label from the y-axis in screen units

    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"
    
    #Set grid format:
    p.grid.grid_line_alpha = 0
    p.ygrid.band_fill_color = "olive"
    p.ygrid.band_fill_alpha = 0.1

    #Deactivate hover-tool, which is by default active:
    p.toolbar.active_inspect = None

    p.legend.location = "top_left"
    p.legend.click_policy="hide"
    
    list_tuples_for_tooltip =  [( 'Time (UTC)',   ('@date_start{%Y-%m-%d}' + ' to ' + '@date_end{%Y-%m-%d}')),
                ( 'Nuclear ∆14C',  '@{delta14C_nuclear}{0.2f}' ),
                ( 'Fossil fuel ∆14C',  '@{delta14C_fossil_fuel}{0.2f}' ),
                ( 'Background ∆14C',  '@{delta14C_background}{0.2f}' ),
                ( 'Modelled ∆14C',  '@{delta14C_modelled}{0.2f}' ),
                ( 'Count averaged footprints',  '@{count}{0f}' ),
                ( 'Count NaN footprints',  '@{count_nan}{0f}' )]
    

    if include_meas:
        
        list_tuples_for_tooltip.append(tuple(('Measured ∆14C',  '@{Measurement_value}{0.2f}' )))
        list_tuples_for_tooltip.append(tuple(('Standard deviation measurement',  '@{Std_deviation_measurement}{0.2f}' )))

    if hasattr(radiocarbonObject.settings, 'resample') or include_meas:
    #if radiocarbonObject.settings['resample'][0] == 'M' or int(radiocarbonObject.settings['resample'][0])>0 or include_meas:
        p.add_tools(HoverTool(
            names=['nuclear'],
            tooltips=list_tuples_for_tooltip,
            formatters={
            '@date_start'      : 'datetime',
            '@date_end'      : 'datetime'
        },


            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='vline'
        ))
    
    #when not integration time. 
    else:
        p.add_tools(HoverTool(
        names=['nuclear'],
        tooltips=[
            ( 'Time (UTC)',   '@date{%Y-%m-%d}'),
            ( 'Nuclear ∆14C',  '@{delta14C_nuclear}{0.2f}' ),
            ( 'Fossil fuel ∆14C',  '@{delta14C_fossil_fuel}{0.2f}' ),
            ( 'Background ∆14C',  '@{delta14C_background}{0.2f}' ),
            ( 'Modelled ∆14C',  '@{delta14C_modelled}{0.2f}' )
        ],

        formatters={
            '@date'      : 'datetime'
        },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline'
    ))
    

    show(p)
    
#plot the nuclear contamination by facility. Used in gui_stilt if selected to include by facility. 
def plot_nuclear_contamination_by_facility_bokhe(radiocarbonObject):
    
    station_name = radiocarbonObject.settings['stilt']['name']
    
    station = radiocarbonObject.stationId
    
    if radiocarbonObject.dfDelta14CStationResampleBokeh is not None:
        
        dfDelta14CFacility = radiocarbonObject.dfDelta14CFacilityResampleBokeh
        dfDelta14CStation = radiocarbonObject.dfDelta14CStationResampleBokeh
        list_tuples_for_tooltip=[('Time (UTC)', '@date_start{%Y-%m-%d}' + ' to ' + '@date_end{%Y-%m-%d}'), ('Count averaged footprints',  '@{count}{0f}'), ('Count NaN footprints',  '@{count_nan}{0f}')]
        
        formatters = {'@date_start':'datetime','@date_end':'datetime'}
    
    else:
        dfDelta14CFacility = radiocarbonObject.dfDelta14CFacility
    
        dfDelta14CStation = radiocarbonObject.dfDelta14CStation
        
        list_tuples_for_tooltip=[('Time (UTC)', '@date{%Y-%m-%d %H:%M:%S}')]
        
        formatters = {'@date':'datetime'}

    threshold = radiocarbonObject.settings['threshold']
    
    average_nuclear_total = dfDelta14CStation['delta14C_nuclear'].mean() 
    
    source_facility = ColumnDataSource(data = dfDelta14CFacility)
    
    source_total = ColumnDataSource(data = dfDelta14CStation)
    
    if station_name!='':
        for_title='∆14C at ' + station_name + ' (' + station + ') by nuclear facility (>' + str(threshold) + ' permil)'
    else:
        for_title='∆14C at ' + station + 'by nuclear facility (>' + str(threshold) + ' permil)'

    #Create a figure object:
    p = bokeh_figure(plot_width=1000,
               plot_height=500,
               x_axis_label='Time (UTC)', 
               y_axis_label='∆14C [‰]',
               x_axis_type='datetime',
               title = for_title,
               tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')

    # line with nuclear 
    p.line('date','delta14C_nuclear', source=source_total, line_width=1, color='red', legend_label=('Total ∆14C nuclear (' + str( round(average_nuclear_total,4)) + ' permil)'))

    colors= seaborn.color_palette('colorblind', n_colors=71)

    colors= colors.as_hex()
    
    #for map
    dfFacilitiesOverThreshold = pd.DataFrame(columns=['facility', 'lat', 'lon', 'permil contam.'])

    index=0
    
    first=True

    for key in dictionary_radiocarbon_emissions:

        column_name=dictionary_radiocarbon_emissions[key]['name']

        #only facilities that are over the threshold in dfDelta14CFacility
        if not column_name in dfDelta14CFacility.columns:
            
            continue
        
        #set to false if at least one facility contributes over the threshold. 
        first=False
            
        average_contamination = dfDelta14CFacility[column_name].mean()
        

        by_facility= p.line('date', column_name, source=source_facility, line_width=1, color=colors[index],legend_label=(column_name + ' (average ' + str(round(average_contamination,4)) + ' permil)'))

        average_contamination = dfDelta14CFacility[column_name].mean()
        
        lat = dictionary_radiocarbon_emissions[key]['latitude']
        lon = dictionary_radiocarbon_emissions[key]['longitude']
        
        dfFacilitiesOverThreshold.loc[index] = [column_name, lat, lon, average_contamination]
        
        list_tuples_for_tooltip.append(tuple((column_name + ' ∆14C',  '@{' + column_name + '}{0.2f}' )))
                       
        index=index+1
        

    #only show visualisations if there are any facilities over the theshold. Otherwise print message that there is no
    #facilities contaminating more than the threshold.
    if len(list_tuples_for_tooltip)>1 and first==False:

        #Set title attributes:
        p.title.align = 'center'
        p.title.text_font_size = '13pt'
        p.title.offset = 15

        #Set label font style:
        p.xaxis.axis_label_text_font_style = 'normal'
        p.yaxis.axis_label_text_font_style = 'normal'
        p.xaxis.axis_label_standoff = 15 #Sets the distance of the label from the x-axis in screen units
        p.yaxis.axis_label_standoff = 15 #Sets the distance of the label from the y-axis in screen units

        p.xaxis.major_label_text_font_size = "15pt"
        p.yaxis.major_label_text_font_size = "15pt"
        p.xaxis.axis_label_text_font_size = "15pt"
        p.yaxis.axis_label_text_font_size = "15pt"

        #Set grid format:
        p.grid.grid_line_alpha = 0
        p.ygrid.band_fill_color = "olive"
        p.ygrid.band_fill_alpha = 0.1

        #Deactivate hover-tool, which is by default active:
        p.toolbar.active_inspect = None

        p.legend.location = "top_left"
        p.legend.click_policy="hide"

        #add the other stations also?
        #for resample - also use from to date.
        #line_with_hoover
        p.add_tools(HoverTool(renderers=[by_facility],
            tooltips=list_tuples_for_tooltip,
            formatters=formatters,
            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='vline'
        ))
        #return plot:
        show(p)

        radiocarbonObject.dfFacilitiesOverThreshold = dfFacilitiesOverThreshold 

    return radiocarbonObject
    
#map showing the contributing facilities. Used in gui_stilt if selected to include by facility. 
def nuclear_contamination_by_facility_map(radiocarbonObject):
    
    station_lat = radiocarbonObject.lat
    station_lon = radiocarbonObject.lon
    station = radiocarbonObject.stationId
    station_name = radiocarbonObject.settings['stilt']['name']
    dfFacilitiesOverThreshold = radiocarbonObject.dfFacilitiesOverThreshold
    date_range = radiocarbonObject.dateRange
  
    if 'icos' in radiocarbonObject.settings:
        uri=radiocarbonObject.settings['icos']['uri'][0]
    else:
        uri=''

    #Create folium map-object:
    m = folium.Map(location=[station_lat, station_lon],
           zoom_start=4,
           tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
           attr = 'Esri',
           name = 'Esri Satellite',
           overlay = False,
           control = True)

    marker_text_station = branca.element.IFrame(html=html_table_station(station, station_name, uri), width=300, height=100)

    popup_station=folium.Popup(marker_text_station,
               parse_html=True,
               max_width=400)


    #icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_stations.png'), icon_size=(16,25))
    #icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_nuclear_facilities.png'), icon_size=(16.6,20))
    #icon_size = (16.6,20)
    #Create marker and add it to the map:
    folium.Marker(location=[station_lat,station_lon],
                  popup=popup_station,
                  icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_stations.png'), icon_size=(16,25))).add_to(m)

    
    for index, row in dfFacilitiesOverThreshold.iterrows():

        marker_text_nuclear= branca.element.IFrame(html_table_radiocarbon_contribution_facility(row['facility'], \
            date_range, row['permil contam.']), width=400, height=100)

        popup_nuclear_facility=folium.Popup(marker_text_nuclear,parse_html=True,max_width=400)

        #Create marker and add it to the map:
        folium.Marker(location=[row['lat'],row['lon']],
                                popup=popup_nuclear_facility,
                                icon=folium.CustomIcon(os.path.join(folder_w_data, 'marker_nuclear_facilities.png'), icon_size=(16.6,20))).add_to(m)

    display(m)

#create dataframes with delta14C, used in radiocarbon_object. Returned and added to the radiocarbonObject
def delta_radiocarbon_dataframes(radiocarbonObject):

    station=radiocarbonObject.stationId
    station_name=radiocarbonObject.settings['stilt']['name']
    date_range=radiocarbonObject.dateRange
    timeselect=radiocarbonObject.settings['timeOfDay']
    background_filename=radiocarbonObject.settings['backgroundFilename']
    facility_inclusion=radiocarbonObject.settings['facilityInclusion']
    threshold=radiocarbonObject.settings['threshold']
    
    if facility_inclusion:
        facility_names = [dictionary_radiocarbon_emissions[key]['name'] for key in dictionary_radiocarbon_emissions]
        
        columns_output_df_facility = ['date', 'nan_for_count'] + facility_names 
        
        dfDelta14CFacility = pd.DataFrame(columns=columns_output_df_facility)
        
        #needed for map showing where the facilities are (link to landing page)
        if 'icos' in radiocarbonObject.settings:
            uri=radiocarbonObject.settings['icos']['uri'][0]
        else:
            uri=''
    
    bg_values=get_background_values_nuclear_corrected(background_filename)
    

    dfDelta14CStation = pd.DataFrame(columns=['date', 'delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled', 'radd_year', 'nan_for_count', 'nan_for_graph'])
    
    #from stilt - modelled co2 concentration. also broken down into ex different fossil fuels
    modelled_concentration = read_stilt_timeseries(station, date_range)
    
    first=True
    index=0
    for date in date_range:
        
        filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
         +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

        if not os.path.isfile(filename):
            
            dfDelta14CStation.loc[index] = [date, np.nan, np.nan, np.nan, np.nan, np.nan, 1, 0]

            
            if facility_inclusion:
                
                list_facilities_nan = [np.nan for facility in facility_names ]
            
                data_nan_facilities = [date, 1] + list_facilities_nan

                dfDelta14CFacility.loc[index] = data_nan_facilities
            
            index=index+1
            
            continue
        
        #if first time - access the radiocarbon data for specific year.
        #also, if the year of the "current" date is new (ex jan 1 2016). Access the data for the current year instead. 
        if first==True or date.year!=int(year):
            
            year=date.year
            
            fp_radiocarbon_bq_s_m2, radd_year = access_best_nuclear_emission_data(year)

            first=False
            
        #access the footprint given the date/time. Needed to calculate the influence from the facility.
        f_fp = cdf.Dataset(filename)

        fp_current=f_fp.variables['foot'][:,:,:]

        #get the "current" modelled concentrations in correct unit (now in micromole - want it in mole because then use molar mass for C of 12 g)
        modelled_concentration_value=modelled_concentration['co2.stilt'][date]/1000000

        if not isinstance(modelled_concentration_value, float):
            continue

        #fossil fuel
        modelled_concentration_date_time=modelled_concentration['co2.stilt'][date]

        date_for_fit_JFJ=pd.Timestamp(date.year, date.month, date.day)

        try:
            background_value=bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'CorrectedFIT'].iloc[0]

        #when no match with date in bg_values, find closest and match
        except:

            nearest_date_test=nearest_date(bg_values.DateTime, date)

            background_value=bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'CorrectedFIT'].iloc[0]

        try:    
            JFJ_foss = bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'ffCO2'].iloc[0]
        except:
            nearest_date_test=nearest_date(bg_values.DateTime, date)
            JFJ_foss = bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'ffCO2'].iloc[0]

        #JFJ_foss --> monthly average. 
        foss_fuel_station_minus_jfj_ppm=(modelled_concentration['co2.fuel.oil'][date]+modelled_concentration['co2.fuel.gas'][date]+\
                                         modelled_concentration['co2.fuel.coal'][date]-JFJ_foss)

        #from Ingeborg's equation 3 https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2003GL018477
        #foss_fuel_station_minus_jfj_ppm --> cfoss
        #modelled_concentration_date_time --> cmeas (HEI)
        #background_value --> deltaC14BG
        modelled_delta_c14_not_nuclear_corrected=(foss_fuel_station_minus_jfj_ppm/modelled_concentration_date_time)*(background_value+1000)-background_value

        modelled_delta_c14_not_nuclear_corrected=-modelled_delta_c14_not_nuclear_corrected

        #nuclear contamination
        #keeping it a grid (fp_radiocarbon_bq_s_m2*fp_current) to see the resulting shift in radiocarbon caused by each individual cell
        delta_radiocarbon_contribution_grid=(((fp_radiocarbon_bq_s_m2*fp_current) / (modelled_concentration_value* Mc * Aabs)) ) *1000

        #get one value summed value of this grid for each date/time. What is used in the time series output from running this cell
        delta_radiocarbon_contribution_summed= delta_radiocarbon_contribution_grid[:][:].sum()

        fossil_fuel_component=modelled_delta_c14_not_nuclear_corrected-background_value

        modelled_delta_c14_nuclear_corrected = modelled_delta_c14_not_nuclear_corrected + delta_radiocarbon_contribution_summed

        dfDelta14CStation.loc[index] = [date, background_value, delta_radiocarbon_contribution_summed, fossil_fuel_component, modelled_delta_c14_nuclear_corrected, radd_year, 0, np.nan]


        #for each date (current level), get the contribution from each facility (if user chose she wants it. 
        if facility_inclusion:

            data_facilities = list_facilities_nuclear_contrib_specific_date(date, delta_radiocarbon_contribution_grid)

            dfDelta14CFacility.loc[index] = data_facilities
        
        index=index+1

    #added - index-error.
    dfDelta14CStation['date'] = pd.to_datetime(dfDelta14CStation['date'])


    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    
    if facility_inclusion:
        
              
        list_columns_drop = []
        for column in dfDelta14CFacility.columns:
            

            if column=='date' or column=='nan_for_count':
                continue
            
            
            if not dfDelta14CFacility[column].mean()>float(threshold):
                list_columns_drop.append(column)
        
        dfDelta14CFacility=dfDelta14CFacility.drop(columns=list_columns_drop)
    
    
        return dfDelta14CStation, dfDelta14CFacility
    
    else:
        
        return dfDelta14CStation
    
    
# MEASURED DATA FROM CP IN COMBINATION WITH MODELLING OF DELTA14C.


#get the list of stations with radiocarbon measurement data at the Carbon Portal server. 
#takes a while, potential improvement? 
def list_station_tuples_w_radiocarbon_data():
       
    sparql = RunSparql()
    sparql.format = 'pandas'
    sparql.query = open(os.path.join(folder_w_data, 'c14.sparql'), 'r').read()
    df_stations_w_radiocarbon_data_cp = sparql.run() 
    
    list_of_tuples_for_dropdown=[]
    
    for index, row in df_stations_w_radiocarbon_data_cp.iterrows():
        
        station_name = row['stationName']
        station_id = row['stationId']
        sampling_height = row['samplingHeight']
        
        display = station_name + ' (' + str(sampling_height) + ')'
        
        values_dictionary = {'station_code': station_id, 'sampling_height':sampling_height}
        
        list_of_tuples_for_dropdown.append((display, values_dictionary)) 
        
    return list_of_tuples_for_dropdown
    

#add count and count_nan variables. also date_start and date_end.
def radiocarbon_cp_results(radiocarbonObjectMeas):
    
    stilt_station = radiocarbonObjectMeas.stationId
    timeselect_list = radiocarbonObjectMeas.settings['timeOfDay']
    timeselect_list_sting=', '.join(str(x) for x in timeselect_list)
    background_filename = radiocarbonObjectMeas.settings['backgroundFilename']
    download_option = radiocarbonObjectMeas.settings['downloadOption']
    meas_station = radiocarbonObjectMeas.stationId[0:3]
    meas_sampling_height = radiocarbonObjectMeas.settings['samplingHeightMeas']
   
    stilt_station_alt=radiocarbonObjectMeas.settings['stilt']['alt']
    stilt_station_name=radiocarbonObjectMeas.settings['stilt']['name']
    stilt_station_lat=radiocarbonObjectMeas.lat
    stilt_station_lon=radiocarbonObjectMeas.lon
    
    date_today= current_date.today()

    #dataframe with all the measurements. Loop over.
    radiocarbon_data= radiocarbonObjectMeas.measuredData

    #the information needed to calculate modelled delta C14 and fossil fuel component
    bg_values=get_background_values_nuclear_corrected(background_filename)

    #before SamplingStartDate and SamplingEndDate (date_start, date_end)
    df_for_export = pd.DataFrame(columns=['date_start','date_end','Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year','count', 'count_nan'])
    
    #this dataframe is added to twice for each measurement (since integrated - start and end data)
    #the 'date' column will first get the same value as SamplingStartDate and the second time the 
    #same value as SamplingEndDate
    df_for_plot = pd.DataFrame(columns=['date', 'date_start','date_end','Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year', 'count', 'count_nan'])
    
    #if len(obj_data)>0:
    
    index=0
    #the plot dataframe will be added to twice in each loop (start - and end time same values for line in graph
    #across integration time. 
    index_plot=0

    #access many at the same time (all the entries - one for each radiocarbon measurement)
    #for each entry at the carbon portal (not all will be used - only when footprints for the same time period)
    first=True
    for (radiocarbon_measurement, measurement_start_date, integration_time, std_deviation) in zip(radiocarbon_data['14C'], radiocarbon_data['TIMESTAMP'], radiocarbon_data['IntegrationTime'], radiocarbon_data['Stdev']):

        #prev - if not in list_hours.
        if measurement_start_date.hour not in timeselect_list or measurement_start_date.minute>0:

            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_start_date.hour))

            measurement_start_date = dt.datetime(int(measurement_start_date.year), int(measurement_start_date.month), int(measurement_start_date.day), updated_hour, 0)

        measurement_end_date=measurement_start_date + timedelta(days=int(integration_time))

        #now filtered date_range_measured.
        date_range_measured = date_range_hour_filtered(measurement_start_date, measurement_end_date, timeselect_list)

        if date_range_measured.empty:
            print('no footprints for date range of measured concentration (',min(date_range_measured), 'to', max(date_range_measured), ')')
            continue

        modelled_concentration = read_stilt_timeseries(stilt_station, date_range_measured)

        #which radd-year(s) - radiocarbon data - used for each sample. Max 2... integration time about 14 days.
        year_list=[]

        #rather df_each_footprint? 
        df_each_meas = pd.DataFrame(columns=['delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'])

        index_each_meas = 0
        count_nan = 0
    
        #now will print a warning for each measurement. 
        for date in date_range_measured:

            filename=(pathFP+stilt_station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename)==False:
                count_nan = count_nan + 1
                continue

            f_fp = cdf.Dataset(filename)

            fp_current=f_fp.variables['foot'][:,:,:]

            modelled_concentration_value=modelled_concentration['co2.stilt'][date]/1000000

            #in micromol for fossil fuel
            modelled_concentration_date_time=modelled_concentration['co2.stilt'][date]

            try:
                if not isinstance(modelled_concentration_value, float) and math.isnan(modelled_concentration_value)==False:
                    continue 

            #happen for ex date 2017-01-01 00:00. A series because two are matched with the date. 
            except:

                continue

            date_for_fit_JFJ=pd.Timestamp(date.year, date.month, date.day)

            try:
                background_value=bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'CorrectedFIT'].iloc[0]

            #when no match with date in bg_values, find closest and match
            except:

                nearest_date_test=nearest_date(bg_values.DateTime, date)

                background_value=bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'CorrectedFIT'].iloc[0]

            try:    
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'ffCO2'].iloc[0]
            except:
                nearest_date_test=nearest_date(bg_values.DateTime, date)
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'ffCO2'].iloc[0]

            #correct for fossil fuel emissions in the at supposedly clean background site
            #if smaller component at the selected station, the fossil fuel component (delta 14C) will be positive rather than negative.
            foss_fuel_station_minus_jfj_ppm=(modelled_concentration['co2.fuel.oil'][date]+modelled_concentration['co2.fuel.gas'][date]+\
                                 modelled_concentration['co2.fuel.coal'][date]-JFJ_foss)

            modelled_delta_c14_not_nuclear_corrected=(foss_fuel_station_minus_jfj_ppm/modelled_concentration_date_time)*(background_value+1000)-background_value

            modelled_delta_c14_not_nuclear_corrected=-modelled_delta_c14_not_nuclear_corrected

            fossil_fuel_component=modelled_delta_c14_not_nuclear_corrected-background_value


            #if first time (first defined out of loop)- access the radiocarbon data for specific year.
            #also, if the year of the "current" date is new (ex jan 1 2016). Access the data for the current year instead. 
            if first==True or date.year!=int(year):

                year=date.year

                fp_radiocarbon_bq_s_m2, radd_year = access_best_nuclear_emission_data(year)

                first=False

            #keeping nuclear contamination it a grid (fp_radiocarbon_bq_s_m2*fp_current) to see the resulting shift in radiocarbon caused by each individual cell
            delta_radiocarbon_contribution_grid=(((fp_radiocarbon_bq_s_m2*fp_current) / (modelled_concentration_value* Mc * Aabs)) ) *1000

            #get one value summed value of this grid for each date/time. What is used in the time series output from running this cell
            delta_radiocarbon_contribution_summed= delta_radiocarbon_contribution_grid[:][:].sum()

            #modelled delta 14C - nuclear corrected (not included in the Levin et al paper)
            modelled_delta_c14_nuclear_corrected=modelled_delta_c14_not_nuclear_corrected+delta_radiocarbon_contribution_summed

            #'delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'
            df_each_meas.loc[index_each_meas] = [background_value, delta_radiocarbon_contribution_summed, fossil_fuel_component, modelled_delta_c14_nuclear_corrected]

            index_each_meas=index_each_meas + 1

            #if always using the same RADD year for all footprints in integrated sample (not ex dec 20 to jan 4)
            if radd_year not in year_list:
                year_list.append(radd_year)

        #average given date-time. If there are values to average (not division by 0)
        #shift per integrated time is nuclear contamination (delta 14C)
        if len(df_each_meas)>0:


            #get the correct information with regards to what RADD data has been used. 
            if len(year_list)>1:
                radd_data_year_export=(year_list[0] + '&' + year_list[1])   
            elif len(year_list)==1:
                radd_data_year_export=year_list[0]
            else:
                radd_data_year_export='no data'

            shift_nuclear=df_each_meas["delta14C_nuclear"].mean()
            shift_fossil_fuel=df_each_meas["delta14C_fossil_fuel"].mean()
            shift_background=df_each_meas["delta14C_background"].mean()
            shift_modelled=df_each_meas["delta14C_modelled"].mean()
            
            count=len(date_range_measured)
            #count_nan=

            #dataframe already created at the top. here append whole row with values for export. one row per integrated sample
            df_for_export.loc[index] = [measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]

            #index to move to the next row for the next integrated sample 
            index=index+1  

            df_for_plot.loc[index_plot] = [measurement_start_date, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]

            index_plot = index_plot + 1

            #measurement_end_date into date column. otherwise same values as above record.
            df_for_plot.loc[index_plot] = [measurement_end_date, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]
            index_plot = index_plot + 1
                
    return df_for_export, df_for_plot
               
        
def read_csv_to_column_list(filename):
    
    csv_as_pandas= pd.read_csv(filename)
    
    columns_csv = csv_as_pandas.columns.tolist()
    
    return columns_csv

# DATA FROM UPLOADED FILE (PROVIDED BY HEIDELBERG --> not in version that goes on exploretest.
def dropdown_stations_from_file(radiocarbon_data, location, sampling_height, crl):
    
    unique_location_elevation_crl=radiocarbon_data.groupby([location,sampling_height, crl]).size().reset_index().rename(columns={0:'count'})

    stations_list= unique_location_elevation_crl[location].tolist()

    location_height_list= unique_location_elevation_crl[sampling_height].tolist()

    crl_sampler_list= unique_location_elevation_crl['CRL_sampler'].tolist()
    
    list_of_tuples_for_dropdown=[]

    for (station_code, location_height, crl_sampler) in zip(stations_list, location_height_list, crl_sampler_list):

        display_name= station_code + ' (' + str(location_height) + 'm, ' + str(crl_sampler) + ' CRL)'

        #return many values for the user selected option (code, crl sampler, location height all to be used later also)
        value_dictionary = {'station_code': station_code, 'crl_sampler': crl_sampler, 'location_height':location_height}

        station_tuple_for_dropdown=(display_name, value_dictionary)

        if len(station_code)==3:
            list_of_tuples_for_dropdown.append(station_tuple_for_dropdown)
        
        
    return list_of_tuples_for_dropdown

#will this be needed? use the same as radiocarbon_cp_results? 
def radiocarbon_file_result(radiocarbonObjectFile):
    
    #get column names. 
    #correct with stationCodeMeas? else compare to old notebook. print meas_station. 
    meas_station = radiocarbonObjectFile.settings['stationCodeMeas']
    crl_sampler = radiocarbonObjectFile.settings['crlSampler']
    station_column=radiocarbonObjectFile.settings['stationColumn']
    meas_column=radiocarbonObjectFile.settings['measurementColumn']
    std_error_column = radiocarbonObjectFile.settings['stdErrorColumn']
    samp_height_column=radiocarbonObjectFile.settings['samplingHeightColumn'] 
    crl_column=radiocarbonObjectFile.settings['crlColumn'] 
    start_date_column=radiocarbonObjectFile.settings['startDateColumn'] 
    end_date_column=radiocarbonObjectFile.settings['endDateColumn'] 
    
    timeselect_list=radiocarbonObjectFile.settings['timeOfDay'] 
    stilt_station = radiocarbonObjectFile.stationId
    
    filename = radiocarbonObjectFile.settings['fileName'] 
    background_filename=radiocarbonObjectFile.settings['backgroundFilename']
    
    bg_values=get_background_values_nuclear_corrected(background_filename)
    
    radiocarbon_data= pd.read_csv(filename)

    radiocarbon_data=radiocarbon_data[(radiocarbon_data[station_column] == meas_station) & (radiocarbon_data[crl_column]==crl_sampler)]
    
    
    df_for_export = pd.DataFrame(columns=['SamplingStartDate', 'SamplingEndDate', 'Measurement_value', 'Std_error_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year' ])
    df_for_plot = pd.DataFrame(columns=['date', 'SamplingStartDate','SamplingEndDate','Measurement_value','Std_error_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year' ])
    
    index=0
    #the plot dataframe will be added to twice in each loop (start - and end time same values for line in graph
    #across start to end date. 
    index_plot=0
    for (radiocarbon_measurement, measurement_start_date, measurement_end_date, crl, std_error) in zip(radiocarbon_data[meas_column], radiocarbon_data[start_date_column], radiocarbon_data[end_date_column], radiocarbon_data[crl_column], radiocarbon_data[std_error_column]):
        
        measurement_start_date=pd.Timestamp(measurement_start_date)
        measurement_end_date=pd.Timestamp(measurement_end_date)
        

        #prev - if not in list_hours.
        if measurement_start_date.hour not in timeselect_list:

            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_start_date.hour))

            measurement_start_date = dt.datetime(int(measurement_start_date.year), int(measurement_start_date.month), int(measurement_start_date.day), updated_hour)

        if measurement_end_date.hour not in timeselect_list:
            
            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_start_date.hour))

            measurement_end_date = dt.datetime(int(measurement_end_date.year), int(measurement_end_date.month), int(measurement_end_date.day), updated_hour)


        #now filtered date_range_measured.
        #date_range_measured = pd.date_range(measurement_start_date, measurement_end_date, freq='3H')
        date_range_measured = date_range_hour_filtered(measurement_start_date, measurement_end_date, timeselect_list)

        if date_range_measured.empty:
            print('no footprints for date range of measured concentration (',min(date_range_measured), 'to', max(date_range_measured), ')')
            continue

        modelled_concentration = read_stilt_timeseries(stilt_station, date_range_measured)

        #which radd-year(s) - radiocarbon data - used for each sample. Max 2... integration time about 14 days.
        year_list=[]

        df_each_meas = pd.DataFrame(columns=['delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'])

        index_each_meas = 0

        first=True
        for date in date_range_measured:

            filename=(pathFP+stilt_station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename)==False:
                continue

            f_fp = cdf.Dataset(filename)

            fp_current=f_fp.variables['foot'][:,:,:]

            modelled_concentration_value=modelled_concentration['co2.stilt'][date]/1000000


            #in micromol for fossil fuel
            modelled_concentration_date_time=modelled_concentration['co2.stilt'][date]


            try:
                if not isinstance(modelled_concentration_value, float) and math.isnan(modelled_concentration_value)==False:
                    continue 

            #happen for ex date 2017-01-01 00:00. A series because two are matched with the date. 
            except:

                continue

            date_for_fit_JFJ=pd.Timestamp(date.year, date.month, date.day)

            try:
                background_value=bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'CorrectedFIT'].iloc[0]

            #when no match with date in bg_values, find closest and match
            except:

                nearest_date_test=nearest_date(bg_values.DateTime, date)

                background_value=bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'CorrectedFIT'].iloc[0]

            try:    
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'ffCO2'].iloc[0]
            except:
                nearest_date_test=nearest_date(bg_values.DateTime, date)
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'ffCO2'].iloc[0]

            #correct for fossil fuel emissions in the at supposedly clean background site
            #if smaller component at the selected station, the fossil fuel component (delta 14C) will be positive rather than negative.
            foss_fuel_station_minus_jfj_ppm=(modelled_concentration['co2.fuel.oil'][date]+modelled_concentration['co2.fuel.gas'][date]+\
                                 modelled_concentration['co2.fuel.coal'][date]-JFJ_foss)

            modelled_delta_c14_not_nuclear_corrected=(foss_fuel_station_minus_jfj_ppm/modelled_concentration_date_time)*(background_value+1000)-background_value

            modelled_delta_c14_not_nuclear_corrected=-modelled_delta_c14_not_nuclear_corrected

            fossil_fuel_component=modelled_delta_c14_not_nuclear_corrected-background_value



            #if first time (first defined out of loop)- access the radiocarbon data for specific year.
            #also, if the year of the "current" date is new (ex jan 1 2016). Access the data for the current year instead. 
            if first==True or date.year!=int(year):

                year=date.year

                fp_radiocarbon_bq_s_m2, radd_year = access_best_nuclear_emission_data(year)

                first=False

            #keeping nuclear contamination it a grid (fp_radiocarbon_bq_s_m2*fp_current) to see the resulting shift in radiocarbon caused by each individual cell
            delta_radiocarbon_contribution_grid=(((fp_radiocarbon_bq_s_m2*fp_current) / (modelled_concentration_value* Mc * Aabs)) ) *1000

            #get one value summed value of this grid for each date/time. What is used in the time series output from running this cell
            delta_radiocarbon_contribution_summed= delta_radiocarbon_contribution_grid[:][:].sum()



            #modelled delta 14C - nuclear corrected (not included in the Levin et al paper)
            modelled_delta_c14_nuclear_corrected=modelled_delta_c14_not_nuclear_corrected+delta_radiocarbon_contribution_summed

            #'delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'
            df_each_meas.loc[index_each_meas] = [background_value, delta_radiocarbon_contribution_summed, fossil_fuel_component, modelled_delta_c14_nuclear_corrected]

            index_each_meas=index_each_meas + 1

            #if always using the same RADD year for all footprints in integrated sample (not ex dec 20 to jan 4)
            if radd_year not in year_list:
                year_list.append(radd_year)

        #average given date-time. If there are values to average (not division by 0)
        #shift per integrated time is nuclear contamination (delta 14C)
        if len(df_each_meas)>0:


            #get the correct information with regards to what RADD data has been used. 
            if len(year_list)>1:
                radd_data_year_export=(year_list[0] + '&' + year_list[1])   
            elif len(year_list)==1:
                radd_data_year_export=year_list[0]
            else:
                radd_data_year_export='no data'

            shift_nuclear=df_each_meas["delta14C_nuclear"].mean()
            shift_fossil_fuel=df_each_meas["delta14C_fossil_fuel"].mean()
            shift_background=df_each_meas["delta14C_background"].mean()
            shift_modelled=df_each_meas["delta14C_modelled"].mean()

            #dataframe already created at the top. here append whole row with values for export. one row per integrated sample
            df_for_export.loc[index] = [measurement_start_date, measurement_end_date, radiocarbon_measurement, std_error, shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year]

            #index to move to the next row for the next integrated sample 
            index=index+1  

            df_for_plot.loc[index_plot] = [measurement_start_date, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_error,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year]

            index_plot = index_plot + 1

            #measurement_end_date into date column. otherwise same values as above record.
            df_for_plot.loc[index_plot] = [measurement_end_date, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_error,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year]
            index_plot = index_plot + 1
                
    return df_for_export, df_for_plot

def download_result(radiocarbonObject, df_type='Station'):
   
    station=radiocarbonObject.stationId
    stilt_station_alt=radiocarbonObject.settings['stilt']['alt']
    stilt_station_lat=radiocarbonObject.settings['stilt']['lat']
    stilt_station_lon=radiocarbonObject.settings['stilt']['lon']
    background_filename=radiocarbonObject.settings['backgroundFilename']
    timeselect=radiocarbonObject.settings['timeOfDay']
    #timeselect_list_string=', '.join(str(x) for x in timeselect)
    
    timeselect_list_string =':00, '.join(str(x) for x in timeselect) + ':00 (UTC)'
    date_today=date_today= current_date.today()
    
    #open a new file with that name and first write some metadata to the top of the file
    
    if df_type=='CP_data' or df_type=='HEI_data':
        f = open(os.path.join(radiocarbonObject.settings['output_folder'], radiocarbonObject.settings['date/time generated'] + radiocarbonObject.stationId + '_' + df_type + '_analysis_results.csv'), 'a')
        date_range_text= ''
        
    else:

        f = open(os.path.join(radiocarbonObject.settings['output_folder'],'dfDelta14C' + df_type + '.csv'), 'a')
        date_range_text=('# Footprint selection (date range): ' + str(min(radiocarbonObject.dateRange)) + ' to ' + str(max(radiocarbonObject.dateRange)) + '\n')

    f.write('# Yearly average radiocarbon emissions data from RADD (downloaded 2020-08-25 from https://europa.eu/radd/). See what yearly average was used in column "radd_year".\n')
    f.write('# STILT transport model used to generate footprints:\n# -->10 days backward simulation\n# -->1/8 degrees longitude x 1/12 degrees latitude resolution\n# -->Meteorological data from ECMWF: 3 hourly operational analysis/forecasts on 0.25 x 0.25 degree\n')
    f.write('# STILT footprints code: ' + station + '\n')
    f.write('# STILT altitude above ground: ' + str(stilt_station_alt) + 'm\n')
    f.write('# STILT position latitude: ' + str(stilt_station_lat) + '°N\n')
    f.write('# STILT position longitude: ' + str(stilt_station_lon) + '°E\n')
    f.write(date_range_text)
    f.write('# Footprint hours: ' + timeselect_list_string + '\n')
    f.write('# delta14C background file: ' + background_filename + '\n')
    
    if 'flask' in radiocarbonObject.settings:
        f.write('# Data from flask: ' + str(radiocarbonObject.settings['flask']) + '\n')
    
    #only data from heidelberg will have this
    if 'crlSampler' in radiocarbonObject.settings:
        f.write('# CRL Sampler: ' + str(radiocarbonObject.settings['crlSampler']) + '\n')

    f.write('# Date of analysis: ' + str(date_today) + '\n')
    
    if df_type=='Station':
        
        dfDelta14CStation = radiocarbonObject.dfDelta14CStation
        dfDelta14CStation.to_csv(f,index=False)
        
    elif df_type=='Facility':
        dfDelta14CFacility = radiocarbonObject.dfDelta14CFacility
        dfDelta14CFacility.to_csv(f,index=False)
        
    elif df_type=='StationResample':
        
        dfDelta14CStationResample = radiocarbonObject.dfDelta14CStationResample
        
        
        dfDelta14CStationResample_columns = dfDelta14CStationResample.columns.tolist()

        dfDelta14CStationResample_columns.remove('date_start')
        dfDelta14CStationResample_columns.remove('date_end')
        dfDelta14CStationResample_columns.remove('count')
        dfDelta14CStationResample_columns.remove('count_nan')
        dfDelta14CStationResample_columns.remove('for_index')
        dfDelta14CStationResample_columns.insert(0, 'date_start')
        dfDelta14CStationResample_columns.insert(1, 'date_end')
        dfDelta14CStationResample_columns.insert(2, 'count')
        dfDelta14CStationResample_columns.insert(3, 'count_nan')
        
        dfDelta14CStationResample = dfDelta14CStationResample.drop(columns='for_index')
        
        dfDelta14CStationResample = dfDelta14CStationResample[dfDelta14CStationResample_columns]
        
        dfDelta14CStationResample.to_csv(f, index=False)
        
    elif df_type=='FacilityResample':
        
        if radiocarbonObject.dfFacilitiesOverThreshold is not None:
            dfDelta14CFacilityResample = radiocarbonObject.dfDelta14CFacilityResample

            dfDelta14CFacilityResample_columns = dfDelta14CFacilityResample.columns.tolist()
            dfDelta14CFacilityResample_columns.remove('date_start')
            dfDelta14CFacilityResample_columns.remove('date_end')
            dfDelta14CFacilityResample_columns.remove('count')
            dfDelta14CFacilityResample_columns.remove('count_nan')
            dfDelta14CFacilityResample_columns.remove('for_index')
            dfDelta14CFacilityResample_columns.insert(0, 'date_start')
            dfDelta14CFacilityResample_columns.insert(1, 'date_end')
            dfDelta14CFacilityResample_columns.insert(2, 'count')
            dfDelta14CFacilityResample_columns.insert(3, 'count_nan')

            dfDelta14CFacilityResample = dfDelta14CFacilityResample.drop(columns='for_index')

            dfDelta14CFacilityResample = dfDelta14CFacilityResample[dfDelta14CFacilityResample_columns]

            dfDelta14CFacilityResample.to_csv(f, index=False)
        else:
            f.write('No nuclear facilities contributing > ' + str(radiocarbonObject.settings['threshold']) +' permil')

    elif df_type=='FacilityMap':
        
        if radiocarbonObject.dfFacilitiesOverThreshold is not None:
        
            dfFacilitiesOverThreshold = radiocarbonObject.dfFacilitiesOverThreshold

            dfFacilitiesOverThreshold.to_csv(f, index=False)
        else:
            f.write('No nuclear facilities contributing > ' + str(radiocarbonObject.settings['threshold']) +' permil')
    
    elif df_type=='CP_data' or df_type=='HEI_data':
        
        #think about naming
        dfDataFromCP = radiocarbonObject.df_for_export
        dfDataFromCP.to_csv(f, index=False)

    f.close()
    

def save_settings(radiocarbonObject, df_type=''):
    
    # save settings as json file
    file = os.path.join(radiocarbonObject.settings['output_folder'], radiocarbonObject.settings['date/time generated'] + radiocarbonObject.stationId + '_' + df_type +'_settings.json')
    with open(file, 'w') as f:
        json.dump(radiocarbonObject.settings, f, indent=4)
        
#change to save_data_model   
def save_data(radiocarbonObject):
    
    save_settings(radiocarbonObject)
    #save the nuclear facility results
    #download_results_nuclear_facility_influence_by_station(radiocarbonObject)
    download_result(radiocarbonObject, df_type='Station')
    
    if radiocarbonObject.settings['facilityInclusion']==True:
        
        download_result(radiocarbonObject, df_type='Facility')
        
    #settings resample can be 7D for 7 days
    if radiocarbonObject.settings['resample'][0] == 'M' or int(radiocarbonObject.settings['resample'][0])>0:
        
        #need to append the resampled result to the radiocarbon object before doing this step. 
        #wrong in description - no radd year?
        download_result(radiocarbonObject, df_type='StationResample')
        
        if radiocarbonObject.settings['facilityInclusion']:
            download_result(radiocarbonObject, df_type='FacilityResample')

            download_result(radiocarbonObject, df_type='FacilityMap')
            
def save_data_cp(radiocarbonObject):
    
    save_settings(radiocarbonObject, df_type='CP_data')
    
    #if works - change name
    download_result(radiocarbonObject, df_type='CP_data')
    
def save_data_meas(radiocarbonObject, df_type):
    
    save_settings(radiocarbonObject, df_type)
    

    download_result(radiocarbonObject, df_type)
    
def display_info_html_table(radiocarbonObject, meas_data=False):
    
    stilt_station = radiocarbonObject.stationId
    stilt_station_alt = radiocarbonObject.settings['stilt']['alt']
    stilt_station_lat = radiocarbonObject.settings['stilt']['lat']
    stilt_station_lon = radiocarbonObject.settings['stilt']['lon']
    date_today = current_date.today()
    background_filename = radiocarbonObject.settings['backgroundFilename']
    
    if meas_data==False:

        html_date_range = '<b>Footprint selection (date range):</b> ' + str(min(radiocarbonObject.dateRange)) + ' to ' + str(max(radiocarbonObject.dateRange)) + '<br>'
        
        timeselect_list = radiocarbonObject.settings['timeOfDay']
        timeselect_string=[str(value) for value in timeselect_list]
        timeselect_string =':00, '.join(timeselect_string) + ':00 (UTC)<br>'
        
        html_timeselect_string = '<b>Footprint selection (hour(s)):</b> ' + timeselect_string
        
        html_meas_station = ''
        
        html_date_range_meas = ''
        
        flask_string = ''
        
        clr_string = ''
        
    else:
        
        html_timeselect_string = ''
        html_date_range = ''
        
        if 'clrSampler' in radiocarbonObject.settings:
            clr_string= '<b>CLR Sampler</b>: ' + radiocarbonObject.settings['clrSampler'] 
        else:
            clr_string = ''

        meas_station = stilt_station[0:3]
        try:
            meas_sampling_height = radiocarbonObject.settings['samplingHeightMeas']
            
        except:
            meas_sampling_height = ''
            
        html_meas_station = '<br><b>Location (measurements):</b> ' + meas_station + '<br><b>Sampling height, elevation above ground (measurements):</b> ' + str(meas_sampling_height) + 'm<br>'
        
        if 'TIMESTAMP' in radiocarbonObject.measuredData.columns:
            start_date_column = 'TIMESTAMP'
           
        else:
            
            start_date_column = radiocarbonObject.settings['startDateColumn']
            
        if 'flask' in radiocarbonObject.settings:
            
            flask_string = '<br><b>Measurements from flask</b>: ' + str(radiocarbonObject.settings['flask']) 
            
        else:
            flask_string = ''
                
        html_date_range_meas = '<b>Date start of first measurement</b>: ' + str(min(radiocarbonObject.measuredData[start_date_column])) + '<br>' + \
        '<b>Date start of last measurement</b>: ' + str(max(radiocarbonObject.measuredData[start_date_column])) + '<br>'

    display(HTML('<p style="font-size:15px;"><b>Information relevant for analysis (also included in csv-file if chosen to download)</b><br><br> '\
    'Yearly average radiocarbon emissions data downloaded 2020-08-25 from <a href="https://europa.eu/radd/" target="_blank">European Commission RAdioactive Discharges Database</a>.<br><br>' + \
    '<b>STILT transport model used to generate footprints:</b><br><ul><li>10 days backward simulation</li><li>1/8° longitude x 1/12° latitude resolution</li><li>Meteorological data from ECMWF: 3 hourly operational analysis/forecasts on 0.25 x 0.25 degree</li></ul>' +\
    '<b>STILT footprints code:</b> ' + stilt_station + '<br><b>STILT altitude above ground:</b> ' + str(stilt_station_alt) + 'm<br>' + \
    '<b>STILT position latitude:</b> ' + str(stilt_station_lat) + '°N<br>' + '<b>STILT position longitude:</b> ' + str(stilt_station_lon) + '°E<br>' + html_date_range + html_timeselect_string + flask_string + html_meas_station  + html_date_range_meas +  clr_string + \
    '<br><br><b>∆14C background file</b>: ' + background_filename + '<br><br><b>Date of analysis:</b> ' + str(date_today) + '</p>'))
    
    
###########################################
# FUNCTIONS USED IN THE PRIVATE NOTEBOOK ONLY

#add count and count_nan variables. also date_start and date_end.
def radiocarbon_hei_results(radiocarbonObjectMeas):
    
    stilt_station = radiocarbonObjectMeas.stationId
    timeselect_list = radiocarbonObjectMeas.settings['timeOfDay']
    timeselect_list_sting=', '.join(str(x) for x in timeselect_list)
    background_filename = radiocarbonObjectMeas.settings['backgroundFilename']
    download_option = radiocarbonObjectMeas.settings['downloadOption']
    meas_station = radiocarbonObjectMeas.stationId[0:3]
    meas_sampling_height = radiocarbonObjectMeas.settings['samplingHeightMeas']
    
    measurement_column = radiocarbonObjectMeas.settings['measurementColumn']
    start_date_column = radiocarbonObjectMeas.settings['startDateColumn']
    end_date_column = radiocarbonObjectMeas.settings['endDateColumn']
    
    std_error_column = radiocarbonObjectMeas.settings['stdErrorColumn']
   
    stilt_station_alt=radiocarbonObjectMeas.settings['stilt']['alt']
    stilt_station_name=radiocarbonObjectMeas.settings['stilt']['name']
    stilt_station_lat=radiocarbonObjectMeas.lat
    stilt_station_lon=radiocarbonObjectMeas.lon
    
    date_today= current_date.today()

    #dataframe with all the measurements. Loop over.
    radiocarbon_data= radiocarbonObjectMeas.measuredData

    #the information needed to calculate modelled delta C14 and fossil fuel component
    bg_values=get_background_values_nuclear_corrected(background_filename)

    #'flask' in settings only if from hei... can be true or false. If true, need additional columns
    #(for "surrounding" nuclear comtamination)
    if radiocarbonObjectMeas.settings['flask']:
        df_for_export = pd.DataFrame(columns=['date_start','date_end','meas_date_start', 'meas_date_end', 'Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear', 'delta14Cnuclear_plus3', 'delta14Cnuclear_plus6', 'delta14Cnuclear_plus9', 'delta14Cnuclear_minus3', 'delta14Cnuclear_minus6', 'delta14Cnuclear_minus9', 'delta14C_fossil_fuel', 'delta14C_modelled','radd_year','count', 'count_nan'])
        
    else:
            
        df_for_export = pd.DataFrame(columns=['date_start','date_end','meas_date_start', 'meas_date_end', 'Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year','count', 'count_nan'])
    
    #this dataframe is added to twice for each measurement (since integrated - start and end data)
    #the 'date' column will first get the same value as SamplingStartDate and the second time the 
    #same value as SamplingEndDate
    df_for_plot = pd.DataFrame(columns=['date', 'date_start','date_end', 'meas_date_start', 'meas_date_end', 'Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','radd_year', 'count', 'count_nan'])
    
    index=0
    #the plot dataframe will be added to twice in each loop (start - and end time same values for line in graph
    #across integration time. 
    index_plot=0

    #access many at the same time (all the entries - one for each radiocarbon measurement)
    #for each entry at the carbon portal (not all will be used - only when footprints for the same time period)
    first=True
    for (radiocarbon_measurement, measurement_start_date, measurement_end_date, std_deviation) in zip(radiocarbon_data[measurement_column], radiocarbon_data[start_date_column], radiocarbon_data[end_date_column], radiocarbon_data[std_error_column]):
        

        measurement_start_date=pd.Timestamp(measurement_start_date)
               
        measurement_end_date=pd.Timestamp(measurement_end_date)
        
        # the model start date must match the STILT model hours (0, 3, 6, 9, 12, 15, 18, 21)
        # want to keep the orignal date/times though (measurement_start_date/measurement_end_date)
        measurement_start_date_model = measurement_start_date
        measurement_end_date_model = measurement_end_date
 
        if measurement_start_date.hour not in timeselect_list or measurement_start_date.minute>0:

            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_start_date.hour))

            measurement_start_date_model = dt.datetime(int(measurement_start_date.year), int(measurement_start_date.month), int(measurement_start_date.day), updated_hour, 0)
        
        #measurement_start_date here previously 
        if measurement_end_date.hour not in timeselect_list or measurement_end_date.minute>0:
            
            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_end_date.hour))
            
            measurement_end_date_model = dt.datetime(int(measurement_end_date.year), int(measurement_end_date.month), int(measurement_end_date.day), updated_hour, 0)
            
        #now filtered date_range_measured.
        
        date_range_measured = date_range_hour_filtered(measurement_start_date_model, measurement_end_date_model, timeselect_list)

        if date_range_measured.empty:

            print('no footprints for date range of measured concentration (' + str(measurement_start_date) + ' to ' + str(measurement_end_date))
            
            continue
        if radiocarbonObjectMeas.settings['flask']==False:
            modelled_concentration = read_stilt_timeseries(stilt_station, date_range_measured)
        else:
            date_range_flask = pd.date_range((measurement_start_date_model - timedelta(hours=9)), (measurement_end_date_model + timedelta(hours=9)), freq='3H')
            modelled_concentration = read_stilt_timeseries(stilt_station, date_range_flask)
            

        #which radd-year(s) - radiocarbon data - used for each sample. Max 2... integration time about 14 days.
        year_list=[]

        #rather df_each_footprint? 
        df_each_meas = pd.DataFrame(columns=['delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'])

        index_each_meas = 0
        count_nan = 0
        
        if radiocarbonObjectMeas.settings['flask']:
            
            measurement_start_date_model_plus3 = measurement_start_date_model+timedelta(hours=3)
            measurement_start_date_model_plus6 = measurement_start_date_model+timedelta(hours=6)
            measurement_start_date_model_plus9 = measurement_start_date_model+timedelta(hours=9)
            measurement_end_date_model_minus3 = measurement_end_date_model-timedelta(hours=3)
            measurement_end_date_model_minus6 = measurement_end_date_model-timedelta(hours=6)
            measurement_end_date_model_minus9 = measurement_end_date_model-timedelta(hours=9)
            
            list_dates_flask = [measurement_start_date_model_plus3, measurement_start_date_model_plus6, measurement_start_date_model_plus9, measurement_end_date_model_minus3,measurement_end_date_model_minus6, measurement_end_date_model_minus9]
            
            list_plus_minus_nuclear_values = []
            first_in_flask=True
            for date_flask in list_dates_flask:
                
                filename=(pathFP+stilt_station+'/'+str(date_flask.year)+'/'+str(date_flask.month).zfill(2)+ '/'
                 +str(date_flask.year) + 'x'+ str(date_flask.month).zfill(2) + 'x' + str(date_flask.day).zfill(2) + 'x' + str(date_flask.hour).zfill(2) +'/foot')

                if os.path.isfile(filename)==False:
                    
                    list_plus_minus_nuclear_values.append(np.nan)
                    
                    continue

                f_fp = cdf.Dataset(filename)

                fp_current=f_fp.variables['foot'][:,:,:]

                modelled_concentration_value=modelled_concentration['co2.stilt'][date_flask]/1000000

                #in micromol for fossil fuel
                modelled_concentration_date_time=modelled_concentration['co2.stilt'][date_flask]

                try:
                    if not isinstance(modelled_concentration_value, float) and math.isnan(modelled_concentration_value)==False:
                        continue 

                #happen for ex date 2017-01-01 00:00. A series because two are matched with the date. 
                except:

                    continue

                date_for_fit_JFJ=pd.Timestamp(date_flask.year, date_flask.month, date_flask.day)

                try:
                    background_value=bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'CorrectedFIT'].iloc[0]

                #when no match with date in bg_values, find closest and match
                except:

                    nearest_date_test=nearest_date(bg_values.DateTime, date_flask)

                    background_value=bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'CorrectedFIT'].iloc[0]

                try:    
                    JFJ_foss = bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'ffCO2'].iloc[0]
                except:
                    nearest_date_test=nearest_date(bg_values.DateTime, date_flask)
                    JFJ_foss = bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'ffCO2'].iloc[0]

                #correct for fossil fuel emissions in the at supposedly clean background site
                #if smaller component at the selected station, the fossil fuel component (delta 14C) will be positive rather than negative.
                foss_fuel_station_minus_jfj_ppm=(modelled_concentration['co2.fuel.oil'][date_flask]+modelled_concentration['co2.fuel.gas'][date_flask]+\
                                     modelled_concentration['co2.fuel.coal'][date_flask]-JFJ_foss)

                
                if first_in_flask==True or date_flask.year!=int(year):

                    year=date_flask.year

                    fp_radiocarbon_bq_s_m2, radd_year = access_best_nuclear_emission_data(year, display_message=False)

                    first_in_flask=False
                    
                #keeping nuclear contamination it a grid (fp_radiocarbon_bq_s_m2*fp_current) to see the resulting shift in radiocarbon caused by each individual cell
                delta_radiocarbon_contribution_grid=(((fp_radiocarbon_bq_s_m2*fp_current) / (modelled_concentration_value* Mc * Aabs)) ) *1000

                #get one value summed value of this grid for each date/time. What is used in the time series output from running this cell
                delta_radiocarbon_contribution_summed= delta_radiocarbon_contribution_grid[:][:].sum()
                
                list_plus_minus_nuclear_values.append(delta_radiocarbon_contribution_summed)

        #now will print a warning for each measurement. 
        for date in date_range_measured:

            filename=(pathFP+stilt_station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename)==False:
                count_nan = count_nan + 1
                continue

            f_fp = cdf.Dataset(filename)

            fp_current=f_fp.variables['foot'][:,:,:]

            modelled_concentration_value=modelled_concentration['co2.stilt'][date]/1000000

            #in micromol for fossil fuel
            modelled_concentration_date_time=modelled_concentration['co2.stilt'][date]

            try:
                if not isinstance(modelled_concentration_value, float) and math.isnan(modelled_concentration_value)==False:
                    continue 

            #happen for ex date 2017-01-01 00:00. A series because two are matched with the date. 
            except:

                continue

            date_for_fit_JFJ=pd.Timestamp(date.year, date.month, date.day)

            try:
                background_value=bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'CorrectedFIT'].iloc[0]

            #when no match with date in bg_values, find closest and match
            except:

                nearest_date_test=nearest_date(bg_values.DateTime, date)

                background_value=bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'CorrectedFIT'].iloc[0]

            try:    
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == date_for_fit_JFJ, 'ffCO2'].iloc[0]
            except:
                nearest_date_test=nearest_date(bg_values.DateTime, date)
                JFJ_foss = bg_values.loc[bg_values['DateTime'] == nearest_date_test, 'ffCO2'].iloc[0]

            #correct for fossil fuel emissions in the at supposedly clean background site
            #if smaller component at the selected station, the fossil fuel component (delta 14C) will be positive rather than negative.
            foss_fuel_station_minus_jfj_ppm=(modelled_concentration['co2.fuel.oil'][date]+modelled_concentration['co2.fuel.gas'][date]+\
                                 modelled_concentration['co2.fuel.coal'][date]-JFJ_foss)

            modelled_delta_c14_not_nuclear_corrected=(foss_fuel_station_minus_jfj_ppm/modelled_concentration_date_time)*(background_value+1000)-background_value

            modelled_delta_c14_not_nuclear_corrected=-modelled_delta_c14_not_nuclear_corrected

            fossil_fuel_component=modelled_delta_c14_not_nuclear_corrected-background_value


            #if first time (first defined out of loop)- access the radiocarbon data for specific year.
            #also, if the year of the "current" date is new (ex jan 1 2016). Access the data for the current year instead. 
            if first==True or date.year!=int(year):

                year=date.year

                fp_radiocarbon_bq_s_m2, radd_year = access_best_nuclear_emission_data(year)

                first=False

            #keeping nuclear contamination it a grid (fp_radiocarbon_bq_s_m2*fp_current) to see the resulting shift in radiocarbon caused by each individual cell
            delta_radiocarbon_contribution_grid=(((fp_radiocarbon_bq_s_m2*fp_current) / (modelled_concentration_value* Mc * Aabs)) ) *1000

            #get one value summed value of this grid for each date/time. What is used in the time series output from running this cell
            delta_radiocarbon_contribution_summed= delta_radiocarbon_contribution_grid[:][:].sum()

            #modelled delta 14C - nuclear corrected (not included in the Levin et al paper)
            modelled_delta_c14_nuclear_corrected=modelled_delta_c14_not_nuclear_corrected+delta_radiocarbon_contribution_summed

            #'delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled'
            df_each_meas.loc[index_each_meas] = [background_value, delta_radiocarbon_contribution_summed, fossil_fuel_component, modelled_delta_c14_nuclear_corrected]

            index_each_meas=index_each_meas + 1

            #if always using the same RADD year for all footprints in integrated sample (not ex dec 20 to jan 4)
            if radd_year not in year_list:
                year_list.append(radd_year)

        #average given date-time. If there are values to average (not division by 0)
        #shift per integrated time is nuclear contamination (delta 14C)
        if len(df_each_meas)>0:


            #get the correct information with regards to what RADD data has been used. 
            if len(year_list)>1:
                radd_data_year_export=(year_list[0] + '&' + year_list[1])   
            elif len(year_list)==1:
                radd_data_year_export=year_list[0]
            else:
                radd_data_year_export='no data'

            shift_nuclear=df_each_meas["delta14C_nuclear"].mean()
            shift_fossil_fuel=df_each_meas["delta14C_fossil_fuel"].mean()
            shift_background=df_each_meas["delta14C_background"].mean()
            shift_modelled=df_each_meas["delta14C_modelled"].mean()
            
            count=len(date_range_measured)
            #count_nan=

            #dataframe already created at the top. here append whole row with values for export. one row per integrated sample
            if radiocarbonObjectMeas.settings['flask']:
                df_for_export.loc[index] = [measurement_start_date_model, measurement_end_date_model,measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, list_plus_minus_nuclear_values[0], list_plus_minus_nuclear_values[1], list_plus_minus_nuclear_values[2], list_plus_minus_nuclear_values[3], list_plus_minus_nuclear_values[4],list_plus_minus_nuclear_values[5], shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]
                
            else: 
                df_for_export.loc[index] = [measurement_start_date_model, measurement_end_date_model,measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]

            #index to move to the next row for the next integrated sample 
            index=index+1  

            df_for_plot.loc[index_plot] = [measurement_start_date_model, measurement_start_date_model, measurement_end_date_model, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]

            index_plot = index_plot + 1

            #measurement_end_date into date column. otherwise same values as above record.
            df_for_plot.loc[index_plot] = [measurement_end_date_model, measurement_start_date_model, measurement_end_date_model, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled, radd_year, count, count_nan]
            index_plot = index_plot + 1
                
    return df_for_export, df_for_plot
               
 