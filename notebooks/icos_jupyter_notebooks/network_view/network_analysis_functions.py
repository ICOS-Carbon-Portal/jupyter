# station 
import requests
from cartopy.io.shapereader import Reader
from IPython.core.display import display, HTML 
from ipywidgets import Dropdown, Button, Output
import numpy as np
import json
from numpy import loadtxt
import pandas as pd
import netCDF4 as cdf
from netCDF4 import Dataset, date2index
import datetime as dt
#dt.date?
from datetime import date
import xarray as xr
# replace here? 
from icoscp.sparql import sparqls, runsparql
from icoscp.sparql.runsparql import RunSparql
from matplotlib.colors import LogNorm
import matplotlib
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
cartopy.config['data_dir'] = '/data/project/cartopy/' 
from cartopy.feature import ShapelyFeature
import matplotlib.patches as mpatches
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import os
import shapely
from shapely.geometry import box
from matplotlib.colors import ListedColormap,LinearSegmentedColormap
import copy
from ipywidgets import IntProgress
import math
from icoscp.stilt import stiltstation
from matplotlib.legend import Legend
import textwrap
 
#path_network_footprints = 'network_footprints'
#path_network_footprints_representation = 'network_footprints_representation'
#path_network_footprints = '/data/project/obsnet/network_footprints'
#path_network_footprints_representation = '/data/project/obsnet/network_footprints_representation'
pathFP='/data/stiltweb/stations/'
stcDataPath = '/data/project/stc/'
path_cp = '/data/dataAppStorage/netcdf/'
data_folder = '/data/project/stc/footprints_2018_averaged'
load_lat=loadtxt(os.path.join(data_folder, 'latitude.csv'), delimiter=',')
load_lon=loadtxt(os.path.join(data_folder, 'longitude.csv'), delimiter=',')

country_masks = Dataset(os.path.join(stcDataPath,'europe_STILT_masks.nc'))

dictionary_area_choice = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus',\
                          'BEL':'Belgium', 'BIH':'Bosnia and Herzegovina', 'BGR':'Bulgaria', 'HRV':'Croatia',\
                          'CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland',\
                          'FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland',\
                          'ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LIE':'Liechtenstein','LTU':'Lithuania',\
                          'LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta','MDA':'Moldova','MNE':'Montenegro',\
                          'NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia',\
                          'ROU':'Romania','SMR':'San Marino','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain',\
                          'SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom', 'Europe':'Europe'}

dictionary_color = {'Broad leaf forest': {'color': '#4c9c5e'}, 'Coniferous forest':{'color':'#CAE0AB'}, 'Mixed forest':{'color':'#90C987'}, 'Ocean':{'color':'#1964B0'}, 'Other':{'color':'#882E72'}, 'Grass/shrubland':{'color':'#F1932D'}, 'Cropland':{'color': '#521A13'}, 'Pasture':{'color':'#F7F056'}, 'Urban':{'color':'#DC050C'}, 'Unknown':{'color':'#777777'}}

# for the monitoring potential maps:
N = 256
pasture_for_cmap = np.ones((N, 4))
pasture_for_cmap[:, 0] = np.linspace(247/256, 1, N) # R 
pasture_for_cmap[:, 1] = np.linspace(240/256, 1, N) # G
pasture_for_cmap[:, 2] = np.linspace(86/256, 1, N)  # B
pasture_for_cmap_r = np.flip(pasture_for_cmap, 0)
pasture_cmp = ListedColormap(pasture_for_cmap_r)

cropland_for_cmap = np.ones((N, 4))
cropland_for_cmap[:, 0] = np.linspace(82/256, 1, N) # R 
cropland_for_cmap[:, 1] = np.linspace(26/256, 1, N) # G 
cropland_for_cmap[:, 2] = np.linspace(19/256, 1, N)  # B
cropland_for_cmap_r = np.flip(cropland_for_cmap, 0)
cropland_cmap = ListedColormap(cropland_for_cmap_r)

# broad leaf forest
blf_for_cmap = np.ones((N, 4))
blf_for_cmap[:, 0] = np.linspace(76/256, 1, N) # R 
blf_for_cmap[:, 1] = np.linspace(156/256, 1, N) # G 
blf_for_cmap[:, 2] = np.linspace(94/256, 1, N)  # B
blf_for_cmap_r = np.flip(blf_for_cmap, 0)
blf_cmp = ListedColormap(blf_for_cmap_r)

# coniferous forest
cf_for_cmap = np.ones((N, 4))
cf_for_cmap[:, 0] = np.linspace(202/256, 1, N) # R 
cf_for_cmap[:, 1] = np.linspace(224/256, 1, N) # G 
cf_for_cmap[:, 2] = np.linspace(171/256, 1, N)  # B
cf_for_cmap_r = np.flip(cf_for_cmap, 0)
cf_cmp = ListedColormap(cf_for_cmap_r)

# mixed forest
mf_for_cmap = np.ones((N, 4))
mf_for_cmap[:, 0] = np.linspace(144/256, 1, N) # R 
mf_for_cmap[:, 1] = np.linspace(201/256, 1, N) # G 
mf_for_cmap[:, 2] = np.linspace(135/256, 1, N)  # B
mf_for_cmap_r = np.flip(mf_for_cmap, 0)
mf_cmp = ListedColormap(mf_for_cmap_r)

# grass and shrub
gs_for_cmap = np.ones((N, 4))
gs_for_cmap[:, 0] = np.linspace(241/256, 1, N) # R 
gs_for_cmap[:, 1] = np.linspace(147/256, 1, N) # G 
gs_for_cmap[:, 2] = np.linspace(45/256, 1, N)  # B
gs_for_cmap_r = np.flip(gs_for_cmap, 0)
gs_cmp = ListedColormap(gs_for_cmap_r)

# emission 
emission_for_cmap = np.ones((N, 4))
emission_for_cmap[:, 0] = np.linspace(170/256, 1, N) # R 
emission_for_cmap[:, 1] = np.linspace(51/256, 1, N) # G 
emission_for_cmap[:, 2] = np.linspace(106/256, 1, N)  # B
emission_for_cmap_r = np.flip(emission_for_cmap, 0)
emission_cmp = ListedColormap(emission_for_cmap_r)

color_name_dict = {'gee':{'color':copy.copy(matplotlib.cm.get_cmap("Greens")), 'name' : 'GEE'}, 'resp':{'color':copy.copy(matplotlib.cm.get_cmap("Reds")), 'name' : 'Respiration'},
                   'bl':{'color':blf_cmp, 'name' : 'Broad leaf forest'}, 'cf':{'color':cf_cmp, 'name' : 'Coniferous forest'},\
        'gs':{'color':gs_cmp, 'name' : 'Grass and shrubland'}, 'mf':{'color':mf_cmp, 'name' : 'Mixed forest'},\
        'pa':{'color':pasture_cmp, 'name' : 'Pasture'}, 'cl':{'color':cropland_cmap, 'name' : 'Cropland'}}

country_code_name_dict = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium',\
                          'BIH':'Bosnia and Herzegovina', 'BGR':'Bulgaria', 'HRV':'Croatia','CYP':'Cyprus',\
                          'CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany',\
                          'GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia',\
                          'LIE':'Liechtenstein','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta',\
                          'MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland',\
                          'PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SMR':'San Marino','SVK':'Slovakia',\
                          'SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}

country_code_zoom_dict = {'ALB':{'lat':41.1533, 'lon':20.1683, 'zoom' : 1}, 'BLR':{'lat':53.7098, 'lon':27.9534,  'zoom' : 2},\
                          "BEL":{'lat':50.5039, 'lon':4.4699, 'zoom' : 1},"BIH":{'lat':43.9159, 'lon':17.6791, 'zoom' : 1},\
                          "BGR":{'lat':42.7339, 'lon':25.4858, 'zoom' : 1},"HRV":{'lat':45.1000, 'lon':15.2000, 'zoom' : 2},\
                          "CYP":{'lat':35.1264, 'lon':33.4299, 'zoom' : 1},"CZE":{'lat':49.8175, 'lon':15.4730, 'zoom' : 1},\
                          "DNK":{'lat':56.2639, 'lon':9.5018, 'zoom' : 1},"EST":{'lat':58.5953, 'lon':25.0136, 'zoom' : 1},\
                          "FIN":{'lat':65, 'lon':25.7482, 'zoom' : 2}, "FRA":{'lat':46.2276, 'lon':2.2137, 'zoom' : 2},\
                          "DEU":{'lat':51.1657, 'lon':10.4515, 'zoom' : 2},"GRC":{'lat':39.0742, 'lon':21.8243, 'zoom' : 2},\
                          "HUN":{'lat':47.1625, 'lon':19.5033, 'zoom' : 2},"IRL":{'lat':53.1424, 'lon':-7.6921, 'zoom' : 1},\
                          "ITA":{'lat':42.5, 'lon':12.5674, 'zoom' : 2},"XKX":{'lat':42.6026, 'lon':20.9030, 'zoom' : 1},\
                          "LVA":{'lat':56.8796, 'lon':24.6032, 'zoom' : 2},"LIE":{'lat':47.1660, 'lon':9.5554, 'zoom' : 1},\
                          "LTU":{'lat':55.1694, 'lon':23.8813, 'zoom' : 1},"LUX":{'lat':49.8153, 'lon':6.1296, 'zoom' : 1},\
                          "MKD":{'lat':41.6086, 'lon':21.7453, 'zoom' : 1},"MTL":{'lat':35.9375, 'lon':14.3754, 'zoom' : 1},\
                          "MDA":{'lat':47.4116, 'lon':28.3699, 'zoom' : 1},"MNE":{'lat':42.7087, 'lon':19.3744, 'zoom' : 1},\
                          "NLD":{'lat':52.1326, 'lon':5.2913, 'zoom' : 1},"NOR":{'lat':65, 'lon':17, 'zoom' : 3},\
                          "POL":{'lat':51.9194, 'lon':19.1451, 'zoom' : 2}, "PRT":{'lat':39.3999, 'lon':8.2245, 'zoom' : 1},\
                          "SRB":{'lat':44.0165, 'lon':21.0059, 'zoom' : 1},"ROU":{'lat':45.9432, 'lon':24.9668, 'zoom' : 2},\
                          "SMR":{'lat':43.9424, 'lon':12.4578, 'zoom' : 1},"SVK":{'lat':48.6690, 'lon':19.6990, 'zoom' : 1},\
                          "SVN":{'lat':46.1512, 'lon':14.9955, 'zoom' : 1},"ESP":{'lat':40.4637, 'lon':-3, 'zoom' : 2},\
                          "SWE":{'lat':60.1282, 'lon':16, 'zoom' : 3},"CHE":{'lat':46.8182, 'lon':8.2275, 'zoom' : 1},\
                          "GBR":{'lat':55, 'lon':-3.4360, 'zoom' : 2}, "Andorra":{'lat':42.5063, 'lon':1.5218, 'zoom' : 1},\
                         "AUT":{'lat':47.5162, 'lon':14.5501, 'zoom' : 2}}

# for the bar graph with land cover
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

def degrees_from_point_to_grid_cells(station_lat, station_lon, grid_lat, grid_lon):
    
    degrees_0_360=[compass_bearing((station_lat, station_lon), (lat, lon)) for lat in grid_lat for lon in grid_lon]
        
    #return list with degrees
    return degrees_0_360

def read_stilt_timeseries(station, date_range, timeselect_list):
    

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


def find_dobj_from_name(filename):

    '''
    Description: Function that returns the data object 
                 for a specified level 3 product netcdf filename. 
                
    Input:       netcdf filename
    
    Output:      Data Object ID (var_name: "dobj", var_type: String)
    '''
    
    query = '''
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        select ?dobj 
        where{
        ?dobj cpmeta:hasName "'''+filename+'''"^^xsd:string .
        FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
        FILTER EXISTS {?dobj cpmeta:hasSizeInBytes ?size }
        }
    '''
    return query

def check_cp(cp_path,filename):
    cp_name = ''
    dobj_L3 = RunSparql(sparql_query=find_dobj_from_name(filename),output_format='csv').run()

    if len(dobj_L3.split('/')) > 1:
        cp_name = (cp_path+dobj_L3.split('/')[-1]).strip()
    if not(os.path.exists(cp_name)):
        cp_name = ''
        print('file '+filename+' does not exist in CP')
        
    return cp_name
    
def update_footprint_based_on_threshold(input_footprint, threshold):

    threshold_sensitivity=input_footprint.sum()*threshold

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

    if threshold==1:

        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['sensitivity']==0, 0, 1)
    else:
        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['cumsum_sens']>=threshold_sensitivity, 0, 1)
    
    #mask*sensitivity = for "new" footprint that only has sensitivity values in the cells that have the value 1.
    df_sensitivity_sorted['mask_sensitivity']=df_sensitivity_sorted['mask_threshold']*df_sensitivity_sorted['sensitivity']

    #sort it back (so in correct lat/lon order for "packing back up" to 2D)
    df_sensitivity_upd=df_sensitivity_sorted.sort_index()

    list_updated_sensitivity=df_sensitivity_upd['mask_sensitivity'].tolist()
    
    upd_footprint_sens=np.array(list_updated_sensitivity).reshape(480, 400)

    return upd_footprint_sens

def return_europe_mask():
    
    all_countries= ["ALB","Andorra", "AUT", "BLR","BEL", "BIH", "BGR", "HRV", "CYP", "CZE", "DNK","EST","FIN","FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD", "MTL","MDA","MNE","NLD","NOR","POL","PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR"]
    first_country = True
    for country_code in all_countries:
        
        country_mask = country_masks.variables[country_code][:,:]

        if first_country:

            europe_mask = country_mask

            first_country = False

        else:
            europe_mask = europe_mask + country_mask
            
    return europe_mask

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
      
def read_aggreg_network_footprints(nwc, extended = False):
    
    if extended:
        folder = nwc['extendedNetwork']
        path = nwc['pathFpExtended']
        
    else:
        folder = nwc['networkFile']
        path = nwc['pathFp']

    date_range = pd.date_range(dt.datetime(nwc['startYear'],nwc['startMonth'],nwc['startDay'],0), (dt.datetime(nwc['endYear'], nwc['endMonth'], nwc['endDay'], 21)), freq='3H')
    date_range_subset = [date for date in date_range if date.hour in nwc['timeOfDay']]
    
    fp=[]
    nfp=0
    first = True
    for date in date_range_subset:
        date_string = str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' +  str(date.hour)
        
        filename = os.path.join(path, folder, date_string + '.csv')

        if os.path.isfile(filename):
            
            network_fp = pd.read_csv(filename)
            
            if first:
                
                network_total = network_fp[date_string]
                first = False
            else:
                network_total = network_total + network_fp[date_string]
                
            nfp = nfp + 1
            
    # average here:
    network_average = network_total / nfp
    
    network_average_fp = np.array(network_average.to_list()).reshape(480, 400)
    
    return network_average_fp


def average_network_footprint(date_range, stations, threshold = 0.5):
  
    df_footprints_network = pd.DataFrame()

    index=1

    list_none_footprints = []
    
    for station in stations:

        nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)

        if loaded_fp is None:

            list_none_footprints.append(station)

            continue

        upd_fp_sens=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        df_footprints_network[('fp_' + str(index))]=upd_fp_sens.flatten()
        
        #for new column values
        index=index+1
    
    # make a footprint based on all max values of the combined footprints. 
    df_max_base_network = df_footprints_network[df_footprints_network.columns].max(axis=1)
    average_network_footprint=np.array(df_max_base_network.tolist()).reshape((len(load_lat), len(load_lon)))
    
    return average_network_footprint, list_none_footprints

# function to convert station longitude and latitude (slat, slon) to indices of STILT model grid (ix,jy)
def lonlat_2_ixjy(slon,slat,mlon,mlat):
    #slon, slat: longitude and latitude of station
    #mlon, mlat: 1-dim. longitude and latitude of model grid
    ix = (np.abs(mlon-slon)).argmin()
    jy = (np.abs(mlat-slat)).argmin()
    return ix,jy

# footprint_show_percentages() is used to with argument percent=True to generate an aggregated % sensitivity map. 
def plot_maps(field, lon, lat, nwc, footprint_stations='', title='', label='', unit='', linlog='linear', extend = 'both', station='', vmin=None, vmax=None, colors='GnBu',pngfile='', output='', reference = '',  monitoring_potential = False): 

    # Set scale for features from Natural Earth
    NEscale = '50m'

    # Create a feature for Countries at 1:50m from Natural Earth
    countries = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale='50m',
        facecolor='none')

    fig = plt.figure(figsize=(18,10))

    # set up a map
    ax = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
    img_extent = (lon.min(), lon.max(), lat.min(), lat.max())
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],crs=ccrs.PlateCarree())
    ax.add_feature(countries, edgecolor='black', linewidth=0.3)

    cmap = copy.copy(matplotlib.cm.get_cmap(colors))
    cmap.set_under(color='white')

    if linlog == 'linear':
        if vmin is None:
            im = ax.imshow(field[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=0.0000001,vmax=vmax)
            cs = ax.imshow(field[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=0.00000001,vmax=vmax)
        else:
            
            im = ax.imshow(field[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cs = ax.imshow(field[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
         

    if monitoring_potential:
        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend=extend, ticks=[])
    else:
        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend=extend)

    cbar.set_label(label)
     
    plt.title(title)
    
    if reference != '':
        
        ax.plot(nwc['stationsLonExtended'], nwc['stationsLatExtended'],'o',color='purple',ms=2,transform=ccrs.PlateCarree())
    
    ax.plot(nwc['stationsLon'],nwc['stationsLat'],'o',color='blue',ms=2,transform=ccrs.PlateCarree())
    plt.tight_layout()
    plt.show()
    
    if len(pngfile)>0:
        
        if not os.path.exists(output):
            os.makedirs(output)
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
        
        return plt
    
# footprint_show_percentages() is used to with argument percent=True to generate an aggregated % sensitivity map. 
def plot_maps_country_zoom(field, lon, lat, nwc, zoom_lat=51.1657, zoom_lon=10.4515, zoom_level = 2, output='monitorint_potential_maps', title='', label='', unit='', linlog='linear', station='', zoom='',vmin=None, vmax=None, colors='GnBu', pngfile='', directory='figures', mask=False, reference = '', monitoring_potential = False): 

    # zoom in country (given lat and lon)
    ix,jy = lonlat_2_ixjy(zoom_lon,zoom_lat,load_lon,load_lat)

    if zoom_level == 1:
        x_change = 25
        y_change = 30
    if zoom_level == 2:
        x_change = 50
        y_change = 60
    if zoom_level == 3:
        x_change = 100
        y_change = 120
        
    # define zoom area 
    i1 = np.max([ix-x_change,0])
    i2 = np.min([ix+x_change,400])
    j1 = np.max([jy-y_change,0])
    j2 = np.min([jy+y_change,480])

    lon_z=load_lon[i1:i2]
    lat_z=load_lat[j1:j2]

    field_z=field[j1:j2,i1:i2]
    #field2_z=field2[j1:j2,i1:i2]

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
    # set up a map
    img_extent = (lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max())
    ax.set_extent([lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()],crs=ccrs.PlateCarree())
    ax.add_feature(countries, edgecolor='black', linewidth=0.3)
    
    cmap = copy.copy(matplotlib.cm.get_cmap(colors))
    
    cmap.set_under(color='white')  
    
    if linlog == 'linear':
        if vmin is None:
            
            im = ax.imshow(field_z[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=0.0000001,vmax=vmax)
            cs = ax.imshow(field_z[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=0.0000001,vmax=vmax)
        else:
            
            im = ax.imshow(field_z[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cs = ax.imshow(field_z[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
    
    if monitoring_potential:
        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend='both', ticks=[])
    else:
        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend='both')

    cbar.set_label(label)

    plt.title(title)
    
    if reference != '':
        
        ax.plot(nwc['stationsLonExtended'], nwc['stationsLatExtended'],'o',color='purple',ms=2,transform=ccrs.PlateCarree())
    
    ax.plot(nwc['stationsLon'],nwc['stationsLat'],'o',color='blue',ms=2,transform=ccrs.PlateCarree())

    plt.tight_layout()
    plt.show()
    
    if len(pngfile)>0:
        
        output = output

        if not os.path.exists(output):
            os.makedirs(output)
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
        
# compare the current and extended networks in a map with two different colors. 
def plot_maps_two(field, field2, mask_threshold, lon, lat, footprint_stations='', title='', label='', unit='', linlog='linear', extend = 'both', station='', zoom='', vmin=None, vmax=None, colors='GnBu',pngfile='', directory='figures', mask=False, percent=False, date_time_predefined='', output=''): 

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

    cmap = copy.copy(matplotlib.cm.get_cmap(colors))

    cmap.set_under(color='white')

    if linlog == 'linear':
        if vmin is None:
            im = ax.imshow(field[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=0.0000001,vmax=vmax)
            #cs = ax.imshow(field[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=0.00000001,vmax=vmax)
        else:
            
            im = ax.imshow(field[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)

            # mask - remove so you cannot see - values that are below 0.0001 in the difference between the current and extended.
            upd_field2 = np.ma.masked_array(field2, field2 < mask_threshold)
            
            cmap2 = copy.copy(matplotlib.cm.get_cmap("Blues"))

            cmap2.set_under(color='white')
            im2 = ax.imshow(upd_field2[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap2,vmin=vmin,vmax=vmax)
            cs = ax.imshow(upd_field2[:,:], origin='lower', extent=img_extent,cmap=cmap2,vmin=vmin,vmax=vmax)
            
        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend=extend)
        cbar.set_label(label)

    ax.text(0.01, -0.25, 'min: %.2f' % np.min(upd_field2[:,:]), horizontalalignment='left',transform=ax.transAxes)
    ax.text(0.99, -0.25, 'max: %.2f' % np.max(upd_field2[:,:]), horizontalalignment='right',transform=ax.transAxes)
    
    # add "legend":
    ax.plot([-12.111, -59.111], [-12.112, -59.112], '-', label='Current network', linewidth=8, color='#238b45')
    ax.plot([-9.111, -59.111], [-9.112, -59.112], '-', label='Extended network', linewidth=8, color='#2171b5')
    
    ax.legend(loc='upper left', fontsize='medium')

    plt.title(title)
 
    plt.show()
    
    if len(pngfile)>0:
        
        output = output

        if not os.path.exists(output):
            os.makedirs(output)
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
        
        return plt
    
def display_network_with_extended(nwc, vmax_footprint = 'extended'):
    
    if nwc['extendedNetwork']== 'No extension':
        display(HTML('<p style="font-size:14px;">Specify an "extended network" in the section "The view from the current ICOS network".</p>'))
        return

    # compare so that the analysed network really is an extension to the reference network
    # station list extended network:
    extended_network_file = nwc['extendedNetwork']
    json_file_extended = extended_network_file + '.json' 
    extended_network_footprint_info = open(os.path.join(nwc['pathFpExtended'], json_file_extended))
    extended_network_footprint_info_load = json.load(extended_network_footprint_info)
    extended_stations = extended_network_footprint_info_load['stations']
    
    json_file_reference = nwc['networkFile'] + '.json'

    reference_network_footprint_info = open(os.path.join(nwc['pathFp'], json_file_reference))
    reference_network_footprint_info_load = json.load(reference_network_footprint_info)
    reference_stations = reference_network_footprint_info_load['stations']

    added_stations = [station for station in extended_stations if station not in reference_stations]

    # stop the code in case the reference network stations are not all in the extended network
    check_feasibility = [station for station in reference_stations if station not in extended_stations]

    if len(check_feasibility) > 0:

        check_feasibility_string = ', '.join([str(elem) for elem in check_feasibility])[:-1]

        display(HTML('<p style="font-size:14px;">This part of the tool is meant to compare an (extended) network to a reference network. In this case, the reference network contains stations that are not included in the extended network (' + check_feasibility_string + ')</p>'))

    else:

        added_stations_string = ', '.join([str(elem) for elem in added_stations])[:-1]

        display(HTML('<p style="font-size:14px;">Results for the reference network extended with station: ' + added_stations_string + '</p>'))

    current_network = nwc['averageFp'] 
    
    extended_network = nwc['averageFpExtended'] 
  
    difference = extended_network - current_network

    if vmax_footprint == 'current':
        vmax = np.percentile(current_network, 99.9)
    else:
        vmax = np.percentile(extended_network, 99.9)

    mask_threshold = 0.0004
    plot_maps_two(current_network, difference , mask_threshold, load_lon, load_lat, linlog='linear', extend = 'both', 
              vmin=0.0004, vmax=vmax, colors='Greens',pngfile='', label= 'sensitivity: ppm /(μmol / (m²s))')
    
    

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

def overview_map(country_code):
    fig = plt.figure(figsize=(18,10))

    # set up a map
    ax = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())

    img_extent = (load_lon.min(), load_lon.max(), load_lat.min(), load_lat.max())
    ax.set_extent([load_lon.min(), load_lon.max(), load_lat.min(), load_lat.max()],crs=ccrs.PlateCarree())

    countries_borders = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale='50m',
        facecolor='none')

    ax.add_feature(countries_borders, edgecolor='black', linewidth=1)

    ax.add_feature(cfeature.OCEAN)

    reader = shpreader.Reader('/data/project/cartopy/shapefiles/natural_earth/cultural/ne_10m_admin_0_countries.shp')

    country_information = [country for country in reader.records() if country.attributes["ADM0_A3"] == country_code][0]

    # tuple lon, lat (lower left) lon, lat (upper right)
    country_bounds = country_information.geometry.bounds

    bbox = shapely.geometry.box(country_bounds[0], country_bounds[1], country_bounds[2], country_bounds[3], ccw=True)

    x_bbox,y_bbox = bbox.exterior.xy
    
    plt.plot(x_bbox,y_bbox, color = 'Green')
    
    plt.title(country_code_name_dict[country_code])
    plt.show()
    
                
def display_selected_fp_file(nwc):
    
    fp_average_footprint = nwc['averageFp']
    
    vmax = np.percentile(fp_average_footprint, 99.9)

    plot_maps(fp_average_footprint, load_lon, load_lat, nwc, colors = 'Greens', vmax=vmax, vmin = 0.0004,\
              label= 'sensitivity: ppm /(μmol / (m²s))', output='temp_output', extend = 'both', pngfile = 'average_map', linlog='linear')
    

def landcover_view(nwc, countries, pngfile = '', output= ''):
    
    network_footprint = nwc['averageFp']
    
    f_gridarea = cdf.Dataset(os.path.join(stcDataPath, 'gridareaSTILT.nc'))
    gridarea = f_gridarea.variables['cell_area'][:]
    
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018') 

    
    list_land_cover_classes = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean,\
                               grass_shrub, other, unknown]
    
    landcover_total_ocean_excluded = broad_leaf_forest + coniferous_forest+mixed_forest+cropland+pasture+urban+\
                               grass_shrub+other+unknown
    
    
    # want vegetation fraction HILDA land cover maps for computing sensing / km2 for specific land cover 
    # in country or region (on the total)
    list_classes_fractions = []

    for landcover in list_land_cover_classes:

        landcover_fraction = landcover/(gridarea/1000000)

        list_classes_fractions.append(landcover_fraction)
        
    land_cover_names = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', \
                        'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
    
    all_countries = ["ALB","Andorra","AUT", "BLR","BEL","BIH", "BGR","HRV","CYP","CZE","DNK","EST","FIN", "FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD","MTL", "MDA","MNE","NLD","NOR", "POL", "PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR", "Europe"]
    
    
    columns_save= ['country', 'total_sens', 'total_sens_km2']
    #list_for_columns = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
    #                  'pasture', 'urban', 'unknown']
        
    list_for_columns = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'cropland', \
                      'pasture', 'urban', 'ocean', 'grass_shrub', 'other', 'unknown']

    for column in list_for_columns:
        columns_save.append(column + '_country')
        columns_save.append(column + '_sensing')
        columns_save.append(column + '_sensing_total')
        columns_save.append(column + '_sensing_km2')


    df = pd.DataFrame(columns=columns_save)
    i=0
    for country_code in all_countries:
        
        data_specific_country = [country_code]
        
        if country_code == "Europe":
            
            country_mask = return_europe_mask()
        else: 
            country_mask = country_masks.variables[country_code][:,:]
        #area of country 
        country_area_grid = (gridarea*country_mask)/1000000

        country_area_total=country_area_grid.sum()

        country_network_footprint_sens_total = (network_footprint * country_mask).sum()

        country_network_footprint_sens_km2 = country_network_footprint_sens_total/country_area_total
        
        data_specific_country.extend([country_network_footprint_sens_total, country_network_footprint_sens_km2])

        total = 0 
        
        for land_cover, land_cover_fraction, land_cover_name in zip(list_land_cover_classes, list_classes_fractions, land_cover_names):

            # country breakdown
            area_country_landcover = (land_cover*country_mask).sum()
            
            country_area_total_lc = (landcover_total_ocean_excluded*country_mask).sum()
            
            percent_country_breakdown = (area_country_landcover / country_area_total_lc)*100 

            # base network breakdown - use land_cover in km2 rather than fraction. Otherwise for instance
            # northern latitude cells which has a smaller area would be over-represented compared to reality. 
            sens_country_landcover_base = (country_mask * network_footprint * land_cover).sum()
            
            # here, can use land cover fraction because want sensing/km2 in the country.
            sens_country_landcover_base_km2 = (country_mask * network_footprint * land_cover_fraction).sum()/country_area_total_lc

            km2_sensing_total = (network_footprint * country_mask * landcover_total_ocean_excluded).sum() 
            if not sens_country_landcover_base == 0 and not km2_sensing_total == 0:
                percent_landcover_sens = (sens_country_landcover_base / km2_sensing_total)*100
            else:
                percent_landcover_sens = 0
            data_specific_country.extend([percent_country_breakdown, percent_landcover_sens, sens_country_landcover_base, sens_country_landcover_base_km2])
            
        df.loc[i] = data_specific_country
        i = i + 1 

    df_landcover_breakdown = df
    
    # sort countries from largest to smallest sensing/km2:
    list_sensing_countries = []
    list_countries = []
    for country_code in countries:  
        sensing_country = df_landcover_breakdown.loc[(df_landcover_breakdown['country'] == country_code)]['total_sens_km2'].iloc[0]
        list_sensing_countries.append(sensing_country)

    sorted_country_list = [x for _,x in sorted(zip(list_sensing_countries,countries), reverse = True)]
    
    sorted_country_list.append('Europe')
    
    # exluded ocean (3rd to last): '#1964B0',
    
    land_cover_values = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', \
                         'Pasture', 'Urban','Grass/shrubland', 'Other']
    
    land_cover_types =  ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'cropland', \
                      'pasture', 'urban', 'grass_shrub', 'other']

    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C',  '#F1932D', '#882E72']
    
    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(12,8)) 
    y_pos = np.arange(1)
    ax = plt.subplot(111)
    y_pos_steps = 1/(len(countries)/2)
    y_pos_minus = -1 + 1/(len(countries)/2)
    width = y_pos_steps/6
    
    list_y_pos = []
    first = True
    for country in sorted_country_list:
        bottom = 0
        bottom_country = 0
        # locate the row:
        country_row = df_landcover_breakdown.loc[df_landcover_breakdown['country'] == country] 

        list_y_pos.append(y_pos_minus)
        
        for landcover, landcover_color in zip(land_cover_types, colors): 

            # percent sensing of land cover within footprint
            value = float(country_row[landcover + '_sensing'])
            
            # compare to percent country for every country (not just Europe)
            value_country = float(country_row[landcover + '_country'])

            if first and landcover == 'broad_leaf_forest':
                    
                p1= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width=width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width=width, color = landcover_color,align='center')
     
            if first and landcover == 'coniferous_forest':
                p2= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width = width, color = landcover_color,align='center')
                     
                    
            if first and landcover == 'mixed_forest':
                p3= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
             
                                        
            if first and landcover == 'cropland':
                p4= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
                    
            if first and landcover == 'pasture':
                p5= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country,alpha = 0.5,  bottom = bottom_country, width =width, color = landcover_color,align='center')
     
                                        
            if first and landcover == 'urban':
                p6= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus +(y_pos_steps/7), value_country,alpha = 0.5,  bottom = bottom_country, width =width, color = landcover_color,align='center')
                                        
            if first and landcover == 'grass_shrub':
                p8= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
     
                                        
            if first and landcover == 'other':
                p9= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black',color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
                                 
                first = False

            if not first:
                ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width = width, color = landcover_color,align='center')
                
            bottom = bottom + value
            
            bottom_country = bottom_country + value_country
                
        y_pos_minus = y_pos_minus + y_pos_steps

    leg = Legend(ax, (p9[0], p8[0],p6[0],p5[0],p4[0], p3[0],p2[0],p1[0]), \
                 ('Other','Grass/shrubland','Urban','Pasture','Cropland', 'Mixed forest', \
                  'Coniferous forest','Broad leaf forest'), \
                 loc='upper right', title = '',  bbox_to_anchor=(1.24, 0.33))
    ax.add_artist(leg)

    list_country_names = []
    list_sensing_countries = []
    for country_code in sorted_country_list:
        if country_code == 'GBR':
            country_name = 'UK\n'
        if country_code == 'SRB':
            country_name = 'Serbia'
        else:
            country_name = dictionary_area_choice[country_code]
        #sens/km2 for specific station:
        sensing_country = df_landcover_breakdown.loc[(df_landcover_breakdown['country'] == country_code)]['total_sens_km2'].iloc[0]
        list_sensing_countries.append(sensing_country)
        sensing_country_formatted = "{:.1e}".format(sensing_country)
        list_country_names.append(country_name + ' (' + sensing_country_formatted + ')')
    
    countries=[textwrap.fill(text,12) for text in list_country_names]

    tuple_countries = tuple(countries)
    
    plt.xticks(np.array(list_y_pos),tuple_countries, rotation = 45)

    plt.axvline(x=y_pos_minus-(y_pos_steps*1.5), color = 'black', ls= '--')
    ax.set_ylabel('%')
    
    fig.text(.5, 0.9, "Land cover sensed by network within country (left) vs. present in country (right)", ha='center')

    fig.text(0.5, -0.03, "Country (sensitivity/km²)", ha='center')
   
                 
    if len(pngfile)>0:
        
        if not os.path.exists(output):
            os.makedirs(output)
  
        plt.savefig(output+'/'+pngfile,dpi=100,bbox_inches='tight')

    plt.show()
    
def share_representaiton_table(nwc, countries, csvfile = '', output = ''):

    countries = list(countries)
    countries.insert(0, 'Europe')
    representation_file = nwc['networkFile'] + '_representation.csv'
    
    df_to_analyze = pd.read_csv(os.path.join(nwc['pathFp'] + '_representation', representation_file))
        
    date_range = pd.date_range(dt.datetime(nwc['startYear'],nwc['startMonth'],nwc['startDay'],0), (dt.datetime(nwc['endYear'], nwc['endMonth'], nwc['endDay'], 21)), freq='3H')
    date_range_subset = [date for date in date_range if date.hour in nwc['timeOfDay']]
    date_range_string_alt = [str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' + str(date.hour) for date in date_range_subset]

    # usually the df_to_analyze contains a longer date range than the one of interest. 
    df_to_analyze_subset = df_to_analyze.loc[df_to_analyze['date'].isin(date_range_string_alt)]
    
    columns =  ['Country', 'Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Other', 'Grass and shrubland', 'Cropland', \
              'Pastures', 'Urban']
    
    df_country_flux_representation = pd.DataFrame(columns = columns)

    i = 0
    for country in countries:
        country_columns_gee = []

        for column in df_to_analyze_subset.columns:

            if country in column and 'gee' in column:
                
                if 'broad_leaf_forest' in column or 'coniferous_forest' in column or 'mixed_forest' in column \
                or 'cropland' in column or 'pasture' in column or 'urban' in column or 'grass_shrub' in column or 'other' in column:
                    country_columns_gee.append(column)
        df_subset_gee = abs(df_to_analyze_subset[country_columns_gee])
        df_subset_gee_mean = df_subset_gee.mean()
        
        df_subset_gee_mean_network = df_subset_gee_mean[::2].to_list()

        df_subset_gee_mean_network_even = df_subset_gee_mean[1::2].to_list()

        ratio_gee_list = []
        for network_gee, even_gee in zip(df_subset_gee_mean_network, df_subset_gee_mean_network_even):
            if network_gee>0:
                ratio_gee = ((network_gee/even_gee)*100)-100
                ratio_gee_list.append(ratio_gee)
            else:
                ratio_gee_list.append(np.nan)
        
        df_country_flux_representation.loc[i] = [country] + ratio_gee_list
        
        i = i + 1
        
        pd.set_option('display.float_format', lambda x: '%.0f' % x)
        
    df_country_flux_representation.to_csv(os.path.join(output, csvfile))  
    display(df_country_flux_representation) 
    
def flux_breakdown_countries_percentages(nwc, countries, pngfile='', output=''):
    
    representation_file = nwc['networkFile'] + '_representation.csv'
    
    df_fluxes_full = pd.read_csv(os.path.join(nwc['pathFp'] + '_representation', representation_file))
        
    date_range = pd.date_range(dt.datetime(nwc['startYear'],nwc['startMonth'],nwc['startDay'],0), (dt.datetime(nwc['endYear'], nwc['endMonth'], nwc['endDay'], 21)), freq='3H')
    date_range_subset = [date for date in date_range if date.hour in nwc['timeOfDay']]
    date_range_string_alt = [str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' + str(date.hour) for date in date_range_subset]

    # usually the df_fluxes_full contains a longer date range than the one of interest. 
    df_fluxes =  df_fluxes_full.loc[df_fluxes_full['date'].isin(date_range_string_alt)]

    fp_average_footprint = nwc['averageFp']
    representation_file = nwc['networkFile']+ '_representation.csv'    

    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')
    gridarea = f_gridarea.variables['cell_area'][:]/1000000
    
    # sort countries from largest to smallest sensing/km2:
    list_sensing_countries = []
    list_countries = []
    for country_code in countries:  
        
        if country_code == "Europe":
            country_mask = return_europe_mask()

        else:
            country_mask = country_masks.variables[country_code][:,:]
            
        sensing_km2 = (fp_average_footprint * country_mask).sum()/(gridarea * country_mask).sum()
        
        #sensing_country = df_landcover_breakdown.loc[(df_landcover_breakdown['country'] == country_code)]['total_sens_km2'].iloc[0]
        list_sensing_countries.append(sensing_km2)
    
    country_mask_europe = return_europe_mask()
    sensing_km2_europe = (fp_average_footprint * country_mask_europe).sum()/(gridarea * country_mask_europe).sum()

    sorted_country_list = [x for _,x in sorted(zip(list_sensing_countries,countries), reverse = True)]
    
    sorted_list_sensing_countries = [x for _,x in sorted(zip(list_sensing_countries,list_sensing_countries), reverse = True)]
    
    sorted_country_list.append('Europe')
    
    sorted_list_sensing_countries.append(sensing_km2_europe)

    # ocean 3rd to last
    land_cover_types =  ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'cropland', \
                      'pasture', 'urban', 'grass_shrub', 'other']
    
    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C', '#F1932D', '#882E72']
    
    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(12,8)) 
    #fig = plt.figure(figsize=(len(countries) + 1,len(countries)*0.75)) 
    y_pos = np.arange(1)
    ax = plt.subplot(111)
    #ax.yaxis.grid(True)

    y_pos_steps = 1/(len(countries)/2)
    #y_pos_minus = -0.95
    y_pos_minus = -1 + 1/(len(countries)/2)
    # should have the same y_postion if the same country
    width = y_pos_steps/6
    list_y_pos = []
    first = True
    for country in sorted_country_list:

        ### extract from flux dataframe
        country_columns_gee_even = []

        country_columns_gee_network = []

        for column in df_fluxes.columns:
            if country in column:
                if 'gee' in column:

                    if 'total' not in column:

                        # added
                        if 'ocean' not in column:

                            if 'even' in column:

                                country_columns_gee_even.append(column)

                            else:
                                #'network' in column:
                                country_columns_gee_network.append(column)

        df_even =  abs(df_fluxes[country_columns_gee_even])

        df_network = abs(df_fluxes[country_columns_gee_network])

        df_even_mean = df_even.mean()

        df_even_mean_percent = (df_even_mean/df_even_mean.sum())*100

        df_network_mean = df_network.mean()

        df_network_mean_percent = (df_network_mean/df_network_mean.sum())*100

        bottom = 0
        bottom_country = 0
        # locate the row:
        #country_row = df_landcover_breakdown.loc[df_landcover_breakdown['country'] == country] 

        list_y_pos.append(y_pos_minus)
        
        for landcover, landcover_color in zip(land_cover_types, colors): 
            
            # now percent
            value = float(df_network_mean_percent[country + '_' + landcover + '_gee'])
            
            # compare to percent country for every country (not just Europe)
            value_country = float(df_even_mean_percent[country + '_' + landcover + '_gee_even'])

            if first and landcover == 'broad_leaf_forest':
                    
                p1= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width=width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width=width, color = landcover_color,align='center')
     
            if first and landcover == 'coniferous_forest':
                p2= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width = width, color = landcover_color,align='center')
                    
            if first and landcover == 'mixed_forest':
                p3= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
             
                                        
            if first and landcover == 'cropland':
                p4= ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
     
                    
            if first and landcover == 'pasture':
                p5= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
     
                                        
            if first and landcover == 'urban':
                p6= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
     
        
            if first and landcover == 'grass_shrub':
                p8= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
     
                                        
            if first and landcover == 'other':
                p9= ax.bar(y_pos + y_pos_minus-(y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width =width, color = landcover_color,align='center')
                                 
                first = False

            if not first:
                ax.bar(y_pos + y_pos_minus - (y_pos_steps/7), value, bottom = bottom, width = width, edgecolor = 'black', color = landcover_color,align='center')
                ax.bar(y_pos + y_pos_minus + (y_pos_steps/7), value_country, alpha = 0.5, bottom = bottom_country, width = width, color = landcover_color,align='center')
                
            bottom = bottom + value
            
            bottom_country = bottom_country + value_country
                
        y_pos_minus = y_pos_minus + y_pos_steps
    #3rd ocean
    leg = Legend(ax, (p9[0], p8[0],p6[0],p5[0],p4[0], p3[0],p2[0],p1[0]), \
                 ('Other','Grass/shrubland','Urban','Pasture','Cropland', 'Mixed forest', \
                  'Coniferous forest','Broad leaf forest'), \
                 loc='upper right', title = '', bbox_to_anchor=(1.24, 0.33))

    ax.add_artist(leg)
    
    list_country_names = []
    list_sensing_countries = []
    i = 0
    for country_code in sorted_country_list:
        if country_code == 'GBR':
            country_name = 'UK\n'
        if country_code == 'SRB':
            country_name = 'Serbia'
        else:
            
            country_name = dictionary_area_choice[country_code]
        #sens/km2 for specific country:
        sensing_country = sorted_list_sensing_countries[i]

        sensing_country_formatted = "{:.1e}".format(sensing_country)

        list_country_names.append(country_name+ ' (' + sensing_country_formatted + ')')
        
        i = i + 1
    
    countries=[textwrap.fill(text,12) for text in list_country_names]

    tuple_countries = tuple(countries)
    
    plt.xticks(np.array(list_y_pos),tuple_countries, rotation = 45)

    #0.97
    plt.axvline(x=y_pos_minus-(y_pos_steps*1.5), color = 'black', ls= '--')
    ax.set_ylabel('%')
    fig.text(.5, 0.9, "GEE sensed by the network within country (left) vs. present in country (right)", ha='center')
                 
    if len(pngfile)>0:
        
        if not os.path.exists(output):
            os.makedirs(output)
  
        plt.savefig(output+'/'+pngfile,dpi=100,bbox_inches='tight')

        
    plt.show()
    
def initiate_monitoring_potential_maps(nwc, extended = False):
   
    """countries = [('Europe', 'Europe'),('Albania','ALB'),('Andorra','Andorra'),('Austria','AUT'),('Belarus','BLR'),('Belgium','BEL'),('Bosnia and Herzegovina','BIH'),('Bulgaria','BGR'),('Croatia','HRV'),('Cyprus','CYP'),('Czechia','CZE'),('Denmark','DNK'),('Estonia','EST'),('Finland','FIN'),('France','FRA'),('Germany','DEU'),('Greece','GRC'),('Hungary','HUN'),('Ireland','IRL'),('Italy','ITA'),('Kosovo','XKX'),('Latvia','LVA'),('Liechtenstein','LIE'),('Lithuania','LTU'),('Luxembourg','LUX'),('Macedonia','MKD'),('Malta','MTL'),('Moldova','MDA'),('Montenegro','MNE'),('Netherlands','NLD'),('Norway','NOR'),('Poland','POL'),('Portugal','PRT'),('Republic of Serbia','SRB'),('Romania','ROU'),('San Marino','SMR'),('Slovakia','SVK'),('Slovenia','SVN'),('Spain','ESP'),('Sweden','SWE'),('Switzerland','CHE'),('United Kingdom','GBR')]"""
    
    countries = [('Europe', 'Europe'),('Austria','AUT'),('Belgium','BEL'),('Czechia','CZE'),('Denmark','DNK'),('Estonia','EST'),('Finland','FIN'),('France','FRA'),('Germany','DEU'),('Greece','GRC'),('Hungary','HUN'),('Ireland','IRL'),('Italy','ITA'),('Netherlands','NLD'),('Norway','NOR'),('Poland','POL'),('Spain','ESP'),('Sweden','SWE'),('Switzerland','CHE'),('United Kingdom','GBR')]

    country_choice = Dropdown(options = countries,
                       description = 'Country',
                       layout = {'height': 'initial'},
                       value="Europe",
                       disabled= False)
    
    
    update_button = Button(description='Run selection',
                       disabled=False, # disabed until a station has been selected
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)
    
    update_button.style.button_color='#4169E1'
    
    def update_func(button_c):
        
        update_button.disabled = True
        
        result_monitoring_potential.clear_output()
        
        with result_monitoring_potential:

        
            monitoring_potential_maps(nwc, country_choice.value, extended = extended)
            
        update_button.disabled = False
        
    
    update_button.on_click(update_func)
    
    
    result_monitoring_potential = Output()
    form_out = Output()
 
    with form_out:
        
        display(country_choice, update_button, result_monitoring_potential)
        
    display(form_out)
    
# this function will improve
def monitoring_potential_maps(nwc, country, extended = False):

    folder_current =nwc['networkFile']
    folder_extended = nwc['extendedNetwork']
    date_range = pd.date_range(dt.datetime(nwc['startYear'],nwc['startMonth'],nwc['startDay'],0), (dt.datetime(nwc['endYear'], nwc['endMonth'], nwc['endDay'], 21)), freq='3H')
    date_range_subset = [date for date in date_range if date.hour in nwc['timeOfDay']]
    
    f = IntProgress(min=0, max=len(date_range_subset)) # instantiate the bar

    display(f) 
    
    if extended: 
        
        if nwc['extendedNetwork']== 'No extension':
            display(HTML('<p style="font-size:14px;">Specify an "extended network" in the section "The view from the current ICOS network".</p>'))
            return
      
        reference = nwc['extendedNetwork']
    #if reference != '':
        # compare so that the analysed network really is an extension to the reference network
        
        # station list extended network:
        json_file_extended = nwc['extendedNetwork'] + '.json' 
        extended_network_footprint_info = open(os.path.join(nwc['pathFpExtended'], json_file_extended))
        extended_network_footprint_info_load = json.load(extended_network_footprint_info)
        extended_stations = extended_network_footprint_info_load['stations']

        json_file_reference = nwc['networkFile'] + '.json'
        
        reference_network_footprint_info = open(os.path.join(nwc['pathFp'], json_file_reference))
        reference_network_footprint_info_load = json.load(reference_network_footprint_info)
        reference_stations = reference_network_footprint_info_load['stations']

        added_stations = [station for station in extended_stations if station not in reference_stations]

        # stop the code in case the reference network stations are not all in the extended network
        check_feasibility = [station for station in reference_stations if station not in extended_stations]
        
        if len(check_feasibility) > 0:
            
            check_feasibility_string = ', '.join([str(elem) for elem in check_feasibility])[:-1]
            
            display(HTML('<p style="font-size:14px;">This part of the tool is meant to compare an (extended) network to a reference network. In this case, the reference network contains stations that are not included in the extended network (' + check_feasibility_string + ')</p>'))

 
        else:
            
            added_stations_string = ', '.join([str(elem) for elem in added_stations])[:-1]
            
            display(HTML('<p style="font-size:14px;">Results for the reference network extended with station: ' + added_stations_string + '</p>'))
            
            #loaded_footprints_reference = nwc['loadedFps'] 
            
        #loaded_footprints = nwc['loadedFpsExtended']
        
    else:
        reference = ''
        #loaded_footprints = nwc['loadedFps'] 

    if country == "Europe":
        country_mask = return_europe_mask()

    else:
        country_mask = country_masks.variables[country][:,:]

    # grid area (m2) of each cell:
    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')
    gridarea = f_gridarea.variables['cell_area'][:]/1000000

    # access the flux data
    filename_resp = check_cp(path_cp,'VPRM_ECMWF_RESP_2020_CP.nc')

    filename_gee = check_cp(path_cp,'VPRM_ECMWF_GEE_2020_CP.nc')

    f_resp = cdf.Dataset(filename_resp)

    f_gee = cdf.Dataset(filename_gee)

    # same for both datasets
    times = f_resp.variables['time']

    list_landcover_names = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    # access HILDA land cover data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    list_classes_km2 = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown]

    # want vegetation fraction HILDA land cover maps (as opposed to km2 for the entire cell - "list_classes_km2")
    list_landcover_fractions = []

    for landcover in list_classes_km2:

        landcover_fraction = landcover/gridarea

        list_landcover_fractions.append(landcover_fraction)

    # counter to place the data in a new row for each date
    i = 0
    first = True

    for date in date_range_subset:
        f.value += 1

        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)
        # this is for correct column name in the saved network footprints 
        fp_string = str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' +  str(date.hour)

        ntime = date2index(date,times,select='nearest')

        resp = f_resp.variables['RESP'][ntime][:][:]
        gee = f_gee.variables['GEE'][ntime][:][:]

        # access dataframe column with saved network footprint
        #fp_network_50 = np.array(loaded_footprints[fp_string].to_list()).reshape(480, 400)
        if extended:
            
            filename = os.path.join(nwc['pathFpExtended'], folder_extended, fp_string + '.csv')
        else:
            filename = os.path.join(nwc['pathFp'], folder_current, fp_string + '.csv')
        network_fp = pd.read_csv(filename)
        fp_network_50 = np.array(network_fp[fp_string].to_list()).reshape(480, 400)


        # network view of fluxes
        fp_network_50_resp = fp_network_50 * resp * country_mask
        fp_network_50_gee = fp_network_50 * gee * country_mask

        #create "fake footprint" where evenly spread out sensing capacity
        # if want to see the improvement of adding stations, use a reference network. That way the same colorbar can be applied
        # and the color will only change if there is added sensing to the cell in the extended network.
        if extended:
            
            filename = os.path.join(nwc['pathFpExtended'], folder_extended, fp_string + '.csv')
            network_fp = pd.read_csv(filename)
            fp_orig = np.array(network_fp[fp_string].to_list()).reshape(480, 400)

            # reference for average footprint
            #fp_orig = np.array(loaded_footprints_reference[fp_string].to_list()).reshape(480, 400)
            sum_sensing = (fp_orig * country_mask).sum()
            
            sum_sensing_original = (fp_network_50 * country_mask).sum()  
            average_sens_original = sum_sensing_original / country_mask.sum()
            
            sens_per_cell_list_original = [average_sens_original]*192000
            
            fp_network_50_even_original =np.array(sens_per_cell_list_original).reshape((len(load_lat), len(load_lon)))
            
            fp_network_50_even_resp_original = fp_network_50_even_original * resp * country_mask 
            fp_network_50_even_gee_original = fp_network_50_even_original * gee * country_mask 


        else:

            sum_sensing = (fp_network_50 * country_mask).sum()   

        average_sens = sum_sensing / country_mask.sum()

        sens_per_cell_list = [average_sens]*192000

        fp_network_50_even=np.array(sens_per_cell_list).reshape((len(load_lat), len(load_lon)))

        fp_network_50_even_resp = fp_network_50_even * resp * country_mask 
        fp_network_50_even_gee = fp_network_50_even * gee * country_mask 

        for landcover_hilda, landcover_name in zip(list_landcover_fractions, list_landcover_names):

            # added - multiply landcover_hilda by country mask. If not use land cover fraction. 
            total_resp_landcover = fp_network_50_resp * landcover_hilda 
            total_gee_landcover = fp_network_50_gee * landcover_hilda 

            total_resp_landcover_even = fp_network_50_even_resp * landcover_hilda
            total_gee_landcover_even = fp_network_50_even_gee * landcover_hilda   
            
            if extended:
                
                total_resp_landcover_even_original = fp_network_50_even_resp_original * landcover_hilda
                total_gee_landcover_even_original = fp_network_50_even_gee_original * landcover_hilda    

            if landcover_name == 'broad_leaf_forest':

                if first:

                    for_average_network_resp_bl = total_resp_landcover
                    for_average_even_resp_bl =  total_resp_landcover_even

                    for_average_network_gee_bl = total_gee_landcover
                    for_average_even_gee_bl = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_bl_orig =  total_resp_landcover_even_original
                        for_average_even_gee_bl_orig =  total_gee_landcover_even_original

                else: 

                    for_average_network_resp_bl = for_average_network_resp_bl + total_resp_landcover
                    for_average_even_resp_bl =  for_average_even_resp_bl + total_resp_landcover_even

                    for_average_network_gee_bl = for_average_network_gee_bl + total_gee_landcover
                    for_average_even_gee_bl = for_average_even_gee_bl + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_bl_orig =  for_average_even_resp_bl_orig + total_resp_landcover_even_original
                        for_average_even_gee_bl_orig =  for_average_even_gee_bl_orig + total_gee_landcover_even_original             

            if landcover_name == 'coniferous_forest':

                if first:

                    for_average_network_resp_cf = total_resp_landcover
                    for_average_even_resp_cf =  total_resp_landcover_even

                    for_average_network_gee_cf = total_gee_landcover
                    for_average_even_gee_cf = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_cf_orig =  total_resp_landcover_even_original
                        for_average_even_gee_cf_orig =  total_gee_landcover_even_original

                else: 

                    for_average_network_resp_cf = for_average_network_resp_cf + total_resp_landcover
                    for_average_even_resp_cf =  for_average_even_resp_cf + total_resp_landcover_even

                    for_average_network_gee_cf = for_average_network_gee_cf + total_gee_landcover
                    for_average_even_gee_cf = for_average_even_gee_cf + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_cf_orig =  for_average_even_resp_cf_orig + total_resp_landcover_even_original
                        for_average_even_gee_cf_orig =  for_average_even_gee_cf_orig + total_gee_landcover_even_original  


            if landcover_name == 'mixed_forest':

                if first:

                    for_average_network_resp_mf = total_resp_landcover
                    for_average_even_resp_mf =  total_resp_landcover_even

                    for_average_network_gee_mf = total_gee_landcover
                    for_average_even_gee_mf = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_mf_orig =  total_resp_landcover_even_original
                        for_average_even_gee_mf_orig =  total_gee_landcover_even_original

                else: 

                    for_average_network_resp_mf = for_average_network_resp_mf + total_resp_landcover
                    for_average_even_resp_mf =  for_average_even_resp_mf + total_resp_landcover_even

                    for_average_network_gee_mf = for_average_network_gee_mf + total_gee_landcover
                    for_average_even_gee_mf = for_average_even_gee_mf + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_mf_orig =  for_average_even_resp_mf_orig + total_resp_landcover_even_original
                        for_average_even_gee_mf_orig =  for_average_even_gee_mf_orig + total_gee_landcover_even_original  

            if landcover_name == 'grass_shrub':

                if first:

                    for_average_network_resp_gs = total_resp_landcover
                    for_average_even_resp_gs =  total_resp_landcover_even

                    for_average_network_gee_gs = total_gee_landcover
                    for_average_even_gee_gs = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_gs_orig =  total_resp_landcover_even_original
                        for_average_even_gee_gs_orig =  total_gee_landcover_even_original

                else: 

                    for_average_network_resp_gs = for_average_network_resp_gs + total_resp_landcover
                    for_average_even_resp_gs =  for_average_even_resp_gs + total_resp_landcover_even

                    for_average_network_gee_gs = for_average_network_gee_gs + total_gee_landcover
                    for_average_even_gee_gs = for_average_even_gee_gs + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_gs_orig =  for_average_even_resp_gs_orig + total_resp_landcover_even_original
                        for_average_even_gee_gs_orig =  for_average_even_gee_gs_orig + total_gee_landcover_even_original  

            if landcover_name == 'pasture':

                if first:

                    for_average_network_resp_pa = total_resp_landcover
                    for_average_even_resp_pa =  total_resp_landcover_even

                    for_average_network_gee_pa = total_gee_landcover
                    for_average_even_gee_pa = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_pa_orig =  total_resp_landcover_even_original
                        for_average_even_gee_pa_orig =  total_gee_landcover_even_original

                else: 

                    for_average_network_resp_pa = for_average_network_resp_pa + total_resp_landcover
                    for_average_even_resp_pa =  for_average_even_resp_pa + total_resp_landcover_even

                    for_average_network_gee_pa = for_average_network_gee_pa + total_gee_landcover
                    for_average_even_gee_pa = for_average_even_gee_pa + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_pa_orig =  for_average_even_resp_pa_orig + total_resp_landcover_even_original
                        for_average_even_gee_pa_orig =  for_average_even_gee_pa_orig + total_gee_landcover_even_original  


            if landcover_name == 'cropland':

                if first:

                    for_average_network_resp_cl = total_resp_landcover
                    for_average_even_resp_cl =  total_resp_landcover_even

                    for_average_network_gee_cl = total_gee_landcover
                    for_average_even_gee_cl = total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_cl_orig =  total_resp_landcover_even_original
                        for_average_even_gee_cl_orig =  total_gee_landcover_even_original
                else: 

                    for_average_network_resp_cl = for_average_network_resp_cl + total_resp_landcover
                    for_average_even_resp_cl =  for_average_even_resp_cl + total_resp_landcover_even

                    for_average_network_gee_cl = for_average_network_gee_cl + total_gee_landcover
                    for_average_even_gee_cl = for_average_even_gee_cl + total_gee_landcover_even 
                    
                    if extended:
                        
                        for_average_even_resp_cl_orig =  for_average_even_resp_cl_orig + total_resp_landcover_even_original
                        for_average_even_gee_cl_orig =  for_average_even_gee_cl_orig + total_gee_landcover_even_original  

        # save average representations (total gee, total resp)
        if first:
            for_average_network_resp = fp_network_50_resp
            for_average_even_resp =  fp_network_50_even_resp

            for_average_network_gee = fp_network_50_gee
            for_average_even_gee = fp_network_50_even_gee

            first = False
            
            if extended:
                        
                for_average_even_resp_orig =  fp_network_50_even_resp_original
                for_average_even_gee_orig =  fp_network_50_even_gee_original

        else: 

            for_average_network_resp = for_average_network_resp + fp_network_50_resp
            for_average_even_resp =  for_average_even_resp + fp_network_50_even_resp

            for_average_network_gee = for_average_network_gee + fp_network_50_gee
            for_average_even_gee = for_average_even_gee + fp_network_50_even_gee 
            
            if extended:
                        
                for_average_even_resp_orig =  for_average_even_resp_orig + fp_network_50_even_resp_original
                for_average_even_gee_orig =  for_average_even_gee_orig + fp_network_50_even_gee_original 

        i = i + 1

    # average and save as df
    df_network_and_average_fluxes = pd.DataFrame()

    # total flux in europe
    average_network_resp = for_average_network_resp / i
    df_network_and_average_fluxes['average_network_resp'] = average_network_resp.flatten()
    average_even_resp =  for_average_even_resp / i
    df_network_and_average_fluxes['average_even_resp'] = average_even_resp.flatten()
    
    average_network_gee = for_average_network_gee / i
    df_network_and_average_fluxes['average_network_gee'] = average_network_gee.flatten()
    average_even_gee = for_average_even_gee / i
    df_network_and_average_fluxes['average_even_gee'] = average_even_gee.flatten()

    # broad leaf forest flux
    average_network_resp_bl = for_average_network_resp_bl / i
    df_network_and_average_fluxes['average_network_resp_bl'] = average_network_resp_bl.flatten()
    average_even_resp_bl =  for_average_even_resp_bl / i
    df_network_and_average_fluxes['average_even_resp_bl'] = average_even_resp_bl.flatten()

    average_network_gee_bl = for_average_network_gee_bl / i
    df_network_and_average_fluxes['average_network_gee_bl'] = average_network_gee_bl.flatten()
    average_even_gee_bl = for_average_even_gee_bl / i 
    df_network_and_average_fluxes['average_even_gee_bl'] = average_even_gee_bl.flatten()

    # coniferous forest flux
    average_network_resp_cf = for_average_network_resp_cf / i
    df_network_and_average_fluxes['average_network_resp_cf'] = average_network_resp_cf.flatten()
    average_even_resp_cf =  for_average_even_resp_cf / i
    df_network_and_average_fluxes['average_even_resp_cf'] = average_even_resp_cf.flatten()

    average_network_gee_cf = for_average_network_gee_cf / i
    df_network_and_average_fluxes['average_network_gee_cf'] = average_network_gee_cf.flatten()
    average_even_gee_cf = for_average_even_gee_cf / i
    df_network_and_average_fluxes['average_even_gee_cf'] = average_even_gee_cf.flatten()

    # mixed forest flux
    average_network_resp_mf = for_average_network_resp_mf / i
    df_network_and_average_fluxes['average_network_resp_mf'] = average_network_resp_mf.flatten()
    average_even_resp_mf =  for_average_even_resp_mf / i
    df_network_and_average_fluxes['average_even_resp_mf'] = average_even_resp_mf.flatten()

    average_network_gee_mf = for_average_network_gee_mf / i
    df_network_and_average_fluxes['average_network_gee_mf'] = average_network_gee_mf.flatten()
    average_even_gee_mf = for_average_even_gee_mf / i
    df_network_and_average_fluxes['average_even_gee_mf'] = average_even_gee_mf.flatten()

    # grass and shurb flux
    average_network_resp_gs = for_average_network_resp_gs / i
    df_network_and_average_fluxes['average_network_resp_gs'] = average_network_resp_gs.flatten()
    average_even_resp_gs =  for_average_even_resp_gs / i
    df_network_and_average_fluxes['average_even_resp_gs'] = average_even_resp_gs.flatten()

    average_network_gee_gs = for_average_network_gee_gs / i
    df_network_and_average_fluxes['average_network_gee_gs'] = average_network_gee_gs.flatten()
    average_even_gee_gs = for_average_even_gee_gs / i
    df_network_and_average_fluxes['average_even_gee_gs'] = average_even_gee_gs.flatten()

    # pasture flux:
    average_network_resp_pa = for_average_network_resp_pa / i
    df_network_and_average_fluxes['average_network_resp_pa'] = average_network_resp_pa.flatten()
    average_even_resp_pa =  for_average_even_resp_pa / i
    df_network_and_average_fluxes['average_even_resp_pa'] = average_even_resp_pa.flatten()

    average_network_gee_pa = for_average_network_gee_pa / i
    df_network_and_average_fluxes['average_network_gee_pa'] = average_network_gee_pa.flatten()
    average_even_gee_pa = for_average_even_gee_pa / i
    df_network_and_average_fluxes['average_even_gee_pa'] = average_even_gee_pa.flatten()

    # cropland flux
    average_network_resp_cl = for_average_network_resp_cl / i
    df_network_and_average_fluxes['average_network_resp_cl'] = average_network_resp_cl.flatten()
    average_even_resp_cl =  for_average_even_resp_cl / i
    df_network_and_average_fluxes['average_even_resp_cl'] = average_even_resp_cl.flatten()

    average_network_gee_cl = for_average_network_gee_cl / i
    df_network_and_average_fluxes['average_network_gee_cl'] = average_network_gee_cl.flatten()
    average_even_gee_cl = for_average_even_gee_cl / i
    df_network_and_average_fluxes['average_even_gee_cl'] = average_even_gee_cl.flatten()
    
    if extended:
        
        # total flux in europe
        average_even_resp_orig =  for_average_even_resp_orig / i
        df_network_and_average_fluxes['average_even_resp_orig'] = average_even_resp_orig.flatten()

        average_even_gee_orig = for_average_even_gee_orig / i
        df_network_and_average_fluxes['average_even_gee_orig'] = average_even_gee_orig.flatten()

        # broad leaf forest flux
        average_even_resp_bl_orig =  for_average_even_resp_bl_orig / i
        df_network_and_average_fluxes['average_even_resp_bl_orig'] = average_even_resp_bl_orig.flatten()

        average_even_gee_bl_orig = for_average_even_gee_bl_orig / i 
        df_network_and_average_fluxes['average_even_gee_bl_orig'] = average_even_gee_bl_orig.flatten()

        # coniferous forest flux
        average_even_resp_cf_orig =  for_average_even_resp_cf_orig / i
        df_network_and_average_fluxes['average_even_resp_cf_orig'] = average_even_resp_cf_orig.flatten()

        average_even_gee_cf_orig = for_average_even_gee_cf_orig / i
        df_network_and_average_fluxes['average_even_gee_cf_orig'] = average_even_gee_cf_orig.flatten()

        # mixed forest flux
        average_even_resp_mf_orig =  for_average_even_resp_mf_orig / i
        df_network_and_average_fluxes['average_even_resp_mf_orig'] = average_even_resp_mf_orig.flatten()

        average_even_gee_mf_orig = for_average_even_gee_mf_orig / i
        df_network_and_average_fluxes['average_even_gee_mf_orig'] = average_even_gee_mf_orig.flatten()

        # grass and shurb flux
        average_even_resp_gs_orig =  for_average_even_resp_gs_orig / i
        df_network_and_average_fluxes['average_even_resp_gs_orig'] = average_even_resp_gs_orig.flatten()

        average_even_gee_gs_orig = for_average_even_gee_gs_orig / i
        df_network_and_average_fluxes['average_even_gee_gs_orig'] = average_even_gee_gs_orig.flatten()

        # pasture flux:
        average_even_resp_pa_orig =  for_average_even_resp_pa_orig / i
        df_network_and_average_fluxes['average_even_resp_pa_orig'] = average_even_resp_pa_orig.flatten()

        average_even_gee_pa_orig = for_average_even_gee_pa_orig / i
        df_network_and_average_fluxes['average_even_gee_pa_orig'] = average_even_gee_pa_orig.flatten()

        # cropland flux
        average_even_resp_cl_orig =  for_average_even_resp_cl_orig / i
        df_network_and_average_fluxes['average_even_resp_cl_orig'] = average_even_resp_cl_orig.flatten()

        average_even_gee_cl_orig = for_average_even_gee_cl_orig / i
        df_network_and_average_fluxes['average_even_gee_cl_orig'] = average_even_gee_cl_orig.flatten()

    if country != 'Europe' and country != 'France' and country != 'Norway' and country!='Spain':
        
        overview_map(country)

    percentile = 99.9

    # can change to 'resp' here. 
    component = 'gee'
    
    index = 0
    
    index_within = 0
    
    columns_original = [column for column in df_network_and_average_fluxes.columns if 'orig' in column.split("_") and component in column.split("_")]

    for column in df_network_and_average_fluxes.columns:

        column_list = column.split("_")

        if component in column:

            if column_list[1] == 'network':
                

                colors = color_name_dict[column_list[-1]]['color']
                name = color_name_dict[column_list[-1]]['name']

                footprint = np.array(df_network_and_average_fluxes[column].to_list()).reshape((len(load_lat), len(load_lon)))

                column_even = df_network_and_average_fluxes.columns[index + 1]

                footprint_even = np.array(df_network_and_average_fluxes[column_even].to_list()).reshape((len(load_lat), len(load_lon)))

                if extended:
                    footprint_even_original = np.array(df_network_and_average_fluxes[columns_original[index_within]].to_list()).reshape((len(load_lat), len(load_lon)))
                    index_within = index_within + 1
                    percent = (footprint.sum() / footprint_even_original.sum()) * 100
                    percent_compare = percent - 100 
                    
                else:
                    percent = (footprint.sum() / footprint_even.sum()) * 100
                    percent_compare = percent - 100 

                if percent_compare > 0:
                    add_for_title = '(+' + str("%.1f" % percent_compare) + '% representation)' 

                else:
                    add_for_title =  '(-' + str("%.1f" % abs(percent_compare)) + '% representation)'   

                if country == 'Europe':
                    if not np.percentile(abs(footprint_even),percentile) < 0.0001:
                        #vmax = np.percentile(abs(footprint_even),percentile)
                        plot_maps(abs(footprint_even)-abs(footprint), load_lon, load_lat,nwc, title = (name + ' monitoring potential '+ add_for_title), colors = colors, output='monitoring_potential_maps',label = 'relatively low potential                                                                           relatively high potential', reference = reference, monitoring_potential = True)

                    else:
                        print('Sensing of ' +  name +' in ' + country_name + ' is very low and it is not feaible to show monitoring potential of')

                else:

                    zoom_lat = country_code_zoom_dict[country]['lat']
                    zoom_lon = country_code_zoom_dict[country]['lon']
                    zoom_level = country_code_zoom_dict[country]['zoom']
                    country_name = country_code_name_dict[country]

                    plot_maps_country_zoom(abs(footprint_even)-abs(footprint), load_lon, load_lat, nwc, zoom_lat=zoom_lat, zoom_lon=zoom_lon, zoom_level=zoom_level, title = (name + ' monitoring potential ' + country_name + ' ' + add_for_title),  output='monitoring_potential_maps', colors = colors,label = 'relatively low potential                                                                           relatively high potential', reference = reference, monitoring_potential = True)

        index = index + 1

# Station characterization
def signals_table_anthro(stc):
    
    stations = stc['signalsStations']
    timeselect_list = stc['timeOfDay']
    date_range_whole = pd.date_range(dt.datetime(stc['startYear'],stc['startMonth'],stc['startDay'],0), (dt.datetime(stc['endYear'], stc['endMonth'], stc['endDay'], 21)), freq='3H')
    
    date_range = [date for date in date_range_whole if date.hour in timeselect_list]

    df_save = pd.DataFrame(columns= ['Station',
                                     'Transport (ppm)','Energy (ppm)','Industry (ppm)','Residential (ppm)', 'Other categories (ppm)', 'Total (ppm)',\
                                     'Gas (ppm)', 'Bio (ppm)', 'Waste (ppm)', 'Oil (ppm)', 'Coal (ppm)', 'Cement (ppm)'])

    index = 0
    for station in stations:

        #df_winter1 = read_stilt_timeseries(station, winter_date_range1, timeselect_list)
        #df_winter2 = read_stilt_timeseries(station, winter_date_range2, timeselect_list)
        df_winter = read_stilt_timeseries(station, date_range, timeselect_list)
        
        df_winter_only_number = df_winter.select_dtypes(['number'])
        #df_winter = df_winter1.append(df_winter2)
        df_winter_mean=df_winter_only_number.mean()

        source_categories = [df_winter_mean['co2.transport'], df_winter_mean['co2.energy'],\
                            df_winter_mean['co2.industry'], df_winter_mean['co2.residential'], df_winter_mean['co2.other_categories']]
        total = df_winter_mean['co2.transport'] + df_winter_mean['co2.energy'] +\
                            df_winter_mean['co2.industry']+ df_winter_mean['co2.residential']+ df_winter_mean['co2.other_categories']

        
        fuel_categories = [df_winter_mean['co2.fuel.gas'], df_winter_mean['co2.fuel.bio'], df_winter_mean['co2.fuel.waste'],\
                            df_winter_mean['co2.fuel.oil'], df_winter_mean['co2.fuel.coal'], df_winter_mean['co2.cement'],]



        df_save.loc[index] = [station] + source_categories + [total] + fuel_categories
        index = index + 1
        
    df_save_sort = df_save.sort_values(by=['Station'])
    subset_style = subset = ['Transport (ppm)','Energy (ppm)','Industry (ppm)','Residential (ppm)', 'Other categories (ppm)', 'Gas (ppm)', 'Bio (ppm)', 'Waste (ppm)','Oil (ppm)', 'Coal (ppm)', 'Cement (ppm)']
    subset_format = {key: "{:.2f}" for key in subset_style}
    subset_format['Total (ppm)'] = '{:.2f}'
    df_save_sort_styled = df_save_sort.style.background_gradient(cmap='Reds', axis=None, subset = subset_style)\
                                            .format(subset_format)
    display(df_save_sort_styled)
    
    #df_save.to_csv(name_save + '.csv', index = False)
    
def signals_table_bio(stc, component='gee'):   
    
    stations = stc['signalsStations']
    timeselect_list = stc['timeOfDay']
    
    date_range_whole = pd.date_range(dt.datetime(stc['startYear'],stc['startMonth'],stc['startDay'],0), (dt.datetime(stc['endYear'], stc['endMonth'], stc['endDay'], 21)), freq='3H')
    
    date_range = [date for date in date_range_whole if date.hour in timeselect_list]
    
    
    #only applies to the stilt timeseries - do not change!
    timeselect_list=stc['timeOfDay']

    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')

    gridarea = f_gridarea.variables['cell_area'][:]/1000000

    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    list_classes_names = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    list_classes_km2 = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, \
                        pasture, urban, unknown]

    # want vegetation fraction HILDA land cover maps (as opposed to km2 for the entire cell - "list_classes_km2")
    list_classes = []

    for landcover in list_classes_km2:

        landcover_fraction = landcover/gridarea

        list_classes.append(landcover_fraction)

    df_save = pd.DataFrame(columns= ['Station',
                                     'Respiration total', 
                                     '(Respiration total (STILT))',
                                    'GEE total', '(GEE total (STILT))',
                                    'Broad leaf forest (Resp)', 'Broad leaf forest (GEE)', 
                                    'Coniferous forest (Resp)',  'Coniferous forest (GEE)',\
                                    'Mixed forest (Resp)', 'Mixed forest (GEE)',\
                                    'Ocean (Resp)','Ocean (GEE)', \
                                    'Other (Resp)', 'Other (GEE)', \
                                    'Grass and shrub (Resp)',  'Grass and shrub (GEE)',\
                                    'Cropland (Resp)', 'Cropland (GEE)',\
                                    'Pasture (Resp)', 'Pasture (GEE)',
                                    'Urban (Resp)', 'Urban (GEE)',\
                                    'Unknown (Resp)', 'Unknown (GEE)', 'Total GEE (ppm)'])

    # index for putting the data for each station (mean) in the correct place in the dataframe "df_save"
    i_outer = 0

    for station in stations:

        df_stilt_result = read_stilt_timeseries(station, date_range, timeselect_list)
        df_stilt_result = df_stilt_result.reset_index()

        df_save_station = pd.DataFrame(columns= ['Station','date', 'Respiration total', '(Respiration total (STILT))',\
                                        'GEE total', '(GEE total (STILT))',
                                        'Broad leaf forest (Resp)', 'Broad leaf forest (GEE)', 
                                        'Coniferous forest (Resp)',  'Coniferous forest (GEE)',\
                                        'Mixed forest (Resp)', 'Mixed forest (GEE)',\
                                        'Ocean (Resp)','Ocean (GEE)', \
                                        'Other (Resp)', 'Other (GEE)',\
                                        'Grass and shrub (Resp)',  'Grass and shrub (GEE)',\
                                        'Cropland (Resp)', 'Cropland (GEE)',\
                                        'Pasture (Resp)', 'Pasture (GEE)',
                                        'Urban (Resp)', 'Urban (GEE)',\
                                        'Unknown (Resp)', 'Unknown (GEE)', 'Total GEE (ppm)'])

        # index for putting the data for each station for each date in the correct place in the dataframe "df_save_station"
        i = 0 
        first = True
        current_year = 0
        for date in date_range:

            # access the correct VPRM flux dataset
            if first or date.year!=current_year:

                current_year = date.year

                filename_resp = check_cp(path_cp,'VPRM_ECMWF_RESP_' + str(current_year) + '_CP.nc')

                filename_gee = check_cp(path_cp,'VPRM_ECMWF_GEE_' + str(current_year) + '_CP.nc')

                f_resp = cdf.Dataset(filename_resp)

                f_gee = cdf.Dataset(filename_gee)

                # same for both datasets
                times = f_resp.variables['time']

                first = False


            date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)

            ntime = date2index(date,times,select='nearest')

            resp = f_resp.variables['RESP'][ntime][:][:]

            gee = f_gee.variables['GEE'][ntime][:][:]

            filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
                 +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename):


                f_fp = cdf.Dataset(filename)
                fp=f_fp.variables['foot'][:,:,:]

                fp_resp_station = resp * fp 
                respiration_station = fp_resp_station.sum()    

                fp_gee_station = abs(gee) * fp
                gee_station = fp_gee_station.sum()   
                respiration_station_stilt = df_stilt_result[df_stilt_result['date'] == date]['co2.bio.resp'].to_list()[0]
                gee_station_stilt = abs(df_stilt_result[df_stilt_result['date'] == date]['co2.bio.gee'].to_list()[0])

                # to be extended with land cover data
                data_row = [station, date_string, respiration_station, respiration_station_stilt, gee_station, gee_station_stilt]

                total_gee = 0
                for landcover_hilda, landcover_name in zip(list_classes, list_classes_names):

                    fp_resp_station_landcover = fp_resp_station * landcover_hilda
                    respiration_station_landcover_class = fp_resp_station_landcover.sum()    

                    fp_gee_station_landcover = fp_gee_station * landcover_hilda
                    gee_station_landcover_class = fp_gee_station_landcover.sum()    
                    total_gee = total_gee + gee_station_landcover_class
                    
            
                    data_row.extend([respiration_station_landcover_class, gee_station_landcover_class])

                df_save_station.loc[i] = data_row + [total_gee]


                i = i + 1

        # un-comment here to save the timeseries for each of the stations
        #file_name = 'biogenic_summer2020_' + station + '_jun_aug_2020.csv'

        #df_save_station.to_csv(file_name, index=False)
        
        df_save_station_only_number = df_save_station.select_dtypes(['number'])

        df_save_station_mean = df_save_station_only_number.mean().to_list()

        df_save_station_mean.insert(0, station)
        
        df_save.loc[i_outer] = df_save_station_mean

        i_outer = i_outer + 1
        
    df_save_sort = df_save.sort_values(by=['Total GEE (ppm)'])
    
    if component == 'resp':
        df_save_subset_resp = df_save[['Station',  'Broad leaf forest (Resp)', 'Coniferous forest (Resp)', 'Mixed forest (Resp)', 'Other (Resp)',  'Grass and shrub (Resp)',  'Cropland (Resp)',  'Pasture (Resp)',  'Urban (Resp)', 'Respiration total', '(Respiration total (STILT))']]
        
        df_save_sort = df_save_subset_resp.sort_values(by=['Station'])
        df_save_sort_styled = df_save_sort.style.background_gradient(cmap = 'Reds', axis=None,subset = ['Broad leaf forest (Resp)', 'Coniferous forest (Resp)', 'Mixed forest (Resp)', 'Other (Resp)',  'Grass and shrub (Resp)',  'Cropland (Resp)',  'Pasture (Resp)',  'Urban (Resp)'])
        
    else:
        
        df_save_subset_gee = df_save[['Station',  'Broad leaf forest (GEE)', 'Coniferous forest (GEE)', 'Mixed forest (GEE)', 'Other (GEE)',  'Grass and shrub (GEE)',  'Cropland (GEE)',  'Pasture (GEE)',  'Urban (GEE)', 'GEE total', '(GEE total (STILT))']]
        
        df_save_sort = df_save_subset_gee.sort_values(by=['Station'])
        
        subset_style = subset = ['Broad leaf forest (GEE)', 'Coniferous forest (GEE)', 'Mixed forest (GEE)', 'Other (GEE)',  'Grass and shrub (GEE)',  'Cropland (GEE)',  'Pasture (GEE)',  'Urban (GEE)']
        subset_format = {key: "{:.2f}" for key in subset_style}
        subset_format['GEE total'] = '{:.2f}'
        subset_format['(GEE total (STILT))'] = '{:.2f}'

        df_save_sort_styled = df_save_sort.style.background_gradient(cmap = 'Greens', axis=None, subset = subset_style)\
                                          .format(subset_format)

    display(df_save_sort_styled)
    #df_save.to_csv(name_save + '.csv', index=False)
    
def footprint_show_percentages(footprint_code, input_footprint, fp_lat, fp_lon, return_fp=False):

    sum_sensitivity_values=sum(input_footprint.flatten()) 
    #create a dataframe that will have the updated sensitivity values + the steps on the way
    df_sensitivity = pd.DataFrame()

    #one column with the original senstivity values. Has an index that will be used to sort back to 
    #this order (flattened 2D... back to 2D with updated sensitivity values in last step)
    df_sensitivity['sensitivity']=input_footprint.flatten()
    
    #sensitivity values sorterd from largest to smallest
    df_sensitivity_sorted=df_sensitivity.sort_values(by=['sensitivity'], ascending=False)
    
    #another column that has the cumilated sum of the values in the sensitivity column.
    #used to determine when the footprint threshold is met. 
    df_sensitivity_sorted['cumsum_sens']=df_sensitivity_sorted.cumsum()
    
    #mask threshold: when the cumulative sum is over the threshold - these values are assigned 0.
    #to be multiplied with the original sensitivity values (disregard the ones with value 0)
    #df_sensitivity_sorted['ten_percent']=df_sensitivity_sorted['cumsum_sens']
    df_sensitivity_sorted['twenty_percent']=df_sensitivity_sorted['cumsum_sens']
    df_sensitivity_sorted['thirty_percent']=df_sensitivity_sorted['cumsum_sens']
    df_sensitivity_sorted['forty_percent']=df_sensitivity_sorted['cumsum_sens']
    df_sensitivity_sorted['fifty_percent']=df_sensitivity_sorted['cumsum_sens']
    
    
    ten_percent = sum_sensitivity_values*0.1
    twenty_percent = sum_sensitivity_values*0.2
    thirty_percent = sum_sensitivity_values*0.3
    forty_percent = sum_sensitivity_values*0.4
    fifty_percent = sum_sensitivity_values*0.5
    sixty_percent = sum_sensitivity_values*0.6
    seventy_percent = sum_sensitivity_values*0.7
    eighty_percent = sum_sensitivity_values*0.8
    ninty_percent = sum_sensitivity_values*0.9

    
    df_sensitivity_sorted['ten_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=ten_percent, 0, 1)
    df_sensitivity_sorted['twenty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=twenty_percent, 0, 1)
    df_sensitivity_sorted['thirty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=thirty_percent, 0, 1)
    df_sensitivity_sorted['forty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=forty_percent, 0, 1)
    df_sensitivity_sorted['fifty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=fifty_percent, 0, 1)  
    df_sensitivity_sorted['sixty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=sixty_percent, 0, 1)
    df_sensitivity_sorted['seventy_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=seventy_percent, 0, 1)
    df_sensitivity_sorted['eighty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=eighty_percent, 0, 1)
    df_sensitivity_sorted['ninty_percent']= np.where(df_sensitivity_sorted['cumsum_sens']>=ninty_percent, 0, 1)
    

    df_sensitivity_sorted['aggreg'] = df_sensitivity_sorted['ten_percent'] + df_sensitivity_sorted['twenty_percent']+df_sensitivity_sorted['thirty_percent']+df_sensitivity_sorted['forty_percent']+df_sensitivity_sorted['fifty_percent'] + df_sensitivity_sorted['sixty_percent'] + df_sensitivity_sorted['seventy_percent'] + df_sensitivity_sorted['eighty_percent'] + df_sensitivity_sorted['ninty_percent']
    
    df_sensitivity_sorted['aggreg']=df_sensitivity_sorted['aggreg']*10
    
    df_sensitivity_sorted['reversed_percent'] = 100 - df_sensitivity_sorted['aggreg']
    
    df_sensitivity_sorted['reversed_percent']= np.where(df_sensitivity_sorted['reversed_percent']>90, 0, df_sensitivity_sorted['reversed_percent'])
    
    df_sensitivity_upd=df_sensitivity_sorted.sort_index()
    
    list_aggreg_footprint=df_sensitivity_upd['reversed_percent'].tolist()

    footprint_0_90=np.array(list_aggreg_footprint).reshape((len(fp_lat), len(fp_lon)))
    
    if return_fp:
        return footprint_0_90
    
    else:
        plot_maps(footprint_0_90, fp_lon, fp_lat, colors='Blues_r', vmin=10, vmax=90, percent = True, unit='%', title=(footprint_code + ' 2018'))
    
def average_threshold_fp(station, date_range, threshold):
    
    pathFP='/data/stiltweb/stations/'
    
    nfp=0
    first = True
    
    # do for multiple seasons later
    for date in date_range:

        filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
             +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')
 
        if os.path.isfile(filename):
            f_fp = cdf.Dataset(filename)
            fp=f_fp.variables['foot'][:,:,:]
            fp_50 = update_footprint_based_on_threshold(fp, threshold)
            if (first):
                #fp=f_fp.variables['foot'][:,:,:]
                average_fp = fp_50
                first = False
            else:
                average_fp = average_fp + fp_50 
            f_fp.close()
            nfp+=1
    if nfp>1:
        
        average_fp=average_fp/nfp
            
        return average_fp
    else:
        return None
    
def countour_map_summer_winter(stc,pngfile = ''):   
    
    station = stc['specificStation']
    station_lat = stc['specificStationLat'] 
    station_lon = stc['specificStationLon'] 
    station_name = stc['specificStationName'] 
    
    threshold = 0.5
    smooth = 8
    percent = 80
    
    # colors for the countour lines
    contour_colors = ['green', 'black']

    # names of the seasons for map legend
    seasons = ['Summer', 'Winter']

    date_range_summer_whole = pd.date_range(dt.datetime(stc['startYear'],6,1,0), (dt.datetime(stc['startYear'], 9, 1,0)-dt.timedelta(hours=3)), freq='3H')
    
    date_range_summer = [date for date in date_range_summer_whole if date.hour in stc['timeOfDay']]
    
    date_range_winter_whole = pd.date_range(start=pd.Timestamp(stc['startYear'], 1, 1, 0), end=pd.Timestamp(stc['startYear'], 3, 1, 0) -dt.timedelta(hours=3), freq='3H').to_list() + pd.date_range(start=pd.Timestamp(stc['startYear'], 12, 1, 0), end=pd.Timestamp(stc['startYear'], 12, 31, 21), freq='3H').to_list() 
    
    date_range_winter = [date for date in date_range_winter_whole if date.hour in stc['timeOfDay']]

    average_fp_summer = average_threshold_fp(station, date_range_summer, threshold)
    
    average_fp_winter = average_threshold_fp(station, date_range_winter, threshold)
 
    list_fp = [average_fp_summer, average_fp_winter]

    title = ''

    # rather than returning this - plot the contours:    
    matplotlib.rcParams.update({'font.size': 12})
    first = True

    alpha = 0.7    

    # zoom in over area around station:
    ix,jy = lonlat_2_ixjy(station_lon,station_lat,load_lon,load_lat)

    # need to keep this ratio between x_change and y_change
    x_change = 100
    y_change = 120
    # define zoom area 
    i1 = np.max([ix-x_change,0])
    i2 = np.min([ix+x_change,400])
    j1 = np.max([jy-y_change,0])
    j2 = np.min([jy+y_change,480])

    lon_z=load_lon[i1:i2]
    lat_z=load_lat[j1:j2]

    index = 0

    for fp in list_fp:
        
    #for date_range in list_date_ranges:
        contour_color = contour_colors[index]
        season = seasons[index]
        
        if fp is None:
            print('Missing footprints for ' + season + ' ' + str(stc['startYear']))

        # update here
        #sum_sensitivity_values=sum(input_footprint.flatten()) 
        #cutoff = sum_sensitivity_values * 0.5
        #fp_reduced = np.where(fp_percentages>percent, 0, fp_percentages) 

        fp_percentages = footprint_show_percentages(station, fp, load_lat, load_lon, return_fp=True)

        # percent is where we'd like to have the cut-off
        fp_precentages_reduced = np.where(fp_percentages>percent, 0, fp_percentages) 

        # want only the cells that are zoomed in over:
        fp_precentages_reduced_z=fp_precentages_reduced[j1:j2,i1:i2]

        if first:

            # Create a feature for Countries at 1:50m from Natural Earth
            countries = cfeature.NaturalEarthFeature(
                category='cultural',
                name='admin_0_countries',
                scale='50m',
                facecolor='none')

            fig = plt.figure(figsize=(18,10))

            # set up a map
            ax = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())

            # set up a map
            img_extent = (lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max())
            ax.set_extent([lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()],crs=ccrs.PlateCarree())

            # add mock-lines for legend (they will not show up, VERY short). legend items cannot be added for countour
            ax.plot([9.111, 59.111], [9.112, 59.112], '-', linewidth=2, color=contour_color)

            ax.add_feature(countries, edgecolor='grey', linewidth=0.5)

            ax.add_feature(cfeature.OCEAN)


            # how many points to skip over every like being drawn is given by variable "smooth"
            ax.contour(fp_precentages_reduced_z[::smooth,::smooth], levels = [percent], alpha=alpha,colors=contour_color, origin='lower', extent=img_extent, vmax=50, antialiased=True)

            plt.title(title)

            first = False

        else:
            # when addding more than one contour line.
            ax.contour(fp_precentages_reduced_z[::smooth,::smooth], levels = [percent], alpha=alpha,colors=contour_color, origin='lower', extent=img_extent, vmax=50, antialiased=True)
        ax.plot([9.111, 59.111], [9.112, 59.112], '-', label=season, linewidth=2, color=contour_color)
        index = index + 1

    #show station location 
    ax.plot(station_lon,station_lat,'+',color='Blue',ms=5,transform=ccrs.PlateCarree(), label = station_name)

    ax.legend(loc='lower right', fontsize='medium')

    plt.show()


    if len(pngfile)>0:

        output = 'output_plot_percent_footprint_contour'

        if not os.path.exists(output):
            os.makedirs(output)

        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')

def land_cover_bar_graph_winter_summer(stc, pngfile=''): 
    
    station = stc['specificStation']
    station_lat = stc['specificStationLat'] 
    station_lon = stc['specificStationLon'] 
    station_name = stc['specificStationName'] 

    date_range1_whole = pd.date_range(dt.datetime(stc['startYear'],6,1,0), (dt.datetime(stc['startYear'], 9, 1,0)-dt.timedelta(hours=3)), freq='3H')
    
    date_range1 = [date for date in date_range1_whole if date.hour in stc['timeOfDay']]
    
    date_range2_whole = pd.date_range(start=pd.Timestamp(stc['startYear'], 1, 1, 0), end=pd.Timestamp(stc['startYear'], 3, 1, 0) -dt.timedelta(hours=3), freq='3H').to_list() + pd.date_range(start=pd.Timestamp(stc['startYear'], 12, 1, 0), end=pd.Timestamp(stc['startYear'], 12, 31, 21), freq='3H').to_list() 
    
    date_range2 = [date for date in date_range2_whole if date.hour in stc['timeOfDay']]

    #saved distances and degrees for ICOS stations:
    df_w_distances=pd.read_csv("/data/project/stc/approved_stations_distances.csv")
    df_w_degrees=pd.read_csv("/data/project/stc/approved_stations_degrees.csv") 

    #if not saved distances to all 192000 cells, calculate it. 
    if station in df_w_degrees.keys().tolist():
        degrees=df_w_degrees[station]

    else:
        degrees=degrees_from_point_to_grid_cells(station_lat, station_lon, load_lat, load_lon)


    # take two date ranges for final graph
    nfp1, fp1, lon, lat, title_not_used = read_aggreg_footprints(station, date_range1)

    nfp2, fp2, lon, lat, title_not_used = read_aggreg_footprints(station, date_range2)

    #get all the land cover data from netcdfs 
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    #land cover classes (imported in the land cover section):
    broad_leaf_forest1=fp1*broad_leaf_forest
    coniferous_forest1=fp1*coniferous_forest
    mixed_forest1=fp1*mixed_forest
    ocean1=fp1*ocean
    other1=fp1*other
    grass_shrub1=fp1*grass_shrub
    cropland1=fp1*cropland
    pasture1=fp1*pasture
    urban1=fp1*urban
    unknown1=fp1*unknown

    broad_leaf_forest2=fp2*broad_leaf_forest
    coniferous_forest2=fp2*coniferous_forest
    mixed_forest2=fp2*mixed_forest
    ocean2=fp2*ocean
    other2=fp2*other
    grass_shrub2=fp2*grass_shrub
    cropland2=fp2*cropland
    pasture2=fp2*pasture
    urban2=fp2*urban
    unknown2=fp2*unknown

    #lists of these values
    broad_leaf_forest_values1 = [item for sublist in broad_leaf_forest1[0] for item in sublist]
    coniferous_forest_values1 = [item for sublist in coniferous_forest1[0] for item in sublist]
    mixed_forest_values1 = [item for sublist in mixed_forest1[0] for item in sublist]
    ocean_values1 = [item for sublist in ocean1[0] for item in sublist]
    other_values1 = [item for sublist in other1[0] for item in sublist]
    grass_shrub_values1 = [item for sublist in grass_shrub1[0] for item in sublist]
    cropland_values1 = [item for sublist in cropland1[0] for item in sublist]
    pasture_values1 = [item for sublist in pasture1[0] for item in sublist]
    urban_values1 = [item for sublist in urban1[0] for item in sublist]
    unknown_values1 = [item for sublist in unknown1[0] for item in sublist]

    broad_leaf_forest_values2 = [item for sublist in broad_leaf_forest2[0] for item in sublist]
    coniferous_forest_values2 = [item for sublist in coniferous_forest2[0] for item in sublist]
    mixed_forest_values2 = [item for sublist in mixed_forest2[0] for item in sublist]
    ocean_values2 = [item for sublist in ocean2[0] for item in sublist]
    other_values2 = [item for sublist in other2[0] for item in sublist]
    grass_shrub_values2 = [item for sublist in grass_shrub2[0] for item in sublist]
    cropland_values2 = [item for sublist in cropland2[0] for item in sublist]
    pasture_values2 = [item for sublist in pasture2[0] for item in sublist]
    urban_values2 = [item for sublist in urban2[0] for item in sublist]
    unknown_values2 = [item for sublist in unknown2[0] for item in sublist]



    #putting it into a dataframe: initially 192000 values (one per cell) for each of the aggregated land cover classes
    #into same dataframe - have the same coulmn heading. "landcover_type" will be used in "groupby" together with the "slice" (in degrees)
    df_broad_leaf_forest1 = pd.DataFrame({'landcover_vals': broad_leaf_forest_values1,
                               'degrees': degrees,
                               'landcover_type':'Broad leaf forest'})

    df_coniferous_forest1 = pd.DataFrame({'landcover_vals': coniferous_forest_values1,
                           'degrees': degrees,
                           'landcover_type':'Coniferous forest'})

    df_mixed_forest1 = pd.DataFrame({'landcover_vals': mixed_forest_values1,
                           'degrees': degrees,
                           'landcover_type':'Mixed forest'})

    df_ocean1 = pd.DataFrame({'landcover_vals': ocean_values1,
                           'degrees': degrees,
                           'landcover_type':'Ocean'})

    df_other1 = pd.DataFrame({'landcover_vals': other_values1,
                           'degrees': degrees,
                           'landcover_type':'Other'})

    df_grass_shrub1 = pd.DataFrame({'landcover_vals':  grass_shrub_values1,
                           'degrees': degrees,
                           'landcover_type':'Grass/shrubland'})

    df_cropland1 = pd.DataFrame({'landcover_vals':  cropland_values1,
                           'degrees': degrees,
                           'landcover_type':'Cropland'})

    df_pasture1 = pd.DataFrame({'landcover_vals': pasture_values1,
                           'degrees': degrees,
                           'landcover_type':'Pasture'})

    df_urban1 = pd.DataFrame({'landcover_vals':  urban_values1,
                           'degrees': degrees,
                           'landcover_type':'Urban'})

    df_unknown1 = pd.DataFrame({'landcover_vals':  unknown_values1,
                           'degrees': degrees,
                           'landcover_type':'Unknown'})


    df_broad_leaf_forest2 = pd.DataFrame({'landcover_vals': broad_leaf_forest_values2,
                               'degrees': degrees,
                               'landcover_type':'Broad leaf forest'})

    df_coniferous_forest2 = pd.DataFrame({'landcover_vals': coniferous_forest_values2,
                           'degrees': degrees,
                           'landcover_type':'Coniferous forest'})

    df_mixed_forest2 = pd.DataFrame({'landcover_vals': mixed_forest_values2,
                           'degrees': degrees,
                           'landcover_type':'Mixed forest'})

    df_ocean2 = pd.DataFrame({'landcover_vals': ocean_values2,
                           'degrees': degrees,
                           'landcover_type':'Ocean'})

    df_other2 = pd.DataFrame({'landcover_vals': other_values2,
                           'degrees': degrees,
                           'landcover_type':'Other'})

    df_grass_shrub2 = pd.DataFrame({'landcover_vals':  grass_shrub_values2,
                           'degrees': degrees,
                           'landcover_type':'Grass/shrubland'})

    df_cropland2 = pd.DataFrame({'landcover_vals':  cropland_values2,
                           'degrees': degrees,
                           'landcover_type':'Cropland'})

    df_pasture2 = pd.DataFrame({'landcover_vals': pasture_values2,
                           'degrees': degrees,
                           'landcover_type':'Pasture'})

    df_urban2 = pd.DataFrame({'landcover_vals':  urban_values2,
                           'degrees': degrees,
                           'landcover_type':'Urban'})

    df_unknown2 = pd.DataFrame({'landcover_vals':  unknown_values2,
                           'degrees': degrees,
                           'landcover_type':'Unknown'})


    #into one dataframe
    df_all1 = df_cropland1.append([df_broad_leaf_forest1, df_coniferous_forest1, df_mixed_forest1, df_ocean1, df_other1, \
                                   df_grass_shrub1, df_pasture1, df_urban1, df_unknown1])

    df_all2 = df_cropland2.append([df_broad_leaf_forest2, df_coniferous_forest2, df_mixed_forest2, df_ocean2, df_other2, \
                                   df_grass_shrub2, df_pasture2, df_urban2, df_unknown2])

    #not change with user input
    dir_bins = np.arange(22.5, 383.5, 45)
    dir_bins= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5,383.5])
    dir_labels= np.asarray([0, 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5])

    #get columns - for each degree
    rosedata1=df_all1.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    rosedata1=rosedata1.replace({'Degree_bins': {0.0: 337.5}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata1=rosedata1.groupby(by=['landcover_type', 'Degree_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata1=rosedata1.unstack(level='landcover_type')

    #want to sort the dataframe so that the land cover the station is the most
    #sensitive to is first. 
    rosedata_sum1=rosedata1.sum() 
    rosedata_sum_sorted1=rosedata_sum1.sort_values(ascending=False)

    # order of this list to sort bort the result from date range 1 and date range 2. 
    list_land_cover_names_sorted=list(rosedata_sum_sorted1.index)
    rosedata1=rosedata1[list_land_cover_names_sorted]


    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    total_all1=sum(rosedata_sum1)

    rosedata1= rosedata1.applymap(lambda x: x / total_all1 * 100)

    #get columns - for each degree
    rosedata2=df_all2.assign(Degree_bins=lambda df: pd.cut(df['degrees'], bins=dir_bins, labels=dir_labels, right=False))

    rosedata2=rosedata2.replace({'Degree_bins': {0.0: 337.5}})

    #group the data by the distance bins, and again by the direction bins. The value to be summed in the sensitivity values.
    rosedata2=rosedata2.groupby(by=['landcover_type', 'Degree_bins'])['landcover_vals'].sum()

    #changes the format:
    rosedata2=rosedata2.unstack(level='landcover_type')

    rosedata_sum2=rosedata2.sum() 
    # want to sort it in the same way for both date ranges (largest to smallest given first date range)
    rosedata2=rosedata2[list_land_cover_names_sorted]    

    #for all values: want the % of the total sensitivity (one value for each distance for each direction)
    total_all2=sum(rosedata_sum2)

    rosedata2= rosedata2.applymap(lambda x: x / total_all2 * 100)

    # into list of arrays.
    # want each array to be the 16 values (8 directions x2 for the results from thee two date ranges) 
    # for one land cover type to be displayed in a stacked bar
    # there will be one array per land cover type (10)
    list_land_cover_values=[]
    for land_cover_type in list_land_cover_names_sorted:

        list_date_range1 = rosedata1[land_cover_type].values
        list_date_range2 = rosedata2[land_cover_type].values

        # every second value should be from the 1st date range (summer for instance)
        # and every other value should be from the 2nd date range (winter for instance)
        aggreg_list = []
        for value_date_range1, value_date_range2 in zip(list_date_range1, list_date_range2):
            aggreg_list.append(value_date_range1)
            aggreg_list.append(value_date_range2)

        list_land_cover_values.append(np.array(aggreg_list))

    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(11,13)) 
    ax = fig.add_subplot(1,1,1)

    # space it in a way summer and winter are close.
    ind = np.array([ 0,  0.5,  2,  2.5,  4,  4.5,  6,  6.5,  8,  8.5, 10, 10.5, 12, 12.5, 14, 14.5])

    width = 0.35       

    # p1 is the first land cover type (with largest share for date range 1).
    # the remaining (9) land cover classes are stacked on top (with the below - "bottom" - land cover types under)
    p1 = ax.bar(ind, list_land_cover_values[0], width, color=dictionary_color[list_land_cover_names_sorted[0]]['color'], edgecolor='black')

    p2 = ax.bar(ind, list_land_cover_values[1], width, color=dictionary_color[list_land_cover_names_sorted[1]]['color'],edgecolor='black',
                 bottom=list_land_cover_values[0])
    p3 = ax.bar(ind, list_land_cover_values[2], width, color=dictionary_color[list_land_cover_names_sorted[2]]['color'], edgecolor='black',
                 bottom=list_land_cover_values[0]+list_land_cover_values[1])
    p4 = ax.bar(ind, list_land_cover_values[3], width, color=dictionary_color[list_land_cover_names_sorted[3]]['color'], edgecolor='black',
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2])
    p5 = ax.bar(ind, list_land_cover_values[4], width, color=dictionary_color[list_land_cover_names_sorted[4]]['color'], edgecolor='black',
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3])
    p6 = ax.bar(ind, list_land_cover_values[5], width, color=dictionary_color[list_land_cover_names_sorted[5]]['color'], edgecolor='black',
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4])
    p7 = ax.bar(ind, list_land_cover_values[6], width, color=dictionary_color[list_land_cover_names_sorted[6]]['color'], edgecolor='black',
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5])

    p8 = ax.bar(ind, list_land_cover_values[7], width, color=dictionary_color[list_land_cover_names_sorted[7]]['color'], edgecolor='black', 
                bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6])

    p9 = ax.bar(ind, list_land_cover_values[8], width, color=dictionary_color[list_land_cover_names_sorted[8]]['color'], edgecolor='black', \
                bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6]+list_land_cover_values[7])

    p10 = ax.bar(ind, list_land_cover_values[9], width, color=dictionary_color[list_land_cover_names_sorted[9]]['color'], edgecolor='black', \
                 bottom=list_land_cover_values[0]+list_land_cover_values[1]+list_land_cover_values[2]+list_land_cover_values[3]+\
                 list_land_cover_values[4]+list_land_cover_values[5]+list_land_cover_values[6]+ list_land_cover_values[7]+list_land_cover_values[8])

    #want to reverese the order (ex if oceans at the "bottom" in the graph - ocean label should be furthest down)
    handles=(p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p8[0], p9[0])

    index=0
    list_labels=[]
    for land_cover_name in list_land_cover_names_sorted:

        # date ramge 1 and 2 (summer and winter), sum every second (how the data is stored - 16 (8 directions x2) 
        # to get the total % in all directions (which is displayed in the legend)
        for_lable= (land_cover_name + ' (' + str("%.0f" % sum(list_land_cover_values[index][::2])) + ', ' + str("%.0f" % sum(list_land_cover_values[index][1::2])) +')')
        if not land_cover_name == 'Unknown':
        
            list_labels.append(for_lable)
        index=index+1

    labels=[textwrap.fill(text,25) for text in list_labels]

    #other way - smallest in legend up top which is how 
    plt.legend(handles[::-1], labels[::-1],bbox_to_anchor=(1, 0.56), title = "     Summer (%), Winter (%)")

    plt.ylabel('%')

    #first one is not north (in rosedata - rather 22.5 to 67.5 (NE).
    # two values (date range 1 and 2) for each direction
    plt.xticks(ind, ('N', 'E','   E','','S','E', '   S',  '', 'S','W','   W', '','N', 'W','   N',''))
    ax.yaxis.grid(True)

    fig.set_size_inches(11, 13)
    
    plt.show()
    if len(pngfile)>0:
        
        output = 'output_summer_winter_landcover_breakdown'

        if not os.path.exists(output):
            os.makedirs(output)
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')

def representation_within_country(nwc, station, countries):
    
    date_range_original = pd.date_range(dt.datetime(nwc['startYear'],nwc['startMonth'],nwc['startDay'],0), (dt.datetime(nwc['endYear'], nwc['endMonth'], nwc['endDay'], 21)), freq='3H')
    date_range= [date for date in date_range_original if date.hour in nwc['timeOfDay']]

    # grid area (m2) of each cell:
    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')
    gridarea = f_gridarea.variables['cell_area'][:]/1000000

    # access the flux data
    filename_resp = check_cp(path_cp,'VPRM_ECMWF_RESP_2020_CP.nc')

    filename_gee = check_cp(path_cp,'VPRM_ECMWF_GEE_2020_CP.nc')

    f_resp = cdf.Dataset(filename_resp)

    f_gee = cdf.Dataset(filename_gee)

    # same for both datasets
    times = f_resp.variables['time']

    # access HILDA land cover data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    list_classes_names = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    list_classes_km2 = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown]

    # want vegetation fraction HILDA land cover maps (as opposed to km2 for the entire cell - "list_classes_km2")
    list_classes = []

    for landcover in list_classes_km2:

        landcover_fraction = landcover/gridarea

        list_classes.append(landcover_fraction)

    # what columns to have in the resulting dataframe depend on selection of countries.
    # here create a loop that creates file names.
    # order here is essential. The same order will be kept in the loop that creates and finally sets the data into 
    # this dataframe
    columns_save= ['date', 'total_resp', 'total_gee', 'broad_leaf_forest_resp','broad_leaf_forest_gee', 'coniferous_forest_resp',\
                   'coniferous_forest_gee', 'mixed_forest_resp','mixed_forest_gee', 'ocean_resp', 'ocean_gee', 'other_resp', 'other_gee',
                   'grass_shrub_resp', 'grass_shrub_gee', 'cropland_resp', 'cropland_gee',\
                   'pasture_resp','pasture_gee', 'urban_resp','urban_gee', 'unknown_resp', 'unknown_gee']

    list_for_columns = ['total_country', 'broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']
    for country in countries:

        for column in list_for_columns:
            columns_save.append(country + '_' + column + '_resp')
            columns_save.append(country + '_' + column + '_gee')

    df_save_individual = pd.DataFrame(columns=columns_save)

    # counter to place the data in a new row for each date
    i = 0
    for date in date_range:

        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)

        ntime = date2index(date,times,select='nearest')

        resp = f_resp.variables['RESP'][ntime][:][:]
        gee = f_gee.variables['GEE'][ntime][:][:]

        # footprint for specific date
        filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'+str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

        if os.path.isfile(filename):

            f_fp = cdf.Dataset(filename)

            fp=f_fp.variables['foot'][:,:,:]

            fp_resp = fp * resp
            fp_gee = fp * gee

            # added for individual station - interested in how much is sensed within border
            fp_resp_total = fp_resp.sum()
            fp_gee_total = fp_gee.sum()

            # the list "data_specific_date" will be filled with data for all the columns for this specific date
            # added to the dataframe when the country loop is done (load data for all selected countries), and the 
            # loop over land cover classes which is started once for each country (sensing of broad leaf forest
            # for specific country for specific day)
            data_specific_date = [date_string, fp_resp_total, fp_gee_total]

            for landcover_hilda, landcover_name in zip(list_classes, list_classes_names):

                    total_resp_landcover = (fp_resp * landcover_hilda).sum()
                    total_gee_landcover = (fp_gee * landcover_hilda).sum()

                    #total_resp_landcover_country, total_gee_landcover_country,\
                                    # total_resp_country_landcover_even,total_gee_country_landcover_even
                    data_specific_date.extend([total_resp_landcover, total_gee_landcover])  


            for country_code in countries:


                if country_code == "Europe":
                    country_mask = return_europe_mask()

                else:
                    country_mask = country_masks.variables[country_code][:,:]

                # this is what is interesting. compare to total flux sensed at station
                total_resp_country = (fp_resp * country_mask).sum()
                total_gee_country = (fp_gee * country_mask).sum()

                percent_resp_country = (total_resp_country/fp_resp_total) * 100 
                percent_gee_country = (total_gee_country/fp_gee_total) * 100

                data_specific_date.extend([total_resp_country, total_gee_country])

                for landcover_hilda, landcover_name in zip(list_classes, list_classes_names):

                    total_resp_landcover_country = (fp_resp * country_mask * landcover_hilda).sum()
                    total_gee_landcover_country = (fp_gee * country_mask * landcover_hilda).sum()

                    data_specific_date.extend([total_resp_landcover_country, total_gee_landcover_country])  

            df_save_individual.loc[i] = data_specific_date
            i = i + 1
    
    pd.set_option('display.float_format', lambda x: '%.1f' % x)

    output_df = pd.DataFrame()

    output_df['landcover'] = ['Total GEE', 'Broad leaf forest GEE', \
                              'Coniferous forest GEE', 'Mixed forest GEE',\
                              'Other GEE', 'Grass and Shrub GEE',\
                             'Cropland GEE', 'Pasture GEE',\
                              'Urban GEE']

    country_columns_gee = []
    country_columns_resp = []
    for column in df_save_individual:
  
        column_list = column.split("_")   

        if 'gee' in column and 'ocean' not in column and 'unknown' not in column:
            country_columns_gee.append(column)

            if column_list[0]=='total':

                total_column = column


        if 'resp' in column:
            country_columns_resp.append(column) 

            if column_list[0]=='total':

                total_column = column


    #display as table!
    df_subset_gee = abs(df_save_individual[country_columns_gee])
    df_subset_resp = df_save_individual[country_columns_resp]

    df_subset_gee_mean = df_subset_gee.mean()
    df_subset_resp_mean = df_subset_resp.mean()

    df_subset_gee_columns = df_subset_gee_mean.index.to_list()

    values_total = df_subset_gee_mean[0:9]

    value_total = values_total[0]

    percent_total = [((value_landcover/value_total)*100) for value_landcover in values_total[1:]]

    output_df['Total'] = [np.nan] + percent_total


    for country in countries:

        index = 0

        first = True

        for column in df_subset_gee_columns: 


            column_list = column.split("_")
            if first: 
                if column_list[0] == country:

                    values_specific_country = df_subset_gee_mean[index:index+9]

                    value_total_specific_country = values_specific_country[0]

                    percent_specific_country = [((value_landcover/value_total_specific_country)*100) for value_landcover in values_specific_country[1:]]

                    total_country = (value_total_specific_country/value_total)*100
                    output_df[country + (' (%)')] = [total_country] + percent_specific_country

                    index = index + 11

                    first = False

            index = index + 1


    display(output_df)

    
    return df_save_individual

