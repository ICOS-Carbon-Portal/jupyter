# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 

"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Checkbox
import stiltStations
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import network_characterization_functions as functions

import json

stiltstations = stiltStations.getStilt()

#for base network it is only possible to choose between ICOS stations:
icos_list_2018 = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>12 if v['icos']])

icos_list = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items()])

#for the compare network any site with STILT runs is possible
#however, it must have 12 months worth of data to show up in the dropdown
all_list_2018 = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>12])

all_list = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items()])

countries = [('Albania','ALB'),('Andorra','Andorra'),('Austria','AUT'),('Belarus','BLR'),('Belgium','BEL'),('Bosnia and Herzegovina','BIH'),('Bulgaria','BGR'),('Croatia','HRV'),('Cyprus','CYP'),('Czechia','CZE'),('Denmark','DNK'),('Estonia','EST'),('Finland','FIN'),('France','FRA'),('Germany','DEU'),('Greece','GRC'),('Hungary','HUN'),('Ireland','IRL'),('Italy','ITA'),('Kosovo','XKX'),('Latvia','LVA'),('Liechtenstein','LIE'),('Lithuania','LTU'),('Luxembourg','LUX'),('Macedonia','MKD'),('Malta','MTL'),('Moldova','MDA'),('Montenegro','MNE'),('Netherlands','NLD'),('Norway','NOR'),('Poland','POL'),('Portugal','PRT'),('Republic of Serbia','SRB'),('Romania','ROU'),('San Marino','SMR'),('Slovakia','SVK'),('Slovenia','SVN'),('Spain','ESP'),('Sweden','SWE'),('Switzerland','CHE'),('United Kingdom','GBR')]

dict_countries = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium','BIH':'Bosnia and Herzegovina','BGR':'Bulgaria','HRV':'Croatia','CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LIE':'Liechtenstein','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta','MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SMR':'San Marino','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}

def set_settings(s):
    
    prepared_footprints.value= s['perpared_2018_footprints']
    
    if prepared_footprints.value == False:
        
        s_year.value = s['startYear'] 
        s_month.value = s['startMonth']
        s_day.value = s['startDay']
        e_year.value = s['endYear'] 
        e_month.value = s['endMonth']
        e_day.value = s['endDay']
        time_selection.value = s['timeOfDay']

    sites_base_network_options.value = s['baseNetwork']   
    sites_compare_network_options.value = s['compareNetwork'] 
    colorbar_choice.value = s['colorBar']
    threshold_option.value = s['percent']
    area_type.value = s['countryDefinition'] 
    country_options.value = s['countries']
    breakdown_type.value = s['weighing']
    download_output_option.value = s['download']


def disable_enable_update_button():    

    if len(selected_base_network_stations.options)>0:
        
        if ((prepared_footprints.value==False) and ((s_year.value != e_year.value) or (s_month.value != e_month.value) or (s_day.value != e_day.value)) or (prepared_footprints.value==True)):
            update_button.disabled = False
        else:
            update_button.disabled = True              
    else:
        update_button.disabled = True

        
def prepare_footprints_change(c):
    
    selected_base_network_stations.options = () 
    selected_compare_network_stations.options = ()
    
    if prepared_footprints.value == False:
        
        sites_base_network_options.options = all_list
        sites_compare_network_options.options = icos_list

        s_year.disabled = False
        s_month.disabled = False
        s_day.disabled = False

        e_year.disabled = False
        e_month.disabled = False
        e_day.disabled = False

        time_selection.disabled = False

    else:
       
        sites_base_network_options.options = all_list_2018
        sites_compare_network_options.options = icos_list_2018

        s_year.disabled = True
        s_month.disabled = True
        s_day.disabled = True

        e_year.disabled = True
        e_month.disabled = True
        e_day.disabled = True

        time_selection.disabled = True


    disable_enable_update_button()
        

def change_stations_compare_network(c):
    current_selection = [station_tuple[1] for station_tuple in selected_compare_network_stations.options]
    compare_network_selection = set(list(sites_compare_network_options.value) + current_selection)     
    compare_network_selection_tuplelist = [station for station in all_list if station[1] in compare_network_selection]
    selected_compare_network_stations.options = sorted(compare_network_selection_tuplelist)

def change_selected_compare_network_stations(c):
    
    sites_compare_network_options.value = [station for station in sites_compare_network_options.value if station not in selected_compare_network_stations.value]
    
    selected_compare_network_stations.options = [station_tuple for station_tuple in selected_compare_network_stations.options if station_tuple[1] not in selected_compare_network_stations.value]

def change_stations_base_network(c):
    
    current_selection = [station_tuple[1] for station_tuple in selected_base_network_stations.options]
    base_network_selection = set(list(sites_base_network_options.value) + current_selection)     
    base_network_selection_tuplelist = [station for station in all_list if station[1] in base_network_selection]
    selected_base_network_stations.options = sorted(base_network_selection_tuplelist)
    
    # exclude the selected base network stations from the options in the compare network list:
    sites_compare_network_options.options = [station for station in all_list if not station[1] in base_network_selection]
    
    # exclude the selected base network stations from list of selected compare network stations:
    selected_compare_network_stations.options = [station for station in selected_compare_network_stations.options if not station[1] in base_network_selection]
    
    disable_enable_update_button()
    
def change_selected_base_network_stations(c):
    
    sites_base_network_options.value = [station for station in sites_base_network_options.value if station not in selected_base_network_stations.value]
    
    selected_base_network_stations.options = [station_tuple for station_tuple in selected_base_network_stations.options if station_tuple[1] not in selected_base_network_stations.value]

    # exclude the selected base network stations from the options in the compare network list:
    sites_compare_network_options.options = [station for station in all_list if not station in selected_base_network_stations.options]
    
    # exclude the selected base network stations from list of selected compare network stations:
    selected_compare_network_stations.options = [station for station in selected_compare_network_stations.options if not station[1] in selected_base_network_stations.options]
    
    disable_enable_update_button()


def change_countries(c):
    
    #selected_countries.options = country_options.value
    list_tuple = []
    for country_code in list(country_options.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
        
    #a = set(list(country_options.value) + list(selected_countries.options))    
    a = set(list_tuple + list(selected_countries.options))    
    selected_countries.options = sorted(a)

def change_selected_countries(c):
    
    list_tuple = []
    for country_code in list(selected_countries.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
    
    #selected_countries.options = [o for o in selected_countries.options if o not in selected_countries.value]
    selected_countries.options = [o for o in selected_countries.options if o not in list_tuple]


def file_set_widgets(c):
    
    uploaded_file = file_name.value
    
    #check if there is content in the dictionary (uploaded file)
    if bool(uploaded_file):
        settings_file=uploaded_file[list(uploaded_file.keys())[0]]['content']
        settings_json = settings_file.decode('utf8').replace("'", '"')
        settings_dict = json.loads(settings_json)
        set_settings(settings_dict)
        
        
def change_yr(c):
    
    disable_enable_update_button()
    
    years = [x for x in s_year.options if x >= c['new']]
    
    e_year.options = years
        
def change_mt(c):
    disable_enable_update_button()
    #the day widget populated depending on what month it is (different number of days)
    month_days_30=[4,6,9,11]
    month_days_31=[1,3,5,7,8,10,12]

    if c['new'] in month_days_31:
        s_day.options=list(range(1,32))

    elif c['new'] in month_days_30:
        s_day.options=list(range(1,31))
    else:
        s_day.options=list(range(1,29))
    
    #when change start_month - change end month also (if same year)
    if s_year.value==e_year.value :        
        month = [int(x) for x in s_month.options if x >= c['new']]                
        e_month.options=month

    #when change start_month - change end day also (if same year and month OR the first time)
    if s_year.value==e_year.value and s_month.value==e_month.value:
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options=day
        
def change_day(c):
    disable_enable_update_button()
    
    #when change the day... if the same month and year (start) - update
    if s_year.value==e_year.value and s_month.value==e_month.value:
        if s_day.value > e_day.value:
            day = [int(x) for x in s_day.options if x >= s_day.value]
            e_day.options = day
    

def change_yr_end(c):
    disable_enable_update_button()
    
    years = [x for x in s_year.options if x >= s_year.value]
    
    e_year.options = years
   
    
    if s_year.value==e_year.value:

        month = [x for x in s_month.options if x >= s_month.value]        
        e_month.options = month

def change_month_end(c):
    disable_enable_update_button()
    
    if s_year.value==e_year.value and e_month.value==s_month.value:
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options= day
    else:
        month_days_30=[4,6,9,11]
        month_days_31=[1,3,5,7,8,10,12]

        if c['new'] in month_days_31:
            e_day.options=list(range(1,32))

        elif c['new'] in month_days_30:
            e_day.options=list(range(1,31))

        else:
            e_day.options=list(range(1,29))
           
    
def change_day_end(c):
    
    disable_enable_update_button()
        
#----------- start processing -----------------

#clear all the output
def clear_all_output():
    output_same_station_base_compare.clear_output()
    output_no_footprints.clear_output()
    output_no_footprints_compare.clear_output()
    output_summed_sens_fp.clear_output()
    output_aggreg_fp_see_not_see.clear_output()
    output_summed_fp_see_not_see.clear_output()
    output_summed_sens_fp_uploaded_fp.clear_output()
    output_aggreg_fp_see_not_see_uploaded_fp.clear_output()
    output_breakdown_countries.clear_output()
    output_header_landcover_section.clear_output()
    breakdown_landcover_output.clear_output()
    output_header_landcover_section.clear_output()
    output_aggreg_fp_see_not_see_uploaded_fp.clear_output()
    output_summed_fp_see_not_see_uploaded_fp.clear_output()

def clear_selection_base(button_c):
    
    sites_base_network_options.value = ()
    
def clear_selection_compare(button_c):
    
    sites_compare_network_options.value = ()
       
def update_func(button_c):
    
    update_button.disabled = True
    clear_all_output()
    
    if not prepared_footprints.value:
        
        date_range = pd.date_range(start=(str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value)), end=(str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value)), freq='3H')
        timeselect_list = list(time_selection.value)
        timeselect_string=[str(value) for value in timeselect_list]
        timeselect_string =':00, '.join(timeselect_string) + ':00'

        date_range = functions.date_range_hour_filtered(date_range, timeselect_list)

    else:
        date_range = ''

    sites_base_network = [station_tuple[1] for station_tuple in selected_base_network_stations.options]
    sites_compare_network=[station_tuple[1] for station_tuple in selected_compare_network_stations.options]

    threshold_percent = str(threshold_option.value)
    threshold_int = threshold_option.value/100
    
    download_output=download_output_option.value
    colorbar=colorbar_choice.value
    
    type_area = area_type.value
    
    breakdown = breakdown_type.value
    
    countries=[selected_country[1] for selected_country in list(selected_countries.options)]

    fp_combined_base_network, fp_mask_count_base_network, fp_mask_base_network, fp_max_base_network, lon, lat, list_none_footprints = functions.aggreg_2018_footprints_base_network(sites_base_network, threshold_int, date_range)
    
    
    string_list_none_footprints = ', '.join([str(elem) for elem in list_none_footprints])
 
    #in case no footprints at all in base network --> nothing after in case true
    if len(list_none_footprints) == len(sites_base_network):

        with output_no_footprints:
    
            display(HTML('<p style="font-size:16px">No footprints available for base network selection: ' + string_list_none_footprints + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to generate these footprints.</p>'))
        
        update_button.disabled = False
        
        return
    else:
      
        with output_no_footprints:
    
            if len(list_none_footprints)>0:
                
                display(HTML('<p style="font-size:16px">No footprints available for base network selection: ' + string_list_none_footprints + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to generate these footprints.</p>'))
           
    if download_output:
        
        if prepared_footprints.value:
        
            settings = {'perpared_2018_footprints': prepared_footprints.value,"baseNetwork": sites_base_network, "compareNetwork": sites_compare_network, "colorBar": colorbar_choice.value, "percent": threshold_option.value, "countryDefinition": area_type.value , "countries": countries, "weighing": breakdown_type.value, "download": download_output_option.value}
        else:
            settings = {'perpared_2018_footprints': prepared_footprints.value,'startYear': s_year.value, 'startMonth': s_month.value, 'startDay': s_day.value, 'endYear': e_year.value,'endMonth': e_month.value,'endDay': e_day.value, 'timeOfDay':list(time_selection.value), "baseNetwork": sites_base_network, "compareNetwork": sites_compare_network, "colorBar": colorbar_choice.value, "percent": threshold_option.value, "countryDefinition": area_type.value , "countries": countries, "weighing": breakdown_type.value, "download": download_output_option.value}
            

        functions.save_settings(settings, directory='network_characterization/network_characterization_2018')

    if len(sites_compare_network)>0:      
        
        fp_combined_compare_network, fp_mask_count_compare_network, fp_mask_compare_network, fp_max_compare_network, lon, lat, list_none_footprints = functions.aggreg_2018_footprints_compare_network(sites_base_network, sites_compare_network, threshold_int, date_range)
        
        string_list_none_footprints = ', '.join([str(elem) for elem in list_none_footprints])
        
        if len(list_none_footprints) == len(sites_compare_network):

            with output_no_footprints_compare:

                display(HTML('<p style="font-size:16px">No footprints available for compare network selection: ' + string_list_none_footprints + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to generate these footprints. </p>'))
            update_button.disabled = False

            return
        else:

            with output_no_footprints_compare:

                if len(list_none_footprints)>0:

                    display(HTML('<p style="font-size:16px">No footprints available for compare network selection: ' + string_list_none_footprints + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to generate these footprints. </p>'))

        vmax_see_not_see = np.max(fp_mask_count_compare_network)
        vmax_sens = np.max(fp_combined_compare_network)
        
    else:
        vmax_see_not_see= None
        vmax_sens=None

        sites_compare_network = ''
   
    with output_summed_sens_fp:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint (' + threshold_percent  + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint'
        
        else:
            pngfile = ''
            
        functions.plot_maps(fp_combined_base_network, lon, lat, linlog='', colors=colorbar, pngfile=pngfile, directory='network_characterization/network_characterization_2018', unit = 'ppm /(μmol / (m²s))', vmax=vmax_sens) 

    with output_aggreg_fp_see_not_see:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint mask (' + threshold_percent + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint_mask'

        else:
            pngfile = ''

        functions.plot_maps(fp_mask_base_network, lon, lat, vmax=1, vmin=0.001, colors=colorbar, pngfile=pngfile,directory='network_characterization/network_characterization_2018', mask=True)
        
    with output_summed_fp_see_not_see:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint mask count (' + threshold_percent + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint_mask_count'


        else:
            pngfile = ''
        #vmin - 0.001
        functions.plot_maps(fp_mask_count_base_network, lon, lat, vmax=vmax_see_not_see, vmin=0.001, colors=colorbar, pngfile=pngfile, directory='network_characterization/network_characterization_2018', unit='count')

    #should not be able to add the same stations to the compare network
    sites_compare_network_upd = []
    sites_duplicate = []
    for site in sites_compare_network:
        if site in sites_base_network:
            sites_duplicate.append(site)
            continue
        else:
            sites_compare_network_upd.append(site)
    
    if len(sites_duplicate)>0:
        
        string_same_station_base_compare = ', '.join([str(elem) for elem in sites_duplicate])
        
        with output_same_station_base_compare:
            
            #plural in output text
            if len(sites_duplicate)>1:
                display(HTML('<p style="font-size:16px">Sites selected for the compare network which are already included in the base network: ' + string_same_station_base_compare + '. These are not included in the analyzed compare network. </p>'))
            
            #singular in output text
            else:
                display(HTML('<p style="font-size:16px">Site selected for the compare network which is already included in the base network: ' + string_same_station_base_compare + '. This site is not included in the analyzed compare network. </p>'))
   
   
    sites_compare_network = sites_compare_network_upd
    
    #HERE IF there is a compare network in addition to base network
    if len(sites_compare_network)>0:

        with output_summed_sens_fp_uploaded_fp:
            
            if download_output:
                pngfile = 'compare_network_footprint'

            else:
                pngfile = ''
    
            display(HTML('<p style="font-size:16px;text-align:center">Compare network footprint (' + threshold_percent + '%)</p>'))
            
            functions.plot_maps(fp_combined_compare_network, lon, lat, linlog='', colors=colorbar,pngfile=pngfile, directory='network_characterization/network_characterization_2018', unit= 'ppm /(μmol / (m²s))')        

       
        with output_aggreg_fp_see_not_see_uploaded_fp:
            
            if download_output:
                pngfile = 'compare_network_footprint_mask'


            else:
                pngfile = ''
     
            display(HTML('<p style="font-size:16px;text-align:center">Compare network footprint mask (' + threshold_percent + '%)</p>'))

            functions.plot_maps(fp_mask_compare_network, lon, lat, vmin=0.001, colors=colorbar, pngfile=pngfile,directory='network_characterization/network_characterization_2018', mask=True)


        with output_summed_fp_see_not_see_uploaded_fp:
            
            
            if download_output:
                pngfile = 'compare_network_footprint_mask_count'


            else:
                pngfile = '' 
            
            display(HTML('<p style="font-size:16px;text-align:center;">Compare network footprint mask count (' + threshold_percent + '%)</p>'))

            functions.plot_maps(fp_mask_count_compare_network, lon, lat, vmin=1, colors=colorbar, pngfile=pngfile, directory='network_characterization/network_characterization_2018', unit='count')

        with output_breakdown_countries:

            functions.breakdown_countries_compare_network(fp_mask_base_network, fp_mask_compare_network, type_area) 

        with output_header_landcover_section:
            
            if len(countries)==0:
                
                pass
            
            else:
                display(HTML('<p style="font-size:20px;text-align:left;font-weight:bold;"><br>Land cover breakdown and population</p>'))


        with breakdown_landcover_output:
           
            
            functions.breakdown_landcover_compare_network(countries, fp_max_base_network, fp_mask_base_network, fp_max_compare_network, fp_mask_compare_network, breakdown, download_output, type_area)
            
       
    else:
        with output_breakdown_countries:
            
            
            functions.breakdown_countries_base_network(fp_mask_base_network, fp_combined_base_network, type_area) 


        with output_header_landcover_section:
            

            if len(countries)==0:
                pass
            else:
                display(HTML('<p style="font-size:20px;text-align:left;font-weight:bold;"><br>Land cover breakdown and population</p>'))


        with breakdown_landcover_output:

            functions.breakdown_landcover_base_network(countries, fp_max_base_network, fp_mask_base_network, breakdown, type_area)

    update_button.disabled = False
#-----------widgets definition ----------------
    
style_bin = {'description_width': 'initial'}


colorbar_choice_list= ['GnBu', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',\
                         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu','PuBu', 'YlGnBu', \
                         'PuBuGn', 'BuGn', 'YlGn']


heading_network_selection = Output()

with heading_network_selection:
    display(HTML('<p style="font-size:20px;font-weight:bold;">Define site network(s)</p>'))
    
heading_perpared_footprints = Output()
    
with heading_perpared_footprints:
    
    display(HTML('<p style="font-size:14px;">Check the below box to use aggregated footprints for year 2018. Aggregated footprints have already been computed for most sites and will make the tool run fast. Checking the box will change what sites are available for selection to only include sites that has footprints for all of 2018.</p>'))
    
prepared_footprints = Checkbox(
    value=False,
    description='2018 aggregate footprint(s)',
    style=style_bin
)

heading_sites_base_network_options = Output()

with heading_sites_base_network_options:
    display(HTML('<p style="font-size:16px;">Select sites for base network</p>'))

sites_base_network_options= SelectMultiple(
    options=icos_list,
    style=style_bin,
    rows=14,
    description='',
    disabled=False) 

sites_base_network_options.layout.margin = '0px 0px 0px 0px' #top, right, bottom, left

heading_selected_base_network_stations  = Output()
with heading_selected_base_network_stations:
    display(HTML('<p style="font-size:16px;">Current selection (click to deselect):</p>'))

selected_base_network_stations = SelectMultiple(
    options=(),
    style=style_bin,
    rows=8,
    description='',
    disabled=False) 

selected_base_network_stations.layout.margin = '0px 0px 0px 0px'

threshold_option = BoundedIntText(
    value=50,
    min=1,
    max=99,
    step=1,
    style=style_bin,
    description='Percent footprint(s):',
    disabled=False
)

threshold_option.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

heading_sites_compare_network_options = Output()
with heading_sites_compare_network_options:
    
    display(HTML('<p style="font-size:16px;">Select sites/points of interests for compare network (optional)</p>'))
    
heading_sites_compare_network_options.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left
    
sites_compare_network_options = SelectMultiple(options = all_list,
                                               rows=14)

sites_compare_network_options.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

heading_selected_compare_network_stations  = Output()

with heading_selected_compare_network_stations:
    display(HTML('<p style="font-size:16px;">Current selection (click to deselect):</p>'))
    
heading_selected_compare_network_stations.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left
    
selected_compare_network_stations = SelectMultiple(options = (),
                                               rows=8)

selected_compare_network_stations.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left


#Create a Dropdown widget with year values (start year):
s_year = Dropdown(options = range(2006, 2020),
                  value = 2018,
                  description = 'Start Year',
                  disabled= False,)

#Create a Dropdown widget with month values (start month):
s_month = Dropdown(options = range(1, 13),
                   description = 'Start Month',
                   disabled= False,)

#Create a Dropdown widget with year values (end year):
e_year = Dropdown(options = range(2018, 2020),
                  value = 2018,
                  description = 'End Year',
                  disabled= False,)

#Create a Dropdown widget with month values (end month):
e_month = Dropdown(options = range(1, 13),
                   description = 'End Month',
                   disabled= False,)

s_day = Dropdown(options = range(1,32),
                description = 'Start Day',
                disabled = False,)

e_day = Dropdown(options = range(1,32),
            description = 'End Day',
            disabled = False,)

header_timeselect = Output()

with header_timeselect:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date range and hour(s) of the day for footprint aggregation:</p>'))

options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]

time_selection= SelectMultiple(
    options=options_time_selection,
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    style=style_bin,
    description='Time of day',
    disabled=False)

heading_map_specifications = Output()

with heading_map_specifications:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;"><br>Map settings</p>'))
    
colorbar_choice = Dropdown(
    description='Colorbar:', 
    style=style_bin,
    options=colorbar_choice_list,
    disabled=False,
)

heading_analysis_ancillary_data = Output()

with heading_analysis_ancillary_data:
    display(HTML('<p style="font-size:20px;font-weight:bold;"><br>Make choices for land cover and population breakdown within the network(s) (optional)</p>'))

heading_country_options = Output()
with heading_country_options:
    display(HTML('<p style="font-size:16px;">Countries of interest: </p>'))

country_options= SelectMultiple(
    options=countries,
    style=style_bin,
    rows=10,
    description='')

country_options.layout.margin = '0px 0px 0px 0px'

heading_selected_countries = Output()
with heading_selected_countries:
    display(HTML('<p style="font-size:16px;">Current selection (click to deselect):</p>'))
    
heading_selected_countries.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

selected_countries = SelectMultiple(
    options='',
    style=style_bin,
    rows=10,
    description='')

selected_countries.layout.margin = '0px 0px 0px 70px'

heading_area_type = Output()
with heading_area_type:
    display(HTML('<p style="font-size:14px;">Choose between getting the land cover<br>breakdown of the land covered, or to include<br>the EEZ (exclusive economic zone): </p>'))

heading_area_type.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

area_type=RadioButtons(
        options=['Land', 'Land + EEZ'],
        value='Land',
        description=' ')

area_type.layout.margin = '0px 0px 0px 50px' #top, right, bottom, left

heading_breakdown_choice = Output()
with heading_breakdown_choice:
    display(HTML('<p style="font-size:14px;">Choose between using the footprint masks and<br>sensitivity weighted footprints to compute the<br>ancillary data values:</p>'))

heading_breakdown_choice.layout.margin = '0px 0px 0px 0px' #top, right, bottom, left

breakdown_type=RadioButtons(
        options=[('Footprint', 'sens'), ('Footprint mask', 'mask')],
        value='sens',
        description=' ')

download_output_heading = Output()

with download_output_heading:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;">Download output</p>'))
      
download_output_option=RadioButtons(
        options=[('No', False), ('Yes', True)],
        description=' ')

header_filename = Output()

with header_filename:
    display(HTML('<p style="font-size:16px;font-weight:bold;">Load settings from file (optional)</p>'))


file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)


#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.layout.margin = '0px 0px 0px 160px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

box_base_network = VBox([heading_sites_base_network_options, sites_base_network_options, heading_selected_base_network_stations, selected_base_network_stations])
box_compare_network = VBox([heading_sites_compare_network_options, sites_compare_network_options, heading_selected_compare_network_stations, selected_compare_network_stations])

base_compare_combined = HBox([box_base_network, box_compare_network])

year_box = VBox([s_year, e_year])
month_box = VBox([s_month, e_month])
day_box = VBox([s_day, e_day])

#the two vertical boxes next to each other in a horizontal box
#Add both time-related VBoxes to a HBox:
time_box = HBox([year_box, month_box, day_box])

box_map_settings = HBox([colorbar_choice, threshold_option])

box_country_options = VBox([heading_country_options, country_options])

box_country_selection = VBox([heading_selected_countries, selected_countries])

country_selection_combined = HBox([box_country_options, box_country_selection])

breakdown_choice = VBox([heading_breakdown_choice, breakdown_type])

area_type_choice = VBox([heading_area_type, area_type])

box_additional_selections_combined = HBox([breakdown_choice, area_type_choice])

final_row = HBox([file_name, update_button])
#Add all widgets to a VBox:
form = VBox([heading_network_selection, heading_perpared_footprints, prepared_footprints, base_compare_combined, header_timeselect, time_box, time_selection, heading_map_specifications, box_map_settings, heading_analysis_ancillary_data, country_selection_combined, box_additional_selections_combined, download_output_heading, download_output_option, header_filename, final_row])

#Initialize form output:
form_out = Output()

output_same_station_base_compare = Output()
output_no_footprints = Output()
output_no_footprints_compare = Output()
output_summed_sens_fp = Output()
output_summed_sens_fp_uploaded_fp = Output()

output_summed_fp_see_not_see = Output()
output_summed_fp_see_not_see_uploaded_fp = Output()

output_aggreg_fp_see_not_see = Output()
output_aggreg_fp_see_not_see_uploaded_fp = Output()
output_breakdown_countries = Output()
breakdown_landcover_output = Output()
output_header_landcover_section = Output()

#--------------------------------------------------------------------
# Observers

prepared_footprints.observe(prepare_footprints_change, 'value')

sites_base_network_options.observe(change_stations_base_network, 'value')
selected_base_network_stations.observe(change_selected_base_network_stations, 'value')

sites_compare_network_options.observe(change_stations_compare_network, 'value')
selected_compare_network_stations.observe(change_selected_compare_network_stations, 'value')

s_year.observe(change_yr, 'value')
s_month.observe(change_mt, 'value')    
s_day.observe(change_day, 'value')
e_year.observe(change_yr_end, 'value')
e_month.observe(change_month_end, 'value')
e_day.observe(change_day_end, 'value')

country_options.observe(change_countries, 'value')
selected_countries.observe(change_selected_countries, 'value')

file_name.observe(file_set_widgets, 'value')

update_button.on_click(update_func)

#--------------------------------------------------------------------

#Open form object:
with form_out:

    if 'output_summed_sens_fp_uploaded_fp' in locals():
        
        box_footprints_sens = HBox([output_summed_sens_fp, output_summed_sens_fp_uploaded_fp])
        box_footprints_summed = HBox([output_summed_fp_see_not_see, output_summed_fp_see_not_see_uploaded_fp])
        box_footprints_aggreg = HBox([output_aggreg_fp_see_not_see, output_aggreg_fp_see_not_see_uploaded_fp])

        display(form, output_same_station_base_compare, output_no_footprints, output_no_footprints_compare, box_footprints_sens, box_footprints_summed, box_footprints_aggreg, output_breakdown_countries, output_header_landcover_section, breakdown_landcover_output)
        
    else:
        
        display(form, output_same_station_base_compare, output_no_footprints, output_summed_sens_fp, output_summed_fp_see_not_see, output_aggreg_fp_see_not_see, output_breakdown_countries, output_header_landcover_section, breakdown_landcover_output)



#Display form:
display(form_out)    