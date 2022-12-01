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
import create_network_analysis
stilt_stations = stiltstation.find()
button_color_able='#4169E1'
button_color_disable='#900D09'

path_network_footprints = '/data/project/obsnet/network_footprints'
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

style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

file_info = Output()
with file_info:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Available network footprint files: </p>'))
    for root, dirs, files in os.walk(r'' + path_network_footprints):
        for file in files:
            if file.endswith('.json'):
                network_footprint_info = open(os.path.join(path_network_footprints, file))
                network_footprint_info_load = json.load(network_footprint_info)

                stations_string = ', '.join([str(elem) for elem in network_footprint_info_load['stations']]) 
                months = list(range(network_footprint_info_load['startMonth'], network_footprint_info_load['endMonth'] + 1))
                date_created = network_footprint_info_load['dateCreated']
                display(HTML('<p style="font-size:15px;"><b>Name: </b> ' + str(network_footprint_info_load['fileName']) + '<br><b>Date created: </b> ' + date_created + '<br><b>Stations: </b> ' + stations_string + '<br><b>Year: </b> ' +  str(network_footprint_info_load['startYear']) + '<br><b>Month(s): </b> ' +  str(months)+ '<br><b>Threshold:</b> ' +  str(network_footprint_info_load['fpPercent']*100)+ '%</p>'))

    for root, dirs, files in os.walk(r'' + path_network_footprints_local):
        first = True
        for file in files:
            if file.endswith('-checkpoint.json'):
                break
            if file.endswith('.json'):
                if first:
                    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Available local network footprint files: </p>'))
                    first = False
                network_footprint_info = open(os.path.join(path_network_footprints_local, file))
                network_footprint_info_load = json.load(network_footprint_info)
                stations_string = ', '.join([str(elem) for elem in network_footprint_info_load['stations']]) 
                months = list(range(network_footprint_info_load['startMonth'], network_footprint_info_load['endMonth'] + 1))
                date_created = network_footprint_info_load['dateCreated']
                display(HTML('<p style="font-size:15px;"><b>Name: </b> ' + str(network_footprint_info_load['fileName']) + '<br><b>Date created: </b> ' + date_created + '<br><b>Stations: </b> ' + stations_string + '<br><b>Year: </b> ' +  str(network_footprint_info_load['startYear']) + '<br><b>Month(s): </b> ' +  str(months)+ '<br><b>Threshold:</b> ' +  str(network_footprint_info_load['fpPercent']*100)+ '%</p>'))


name_save = Text(
            value='',
            placeholder='name_save',
            description='Network name:',
            disabled=False,
            style=style)

network_choice = Dropdown(options = list_network_files,
                   description = 'Network footprint folder',
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


notes = Textarea(
        value='',
        placeholder='Notes about network',
        description='Notes:',
        disabled=False,
        style = style)

update_button = Button(description='Run selection',
                   disabled=False, # disabed until a station has been selected
                   button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                   tooltip='Click me',)

update_button.style.button_color='#4169E1'

def change_network_choice(c):

    stations_choice.disabled = False
    selected_stations.disabled = False

    json_file = network_choice.value +'.json'

    if network_choice.value[-5:] == 'local':
        json_file = network_choice.value[:-6] + '.json'
        network_footprint_info = open(os.path.join(path_network_footprints_local, json_file))
    else:
        json_file = network_choice.value + '.json'
        network_footprint_info = open(os.path.join(path_network_footprints, json_file))

    global network_footprint_info_load

    network_footprint_info_load = json.load(network_footprint_info)

    selected_year = network_footprint_info_load['startYear']

    stations = network_footprint_info_load['stations']

    list_optional_stations = sorted([k for k, v in stilt_stations.items() if str(selected_year) in v['years'] if len(v[str(selected_year)]['months']) == 12 if k not in stations])

    stations_choice.options = list_optional_stations

def change_stations_choice(c):

    list_stations_choice = list(stations_choice.value)     
    a = set(list_stations_choice + list(selected_stations.options))    
    selected_stations.options = sorted(a)

def change_selected_stations(c):

    stations_choice.value = [o for o in stations_choice.value if o not in list(selected_stations.value)]

    list_stations = list(selected_stations.value)

    selected_stations.options = [o for o in selected_stations.options if o not in list_stations]


def update_func(button_c):

    output_name_same.clear_output()
    output_create_network.clear_output()
    update_button.disabled = True

    stations = list(selected_stations.options)
    
    name_save_choice = name_save.value
    
    # check so that the input name is unique (else there would be an error)
    for root, dirs, files in os.walk(r'' + path_network_footprints_local):
        for file in files:
            if file.endswith('-checkpoint.json'):
                break

            if file == name_save_choice + '.json':
                
                with output_name_same:
                    
                    display(HTML('<p style="font-size:15px;"><mark>"' + name_save_choice +'" is the name of an existing network</mark>. Try a different name and run the tool again.</p>')) 
                    
                update_button.disabled = False
                update_button.tooltip = 'Unable to run'
                update_button.style.button_color=button_color_able
                return
    
    with output_create_network:

        create_network_analysis.create_network_fps_by_extension(stations, network_choice.value, name_save_choice, notes.value)

    update_button.disabled = False

network_choice.observe(change_network_choice, 'value')
stations_choice.observe(change_stations_choice, 'value')
selected_stations.observe(change_selected_stations, 'value')
update_button.on_click(update_func)

settings_grid =GridspecLayout(2, 3)

settings_grid[0:1, 0:1] =  name_save
settings_grid[1:2, 0:1] =  network_choice

settings_grid_1 =GridspecLayout(1, 3)
settings_grid_1[0:1, 0:1] =  stations_choice
settings_grid_1[0:1, 1:2] = selected_stations

form_out = Output()
output_create_network = Output()
output_name_same = Output()

with form_out:

    display(file_info, settings_grid, settings_grid_1, notes, update_button, output_name_same, output_create_network)

display(form_out)