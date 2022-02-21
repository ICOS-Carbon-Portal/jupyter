# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 09:47:58 2020

@author: Ida Storm
"""
import pandas as pd
import os
import netCDF4 as cdf
import numpy as np
import cartopy
cartopy.config['data_dir'] = '/data/project/cartopy/'
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import six
from numpy import loadtxt
from netCDF4 import Dataset
import math
from ipywidgets import Output, HBox
from IPython.core.display import HTML 
from datetime import date
from bokeh.transform import factor_cmap

#for bokeh
from bokeh.io import show, output_notebook, reset_output
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, FactorRange, Legend

from datetime import datetime
from matplotlib.colors import LogNorm
import json

reset_output()
output_notebook()


folder_tool_fps = '/data/project/stc/footprints_2018_averaged'

#added 
folder_data = '/data/project/stc/'

dictionary_area_choice = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium', 'BIH':'Bosnia and Herzegovina', 'BGR':'Bulgaria', 'HRV':'Croatia','CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LIE':'Liechtenstein','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta','MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SMR':'San Marino','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}

country_masks = Dataset(os.path.join(folder_data,'europe_STILT_masks.nc'))
country_masks_eez_included = Dataset(os.path.join(folder_data,'europe_STILT_masks_eez_included.nc'))

#function to read and aggregate footprints for given date range
def read_aggreg_footprints(station, date_range):
    
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
          
    #consider return timeselect
    return date_range

def save_settings(settings, directory):

    output = os.path.join(os.path.expanduser('~'), 'output', directory, date_time)

    if not os.path.exists(output):
        os.makedirs(output)

    export_file=output + '/settings.json'

    # save settings as json file
    with open(export_file, 'w') as f:
        json.dump(settings, f, indent=4)

def import_landcover_HILDA(year='2018'):
    
    name_data = 'hilda_lulc_'+ year +'.nc' 
    
    all_hilda_classes= Dataset(folder_data + name_data)

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

    pop_data= Dataset(os.path.join(folder_data, 'GEOSTAT_population_2011_2018.nc'))
    
    fp_pop=pop_data.variables['2018'][:,:]
    return fp_pop

# function to convert station longitude and latitude (slat, slon) to indices of STILT model grid (ix,jy)
def lonlat_2_ixjy(slon,slat,mlon,mlat):
    #slon, slat: longitude and latitude of station
    #mlon, mlat: 1-dim. longitude and latitude of model grid
    ix = (np.abs(mlon-slon)).argmin()
    jy = (np.abs(mlat-slat)).argmin()
    return ix,jy

# footprint_show_percentages() is used to with argument percent=True to generate an aggregated % sensitivity map. 
def plot_maps(field, lon, lat, title='', label='', unit='', linlog='linear', station='', zoom='', 
              vmin=None, vmax=None, colors='GnBu',pngfile='', directory='figures', mask=False, percent=False, date_time_predefined=''): 

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
        
        im = ax.imshow(field[:,:], interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=0.00001,vmax=vmax)
        cs = ax.imshow(field[:,:], origin='lower', extent=img_extent,cmap=cmap,vmin=0.000001,vmax=vmax)
        
        if percent:

            ticks = [10,20,30,40,50,60,70,80,90,100]
            
            ticklabels = [' ', 10, 20, 30, 40, 50, 60, 70, 80, 90]
            
            vmin =10
            
            norm = matplotlib.colors.BoundaryNorm(ticks, cmap.N, extend='both')
            
            im = ax.imshow(field[:,:], norm=norm, interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            
            cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='neither', format='%.0f', ticks=ticks)

            cbar.locator = matplotlib.ticker.FixedLocator(ticks)
            
            cbar.update_ticks()
            
            cbar.ax.set_xticklabels(ticklabels) 
            
            cbar.set_label(label+'  '+unit)
            
        else:
            cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        
            cbar.ax.minorticks_off()

            cbar.set_label(label+unit)
       
    else:

        cs = ax.imshow(field[:,:],norm=LogNorm(), origin='lower', extent=img_extent,cmap=cmap,vmin=0.000001,vmax=vmax)

        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        
        cbar.ax.minorticks_off()

        cbar.set_label(label+unit)
    
    plt.title(title)
    
    #show station location if station is provided
    if station != '':
        station_lon=[]
        station_lat=[]
        station_lon.append(stations[station]['lon'])
        station_lat.append(stations[station]['lat'])
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        
    #zoom=str(zoom)
  
    plt.show()
   
    if len(pngfile)>0:
 
        if percent:
            #date_time defined globally for the else option
            output = os.path.join(os.path.expanduser('~'), 'output/vis_average_footprints', date_time_predefined)
        else:

            try:
                output = os.path.join(os.path.expanduser('~'), 'output', directory, date_time)
            except:
                output = os.path.join(os.path.expanduser('~'), 'output', directory, date_time_predefined)


        if not os.path.exists(output):
            os.makedirs(output)
  
        print(output)
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
    if percent:
        
        return plt

def update_footprint_based_on_threshold(input_footprint, fp_lat, fp_lon, threshold):

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
    
    #mask*sensitivity = for "new" footprint that only has sensitivity values in the cells that have the value 1.
    df_sensitivity_sorted['mask_sensitivity']=df_sensitivity_sorted['mask_threshold']*df_sensitivity_sorted['sensitivity']

    #sort it back (so in correct lat/lon order for "packing back up" to 2D)
    df_sensitivity_upd=df_sensitivity_sorted.sort_index()

    list_updated_sensitivity=df_sensitivity_upd['mask_sensitivity'].tolist()
    
    upd_footprint_sens=np.array(list_updated_sensitivity).reshape((len(fp_lat), len(fp_lon)))

    #want a footprint with 0/1 for see or not see also 
    list_mask_threshold=df_sensitivity_upd['mask_threshold'].tolist()

    upd_footprint_see_not_see=np.array(list_mask_threshold).reshape((len(fp_lat), len(fp_lon)))

    return upd_footprint_sens, upd_footprint_see_not_see

def load_fp(station):
    
    name_load_footprint_csv='fp_' + station + '.csv'
    
    if os.path.isfile(os.path.join(folder_tool_fps, name_load_footprint_csv)):
        loaded_fp=loadtxt(os.path.join(folder_tool_fps, name_load_footprint_csv), delimiter=',')
    else:

        loaded_fp = None

    return loaded_fp

def return_networks(networkObj):
    now = datetime.now()
    global date_time
    date_time = now.strftime("%Y%m%d_%H%M%S")
    
    sites_base_network = networkObj.settings['baseNetwork']
    sites_compare_network = networkObj.settings['compareNetwork']
    threshold_value = int(networkObj.settings['percent'])
    threshold = threshold_value/100
    date_range = networkObj.dateRange
    hours = networkObj.settings['timeOfDay']
    load_lat=networkObj.loadLat
    load_lon=networkObj.loadLon
    
    df_footprints_network = pd.DataFrame()

    index=1

    list_none_footprints = []
    
    for station in sites_base_network:

        #if use 2018 aggregated footprint
        if pd.Timestamp(min(date_range))==pd.Timestamp(2018, 1, 1, 0) and pd.Timestamp(max(date_range))==pd.Timestamp(2018,12,31,0) and len(hours)==8:

            loaded_fp=load_fp(station)
            
            #might just not be pre-computed 2018 footprint
            if loaded_fp is None:

                nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
                #if still None, then add to list of sites with no footprints and continue
                if loaded_fp is None:

                    list_none_footprints.append(station)
                    
        else:

            nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)

            if loaded_fp is None:

                list_none_footprints.append(station)

                continue

        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        df_footprints_network[('fp_' + str(index))]=upd_fp_sens.flatten()
        
        #for new column values
        index=index+1
    
    # make a footprint based on all max values of the combined footprints. 
    df_max_base_network = df_footprints_network[df_footprints_network.columns].max(axis=1)

    #in case of no available footprints for any of the selections. 
    if len(df_max_base_network.tolist()) == 0:
        
        fp_max_base_network= None  
        fp_max_compare_network= None 
        
        return fp_max_base_network, fp_max_compare_network, list_none_footprints
    
    else:
        
        # will only happen in case of available footprints for >0 sites
        fp_max_base_network=np.array(df_max_base_network.tolist()).reshape((len(load_lat), len(load_lon)))
    
        # if no base network to add to, there will be no compare network either 
        if len(sites_compare_network) == 0:

            return fp_max_base_network, None, list_none_footprints, date_time

        for station in sites_compare_network:

            #if use 2018 aggregated footprint
            if pd.Timestamp(min(date_range))==pd.Timestamp(2018, 1, 1, 0) and pd.Timestamp(max(date_range))==pd.Timestamp(2018,12,31,0) and len(hours)==8:

                loaded_fp=load_fp(station)

                #might just not be pre-computed 2018 footprint
                if loaded_fp is None:

                    nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
                    
                    #if still None, then add to list of sites with no footprints and continue
                    if loaded_fp is None:

                        list_none_footprints.append(station)

            else:

                nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
                
                if loaded_fp is None:

                    list_none_footprints.append(station)

                    continue

            upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)

            df_footprints_network[('fp_' + str(index))]= upd_fp_sens.flatten()

            #for new column values
            index=index+1

        # make a footprint based on all max values of the combined footprints. 
        df_max_compare_network = df_footprints_network[df_footprints_network.columns].max(axis=1)

        fp_max_compare_network=np.array(df_max_compare_network.tolist()).reshape((len(load_lat), len(load_lon)))

        if fp_max_compare_network.sum() == fp_max_base_network.sum():
            fp_max_compare_network = None

        return fp_max_base_network, fp_max_compare_network, list_none_footprints, date_time
    

def country_dict_landcover(networkObj):
    
    base_network =  networkObj.baseNetwork
    
    total_sens_base_network = base_network.sum()
    
    compare_network = networkObj.compareNetwork
    
    fp_pop = import_population_data()
    
    if compare_network is not None: 
        total_sens_compare_network = compare_network.sum()
    
    f_gridarea = cdf.Dataset(os.path.join(folder_data, 'gridareaSTILT.nc'))
    gridarea = f_gridarea.variables['cell_area'][:]
    
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018') 
    
    list_land_cover_classes = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean, grass_shrub, other, unknown]
    
    land_cover_names = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
    
    all_countries = ["ALB","Andorra","AUT", "BLR","BEL","BIH", "BGR","HRV","CYP","CZE","DNK","EST","FIN", "FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD","MTL", "MDA","MNE","NLD","NOR", "POL", "PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR"]
    
    dict_all_countries= {}
    
    for country_code in all_countries:
        
        dict_all_countries[country_code]={}
     
        dict_all_countries[country_code]['country_breakdown'] = {}
        
        dict_all_countries[country_code]['base_network_breakdown'] = {}
        
        country_mask = country_masks.variables[country_code][:,:]
        #area of country 
        country_area_grid = (gridarea*country_mask)/1000000
        country_area_total=country_area_grid.sum()
        dict_all_countries[country_code]['country_breakdown']['total area (km2)'] = country_area_total
        
        if compare_network is not None: 
            
            dict_all_countries[country_code]['compare_network_breakdown'] = {}
            
            country_compare_network_sens_total = (compare_network * country_mask).sum()
            
            dict_all_countries[country_code]['compare_network_breakdown']['total sens'] = country_compare_network_sens_total
            
            dict_all_countries[country_code]['compare_network_breakdown']['total sens/km2'] = country_compare_network_sens_total/country_area_total
     
            dict_all_countries[country_code]['compare_network_breakdown']['population sens'] = (country_mask * compare_network * fp_pop).sum()
            
      
        country_base_network_sens_total = (base_network * country_mask).sum()

        dict_all_countries[country_code]['base_network_breakdown']['total sens'] = country_base_network_sens_total

        dict_all_countries[country_code]['base_network_breakdown']['total sens/km2'] = country_base_network_sens_total/country_area_total
        
        dict_all_countries[country_code]['base_network_breakdown']['population sens'] = (country_mask * base_network * fp_pop).sum()
       
        for land_cover, land_cover_name in zip(list_land_cover_classes, land_cover_names):
        
            # country breakdown
            area_country_landcover = (land_cover*country_mask).sum()
            
            percent_country_breakdown = (area_country_landcover / country_area_total)*100 
            
            dict_all_countries[country_code]['country_breakdown'][land_cover_name]=percent_country_breakdown

            if compare_network is not None: 
                sens_country_landcover_compare = (country_mask * compare_network * land_cover).sum()
                
                dict_all_countries[country_code]['compare_network_breakdown'][land_cover_name+ ' total'] = sens_country_landcover_compare
                

            # base network breakdown
            
            sens_country_landcover_base = (country_mask * base_network * land_cover).sum()

            dict_all_countries[country_code]['base_network_breakdown'][land_cover_name + ' total']= sens_country_landcover_base

    return dict_all_countries
    
    
def leader_chart_sensitivity(networkObj):
    
    compare_network =  networkObj.compareNetwork
    
    all_countries = ["ALB","Andorra","AUT", "BLR","BEL","BIH", "BGR","HRV","CYP","CZE","DNK","EST","FIN", "FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD","MTL", "MDA","MNE","NLD","NOR", "POL", "PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR"]
    
    if compare_network is None:
        df_leader_chart_sens = pd.DataFrame(columns=['Country', 'Sensitivity/km2'])
        
    else:
        df_leader_chart_sens = pd.DataFrame(columns=['Country', 'Sens./km2 base', 'Sens./km2 compare', 'Increase (%)'])
    
    i = 0
    
    for country in all_countries:
        
        country_name = dictionary_area_choice[country]
        
        base_sens_km2 = networkObj.countryDict[country]['base_network_breakdown']['total sens/km2']
        
        if base_sens_km2>0 and compare_network is None:
            
            df_leader_chart_sens.loc[i] = [country_name, base_sens_km2]
            
            i = i + 1
        
        else: 
            
            if compare_network is not None:

                compare_sens_km2 = networkObj.countryDict[country]['compare_network_breakdown']['total sens/km2']

                if compare_sens_km2>0:

                    #diff_base_compare = compare_sens_km2 - base_sens_km2
                    diff_base_compare_percent = (((compare_sens_km2/base_sens_km2)*100)-100) 

                    df_leader_chart_sens.loc[i] = [country_name, base_sens_km2, compare_sens_km2, diff_base_compare_percent]

                    i = i + 1

  
    if compare_network is not None:
        
        df_leader_chart_sens = df_leader_chart_sens.sort_values(by=['Sens./km2 base'], ascending=False)

        styled_df_leader_chart_sens = (df_leader_chart_sens.style
                                              .format({'Sens./km2 base' : '{:.2E}', 'Sens./km2 compare': '{:.2E}', 'Increase (%)': '{:.0f}'})
                                              .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))
        
        styled_df_leader_chart_sens = styled_df_leader_chart_sens.set_properties(**{'text-align': 'center'}).hide_index()


    else:

        df_leader_chart_sens = df_leader_chart_sens.sort_values(by=['Sensitivity/km2'], ascending=False)
        
        styled_df_leader_chart_sens = (df_leader_chart_sens.style
                                              .format({'Sensitivity/km2' : '{:.2E}'})
                                              .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

        styled_df_leader_chart_sens = styled_df_leader_chart_sens.set_properties(**{'text-align': 'center'}).hide_index()

    return styled_df_leader_chart_sens, df_leader_chart_sens

def population_bar_graph_base(networkObj):
    
    base_network = networkObj.baseNetwork    
    countries = networkObj.settings['countries']
    dictionary = networkObj.countryDict
    
    population_sensitivity_list = []
    
    country_names = []
    
    for country in countries: 
        
        country_name = dictionary_area_choice[country]
          
        if dictionary[country]['base_network_breakdown']['population sens']>0:
        
            population = dictionary[country]['base_network_breakdown']['population sens']
            
            population_sensitivity_list.append(population)
            
            country_names.append(country_name)
        
    dictionary_population_by_country = {'Countries': country_names, 'Population': population_sensitivity_list}

    p = figure(x_range= country_names, title='Sensitivities of network to country populations', toolbar_location="below", tooltips="@Population{0f}", width=800, height=350)

    p.vbar(x='Countries', top = 'Population', width=0.5, color='Darkblue', source = dictionary_population_by_country)

    p.yaxis.axis_label = 'population * (ppm /(μmol / (m²s)))'
    
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.label_text_font_size = "10px"
    p.xaxis.major_label_orientation = "vertical"

    output_population_by_country = Output()

    with output_population_by_country:

        output_population_by_country.clear_output()
        
        if len(country_names)>1:

            show(p)

    display(output_population_by_country)
    
def population_bar_graph_compare(networkObj):
    
    base_network = networkObj.baseNetwork    
    compare_network = networkObj.compareNetwork
    countries = networkObj.settings['countries']
    dictionary = networkObj.countryDict
    
    base_network = []
    
    compare_minus_base_for_stack = []
    
    country_names = []
    
    df_diff_base_compare = pd.DataFrame()
    
    change_base_compare_percent = []
    
    for country in countries: 
        
        country_name = dictionary_area_choice[country]
          
        if dictionary[country]['base_network_breakdown']['population sens']>0:
        
            population_base = dictionary[country]['base_network_breakdown']['population sens']
            
            base_network.append(population_base)
            
            country_names.append(country_name)
            
        else:
            
            if networkObj.countryDict[country]['compare_network_breakdown']['population sens']>0:
                
                population_base = 0
                
                base_network.append(population_base)
                
                country_names.append(country_name)
              
        if networkObj.countryDict[country]['compare_network_breakdown']['total sens']>0:
            
            population_compare = dictionary[country]['compare_network_breakdown']['population sens']
            
            compare_minus_base = population_compare - population_base
            
            compare_minus_base_for_stack.append(compare_minus_base)
            
            if population_base > 0:
                
                change_percent = ((population_compare / population_base)*100 - 100)
            
            elif population_compare > 0:
                
                change_percent = 99999
                
            else:
                change_percent = 0 

            change_base_compare_percent.append(change_percent)
    
    # table showing difference between base and compare       
    df_diff_base_compare['Increase sensitivity (%)'] = change_base_compare_percent
    
    output_population_table = Output()
    
    with output_population_table:

        output_population_table.clear_output()

        df_diff_base_compare = df_diff_base_compare.astype(float)

        df_diff_base_compare.insert(0, 'Country', country_names)

        styled_df_diff_base_compare = (df_diff_base_compare.style
                                      .format({'Increase sensitivity (%)': '{:.0f}'})
                                      .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

        styled_df_diff_base_compare = styled_df_diff_base_compare.set_properties(**{'text-align': 'center'}).hide_index()

        display(styled_df_diff_base_compare)  

    dictionary_sensitivity_population_by_country = {'Countries': country_names,
                     'Base': base_network,
                     'Compare (added)': compare_minus_base_for_stack}
    
    p = figure(x_range=country_names, title='Sensitivities of networks to country populations', toolbar_location="below", tooltips="$name : @$name{0f}")

    p.vbar_stack(['Base', 'Compare (added)'], x='Countries', width=0.5, color=['Darkblue', 'Green'],\
                 source=dictionary_sensitivity_population_by_country,\
                 legend_label=['Base', 'Compare (added)'])

    p.yaxis.axis_label = 'population * (ppm /(μmol / (m²s)))'

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend[0].items.reverse()
    p.legend.label_text_font_size = "10px"
    p.xaxis.major_label_orientation = "vertical"

    output_population_by_country = Output()

    with output_population_by_country:

        output_population_by_country.clear_output()

        show(p)

    box_population = HBox([output_population_by_country, output_population_table])
    
    display(box_population)

def land_cover_bar_graphs_base(networkObj):
    
    base_network = networkObj.baseNetwork    
    countries = networkObj.settings['countries']
    dictionary = networkObj.countryDict
  
    # for the graph with all countries 
    land_cover_values = ['Broad leaf', 'Coniferous', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrub', 'Other', 'Unknown']
    
    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C', '#1964B0', '#F1932D', '#882E72','#777777']
    
    country_names = []
    
    broad_leaf_forest_list = [] 
    coniferous_forest_list = [] 
    mixed_forest_list = [] 
    ocean_list = [] 
    other_list = [] 
    grass_shrub_list = [] 
    cropland_list = [] 
    pasture_list = [] 
    urban_list = [] 
    unknown_list = []
    
    for country in countries:
        
        if dictionary[country]['base_network_breakdown']['total sens']>0:
        
            country_name = dictionary_area_choice[country]

            country_names.append(country_name)
            
            broad_leaf_forest = dictionary[country]['base_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['base_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['base_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['base_network_breakdown']['Cropland total']
            pasture = dictionary[country]['base_network_breakdown']['Pasture total']
            urban = dictionary[country]['base_network_breakdown']['Urban total']
            ocean = dictionary[country]['base_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['base_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['base_network_breakdown']['Other total']   
            unknown = dictionary[country]['base_network_breakdown']['Unknown total']
            
            # for the graph with all countries 
            broad_leaf_forest_list.append(broad_leaf_forest)
            coniferous_forest_list.append(coniferous_forest)
            mixed_forest_list.append(mixed_forest)
            cropland_list.append(cropland)
            pasture_list.append(pasture)
            urban_list.append(urban)
            ocean_list.append(ocean)
            grass_shrub_list.append(grass_shrub)
            other_list.append(other)
            unknown_list.append(unknown)
            
    dictionary_landcover_by_country = {'Countries': country_names,'Broad leaf forest': broad_leaf_forest_list, 'Coniferous forest': coniferous_forest_list, 'Mixed forest': mixed_forest_list,'Cropland' : cropland_list,'Pasture': pasture_list,'Urban': urban_list, 'Ocean': ocean_list, 'Grass/shrubland': grass_shrub_list, 'Other': other_list, 'Unknown': unknown_list}
    
    p_aggreg = figure(x_range=country_names, title='Sensitivity of network to countries split by land cover', toolbar_location="right", tooltips="$name @Countries: @$name{0f}", height=550, width=800)

    graph_items = p_aggreg.vbar_stack(land_cover_values, x='Countries', width=0.5, color=colors, source=dictionary_landcover_by_country)
    
    # to make the legend appear to the right of the graph 
    legend_items = [(land_cover, [graph]) for  land_cover, graph in zip(land_cover_values, graph_items)]
    legend = Legend(items=legend_items)
    p_aggreg.add_layout(legend, 'right')
    
    p_aggreg.y_range.start = 0
    p_aggreg.x_range.range_padding = 0.1
    p_aggreg.xgrid.grid_line_color = None
    p_aggreg.axis.minor_tick_line_color = None
    p_aggreg.outline_line_color = None
    p_aggreg.legend.label_text_font_size = "10px"
    p_aggreg.legend[0].items.reverse()
    p_aggreg.xaxis.major_label_orientation = "vertical"
    p_aggreg.yaxis.axis_label = 'area (km²) * (ppm /(μmol / (m²s)))'
    
    output_landcover_all = Output()
    
    with output_landcover_all:
        output_landcover_all.clear_output()
        
        if len(country_names)>1:
    
            show(p_aggreg)
        
    display(output_landcover_all)
   
    colors_individual = ['#82ba8f','#4c9c5f','#dae9c4','#CAE0AB','#b1d9ab','#90C987', '#865f5a', '#521A13', '#f8f167',  '#ded74d', '#ee8286', '#DC050C', '#5e93c8', '#1964B0', '#f7be81','#F1932D', '#c497b8', '#882E72','#a0a0a0','#777777']
    
    categories = ['Country', 'Network']
    
    
    for country in countries:
        
        output_landcover_individual = Output()
   
        if dictionary[country]['base_network_breakdown']['total sens']>0:
        
            country_name = dictionary_area_choice[country]
           
            broad_leaf_forest = dictionary[country]['base_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['base_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['base_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['base_network_breakdown']['Cropland total']
            pasture = dictionary[country]['base_network_breakdown']['Pasture total']
            urban = dictionary[country]['base_network_breakdown']['Urban total']
            ocean = dictionary[country]['base_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['base_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['base_network_breakdown']['Other total']   
            unknown = dictionary[country]['base_network_breakdown']['Unknown total']
   
            # one graph for each country showing landcover breakdown of the country as well as the breakdown within the footprint   
            total = broad_leaf_forest + coniferous_forest + mixed_forest + cropland + pasture + urban + ocean + grass_shrub + other + unknown 
            
            broad_leaf_forest_percent = (broad_leaf_forest / total) * 100
            coniferous_forest_percent = (coniferous_forest / total) * 100
            mixed_forest_percent = (mixed_forest / total) * 100
            cropland_percent = (cropland / total) * 100
            pasture_percent = (pasture / total) * 100
            urban_percent = (urban / total) * 100
            ocean_percent = (ocean / total) * 100
            grass_shrub_percent = (grass_shrub / total) * 100
            other_percent = (other / total) * 100
            unknown_percent = (unknown / total) * 100
            
            broad_leaf_forest_country_percent = dictionary[country]['country_breakdown']['Broad leaf forest']   
            coniferous_forest_country_percent = dictionary[country]['country_breakdown']['Coniferous forest'] 
            mixed_forest_country_percent = dictionary[country]['country_breakdown']['Mixed forest'] 
            cropland_country_percent = dictionary[country]['country_breakdown']['Cropland'] 
            pasture_country_percent = dictionary[country]['country_breakdown']['Pasture'] 
            urban_country_percent = dictionary[country]['country_breakdown']['Urban'] 
            ocean_country_percent = dictionary[country]['country_breakdown']['Ocean'] 
            grass_shrub_country_percent = dictionary[country]['country_breakdown']['Grass/shrubland'] 
            other_country_percent = dictionary[country]['country_breakdown']['Other'] 
            unknown_country_percent = dictionary[country]['country_breakdown']['Unknown'] 
                
            dictionary_landcover = {'Sensitivity country': [broad_leaf_forest_country_percent, coniferous_forest_country_percent,mixed_forest_country_percent,cropland_country_percent, pasture_country_percent, urban_country_percent, ocean_country_percent, grass_shrub_country_percent, other_country_percent, unknown_country_percent],
                                    
                                    'Sensitivity network': [broad_leaf_forest_percent,  coniferous_forest_percent,mixed_forest_percent, cropland_percent, pasture_percent,urban_percent, ocean_percent,grass_shrub_percent, other_percent, unknown_percent]}
            
            x = [ (land_cover, category) for land_cover in land_cover_values for category in categories ]
            
            counts = sum(zip(dictionary_landcover['Sensitivity country'], dictionary_landcover['Sensitivity network']), ()) 
            
            source = ColumnDataSource(data=dict(x=x, counts=counts, colors=colors_individual))

            label_yaxis = '%'
            
            title = 'Land cover within ' + country_name + ' vs. sensitivity of network split by land cover within ' + country_name

            #p_individual = figure(x_range=land_cover_values_individual, title=title, toolbar_location="below")
            p_individual = figure(x_range=FactorRange(*x), title=title, width = 800, height = 350, toolbar_location="right", tooltips="@x : @counts{0f} %")

            #p_individual.vbar(x='Land cover values', top = 'Sensitivity', width=0.5, color='color', source=dictionary_landcover)
            p_individual.vbar(x='x', top = 'counts', width=0.5, color = 'colors', source=source)

            p_individual.yaxis.axis_label = label_yaxis

            p_individual.y_range.start = 0
            p_individual.x_range.range_padding = 0.1
            p_individual.xgrid.grid_line_color = None
            p_individual.axis.minor_tick_line_color = None
            p_individual.outline_line_color = None

            p_individual.legend.label_text_font_size = "10px"
            p_individual.xaxis.major_label_orientation = "vertical"

            
            with output_landcover_individual:
                output_landcover_individual.clear_output()
                show(p_individual)
                
            display(output_landcover_individual)


def land_cover_bar_graphs_compare(networkObj):
    
    base_network = networkObj.baseNetwork
    compare_network = networkObj.compareNetwork
    countries = networkObj.settings['countries']
    dictionary= networkObj.countryDict
    
    land_cover_values = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
    
    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C', '#1964B0', '#F1932D', '#882E72','#777777']
    
    country_names = []
    
    broad_leaf_forest_list = [] 
    coniferous_forest_list = [] 
    mixed_forest_list = [] 
    ocean_list = [] 
    other_list = [] 
    grass_shrub_list = [] 
    cropland_list = [] 
    pasture_list = [] 
    urban_list = [] 
    unknown_list = []
    
    factors = []
    colors_individual = ['#82ba8f','#4c9c5f','#dae9c4','#CAE0AB','#b1d9ab','#90C987', '#865f5a', '#521A13', '#f8f167',  '#ded74d', '#ee8286', '#DC050C', '#5e93c8', '#1964B0', '#f7be81','#F1932D', '#c497b8', '#882E72','#a0a0a0','#777777']
    
    for country in countries:
            
        country_name = dictionary_area_choice[country]
        
        if networkObj.countryDict[country]['base_network_breakdown']['total sens']>0:
            
            factors.append((country_name, 'Base'))
            
            broad_leaf_forest = dictionary[country]['base_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['base_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['base_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['base_network_breakdown']['Cropland total']
            pasture = dictionary[country]['base_network_breakdown']['Pasture total']
            urban = dictionary[country]['base_network_breakdown']['Urban total']
            ocean = dictionary[country]['base_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['base_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['base_network_breakdown']['Other total']  
            unknown = dictionary[country]['base_network_breakdown']['Unknown total']
            if unknown <0:
                unknown = 0
       
            broad_leaf_forest_list.append(broad_leaf_forest)
            coniferous_forest_list.append(coniferous_forest)
            mixed_forest_list.append(mixed_forest)
            cropland_list.append(cropland)
            pasture_list.append(pasture)
            urban_list.append(urban)
            ocean_list.append(ocean)
            grass_shrub_list.append(grass_shrub)
            other_list.append(other)
            unknown_list.append(unknown)
            
        # if zero (base)
        else:
            
            # only need to add anything in case value in compare network
            if networkObj.countryDict[country]['compare_network_breakdown']['total sens']>0:
                
                factors.append((country_name, 'Base'))
                
                broad_leaf_forest_list.append(0)
                coniferous_forest_list.append(0)
                mixed_forest_list.append(0)
                cropland_list.append(0)
                pasture_list.append(0)
                urban_list.append(0)
                ocean_list.append(0)
                grass_shrub_list.append(0)
                other_list.append(0)
                unknown_list.append(0)
 
        # the compare network contains at least the base network + additional sites
        if networkObj.countryDict[country]['compare_network_breakdown']['total sens']>0:
            
            factors.append((country_name, 'Compare'))
            
            broad_leaf_forest = dictionary[country]['compare_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['compare_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['compare_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['compare_network_breakdown']['Cropland total']
            pasture = dictionary[country]['compare_network_breakdown']['Pasture total']
            urban = dictionary[country]['compare_network_breakdown']['Urban total']
            ocean = dictionary[country]['compare_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['compare_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['compare_network_breakdown']['Other total']   
            unknown = dictionary[country]['compare_network_breakdown']['Unknown total']
            if unknown <0:
                unknown = 0
       
            broad_leaf_forest_list.append(broad_leaf_forest)
            coniferous_forest_list.append(coniferous_forest)
            mixed_forest_list.append(mixed_forest)
            cropland_list.append(cropland)
            pasture_list.append(pasture)
            urban_list.append(urban)
            ocean_list.append(ocean)
            grass_shrub_list.append(grass_shrub)
            other_list.append(other)
            unknown_list.append(unknown)
   
    dictionary_landcover_by_country  = {'x': factors,
                                        'Broad leaf forest':broad_leaf_forest_list, 
                                        'Coniferous forest': coniferous_forest_list,
                                        'Mixed forest':mixed_forest_list,
                                        'Cropland':cropland_list,
                                        'Pasture':pasture_list,
                                        'Urban':urban_list,
                                        'Ocean': ocean_list,
                                        'Grass/shrubland': grass_shrub_list,
                                        'Other':other_list,
                                        'Unknown': unknown_list}
                                        
    source = ColumnDataSource(data=dictionary_landcover_by_country)
            
    p = figure(x_range=FactorRange(*factors), title='Sensitivities of networks to countries split by land cover', height=550, width=900,toolbar_location="right", tooltips="$name : @$name{0f}")

    graph_items= p.vbar_stack(land_cover_values, x='x', width=0.5, color=colors, source=source)

        # to make the legend appear to the right of the graph 
    legend_items = [(land_cover, [graph]) for  land_cover, graph in zip(land_cover_values, graph_items)]
    legend = Legend(items=legend_items)
    p.add_layout(legend, 'right')

 
    p.y_range.start = 0
    p.legend[0].items.reverse()
    p.legend.label_text_font_size = "10px"
    p.xaxis.major_label_orientation = "vertical"
    p.xaxis.group_label_orientation = 'vertical'
    p.yaxis.axis_label = 'area (km²) * (ppm /(μmol / (m²s)))'
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    
    output_landcover_all = Output()
    
    with output_landcover_all:
        
        output_landcover_all.clear_output()
    
        show(p)
        
    display(output_landcover_all)

    for country in countries:
        
        # to display land cover graph for each country 
        output_landcover_individual = Output()
        
        # to display land cover table for each country 
        output_landcover_individual_table = Output()
        
        # dataframe that will be displayed as table. It will contain land cover categories and associated 
        # increase in sensitivity given the compare network as opposed to the base network
        df_diff_base_compare = pd.DataFrame()
        
        country_name = dictionary_area_choice[country]
        
        if networkObj.countryDict[country]['base_network_breakdown']['total sens']>0:
            
            broad_leaf_forest = dictionary[country]['base_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['base_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['base_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['base_network_breakdown']['Cropland total']
            pasture = dictionary[country]['base_network_breakdown']['Pasture total']
            urban = dictionary[country]['base_network_breakdown']['Urban total']
            ocean = dictionary[country]['base_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['base_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['base_network_breakdown']['Other total']   
            unknown = dictionary[country]['base_network_breakdown']['Unknown total']
       
            broad_leaf_forest_list.append(broad_leaf_forest)
            coniferous_forest_list.append(coniferous_forest)
            mixed_forest_list.append(mixed_forest)
            cropland_list.append(cropland)
            pasture_list.append(pasture)
            urban_list.append(urban)
            ocean_list.append(ocean)
            grass_shrub_list.append(grass_shrub)
            other_list.append(other)
            unknown_list.append(unknown)
            
            list_land_cover_country_base = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean, grass_shrub, other, unknown]

        # if zero (base)
        else:
            
            # only need to add anything in case value in compare network
            if networkObj.countryDict[country]['compare_network_breakdown']['total sens']>0:
                
                broad_leaf_forest_list.append(0)
                coniferous_forest_list.append(0)
                mixed_forest_list.append(0)
                cropland_list.append(0)
                pasture_list.append(0)
                urban_list.append(0)
                ocean_list.append(0)
                grass_shrub_list.append(0)
                other_list.append(0)
                unknown_list.append(0)
                
                list_land_cover_country_base = [0,0,0,0,0,0,0,0,0,0]
        
        # the compare network contains at least the base network + additional sites
        if networkObj.countryDict[country]['compare_network_breakdown']['total sens']>0:
            
            broad_leaf_forest = dictionary[country]['compare_network_breakdown']['Broad leaf forest total']   
            coniferous_forest = dictionary[country]['compare_network_breakdown']['Coniferous forest total']
            mixed_forest = dictionary[country]['compare_network_breakdown']['Mixed forest total']
            cropland = dictionary[country]['compare_network_breakdown']['Cropland total']
            pasture = dictionary[country]['compare_network_breakdown']['Pasture total']
            urban = dictionary[country]['compare_network_breakdown']['Urban total']
            ocean = dictionary[country]['compare_network_breakdown']['Ocean total']
            grass_shrub = dictionary[country]['compare_network_breakdown']['Grass/shrubland total'] 
            other = dictionary[country]['compare_network_breakdown']['Other total']   
            unknown = dictionary[country]['compare_network_breakdown']['Unknown total']
       
            broad_leaf_forest_list.append(broad_leaf_forest)
            coniferous_forest_list.append(coniferous_forest)
            mixed_forest_list.append(mixed_forest)
            cropland_list.append(cropland)
            pasture_list.append(pasture)
            urban_list.append(urban)
            ocean_list.append(ocean)
            grass_shrub_list.append(grass_shrub)
            other_list.append(other)
            unknown_list.append(unknown)
            
            list_land_cover_country_compare = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean, grass_shrub, other, unknown]

            compare_minus_base_for_stack = [compare - base for base, compare in zip(list_land_cover_country_base, list_land_cover_country_compare)]

            #for land cover bar graph:
            dictionary_landcover = {'Land cover values': land_cover_values,
                         'Base': list_land_cover_country_base,
                         'Compare (added)': compare_minus_base_for_stack}

            label_yaxis = 'km² area * (ppm /(μmol / (m²s)))'

            title = 'Sensitivities of networks split by land cover within: ' + country_name

            p_individual = figure(x_range=land_cover_values, title=(title), toolbar_location="below", tooltips="$name : @$name{0f}")

            p_individual.vbar_stack(['Base', 'Compare (added)'], x='Land cover values', width=0.5, color=['Grey', 'Green'], source=dictionary_landcover, legend_label=['Base', 'Compare (added)'])

            p_individual.yaxis.axis_label = label_yaxis

            p_individual.y_range.start = 0
            p_individual.x_range.range_padding = 0.1
            p_individual.xgrid.grid_line_color = None
            p_individual.axis.minor_tick_line_color = None
            p_individual.outline_line_color = None
            p_individual.legend[0].items.reverse()

            p_individual.legend.label_text_font_size = "10px"
            p_individual.xaxis.major_label_orientation = "vertical"
            
            # for diff table
            change_base_compare_percent=[]
            for i in range(len(list_land_cover_country_base)):

                if list_land_cover_country_base[i]>0:
                    diff_base_compare = (((list_land_cover_country_compare[i]/list_land_cover_country_base[i])*100)-100) 

                elif list_land_cover_country_compare[i]>0:
                    diff_base_compare = 99999 
                else:
                    diff_base_compare = 0

                change_base_compare_percent.append(diff_base_compare)

            df_diff_base_compare['Increase sensitivity (%)'] = change_base_compare_percent

            with output_landcover_individual:
                output_landcover_individual.clear_output()
                show(p_individual)
                
            with output_landcover_individual_table:
                
                output_landcover_individual_table.clear_output()

                df_diff_base_compare = df_diff_base_compare.astype(float)

                df_diff_base_compare.insert(0, 'Category', land_cover_values)

                styled_df_diff_base_compare = (df_diff_base_compare.style
                                              .format({'Increase sensitivity (%)': '{:.0f}'})
                                              .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

                styled_df_diff_base_compare = styled_df_diff_base_compare.set_properties(**{'text-align': 'center'}).hide_index()
                
                display(styled_df_diff_base_compare)  
                
            box_landcover_individual = HBox([output_landcover_individual, output_landcover_individual_table])

            display(box_landcover_individual)
    
def histogram_fp_distribution(networkObj, fp_type):
    
    if fp_type == 'base':
        network=networkObj.baseNetwork
    else:
        network = networkObj.compareNetwork
        
    vmax = networkObj.vmaxSens
    
    df_values_fp = pd.DataFrame()

    df_values_fp['sensitivity'] = network.flatten()

    max_original = df_values_fp['sensitivity'].max()

    number_cells_above = df_values_fp[df_values_fp.sensitivity >= vmax].shape[0]
    
    df_for_hist = df_values_fp[(df_values_fp['sensitivity'] > 0) & (df_values_fp['sensitivity'] <vmax)]
    
    number_cells = len(df_for_hist)
    
    percentile_excluded = 100-((number_cells_above/number_cells)*100)
    
    histogram = df_for_hist.plot(kind='hist', bins=10, figsize=(7,6), legend=False, range=[0, vmax])
    histogram.grid(True)
    
    histogram.set_xlabel('ppm /(μmol / (m²s)')
    
    return histogram, percentile_excluded, max_original, number_cells_above
    
# 10-90% footprint visualization notebook
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
    
def percent_of_potential(input_footprint, fp_lat, fp_lon):
    
    max_fp_value = input_footprint.max()
    
    update_values = pd.DataFrame()
    
    update_values['flattened_fp'] = input_footprint.flatten()
    
    ten_percent = max_fp_value*0.1
    twenty_percent = max_fp_value*0.2
    thirty_percent = max_fp_value*0.3
    forty_percent = max_fp_value*0.4
    fifty_percent = max_fp_value*0.5
    sixty_percent = max_fp_value*0.6
    seventy_percent = max_fp_value*0.7
    eighty_percent = max_fp_value*0.8
    ninty_percent = max_fp_value*0.9
    
    #one is true here, in the other function (consum) 0 was true
    update_values['ten_percent']= np.where(update_values['flattened_fp']>=ten_percent, 1, 0)
    update_values['twenty_percent']= np.where(update_values['flattened_fp']>=twenty_percent, 1, 0)
    update_values['thirty_percent']= np.where(update_values['flattened_fp']>=thirty_percent, 1, 0)
    update_values['forty_percent']= np.where(update_values['flattened_fp']>=forty_percent, 1, 0)
    update_values['fifty_percent']= np.where(update_values['flattened_fp']>=fifty_percent, 1, 0)  
    update_values['sixty_percent']= np.where(update_values['flattened_fp']>=sixty_percent, 1, 0)
    update_values['seventy_percent']= np.where(update_values['flattened_fp']>=seventy_percent, 1, 0)
    update_values['eighty_percent']= np.where(update_values['flattened_fp']>=eighty_percent, 1, 0)
    update_values['ninty_percent']= np.where(update_values['flattened_fp']>=ninty_percent, 1, 0)
    
    update_values['aggreg'] = update_values['ten_percent'] + update_values['twenty_percent']+update_values['thirty_percent']+update_values['forty_percent']+update_values['fifty_percent'] + update_values['sixty_percent'] + update_values['seventy_percent'] + update_values['eighty_percent'] + update_values['ninty_percent']
    
    update_values['aggreg']=update_values['aggreg']*10
     
    list_updated_values=update_values['aggreg'].tolist()

    footprint_0_90=np.array(list_updated_values).reshape((len(fp_lat), len(fp_lon)))
    
    return footprint_0_90