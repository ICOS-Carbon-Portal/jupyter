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
from icoscp.stilt import stiltstation
import ipywidgets as widgets
from matplotlib import pyplot as plt
import network_analysis_functions
global stilt_stations
stilt_stations = stiltstation.find()
button_color_able='#4169E1'
button_color_disable='#900D09'

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
    s['signalsStations'] = stations_choice.value
    s['specificStation'] = specific_station_choice.value
    s['specificStationLat'] = stilt_stations[specific_station_choice.value]['lat']
    s['specificStationLon'] = stilt_stations[specific_station_choice.value]['lon']
    s['specificStationName'] = stilt_stations[specific_station_choice.value]['name']
    
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
    specific_station_choice.disabled = False
    update_button.disabled = False
    
    list_optional_stations = sorted([k for k, v in stilt_stations.items() if str(selected_year) in v['years'] if len(v[str(selected_year)]['months']) == 12])
    
    stations_choice.options = list_optional_stations
    
    # stations in the study
    stations = ["KRE250", "SMR125", "PAL","PUI084","UTO","OPE120","PUY","SAC100","TRN180", "GAT344", "HEL110","HPB131", 
            "JUE120","KIT200", "LIN099","OXK163","STE252","TOH147", "WES","ZSF","IPR100","LMP","CMN760","PRS","LUT",
            "BIR075","HTM150","NOR100","SVB150","JFJ", "WAO",\
           "HUN115","ARN100","LMU080","MAJ100","PSE150", "PCW150", "BIK300", "KAS", "SNZ", 
            "EST110", "LAH032", "VSD006","SSL", "FKL015", "HAC", "MHD", "MAH","VTO014", "RGL090"]
    
    pre_selection = [station for station in stations if station in list_optional_stations]
    
    stations_choice.value = pre_selection
    
    specific_station_choice.options = list_optional_stations
    specific_station_choice.value = 'HTM150'
    s_year.options = [selected_year]
    s_year.value = selected_year
    e_year.options = [selected_year]
    e_year.value = selected_year
    
    s_month.options = list(range(1,13))
    s_month.value = 1
    e_month.options = list(range(1,13))
    s_month.value = 1
    
    s_day.options = list(range(1,32))
    s_day.value = 1
    e_day.options = list(range(1,32))
    s_day.value = 1

    observe()

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
    
    header_output.clear_output()
    signals_anthro.clear_output()
    signals_bio.clear_output()
    contour_map.clear_output()
    landcover_bar.clear_output()
   
    update_button.disabled = True
    update_button.tooltip = 'Unable to run'
    update_button.style.button_color=button_color_disable
    
    global stc
    stc = get_settings()

    with signals_anthro:
        
        display(HTML('<p style="font-size:18px;"><b>Table 1 (anthropogenic signal):</b></p>')) 
        
        network_analysis_functions.signals_table_anthro(stc)

    with signals_bio:
        
        display(HTML('<p style="font-size:18px;"><b>Table 1 (biogenic GEE signal):</b><br><br>Note that this takes a while to run, especially if many stations are selected and a long date range is chosen.</p>')) 
        
        network_analysis_functions.signals_table_bio(stc, component = 'gee')
    
    with contour_map:
        
        display(HTML('<p style="font-size:18px;"><b>Figure 2a:</b><br><br>Improvements to the contour lines is extected in a coming release.</p>'))
        
        network_analysis_functions.countour_map_summer_winter(stc)

    with landcover_bar: 
        display(HTML('<p style="font-size:18px;"><b>Figure 2b:</b><br><br>Summer is on the left, winter on the right.</p>'))
        
        network_analysis_functions.land_cover_bar_graph_winter_summer(stc)
        
    update_button.disabled = False
    update_button.tooltip = 'Unable to run'
    update_button.style.button_color=button_color_able
    
#-----------widgets definition -----------------
    
style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}


header_stations = Output()
with header_stations:
    display(HTML('<p style="font-size:15px;"><b>Select stations and date range for signals table:</b><br><br>The dropdown is populated with a pre-selection of stations in the current network. Use the carbon portal on demand calculator to produce new footprints.</p>'))
    
            
year_options = Dropdown(options = [2020],
                   description = 'Select year (currently only 2020):',
                   value=None,
                   disabled= False,
                   layout = {'heigh': 'initial'},
                   style = style)

stations_choice = SelectMultiple(options = [],
                   description = 'Select stations:',
                   value=[],
                   disabled= True,
                   rows = 12,
                   layout = {'height':'initial'},
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

header_specific_station = Output()
with header_specific_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station for summer/winter comparison: </p>'))
    
specific_station_choice = Dropdown(options = [],
                   description = 'Select station:',
                   value=None,
                   disabled= True,
                   layout = {'height':'initial'},
                   style = style)

update_button = Button(description='Run selection',
                       disabled=True, # disabed until a station has been selected
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.style.button_color=button_color_able

# structure how the output should be presented 

settings_grid_2 =GridspecLayout(2, 3)
settings_grid_2[0:1, 0:1] = s_year
settings_grid_2[0:1, 1:2] = s_month
settings_grid_2[0:1, 2:3] = s_day

settings_grid_2[1:2, 0:1] = e_year
settings_grid_2[1:2, 1:2] = e_month
settings_grid_2[1:2, 2:3] = e_day 

settings_grid_3=GridspecLayout(1, 3)
settings_grid_3[0:1, 0:1] = time_selection

#Initialize form output:
form_out = Output()
#Initialize results output widgets:
header_output = Output()    
signals_anthro = Output()
signals_bio = Output()
contour_map = Output()
landcover_bar = Output()

#--------------------------------------------------------------------

# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():    

    year_options.observe(change_year_options, 'value')
    #network_choice.observe(change_network, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_month.observe(change_month_end, 'value')

    
    #Call update-function when button is clicked:
    update_button.on_click(update_func)

def unobserve():    
    #network_choice.unobserve(change_network, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')    
    e_month.unobserve(change_month_end, 'value')
    
# start observation
observe()
    
#--------------------------------------------------------------------
#Open form object:
with form_out:
    display(year_options, header_stations, stations_choice,settings_grid_2,settings_grid_3, header_specific_station, specific_station_choice, update_button, signals_anthro, signals_bio, contour_map, landcover_bar)

#Display form:
display(widgets.HTML(style_scroll),form_out)   