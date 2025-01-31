# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 

"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Checkbox
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import network_characterization_functions as functions
import json
import network_object
from icoscp_stilt import stiltstation
import ipywidgets as widgets
from bokeh.io import show, output_notebook, reset_output
import matplotlib.pyplot as plt

# style to supress scrolling in the output 
style_scroll = """
    <style>
       .jupyter-widgets-output-area .output_scroll {
            height: unset !important;
            border-radius: unset !important;
            -webkit-box-shadow: unset !important;
            box-shadow: unset !important;
        }
        .jupyter-widgets-output-area  {
            height: auto !important;
        }
    </style>
    """

# access all stations with stiltruns (see in viewer here: https://stilt.icos-cp.eu/viewer/) 
stiltstations= stiltstation.find()

list_all_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if v['geoinfo']])
list_all_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if not v['geoinfo']]
list_all = list_all_not_located + list_all_located

list_2018_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if v['geoinfo']])
list_2018_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if not v['geoinfo']]
list_2018 = list_2018_not_located + list_2018_located 

countries = [('Albania','ALB'),('Andorra','Andorra'),('Austria','AUT'),('Belarus','BLR'),('Belgium','BEL'),('Bosnia and Herzegovina','BIH'),('Bulgaria','BGR'),('Croatia','HRV'),('Cyprus','CYP'),('Czechia','CZE'),('Denmark','DNK'),('Estonia','EST'),('Finland','FIN'),('France','FRA'),('Germany','DEU'),('Greece','GRC'),('Hungary','HUN'),('Ireland','IRL'),('Italy','ITA'),('Kosovo','XKX'),('Latvia','LVA'),('Liechtenstein','LIE'),('Lithuania','LTU'),('Luxembourg','LUX'),('Macedonia','MKD'),('Malta','MTL'),('Moldova','MDA'),('Montenegro','MNE'),('Netherlands','NLD'),('Norway','NOR'),('Poland','POL'),('Portugal','PRT'),('Republic of Serbia','SRB'),('Romania','ROU'),('San Marino','SMR'),('Slovakia','SVK'),('Slovenia','SVN'),('Spain','ESP'),('Sweden','SWE'),('Switzerland','CHE'),('United Kingdom','GBR')]

dict_countries = {'ALB':'Albania', 'Andorra':'Andorra', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium','BIH':'Bosnia and Herzegovina','BGR':'Bulgaria','HRV':'Croatia','CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LIE':'Liechtenstein','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MTL':'Malta','MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SMR':'San Marino','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}

def getSettings():

    s = {}
    
    if prepared_footprints.value:
        
        s['startYear'] = 2018
        s['startMonth'] = 1
        s['startDay'] = 1
        s['endYear'] = 2018
        s['endMonth'] = 12
        s['endDay'] = 31
        s['timeOfDay'] = [0,3,6,9,12,15,18,21]
        
    else: 
        
        s['startYear'] = s_year.value 
        s['startMonth'] = s_month.value
        s['startDay'] = s_day.value
        s['endYear'] = e_year.value
        s['endMonth'] = e_month.value
        s['endDay'] = e_day.value
        s['timeOfDay'] = list(time_selection.value)
        
    s['perpared_2018_footprints'] = prepared_footprints.value
    
    s['baseNetwork'] = [station_tuple[1] for station_tuple in selected_base_network_stations.options]
    s['compareNetwork'] = [station_tuple[1] for station_tuple in selected_compare_network_stations.options]
    s['percent'] = str(threshold_option.value)
    s['countries'] = [selected_country[1] for selected_country in list(selected_countries.options)]
    s['download'] = download_output_option.value  
    
    return s

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
    threshold_option.value = s['percent'] 
    country_options.value = s['countries']
    download_output_option.value = s['download']


def disable_enable_update_button():    

    if len(selected_base_network_stations.options)>0:
        
        if ((prepared_footprints.value==False) and ((s_year.value != e_year.value) or (s_month.value != e_month.value) or (s_day.value != e_day.value)) or (prepared_footprints.value==True)):
            update_button.disabled = False
        else:
            update_button.disabled = True              
    else:
        update_button.disabled = True

def use_icos_network_change(c):
    
    if use_icos_network.value == True:
        prepared_footprints.value= True
        
        """
    
        list_icos_stations = [k for k, v in stiltstations.items() if v['icos']]

        list_icos_stations_reduced = []
        stations_reduced = []
        for station in list_icos_stations:

            if station[0:3] not in stations_reduced:

                list_icos_stations_reduced.append(station)
                stations_reduced.append(station[0:3])

            # if there already is a station with that name
            else:

                #remove from list and replace with higher val 
                matched_station = [s for s in list_icos_stations_reduced if s[0:3] == station[0:3]][0]

                if len(station)>3 and len(matched_station)>3:
                    
                    #can only check if value in stilt station name (always the case, except CMN_test)
                    if station[3:6].isdecimal() and matched_station[3:6].isdecimal():
                        if int(station[3:6])>int(matched_station[3:6]):
                            list_icos_stations_reduced.remove(matched_station)
                            list_icos_stations_reduced.append(station)
                            stations_reduced.append(station[0:3])
                            
        """
        
        list_icos_stations_reduced = ['BIR075','GAT344', 'HEL110', 'HPB131','HTM150', 'UTO','IPR100', 'JFJ','JUE120','KIT200','KRE250','LMP','LIN099','LUT','CMN760','NOR100','OPE120','OXK163','PAL','PRS','PUI084','PUY','SMR125','SAC100','STE252','SVB150','TOH147','TRN180','WES','WAO','ZSF']

        sites_base_network_options.value = list_icos_stations_reduced


def prepare_footprints_change(c):

    selected_base_network_stations.options = () 
    selected_compare_network_stations.options = ()
    
    if prepared_footprints.value == False:
        
        use_icos_network.value = False
        
        sites_base_network_options.options = list_all
        sites_compare_network_options.options = list_all

        s_year.disabled = False
        s_month.disabled = False
        s_day.disabled = False

        e_year.disabled = False
        e_month.disabled = False
        e_day.disabled = False

        time_selection.disabled = False

    else:
       
        sites_base_network_options.options = list_2018
        sites_compare_network_options.options = list_2018

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
    compare_network_selection_tuplelist = [station for station in list_all if station[1] in compare_network_selection]
    selected_compare_network_stations.options = sorted(compare_network_selection_tuplelist)

def change_selected_compare_network_stations(c):
    
    sites_compare_network_options.value = [station for station in sites_compare_network_options.value if station not in selected_compare_network_stations.value]
    
    selected_compare_network_stations.options = [station_tuple for station_tuple in selected_compare_network_stations.options if station_tuple[1] not in selected_compare_network_stations.value]

def change_stations_base_network(c):
    
    current_selection = [station_tuple[1] for station_tuple in selected_base_network_stations.options]
    base_network_selection = set(list(sites_base_network_options.value) + current_selection)     
    base_network_selection_tuplelist = [station for station in list_all if station[1] in base_network_selection]
    selected_base_network_stations.options = sorted(base_network_selection_tuplelist)
    
    # exclude the selected base network stations from the options in the compare network list:
    if prepared_footprints.value:
        sites_compare_network_options.options = [station for station in list_2018 if not station[1] in base_network_selection]
    else:
        sites_compare_network_options.options = [station for station in list_all if not station[1] in base_network_selection]
        
    # exclude the selected base network stations from list of selected compare network stations:
    selected_compare_network_stations.options = [station for station in selected_compare_network_stations.options if not station[1] in base_network_selection]
    
    disable_enable_update_button()
    
def change_selected_base_network_stations(c):
    
    sites_base_network_options.value = [station for station in sites_base_network_options.value if station not in selected_base_network_stations.value]
    
    selected_base_network_stations.options = [station_tuple for station_tuple in selected_base_network_stations.options if station_tuple[1] not in selected_base_network_stations.value]

    # exclude the selected base network stations from the options in the compare network list:
    #sites_compare_network_options.options = [station for station in list_all if not station in selected_base_network_stations.options]
    
    if prepared_footprints.value:
        sites_compare_network_options.options = [station for station in list_2018 if not station in selected_base_network_stations.options]
    else:
        sites_compare_network_options.options = [station for station in list_all if not station in selected_base_network_stations.options]
       
    # exclude the selected base network stations from list of selected compare network stations:
    selected_compare_network_stations.options = [station for station in selected_compare_network_stations.options if not station[1] in selected_base_network_stations.options]
    
    disable_enable_update_button()

def change_countries(c):
    
    list_tuple = []
    for country_code in list(country_options.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
         
    a = set(list_tuple + list(selected_countries.options))    
    selected_countries.options = sorted(a)

def change_selected_countries(c):
    
    country_options.value = [o for o in country_options.value if o not in list(selected_countries.value)]
    list_tuple = []
    for country_code in list(selected_countries.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
    
    selected_countries.options = [o for o in selected_countries.options if o not in list_tuple]

def file_set_widgets(c):

    uploaded_file = file_name.value

    # If the content of the file is loaded as a dictionary or tuple
    # depends on the version of ipywidgets.
    # Case of Dictionary.
    if isinstance(uploaded_file, dict):
        settings_content = uploaded_file[list(uploaded_file.keys())[0]]['content']
    # Case of Tuple.
    else:
        settings_content = uploaded_file[0]['content'].tobytes()
    settings_dict = json.loads(settings_content)
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
        
#clear all the output
def clear_all_output():
    output_no_footprints.clear_output()
    output_base_footprint_information.clear_output()
    output_histogram_base.clear_output()
    output_base_network_fp_linear.clear_output()
    
    output_compare_footprint_information.clear_output()
    output_histogram_compare.clear_output()
    output_compare_network_fp_linear.clear_output()
    output_base_minus_compare.clear_output()
    output_leader_chart.clear_output()
    output_landcover_bargraph_countries.clear_output()
    output_population_bargraph_countries.clear_output()
    output_population_bokhe.clear_output()
    output_population_table.clear_output()
    output_header_landcover_section.clear_output()
    breakdown_landcover_output.clear_output()
    output_header_landcover_section.clear_output()

def clear_selection_base(button_c):
    
    sites_base_network_options.value = ()
    
def clear_selection_compare(button_c):
    
    sites_compare_network_options.value = ()

#----------- start processing -----------------

def update_func(button_c):

    update_button.disabled = True
    clear_all_output()
    
    settings = getSettings() 
    
    download_output = download_output_option.value
    
    global networkObj
    
    networkObj = network_object.NetworkObj(settings)
    
    threshold_percent = str(networkObj.settings['percent'])
    pngfile = ''
    lin_color = 'GnBu'
    log_color = 'PuBuGn'
    
    if len(networkObj.noFootprints)> 0:
        settings['noFootprints'] = networkObj.noFootprints
        no_footprints_list = [v['name'] + ' ('+ k + ')' for k, v in stiltstations.items() if k in networkObj.noFootprints]
        no_footprints_string = ", ".join(no_footprints_list)
        
        with output_no_footprints:
        
            display(HTML('<p style="font-size:16px">No footprints available for the selected date range for ' + no_footprints_string + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to generate these footprints.</p>'))
        
        all_stations = networkObj.settings['baseNetwork'] + networkObj.settings['compareNetwork']

        list_used_stations = [station for station in all_stations if station not in networkObj.noFootprints]
    
    else:
        list_used_stations = networkObj.settings['baseNetwork'] + networkObj.settings['compareNetwork']

    if len(list_used_stations) == 0:
        
        update_button.disabled = False
        return
    
    else:
        # lats' and lons' of stations:
        min_lat = min([v['lat'] for k, v in stiltstations.items() if k in list_used_stations]) 
        max_lat = max([v['lat'] for k, v in stiltstations.items() if k in list_used_stations]) 
        min_lon = min([v['lon'] for k, v in stiltstations.items() if k in list_used_stations]) 
        max_lon = max([v['lon'] for k, v in stiltstations.items() if k in list_used_stations]) 

        settings['domain'] = (min_lon, max_lon, min_lat, max_lat)

        if networkObj.baseNetwork is not None:

            histogram_base, percentile_excluded, max_original, number_cells_above = functions.histogram_fp_distribution(networkObj, fp_type= 'base')

            with output_base_footprint_information:

                display(HTML('<p style="font-size:16px;text-align:center">Base network footprint (' + threshold_percent  + '%)<br>' + str("%0.1f" % percentile_excluded) + 'th percentile of non-zero fp cells as maximum <br> Network maximum: ' + str("%0.3f" % max_original) + ' (' + str(number_cells_above) + ' cells excluded)' + '</p>'))

            with output_histogram_base:

                plt.show(histogram_base)

            with output_base_network_fp_linear:

                if download_output:
                    pngfile = 'base_footprint_linear'

                else:
                    pngfile = ''

                functions.plot_maps(networkObj.baseNetwork, networkObj.loadLon, networkObj.loadLat, linlog='linear', colors=lin_color, pngfile=pngfile, directory='network_characterization/network_characterization', unit = 'ppm /(μmol / (m²s))', vmax=networkObj.vmaxSens) 

        else:

            update_button.disabled = False
            return

        if networkObj.compareNetwork is not None:

            histogram_compare, percentile_excluded, max_original, number_cells_above = functions.histogram_fp_distribution(networkObj, fp_type='compare')

            with output_compare_footprint_information:

                display(HTML('<p style="font-size:16px;text-align:center">Compare network footprint (' + threshold_percent  + '%)<br>' + str("%0.1f" % percentile_excluded) + 'th percentile of non-zero fp cells as maximum <br> Network maximum: ' + str("%0.3f" % max_original) + ' (' + str(number_cells_above) + ' cells excluded)' + '</p>'))

            with output_histogram_compare:

                plt.show(histogram_compare)

            with output_compare_network_fp_linear: 

                if download_output:
                    pngfile = 'compare_footprint_linear'

                else:
                    pngfile = ''

                functions.plot_maps(networkObj.compareNetwork, networkObj.loadLon, networkObj.loadLat, linlog='linear', colors=lin_color, pngfile=pngfile, directory='network_characterization/network_characterization', unit = 'ppm /(μmol / (m²s))', vmax=networkObj.vmaxSens) 

            with output_base_minus_compare:
                display(HTML('<p style="font-size:16px;text-align:center">Compare network - base network</p>'))

                if download_output:
                    pngfile = 'compare_minus_base_footprint_linear'

                else:
                    pngfile = ''

                functions.plot_maps(networkObj.compareMinusBase, networkObj.loadLon, networkObj.loadLat, linlog='linear', colors=lin_color, pngfile=pngfile, directory='network_characterization/network_characterization', unit = 'ppm /(μmol / (m²s))', vmax=networkObj.vmaxSens)

        df_leader_chart_sens, original_df_leader_chart_sens = functions.leader_chart_sensitivity(networkObj)

        with output_leader_chart:

            display(HTML('<p style="font-size:16px;text-align:center">Sensitivity/km2 of network by country</p>'))

            display(df_leader_chart_sens)

            if networkObj.compareNetwork is not None:
                display(HTML('<p style="font-size:12px;text-align:left"><b>*"inf" means there is nothing to compare to.</p></b>'))

            if download_output:

                path_output= os.path.join(os.path.expanduser('~'), 'output/network_characterization/network_characterization/' + str(networkObj.dateTime))

                original_df_leader_chart_sens.to_csv(path_output + '/leader_chart.csv')

        if networkObj.compareNetwork is not None:

            with output_landcover_bargraph_countries:
                if len(networkObj.settings['countries'])>0:
                    functions.land_cover_bar_graphs_compare(networkObj)

        else:

            with output_landcover_bargraph_countries:
                if len(networkObj.settings['countries'])>0:
                    functions.land_cover_bar_graphs_base(networkObj)

            with output_population_bargraph_countries:
                if len(networkObj.settings['countries'])>0:
                    functions.population_bar_graph_base(networkObj)

        #only if choose to donwload:
        if download_output:
            functions.save_settings(settings, directory='network_characterization/network_characterization')

    update_button.disabled = False
#-----------widgets definition ----------------
    
style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

heading_network_selection = Output()

with heading_network_selection:
    display(HTML('<p style="font-size:20px;font-weight:bold;">Define station network(s)</p>'))
    
heading_perpared_footprints = Output()
    
with heading_perpared_footprints:
    
    display(HTML('<p style="font-size:14px;">Check the below box to use aggregated footprints for year 2018. Aggregated footprints have already been computed for most stations and will make the tool run fast. Checking the box will change what stations are available for selection to only include stations that has footprints for all of 2018.</p>'))
    
prepared_footprints = Checkbox(
    value=False,
    description='2018 aggregate footprint(s)',
    style=style,
    layout=layout
)

use_icos_network = Checkbox(
    value=False,
    description='Select current ICOS network',
    style=style,
    layout=layout
)

heading_sites_base_network_options = Output()

with heading_sites_base_network_options:
    display(HTML('<p style="font-size:16px;">Select stations for base network</p>'))

sites_base_network_options= SelectMultiple(
    options=list_all,
    style=style,
    layout=layout,
    rows=14,
    description='',
    disabled=False) 

sites_base_network_options.layout.margin = '0px 0px 0px 0px' #top, right, bottom, left

heading_selected_base_network_stations  = Output()
with heading_selected_base_network_stations:
    display(HTML('<p style="font-size:16px;">Current selection (click to deselect):</p>'))

selected_base_network_stations = SelectMultiple(
    options=(),
    style=style,
    layout=layout,
    rows=8,
    description='',
    disabled=False) 

selected_base_network_stations.layout.margin = '0px 0px 0px 0px'

threshold_option = BoundedIntText(
    value=50,
    min=1,
    max=99,
    step=1,
    style=style,
    layout=layout,
    description='Percent footprint(s):',
    disabled=False
)

threshold_option.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

heading_sites_compare_network_options = Output()
with heading_sites_compare_network_options:
    
    display(HTML('<p style="font-size:16px;">Select stations/points of interests for compare network (optional)</p>'))
    
heading_sites_compare_network_options.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left
    
sites_compare_network_options = SelectMultiple(options = list_all,
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
s_year = Dropdown(options = range(2006, 2022),
                  value = 2018,
                  description = 'Start Year',
                  disabled= False,
                  style=style,
                  layout=layout)

#Create a Dropdown widget with month values (start month):
s_month = Dropdown(options = range(1, 13),
                   description = 'Start Month',
                   disabled= False,
                  style=style,
                  layout=layout)

#Create a Dropdown widget with year values (end year):
e_year = Dropdown(options = range(2018, 2022),
                  value = 2018,
                  description = 'End Year',
                  disabled= False,
                  style=style,
                  layout=layout)

#Create a Dropdown widget with month values (end month):
e_month = Dropdown(options = range(1, 13),
                   description = 'End Month',
                   disabled= False,
                  style=style,
                  layout=layout)

s_day = Dropdown(options = range(1,32),
                description = 'Start Day',
                disabled = False,
                  style=style,
                  layout=layout)

e_day = Dropdown(options = range(1,32),
            description = 'End Day',
            disabled = False,
                  style=style,
                  layout=layout)

header_timeselect = Output()

with header_timeselect:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date range and hour(s) of the day for footprint aggregation:</p>'))

options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]

time_selection= SelectMultiple(
    options=options_time_selection,
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    style=style,
    description='Time of day',
    disabled=False)

heading_analysis_ancillary_data = Output()

with heading_analysis_ancillary_data:
    display(HTML('<p style="font-size:20px;font-weight:bold;"><br>Make choices for land cover and population breakdown within the network(s) (optional)</p>'))

heading_country_options = Output()
with heading_country_options:
    display(HTML('<p style="font-size:16px;">Countries of interest: </p>'))

country_options= SelectMultiple(
    options=countries,
    style=style,
    layout=layout,
    rows=10,
    description='')

country_options.layout.margin = '0px 0px 0px 0px'

heading_selected_countries = Output()
with heading_selected_countries:
    display(HTML('<p style="font-size:16px;">Current selection (click to deselect):</p>'))
    
heading_selected_countries.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

selected_countries = SelectMultiple(
    options='',
    style=style,
    layout=layout,
    rows=10,
    description='')

selected_countries.layout.margin = '0px 0px 0px 70px'


download_output_heading = Output()

with download_output_heading:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;">Download output</p>'))
      
download_output_option=RadioButtons(
        options=[('No', False), ('Yes', True)],
        description=' ',
        layout=layout)

header_filename = Output()

with header_filename:
    display(HTML('<p style="font-size:16px;font-weight:bold;">Load settings from file (optional)</p>'))


file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False,  # True to accept multiple files upload else False
    layout=layout)


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

box_selections = HBox([prepared_footprints,threshold_option])

box_country_options = VBox([heading_country_options, country_options])

box_country_selection = VBox([heading_selected_countries, selected_countries])

country_selection_combined = HBox([box_country_options, box_country_selection])

final_row = HBox([file_name, update_button])
#Add all widgets to a VBox:
form = VBox([heading_network_selection, heading_perpared_footprints, use_icos_network, box_selections, base_compare_combined, header_timeselect, time_box, time_selection, heading_analysis_ancillary_data, country_selection_combined, download_output_heading, download_output_option, header_filename, final_row])

#Initialize form output:
form_out = Output()

output_no_footprints = Output()
output_base_footprint_information = Output()
output_histogram_base = Output()
output_base_network_fp_linear = Output()

output_compare_footprint_information = Output()
output_histogram_compare = Output()
output_compare_network_fp_linear = Output()
output_base_minus_compare = Output()
output_leader_chart = Output()
output_landcover_bargraph_countries = Output()
output_population_bargraph_countries = Output()
output_population_bokhe = Output()
output_population_table = Output()

output_breakdown_countries = Output()
breakdown_landcover_output = Output()
output_header_landcover_section = Output()

#--------------------------------------------------------------------
# Observers

prepared_footprints.observe(prepare_footprints_change, 'value')
use_icos_network.observe(use_icos_network_change, 'value')

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
    
    vbox_base = VBox([output_base_footprint_information, output_histogram_base, output_base_network_fp_linear])
    
    vbox_compare = VBox([output_compare_footprint_information, output_histogram_compare, output_compare_network_fp_linear])
    
    box_base_compare = HBox([vbox_base, vbox_compare])
    
    box_difference_and_leader = HBox([output_base_minus_compare, output_leader_chart])

    h_box_population = HBox([output_population_bokhe, output_population_table])
    
    display(form, output_no_footprints,box_base_compare, box_difference_and_leader, output_landcover_bargraph_countries, output_population_bargraph_countries, h_box_population)

#Display form:
display(widgets.HTML(style_scroll),form_out)   