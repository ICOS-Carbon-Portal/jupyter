# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 
"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, RadioButtons,IntProgress,IntSlider, GridspecLayout, Text, BoundedFloatText, FileUpload, Checkbox, BoundedIntText

import stiltStations
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation

import radiocarbon_functions
import radiocarbon_object_cp


import os
import matplotlib.pyplot as plt

from datetime import datetime
import json


## Global variables
#---------------------------------------------------------
# create a dict with all stiltstations
stiltstations = stiltStations.getStilt()

# create a list (tuple) for the dropdown list of stations
icoslist = sorted([(v['name'],k) for k,v in stiltstations.items() if v['icos']])

icoslist.sort(key=lambda x:x[0])

#---------------------------------------------------------

# read or set the parameters

def getSettings():
    #s = settings.getDict()    
    s = {}
    
    try:
        s['stationCode'] = station_choice_model.value
        if stiltstations[s['stationCode']]['icos']:
            s['icos'] = cpstation.get(s['stationCode'][0:3].upper()).info()
        s['stilt'] = stiltstations[s['stationCode']]
        s['timeOfDay'] = time_selection.value
        s['backgroundFilename'] = background_choice.value
        s['downloadOption'] = download_choice.value
        
        s['samplingHeightMeas'] = station_choice_meas.value['sampling_height']

    except:
        
        return    
    
    return s

def set_settings(s):
    
    #error here
    station_choice_meas.value = {'station_code': s['stationCode'][0:3], 'sampling_height': s['samplingHeightMeas']}
    #station_choice_meas.value = s['stationCode'][0:3]  
    station_choice_model.value = s['stationCode']
    time_selection.value = s['timeOfDay']
    
    background_choice.value = s['backgroundFilename']
    download_choice.value = s['downloadOption']

       

#----------- start processing -----------------

def file_set_widgets(c):
    
    uploaded_file = file_name.value
    
    #check if there is content in the dictionary (uploaded file)
    if bool(uploaded_file):
        settings_file=uploaded_file[list(uploaded_file.keys())[0]]['content']
        settings_json = settings_file.decode('utf8').replace("'", '"')
        settings_dict = json.loads(settings_json)
        set_settings(settings_dict)
    

def updateProgress(f, desc=''):
    # custom progressbar updates
    f.value += 1
    if not desc:
        f.description = 'step ' + str(f.value) + '/' + str(f.max)
    else:
        f.description = str(desc)
        


def change_meas_station(c):

    meas_station=station_choice_meas.value['station_code']

    matching_stiltruns = [(widget_value, station_code) for widget_value, station_code in icoslist if meas_station in station_code]

    station_choice_model.options=matching_stiltruns

style_bin = {'description_width': 'initial'}

header_station = Output()
with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station (meas): </p>'))

#depending on what is available at the carbon portal
stations_with_data = radiocarbon_functions.list_station_tuples_w_radiocarbon_data()

station_choice_meas = Dropdown(options = stations_with_data,
                   description = '',
                   value=None,
                   disabled= False,)

header_station_model = Output()
with header_station_model:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station (model): </p>'))

#at first, no options available. 
station_choice_model = Dropdown(options = '',                       
                   description = '',
                   value=None,
                   disabled= False,)

header_background = Output()

with header_background:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select background fit: </p>'))

background_choice_output = Output()


list_tuples_background=[('JFJ (720m model corrected) and MHD', 'JFJ720_MHD_1.csv'), ('JFJ (960m model corrected) and MHD', 'JFJ960_MHD_1.csv'), ('IZO and MHD', 'IZO_MHD_1.csv')]

background_choice = RadioButtons(
           options = list_tuples_background,
           value='JFJ720_MHD_1.csv',
           description=' ',
           disabled= False,)

background_choice.layout.width = '603px'

header_timeselect = Output()
with header_timeselect:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select which footprints to use (UTC): </p>'))

#displayed (option, value of widget selection)
options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]

time_selection= SelectMultiple(
    options=options_time_selection,
    #default is all values selected
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    style=style_bin,
    description='',
    disabled=False)

header_download = Output()
with header_download:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Download output:</p>'))

download_choice = RadioButtons(
    options=['yes', 'no'],
    description=' ',
    value='yes',
    disabled=False)

download_choice.layout.width = '603px'


header_upload = Output()

with header_upload:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Load settings from file (optional): </p>'))

file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)

update_button = Button(description='Run selection',
                       disabled=False,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)
update_button.layout.margin = '0px 0px 0px 260px' #top, right, bottom, left

royal='#4169E1'
update_button.style.button_color=royal

station_selection=VBox([header_station, station_choice_meas])
station_selection_model=VBox([header_station_model, station_choice_model])

station_selections=HBox([station_selection, station_selection_model])

update_buttons = HBox([file_name, update_button])

form = VBox([station_selections,header_timeselect,time_selection,header_background, background_choice, header_download, download_choice, header_upload, update_buttons])

#observers - what happens when change meas-station ()
station_choice_meas.observe(change_meas_station, 'value')

#Initialize form output:
form_out = Output()
output_per_station = Output()
#output_per_station_per_facility = Output()
#output_county_breakdown = Output()
progress_bar = Output()

result_radiocarbon = Output()

def update_func(button_c):

    progress_bar.clear_output()

    with progress_bar:
        f = IntProgress(min=0, max=3, style=style_bin)
        display(f)
        updateProgress(f, 'create radiocarbon object')


    settings = getSettings() 
   
    #possible to access in the notebook with the GUI using "global". 
    global radiocarbonObject

    with output_per_station:

        output_per_station.clear_output()  
 
        radiocarbonObject=radiocarbon_object_cp.RadiocarbonObjectMeasCp(settings) 
    
        radiocarbon_functions.display_info_html_table(radiocarbonObject, meas_data=True)
    
        updateProgress(f, 'create the Bokeh plot')
    
        radiocarbon_functions.plot_radiocarbon_bokhe(radiocarbonObject, include_meas=True)
        
        #download data.
        
       
        if radiocarbonObject.settings['downloadOption'] == 'yes':
            now = datetime.now()
            radiocarbonObject.settings['date/time generated'] =  now.strftime("%Y%m%d_%H%M%S_")
            radiocarbonObject.settings['output_folder'] = os.path.join('output_cp', (radiocarbonObject.settings['date/time generated']+radiocarbonObject.stationId))
            if not os.path.exists('output_cp'):
                os.makedirs('output_cp')

            os.mkdir(radiocarbonObject.settings['output_folder'])

            #possibly add format also (input to function save_model)
            radiocarbon_functions.save_data_cp(radiocarbonObject)
        
    updateProgress(f, 'finished')
    
    f.value = 3

update_button.on_click(update_func)

file_name.observe(file_set_widgets, 'value')

#Open form object:
with form_out:

    display(form, progress_bar, output_per_station)

#Display form:
display(form_out)