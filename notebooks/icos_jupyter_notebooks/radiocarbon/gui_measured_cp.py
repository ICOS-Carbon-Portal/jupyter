# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 
"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, RadioButtons,IntProgress,IntSlider, GridspecLayout, Text, BoundedFloatText, FileUpload, Checkbox, BoundedIntText
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import radiocarbon_functions
import radiocarbon_object_cp
import os
import matplotlib.pyplot as plt
from datetime import datetime
import json

from icoscp.stilt import stiltstation

stiltstations= stiltstation.find()

def getSettings():
 
    s = {}
    
    try:
        
        dictionary_meas_to_stilt={'HPB': 'HPB131', 'HTM':'HTM150', 'JFJ':'JFJ', 'LIN': 'LIN099', 'NOR':'NOR100', 'OPE':'OPE120', 'PAL': 'PAL', 'SAC': 'SAC100', 'SVB':'SVB150', 'KRE':'KRE250', 'KIT':'KIT200', 'STE':'STE252'}
        
        if not station_choice_meas.value['station_code'] in dictionary_meas_to_stilt:

            guess_stilt_code = station_choice_meas.value['station_code'] + str(station_choice_meas.value['sampling_height'])

            s['stationCode'] = guess_stilt_code
            
        else:
        
            s['stationCode'] = dictionary_meas_to_stilt[station_choice_meas.value['station_code']]
        if stiltstations[s['stationCode']]['icos']:
            s['icos'] = cpstation.get(s['stationCode'][0:3].upper()).info()
        s['stilt'] = stiltstations[s['stationCode']]
        s['timeOfDay'] = [0, 3, 6, 9, 12, 15, 18, 21]
        s['backgroundFilename'] = 'IZOMHd24.csv'
        s['downloadOption'] = download_choice.value
        
        s['codeMeasCP'] = station_choice_meas.value['station_code']
        s['samplingHeightMeas'] = station_choice_meas.value['sampling_height']

    except:
        
        return    
    
    return s

#----------- start processing -----------------
def updateProgress(f, desc=''):
    # custom progressbar updates
    f.value += 1
    if not desc:
        f.description = 'step ' + str(f.value) + '/' + str(f.max)
    else:
        f.description = str(desc)

style_bin = {'description_width': 'initial'}

header_station = Output()
with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station: </p>'))

#depending on what is available at the carbon portal
stations_with_data = radiocarbon_functions.list_station_tuples_w_radiocarbon_data()

station_choice_meas = Dropdown(options = stations_with_data,
                   description = '',
                   value=None,
                   disabled= False,)

header_download = Output()
with header_download:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Download output:</p>'))
    
header_download.layout.margin = '0px 0px 0px 200px' #top, right, bottom, left

download_choice = RadioButtons(
    options=['yes', 'no'],
    description=' ',
    value='yes',
    disabled=False)

download_choice.layout.width = '603px'
download_choice.layout.margin = '-10px 0px 0px -40px' #top, right, bottom, left

update_button = Button(description='Run selection',
                       disabled=False,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)
#update_button.layout.margin = '0px 0px 0px 260px' #top, right, bottom, left

royal='#4169E1'
update_button.style.button_color=royal

h_box_1=HBox([header_station, header_download])

h_box_2=HBox([station_choice_meas,download_choice])

form = VBox([h_box_1, h_box_2, update_button])

#Initialize form output:
form_out = Output()
output_per_station = Output()
progress_bar = Output()
result_radiocarbon = Output()

def update_func(button_c):
    
    update_button.disabled = True

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
    
        radiocarbon_functions.display_info_html_table(radiocarbonObject, meas_data=True, cp_private=True)
    
        updateProgress(f, 'create the Bokeh plot')
    
        radiocarbon_functions.plot_radiocarbon_bokhe(radiocarbonObject, include_meas=True)
        
        if radiocarbonObject.settings['downloadOption'] == 'yes':
      
            now = datetime.now()
        
            radiocarbonObject.settings['date/time generated'] =  now.strftime("%Y%m%d_%H%M%S_")
            
            output = os.path.join(os.path.expanduser('~'), 'output/radiocarbon_cp_result', radiocarbonObject.settings['date/time generated']+radiocarbonObject.stationId) 
            if not os.path.exists(output):
                os.makedirs(output)
                
            radiocarbonObject.settings['output_folder'] = output


            #possibly add format also (input to function save_model)
            radiocarbon_functions.save_data_cp(radiocarbonObject)
        
    updateProgress(f, 'finished')

    update_button.disabled = False
    
    f.value = 3

update_button.on_click(update_func)


#Open form object:
with form_out:

    display(form, progress_bar, output_per_station)

#Display form:
display(form_out)