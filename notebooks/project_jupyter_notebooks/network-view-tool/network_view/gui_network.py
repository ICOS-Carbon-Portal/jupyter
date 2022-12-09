# -*- coding: utf-8 -*-
"""
Created on November 3 2022

@author: Ida Storm (ida.storm@nateko.lu.se)
"""

from ipywidgets import Dropdown, SelectMultiple, FileUpload, HBox, Text, VBox, Button, Output, IntText, RadioButtons,IntProgress, GridspecLayout
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
from datetime import datetime
import json
import ipywidgets as widgets
from matplotlib import pyplot as plt
import network_analysis_functions
button_color_able='#4169E1'
import pandas as pd
import datetime as dt
import numpy as np
from icoscp.stilt import stiltstation
import network_analysis_functions
stilt_stations = stiltstation.find()

path_network_footprints = '/data/project/obsnet/network_footprints'
path_network_footprints_local = 'network_view/network_footprints'
output = 'network_view/temp_output'

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

# read or set the parameters from the widgets 
def get_settings():
    s = {}
    
    # not from the user - but could make it
    s['vmaxPercentile'] = 99.9 
    
    if network_choice.value[-5:] == 'local': 
        s['networkFile'] = network_choice.value[:-6]
        s['pathFp'] = path_network_footprints_local
    else:
        s['networkFile'] = network_choice.value
        s['pathFp'] = path_network_footprints
    s['startYear'] = s_year.value
    s['startMonth'] = s_month.value
    s['startDay'] = s_day.value
    s['endYear'] = e_year.value
    s['endMonth'] = e_month.value
    s['endDay'] = e_day.value
    s['timeOfDay'] = time_selection.value
    
    if extended_network_choice.value[-5:] == 'local': 
        s['extendedNetwork'] = extended_network_choice.value[:-6]
        s['pathFpExtended'] = path_network_footprints_local
    else:
        s['extendedNetwork'] = extended_network_choice.value
        s['pathFpExtended'] = path_network_footprints
    
    json_file = s['networkFile'] + '.json'
    
    network_footprint_info = open(os.path.join(s['pathFp'], json_file))
    global network_footprint_info_load
    network_footprint_info_load = json.load(network_footprint_info)
    stations = network_footprint_info_load['stations']
    stations_lon = []
    stations_lat = []
    for footprint_station in stations:
        stations_lon.append(stilt_stations[footprint_station]['lon'])
        stations_lat.append(stilt_stations[footprint_station]['lat'])
    
    s['stationsLon'] = stations_lon
    s['stationsLat'] = stations_lat
    
    # load selected network footprint files into the object
    time_of_day = s['timeOfDay']

    s['averageFp'] = network_analysis_functions.read_aggreg_network_footprints(s)
    
    # calculate vmin and vmax values:
    df_values_fp = pd.DataFrame()
    df_values_fp['sensitivity']=s['averageFp'].flatten()

    current_network_over_zero = df_values_fp[df_values_fp['sensitivity'] > 0] 
    
    s['vmax'] = np.percentile(current_network_over_zero['sensitivity'],s['vmaxPercentile'])
    s['vmin'] = s['vmax']/100


    # extended network (if selected)
    if s['extendedNetwork'] != 'No extension':
 

        json_file = s['extendedNetwork'] + '.json'
        network_footprint_info = open(os.path.join(s['pathFpExtended'], json_file))
        extended_network_footprint_info_load = json.load(network_footprint_info)
        
        date_range = pd.date_range(dt.datetime(s['startYear'],s['startMonth'],s['startDay'],0), (dt.datetime(s['endYear'], s['endMonth'], s['endDay'], 21)), freq='3H')
        date_range_subset = [date for date in date_range if date.hour in s['timeOfDay']]
        
        date_range_extended = pd.date_range(dt.datetime(extended_network_footprint_info_load['startYear'],extended_network_footprint_info_load['startMonth'],extended_network_footprint_info_load['startDay'],0), (dt.datetime(extended_network_footprint_info_load['endYear'], extended_network_footprint_info_load['endMonth'], extended_network_footprint_info_load['endDay'], 21)), freq='3H')
        
        date_range_extended_subset =  [date for date in date_range_extended if date.hour in extended_network_footprint_info_load['timeOfDay']]
        
        extended_mismatch = [date for date in date_range_extended_subset if date in date_range_subset]
        
        if len(extended_mismatch) < len(date_range_subset):
            
            with output_extended_mismatch:
            
                display(HTML('<p style="font-size:20px;">The current and extended networks have <mark>different date ranges</mark>. Results will be generated for the current network, but missing for the section "The view from the extended selected network"<br></p>'))
                
                #update so there is no extension to avoid errors when the tool is run
                s['extendedNetwork'] = 'No extension'

        else:
            
            stations = extended_network_footprint_info_load['stations']
            stations_lon = []
            stations_lat = []
            for footprint_station in stations:
                stations_lon.append(stilt_stations[footprint_station]['lon'])
                stations_lat.append(stilt_stations[footprint_station]['lat'])

            s['averageFpExtended'] = network_analysis_functions.read_aggreg_network_footprints(s, extended = True)
            s['stationsLonExtended'] = stations_lon
            s['stationsLatExtended'] = stations_lat

    return s

def date_and_time_string_for_title(nwc):
    timeselect_list = nwc['timeOfDay']
    timeselect_string=[str(value) for value in timeselect_list]
    timeselect_string =':00, '.join(timeselect_string) + ':00'

    date_and_time_string=('\n' + str(nwc['startYear']) + '-' + str(nwc['startMonth']) + '-' + str(nwc['startDay'])\
                + ' to ' + str(nwc['endYear']) + '-' + str(nwc['endMonth']) + '-' \
                + str(nwc['endDay'])+ ', Hour(s): ' + timeselect_string+ '\n')
    return date_and_time_string

# observer functions: things that happen when specific widgets changes
# update what date range can be selected based on what footprint file was selected  
def change_network(c): 
    
    unobserve()
 
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'
    
    # access the new json file and update what is in there. 
    json_file = network_choice.value +'.json'
    
    if network_choice.value[-5:] == 'local':
        json_file = network_choice.value[:-6] + '.json'
        network_footprint_info = open(os.path.join(path_network_footprints_local, json_file))
    else:
        json_file = network_choice.value + '.json'
        network_footprint_info = open(os.path.join(path_network_footprints, json_file))
          
    global network_footprint_info_load
    
    network_footprint_info_load = json.load(network_footprint_info)

    s_year.options= [network_footprint_info_load['startYear']]
    s_year.value = network_footprint_info_load['startYear']
    e_year.options =  [network_footprint_info_load['startYear']]
    e_year.value =  network_footprint_info_load['startYear']
    
    months = list(range(network_footprint_info_load['startMonth'],network_footprint_info_load['endMonth'] + 1,1)) 
    s_month.options= months
    e_month.options = months
    s_month.value = min(months)
    e_month.value = min(months)
   
    # should also change timeselect list
    time_selection.options = network_footprint_info_load['timeOfDay']
    time_selection.value = network_footprint_info_load['timeOfDay']
    
    month_days_30=[4,6,9,11]
    month_days_31=[1,3,5,7,8,10,12]

    if not len(months) == 1:
        if s_month.value in month_days_31:
            s_day.options=list(range(1,32))
            e_day.options=list(range(1,32))
        elif s_month.value in month_days_30:
            s_day.options=list(range(1,31))
            e_day.options=list(range(1,31))
        else:
            s_day.options=list(range(1,29))  
            e_day.options=list(range(1,29)) 
            
        s_day.value = 1
        e_day.value = 1
    else:
        start_day = network_footprint_info_load['startDay']
        end_day = network_footprint_info_load['endDay']
        s_day.options=list(range(start_day,end_day+1))  
        e_day.options=list(range(start_day,end_day+1))  
        s_day.value = start_day
        e_day.value = start_day
    
    observe()
    
def change_mt(c):
    
    #the day widget populated depending on what month it is (different number of days)

    if s_month.value == max(e_month.options):
        end_day = network_footprint_info_load['endDay']
        #s_day.options = list(range(1,end_day+1))
        s_day.options = list(range(1,end_day+1))
     
    else:
        month_days_30=[4,6,9,11]
        month_days_31=[1,3,5,7,8,10,12]

        if s_month.value in month_days_31:
            s_day.options=list(range(1,32))

        elif s_month.value in month_days_30:
            s_day.options=list(range(1,31))
        else:
            s_day.options=list(range(1,29))   

        s_day.value = 1

    #when change start_month - change end day also (if same year and month OR the first time)
    if s_month.value>e_month.value:
        months = [int(x) for x in s_month.options if x >= s_month.value]                
        e_month.options=months
        e_month.value = min(months)
        
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options=day
        e_day.value = min(day)
        
    else:
        e_month_original = e_month.value
        e_month.options = s_month.options
        e_month.value = e_month_original 


def change_day(c):
    
    #when change the day... if the same month and year (start) - update
    if s_month.value==e_month.value:
        original_value = e_day.value 
        allowed_days = [int(x) for x in s_day.options if x >= s_day.value]
        e_day.options = allowed_days  
        
        if original_value in allowed_days:
            e_day.value = original_value
        else:
            e_day.value = min(allowed_days)
    
def change_month_end(c):
    
    if e_month.value == max(e_month.options):
        end_day = network_footprint_info_load['endDay']
        e_day.options = list(range(1,end_day+1))
        
    else:
    
        if e_month.value==s_month.value:
            day = [x for x in s_day.options if x >= s_day.value]
            e_day.options= day
            e_day.value = min(day)

        else:
            month_days_30=[4,6,9,11]
            month_days_31=[1,3,5,7,8,10,12]

            if e_month.value in month_days_31:
                e_day.options=list(range(1,32))

            elif e_month.value in month_days_30:
                e_day.options=list(range(1,31))

            else:
                e_day.options=list(range(1,29))          
            e_day.value = 1

        
dict_countries = {'ALB':'Albania', 'AUT':'Austria','BLR':'Belarus','BEL':'Belgium','BIH':'Bosnia and Herzegovina','BGR':'Bulgaria','HRV':'Croatia','CYP':'Cyprus','CZE':'Czechia','DNK':'Denmark','EST':'Estonia','FIN':'Finland','FRA':'France','DEU':'Germany','GRC':'Greece','HUN':'Hungary','IRL':'Ireland','ITA':'Italy','XKX':'Kosovo','LVA':'Latvia','LTU':'Lithuania','LUX':'Luxembourg','MKD':'Macedonia','MDA':'Moldova','MNE':'Montenegro','NLD':'Netherlands','NOR':'Norway','POL':'Poland','PRT':'Portugal','SRB':'Republic of Serbia','ROU':'Romania','SVK':'Slovakia','SVN':'Slovenia','ESP':'Spain','SWE':'Sweden','CHE':'Switzerland','GBR':'United Kingdom'}
        
def change_country_choice(c):
    
    list_tuple = []
    for country_code in list(country_choice.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
         
    a = set(list_tuple + list(selected_countries.options))    
    selected_countries.options = sorted(a)
        
def change_selected_countries(c):
    
    country_choice.value = [o for o in country_choice.value if o not in list(selected_countries.value)]
    list_tuple = []
    for country_code in list(selected_countries.value):
        country_text = dict_countries[country_code]
        country_tuple = (country_text, country_code)
        list_tuple.append(country_tuple)
    
    selected_countries.options = [o for o in selected_countries.options if o not in list_tuple]

def update_func(button_c):
    output_warning.clear_output()
    header_output.clear_output()
    average_map.clear_output()
    landcover_view.clear_output()
    flux_view.clear_output()
    representation.clear_output()
    output_extended_mismatch.clear_output()
   
    update_button.disabled = True
    update_button.tooltip = 'Unable to run'

    countries = [selected_country[1] for selected_country in list(selected_countries.options)]
    
    if not os.path.exists(output):
        os.makedirs(output)

    if len(countries)>18:
        with output_warning:
            display(HTML('<p style="font-size:18px;color:#900D09">Select a maximum of 18 countries (for nice output graphs).</p>')) 
            header_countries_selection.layout={'border':'3px solid #900D09'}
        
        update_button.disabled = False
        update_button.tooltip = 'Click to start the run'

        
    else:
        
        header_countries_selection.layout={'border':'0px solid #FFFFFF'}
        # create a station characterization object with everything needed to create the output
        # the object will depend on the settings specified using the widgets (get_settings())
        global nwc
        nwc = get_settings()

        date_and_time_string = date_and_time_string_for_title(nwc)

        with header_output:
            display(HTML('<p style="font-size:18px;"><b>Network name</b>: ' + network_choice.value + '<br></p>'))
            display(HTML('<p style="font-size:18px;"><b>Date range</b>: ' + date_and_time_string + '<br></p>'))

        with average_map:

            network_analysis_functions.display_selected_fp_file(nwc) 
            
            display(HTML('<p style="font-size:15px;"><b>Figure 4a: Average network footprint for the selected time-period.</b></p>'))
        
            file_path = os.path.join(output, 'average_map.png')
            if os.path.exists(file_path):      
                html_string = '<br>Access map <a href='  + file_path + ' target="_blank">here</a><br><br>'
                
                display(HTML('<p style="font-size:18px">' +  html_string))

        with landcover_view:

            network_analysis_functions.landcover_view(nwc, countries, pngfile = 'landcover_view.png', output = output)
            
            display(HTML('<p style="font-size:15px;"><b>Figure 4b: Land cover shares within the average network footprint compared to country shares of land cover for selected countries.</b></p>'))
            
            
            file_path = os.path.join(output, 'landcover_view.png')
            if os.path.exists(file_path):      
                html_string = '<br>Access graph <a href='  + file_path + ' target="_blank">here</a><br><br>'
                
                display(HTML('<p style="font-size:18px">' +  html_string))

        with flux_view:

            success = network_analysis_functions.flux_breakdown_countries_percentages(nwc, countries, pngfile='flux_view.png', output=output)
            
            # success == True in case a new graph was produced. Happens unless there are no GEE fluxes (night-time)
            if success:
                file_path = os.path.join(output, 'flux_view.png')
                if os.path.exists(file_path):      
                    html_string = '<br>Access graph <a href='  + file_path + ' target="_blank">here</a><br><br>'

                    display(HTML('<p style="font-size:18px">' +  html_string))

                with representation: 

                    network_analysis_functions.share_representaiton_table(nwc, countries, csvfile = 'representation.csv', output = output)

                    display(HTML('<p style="font-size:15px;">Data used to create <b>Figures 5b and 7b: Network representation of land cover associated fluxes (GEE). Representation is established by comparing the "network views" (the network footprints) of the fluxes to "equal views" (sensing capacity evenly distributed) of the fluxes within selected countries for the time-steps in the selected date range.</b></p>'))

                    file_path = os.path.join(output, 'representation.csv')
                    if os.path.exists(file_path):      
                        html_string = '<br>Access as csv-file <a href='  + file_path + ' target="_blank">here</a><br><br>'

                        display(HTML('<p style="font-size:18px">' +  html_string))

        update_button.disabled = False
        update_button.tooltip = 'Click to start the run'

#-----------widgets definition -----------------
    
style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

file_info = Output()

with file_info:

    display(HTML('<p style="font-size:15px;font-weight:bold;">Available networks: </p>'))
    for root, dirs, files in os.walk(r'' + path_network_footprints):
        for file in files:
            if file.endswith('.json'):
                network_footprint_info = open(os.path.join(path_network_footprints, file))
                network_footprint_info_load = json.load(network_footprint_info)

                stations_string = ', '.join([str(elem) for elem in network_footprint_info_load['stations']]) 
                months = list(range(network_footprint_info_load['startMonth'], network_footprint_info_load['endMonth'] + 1))
                months_string = ', '.join([str(month) for month in months])
                date_created = network_footprint_info_load['dateCreated']
                display(HTML('<p style="font-size:15px;"><b>Name: </b> ' + str(network_footprint_info_load['fileName']) + '<br><b>Date created: </b> ' + date_created + '<br><b>Stations: </b> ' + stations_string + '<br><b>Year: </b> ' +  str(network_footprint_info_load['startYear']) + '<br><b>Month(s): </b> ' +  months_string + '<br><b>Threshold:</b> ' +  str(network_footprint_info_load['fpPercent']*100)+ '%</p>'))


    for root, dirs, files in os.walk(r'' + path_network_footprints_local):
        first = True
        for file in files:
            if file.endswith('-checkpoint.json'):
                break
            if file.endswith('.json'):
                if first:
                    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Available locally created networks: </p>'))
                    first = False

                network_footprint_info = open(os.path.join(path_network_footprints_local, file))
                network_footprint_info_load = json.load(network_footprint_info)
                stations_string = ', '.join([str(elem) for elem in network_footprint_info_load['stations']]) 
                months = list(range(network_footprint_info_load['startMonth'], network_footprint_info_load['endMonth'] + 1))
                months_string = ', '.join([str(month) for month in months])
                date_created = network_footprint_info_load['dateCreated']
                display(HTML('<p style="font-size:15px;"><b>Name: </b> ' + str(network_footprint_info_load['fileName']) + '<br><b>Date created: </b> ' + date_created + '<br><b>Stations: </b> ' + stations_string + '<br><b>Year: </b> ' +  str(network_footprint_info_load['startYear']) + '<br><b>Month(s): </b> ' +  months_string + '<br><b>Threshold:</b> ' +  str(network_footprint_info_load['fpPercent']*100)+ '%</p>'))

    display(HTML('<p style="font-size:15px;">To analyse a <mark>different network</mark>, use the "<a href="network_view/create_network_analysis.ipynb" target="_blank">create_network_analysis</a>" notebook. The new network will automatically appear in the above list and below dropdowns once this notebook cell is run again.<br><br></p>'))
                
header_network = Output()
with header_network:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select network: </p>'))
    
# options files (select in a dropdown):
list_network_files = []
for root, dirs, files in os.walk(r'' + path_network_footprints):
    for file in files:
        if file.endswith('.json'):      
            list_network_files.append(file[:-5])
            
for root, dirs, files in os.walk(r'' + path_network_footprints_local):
    for file in files:
        if file.endswith('-checkpoint.json'):
            break
        if file.endswith('.json'):     
            list_network_files.append(file[:-5] + '_local')

network_choice = Dropdown(options = list_network_files,
                   description = 'Network name',
                   value=None,
                   disabled= False,
                   layout = layout,
                   style = style)

header_date_time = Output()
with header_date_time:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date and time: </p>'))

#Create a Dropdown widget with year values (start year):
s_year = Dropdown(options = [],
                  description = 'Start Year',
                  disabled= False,
                   layout = layout)

#Create a Dropdown widget with month values (start month):
s_month = Dropdown(options = [],
                   description = 'Start Month',
                   disabled= False,
                   layout = layout)

#Create a Dropdown widget with year values (end year):
e_year = Dropdown(options = [],
                  description = 'End Year',
                  disabled= False,
                   layout = layout)

#Create a Dropdown widget with month values (end month):
e_month = Dropdown(options = [],
                   description = 'End Month',
                   disabled= False,
                   layout = layout)

s_day = Dropdown(options = [],
                description = 'Start Day',
                disabled = False,
                layout = layout)

e_day = Dropdown(options = [],
                description = 'End Day',
                disabled = False,
                layout = layout)

time_selection= SelectMultiple(
    options=[0, 3, 6, 9, 12, 15, 18, 21],
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    description='Time of day',
    disabled=False, 
    layout = layout,
    style = style)

header_countries = Output()
with header_countries:
    display(HTML('<p style="font-size:15px;"><br><b>Select countries for the different views and representation:</b></p>'))
    
header_countries_selection = Output()
with header_countries_selection:
    display(HTML('<p style="font-size:15px;"><br>ICOS membership countries pre-selected (click to deselect):</p>'))
    
countries = [('Albania','ALB'),('Austria','AUT'),('Belarus','BLR'),('Belgium','BEL'),('Bosnia and Herzegovina','BIH'),('Bulgaria','BGR'),('Croatia','HRV'),('Cyprus','CYP'),('Czechia','CZE'),('Denmark','DNK'),('Estonia','EST'),('Finland','FIN'),('France','FRA'),('Germany','DEU'),('Greece','GRC'),('Hungary','HUN'),('Ireland','IRL'),('Italy','ITA'),('Kosovo','XKX'),('Latvia','LVA'),('Lithuania','LTU'),('Luxembourg','LUX'),('Macedonia','MKD'),('Moldova','MDA'),('Montenegro','MNE'),('Netherlands','NLD'),('Norway','NOR'),('Poland','POL'),('Portugal','PRT'),('Republic of Serbia','SRB'),('Romania','ROU'),('Slovakia','SVK'),('Slovenia','SVN'),('Spain','ESP'),('Sweden','SWE'),('Switzerland','CHE'),('United Kingdom','GBR')]

preselect = ["AUT", "BEL","CZE","DNK","FIN", "FRA","DEU","ITA","NLD","NOR", "SWE","CHE","GBR"]
countries_preselected = [country_tuple for country_tuple in countries if country_tuple[1] in preselect]

country_choice = SelectMultiple(options = countries,
                               layout = layout,
                               style = style, 
                               value=[],
                               disabled= False, 
                               rows=10)

selected_countries = SelectMultiple(options = countries_preselected, 
                                    layout =layout,
                                    style = style, 
                                    disabled= False,
                                    rows=10)

header_extended_network = Output()
with header_extended_network:
    display(HTML('<p style="font-size:15px;"><br><b>Select an extended network (optional)</b><br>Specifying an extended network will make it possible to run section 3.3. ("The view from the extended selected network")<br>The output in this section is not affected.<br></p>'))
    
list_extended_network = ['No extension'] + list_network_files
extended_network_choice = Dropdown(options = list_extended_network,
                   description = 'Extended network name',
                   value='No extension',
                   disabled= False,
                   layout = {'height':'initial'},
                   style = style)

update_button = Button(description='Run selection',
                       disabled=True, # disabed until a station has been selected
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Unable to run',)

update_button.style.button_color=button_color_able

# structure how the output should be presented 
settings_grid_1 =GridspecLayout(2, 3)

settings_grid_1[0:1, 0:1] = header_network
settings_grid_1[1:2, 0:1] = network_choice

settings_grid_2 =GridspecLayout(3, 3)
settings_grid_2[0:1, 0:1] = header_date_time
settings_grid_2[1:2, 0:1] = s_year
settings_grid_2[1:2, 1:2] = s_month
settings_grid_2[1:2, 2:3] = s_day

settings_grid_2[2:3, 0:1] = e_year
settings_grid_2[2:3, 1:2] = e_month
settings_grid_2[2:3, 2:3] = e_day 

settings_grid_3=GridspecLayout(1, 3)
settings_grid_3[0:1, 0:1] = time_selection

settings_grid_4=GridspecLayout(1, 3)
settings_grid_4[0:1, 0:1] = header_countries
settings_grid_4[0:1, 1:2] = header_countries_selection

settings_grid_5=GridspecLayout(1, 3)
settings_grid_5[0:1, 0:1] = country_choice
settings_grid_5[0:1, 1:2] = selected_countries

#Initialize form output:
form_out = Output()
#Initialize results output widgets:
output_warning = Output()
header_output = Output()    
average_map = Output()
landcover_view = Output()
flux_view = Output()
representation = Output()
output_extended_mismatch = Output()

#--------------------------------------------------------------------

# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():    

    network_choice.observe(change_network, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_month.observe(change_month_end, 'value')
    country_choice.observe(change_country_choice, 'value')
    selected_countries.observe(change_selected_countries, 'value')

    #Call update-function when button is clicked:
    update_button.on_click(update_func)

def unobserve():    
    network_choice.unobserve(change_network, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')    
    e_month.unobserve(change_month_end, 'value')
    selected_countries.unobserve(change_selected_countries, 'value')
    
# start observation
observe()
    
#--------------------------------------------------------------------
#Open form object:
with form_out:
    display(file_info, settings_grid_1,settings_grid_2,settings_grid_3, settings_grid_4, settings_grid_5, header_extended_network, extended_network_choice, update_button, output_warning, output_extended_mismatch, header_output, average_map, landcover_view, flux_view, representation)

#Display form:
display(widgets.HTML(style_scroll),form_out)   