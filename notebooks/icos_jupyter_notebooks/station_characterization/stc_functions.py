# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 08:04:31 2020

@author: Ida Storm 

Functions to run the station characterization notebook on exploredata.

"""

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import numpy as np
from netCDF4 import Dataset
import textwrap
import datetime as dt
import os
import six
import requests
import tex
from IPython.core.display import display, HTML 
import netCDF4 as cdf
import cartopy
cartopy.config['data_dir'] = '/data/project/cartopy/'
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature
import warnings
warnings.filterwarnings('ignore')
import json

#path to data such as population data and land cover data
stcDataPath='/data/project/stc/'

#path to footprints
pathFP='/data/stiltweb/stations/'

#added to not show the land cover bar graph that is being saved for the PDF which is different size than the one displayed
matplotlib.pyplot.ioff()

#Earth's radius in km (for calculating distances between the station and cells)
R = 6373.8

#Colors for the land cover plots
dictionary_color = {'Broad leaf forest': {'color': '#4c9c5e'}, 'Coniferous forest':{'color':'#CAE0AB'}, 'Mixed forest':{'color':'#90C987'}, 'Ocean':{'color':'#1964B0'}, 'Other':{'color':'#882E72'}, 'Grass/shrubland':{'color':'#F1932D'}, 'Cropland':{'color': '#521A13'}, 'Pasture':{'color':'#F7F056'}, 'Urban':{'color':'#DC050C'}, 'Unknown':{'color':'#777777'}}

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

# function to read STILT concentration time series (new format of STILT results)
# function to read STILT concentration time series (new format of STILT results)
def read_stilt_timeseries(station,date_range,timeselect_list):
    url = 'https://stilt.icos-cp.eu/viewer/stiltresult'
    headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}

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
                   '"co2.fuel.gas","co2.fuel.bio","co2.fuel.waste", "co2.energy","co2.transport", "co2.industry",'+
                   '"co2.other_categories", "co2.residential", "co2.cement", "co2.background",'+
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
def date_range_hour_filtered(date_range, timeselect_list):
    
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
          
    return date_range

def area_footprint_based_on_threshold(input_footprint, fp_lat, fp_lon, threshold):

    #total sensitivity - use this value to calculate what the sensitivity of the ex 50% footprint it (threshold)
    sum_sensitivity_values=sum(input_footprint.flatten())

    threshold_sensitivity=sum_sensitivity_values*threshold

    #create a dataframe that will have the updated sensitivity values + the steps on the way
    df_sensitivity = pd.DataFrame()

    #one column with the original sensitivity values. Has an index that will be used to sort back to 
    #this order (flattened 2D... back to 2D with updated sensitivity values in last step)
    df_sensitivity['sensitivity']=input_footprint.flatten()
    
    #sensitivity values sorterd from largest to smallest
    df_sensitivity_sorted=df_sensitivity.sort_values(by=['sensitivity'], ascending=False)
    
    #another column that has the cumilated sum of the values in the sensitivity column.
    #used to determine when the footprint threshold is met. 
    df_sensitivity_sorted['cumsum_sens']=df_sensitivity_sorted.cumsum()
    
    #mask threshold: when the cumulative sum is over the threshold - these values are assigned 0.
    #to be multiplied with the original sensitivity values (disregard the ones with value 0)
    df_sensitivity_sorted['mask_threshold']=df_sensitivity_sorted['cumsum_sens']

    if threshold==1:

        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['sensitivity']==0, 0, 1)
    else:
        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['cumsum_sens']>=threshold_sensitivity, 0, 1)
        
    #sort it back (so in correct lat/lon order for "packing back up" to 2D)
    df_sensitivity_upd=df_sensitivity_sorted.sort_index()
    #want a footprint with 0/1 for see or not see also 
    list_mask_threshold=df_sensitivity_upd['mask_threshold'].tolist()
    
    upd_footprint_see_not_see=np.array(list_mask_threshold).reshape((len(fp_lat), len(fp_lon)))
    
    #a NetCDF file with the grid size calues in m2
    f_gridarea = cdf.Dataset(stcDataPath + 'gridareaSTILT.nc')
    #area stored in "cell_area". Convert to km2
    gridarea = f_gridarea.variables['cell_area'][:]/1000000
    
    area_within_threshold = sum((upd_footprint_see_not_see * gridarea).flatten())

    return area_within_threshold

def import_landcover_HILDA(year='2018'):
    
    name_data = 'hilda_lulc_'+ year +'.nc' 
    
    all_hilda_classes= Dataset(stcDataPath + name_data)

    #access all the different land cover classes in the .nc files:
    cropland = all_hilda_classes.variables['cropland'][:,:]
    ocean = all_hilda_classes.variables['ocean'][:,:]
    forest_decidious_broad_leaf = all_hilda_classes.variables['f_de_br_le'][:,:]
    forest_decidious_needle_leaf = all_hilda_classes.variables['f_de_ne_le'][:,:]
    forest_evergreen_broad_leaf = all_hilda_classes.variables['f_eg_br_le'][:,:]
    forest_evergreen_needle_leaf = all_hilda_classes.variables['f_eg_ne_le'][:,:]
    mixed_forest = all_hilda_classes.variables['forest_mix'][:,:]
    forest_unknown = all_hilda_classes.variables['forest_unk'][:,:]
    grass_shrub = all_hilda_classes.variables['grass_shru'][:,:]
    other_land = all_hilda_classes.variables['other_land'][:,:]
    pasture = all_hilda_classes.variables['pasture'][:,:]
    urban = all_hilda_classes.variables['urban'][:,:]
    water = all_hilda_classes.variables['water'][:,:]
    unknown = all_hilda_classes.variables['unknown'][:,:]
    
    # aggregated classes:
    broad_leaf_forest = forest_decidious_broad_leaf + forest_evergreen_broad_leaf 
    coniferous_forest = forest_decidious_needle_leaf+ forest_evergreen_needle_leaf
    mixed_forest = mixed_forest + forest_unknown
    other = other_land + water
       
    return broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown

def import_population_data():
   
    pop_data= Dataset(stcDataPath + 'GPW_population_2020.nc')
    fp_pop=pop_data.variables['pop_2020'][:,:]

    return fp_pop

def import_point_source_data():

    point_source_data= Dataset(stcDataPath+ 'E_PRTR_pointsource_2017.nc')

    #emissions in kg/year in the variable "Sum_Tota_1"
    fp_point_source=point_source_data.variables['Sum_Tota_1'][:,:]

    # different from population data: can translate the emissions within each stilt cell
    # to the effect it will have to the final CO2 concentrations at the stations.
    # just need to get it in the right unit (micromole/m2s) and multiply by the individual or aggregated footprints

    # divide by the molar weight in kg. 12 (C)+16(O)+16(O) =44 0.044 in kg.
    # get number of moles of C this way. Want it in micromole though: 1 mole= 1000000 micromole
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

def date_and_time_string_for_title(date_range, timeselect_list):
    
    date_index_number=len(date_range) - 1
    
    timeselect_string=[str(value) for value in timeselect_list]
    timeselect_string =':00, '.join(timeselect_string) + ':00'

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
              vmin=0.0001, vmax=None, colors='GnBu'): 

    station=myStation.stationId
    lon=myStation.lon
    lat=myStation.lat
    unit=myStation.settings['unit']
    if unit=='percent':
        unit='%'
    else:
        if label=='point source contribution':
            unit='(ppm)'
        if label=='population sensitivity':
            unit='(population * (ppm /(μmol / (m²s))))'
        if label=='sensitivity':
            unit='(ppm /(μmol / (m²s)))'

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
    
    ax.add_feature(countries, edgecolor='grey', linewidth=0.5)
   
    reader = shpreader.Reader('/data/project/cartopy/shapefiles/natural_earth/cultural/ne_10m_admin_0_countries.shp')
    
    # Color countries that miss data for population and point source respectively
    if label == 'point source contribution':   
        list_countries_to_add = ['Russian Federation', 'Belarus', 'Ukraine', 'Moldova', 'Turkey', 'Tunisia', 'Algeria', 'Morocco','Bosnia and Herzegovina', 'Serbia', 'Montenegro', 'Kosovo', 'Albania', 'Macedonia']
        legend_title= 'Countries with no point source data'

        for country_to_add in list_countries_to_add:

            country_information = [country for country in reader.records() if country.attributes["NAME_LONG"] == country_to_add][0]
            country_shape = ShapelyFeature([country_information.geometry], ccrs.PlateCarree(), facecolor="white", hatch="/", edgecolor='lightgrey', lw=0.3)                     
            ax.add_feature(country_shape)
        
        # add a legend 
        proxy_artist = mpatches.Rectangle((0, 0), 1, 0.1, facecolor="white", hatch="/", edgecolor='lightgrey', lw=0.5)
        ax.legend([proxy_artist], [legend_title], loc='upper left', fancybox=True)
            
    cmap = plt.get_cmap(colors)
    cmap.set_under(color='white')  
    
    if linlog == 'linear':
        
        im = ax.imshow(field[:,:],interpolation=None,origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='neither')
        cbar.set_label(label+'  '+unit)

    else:
        
        im = ax.imshow(np.log10(field)[:,:],interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='neither')
        cbar.set_label(label+'  log$_{10}$ '+unit)
    
    ax.text(0.01, -0.25, 'min: %.2f' % np.min(field[:,:]), horizontalalignment='left',transform=ax.transAxes)
    ax.text(0.99, -0.25, 'max: %.2f' % np.max(field[:,:]), horizontalalignment='right',transform=ax.transAxes)
    
    #show station location if station is provided
    if station != '':

        ax.plot(lon,lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())

        
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
    
    fp_pop= import_population_data()
    fp_point= import_point_source_data()
    
    #same function used to all three types of map
    if rose_type=='sensitivity':
        
        #only want to look at the aggregated footprint - not multiplied by anciallary datalayer 
        grid_to_display=fp
        
    elif rose_type=='point source contribution':
        
        grid_to_display=fp*fp_point
        
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
    rosedata=df_sensitivity_map.assign(Interval_bins=lambda df: pd.cut(df['distance'], bins=interval_bins, labels=interval_labels, right=True))

    rosedata=rosedata.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))
   
    #the 360 degree are the same as 0:
    rosedata=rosedata.replace({'Degree_bins': {360: 0}})

    #the combination of the distance and direction columns is used to create a unique column value for all cells
    #with certain direction/distance combination.
    #make it to string to be able to combine.
    rosedata['key']=rosedata['Interval_bins'].astype(str) + ' ' + rosedata['Degree_bins'].astype(str) 

    #group by the unique combination of direction and distance
    rosedata_groupby=rosedata.groupby(by=['key'], as_index=False)['sensitivity'].sum().reset_index()

    #merge between the 192000 cells and the "groupedby" values: each cell in a specific direction and distance will
    #get the sum of the cells in that same specific bin. Same color on the map corresponing to % or absolute sensitivity.
    #reset_index() creates a column with the original index of the dataframes that are joined. Needed to sort the dataframe
    #in the next spted because default is to sort by the key used. 
    rosedata=rosedata.reset_index().merge(rosedata_groupby, left_on='key', right_on='key', sort=False)

    #sort by the original index of the 192000 cells: 
    rosedata=rosedata.sort_values(by=['index_x'])

    #x is the "fist" (rosedata.merge) dataframe that was merged (the 192000 individual cells) 
    #y is the dataframe that is merged to the first. Both columns name "sensitivity". 
    #sensitivity_y is the merged data - the summarized sensitivity value for the whole bin (direction and distance bin)
    rosedata_list=rosedata['sensitivity_y'].tolist()

    #now starts the process of "packing it back up" so that it can be displayed as a map (same format as the netCDF files with 480
    #lists of lists - the first list is all tha values that has "the first" latitude value and all 400 different longitude values)
    #calculate the % sensitivity - can be changed to absolute sensitivity
    if unit=='percent':
        rosedata_list=[(sensitivity_value/total_sensitivity)*100 for sensitivity_value in rosedata_list]

    #the "netcdf simulation" (see text above)
    rosedata_list_of_lists=[]

    index=0
    while index<192000:
        index_to=index+400

        #for each list: need to grab the 400 values that are the combination of the same latitude value
        #but different longitude values
        rosedata_list_of_lists.append(rosedata_list[index:index_to])

        #start at the next 400 in the list in the next turn of the loop:
        index=index+400

    #numpy array works to display in map
    rosedata_array=np.array(rosedata_list_of_lists) 
        
    caption=(unit.capitalize() + ' ' + rose_type + ' given direction and distance')
          
    polar_map=plot_maps(myStation, rosedata_array, title=caption, label=rose_type, 
                   linlog='linear', zoom='', vmin=0.0001, vmax=None, colors=colorbar)
        
    return polar_map, caption
    

def land_cover_bar_graph(myStation):    
    
    fp_lon=myStation.fpLon
    fp_lat=myStation.fpLat
    degrees=myStation.degrees
    fp=myStation.fp

    #get all the land cover data from netcdfs 
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')
    
    #land cover classes (imported in the land cover section):
    broad_leaf_forest=fp*broad_leaf_forest
    coniferous_forest=fp*coniferous_forest
    mixed_forest=fp*mixed_forest
    ocean=fp*ocean
    other=fp*other
    grass_shrub=fp*grass_shrub
    cropland=fp*cropland
    pasture=fp*pasture
    urban=fp*urban
    unknown=fp*unknown
                
    #lists of these values
    broad_leaf_forest_values = [item for sublist in broad_leaf_forest[0] for item in sublist]
    coniferous_forest_values = [item for sublist in coniferous_forest[0] for item in sublist]
    mixed_forest_values = [item for sublist in mixed_forest[0] for item in sublist]
    ocean_values = [item for sublist in ocean[0] for item in sublist]
    other_values = [item for sublist in other[0] for item in sublist]
    grass_shrub_values = [item for sublist in grass_shrub[0] for item in sublist]
    cropland_values = [item for sublist in cropland[0] for item in sublist]
    pasture_values = [item for sublist in pasture[0] for item in sublist]
    urban_values = [item for sublist in urban[0] for item in sublist]
    unknown_values = [item for sublist in unknown[0] for item in sublist]
        
        
    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_broad_leaf_forest = pd.DataFrame({'landcover_vals': broad_leaf_forest_values,
                               'degrees': degrees,
                               'landcover_type':'Broad leaf forest'})
    
    df_coniferous_forest = pd.DataFrame({'landcover_vals': coniferous_forest_values,
                           'degrees': degrees,
                           'landcover_type':'Coniferous forest'})
    
    df_mixed_forest = pd.DataFrame({'landcover_vals': mixed_forest_values,
                           'degrees': degrees,
                           'landcover_type':'Mixed forest'})
    
    df_ocean = pd.DataFrame({'landcover_vals': ocean_values,
                           'degrees': degrees,
                           'landcover_type':'Ocean'})
    
    df_other = pd.DataFrame({'landcover_vals': other_values,
                           'degrees': degrees,
                           'landcover_type':'Other'})
    
    df_grass_shrub = pd.DataFrame({'landcover_vals':  grass_shrub_values,
                           'degrees': degrees,
                           'landcover_type':'Grass/shrubland'})
    
    df_cropland = pd.DataFrame({'landcover_vals':  cropland_values,
                           'degrees': degrees,
                           'landcover_type':'Cropland'})
    
    df_pasture = pd.DataFrame({'landcover_vals': pasture_values,
                           'degrees': degrees,
                           'landcover_type':'Pasture'})
    
    df_urban = pd.DataFrame({'landcover_vals':  urban_values,
                           'degrees': degrees,
                           'landcover_type':'Urban'})
    
    df_unknown = pd.DataFrame({'landcover_vals':  unknown_values,
                           'degrees': degrees,
                           'landcover_type':'Unknown'})
    

    #into one dataframe
    df_all = df_cropland.append([df_broad_leaf_forest, df_coniferous_forest, df_mixed_forest, df_ocean, df_other, df_grass_shrub, df_pasture, df_urban, df_unknown])
    

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
    
    p8 = ax.bar(ind, list_land_cover_values[7], width, color=dictionary_color[list_land_cover_names_sorted[7]]['color'], 
                bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6])
    
    p9 = ax.bar(ind, list_land_cover_values[8], width, color=dictionary_color[list_land_cover_names_sorted[8]]['color'], bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6]+list_land_cover_values[7])
    
    p10 = ax.bar(ind, list_land_cover_values[9], width, color=dictionary_color[list_land_cover_names_sorted[9]]['color'], bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6]+ list_land_cover_values[7]+list_land_cover_values[8])

    #want to reverese the order (ex if oceans at the "bottom" in the graph - ocean label should be furthest down)
    handles=(p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p8[0], p9[0], p10[0])

    index=0
    list_labels=[]
    for land_cover_name in list_land_cover_names_sorted:

        for_lable= (land_cover_name + ' (' + str("%.1f" % sum(list_land_cover_values[index])) + '%)')
        list_labels.append(for_lable)
        index=index+1

    labels=[textwrap.fill(text,20) for text in list_labels]

    plt.legend(handles[::-1], labels[::-1],bbox_to_anchor=(1, 0.52))
 
    plt.ylabel('Percent')
    
    #first one is not north (in rosedata - rather 22.5 to 67.5 (NE). 
    plt.xticks(ind, ('NE', 'E','SE', 'S', 'SW','W', 'NW', 'N'))

    ax.yaxis.grid(True)
    
    caption='Land cover within average footprint aggregated by direction'
    fig.set_size_inches(11, 13)

    return fig, caption


#14 font before
def render_mpl_seasonal_table(myStation, data, station, col_width=2, row_height=0.625, font_size=16,
             header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
             bbox=[0, 0, 1, 1], header_columns=0, 
             ax=None):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, cellLoc='center', bbox=bbox, colLabels=data.columns, colWidths=[2.5,1.5,2.5,2,2,2,3.5])

    mpl_table.auto_set_font_size(True)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])

    return fig


def seasonal_table(myStation):
    
    station=myStation.stationId
    year=myStation.settings['startYear']
    available_STILT= myStation.settings['stilt']
    months= available_STILT[str(year)]['months']
    
    var_load=pd.read_csv(stcDataPath + 'seasonal_table_values_GPW_pop.csv') 
    station_year= station +'_' + str(year)

    if station_year in set(var_load.station_year):
        
        sens_whole= var_load.loc[var_load['station_year'] == station_year, 'sens_whole'].iloc[0]
        sens_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'sens_diff_winter'].iloc[0]
        sens_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'sens_diff_spring'].iloc[0]
        sens_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'sens_diff_summer'].iloc[0]
        sens_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'sens_diff_fall'].iloc[0]

        point_whole = var_load.loc[var_load['station_year'] == station_year, 'point_whole'].iloc[0]
        point_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'point_diff_winter'].iloc[0]
        point_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'point_diff_spring'].iloc[0]
        point_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'point_diff_summer'].iloc[0] 
        point_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'point_diff_fall'].iloc[0]

        pop_whole = var_load.loc[var_load['station_year'] == station_year, 'pop_whole'].iloc[0]
        pop_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'pop_diff_winter'].iloc[0]
        pop_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'pop_diff_spring'].iloc[0] 
        pop_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'pop_diff_summer'].iloc[0] 
        pop_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'pop_diff_fall'].iloc[0]

        gee_whole = var_load.loc[var_load['station_year'] == station_year, 'gee_whole'].iloc[0] 
        gee_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'gee_diff_winter'].iloc[0]
        gee_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'gee_diff_spring'].iloc[0]
        gee_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'gee_diff_summer'].iloc[0]
        gee_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'gee_diff_fall'].iloc[0]

        resp_whole = var_load.loc[var_load['station_year'] == station_year, 'resp_whole'].iloc[0]
        resp_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'resp_diff_winter'].iloc[0]
        resp_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'resp_diff_spring'].iloc[0]
        resp_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'resp_diff_summer'].iloc[0]
        resp_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'resp_diff_fall'].iloc[0]

        anthro_whole = var_load.loc[var_load['station_year'] == station_year, 'anthro_whole'].iloc[0]
        anthro_diff_winter = var_load.loc[var_load['station_year'] == station_year, 'anthro_diff_winter'].iloc[0]
        anthro_diff_spring = var_load.loc[var_load['station_year'] == station_year, 'anthro_diff_spring'].iloc[0]
        anthro_diff_summer = var_load.loc[var_load['station_year'] == station_year, 'anthro_diff_summer'].iloc[0]
        anthro_diff_fall = var_load.loc[var_load['station_year'] == station_year, 'anthro_diff_fall'].iloc[0]

    else:
    
        fp_pop= import_population_data()

        fp_point = import_point_source_data()

        # if full year avaialbe - go ahead and create the tabel - else a message will be sent to the user
        if len(months)==12:
            #all hours for the date ranges... could update with date_range_hour_filtered
            winter_date_range1=pd.date_range(dt.datetime(year,1,1,0), (dt.datetime(year, 3, 1,0)-dt.timedelta(hours=3)), freq='3H')
            winter_date_range2=pd.date_range(dt.datetime(year,12,1,0), (dt.datetime(year+1, 1, 1,0)-dt.timedelta(hours=3)), freq='3H')
            spring_date_range=pd.date_range(dt.datetime(year,3,1,0), (dt.datetime(year, 6, 1,0)-dt.timedelta(hours=3)), freq='3H')
            summer_date_range=pd.date_range(dt.datetime(year,6,1,0), (dt.datetime(year, 9, 1,0)-dt.timedelta(hours=3)), freq='3H')
            fall_date_range=pd.date_range(dt.datetime(year,9,1,0), (dt.datetime(year, 12, 1,0)-dt.timedelta(hours=3)), freq='3H')

            #the average footprints given the selected date range
            nfp_winter1, fp_winter1, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, winter_date_range1)
            nfp_winter2, fp_winter2, fp_lon, fp_lat, title_not_used = read_aggreg_footprints(station, winter_date_range2)
            nfp_winter = nfp_winter1 + nfp_winter2
            fp_winter = (fp_winter1 * (nfp_winter1/nfp_winter)) + (fp_winter2 * (nfp_winter2/nfp_winter))
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
            sens_whole = fp_whole[0].sum()

            sens_diff_winter=((fp_winter[0].sum()/sens_whole)*100)-100
            sens_diff_spring=((fp_spring[0].sum()/sens_whole)*100)-100
            sens_diff_summer=((fp_summer[0].sum()/sens_whole)*100)-100
            sens_diff_fall=((fp_fall[0].sum()/sens_whole)*100)-100

            #point source 
            point_whole=(fp_whole*fp_point)[0].sum()

            point_diff_winter=(((fp_winter*fp_point)[0].sum()/point_whole)*100)-100
            point_diff_spring=(((fp_spring*fp_point)[0].sum()/point_whole)*100)-100
            point_diff_summer=(((fp_summer*fp_point)[0].sum()/point_whole)*100)-100
            point_diff_fall=(((fp_fall*fp_point)[0].sum()/point_whole)*100)-100

            #population 
            pop_whole=(fp_whole*fp_pop)[0].sum()
            pop_diff_winter=(((fp_winter*fp_pop)[0].sum()/pop_whole)*100)-100
            pop_diff_spring=(((fp_spring*fp_pop)[0].sum()/pop_whole)*100)-100
            pop_diff_summer=(((fp_summer*fp_pop)[0].sum()/pop_whole)*100)-100
            pop_diff_fall=(((fp_fall*fp_pop)[0].sum()/pop_whole)*100)-100

            #get the modelled concentration values
            timeselect_list=[0, 3, 6, 9, 12, 15, 18, 21]
            df_winter1 = read_stilt_timeseries(station, winter_date_range1, timeselect_list)
            df_winter2 = read_stilt_timeseries(station, winter_date_range2, timeselect_list)
            df_winter = df_winter1.append(df_winter2)
            df_spring = read_stilt_timeseries(station, spring_date_range, timeselect_list)
            df_summer = read_stilt_timeseries(station, summer_date_range, timeselect_list)
            df_fall = read_stilt_timeseries(station, fall_date_range, timeselect_list)

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
            anthro_whole=df_whole_mean['co2.industry']+df_whole_mean['co2.energy']+ df_whole_mean['co2.transport']+ df_winter_mean['co2.residential'] + df_winter_mean['co2.other_categories']

            anthro_diff_winter=(((df_winter_mean['co2.industry']+df_winter_mean['co2.energy']+ df_winter_mean['co2.transport']+ df_winter_mean['co2.residential'] + df_winter_mean['co2.other_categories'])/anthro_whole)*100)-100
            anthro_diff_spring=(((df_spring_mean['co2.industry']+df_spring_mean['co2.energy']+ df_spring_mean['co2.transport']+ df_winter_mean['co2.residential'] + df_winter_mean['co2.other_categories'])/anthro_whole)*100)-100
            anthro_diff_summer=(((df_summer_mean['co2.industry']+df_summer_mean['co2.energy']+ df_summer_mean['co2.transport']+ df_winter_mean['co2.residential'] + df_winter_mean['co2.other_categories'])/anthro_whole)*100)-100
            anthro_diff_fall=(((df_fall_mean['co2.industry']+df_fall_mean['co2.energy']+ df_fall_mean['co2.transport']+ df_winter_mean['co2.residential'] + df_winter_mean['co2.other_categories'])/anthro_whole)*100)-100

        #where there is no information in loaded file, and not all footpritns 
        else:
            seasonal_table = None
            caption = 'No seasonal table, footprints are not available for the whole (start-)year'
            return seasonal_table, caption 
    #here have values either from loaded file or calculated
    year_var=str(year) 
    df_seasonal_table = pd.DataFrame(columns=['Variable', year_var, 'Jan + Feb + Dec', 'Mar-May', 'Jun-Aug','Sep-Nov', 'Unit'], index=['Sensitivity', 'Population','Point source', 'GEE', 'Respiration', 'Anthropogenic'])

    df_seasonal_table.loc['Sensitivity'] = pd.Series({'Variable': 'Sensitivity', year_var:("%.2f" % sens_whole), 'Jan + Feb + Dec':("%+.2f" % sens_diff_winter+ '%'), 'Mar-May':("%+.2f" % sens_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % sens_diff_summer + '%'), 'Sep-Nov':("%+.2f" % sens_diff_fall+ '%'), 'Unit': 'ppm / ($\mu$mol / (m$^{2}$s))'})

    df_seasonal_table.loc['Population'] = pd.Series({'Variable': 'Population', year_var:("%.0f" % pop_whole), 'Jan + Feb + Dec':("%+.2f" % pop_diff_winter+ '%'), 'Mar-May':("%+.2f" % pop_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % pop_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % pop_diff_fall+ '%'), 'Unit': 'pop*(ppm / ($\mu$mol / (m$^{2}$s)))'})


    df_seasonal_table.loc['Point source'] = pd.Series({'Variable': 'Point source', year_var:("%.2f" % point_whole), 'Jan + Feb + Dec':("%+.2f" % point_diff_winter+ '%'), 'Mar-May':("%+.2f" % point_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % point_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % point_diff_fall+ '%'), 'Unit': 'ppm'})


    df_seasonal_table.loc['GEE'] = pd.Series({'Variable': 'GEE','Unit': 'ppm (uptake)', year_var:("%.2f" % gee_whole), 'Jan + Feb + Dec':("%+.2f" % gee_diff_winter+ '%'), 'Mar-May':("%+.2f" % gee_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % gee_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % gee_diff_fall+ '%'), 'Unit': 'ppm (uptake)'})

    df_seasonal_table.loc['Respiration'] = pd.Series({'Variable': 'Respiration', year_var:("%.2f" % resp_whole), 'Jan + Feb + Dec':("%+.2f" % resp_diff_winter+ '%'), 'Mar-May':("%+.2f" % resp_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % resp_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % resp_diff_fall+ '%'), 'Unit': 'ppm'})


    df_seasonal_table.loc['Anthropogenic'] = pd.Series({'Variable': 'Anthropogenic', year_var:("%.2f" % anthro_whole), 'Jan + Feb + Dec':("%+.2f" % anthro_diff_winter+ '%'), 'Mar-May':("%+.2f" % anthro_diff_spring+ '%'), 
                                                          'Jun-Aug':("%+.2f" % anthro_diff_summer+ '%'), 'Sep-Nov':("%+.2f" % anthro_diff_fall+ '%'), 'Unit': 'ppm'})

    caption = 'Seasonal variation year ' + str(year) 

    seasonal_table=render_mpl_seasonal_table(myStation, df_seasonal_table, station, header_columns=0, col_width=2.5)

    return seasonal_table, caption
  
#land cover polar graph:

def land_cover_polar_graph(myStation):
    
    station=myStation.stationId
    station_name=myStation.stationName
    date_range=myStation.dateRange
    timeselect=myStation.settings['timeOfDay']
    fp_lon=myStation.fpLon
    fp_lat=myStation.fpLat
    fp=myStation.fp
    
    title=myStation.settings['titles']
    bin_size=myStation.settings['binSize']
    degrees=myStation.degrees
    polargraph_label= myStation.settings['labelPolar']

    #get all the land cover data from netcdfs 
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')
    
    dir_bins, dir_labels=define_bins_landcover_polar_graph(bin_size=bin_size)
    
    #land cover classes (imported in the land cover section):
    broad_leaf_forest=fp*broad_leaf_forest
    coniferous_forest=fp*coniferous_forest
    mixed_forest=fp*mixed_forest
    ocean=fp*ocean
    other=fp*other
    grass_shrub=fp*grass_shrub
    cropland=fp*cropland
    pasture=fp*pasture
    urban=fp*urban
    unknown=fp*unknown
    
            
    #lists of these values
    broad_leaf_forest_values = [item for sublist in broad_leaf_forest[0] for item in sublist]
    coniferous_forest_values = [item for sublist in coniferous_forest[0] for item in sublist]
    mixed_forest_values = [item for sublist in mixed_forest[0] for item in sublist]
    ocean_values = [item for sublist in ocean[0] for item in sublist]
    other_values = [item for sublist in other[0] for item in sublist]
    grass_shrub_values = [item for sublist in grass_shrub[0] for item in sublist]
    cropland_values = [item for sublist in cropland[0] for item in sublist]
    pasture_values = [item for sublist in pasture[0] for item in sublist]
    urban_values = [item for sublist in urban[0] for item in sublist]
    unknown_values = [item for sublist in unknown[0] for item in sublist]
        
        
    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_broad_leaf_forest = pd.DataFrame({'landcover_vals': broad_leaf_forest_values,
                               'degrees': degrees,
                               'landcover_type':'Broad leaf forest'})
    
    df_coniferous_forest = pd.DataFrame({'landcover_vals': coniferous_forest_values,
                           'degrees': degrees,
                           'landcover_type':'Coniferous forest'})
    
    df_mixed_forest = pd.DataFrame({'landcover_vals': mixed_forest_values,
                           'degrees': degrees,
                           'landcover_type':'Mixed forest'})
    
    df_ocean = pd.DataFrame({'landcover_vals': ocean_values,
                           'degrees': degrees,
                           'landcover_type':'Ocean'})
    
    df_other = pd.DataFrame({'landcover_vals': other_values,
                           'degrees': degrees,
                           'landcover_type':'Other'})
    
    df_grass_shrub = pd.DataFrame({'landcover_vals':  grass_shrub_values,
                           'degrees': degrees,
                           'landcover_type':'Grass/shrubland'})
    
    df_cropland = pd.DataFrame({'landcover_vals':  cropland_values,
                           'degrees': degrees,
                           'landcover_type':'Cropland'})
    
    df_pasture = pd.DataFrame({'landcover_vals': pasture_values,
                           'degrees': degrees,
                           'landcover_type':'Pasture'})
    
    df_urban = pd.DataFrame({'landcover_vals':  urban_values,
                           'degrees': degrees,
                           'landcover_type':'Urban'})
    
    df_unknown = pd.DataFrame({'landcover_vals':  unknown_values,
                           'degrees': degrees,
                           'landcover_type':'Unknown'})
  

    #into one dataframe
    df_all = df_cropland.append([df_broad_leaf_forest, df_coniferous_forest, df_mixed_forest, df_ocean, df_other, df_grass_shrub, df_pasture, df_urban, df_unknown])

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

    directions = np.arange(dir_bins[1], 360, bin_size)
    
    if title=='yes':
        
        date_and_time_string= date_and_time_string_for_title(date_range, timeselect)
        for_title=('Station: ' + station_name + ' (' + station + ')' + '<br>' + 'Area corresponding to land cover sensitivity (%)<br>' + date_and_time_string)
        
    else:
        for_title=''
        
    matplotlib.rcParams.update({'font.size': 18})
    
    #change the data so that each % values is mapped as area:
    #first step - make the "cumsum" value for each direction.
    #ex if the innermost value represent cropland, that remains, the next class 
    #will be that value + the cropland valueand so on...
    index=0
    #loop over all land cover classes except the fitst one (nothing to add to)
    for land_cover_class in list_land_cover_names_sorted[1:]:
        land_cover_before = list_land_cover_names_sorted[index]
        index=index+1
        rosedata[land_cover_class]=rosedata[land_cover_before].values + rosedata[land_cover_class].values
        
    #the max radius is the max value in the last column (ex the "others" column 
    #if that one is the one with the smalles contribution = mapped the furthest 
    #from the station)
    max_radius=max(rosedata[list_land_cover_names_sorted[-1]].values)

    #the area given the "max radius" (area of that slice by dividing it by number of directions)
    area_max=(math.pi*max_radius*max_radius)/len(directions)

    #all other values mapped in relation to this: 
    #first: what is the "area value" for specific class given the max area
    rosedata=rosedata.applymap(lambda x: (x/max_radius)*area_max)
    
    #second: given that area value, what is the radius? (=where it should be placed in the graph)
    rosedata=rosedata.applymap(lambda x: math.sqrt(x / math.pi))
         
    #bar direction and height
    bar_dir, bar_width = _convert_dir(directions)

    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(polar=True))
    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    
    def update_yticks(x, pos):
        area=x*x*math.pi
        area_part=area/area_max
        label=max_radius*area_part

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
            ax.bar(bar_dir, rosedata[land_cover_class].values,
                   #bar width always the same --> depending on how many slices. Each slice same size.
                   width=bar_width,
                   color=dictionary_color[land_cover_class]['color'],
                   label=land_cover_class,
                   linewidth=0)
            first=False
        
        #values are accumulated
        ax.bar(bar_dir, (rosedata[land_cover_after].values-rosedata[land_cover_class].values), 
               width=bar_width, 
               #all the values "leading up" to this one. then add "the different (see above) on top
               bottom=rosedata[land_cover_class].values,
               color=dictionary_color[land_cover_after]['color'],
               label=land_cover_after,
               linewidth=0)
       
    
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])    
    ax.legend(labels, bbox_to_anchor=(1.5, 0), ncol=1, loc=4)
    
    caption = "Land cover within average footprint aggregated by direction (polar)"
    
    return fig, caption

    
#given the directions (and number of them), get the direction of the bars and their width
#function used in the final step of generating a graph
def _convert_dir(directions, N=None):
    if N is None:
        N = directions.shape[0]
    barDir = directions * np.pi/180. - np.pi/N
    barWidth = 2 * np.pi / N
    return barDir, barWidth
    
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
   
#multiple variables graph    
def multiple_variables_graph(myStation):
    
    selected_station=myStation.stationId
    station_name=[myStation.stationName]
    timeselect_list=myStation.settings['timeOfDay']    
    date_range=myStation.dateRange
    
    df_save = pd.DataFrame(columns=['Station','Sensitivity','Area 50% sensitivity', 'GEE','Respiration','Anthro','Point source','Population'])

    all_stations=['TRN180', 'SVB150', 'TOH147', 'SMR125', 'LUT', 'KRE250', 'IPR100', 'JFJ', 'KIT200', 'GAT344']
    
    if selected_station not in all_stations:
        all_stations.append(selected_station)
        
    start_date_year=min(date_range).year
    end_date_year=max(date_range).year
    
    if start_date_year == end_date_year and len(timeselect_list)==8:
        full_year = True
   
    else:
        full_year = False

    var_load=pd.read_csv(stcDataPath + 'seasonal_table_values_GPW_pop.csv') 

    index = 0 
    stations_missing_footprints=[]
    for station in all_stations:
        
        station_year = station + '_' + str(start_date_year)

        if full_year and station_year in set(var_load.station_year):
            
            sens_whole= var_load.loc[var_load['station_year'] == station_year, 'sens_whole'].iloc[0]
            sens_area_50= var_load.loc[var_load['station_year'] == station_year, 'sens_area_50_percent'].iloc[0] 
            gee_whole= var_load.loc[var_load['station_year'] == station_year, 'gee_whole'].iloc[0]
            resp_whole= var_load.loc[var_load['station_year'] == station_year, 'resp_whole'].iloc[0]
            anthro_whole= var_load.loc[var_load['station_year'] == station_year, 'anthro_whole'].iloc[0]
            point_whole= var_load.loc[var_load['station_year'] == station_year, 'point_whole'].iloc[0]
            pop_whole= var_load.loc[var_load['station_year'] == station_year, 'pop_whole'].iloc[0]
            
        else:
            sens_whole,sens_area_50, gee_whole,resp_whole, anthro_whole,point_whole,pop_whole = values_multiple_variable_graph(myStation, station)
            
        if sens_whole is not None:

            df_save.loc[len(df_save.index)] = [station, sens_whole,sens_area_50,gee_whole,resp_whole, anthro_whole,point_whole,pop_whole]
            index=index+1
        
        
        else:
            stations_missing_footprints.append(station)
            
    if len(stations_missing_footprints)>0:
        
        string_stations_missing_footprints = ", ".join(stations_missing_footprints)
        
        string_stations_missing_footprints = string_stations_missing_footprints[:-1]
        display(HTML('<p style="font-size:16px;">Reference station(s) missing footprints for specified date range: ' + string_stations_missing_footprints + '</p>'))  
        

    #sensitivity is the first attribut (list_item[0]) in the each of the lists (one list per station)
    min_sens=min(df_save['Sensitivity'])
    range_sens=max(df_save['Sensitivity'])-min_sens
    
    min_sens_50=min(df_save['Area 50% sensitivity'])
    range_sens_50=max(df_save['Area 50% sensitivity'])-min_sens_50

    #these lists (list_sensitivity, list_population, list_point_source) will be used to generate texts 
    #for the station characterization PDFs (if choose to create a PDF)
    #--> hence into list here, and not for GEE, respiration and anthropogenic contribution
    min_gee=max(df_save['GEE'])
    range_gee=abs(min_gee-min(df_save['GEE']))

    min_resp=min(df_save['Respiration'])
    range_resp=max(df_save['Respiration'])-min_resp
        
    min_anthro=min(df_save['Anthro'])
    range_anthro=max(df_save['Anthro'])-min_anthro
    
    min_pointsource=min(df_save['Point source'])
    range_pointsource=max(df_save['Point source'])-min_pointsource
    
    min_population=min(df_save['Population'])
    range_population=max(df_save['Population'])-min_population

    df_saved_for_normalized=df_save.copy()

    for station in df_saved_for_normalized['Station']:
        
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Sensitivity', min_sens, range_sens)
        df_saved_for_normalized=compute_normalized(df_saved_for_normalized, station, 'Area 50% sensitivity', min_sens_50, range_sens_50)
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
    list_attributes=['Station', '', 'Sensitivity', 'Area 50% sensitivity', 'Population', 'Point source contribution', 'GEE (uptake)', 'Respiration', 'Anthropogenic contribution']

    #max 15 characters in lable
    list_attributes=[textwrap.fill(text,15) for text in list_attributes]

    #incremented for each station.. 0, 10, 20... etc. Where station name and "line" should start along the y-axis. 
    place_on_axis=0
    for station in df_saved_for_normalized['Station']:
        
        #get all the values for station (row in dataframe)
        station_values=df_saved_for_normalized.loc[df_saved_for_normalized['Station'] == station]

        #place them in the order we want them in the graph. List that will be used for the line. (one per station)
        station_values_list =[place_on_axis, place_on_axis, station_values['Sensitivity'].values[0], station_values['Area 50% sensitivity'], 
                              station_values['Population'].values[0], station_values['Point source'].values[0],
                              station_values['GEE'].values[0], station_values['Respiration'].values[0], 
                              station_values['Anthro'].values[0]]
        
        if station==selected_station:

            plt.plot(list_attributes, station_values_list, linestyle='-', marker='o', lw=3, color= 'black', label=station_name)
            
            #on 'Station position (along the x-axis). 
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
        
    columns_need_quartiles=['Sensitivity','Population','Point source']
    
    for column in columns_need_quartiles:
        
        #df saved - the original values. 
        quartile_df=df_save[column].quantile([0.25,0.5,0.75])

        q1=quartile_df[0.25]
        q2=quartile_df[0.5]
        q3=quartile_df[0.75]
        
        value_selected_station = df_save.loc[df_save['Station'] == selected_station, column]
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
        
    caption=('Selected station relative to reference atmospheric stations')

    return fig, caption

def values_multiple_variable_graph(myStation, station):

    date_range = myStation.dateRange
    timeselect_list = myStation.settings['timeOfDay']  
    fp_pop= import_population_data()
    fp_point= import_point_source_data()
    nfp, fp_station, lon, lat, title = read_aggreg_footprints(station, date_range)
   
    if nfp > 0:

        percent_footprints=(nfp/len(date_range))*100

        if percent_footprints<75:

            display(HTML('<p style="font-size:16px;">' + station + ' (' + str(nfp) + '/' + str(len(date_range)) +' footprints)</p>'))       
            
        sens_area_50 = area_footprint_based_on_threshold(fp_station, lat, lon, 0.5)

        #total average sensitivity for specific station:
        sens_whole=fp_station[0].sum()

        #read the modelled concentration data - for anthro and bio values
        #using the updated version of read_stilt_timeseries allows for filtering out different hours of the days
        df_modelled_concentrations = read_stilt_timeseries(station, date_range, timeselect_list)

        #averages of the values --> default skip nan
        df_mean=df_modelled_concentrations.mean()

        gee_whole=df_mean['co2.bio.gee']

        resp_whole=df_mean['co2.bio.resp']

        #anthro:
        anthro_whole=(df_mean['co2.industry']+df_mean['co2.energy']+ df_mean['co2.transport']+ df_mean['co2.residential'] + df_mean['co2.other_categories'])

        #point source for specific station 
        fp_pointsource_multiplied=fp_station*fp_point
        point_whole=fp_pointsource_multiplied.sum()

        #population for specific station
        fp_pop_multiplied=fp_station*fp_pop
        pop_whole=fp_pop_multiplied.sum()

        return sens_whole, sens_area_50, gee_whole, resp_whole, anthro_whole, point_whole, pop_whole
    
    else:
        
        return None, None, None, None, None, None, None

      
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


def save(stc, fmt='pdf'):
    """
    provide a station characterisation object, with all the figures.
    all figures will be saved
    

    Parameters
    ----------
    stc : station characterisation object format. Instance of class(stationchar)
    fmt : STR, image filename ending, used to infer format ('pdf' | 'png')

    Returns
    -------
    None.

    """
    # stc.figures is a dictionary...like  {1: [fig, caption, shortname]}
    captions = {}
    
    for f in stc.figures:
        fig, cap, name = stc.figures[f]  
        
        if not fig: continue
        
        stc.figures[f][2] = name + '.' + fmt
        filename = os.path.join(stc.settings['output_folder'], (name + '.' + fmt))
        
        # keep the captions for json output
        captions[name] = cap
        
        # special settings for individual figures
        if f==4:  #'landcover_rose'
            ax = fig.gca()
            ax.legend(bbox_to_anchor=(1.9, 0.25), ncol=2)
            
        if f==7: #'landcover_bar'
            fig.set_size_inches(12, 11)        
            
        #common for all figures
        fig.savefig(filename,dpi=100,bbox_inches='tight')
        captions[name] = cap
    
    # save captions as json file    
    file = os.path.join(stc.settings['output_folder'],'captions.json')
    with open(file, 'w') as f:
        json.dump(captions, f, indent=4)
    
    # save settings as json file
    file = os.path.join(stc.settings['output_folder'],'settings.json')
    
    settings_copy = stc.settings.copy()

    delete = ['stilt', 'icos', 'areaFifty', 'date/time generated', 'output_folder', 'Sensitivity', 'Population', 'Point source']

    for item in delete: 
        if item in settings_copy.keys():
            del settings_copy[item]

    with open(file, 'w') as f:
        
        json.dump(settings_copy, f, indent=4)
        
    # save PDF
    tex_string=tex.generate_full(stc)
    
    tex_file=os.path.join(stc.settings['output_folder'], (stc.settings['date/time generated']+stc.stationId+'.tex'))
               
    with open(tex_file,"w") as file:
        file.write(tex_string) 
        
    output_folder = stc.settings['output_folder']

    a = os.system(('pdflatex -output-directory=' + output_folder + ' ' + tex_file))

    if a!=0:
        print('problem generating the output PDF')

    else:
        files_to_remove = ['.aux', '.log', '.out']
        for file_ext in files_to_remove:
            remove = stc.settings['date/time generated']+stc.stationId+ file_ext
            os.remove(output_folder + '/' + remove)
