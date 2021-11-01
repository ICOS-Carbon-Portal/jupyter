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

#for bokeh
from bokeh.io import show, output_notebook, reset_output
from bokeh.plotting import figure
from bokeh.models import HoverTool

from datetime import datetime
from matplotlib.colors import LogNorm
import json
reset_output()
output_notebook()


folder_tool = 'network_characterization' 

folder_tool_fps = '/data/project/stc/footprints_2018_averaged'

#added 
folder_data = '/data/project/stc/'

dictionary_area_choice = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium','BIH':'Bosnia and Herzegovina','BGR':'Bulgaria','HRV':'Croatia','CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LIE':'Liechtenstein','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta','MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SMR':'San Marino','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}

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
        
        if vmax:

            ticks = [*range(1, (vmax+2), 1)]

            ticklabels = ticks[:-1]
            ticklabels.insert(0, ' ')

        else:

            vmax = np.max(field[:,:])
            ticks = [*range(1, (np.max(field[:,:])+2),1)]

            ticklabels = ticks[:-1]
            ticklabels.insert(0, ' ')

        if percent:

            ticks = [10,20,30,40,50,60,70,80,90,100]
            
            ticklabels = [' ', 10, 20, 30, 40, 50, 60, 70, 80, 90]
            
            vmin =10
 
        if not mask:

            #different color if use "neither"
            if vmin==vmax:
                vmax=None
            norm = matplotlib.colors.BoundaryNorm(ticks, cmap.N, extend='both')
            
            im = ax.imshow(field[:,:], norm=norm, interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            
            cbar=plt.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='neither', format='%.0f', ticks=ticks)

            cbar.locator = matplotlib.ticker.FixedLocator(ticks)
            
            cbar.update_ticks()
            
            cbar.ax.set_xticklabels(ticklabels) 
            
            cbar.set_label(label+'  '+unit)

        else:
    
            im = ax.imshow(field[:,:], interpolation='none', origin='lower', extent=img_extent,cmap=cmap, vmin=0.0001, vmax=vmax, alpha=.5)
        
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
  
        fig.savefig(output+'/'+pngfile+'.png',dpi=100,bbox_inches='tight')
    if percent:
        
        return plt

name_correct_dictionary= {'ICOS_memb':'ICOS membership countries','Czech_Rep': 'Czech Republic', 'Switzerlan':'Switzerland', 'Netherland': 'Netherlands'}

def breakdown_countries_base_network(footprint_see_not_see, summed_fp_sens, area_type='Land'):

    f_gridarea = cdf.Dataset(os.path.join(folder_data, 'gridareaSTILT.nc'))

    #area stored in "cell_area" in m2
    gridarea = f_gridarea.variables['cell_area'][:]

    areas_seen=[]
    percent_seen=[]
    percent_seen_eez_included=[]
    
    percent_seen_sens = []
    percent_seen_sens_eez_included = []
    
    area_land_mass = []
    area_land_mass_plus_eez = []
    
    all_available_counties = dictionary_area_choice.keys()

    for country_code in all_available_counties:
        
        country_mask = country_masks.variables[country_code][:,:]

        try:
            country_mask_eez = country_masks_eez_included.variables[country_code][:,:]

        # when no eez for country
        except:    
            country_mask_eez = country_masks.variables[country_code][:,:]

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

        country_mask_eez_area=(gridarea*country_mask_eez)/1000000
        country_mask_area_eez_total=country_mask_eez_area.sum()
        
        country_mask_within_footprint_eez = footprint_see_not_see * country_mask_eez
        country_mask_within_footprint_area_eez = (gridarea * country_mask_within_footprint_eez)/1000000
        country_mask_within_footprint_area_eez_total= country_mask_within_footprint_area_eez.sum()
        
        sensitivity_within_footprint_eez = (summed_fp_sens * country_mask_eez).sum()

        percent_sensitivity_eez = (sensitivity_within_footprint_eez/sensitivity_total)*100

        percent_eez_included=(country_mask_within_footprint_area_eez_total/country_mask_area_eez_total)*100
        
        if percent > 0 or percent_eez_included>0:
            
            area = dictionary_area_choice[country_code]

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
 
        df_percent_seen['Land mass (km²)'] = area_land_mass
        df_percent_seen['Land mass covered (%)'] = percent_seen
        
        df_percent_seen['Land mass+EEZ (km²)'] = area_land_mass_plus_eez
        df_percent_seen['Land+EEZ covered (%)'] = percent_seen_eez_included
        df_percent_seen['Sensitivity of site network falling within borders (%)'] = percent_seen_sens
        df_percent_seen['Sensitivity of site network falling within borders + EEZ (%)'] = percent_seen_sens_eez_included
        

        df_percent_seen.insert(0, 'Country', areas_seen)

        styled_df_percent_seen = (df_percent_seen.style
                                      .format({'Land mass (km²)': '{:.0f}', 'Land mass covered (%)': '{:.2f}', 'Land mass+EEZ (km²)': '{:.0f}',  'Land+EEZ covered (%)': '{:.2f}', 'Sensitivity of site network falling within borders (%)': '{:.2f}', 'Sensitivity of site network falling within borders + EEZ (%)': '{:.2f}'})
                                      .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

        styled_df_percent_seen = styled_df_percent_seen.set_properties(**{'text-align': 'center'}).hide_index()
        display(styled_df_percent_seen)  

    else:
        display(HTML('<p style="font-size:16px;">The footprint covers none of the countries in the dropdown.</p>'))

def breakdown_countries_compare_network(footprint_see_not_see, aggreg_fp_see_not_see_uploaded_fp, area_type='Land'):

    f_gridarea = cdf.Dataset(os.path.join(folder_data, 'gridareaSTILT.nc'))

    #area stored in "cell_area" in m2
    gridarea = f_gridarea.variables['cell_area'][:]

    list_areas=['Sweden', 'Belgium', 'Czech_Rep', 'Denmark', 'Estonia', 'Finland',  'France',  'Germany', 'Hungary', 'Italy', 'Netherland',  'Norway', 'Poland', 'Spain', 'Switzerlan', 'UK', 'ICOS_memb']
    
    list_areas_eez_included=['Swe_eez', 'Belgiu_eez', '', 'Denmar_eez', 'Estoni_eez', 'Finlan_eez', 'France_eez', 'Germa_eez','', 'Italy_eez',  'Nether_eez', 'Norway_eez', 'Poland_eez', 'Spain_eez', '', 'UK_eez', 'ICOS_m_eez']

    areas_seen=[]
    percent_seen=[]
    percent_seen_eez_included=[]

    percent_seen_uploaded_fp=[]
    percent_seen_eez_included_uploaded_fp=[]
    
    area_land_mass = []
    area_land_mass_plus_eez = []
        
    all_available_counties = dictionary_area_choice.keys()

    for country_code in all_available_counties:
        
        country_mask = country_masks.variables[country_code][:,:]

        try:
            country_mask_eez = country_masks_eez_included.variables[country_code][:,:]

        # when no eez for country
        except:    
            country_mask_eez = country_masks.variables[country_code][:,:]
            
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
            
            area = dictionary_area_choice[country_code]

            areas_seen.append(area)
            percent_seen.append('%.2f' % percent)
            percent_seen_eez_included.append('%.2f' % percent_eez_included)
            
            percent_seen_uploaded_fp.append('%.2f' % percent_uploaded_fp)
            percent_seen_eez_included_uploaded_fp.append('%.2f' % percent_eez_included_uploaded_fp)
            
            area_land_mass.append(country_mask_area_total)
            area_land_mass_plus_eez.append(country_mask_area_eez_total)
             
    if len(areas_seen)>0:

        df_percent_seen=pd.DataFrame()
        
        df_percent_seen['Country'] = areas_seen
        
        df_percent_seen['Land mass (km²)'] = area_land_mass
        
        
        df_percent_seen['Land mass covered base network(%)'] = [float(i) for i in percent_seen]
        df_percent_seen['Land mass covered compare network(%)'] = [float(i) for i in percent_seen_uploaded_fp]
        
        df_percent_seen['Land mass+EEZ (km²)'] = area_land_mass_plus_eez
        
        df_percent_seen['Land mass+EEZ % covered base network (%)'] = [float(i) for i in percent_seen_eez_included]
        df_percent_seen['Land mass+EEZ covered compare network (%)'] = [float(i) for i in percent_seen_eez_included_uploaded_fp ]
        
      
        styled_df_percent_seen = (df_percent_seen.style
                                      .format({'Land mass (km²)': '{:.0f}', 'Land mass covered base network(%)': '{:.2f}', 'Land mass covered compare network(%)': '{:.2f}', 'Land mass+EEZ (km²)': '{:.0f}',  'Land mass+EEZ % covered base network (%)': '{:.2f}', 'Land mass+EEZ covered compare network (%)': '{:.2f}'})
                                      .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

        styled_df_percent_seen = styled_df_percent_seen.set_properties(**{'text-align': 'center'}).hide_index()
        display(styled_df_percent_seen)  
       
    else:
        display(HTML('<p style="font-size:16px;">The footprint covers none of the ICOS membership countries.</p>'))
        
        
def footprint_show_percentages(footprint_code, input_footprint, fp_lat, fp_lon, return_fp=False):
    
    
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

"""
def one_or_zero_mask_x(summed_mask):
    
    #where value is greater than or equal to 1, give value 1. Otherwise give value 0. 
    summed_mask_upd=np.where(summed_mask >= 1, 1, 0)

    
    return summed_mask_upd
"""

def load_fp(station):
    
    name_load_footprint_csv='fp_' + station + '.csv'
    
    if os.path.isfile(os.path.join(folder_tool, folder_tool_fps, name_load_footprint_csv)):
        loaded_fp=loadtxt(os.path.join(folder_tool, folder_tool_fps, name_load_footprint_csv), delimiter=',')
    else:

        date_range = pd.date_range(start='2018-01-01', end='2019-01-01', freq='3H')

        #not including midnight between dec 31 and jan 1
        date_range = date_range[:-1]

        nfp, fp, lon, lat, title = read_aggreg_footprints(station, date_range)

        if fp is None:
  
            loaded_fp = None
        else:
 
           loaded_fp=fp[0]

    return loaded_fp

def return_networks(networkObj):
    
    sites_base_network = networkObj.settings['baseNetwork']
    sites_compare_network = networkObj.settings['compareNetwork']
    date_range = pd.date_range(start=(str(networkObj.settings['startYear']) + '-' + str(networkObj.settings['startMonth'])  + '-' + str(networkObj.settings['startDay'])), end=(str(networkObj.settings['endYear']) + '-' + str(networkObj.settings['endMonth'])  + '-' + str(networkObj.settings['endDay'])), freq='3H')
    threshold_value = int(networkObj.settings['percent'])
    threshold = threshold_value/100
    
    load_lat=networkObj.loadLat
    load_lon=networkObj.loadLon
    
    df_max_base_network = pd.DataFrame()
    
    index=1
    first=True
    
    list_none_footprints = []
    
    for station in sites_base_network:
        
        #if use 2018 aggregated footprint
        if min(date_range)==pd.Timestamp(2018, 1, 1, 0) and max(date_range)==pd.Timestamp(2018,12,31,0) and len(networkObj.settings['timeOfDay'])==8:
            loaded_fp=load_fp(station)
            
            if loaded_fp is None:
                list_none_footprints.append(station)
                continue
                
        #in case of user selected date range/time:
        else:

            nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
            
            if loaded_fp is None:
                
                list_none_footprints.append(station)
                continue
   
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        df_max_base_network[('fp_' + str(index))]=upd_fp_sens.flatten()

        if first==True:
            #sensitivity values
            summed_fp_sens=upd_fp_sens

            #only for the first footprint.
            first=False
        else:
            summed_fp_sens=summed_fp_sens+upd_fp_sens
 
        #for new column values
        index=index+1
    
    # make a footprint based on all max values of the combined footprints. 
    df_max_base_network = df_max_base_network[df_max_base_network.columns].max(axis=1)
    
    #in case of no available footprints for any of the selections. 
    if len(df_max_base_network.tolist()) == 0:
        
        summed_fp_sens = None   
        fp_max_base_network= None  

    else:
        
        fp_max_base_network=np.array(df_max_base_network.tolist()).reshape((len(load_lat), len(load_lon)))
        

    return fp_max_base_network
    
    
def aggreg_2018_footprints_base_network(sites_base_network, threshold, date_range = ''):
   
    #this will run once per tool run - define it here as opposed to up top so re-defined date_time 
    #every time the update button is pressed
    now = datetime.now()
    global date_time
    date_time = now.strftime("%Y%m%d_%H%M%S")
    
    load_lat=loadtxt(os.path.join(folder_tool, folder_tool_fps, 'latitude.csv'), delimiter=',')
    load_lon=loadtxt(os.path.join(folder_tool, folder_tool_fps, 'longitude.csv'), delimiter=',')
    
    df_max_base_network = pd.DataFrame()
    
    index=1
    first=True
    
    list_none_footprints = []
    for station in sites_base_network:
        
        #if use 2018 aggregated footprint
        if len(date_range)<1:

            loaded_fp=load_fp(station)
            
            if loaded_fp is None:
                list_none_footprints.append(station)
                continue
                
        #in case of user selected date range/time:
        else:
            nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
            
            if loaded_fp is None:
                
                list_none_footprints.append(station)
                continue
   
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        df_max_base_network[('fp_' + str(index))]=upd_fp_sens.flatten()

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
            
        #for new column values
        index=index+1
    
    df_max_base_network = df_max_base_network[df_max_base_network.columns].max(axis=1)
    
    #in case of no available footprints for any of the selections. 
    if len(df_max_base_network.tolist()) == 0:
        
        summed_fp_sens = None
        summed_fp_see_not_see = None    
        aggreg_fp_see_not_see = None   
        fp_max_base_network= None  

    else:
        fp_max_base_network=np.array(df_max_base_network.tolist()).reshape((len(load_lat), len(load_lon)))
        aggreg_fp_see_not_see = one_or_zero_mask_x(summed_fp_see_not_see)

    return summed_fp_sens, summed_fp_see_not_see, aggreg_fp_see_not_see, fp_max_base_network, load_lon, load_lat, list_none_footprints

def aggreg_2018_footprints_compare_network(sites_base_network, list_additional_footprints, threshold, date_range=''):
    
    load_lat=loadtxt(os.path.join(folder_tool, folder_tool_fps, 'latitude.csv'), delimiter=',')
    load_lon=loadtxt(os.path.join(folder_tool, folder_tool_fps, 'longitude.csv'), delimiter=',')
    
    df_max_compare_network = pd.DataFrame()
    
    index = 1
    first=True
    list_none_footprints_compare = []
    for station in sites_base_network:
        
        if len(date_range)<1:

            loaded_fp=load_fp(station)
            
            if loaded_fp is None:
                
                continue
                
        #in case of user selected date range/time:       
        else:
            
            nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
            
            if loaded_fp is None:

                continue
            
        #based on threshold - get 
        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)

        df_max_compare_network[('fp_' + str(index))]=upd_fp_sens.flatten()
        
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
            
        index = index+1
        
    aggreg_fp_see_not_see = one_or_zero_mask_x(summed_fp_see_not_see) 
    
    summed_fp_sens_additional = summed_fp_sens
    summed_fp_see_not_see_additional = summed_fp_see_not_see
    
    
    for station in list_additional_footprints:
            
        if len(date_range)<1:
        
            loaded_fp = load_fp(station)

            if loaded_fp is None:
                
                list_none_footprints_compare.append(station)
                continue
                
        else:
            
            nfp_not_used, loaded_fp, lon_not_used, lat_not_used, title_not_used = read_aggreg_footprints(station, date_range)
            
            if loaded_fp is None:
                list_none_footprints_compare.append(station)

                continue

        upd_fp_sens, upd_fp_see_not_see=update_footprint_based_on_threshold(loaded_fp, load_lat, load_lon, threshold)
        
        df_max_compare_network[('fp_' + str(index))]=upd_fp_sens.flatten()
        
        summed_fp_sens_additional = summed_fp_sens_additional + upd_fp_sens
        
        summed_fp_see_not_see_additional = summed_fp_see_not_see_additional + upd_fp_see_not_see
        
        index = index + 1

    df_max_compare_network = df_max_compare_network[df_max_compare_network.columns].max(axis=1)

    fp_max_compare_network=np.array(df_max_compare_network.tolist()).reshape((len(load_lat), len(load_lon)))
    
    aggreg_fp_see_not_see_additional = one_or_zero_mask_x(summed_fp_see_not_see_additional) 
   
    return summed_fp_sens_additional, summed_fp_see_not_see_additional, aggreg_fp_see_not_see_additional,fp_max_compare_network, load_lon, load_lat, list_none_footprints_compare

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


#functions for land cover breakdown 

def get_area_total_country(land_cover, country_mask):
    
    land_cover_area_total_country = (land_cover*country_mask).sum()
    
    return land_cover_area_total_country


#can pass either the seen_given see:    
def get_area_fp_country(land_cover, seen_given_see_not_see_mask):
    
    #in case of area:
    land_cover_area_fp = (land_cover*seen_given_see_not_see_mask).sum()
    
    return land_cover_area_fp

def get_sens_fp_country(land_cover, summed_fp_sens_country):
    
    land_cover_sens_fp = (land_cover*summed_fp_sens_country).sum()
    
    return land_cover_sens_fp

#summed_fp_sens: now takes the max footprint (update 2021-07-30)
def breakdown_landcover_base_network(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see, breakdown_type = 'sens', area_type='Land'):
    
    #import the necessary data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018') 
    
    list_land_cover_classes = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean, grass_shrub, other, unknown]
    
    land_cover_values = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
    
    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C', '#1964B0', '#F1932D', '#882E72','#777777']

    fp_pop = import_population_data()

    #gridarea - to calculate how much footprint covers.
    f_gridarea = cdf.Dataset(os.path.join(folder_data, 'gridareaSTILT.nc'))

    #area stored in "cell_area" in m2
    gridarea = f_gridarea.variables['cell_area'][:]

    #for aggregate graphs (all selected countries - in case than more than one country selected.
    countries = []

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
    
    area_broad_leaf_forest = [] 
    area_coniferous_forest = [] 
    area_mixed_forest = [] 
    area_ocean = [] 
    area_other = [] 
    area_grass_shrub = [] 
    area_cropland = [] 
    area_pasture = [] 
    area_urban = [] 
    area_unknown = []
    
    population_sensitivity_list = []
    population_total_list = []
    
    for area_choice in list_area_choice:
        
        country_name = dictionary_area_choice[area_choice]
        
        countries.append(country_name)
        
        list_land_cover_area_total_country = []

        list_land_cover_area_fp = []        
        
        list_land_cover_sens_fp = []    
        
        if area_type == 'Land':
            country_mask = country_masks.variables[area_choice][:,:]
         
        # in case area_type == 'Land + EEZ'
        else:
            try:
                country_mask = country_masks_eez_included.variables[area_choice][:,:]
            
            # when no eez for selected country
            except:    
                country_mask = country_masks.variables[area_choice][:,:]
    
        # m2 to km2
        country_area_grid=(gridarea*country_mask)/1000000
        country_area_total=country_area_grid.sum()
        country_area_grid_see_not_see_area = country_area_grid * aggreg_fp_see_not_see
        country_area_grid_see_not_see_area_total = country_area_grid_see_not_see_area.sum()

        seen_given_see_not_see_mask = country_mask * aggreg_fp_see_not_see
        
        summed_fp_sens_country = country_mask * summed_fp_sens

        i = 0
        
        for land_cover in list_land_cover_classes:
        
            land_cover_area_total_country = get_area_total_country(land_cover, country_mask)
            list_land_cover_area_total_country.append(land_cover_area_total_country)

            land_cover_area_fp = get_area_fp_country(land_cover, seen_given_see_not_see_mask)
            list_land_cover_area_fp.append(land_cover_area_fp)

            land_cover_sens_fp = get_sens_fp_country(land_cover, summed_fp_sens_country)
            list_land_cover_sens_fp.append(land_cover_sens_fp)
            
            # for the aggregated graphs at the end (one bar per country

            if i==0:    
                broad_leaf_forest_list.append(land_cover_sens_fp)
                area_broad_leaf_forest.append(land_cover_area_fp)
            if i==1:
                coniferous_forest_list.append(land_cover_sens_fp)
                area_coniferous_forest.append(land_cover_area_fp)
            if i==2:     
                mixed_forest_list.append(land_cover_sens_fp)
                area_mixed_forest.append(land_cover_area_fp)
            if i==3:     
                cropland_list.append(land_cover_sens_fp)
                area_cropland.append(land_cover_area_fp)
            if i==4:
                pasture_list.append(land_cover_sens_fp)
                area_pasture.append(land_cover_area_fp)            
            if i==5:     
                urban_list.append(land_cover_sens_fp)
                area_urban.append(land_cover_area_fp)
            if i==6:
                ocean_list.append(land_cover_sens_fp)
                area_ocean.append(land_cover_area_fp)  
                
            if i==7:     
                grass_shrub_list.append(land_cover_sens_fp)
                area_grass_shrub.append(land_cover_area_fp)
            if i==8:
                other_list.append(land_cover_sens_fp)
                area_other.append(land_cover_area_fp) 
            if i==9:
                unknown_list.append(land_cover_sens_fp)
                area_unknown.append(land_cover_area_fp) 
            
            i = i + 1

        
        list_land_cover_area_total_country_percent = [(value/country_area_grid_see_not_see_area_total)*100 for value in list_land_cover_area_total_country]
        
        total_sens = sum(list_land_cover_sens_fp)
        
        land_cover_sens_fp_precent = [(value/total_sens)*100 for value in list_land_cover_sens_fp]
        
        # POPULATION:  
        population_sensitivity = (fp_pop*summed_fp_sens_country).sum()
        population_sensitivity_list.append(population_sensitivity)
        
        population_total=(fp_pop*seen_given_see_not_see_mask).sum()
        population_total_list.append(population_total)

        # continue to next country in case of no area of the country touched by the fp
        if seen_given_see_not_see_mask.sum() == 0:
            continue
            
        df_landcover_breakdown = pd.DataFrame()

        if breakdown_type=='sens':

            values_by_country = list_land_cover_sens_fp

            df_landcover_breakdown['Sensitivity'] = values_by_country

            dictionary_values = {'Land cover values':land_cover_values,
                                 'Sensitivity':values_by_country,
                                 'color':colors}
            column_w_data = 'Sensitivity'

            label_yaxis = 'area in km² * (ppm /(μmol / (m²s)))'
            
            title = 'Station/network sensitivity to land cover in ' + country_name

        else:
            values_by_country = list_land_cover_area_fp

            df_landcover_breakdown['Area covered (km²)'] = values_by_country

            dictionary_values = {'Land cover values':land_cover_values,
                                 'Area covered (km²)':values_by_country,
                                 'color':colors}

            column_w_data = 'Area covered (km²)'

            label_yaxis = 'km²'
            
            title = 'Station/network sensitivity area to land cover in ' + country_name


        p = figure(x_range=land_cover_values, title=title, toolbar_location="below")

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

            df_landcover_breakdown.insert(0, 'Category', land_cover_values)

            styled_df_landcover_breakdown = (df_landcover_breakdown.style
                                          .format({column_w_data: '{:.0f}'})
                                          .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

            styled_df_landcover_breakdown= styled_df_landcover_breakdown.set_properties(**{'text-align': 'center'}).hide_index()
            display(styled_df_landcover_breakdown)  

        box_landcover = HBox([output_landcover_breakdown, output_landcover_breakdown_table])
        display(box_landcover)

    #now have data for all selected areas:
    if len(countries)>0:

        if breakdown_type == 'sens':

            title_pop = "Sensitivity to population by country"
            
            title_LC = 'Sensitivity to land cover by country'
            
            #title_LC = 'Station/network sensitivity to land cover in ' + country_name
            
            label_yaxis_pop = 'population * (ppm /(μmol / (m²s)))'
            
            label_yaxis_LC = 'area (km²) * (ppm /(μmol / (m²s)))'

            dictionary_population_by_country = {'Countries': countries,
                                 'Population': population_sensitivity_list}
            
            dictionary_landcover_by_country = {'Countries': countries,'Broad leaf forest': broad_leaf_forest_list, 'Coniferous forest': coniferous_forest_list, 'Mixed forest': mixed_forest_list,'Cropland' : cropland_list,'Pasture': pasture_list,'Urban': urban_list, 'Ocean': ocean_list, 'Grass/shrubland': grass_shrub_list, 'Other': other_list, 'Unknown': unknown_list}


        else:

            title_pop = "Total population within footprints by country"
            
            #title_LC = 'Station/network sensitivity area to land cover in ' + country_name
            
            title_LC = 'Total land cover area within footprints by country'
          
            label_yaxis_pop = 'Population count'
            
            label_yaxis_LC = 'Area (km²)'
            
            dictionary_population_by_country = {'Countries': countries,
                     'Population': population_total_list}

            dictionary_landcover_by_country = {'Countries': countries,'Broad leaf forest': area_broad_leaf_forest, 'Coniferous forest': area_coniferous_forest, 'Mixed forest': area_mixed_forest,'Cropland' : area_cropland,'Pasture': area_pasture,'Urban': area_urban, 'Ocean': area_ocean, 'Grass/shrubland': area_grass_shrub, 'Other': area_other, 'Unknown': area_unknown}

            

        p = figure(x_range=countries, title=title_LC, toolbar_location="below", tooltips="$name @Countries: @$name{0f}")

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
        p.yaxis.axis_label = label_yaxis_LC

        output_landcover_breakdown2 = Output()

        with output_landcover_breakdown2:

            output_landcover_breakdown2.clear_output()

            show(p)

        display(output_landcover_breakdown2)

        #same type of graph but for population
        p = figure(x_range=countries, title=title_pop, toolbar_location="below", tooltips="@Population{0f}")

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
    
#summed_fp_sens and summed_fp_sens_uploaded footprint: now takes the max footprint (update 2021-07-30)
def breakdown_landcover_compare_network(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see, summed_fp_sens_uploaded_fp, aggreg_fp_see_not_see_uploaded_fp, breakdown_type='sens', download_output=False, area_type='Land'):
    
    #import the necessary data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018') 

    list_land_cover_classes = [broad_leaf_forest, coniferous_forest, mixed_forest, cropland, pasture, urban, ocean, grass_shrub, other, unknown]

    
    land_cover_values = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
    
    colors = ['#4c9c5e','#CAE0AB','#90C987', '#521A13', '#F7F056', '#DC050C', '#1964B0', '#F1932D', '#882E72','#777777']
    
    colors_duplicated = ['#4c9c5e','#4c9c5e','#CAE0AB','#CAE0AB', '#90C987', '#90C987', '#521A13', '#521A13', '#F7F056', '#F7F056', '#DC050C', '#DC050C', '#1964B0',  '#1964B0', '#F1932D', '#F1932D', '#882E72', '#882E72','#777777', '#777777']

    land_cover_values_duplicated = ['Broad leaf forest', 'Broad leaf forest+', 'Coniferous forest', 'Coniferous forest+', 'Mixed forest', 'Mixed forest+', 'Cropland', 'Cropland+', 'Pasture', 'Pasture+', 'Urban', 'Urban+', 'Ocean', 'Ocean+', 'Grass/shrubland', 'Grass/shrubland+', 'Other', 'Other+', 'Unknown', 'Unknown+'] 
    
    fp_pop = import_population_data()
    
    f_gridarea = cdf.Dataset(os.path.join(folder_data, 'gridareaSTILT.nc'))

    gridarea = f_gridarea.variables['cell_area'][:]

    countries = []
    # these lists will take the values from both base and compare. 
  
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
    
    area_broad_leaf_forest = [] 
    area_coniferous_forest = [] 
    area_mixed_forest = [] 
    area_ocean = [] 
    area_other = [] 
    area_grass_shrub = [] 
    area_cropland = [] 
    area_pasture = [] 
    area_urban = [] 
    area_unknown = []
    
    population_sensitivity_list = []
    population_area_list = []
    
    count_areas=0
    
    for area_choice in list_area_choice:
        
        country_name = dictionary_area_choice[area_choice]
        
        countries.append(country_name + ' base')
        countries.append(country_name + ' compare')
        
        list_land_cover_area_fp_base = []       
        list_land_cover_area_fp_compare = []  
        
        list_land_cover_sens_fp_base = []    
        list_land_cover_sens_fp_compare = []  
        
        if area_type == 'Land':
            country_mask = country_masks.variables[area_choice][:,:]
         
        # in case area_type == 'Land + EEZ'
        else:
            try:
                country_mask = country_masks_eez_included.variables[area_choice][:,:]
            
            # when no eez for selected country
            except:    
                country_mask = country_masks.variables[area_choice][:,:]

        #area "seen" in the specific country (area_choice)
        seen_given_see_not_see_mask_base = country_mask * aggreg_fp_see_not_see
        summed_fp_sens_country_base = country_mask * summed_fp_sens
        
        seen_given_see_not_see_mask_compare = country_mask * aggreg_fp_see_not_see_uploaded_fp
        summed_fp_sens_country_compare = country_mask * summed_fp_sens_uploaded_fp
  
        i = 0

        for land_cover in list_land_cover_classes:
        
            #land_cover_area_total_country = get_area_total_country(land_cover, country_mask)
            #list_land_cover_area_total_country.append(land_cover_area_total_country)

            land_cover_area_fp_base = get_area_fp_country(land_cover, seen_given_see_not_see_mask_base)
            list_land_cover_area_fp_base.append(land_cover_area_fp_base)  
            
            land_cover_area_fp_compare = get_area_fp_country(land_cover, seen_given_see_not_see_mask_compare)
            list_land_cover_area_fp_compare.append(land_cover_area_fp_compare) 
        
            land_cover_sens_fp_base = get_sens_fp_country(land_cover, summed_fp_sens_country_base)
            list_land_cover_sens_fp_base.append(land_cover_sens_fp_base)
            
            land_cover_sens_fp_compare = get_sens_fp_country(land_cover, summed_fp_sens_country_compare)
            list_land_cover_sens_fp_compare.append(land_cover_sens_fp_compare)  
          
            # for the aggregated graphs at the end (one bar per country
            

            if i==0:    
                broad_leaf_forest_list.append(land_cover_sens_fp_base)
                broad_leaf_forest_list.append(land_cover_sens_fp_compare)
                area_broad_leaf_forest.append(land_cover_area_fp_base)
                area_broad_leaf_forest.append(land_cover_area_fp_compare)     
            if i==1:
                coniferous_forest_list.append(land_cover_sens_fp_base)
                coniferous_forest_list.append(land_cover_sens_fp_compare)
                area_coniferous_forest.append(land_cover_area_fp_base)
                area_coniferous_forest.append(land_cover_area_fp_compare)
            if i==2:     
                mixed_forest_list.append(land_cover_sens_fp_base)
                mixed_forest_list.append(land_cover_sens_fp_compare)
                area_mixed_forest.append(land_cover_area_fp_base)
                area_mixed_forest.append(land_cover_area_fp_compare)
            if i==3:     
                cropland_list.append(land_cover_sens_fp_base)
                cropland_list.append(land_cover_sens_fp_compare)
                area_cropland.append(land_cover_area_fp_base)
                area_cropland.append(land_cover_area_fp_compare)
            if i==4:
                pasture_list.append(land_cover_sens_fp_base)
                pasture_list.append(land_cover_sens_fp_compare)
                area_pasture.append(land_cover_area_fp_base)   
                area_pasture.append(land_cover_area_fp_compare) 
            if i==5:     
                urban_list.append(land_cover_sens_fp_base)
                urban_list.append(land_cover_sens_fp_compare)
                area_urban.append(land_cover_area_fp_base)
                area_urban.append(land_cover_area_fp_compare)
            if i==6:
                ocean_list.append(land_cover_sens_fp_base)
                ocean_list.append(land_cover_sens_fp_compare)
                area_ocean.append(land_cover_area_fp_base)  
                area_ocean.append(land_cover_area_fp_compare)                
            if i==7:     
                grass_shrub_list.append(land_cover_sens_fp_base)
                grass_shrub_list.append(land_cover_sens_fp_compare)
                area_grass_shrub.append(land_cover_area_fp_base)
                area_grass_shrub.append(land_cover_area_fp_compare)
            if i==8:
                other_list.append(land_cover_sens_fp_base)
                other_list.append(land_cover_sens_fp_compare)
                area_other.append(land_cover_area_fp_base) 
                area_other.append(land_cover_area_fp_compare)
            if i==9:
                unknown_list.append(land_cover_sens_fp_base)
                unknown_list.append(land_cover_sens_fp_compare)
                area_unknown.append(land_cover_area_fp_base) 
                area_unknown.append(land_cover_area_fp_compare)
   

            i = i + 1

        # POPULATION:  
        population_sensitivity_base = (fp_pop*summed_fp_sens_country_base).sum()
        population_sensitivity_list.append(population_sensitivity_base)
        population_sensitivity_compare = (fp_pop*summed_fp_sens_country_compare).sum()
        population_sensitivity_list.append(population_sensitivity_compare)
        
        population_total_base=(fp_pop*seen_given_see_not_see_mask_base).sum()
        population_area_list.append(population_total_base)
        population_total_compare =(fp_pop*seen_given_see_not_see_mask_compare).sum()
        population_area_list.append(population_total_compare)

        if seen_given_see_not_see_mask_base.sum() == 0 and seen_given_see_not_see_mask_compare.sum() == 0:
            continue
            
        count_areas = count_areas + 1
        
        #bokeh plot - one per country. Mask or sensitivity.
        df_landcover_breakdown = pd.DataFrame()

        if breakdown_type=='sens':
            
            base_compare_combined = [j for i in zip(list_land_cover_sens_fp_base,list_land_cover_sens_fp_compare) for j in i]
            
            values_by_country = base_compare_combined 

            values_by_country = [0 if math.isnan(x) or x<0 else x for x in values_by_country]

            #every second item in list (starting with the first: [::2], starting with the second: [1::2])
            base_network=values_by_country[::2]
            compare_network = values_by_country[1::2]

            change_base_compare_percent=[]
            for i in range(len(base_network)):

                if base_network[i]>0:
                    diff_base_compare = (((compare_network[i]/base_network[i])*100)-100) 

                elif compare_network[i]>0:
                    diff_base_compare = 9999 
                else:
                    diff_base_compare = 0

                change_base_compare_percent.append(diff_base_compare)

            df_landcover_breakdown['Increase sensitivity (%)'] = change_base_compare_percent

            column_w_data = 'Increase sensitivity (%)'

            compare_minus_base_for_stack = [compare - base for base, compare in zip(base_network, compare_network)]
            
            dictionary_values = {'Land cover values': land_cover_values,
                                 'Base network': base_network,
                                 'Compare network additional': compare_minus_base_for_stack}

            label_yaxis = 'km² area * (ppm /(μmol / (m²s)))'
            
            title = 'Station/network sensitivity to land cover in ' + country_name

        else:
            
            base_compare_combined = [j for i in zip(list_land_cover_area_fp_base,list_land_cover_area_fp_compare) for j in i]
            values_by_country = base_compare_combined

            base_network=values_by_country[::2]
            compare_network = values_by_country[1::2]

            change_base_compare_percent=[]
            for i in range(len(base_network)):

                if base_network[i]>0:
                    diff_base_compare = (((compare_network[i]/base_network[i])*100)-100) 

                elif compare_network[i]>0:
                    diff_base_compare = 9999 
                else:
                    diff_base_compare = 0

                change_base_compare_percent.append(diff_base_compare)

            df_landcover_breakdown['Increase area (%)'] = change_base_compare_percent

            column_w_data = 'Increase area (%)'

            compare_minus_base_for_stack = [compare - base for base, compare in zip(base_network, compare_network)]
            dictionary_values = {'Land cover values': land_cover_values,
                                 'Base network': base_network,
                                 'Compare network additional': compare_minus_base_for_stack}

            label_yaxis = 'area (km²)'
            
            title = 'Station/network sensitivity area to land cover in ' + country_name

        country_name = dictionary_area_choice[area_choice]

        p = figure(x_range=land_cover_values, title=(title), toolbar_location="below", tooltips="$name : @$name{0f}")

        p.vbar_stack(['Base network', 'Compare network additional'], x='Land cover values', width=0.5, color=['Black', 'Green'], source=dictionary_values, legend_label=['Base network', 'Compare network additional'])

        p.yaxis.axis_label = label_yaxis

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.legend.label_text_font_size = "10px"
        p.xaxis.major_label_orientation = "vertical"

        output_landcover_breakdown = Output()
        output_landcover_breakdown_table = Output()

        with output_landcover_breakdown:
            output_landcover_breakdown.clear_output()

            show(p)

        with output_landcover_breakdown_table:
            output_landcover_breakdown_table.clear_output()

            df_landcover_breakdown = df_landcover_breakdown.astype(float)


            df_landcover_breakdown.insert(0, 'Category', land_cover_values)

            styled_df_landcover_breakdown = (df_landcover_breakdown.style
                                          .format({column_w_data: '{:.0f}'})
                                          .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

            styled_df_landcover_breakdown= styled_df_landcover_breakdown.set_properties(**{'text-align': 'center'}).hide_index()
            display(styled_df_landcover_breakdown)  

        box_landcover = HBox([output_landcover_breakdown, output_landcover_breakdown_table])

        display(box_landcover)

    #now have data for all selected countries:    
    if count_areas>0:

        if breakdown_type == 'sens':

            dictionary_sensitivity_by_country = {'Countries': countries,'Broad leaf forest': broad_leaf_forest_list, 'Coniferous forest': coniferous_forest_list, 'Mixed forest': mixed_forest_list,'Cropland' : cropland_list,'Pasture': pasture_list,'Urban': urban_list, 'Ocean': ocean_list, 'Grass/shrubland': grass_shrub_list, 'Other': other_list, 'Unknown': unknown_list}

            label_yaxis = 'km² area * (ppm /(μmol / (m²s)))'

            title = "Sensitivity to land cover by country"

        else:

            dictionary_sensitivity_by_country = {'Countries': countries,'Broad leaf forest': area_broad_leaf_forest, 'Coniferous forest': area_coniferous_forest, 'Mixed forest': area_mixed_forest,'Cropland' : area_cropland,'Pasture': area_pasture,'Urban': area_urban, 'Ocean': area_ocean, 'Grass/shrubland': area_grass_shrub, 'Other': area_other, 'Unknown': area_unknown}

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

        output_landcover_breakdown_all_countries = Output()

        with output_landcover_breakdown_all_countries:

            output_landcover_breakdown_all_countries.clear_output()

            show(p)

        display(output_landcover_breakdown_all_countries)

        #same type of graph but for population
        df_population_breakdown = pd.DataFrame()
        countries_popualtion = [country[:-5] for country in countries[::2]]

        if breakdown_type == 'sens':

            compare_minus_base_for_stack = [compare - base for base, compare in zip(population_sensitivity_list[::2], population_sensitivity_list[1::2])]

            base_network=population_sensitivity_list[::2]
            compare_network = population_sensitivity_list[1::2]

            #change_base_compare_percent_pop = [(((compare_network[i]/base_network[i])*100)-100) for i in range(len(base_network))]

            change_base_compare_percent_pop=[]
            for i in range(len(base_network)):

                if base_network[i]>0:
                    diff_base_compare = (((compare_network[i]/base_network[i])*100)-100) 

                elif compare_network[i]>0:
                    diff_base_compare = 9999 
                else:
                    diff_base_compare = 0


                change_base_compare_percent_pop.append(diff_base_compare)

            df_population_breakdown['Increase population sensitivty (%)'] = change_base_compare_percent_pop
            column_w_data = 'Increase population sensitivty (%)'

            dictionary_sensitivity_population_by_country = {'Countries': countries_popualtion,
                                 'Base_network': population_sensitivity_list[::2],
                                 'Compare_network': compare_minus_base_for_stack}

            label_yaxis = 'population * (ppm /(μmol / (m²s)))'

            title = "Sensitivity to population by country"

        else:

            compare_minus_base_for_stack = [compare - base for base, compare in zip(population_area_list[::2], population_area_list[1::2])]

            base_network=population_area_list[::2]
            compare_network = population_area_list[1::2]

            change_base_compare_percent_pop=[]
            for i in range(len(base_network)):

                if base_network[i]>0:
                    diff_base_compare = (((compare_network[i]/base_network[i])*100)-100) 

                elif compare_network[i]>0:
                    diff_base_compare = 9999 
                else:
                    diff_base_compare = 0


                change_base_compare_percent_pop.append(diff_base_compare)

            df_population_breakdown['Increase population count (%)'] = change_base_compare_percent_pop

            column_w_data ='Increase population count (%)'

            dictionary_sensitivity_population_by_country = {'Countries': countries_popualtion,
                                 'Base_network': population_area_list[::2],
                                 'Compare_network': compare_minus_base_for_stack}

            label_yaxis = 'total population'

            title = "Total population within footprints by country"

        p = figure(x_range=countries_popualtion, title=title, toolbar_location="below", tooltips=[( 'Addition compare network', '@{Compare_network}{0f}'), ('Base network', '@{Base_network}{0f}')])

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
        population_by_country_table = Output()

        with population_by_country:

            population_by_country.clear_output()

            show(p)

        with population_by_country_table:

            population_by_country_table.clear_output()

            df_population_breakdown = df_population_breakdown.astype(float)

            df_population_breakdown.insert(0, 'Category', countries_popualtion)

            styled_df_population_breakdown = (df_population_breakdown.style
                                          .format({column_w_data: '{:.0f}'})
                                          .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

            styled_df_population_breakdown= styled_df_population_breakdown.set_properties(**{'text-align': 'center'}).hide_index()
            display(styled_df_population_breakdown)  

        box_population = HBox([population_by_country, population_by_country_table])

        display(box_population)

def breakdown_landcover_dataframe(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see):

    df_w_values = pd.DataFrame(columns=['Country', 'Year', 'Broad leaf forest total (km2)', 'Broad leaf forest total fp (km2)', 'Broad leaf forest total fp (km² area * (ppm /(μmol / (m²s)))', 'Coniferous forest total (km2)', 'Coniferous forest total fp (km2)', 'Coniferous forest total fp (km² area * (ppm /(μmol / (m²s)))', 'Mixed forest total (km2)', 'Mixed forest total fp (km2)', 'Mixed forest total fp (km² area * (ppm /(μmol / (m²s)))', 'Cropland total (km2)', 'Cropland total fp (km2)', 'Cropland total fp (km² area * (ppm /(μmol / (m²s)))', 'Pasture total (km2)', 'Pasture total fp (km2)', 'Pasture total fp (km² area * (ppm /(μmol / (m²s)))', 'Urban total (km2)', 'Urban total fp (km2)', 'Urban total fp (km² area * (ppm /(μmol / (m²s)))', 'Ocean total (km2)', 'Ocean total fp (km2)', 'Ocean total fp (km² area * (ppm /(μmol / (m²s)))', 'Grass/shrubland total (km2)', 'Grass/shrubland total fp (km2)', 'Grass/shrubland total fp (km² area * (ppm /(μmol / (m²s)))', 'Other total (km2)', 'Other total fp (km2)', 'Other total fp (km² area * (ppm /(μmol / (m²s)))', 'Unknown total (km2)', 'Unknown total fp (km2)', 'Unknown total fp (km² area * (ppm /(μmol / (m²s)))'])
    
    years = ['1990', '2000', '2010', '2019']
    i = 0
    for year in years:
        
        broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year=year)
        
        list_land_cover_classes = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown]
        
        #list_land_cover_names = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']
        
        for area_choice in list_area_choice:
            
            if area_type == 'Land':
                country_mask = country_masks.variables[area_choice][:,:]

            # in case area_type == 'Land + EEZ'
            else:
                try:
                    country_mask = country_masks_eez_included.variables[area_choice][:,:]

                # when no eez for selected country
                except:    
                    country_mask = country_masks.variables[area_choice][:,:]

            seen_given_see_not_see_mask = country_mask * aggreg_fp_see_not_see
            
            summed_fp_sens_country = country_mask * summed_fp_sens
            
            list_one_country_one_year = [area_choice, year]
            
            for land_cover in list_land_cover_classes:
                #country total of land cover
                land_cover_area_total_country = get_area_total_country(land_cover, country_mask)
                list_one_country_one_year.append(land_cover_area_total_country)
                
                #country total of land cover within mask area of footprint
                land_cover_area_fp = get_area_fp_country(land_cover, seen_given_see_not_see_mask)
                list_one_country_one_year.append(land_cover_area_fp)
                
                #total sensitivity to land cover within country
                land_cover_sens_total_fp = get_sens_fp_country(land_cover, summed_fp_sens_country)
                list_one_country_one_year.append(land_cover_sens_total_fp)
    
            df_w_values.loc[i] = list_one_country_one_year
            i = i + 1
   
    return df_w_values

#not updated with new country masks (not used on exploredata)
def breakdown_landcover_hilda_two_years(list_area_choice, summed_fp_sens, aggreg_fp_see_not_see, breakdown_type = 'sens', year_start='1990', year_end='2019'):

    land_cover_values = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']

    land_cover_values = ['Broad leaf forest ' + str(year_start), 'Broad leaf forest ' + str(year_end), 'Coniferous forest ' + str(year_start), 'Coniferous forest ' + str(year_end), 'Mixed forest ' + str(year_start), 'Mixed forest ' + str(year_end), 'Cropland ' + str(year_start), 'Cropland ' + str(year_end), 'Pasture ' + str(year_start), 'Pasture ' + str(year_end), 'Urban ' + str(year_start), 'Urban ' + str(year_end), 'Ocean ' + str(year_start), 'Ocean ' + str(year_end), 'Grass/shrubland ' + str(year_start), 'Grass/shrubland ' + str(year_end), 'Other ' + str(year_start), 'Other ' + str(year_end), 'Unknown ' + str(year_start), 'Unknown ' + str(year_end)]
    
    land_cover_values_simple = ['Broad leaf forest', 'Coniferous forest', 'Mixed forest', 'Cropland', 'Pasture', 'Urban', 'Ocean', 'Grass/shrubland', 'Other', 'Unknown']

    colors = ['#4c9c5e','#4c9c5e','#CAE0AB','#CAE0AB','#90C987','#90C987', '#521A13', '#521A13', '#F7F056','#F7F056', '#DC050C', '#DC050C','#1964B0','#1964B0','#F1932D','#F1932D','#882E72','#882E72', '#777777','#777777']
  

    broad_leaf_forest_start, coniferous_forest_start, mixed_forest_start, ocean_start, other_start, grass_shrub_start, cropland_start, pasture_start, urban_start, unknown_start = import_landcover_HILDA(year=year_start)
                              
    broad_leaf_forest_end, coniferous_forest_end, mixed_forest_end, ocean_end, other_end, grass_shrub_end, cropland_end, pasture_end, urban_end, unknown_end = import_landcover_HILDA(year=year_end)

    list_land_cover_classes_start = [broad_leaf_forest_start, coniferous_forest_start, mixed_forest_start, cropland_start, pasture_start, urban_start, ocean_start, grass_shrub_start, other_start, unknown_start]
    
    list_land_cover_classes_end = [broad_leaf_forest_end, coniferous_forest_end, mixed_forest_end, cropland_end, pasture_end, urban_end, ocean_end, grass_shrub_end, other_end, unknown_end]
      
    all_area_masks= Dataset(os.path.join(folder_tool, 'land_and_land_plus_eez_country_masks_icos_members.nc'))

    for area_choice in list_area_choice:
  
        country_mask = all_area_masks.variables[area_choice][:,:]
        
        seen_given_see_not_see_mask = country_mask * aggreg_fp_see_not_see
        
        summed_fp_sens_country = country_mask * summed_fp_sens

        
        list_land_cover_area_total_country_start = []
        list_land_cover_area_total_country_end = []

        list_land_cover_area_fp_start = []        
        list_land_cover_area_fp_end = []
        
        list_land_cover_sens_fp_start = []        
        list_land_cover_sens_fp_end = []

        
        for land_cover_start, land_cover_end in zip(list_land_cover_classes_start, list_land_cover_classes_end):
            
            land_cover_area_total_country_start = get_area_total_country(land_cover_start, country_mask)
            list_land_cover_area_total_country_start.append(land_cover_area_total_country_start)
 
            land_cover_area_total_country_end = get_area_total_country(land_cover_end, country_mask)
            list_land_cover_area_total_country_end.append(land_cover_area_total_country_end)
     
            land_cover_area_fp_start = get_area_fp_country(land_cover_start, seen_given_see_not_see_mask)
            list_land_cover_area_fp_start.append(land_cover_area_fp_start)
            
            land_cover_area_fp_end = get_area_fp_country(land_cover_end, seen_given_see_not_see_mask)
            list_land_cover_area_fp_end.append(land_cover_area_fp_end)
            
            
            land_cover_sens_total_fp_start = get_sens_fp_country(land_cover_start, summed_fp_sens_country)
            list_land_cover_sens_fp_start.append(land_cover_sens_total_fp_start)
            
            land_cover_sens_fp_start = get_sens_fp_country(land_cover_end, summed_fp_sens_country)
            list_land_cover_sens_fp_end.append(land_cover_sens_fp_start)
            
        list_land_cover_area_total_country_start = [0 if math.isnan(x) or x<0 else x for x in list_land_cover_area_total_country_start]
        
        list_land_cover_area_total_country_end = [0 if math.isnan(x) or x<0 else x for x in list_land_cover_area_total_country_end]

        values_diff_country = []

        for i in range(len(list_land_cover_area_total_country_start)):

            if list_land_cover_area_total_country_start[i]>0.00001:
                diff_base_compare = (((list_land_cover_area_total_country_end[i]/list_land_cover_area_total_country_start[i])*100)-100) 

            #if no sensitivty at start
            else:

                if list_land_cover_area_total_country_end[i]>0.00001:
                    diff_base_compare = 9999
                else:
                    diff_base_compare = 0

            values_diff_country.append(diff_base_compare)

        
        # analysis based on the footprints.
        if seen_given_see_not_see_mask.sum() > 0:
            
            country_name = dictionary_area_choice[area_choice]

            if breakdown_type=='sens':

                compare_values_start = list_land_cover_sens_fp_start

                compare_values_end = list_land_cover_sens_fp_end

                column_w_data = 'Sensitivity'

                label_yaxis = 'area in km² * (ppm /(μmol / (m²s)))'
                
                title = 'Station/network sensitivity to land cover in ' + country_name

            #if using the mast - then see what the area of the different land cover types are below. 
            else:

                compare_values_start = list_land_cover_area_fp_start

                compare_values_end = list_land_cover_area_fp_start

                column_w_data = 'Area'

                label_yaxis = 'km²'
                
                title = 'Station/network sensitivity area to land cover in ' + country_name


            ##### create dataframe - takes country area total of the two years, shows the difference in percent. Also showing the difference in % in terms of sensitivity (using the same footprint / network of footprints)

            start_end_combined = [sub[item] for item in range(len(compare_values_end)) for sub in [compare_values_start, compare_values_end]]

            #for the plot with both years in stacks next to each other. 
            dictionary_values = {'Land cover values':land_cover_values,
                                     column_w_data: start_end_combined,
                                     'color':colors}

            compare_values_start = [0 if math.isnan(x) or x<0 else x for x in compare_values_start]

            compare_values_end = [0 if math.isnan(x) or x<0 else x for x in compare_values_end]

            compare_values_diff = []

            for i in range(len(compare_values_start)):

                if compare_values_start[i]>0.00001:

                    diff = (((compare_values_end[i]/compare_values_start[i])*100)-100) 

                #if no sensitivty at start
                else:

                    if compare_values_end[i]>0.00001:
                        diff = 9999
                    else:
                        diff = 0

                compare_values_diff.append(diff)

            #move this to where have sensitivity info also
            df_landcover_change = pd.DataFrame()

            df_landcover_change['Category'] = land_cover_values_simple

            df_landcover_change['Area (km2) year ' + str(year_start)] = list_land_cover_area_total_country_start

            df_landcover_change['Area (km2) year ' + str(year_end)] = list_land_cover_area_total_country_end

            df_landcover_change['Difference (%)'] = values_diff_country

            if breakdown_type=='sens':
                name_diff_col = 'Difference sensitvity (%)'

            else:
                name_diff_col = 'Difference area (%)'

            df_landcover_change[name_diff_col] = compare_values_diff

            styled_df_landcover_change = (df_landcover_change.style
                                          .format({('Area (km2) year ' + str(year_start)): '{:.0f}', ('Area (km2) year ' + str(year_end)): '{:.0f}', 'Difference (%)': '{:.2f}',  name_diff_col: '{:.2f}'})

                                          .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]))

            styled_df_landcover_change = styled_df_landcover_change.set_properties(**{'text-align': 'center'}).hide_index()
            display(styled_df_landcover_change)

            p = figure(x_range=land_cover_values, title=title, toolbar_location="below", tooltips="@" + column_w_data + "{0f}")


            p.vbar(x='Land cover values', top = column_w_data, width=0.5, color='color', source=dictionary_values)

            p.yaxis.axis_label = label_yaxis

            p.y_range.start = 0
            p.x_range.range_padding = 0.1
            p.xgrid.grid_line_color = None
            p.axis.minor_tick_line_color = None
            p.outline_line_color = None

            p.legend.label_text_font_size = "10px"
            p.xaxis.major_label_orientation = "vertical"

            show(p)
    
#needs to be updated
def save_map_texts(list_footprint_choice, threshold, list_additional_footprints):

    string_station_info='The following stations 2018 footprint(s) were aggregated to generate the base network: ' 
    
    
    for station in list_footprint_choice:
        
        string_station_info+=station + ', '
        
    string_station_info = string_station_info[:-2]
    if len(list_additional_footprints)>0:
        
        string_station_info_additional='\nThe following additional stations 2018 footprint(s) compare network maps: ' 
        
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
        
    export_file=output + '/description_folder_content.txt'
    open_file= open(export_file, "w")
    open_file.write(string_station_info)
    open_file.close() 

#not used in tool on exploredata          
def export_fp(summed_fp_sens):

    np.savetxt(os.path.join(folder_tool, 'fp_export.csv'),summed_fp_sens,delimiter=',',fmt='%.15f')
    
    
#needs to be updated
def save_map_texts(list_footprint_choice, threshold, list_additional_footprints):

    string_station_info='The following stations 2018 footprint(s) were aggregated to generate the base network: ' 
    
    
    for station in list_footprint_choice:
        
        string_station_info+=station + ', '
        
    string_station_info = string_station_info[:-2]
    if len(list_additional_footprints)>0:
        
        string_station_info_additional='\nThe following additional stations 2018 footprint(s) compare network maps: ' 
        
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
        
    export_file=output + '/description_folder_content.txt'
    open_file= open(export_file, "w")
    open_file.write(string_station_info)
    open_file.close() 

def save_settings(settings, directory):

    output = os.path.join(os.path.expanduser('~'), 'output', directory, date_time)

    if not os.path.exists(output):
        os.makedirs(output)

    export_file=output + '/settings.json'

    # save settings as json file
    with open(export_file, 'w') as f:
        json.dump(settings, f, indent=4)
        
        
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
                  