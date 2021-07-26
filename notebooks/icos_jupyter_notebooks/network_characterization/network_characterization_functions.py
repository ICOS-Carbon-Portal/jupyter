# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 09:47:58 2020

@author: Ida Storm
"""
import pandas as pd
import os
import netCDF4 as cdf
import numpy as np
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

#for bokeh
from bokeh.io import show, output_notebook, reset_output
from bokeh.plotting import figure
from bokeh.models import HoverTool

from datetime import datetime
from matplotlib.colors import LogNorm

now = datetime.now()
date_time = now.strftime("%Y%m%d_%H%M%S")

reset_output()
output_notebook()

HOME = os.path.expanduser("~")+'/'

 
path_input=HOME+'icos_jupyter_notebooks/'
#path_input=HOME+'project/stilt_notebooks/footprint_area_analysis/'
path_data=path_input + 'network_characterization/'
path_footprints = path_data + 'footprints_2018_averaged/'

dictionary_area_choice = {'Belgium':'Belgium','Belgiu_eez':'Belgium (EEZ included)', 'Czech_Rep':'Czech Republic', 'Denmark':'Denmark','Denmar_eez':'Denmark (EEZ included)', 'Estonia':'Estonia', 'Estoni_eez':'Estonia (EEZ included)','Finland':'Finland', 'Finlan_eez':'Finland (EEZ included)', 'France':'France', 'France_eez':'France (EEZ included)','Germany':'Germany','Germa_eez':'Germany (EEZ included)', 'Hungary':'Hungary', 'Italy':'Italy', 'Italy_eez':'Italy', 'Netherland':'Netherlands', 'Nether_eez':'Netherlands (EEZ included)', 'Norway':'Norway', 'Norway_eez':'Norway (EEZ included)', 'Poland':'Poland', 'Poland_eez':'Poland (EEZ included)', 'Spain':'Spain', 'Spain_eez':'Spain (EEZ included)', 'Sweden':'Sweden', 'Swe_eez':'Sweden (EEZ included)', 'Switzerlan':'Switzerland', 'UK':'UK',  'UK_eez':'UK (EEZ included)'}

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

# footprint_show_percentages() is used to with argument percent=True to generate an aggregated % sensitivity map. 
def plot_maps(field, lon, lat, title='', label='', unit='', linlog='linear', station='', zoom='', 
              vmin=None, vmax=None, colors='GnBu',pngfile='', directory='figures', mask=False, percent=False): 

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
        
        if vmax:

            ticks = [*range(1, (vmax+2), 1)]

            ticklabels = ticks[:-1]
            
            ticklabels.append(' ')

        else:

            vmax = np.max(field[:,:])
            ticks = [*range(1, (np.max(field[:,:])+2),1)]

            ticklabels = ticks[:-1]
            
            ticklabels.append(' ')

        if percent:

            ticks = [10,20,30,40,50,60,70,80,90, 100]

            ticklabels = ticks[:-1]
            
            ticklabels.append(' ')
            
            vmin =10
        
        if not mask:

            #different color if use "neither"
            if vmin==vmax:
                vmax=None
            norm = matplotlib.colors.BoundaryNorm(ticks, cmap.N, extend='both')
            
            im = ax.imshow(field[:,:], norm=norm, interpolation=None,origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            
            cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='neither', format='%.0f', ticks=ticks)

            cbar.locator = matplotlib.ticker.FixedLocator(ticks)
            
            cbar.update_ticks()
            
            cbar.ax.set_xticklabels(ticklabels) 
            
            cbar.set_label(label+'  '+unit)

        else:
    
            im = ax.imshow(field[:,:], interpolation=None, origin='lower', extent=img_extent,cmap=cmap, vmin=0.0001, vmax=vmax, alpha=.5)
        
    else:

        cs = ax.imshow(field[:,:],norm=LogNorm(), origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)

        cbar = plt.colorbar(cs, orientation='horizontal',pad=0.03,fraction=0.055,extend='neither')
        
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
        
    zoom=str(zoom)
  
    plt.show()
    if len(pngfile)>0:
 
        output = os.path.join(os.path.expanduser('~'), 'output/network_characterization', date_time)

        if not os.path.exists(output):
            os.makedirs(output)
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
   
    plt.close()


name_correct_dictionary= {'ICOS_memb':'ICOS membership countries','Czech_Rep': 'Czech Republic', 'Switzerlan':'Switzerland', 'Netherland': 'Netherlands'}

def breakdown_countries_base_network(footprint_see_not_see, summed_fp_sens):

    f_gridarea = cdf.Dataset(path_data + 'gridareaSTILT.nc')

    #area stored in "cell_area" in m2
    gridarea = f_gridarea.variables['cell_area'][:]

    all_area_masks= cdf.Dataset(path_data + 'land_and_land_plus_eez_country_masks_icos_members.nc')

    list_areas=['Sweden', 'Belgium', 'Czech_Rep', 'Denmark', 'Estonia', 'Finland',  'France',  'Germany', 'Hungary', 'Italy', 'Netherland',  'Norway', 'Poland', 'Spain', 'Switzerlan', 'UK', 'ICOS_memb']
    list_areas_eez_included=['Swe_eez', 'Belgiu_eez', '', 'Denmar_eez', 'Estoni_eez', 'Finlan_eez', 'France_eez', 'Germa_eez','', 'Italy_eez',  'Nether_eez', 'Norway_eez', 'Poland_eez', 'Spain_eez', '', 'UK_eez', 'ICOS_m_eez']

    areas_seen=[]
    percent_seen=[]
    percent_seen_eez_included=[]
    
    percent_seen_sens = []
    percent_seen_sens_eez_included = []
    
    area_land_mass = []
    area_land_mass_plus_eez = []
    

    for area, area_eez in zip(list_areas, list_areas_eez_included):
        country_mask = all_area_masks.variables[area][:,:]
        #area in km2 of the area.
        country_mask_area=(gridarea*country_mask)/1000000
        country_mask_area_total=country_mask_area.sum()
        
        country_mask_within_footprint = footprint_see_not_see * country_mask
        country_mask_within_footprint_area = (gridarea * country_mask_within_footprint)/1000000
        country_mask_within_footprint_area_total= country_mask_within_footprint_area.sum()
        
        percent=(country_mask_within_footprint_area_total/country_mask_area_total)*100
        
        sensitivity_total = summed_fp_sens.sum() 
        sensitivity_within_footprint = (summed_fp_sens * country_mask).sum()
        percent_sensitivity = (sensitivity_within_footprint/sensitivity_total)*100
        
        
        if area_eez=='':
            country_mask_eez=all_area_masks.variables[area][:,:]
        else:
            
            country_mask_eez=all_area_masks.variables[area_eez][:,:]

        country_mask_eez_area=(gridarea*country_mask_eez)/1000000
        country_mask_area_eez_total=country_mask_eez_area.sum()
        
        country_mask_within_footprint_eez = footprint_see_not_see * country_mask_eez
        country_mask_within_footprint_area_eez = (gridarea * country_mask_within_footprint_eez)/1000000
        country_mask_within_footprint_area_eez_total= country_mask_within_footprint_area_eez.sum()
        
        sensitivity_within_footprint_eez = (summed_fp_sens * country_mask_eez).sum()

        percent_sensitivity_eez = (sensitivity_within_footprint_eez/sensitivity_total)*100
        
        
        percent_eez_included=(country_mask_within_footprint_area_eez_total/country_mask_area_eez_total)*100
        if percent > 0 or percent_eez_included>0:
            
            if area in name_correct_dictionary.keys():
                area = name_correct_dictionary[area]

            areas_seen.append(area)
            percent_seen.append(percent)
            percent_seen_eez_included.append(percent_eez_included)
            
            percent_seen_sens.append(percent_sensitivity)
            percent_seen_sens_eez_included.append(percent_sensitivity_eez)
            
                        
            area_land_mass.append(country_mask_area_total)
            area_land_mass_plus_eez.append(country_mask_area_eez_total)
    
      
    if len(areas_seen)>0:
        df_percent_seen=pd.DataFrame() 
         
        df_percent_seen=pd.DataFrame()
 
        df_percent_seen['Area country land mass (km²)'] = area_land_mass
        df_percent_seen['Land covered (%)'] = percent_seen
        
        df_percent_seen['Area country land mass + EEZ (km²)'] = area_land_mass_plus_eez
        df_percent_seen['Land+EEZ covered (%)'] = percent_seen_eez_included
        df_percent_seen['Sensitivity out of total (%)'] = percent_seen_sens
        df_percent_seen['Land+EEZ sensitivity out of total (%)'] = percent_seen_sens_eez_included
        
        df_percent_seen = df_percent_seen.astype(float)
        df_percent_seen=df_percent_seen.round(0)
        df_percent_seen = df_percent_seen.astype(int)
        df_percent_seen.insert(0, 'Country', areas_seen)
        
        
        df_percent_seen = df_percent_seen.style.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        df_percent_seen = df_percent_seen.set_properties(**{'text-align': 'center'}).hide_index()

        display(df_percent_seen)
    else:
        display(HTML('<p style="font-size:16px;">The footprint covers none of the countries in the dropdown.</p>'))

def breakdown_countries_compare_network(footprint_see_not_see, aggreg_fp_see_not_see_uploaded_fp):

    f_gridarea = cdf.Dataset(path_data + 'gridareaSTILT.nc')

    #area stored in "cell_area" in m2
    gridarea = f_gridarea.variables['cell_area'][:]

    all_area_masks= cdf.Dataset(path_data + 'land_and_land_plus_eez_country_masks_icos_members.nc')

    list_areas=['Sweden', 'Belgium', 'Czech_Rep', 'Denmark', 'Estonia', 'Finland',  'France',  'Germany', 'Hungary', 'Italy', 'Netherland',  'Norway', 'Poland', 'Spain', 'Switzerlan', 'UK', 'ICOS_memb']
    
    list_areas_eez_included=['Swe_eez', 'Belgiu_eez', '', 'Denmar_eez', 'Estoni_eez', 'Finlan_eez', 'France_eez', 'Germa_eez','', 'Italy_eez',  'Nether_eez', 'Norway_eez', 'Poland_eez', 'Spain_eez', '', 'UK_eez', 'ICOS_m_eez']

    areas_seen=[]
    percent_seen=[]
    percent_seen_eez_included=[]

    percent_seen_uploaded_fp=[]
    percent_seen_eez_included_uploaded_fp=[]
    
    area_land_mass = []
    area_land_mass_plus_eez = []
        
    for area, area_eez in zip(list_areas, list_areas_eez_included):
        country_mask = all_area_masks.variables[area][:,:]
        #area in km2 of the area.
        country_mask_area=(gridarea*country_mask)/1000000
        country_mask_area_total=country_mask_area.sum()
        
        country_mask_within_footprint = footprint_see_not_see * country_mask
        country_mask_within_footprint_area = (gridarea * country_mask_within_footprint)/1000000
        country_mask_within_footprint_area_total= country_mask_within_footprint_area.sum()
        
        percent=(country_mask_within_footprint_area_total/country_mask_area_total)*100
        
        country_mask_within_footprint_uploaded_fp = aggreg_fp_see_not_see_uploaded_fp * country_mask
        country_mask_within_footprint_area_uploaded_fp = (gridarea * country_mask_within_footprint_uploaded_fp)/1000000
        country_mask_within_footprint_area_total_uploaded_fp= country_mask_within_footprint_area_uploaded_fp.sum()
        
        
        percent_uploaded_fp=(country_mask_within_footprint_area_total_uploaded_fp/country_mask_area_total)*100
        
        if area_eez=='':
            country_mask_eez=all_area_masks.variables[area][:,:]
        else:
            #when no EEZ (no water)
            country_mask_eez=all_area_masks.variables[area_eez][:,:]
        
        country_mask_eez_area=(gridarea*country_mask_eez)/1000000
        country_mask_area_eez_total=country_mask_eez_area.sum()
        
        country_mask_within_footprint_eez = footprint_see_not_see * country_mask_eez
        country_mask_within_footprint_area_eez = (gridarea * country_mask_within_footprint_eez)/1000000
        country_mask_within_footprint_area_eez_total= country_mask_within_footprint_area_eez.sum()
        
        percent_eez_included=(country_mask_within_footprint_area_eez_total/country_mask_area_eez_total)*100
        
        
        country_mask_within_footprint_eez_uploaded_fp = aggreg_fp_see_not_see_uploaded_fp * country_mask_eez
        country_mask_within_footprint_area_eez_uploaded_fp = (gridarea * country_mask_within_footprint_eez_uploaded_fp)/1000000
        country_mask_within_footprint_area_eez_total_uploaded_fp= country_mask_within_footprint_area_eez_uploaded_fp.sum()
        
        percent_eez_included_uploaded_fp = (country_mask_within_footprint_area_eez_total_uploaded_fp/country_mask_area_eez_total)*100
        
        
        if percent > 0 or percent_eez_included>0 or percent_uploaded_fp > 0 or percent_eez_included_uploaded_fp>0:
            
            
            if area in name_correct_dictionary.keys():
                area = name_correct_dictionary[area]

            areas_seen.append(area)
            percent_seen.append('%.2f' % percent)
            percent_seen_eez_included.append('%.2f' % percent_eez_included)
            
            percent_seen_uploaded_fp.append('%.2f' % percent_uploaded_fp)
            percent_seen_eez_included_uploaded_fp.append('%.2f' % percent_eez_included_uploaded_fp)
            
            area_land_mass.append(country_mask_area_total)
            area_land_mass_plus_eez.append(country_mask_area_eez_total)
          
      
    if len(areas_seen)>0:
        
        #if breakdown_type = 'sens':
        
        df_percent_seen=pd.DataFrame()
        #df_percent_seen['Country'] = areas_seen
        
        df_percent_seen['Land mass (km²)'] = area_land_mass
        
        
        df_percent_seen['Land mass covered base network(%)'] = percent_seen
        df_percent_seen['Land mass covered compare network(%)'] = percent_seen_uploaded_fp
        
        df_percent_seen['Land mass+EEZ (km²)'] = area_land_mass_plus_eez
        
        df_percent_seen['Land mass+EEZ % covered base network (%)'] = percent_seen_eez_included
        df_percent_seen['Land mass+EEZ covered compare network(%)'] = percent_seen_eez_included_uploaded_fp 
       
        df_percent_seen = df_percent_seen.astype(float)
        df_percent_seen=df_percent_seen.round(0)
        df_percent_seen = df_percent_seen.astype(int)
        df_percent_seen.insert(0, 'Country', areas_seen)

        df_percent_seen = df_percent_seen.style.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        df_percent_seen = df_percent_seen.set_properties(**{'text-align': 'center'}).hide_index()

        display(df_percent_seen)
    else:
        display(HTML('<p style="font-size:16px;">The footprint covers none of the ICOS membership countries.</p>'))
        
        
def footprint_show_percentages(footprint_code, input_footprint, fp_lat, fp_lon):
    
    
    sum_sensitivity_values=sum(input_footprint.flatten())

    
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
    
    plot_maps(footprint_0_90, fp_lon, fp_lat, colors='Blues_r', vmin=10, vmax=90, percent = True, unit='%', title=(footprint_code + ' 2018'))
    
    
    
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
    
    #did not work when threhsold sensitivity was less than 1. 
    #df_sensitivity_sorted['mask_threshold'].loc[df_sensitivity_sorted['mask_threshold'] >= threshold_sensitivity]=0.0
    #df_sensitivity_sorted['mask_threshold'].loc[df_sensitivity_sorted['mask_threshold'] < threshold_sensitivity]=1.0

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

def one_or_zero_mask_x(summed_mask):
    
    #where value is greater than or equal to 1, give value 1. Otherwise give value 0. 
    summed_mask_upd=np.where(summed_mask >= 1, 1, 0)

    
    return summed_mask_upd

def load_fp(station):
    
    name_load_footprint_csv='fp_' + station + '.csv'
    
    try:
        loaded_fp=loadtxt((path_footprints + name_load_footprint_csv), delimiter=',')
    except:

        date_range = pd.date_range(start='2018-01-01', end='2019-01-01', freq='3H')

        #not including midnight between dec 31 and jan 1
        date_range = date_range[:-1]

        nfp, fp, lon, lat, title = read_aggreg_footprints(station, date_range)

        if fp is None:
            display(HTML('<p style="font-size:15px;">Not all footprints for ' + station + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to compute footprints for year 2018.</p>'))
            
            loaded_fp = 'no footprint'

        np.savetxt((path_footprints + name_load_footprint_csv),fp[0],delimiter=',',fmt='%.15f')

        loaded_fp=loadtxt((path_footprints+ name_load_footprint_csv), delimiter=',')

    return loaded_fp

def aggreg_2018_footprints_base_network(sites_base_network, threshold):
   
    load_lat=loadtxt(path_footprints + 'latitude.csv', delimiter=',')
    load_lon=loadtxt(path_footprints + 'longitude.csv', delimiter=',')
    
    first=True
    for station in sites_base_network:

        name_load_footprint_csv='fp_' + station + '.csv'
 
        loaded_fp=load_fp(station)

        if isinstance(loaded_fp, str) == True:
            continue
     
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        #based on threshold - get
        #footprint_show_percentages(station, loaded_fp, load_lat, load_lon)

        if first==True:
            #sensitivity values
            summed_fp_sens=upd_fp_sens
            #one or zero, for see or not see.
            summed_fp_see_not_see=upd_fp_see_not_see

            #only for the first footprint.
            first=False
        else:
            summed_fp_sens=summed_fp_sens+upd_fp_sens

            #values 0 - x depending on how many stations "sees" each cell
            summed_fp_see_not_see=summed_fp_see_not_see+upd_fp_see_not_see

    aggreg_fp_see_not_see = one_or_zero_mask_x(summed_fp_see_not_see)

    return summed_fp_sens, summed_fp_see_not_see, aggreg_fp_see_not_see, load_lon, load_lat

def aggreg_2018_footprints_compare_network(sites_base_network, list_additional_footprints, threshold):
    
    load_lat=loadtxt(path_footprints + 'latitude.csv', delimiter=',')
    load_lon=loadtxt(path_footprints + 'longitude.csv', delimiter=',')
    
    first=True
    for station in sites_base_network:

        loaded_fp=load_fp(station)
        if isinstance(loaded_fp, str) == True:
            continue

        #based on threshold - get 
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)

        if first==True:
            #sensitivity values
            summed_fp_sens=upd_fp_sens
            #one or zero, for see or not see.
            summed_fp_see_not_see=upd_fp_see_not_see

            #only for the first footprint.
            first=False
        else:
            summed_fp_sens = summed_fp_sens + upd_fp_sens

            #values 0 - x depending on how many stations "sees" each cell
            summed_fp_see_not_see = summed_fp_see_not_see + upd_fp_see_not_see
        
    aggreg_fp_see_not_see = one_or_zero_mask_x(summed_fp_see_not_see) 
    
    summed_fp_sens_additional = summed_fp_sens
    summed_fp_see_not_see_additional = summed_fp_see_not_see
    
    for station in list_additional_footprints:
        
        if station in sites_base_network:
            
            display(HTML('<p style="font-size:15px;">Selected ' + station + ' twice, not using it as "additional footprint"</p>'))

            continue
        
        loaded_fp = load_fp(station)
        
        if isinstance(loaded_fp, str) == True:
            continue
        
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        summed_fp_sens_additional = summed_fp_sens_additional + upd_fp_sens
        
        summed_fp_see_not_see_additional = summed_fp_see_not_see_additional + upd_fp_see_not_see

    aggreg_fp_see_not_see_additional = one_or_zero_mask_x(summed_fp_see_not_see_additional) 


    return summed_fp_sens_additional, summed_fp_see_not_see_additional, aggreg_fp_see_not_see_additional, load_lon, load_lat
    

def import_landcover():
    all_corine_classes= Dataset(path_data + 'all_corine_except_ocean.nc')

    #the "onceans_finalized" dataset is seperate: CORINE class 523 (oceans) did not extend beyond exclusive zone
    #complemented with Natural Earth data.
    #CORINE does not cover the whole area, "nodata" area is never ocean, rather landbased data.
    oceans_finalized= Dataset(path_data + 'oceans_finalized.nc')

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

    pop_data= Dataset(path_data + 'GEOSTAT_population_2011_2018.nc')
    fp_pop=pop_data.variables['2018'][:,:]
    return fp_pop


def breakdown_landcover(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see, breakdown_type = 'sens'):
    
    #import the necessary data
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()
    
    fp_pop = import_population_data()

    #gridarea - to calculate how much footprint covers.
    f_gridarea = cdf.Dataset(path_data + 'gridareaSTILT.nc')

    #area stored in "cell_area" in m2
    #test divide by 1000000 here instead
    gridarea = f_gridarea.variables['cell_area'][:]
    
    all_area_masks= Dataset(path_data + 'land_and_land_plus_eez_country_masks_icos_members.nc')

    countries = []
    urban = []
    cropland= []
    forest = []
    pastures_and_grasslands = []
    oceans_list = []
    other_list = []
    out_of_domain_list = []
    
    area_urban = []
    area_cropland = []
    area_forest = []
    area_pastures_and_grasslands = []
    area_oceans_list = []
    area_other_list = []
    area_out_of_domain_list = []
    
    population_sensitivity_list = []
    population_total_list = []
    
    land_cover_values = ['Urban', 'Cropland', 'Forest','Pastures and grasslands','Oceans', 'Other', 'Out of domain']

    colors=['red', 'darkgoldenrod', 'green', 'yellow','blue','black', 'purple']
    
    for area_choice in list_area_choice:

        #optional - one option is blank
        if area_choice!='':

            country_mask = all_area_masks.variables[area_choice][:,:]
            #area "seen" in the specific country (area_choice)
            seen_given_see_not_see_mask= country_mask*aggreg_fp_see_not_see
            seen_given_see_not_see_mask_area=(gridarea*seen_given_see_not_see_mask)/1000000
            seen_given_see_not_see_mask_area_total=seen_given_see_not_see_mask_area.sum()

            #total area of specific country (area_choice) - to calculate the % "seen" of each land cover class.
            country_area_grid=(gridarea*country_mask)/1000000
            country_area_total=country_area_grid.sum()
            country_area_grid_see_not_see_area = country_area_grid * aggreg_fp_see_not_see
            country_area_grid_see_not_see_area_total = country_area_grid_see_not_see_area.sum()

            percent_seen_given_country_mask = (seen_given_see_not_see_mask_area_total/country_area_total)*100

            #sensitivity footprint
            summed_fp_sens_country=summed_fp_sens*country_mask

            if percent_seen_given_country_mask > 0:

                #percent land cover within see/not see footprint:
                out_of_domain_area = (out_of_domain*seen_given_see_not_see_mask).sum()
                urban_area=(urban_aggreg*seen_given_see_not_see_mask).sum()
                cropland_area=(cropland_aggreg*seen_given_see_not_see_mask).sum()
                forests_area=(forests*seen_given_see_not_see_mask).sum()
                pastures_grasslands_area=(pastures_grasslands*seen_given_see_not_see_mask).sum()
                oceans_area=(oceans*seen_given_see_not_see_mask).sum()
                other_area=(other*seen_given_see_not_see_mask).sum()
                
                urban_percent=(urban_area/country_area_grid_see_not_see_area_total*100)
                cropland_percent=(cropland_area/country_area_grid_see_not_see_area_total*100)
                forests_percent=(forests_area/country_area_grid_see_not_see_area_total*100)
                pastures_grasslands_percent=(pastures_grasslands_area/country_area_grid_see_not_see_area_total*100)
                oceans_percent=(oceans_area/country_area_grid_see_not_see_area_total*100)
                other_percent=(other_area/country_area_grid_see_not_see_area_total*100)

                #to check if valid (if math.isinf(total))
                total= urban_percent + cropland_percent + forests_percent + pastures_grasslands_percent + oceans_percent + other_percent

                #percent sensitivity 
                #here compare to total sensitivity - need out of domain also (even though not show in graph)
                out_of_domain_sens=(out_of_domain*summed_fp_sens_country).sum()
                urban_sens=(urban_aggreg*summed_fp_sens_country).sum()
                cropland_sens=(cropland_aggreg*summed_fp_sens_country).sum()
                forests_sens=(forests*summed_fp_sens_country).sum()
                pastures_grasslands_sens=(pastures_grasslands*summed_fp_sens_country).sum()
                oceans_sens=(oceans*summed_fp_sens_country).sum()
                other_sens=(other*summed_fp_sens_country).sum()
                
                
                
                #total sensitivity - to get the percent sensitivity
                total_sens=out_of_domain_sens+urban_sens+cropland_sens+forests_sens+pastures_grasslands_sens+\
                             oceans_sens+other_sens
                
                percent_out_of_domain=(out_of_domain_sens/total_sens)*100
                percent_urban_sens=(urban_sens/total_sens)*100
                percent_cropland_sens=(cropland_sens/total_sens)*100
                percent_forests_sens=(forests_sens/total_sens)*100
                percent_pastures_grasslands_sens=(pastures_grasslands_sens/total_sens)*100
                percent_oceans_sens=(oceans_sens/total_sens)*100
                percent_other_sens=(other_sens/total_sens)*100
                

                if math.isinf(total):
                    continue
                
                #for aggregated graphs with all countries:
                #sensitivity
                country_name = dictionary_area_choice[area_choice]
                countries.append(country_name)
                urban.append(urban_sens)
                cropland.append(cropland_sens)
                forest.append(forests_sens)
                pastures_and_grasslands.append(pastures_grasslands_sens)
                oceans_list.append(oceans_sens)
                other_list.append(other_sens)
                out_of_domain_list.append(out_of_domain_sens)
                
                #area
                area_urban.append(urban_area)
                area_cropland.append(cropland_area)
                area_forest.append(forests_area)
                area_pastures_and_grasslands.append(pastures_grasslands_area)
                area_oceans_list.append(oceans_area)
                area_other_list.append(other_area)
                area_out_of_domain_list.append(out_of_domain_area)

                population_sensitivity = (fp_pop*summed_fp_sens_country).sum()
                population_total=(fp_pop*seen_given_see_not_see_mask).sum()

                
                population_sensitivity_list.append(population_sensitivity)
                population_total_list.append(population_total)
                

                #bokeh plot - one per country. Mask or sensitivity.
                df_landcover_breakdown = pd.DataFrame()

                if breakdown_type=='sens':
                    
                    values_by_country = [urban_sens, cropland_sens, forests_sens, pastures_grasslands_sens, oceans_sens, other_sens, out_of_domain_sens]
                    #values_by_country = [percent_urban_sens, percent_cropland_sens, percent_forests_sens, percent_pastures_grasslands_sens, percent_oceans_sens, percent_other_sens, percent_out_of_domain]
                    
                    df_landcover_breakdown['Sensitivity'] = values_by_country
                    
                    dictionary_values = {'Land cover values':land_cover_values,
                                         'Sensitivity':values_by_country,
                                         'color':colors}
                    column_w_data = 'Sensitivity'
                    
                    label_yaxis = 'area in km² * (ppm /(μmol / (m²s))))'
                    
                else:
                    values_by_country = [urban_area, cropland_area, forests_area, pastures_grasslands_area, oceans_area, other_area,out_of_domain_area] 

                    df_landcover_breakdown['Area covered (km²)'] = values_by_country
                    
                    dictionary_values = {'Land cover values':land_cover_values,
                                         'Area covered (km²)':values_by_country,
                                         'color':colors}
                    
                    column_w_data = 'Area covered (km²)'
                    
                    label_yaxis = 'km²'
                    
                country_name = dictionary_area_choice[area_choice]

                p = figure(x_range=land_cover_values, title=("Breakdown landcover " + country_name), toolbar_location="below")
                
                p.vbar(x='Land cover values', top = column_w_data, width=0.5, color='color', source=dictionary_values)
                
                p.yaxis.axis_label = label_yaxis

                p.y_range.start = 0
                p.x_range.range_padding = 0.1
                p.xgrid.grid_line_color = None
                p.axis.minor_tick_line_color = None
                p.outline_line_color = None

                p.legend.label_text_font_size = "10px"
                p.xaxis.major_label_orientation = "vertical"

                output_landcover_heading = Output()
                output_landcover_breakdown = Output()
                output_landcover_breakdown_table = Output()


                with output_landcover_breakdown:
                    output_landcover_breakdown.clear_output()

                    show(p)

                with output_landcover_breakdown_table:
                    output_landcover_breakdown_table.clear_output()
                    
                    df_landcover_breakdown = df_landcover_breakdown.astype(float)

                    df_landcover_breakdown = df_landcover_breakdown.round(1)

                    df_landcover_breakdown = df_landcover_breakdown.astype(int)
                    
                    
                    df_landcover_breakdown.insert(0, 'Category', land_cover_values)

                    df_landcover_breakdown = df_landcover_breakdown.style.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                    
                    df_landcover_breakdown=df_landcover_breakdown.set_properties(**{'text-align': 'center'}).hide_index()

                    display(df_landcover_breakdown)

                box_landcover = HBox([output_landcover_breakdown, output_landcover_breakdown_table])
                display(box_landcover)
    
    #now have data for all selected areas:
    if len(countries)>0:
        
        if breakdown_type == 'sens':
            #land cover graph
            dictionary_landcover_by_country = {'Countries': countries,'Urban': urban, 'Cropland': cropland, 'Forest': forest,'Pastures and grasslands' : pastures_and_grasslands,'Oceans': oceans_list,'Other': other_list, 'Out of domain': out_of_domain_list}
            
            title = "Breakdown sensitivity to land cover by country"
            
            label_yaxis = 'area in km² * (ppm /(μmol / (m²s)))'
            
            #population graph
            dictionary_population_by_country = {'Countries': countries,
                                 'Population': population_sensitivity_list}
            
            label_yaxis_pop = 'population * (ppm /(μmol / (m²s)))'
            
        else:
            
            #land cover graph
            title = "Breakdown area of land cover within footprint by country"
            
            dictionary_landcover_by_country = {'Countries': countries,'Urban': area_urban,'Cropland': area_cropland, 'Forest': area_forest,'Pastures and grasslands' : area_pastures_and_grasslands,'Oceans': area_oceans_list,'Other': area_other_list,'Out of domain': area_out_of_domain_list}
            
            label_yaxis = 'area (km²)'
            
            #population graph
            dictionary_population_by_country = {'Countries': countries,
                     'Population': population_total_list}
            
            label_yaxis_pop = 'Population'
            
        p = figure(x_range=countries, title=title, toolbar_location="below", tooltips="$name @Countries: @$name{0f}")

        p.vbar_stack(land_cover_values, x='Countries', width=0.5, color=colors, source=dictionary_landcover_by_country,
                 legend_label=land_cover_values)

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.legend.label_text_font_size = "10px"
        p.legend[0].items.reverse()
        p.xaxis.major_label_orientation = "vertical"
        p.yaxis.axis_label = label_yaxis

        output_landcover_breakdown2 = Output()

        with output_landcover_breakdown2:

            output_landcover_breakdown2.clear_output()

            show(p)

        display(output_landcover_breakdown2)

        #same type of graph but for population

        p = figure(x_range=countries, title="Breakdown population by country", toolbar_location="below", tooltips="@Population{0f}")

        p.vbar(x='Countries', top = 'Population', width=0.5, color='Darkblue', source = dictionary_population_by_country)

        p.yaxis.axis_label = label_yaxis_pop

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.legend.label_text_font_size = "10px"
        p.xaxis.major_label_orientation = "vertical"

        population_by_country = Output()

        with population_by_country:

            population_by_country.clear_output()


            show(p)

        display(population_by_country)
    
def breakdown_landcover_compare_network(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see, summed_fp_sens_uploaded_fp, aggreg_fp_see_not_see_uploaded_fp, breakdown_type='sens'):
    
    #import the necessary data
    out_of_domain, urban_aggreg, cropland_aggreg, forests, pastures_grasslands, oceans, other= import_landcover()
    
    fp_pop = import_population_data()
    
    f_gridarea = cdf.Dataset(path_data + 'gridareaSTILT.nc')

    gridarea = f_gridarea.variables['cell_area'][:]
    
    all_area_masks= Dataset(path_data + 'land_and_land_plus_eez_country_masks_icos_members.nc')

    countries = []
    urban = []
    cropland= []
    forest = []
    pastures_and_grasslands = []
    oceans_list = []
    other_list = []
    out_of_domain_list = []
    
        
    urban_area_list = []
    cropland_area_list = []
    forest_area_list = []
    pastures_and_grasslands_area_list = []
    oceans_list_area_list = []
    other_list_area_list = []
    out_of_domain_list_area_list = []
    
    population_sensitivity_list = []
    population_area_list = []
    
    land_cover_values = ['Urban', 'Cropland', 'Forest','Pastures and grasslands','Oceans', 'Other', 'Out of domain']

    colors=['red', 'darkgoldenrod', 'green', 'yellow','blue','black', 'purple']


    count_areas=0
    for area_choice in list_area_choice:

        #optional - one option is blank
        if area_choice!='':

            country_mask = all_area_masks.variables[area_choice][:,:]
            #area "seen" in the specific country (area_choice)
            seen_given_see_not_see_mask= country_mask*aggreg_fp_see_not_see
            seen_given_see_not_see_mask_area=(gridarea*seen_given_see_not_see_mask)/1000000
            seen_given_see_not_see_mask_area_total=seen_given_see_not_see_mask_area.sum()
            
            
            seen_given_see_not_see_mask_uploaded_fp= country_mask*aggreg_fp_see_not_see_uploaded_fp
            seen_given_see_not_see_mask_area_uploaded_fp=(gridarea*seen_given_see_not_see_mask_uploaded_fp)/1000000
            seen_given_see_not_see_mask_area_total_uploaded_fp=seen_given_see_not_see_mask_area_uploaded_fp.sum()
            

            #total area of specific country (area_choice) - to calculate the % "seen" of each land cover class.
            country_area_grid=(gridarea*country_mask)/1000000
            country_area_total=country_area_grid.sum()
            country_area_grid_see_not_see_area = country_area_grid * aggreg_fp_see_not_see
            country_area_grid_see_not_see_area_total = country_area_grid_see_not_see_area.sum()

            percent_seen_given_country_mask = (seen_given_see_not_see_mask_area_total/country_area_total)*100
            
            percent_seen_given_country_mask_uploaded_fp = (seen_given_see_not_see_mask_area_total_uploaded_fp/country_area_total)*100

 
            #sensitivity footprint
            summed_fp_sens_country=summed_fp_sens*country_mask
            
            summed_fp_sens_country_uploaded_fp=summed_fp_sens_uploaded_fp*country_mask

            if percent_seen_given_country_mask > 0 or percent_seen_given_country_mask_uploaded_fp>0:

                #percent land cover within see/not see footprint:
                out_of_domain_area = (out_of_domain*seen_given_see_not_see_mask).sum()
                urban_area=(urban_aggreg*seen_given_see_not_see_mask).sum()
                cropland_area=(cropland_aggreg*seen_given_see_not_see_mask).sum()
                forests_area=(forests*seen_given_see_not_see_mask).sum()
                pastures_grasslands_area=(pastures_grasslands*seen_given_see_not_see_mask).sum()
                oceans_area=(oceans*seen_given_see_not_see_mask).sum()
                other_area=(other*seen_given_see_not_see_mask).sum()
                
                out_of_domain_area_uploaded_fp = (out_of_domain*seen_given_see_not_see_mask_uploaded_fp).sum()
                urban_area_uploaded_fp=(urban_aggreg*seen_given_see_not_see_mask_uploaded_fp).sum()
                cropland_area_uploaded_fp=(cropland_aggreg*seen_given_see_not_see_mask_uploaded_fp).sum()
                forests_area_uploaded_fp=(forests*seen_given_see_not_see_mask_uploaded_fp).sum()
                pastures_grasslands_area_uploaded_fp=(pastures_grasslands*seen_given_see_not_see_mask_uploaded_fp).sum()
                oceans_area_uploaded_fp=(oceans*seen_given_see_not_see_mask_uploaded_fp).sum()
                other_area_uploaded_fp=(other*seen_given_see_not_see_mask_uploaded_fp).sum()
                
                
                urban_percent=(urban_area/country_area_grid_see_not_see_area_total*100)
                cropland_percent=(cropland_area/country_area_grid_see_not_see_area_total*100)
                forests_percent=(forests_area/country_area_grid_see_not_see_area_total*100)
                pastures_grasslands_percent=(pastures_grasslands_area/country_area_grid_see_not_see_area_total*100)
                oceans_percent=(oceans_area/country_area_grid_see_not_see_area_total*100)
                other_percent=(other_area/country_area_grid_see_not_see_area_total*100)

                #to check if valid (if math.isinf(total))
                total= urban_percent + cropland_percent + forests_percent + pastures_grasslands_percent + oceans_percent+other_percent

                #percent sensitivity 
                #here compare to total sensitivity - need out of domain also (even though not show in graph)
                out_of_domain_sens=(out_of_domain*summed_fp_sens_country).sum()
                urban_sens=(urban_aggreg*summed_fp_sens_country).sum()
                cropland_sens=(cropland_aggreg*summed_fp_sens_country).sum()
                forests_sens=(forests*summed_fp_sens_country).sum()
                pastures_grasslands_sens=(pastures_grasslands*summed_fp_sens_country).sum()
                oceans_sens=(oceans*summed_fp_sens_country).sum()
                other_sens=(other*summed_fp_sens_country).sum()
                
                population_sensitivity = (fp_pop*summed_fp_sens_country).sum()
                
                population_area = (fp_pop*seen_given_see_not_see_mask).sum()
                
                out_of_domain_sens_uploaded_fp=(out_of_domain*summed_fp_sens_country_uploaded_fp).sum()
                urban_sens_uploaded_fp=(urban_aggreg*summed_fp_sens_country_uploaded_fp).sum()
                cropland_sens_uploaded_fp=(cropland_aggreg*summed_fp_sens_country_uploaded_fp).sum()
                forests_sens_uploaded_fp=(forests*summed_fp_sens_country_uploaded_fp).sum()
                pastures_grasslands_sens_uploaded_fp=(pastures_grasslands*summed_fp_sens_country_uploaded_fp).sum()
                oceans_sens_uploaded_fp=(oceans*summed_fp_sens_country_uploaded_fp).sum()
                other_sens_uploaded_fp=(other*summed_fp_sens_country_uploaded_fp).sum()
                
                population_sensitivity_uploaded_fp = (fp_pop*summed_fp_sens_country_uploaded_fp).sum()
                population_area_uploaded_fp = (fp_pop*seen_given_see_not_see_mask_uploaded_fp).sum()
                
                population_total=(fp_pop*seen_given_see_not_see_mask).sum()

                #total sensitivity - to get the percent sensitivity
                total_sens=out_of_domain_sens+urban_sens+cropland_sens+forests_sens+pastures_grasslands_sens+\
                             oceans_sens+other_sens
                percent_out_of_domain=(out_of_domain_sens/total_sens)*100
                percent_urban_sens=(urban_sens/total_sens)*100
                percent_cropland_sens=(cropland_sens/total_sens)*100
                percent_forests_sens=(forests_sens/total_sens)*100
                percent_pastures_grasslands_sens=(pastures_grasslands_sens/total_sens)*100
                percent_oceans_sens=(oceans_sens/total_sens)*100
                percent_other_sens=(other_sens/total_sens)*100
                

                if math.isinf(total):
                    continue

                count_areas = count_areas +1

                #for plots showing all countries next to each other:
                
                country_name = dictionary_area_choice[area_choice]
                countries.append(country_name + ' base')
                urban.append(urban_sens)
                cropland.append(cropland_sens)
                forest.append(forests_sens)
                pastures_and_grasslands.append(pastures_grasslands_sens)
                oceans_list.append(oceans_sens)
                other_list.append(other_sens)
                out_of_domain_list.append(out_of_domain_sens)
                
                urban_area_list.append(urban_area)
                cropland_area_list.append(cropland_area)
                forest_area_list.append(forests_area)
                pastures_and_grasslands_area_list.append(pastures_grasslands_area)
                oceans_list_area_list.append(oceans_area)
                other_list_area_list.append(other_area)
                out_of_domain_list_area_list.append(out_of_domain_area)

                population_sensitivity_list.append(population_sensitivity)
                
                population_area_list.append(population_area)

                countries.append(country_name + ' compare')
                urban.append(urban_sens_uploaded_fp)
                cropland.append(cropland_sens_uploaded_fp)
                forest.append(forests_sens_uploaded_fp)
                pastures_and_grasslands.append(pastures_grasslands_sens_uploaded_fp)
                oceans_list.append(oceans_sens_uploaded_fp)
                other_list.append(other_sens_uploaded_fp)
                out_of_domain_list.append(out_of_domain_sens_uploaded_fp)
                
                urban_area_list.append(urban_area_uploaded_fp)
                cropland_area_list.append(cropland_area_uploaded_fp)
                forest_area_list.append(forests_area_uploaded_fp)
                pastures_and_grasslands_area_list.append(pastures_grasslands_area_uploaded_fp)
                oceans_list_area_list.append(oceans_area_uploaded_fp)
                other_list_area_list.append(other_area_uploaded_fp)
                out_of_domain_list_area_list.append(out_of_domain_area_uploaded_fp)
                                               
                population_area_list.append(population_area_uploaded_fp)

                #change here later
                population_sensitivity_list.append(population_sensitivity_uploaded_fp)

                 #bokeh plot - one per country. Mask or sensitivity.
                df_landcover_breakdown = pd.DataFrame()

                colors_duplicated = ['red', 'red', 'darkgoldenrod','darkgoldenrod', 'green',  'green' , 'yellow', 'yellow', 'blue','blue', 'black', 'black', 'purple','purple']
                
                land_cover_values_duplicated = ['Urban','Urban +', 'Cropland', 'Cropland +', 'Forest','Forest +', 'Pastures and grasslands','Pastures and grasslands +','Oceans', 'Oceans +', 'Other', 'Other +', 'Out of domain', 'Out of domain +'] 
                
                if breakdown_type=='sens':
    
                    values_by_country = [urban_sens, urban_sens_uploaded_fp, cropland_sens, cropland_sens_uploaded_fp, forests_sens, forests_sens_uploaded_fp, pastures_grasslands_sens, pastures_grasslands_sens_uploaded_fp,oceans_sens, oceans_sens_uploaded_fp, other_sens, other_sens_uploaded_fp, out_of_domain_sens, out_of_domain_sens_uploaded_fp]    
                    
                    values_by_country = [0 if math.isnan(x) else x for x in values_by_country]
                    
                    #values_by_country = [percent_urban_sens, percent_cropland_sens, percent_forests_sens, percent_pastures_grasslands_sens, percent_oceans_sens, percent_other_sens, percent_out_of_domain]
                    
                    
                    #every second item in list (starting with the first: [::2], starting with the second: [1::2])
                    df_landcover_breakdown['Sensitivity base network'] = values_by_country[::2]
                    df_landcover_breakdown['Sensitivity compare network'] = values_by_country[1::2]
                    
                    
                    compare_minus_base_for_stack = [compare - base for base, compare in zip(values_by_country[::2], values_by_country[1::2])]
                    dictionary_values = {'Land cover values': land_cover_values,
                                         'Base network': values_by_country[::2],
                                         'Compare network': compare_minus_base_for_stack}
                    
                    #column_w_data = 'Sensitivity'
                    
                    label_yaxis = 'km² area * (ppm /(μmol / (m²s)))'
                    
                else:
                    values_by_country = [urban_area, urban_area_uploaded_fp, cropland_area, cropland_area_uploaded_fp, forests_area, forests_area_uploaded_fp, pastures_grasslands_area, pastures_grasslands_area_uploaded_fp, oceans_area, oceans_area_uploaded_fp, other_area, other_area_uploaded_fp, out_of_domain_area, out_of_domain_area_uploaded_fp] 
            
                    df_landcover_breakdown['Area covered (km²) base network'] = values_by_country[::2]
                    df_landcover_breakdown['Area covered (km²) compare network'] = values_by_country[1::2]
                    
                    compare_minus_base_for_stack = [compare - base for base, compare in zip(values_by_country[::2], values_by_country[1::2])]
                    dictionary_values = {'Land cover values': land_cover_values,
                                         'Base network': values_by_country[::2],
                                         'Compare network': compare_minus_base_for_stack}
                    #column_w_data = 'Area covered (km²)'
                    
                    label_yaxis = 'area (km²)'

                country_name = dictionary_area_choice[area_choice]

                p = figure(x_range=land_cover_values, title=("Breakdown landcover " + country_name), toolbar_location="below", plot_width=350)
                
                p.vbar_stack(['Base network', 'Compare network'], x='Land cover values', width=0.5, color=['Black', 'Green'], source=dictionary_values, legend_label=['Base network', 'Compare network'])
                
                p.yaxis.axis_label = label_yaxis

                p.y_range.start = 0
                p.x_range.range_padding = 0.1
                p.xgrid.grid_line_color = None
                p.axis.minor_tick_line_color = None
                p.outline_line_color = None

                p.legend.label_text_font_size = "10px"
                p.xaxis.major_label_orientation = "vertical"


                output_landcover_heading = Output()
                output_landcover_breakdown = Output()
                output_landcover_breakdown_table = Output()

                with output_landcover_breakdown:
                    output_landcover_breakdown.clear_output()
             
                    show(p)

                with output_landcover_breakdown_table:
                    output_landcover_breakdown_table.clear_output()
                    
                    df_landcover_breakdown = df_landcover_breakdown.astype(float)

                    df_landcover_breakdown = df_landcover_breakdown.round(0)

                    df_landcover_breakdown = df_landcover_breakdown.astype(int)
                    
                    #_duplicated before
                    df_landcover_breakdown.insert(0, 'Category', land_cover_values)

                    df_landcover_breakdown = df_landcover_breakdown.style.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                    
                    df_landcover_breakdown=df_landcover_breakdown.set_properties(**{'text-align': 'center'}).hide_index()

                    display(df_landcover_breakdown)
                    

                box_landcover = HBox([output_landcover_breakdown, output_landcover_breakdown_table])
                display(output_landcover_heading, box_landcover)

    #now have data for all selected areas:
    
    if count_areas>0:

        if breakdown_type == 'sens':
            
            dictionary_sensitivity_by_country = {'Countries': countries,
                                             'Urban': urban,
                                             'Cropland': cropland,
                                             'Forest': forest,
                                             'Pastures and grasslands' : pastures_and_grasslands,
                                             'Oceans': oceans_list,
                                             'Other': other_list,
                                             'Out of domain': out_of_domain_list}
            
            label_yaxis = 'km² area * (ppm /(μmol / (m²s)))'
            
            title = "Sensitivity to land cover by country"
            
        else:

            dictionary_sensitivity_by_country = {'Countries': countries,
                                 'Urban': urban_area_list,
                                 'Cropland': cropland_area_list,
                                 'Forest': forest_area_list,
                                 'Pastures and grasslands' : pastures_and_grasslands_area_list,
                                 'Oceans': oceans_list_area_list,
                                 'Other': other_list_area_list,
                                 'Out of domain': out_of_domain_list_area_list}
            
            label_yaxis = 'km²'
            
            title = "Land cover within footprints by country"

        p = figure(x_range=countries, title=title, toolbar_location="below", tooltips="$name @Countries: @$name{0f}")

        p.vbar_stack(land_cover_values, x='Countries', width=0.5, color=colors, source=dictionary_sensitivity_by_country,
                 legend_label=land_cover_values)

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.legend.label_text_font_size = "10px"
        p.legend[0].items.reverse()
        p.xaxis.major_label_orientation = "vertical"
        p.yaxis.axis_label = label_yaxis 

        output_landcover_breakdown2 = Output()
        
        with output_landcover_breakdown2:

            output_landcover_breakdown2.clear_output()


            show(p)

        display(output_landcover_breakdown2)

        #same type of graph but for population
        countries_popualtion = [country[:-5] for country in countries[::2]]
        if breakdown_type == 'sens':
                 
            compare_minus_base_for_stack = [compare - base for base, compare in zip(population_sensitivity_list[::2], population_sensitivity_list[1::2])]
            
            dictionary_sensitivity_population_by_country = {'Countries': countries_popualtion,
                                 'Base_network': population_sensitivity_list[::2],
                                 'Compare_network': compare_minus_base_for_stack}
                    
            label_yaxis = 'population * (ppm /(μmol / (m²s)))'
            
            title = "Sensitivity to population by country"
            
        else:
            
            compare_minus_base_for_stack = [compare - base for base, compare in zip(population_area_list[::2], population_area_list[1::2])]
            
            dictionary_sensitivity_population_by_country = {'Countries': countries_popualtion,
                                 'Base_network': population_area_list[::2],
                                 'Compare_network': compare_minus_base_for_stack}

            label_yaxis = 'total population'
            
            title = "Total population within footprints by country"
            
        p = figure(x_range=countries_popualtion, title=title, toolbar_location="below", tooltips=[('Base network', '@{Base_network}{0f}'),( 'Addition compare network', '@{Compare_network}{0f}')])
      
        p.vbar_stack(['Base_network', 'Compare_network'], x='Countries', width=0.5, color=['Darkblue', 'Green'],\
                     source=dictionary_sensitivity_population_by_country,\
                     legend_label=['Base network', 'Compare network'])
        
        p.yaxis.axis_label = label_yaxis
            
        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.legend.label_text_font_size = "10px"
        p.xaxis.major_label_orientation = "vertical"

        population_by_country = Output()

        with population_by_country:

            population_by_country.clear_output()

            show(p)

        display(population_by_country)

#not used in tool on exploredata          
def export_fp(summed_fp_sens):

    np.savetxt(path_data + 'fp_export.csv',summed_fp_sens,delimiter=',',fmt='%.15f')
    
    
#needs to be updated
def save_map_texts(list_footprint_choice, threshold, list_additional_footprints):

    string_station_info='The following stations 2018 footprint(s) were aggregated to generate the network maps: ' 
    
    
    for station in list_footprint_choice:
        
        string_station_info+=station + ', '
        
    string_station_info = string_station_info[:-2]
    if len(list_additional_footprints)>0:
        
        string_station_info_additional='\nThe following additional stations 2018 footprint(s) were aggregated to generate the network maps that show also additional stations (_additional): ' 
        
        for station in list_additional_footprints:
            
            string_station_info_additional += station + ', '
            
        string_station_info_additional = string_station_info_additional[:-2]
        
    else:
        
        string_station_info_additional = ''
        
    
        
        
    date_generated = date.today()
    
    threshold_percent=threshold*100
    
    string_station_info+= string_station_info_additional
    
    string_station_info+= '\nThredhold footprint: ' + str(threshold_percent) + '%'
    
    string_station_info+= '\nDate generated: ' + str(date_generated)
    
    #move up to top (+ remove in other places)
    output = os.path.join(os.path.expanduser('~'), 'output/network_characterization', date_time)
                          
    if not os.path.exists(output):
        os.makedirs(output)
        
    export_file=output + '/map_information.txt'
    open_file= open(export_file, "w")
    open_file.write(string_station_info)
    open_file.close() 


                  