# -*- coding: utf-8 -*-
"""
Created on November 3 2022

@author: Ida Storm (ida.storm@nateko.lu.se)
"""

from ipywidgets import Dropdown, SelectMultiple, FileUpload, HBox, Text, VBox, Button, Output, IntText, RadioButtons,IntProgress, GridspecLayout, Checkbox, BoundedIntText, Textarea, Text
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
from datetime import datetime
import json
from icoscp.stilt import stiltstation
import ipywidgets as widgets
from matplotlib import pyplot as plt
import network_analysis_functions
import pandas as pd
global stilt_stations
stilt_stations = stiltstation.find()
button_color_able='#4169E1'

import create_network_analysis
path_network_footprints_local = 'network_footprints'

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

    s['startYear'] = s_year.value
    s['startMonth'] = s_month.value
    s['startDay'] = s_day.value
    s['endYear'] = e_year.value
    s['endMonth'] = e_month.value
    s['endDay'] = e_day.value
    s['timeOfDay'] = time_selection.value
    s['signalsStations'] = selected_stations.options
    
    return s

def date_and_time_string_for_title(stc):
    timeselect_list = nwc['timeOfDay']
    timeselect_string=[str(value) for value in timeselect_list]
    timeselect_string =':00, '.join(timeselect_string) + ':00'

    date_and_time_string=('\n' + str(nwc['startYear']) + '-' + str(nwc['startMonth']) + '-' + str(nwc['startDay'])\
                + ' to ' + str(nwc['endYear']) + '-' + str(nwc['endMonth']) + '-' \
                + str(nwc['endDay'])+ ', Hour(s): ' + timeselect_string+ '\n')
    return date_and_time_string

# what happens when a network is specified
def change_year_options(c):
    
    unobserve()
    
    selected_year = year_options.value 
    stations_choice.disabled = False
    selected_stations.disabled = False
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'
    selected_stations.options = []
    list_optional_stations = sorted([k for k, v in stilt_stations.items() if str(selected_year) in v['years'] if len(v[str(selected_year)]['months']) == 12])
    
    stations_choice.options = list_optional_stations
    
    s_year.options = [selected_year]
    s_year.value = selected_year
    e_year.options = [selected_year]
    e_year.value = selected_year
    
    s_month.options = list(range(1,13))
    s_month.value = 1
    e_month.options = list(range(1,13))
    e_month.value = 1
    
    s_day.options = list(range(1,32))
    s_day.value = 1
    e_day.options = list(range(1,32))
    e_day.value = 1

    observe()
    
def change_stations_choice(c):

    list_stations_choice = list(stations_choice.value)     
    a = set(list_stations_choice + list(selected_stations.options))    
    selected_stations.options = sorted(a)
    
def change_selected_stations(c):

    stations_choice.value = [o for o in stations_choice.value if o not in list(selected_stations.value)]
    
    list_stations = list(selected_stations.value)

    selected_stations.options = [o for o in selected_stations.options if o not in list_stations]

def change_mt(c):
    
    #the day widget populated depending on what month it is (different number of days)
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
        

def update_func(button_c):
    
    create_network_footprints.clear_output()
    create_network_footprints_representation.clear_output()
    output_name_same.clear_output()
   
    update_button.disabled = True
    update_button.tooltip = 'Unable to run'
    
    date_range_full = pd.date_range(start=(str(s_year.value) + '-' + str(s_month.value) + '-' + str(s_day.value)+ ' 00:00:00'), end=(str(e_year.value) + '-' + str(e_month.value) + '-' + str(e_day.value) + ' 21:00:00'), freq='3H')
    
    date_range = [date for date in date_range_full if date.hour in time_selection.value]
    
    stations = selected_stations.options
    
    name_save_choice = name_save.value 
    
    threshold_choice = threshold.value/100
    
    notes_choice = notes.value
    
    # check so that the input name is unique (else there would be an error)
    for root, dirs, files in os.walk(r'' + path_network_footprints_local):
        for file in files:
            if file.endswith('-checkpoint.json'):
                break

            if file == name_save_choice + '.json':
                
                with output_name_same:
                    
                    display(HTML('<p style="font-size:15px;"><mark>"' + name_save_choice +'" is the name of an existing network</mark>. Try a different name and run the tool again.</p>')) 
                    
                update_button.disabled = False
                update_button.tooltip = 'Click to start the run'
                return
                

    with create_network_footprints:
        
        display(HTML('<p style="font-size:18px;"><b>Creating network footprints (step 1/2)</b></p>')) 
        
        create_network_analysis.create_network_fps(stations, date_range, time_selection.value, name_save_choice, threshold_choice, notes_choice)

    with create_network_footprints_representation:
        
        display(HTML('<p style="font-size:18px;"><b>Establishing representation (step 2/2)</b></p>')) 
        create_network_analysis.establish_representation(date_range, name_save_choice)
        
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'

    
#-----------widgets definition -----------------
    
style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

header_stations = Output()
with header_stations:
    display(HTML('<p style="font-size:15px;">Use the carbon portal <a href= "https://stilt.icos-cp.eu/worker/" target="_blank">on demand calculator</a> to produce new footprints. Create footprints for a full year to make the station appear in the list (the station list to choose from changes depending on what year is selected).</p>'))
    
name_save = Text(
    value='',
    placeholder='name_save',
    description='Network name:',
    disabled=False,
    style=style,
    layout=layout
)
            
year_options = Dropdown(options = list(range(2007,2022)),
                   description = 'Select year:',
                   value=None,
                   disabled= False,
                   layout = layout,
                   style = style)

stations_choice = SelectMultiple(options = [],
                   description = 'Select stations:',
                   value=[],
                   disabled= True,
                   rows = 12,
                   layout = layout,
                   style = style)

selected_stations = SelectMultiple(options = [],
                   description = 'Selected (click to de-select):',
                   value=[],
                   disabled= True,
                   rows = 12,
                   layout = layout,
                   style = style)

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

threshold = BoundedIntText(
    value=50,
    min=10,
    max=100,
    step=10,
    style=style,
    layout=layout,
    description='Percent footprints:',
    disabled=False)

notes = Textarea(
    value='',
    placeholder='Optional notes about the network',
    description='Notes:',
    disabled=False,
    style = style)
 
update_button = Button(description='Run selection',
                       disabled=True, # disabed until a station has been selected
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Unable to run',)

update_button.style.button_color=button_color_able

# structure how the output should be presented 
settings_grid_0 = GridspecLayout(2, 3)
settings_grid_0[0:1, 0:1]= name_save
settings_grid_0[1:2, 0:1] = year_options

settings_grid_1 =GridspecLayout(1, 3)
settings_grid_1[0:1, 0:1] =  stations_choice
settings_grid_1[0:1, 1:2] = selected_stations

settings_grid_2 =GridspecLayout(2, 3)
settings_grid_2[0:1, 0:1] = s_year
settings_grid_2[0:1, 1:2] = s_month
settings_grid_2[0:1, 2:3] = s_day

settings_grid_2[1:2, 0:1] = e_year
settings_grid_2[1:2, 1:2] = e_month
settings_grid_2[1:2, 2:3] = e_day 

settings_grid_3=GridspecLayout(1, 3)
settings_grid_3[0:1, 0:1] = time_selection

settings_grid_4 = GridspecLayout(1, 3)
settings_grid_4[0:1, 0:1] = threshold 

#settings_grid_5 = GridspecLayout(1, 3)
#settings_grid_5[0:1, 0:1] = notes

#Initialize form output:
form_out = Output()
#Initialize results output widgets:
create_network_footprints = Output()
create_network_footprints_representation = Output()
output_name_same = Output()

#--------------------------------------------------------------------
# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():    

    year_options.observe(change_year_options, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_month.observe(change_month_end, 'value')
    stations_choice.observe(change_stations_choice, 'value')
    selected_stations.observe(change_selected_stations, 'value')
    
    #Call update-function when button is clicked:
    update_button.on_click(update_func)

def unobserve():    
    #network_choice.unobserve(change_network, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')    
    e_month.unobserve(change_month_end, 'value')
    stations_choice.unobserve(change_stations_choice, 'value')
    selected_stations.unobserve(change_selected_stations, 'value')
    
# start observation
observe()
    
#--------------------------------------------------------------------
#Open form object:
with form_out:
    display(header_stations, settings_grid_0, settings_grid_1,settings_grid_2,settings_grid_3, settings_grid_4, notes, update_button, output_name_same, create_network_footprints, create_network_footprints_representation)

#Display form:
display(widgets.HTML(style_scroll),form_out)   