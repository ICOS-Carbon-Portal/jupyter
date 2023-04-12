# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 
"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, RadioButtons,IntProgress,IntSlider, GridspecLayout, Text, BoundedFloatText, FileUpload, Checkbox, BoundedIntText
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import radiocarbon_functions
import radiocarbon_object
import os
import matplotlib.pyplot as plt
from datetime import datetime
import json
button_color_able='#4169E1'
import warnings
warnings.filterwarnings('ignore')

import ipywidgets as widgets
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

from icoscp.stilt import stiltstation

stiltstations= stiltstation.find()

list_all_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if v['geoinfo']])
list_all_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if not v['geoinfo']]
list_all = list_all_not_located + list_all_located

list_all_icos_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if v['geoinfo'] if v['icos']])
list_all_icos_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k, v in stiltstations.items() if not v['geoinfo'] if v['icos']]
list_all_icos = list_all_icos_not_located + list_all_icos_located


#---------------------------------------------------------

# read or set the parameters

def getSettings():
    #s = settings.getDict()    
    s = {}
    try:
        s['stationCode'] = station_choice.value
        if stiltstations[s['stationCode']]['icos']:
            s['icos'] = cpstation.get(s['stationCode'][0:3].upper()).info()
        s['stilt'] = stiltstations[s['stationCode']]
        s['startYear'] = s_year.value
        s['startMonth'] = s_month.value
        s['startDay'] = s_day.value
        s['endYear'] = e_year.value
        s['endMonth'] = e_month.value
        s['endDay'] = e_day.value
        s['timeOfDay'] = [0, 3, 6, 9, 12, 15, 18, 21]
        s['backgroundFilename'] = '14c_mhd_integrals_noaa_smoothed_final.csv'
        s['downloadOption'] = download_choice.value
        s['facilityInclusion'] = facility_choice.value
        s['threshold'] = threshold_facility_inclusions.value
        
        if resample_monthly.value == True:
            
            s['resample'] = 'MS'
        else: 
            
            s['resample'] = str(resample.value) + 'D'
   
    except:
        return    
    
    return s

def set_settings(s):
    
    station_choice.value = s['stationCode']   
    s_year.value = s['startYear'] 
    s_month.value = s['startMonth']
    s_day.value = s['startDay']
    e_year.value = s['endYear'] 
    e_month.value = s['endMonth']
    e_day.value = s['endDay']
    download_choice.value = s['downloadOption']
    facility_choice.value = s['facilityInclusion']
    threshold_facility_inclusions.value = s['threshold']
    
    if s['resample'] == 'MS':
        resample_monthly.value = True
        resample.disabled = True
        
    else:
        
        resample.disabled = False
        resample_str = s['resample']
        resample_int = int(resample_str[:-1])
        resample.value = resample_int

# check if it is a valid date range, enable/disable update button in accordance.
def check_date_range():
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False
        
# observer functions
def change_stn_type(c): 
    
    # disable update button until date and time defined (see how these are reset below)
    update_button.disabled = True
    update_button.tooltip = 'Unable to run'

    # make sure the new 'options' are not selected..
    unobserve()    
    if station_type.value=='STILT stations':        
        station_choice.options=list_all
    else:       
        station_choice.options= list_all_icos
    
    station_choice.value=None 
    
    # reset the data fields
    s_year.options = []
    e_year.options = []
    s_month.options = []
    e_month.options = []
    s_day.options = []
    e_day.options = []
    
    # make sure future changes are observed again
    observe()
    
def change_stn(c): 
 
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'
    update_button.style.button_color=button_color_able
        
    years = sorted(stiltstations[station_choice.value]['years'])    
    years = [int(x) for x in years] 

    s_year.options=years 
    s_year.value = min(years)
    e_year.options=years
    e_year.value = min(years)
    
    #triggers "change_yr" --> pupulates the month widgets based on STILT footprint availability
    

def change_yr(c):

    years = [x for x in s_year.options if x >= s_year.value]
    #extract available months 
    month = sorted(stiltstations[station_choice.value][str(s_year.value)]['months'])
    month = [int(x) for x in month]
    s_month.options= month
    s_month.value = min(month)
    e_year.options = years
    e_month.options = month
    e_month.value = min(month)
    check_date_range()

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
    if s_year.value==e_year.value and s_month.value>e_month.value:
        month = [int(x) for x in s_month.options if x >= s_month.value]                
        e_month.options=month
        e_month.value = min(month)
        
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options=day
        e_day.value = min(day)
        
    check_date_range()

def change_yr_end(c):
    
    if s_year.value==e_year.value:
        month = [x for x in s_month.options if x >= s_month.value]
        e_month.options = month
        e_month.value = min(month)
    else:
        # if different from start year, all months are up for choice!
        month = sorted(stiltstations[station_choice.value][str(e_year.value)]['months'])
        month = [int(x) for x in month]
        e_month.options = month
        e_month.value = min(month)
        
    if s_year.value==e_year.value and e_month.value==s_month.value:
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
        
    check_date_range()

def change_day(c):
    
    #when change the day... if the same month and year (start) - update
    if s_year.value==e_year.value and s_month.value==e_month.value:
        original_value = e_day.value 
        allowed_days = [int(x) for x in s_day.options if x >= s_day.value]
        e_day.options = allowed_days  
        
        if original_value in allowed_days:
            e_day.value = original_value
        else:
            e_day.value = min(allowed_days)
            
    check_date_range()
    
def change_month_end(c):
    
    if s_year.value==e_year.value and e_month.value==s_month.value:
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
    
    check_date_range()
    
def change_day_end(c):
    
    check_date_range()

def change_resample_monthly(c):
    
    if resample_monthly.value==True:
        resample.disabled = True
    else:
        resample.disabled = False
        
def change_facility_choice(c):
    
    if facility_choice.value==True:
        threshold_facility_inclusions.disabled = False
    else:
        threshold_facility_inclusions.disabled = True
        
def file_set_widgets(c):
    
    uploaded_file = file_name.value
    
    if bool(uploaded_file):
        
        settings_file=uploaded_file[list(uploaded_file.keys())[0]]['content']
        settings_json = settings_file.decode('utf8').replace("'", '"')
        settings_dict = json.loads(settings_json)
        set_settings(settings_dict)
#----------- start processing -----------------

def updateProgress(f, desc=''):
    # custom progressbar updates
    f.value += 1
    if not desc:
        f.description = 'step ' + str(f.value) + '/' + str(f.max)
    else:
        f.description = str(desc)
       
    
def update_func(button_c):
    
    update_button.disabled = True
    
    progress_bar.clear_output()
    header_no_footprints.clear_output()
    output_per_station.clear_output()

    with progress_bar:
        f = IntProgress(min=0, max=6, style=style_bin)
        display(f)
        updateProgress(f, 'create radiocarbon object')

    settings = getSettings()  

    #possible to access in the notebook with the GUI using "global". 
    global radiocarbonObject
    


    with output_per_station:

        radiocarbonObject=radiocarbon_object.RadiocarbonObject(settings) 


        if radiocarbonObject.fp is None:

            with header_no_footprints:
                display(HTML('<p style="font-size:16px">No footprints for selected date range.</p>'))
                f.value = 6

        else:

            radiocarbon_functions.display_info_html_table(radiocarbonObject, meas_data=False)

            updateProgress(f, 'nuclear contamination')

            radiocarbon_functions.plot_radiocarbon_bokhe(radiocarbonObject)

            if radiocarbonObject.settings['facilityInclusion']:

                #radiocarbonObject updated with dataframe "dfFacilitiesOverThreshold".
                #contains name of facilities contamining over "threshold", latitude of facility, longitude of facility
                #and the average contamination from it for the user specified parameters ("dateRange" and "timeOfDay" etc)
                updateProgress(f, 'nuclear by facility')
                radiocarbonObject = radiocarbon_functions.plot_nuclear_contamination_by_facility_bokhe(radiocarbonObject)

                #if there are facilities with average contribution over the user-defined threshold    
                if radiocarbonObject.dfFacilitiesOverThreshold is not None:

                    updateProgress(f, 'nuclear by facility map')
                    radiocarbon_functions.nuclear_contamination_by_facility_map(radiocarbonObject)
                else:
                    display(HTML('<p style="font-size:15px;">No nuclear facilities contributing > ' + str(radiocarbonObject.settings['threshold']) +' permil</p>'))


            #move this to radiocarbon_object.py
            if radiocarbonObject.settings['downloadOption'] == 'yes':
                now = datetime.now()
                radiocarbonObject.settings['date/time generated'] =  now.strftime("%Y%m%d_%H%M%S_")
                
                output = os.path.join(os.path.expanduser('~'), 'output/radiocarbon_model_result', radiocarbonObject.settings['date/time generated']+radiocarbonObject.stationId) 
                if not os.path.exists(output):
                    os.makedirs(output)
                
                radiocarbonObject.settings['output_folder'] = output


                radiocarbon_functions.save_data(radiocarbonObject)

    updateProgress(f, 'finished')
    
    update_button.disabled = False
    
    f.value = 6           
        
#-----------widgets definition -----------------

colorbar_choice_list= ['GnBu', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',\
                         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu','PuBu', 'YlGnBu', \
                         'PuBuGn', 'BuGn', 'YlGn']
 
style_bin = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

#Create a Dropdown widget with station names:
#maybe let it be coded (ex GAT344), but shown options 

station_type=RadioButtons(
        options=['ICOS stations', 'STILT stations'],
        value='ICOS stations',
        description=' ',
        layout = layout,
        disabled=False)

station_choice = Dropdown(options = list_all_icos,
                   description = 'Station',
                   layout = layout,
                   value=None,
                   disabled= False)

#Create a Dropdown widget with year values (start year):
s_year = Dropdown(options = [],
                  description = 'Start Year',     
                  layout = layout,
                  disabled= False,)

#Create a Dropdown widget with month values (start month):
s_month = Dropdown(options = [],
                   description = 'Start Month',
                   layout = layout,
                   disabled= False,)

#Create a Dropdown widget with year values (end year):
e_year = Dropdown(options = [],
                  description = 'End Year',
                  layout = layout,
                  disabled= False,)

#Create a Dropdown widget with month values (end month):
e_month = Dropdown(options = [],
                   description = 'End Month',
                   layout = layout,
                   disabled= False,)

s_day = Dropdown(options = [],
                description = 'Start Day',
                 layout = layout,
                disabled = False,)

e_day = Dropdown(options = [],
            description = 'End Day',
             layout = layout,
            disabled = False,)

station_type=RadioButtons(
        options=['ICOS stations', 'STILT stations'],
        value='ICOS stations',
        description=' ',
        disabled=False)


header_download = Output()
with header_download:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Download output:</p><p style="font-size:14px;">\
    If the user wishes to download the result, the file will end up in a folder on the same level as this notebook called "radiocarbon_output_model" (created once something has been downloaded). It will include csv-files with data presented in the output time series as well as a file settings file, which ends with "_settings.json". The settings file can be uploaded to populate the widgets (see "Load settings from file") with the same parameter selection as the current run. </p>'))

download_choice = RadioButtons(
    options=['yes', 'no'],
    description=' ',
    value='yes',
    disabled=False)
   
header_by_facility = Output()

with header_by_facility:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Nuclear contribution by facility:</p><p style="font-size:14px;">Choose "yes" to include an additional time series plot where the nuclear contribution by facility is displayed in \
    accordance with specified resampling method. A map showing the locations of the contributing facilities will \
    also be output.'))
    
facility_choice = RadioButtons(  
    options=[('yes', True), ('no', False)],
    description=' ',
    value=True,
    disabled=False)

threshold_facility_inclusions = BoundedFloatText(
    description='∆14C contamination (permil)',
    value=0.2,
    min=0,
    style=style_bin,
    layout = layout,
    disabled=False)

header_resample = Output()
with header_resample:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Number of days to resample:</p><p style="font-size:14px;">0 means that the values will be displayed for the individual footprints (0:00, 3:00, 6:00, 9:00, 12:00, 15:00, 18:00, and 21:00 UTC). <br>Any other number than 0 specifies the number of days over which the results will be averaged. <br>If the box "Monthly" is checked the results will be averaged on the monthly timescale. It will disable the option to specify the number of days to resample.<br></p>'))
    
resample = BoundedIntText(
    value=7,
    min=0,
    step=1,
    description='Days:',
    layout = layout,
    disabled=False
)

resample_monthly = Checkbox(
    value=False,
    description='Monthly',
    disabled=False,
    layout = layout,
    indent=False
)

resample_monthly.layout.margin = '0px 0px 0px 20px' #top, right, bottom, left

header_upload = Output()

with header_upload:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Load settings from file (optional): </p><p style="font-size:14px;">It is optional to upload a settings file (see "Download output"). It will populate all the widgets and it \
    will be possible to run the tool ("Run selection") directly upon upload or after making changes to the selections. </p>'))

file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)

#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)
update_button.layout.margin = '0px 0px 0px 260px' #top, right, bottom, left

royal='#4169E1'

update_button.style.button_color=royal

#this is just text that is put in a Vbox (vertical box) ABOVE (verticla) the station selection
#("Select here station and time range")
header_station = Output()
with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select STILT footprints:</p><p style="font-size:14px;">\
    The user can choose to do the analysis for any of the ICOS certified stations (ICOS stations), alternatively any point within the STILT domain with footprints (STILT stations) can be chosen. </p>'))

header_date_time = Output()
with header_date_time:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date range: </p><p style="font-size:14px;">\
    Specify the date range for the analysis. The options in the dropdown will change in accordance\
    with what footprints are available. Footprints can be generated with the <a href="https://stilt.icos-cp.eu/worker/" target="_blank">on demand calculator</a> at the Carbon Portal website. </p>'))

#NOTE vertical - start year above end year
year_box = VBox([s_year, e_year])
month_box = VBox([s_month, e_month])
day_box = VBox([s_day, e_day])

#the two vertical boxes next to each other in a horizontal box
#Add both time-related VBoxes to a HBox:
time_box = HBox([year_box, month_box, day_box])

#Set font of all widgets in the form:
station_choice.layout.width = '603px'
time_box.layout.margin = '25px 0px 10px 0px'
year_box.layout.margin = '0px 0px 0px 0px'

h_box_facility = HBox([facility_choice, threshold_facility_inclusions])

resample_choices = HBox([resample, resample_monthly])
update_buttons = HBox([file_name, update_button])
form = VBox([header_station,station_type,station_choice, header_date_time, time_box, header_resample,\
             resample_choices, header_by_facility, \
             h_box_facility, header_download, download_choice, header_upload, update_buttons])

#Initialize form output:
form_out = Output()

header_no_footprints = Output()
output_per_station = Output()
output_per_station_per_facility = Output()
#output_county_breakdown = Output()
progress_bar = Output()

#--------------------------------------------------------------------

# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():    
    station_type.observe(change_stn_type, 'value')
    station_choice.observe(change_stn, 'value')
    s_year.observe(change_yr, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_day.observe(change_day_end, 'value')
    e_year.observe(change_yr_end, 'value')
    e_month.observe(change_month_end, 'value')
    resample_monthly.observe(change_resample_monthly, 'value')
    facility_choice.observe(change_facility_choice, 'value')
    
    #Call update-function when button is clicked:
    update_button.on_click(update_func)
    
    file_name.observe(file_set_widgets, 'value')

def unobserve():    
    station_type.unobserve(change_stn_type, 'value')
    station_choice.unobserve(change_stn, 'value')
    s_year.unobserve(change_yr, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')    
    e_year.unobserve(change_yr_end, 'value')
    e_month.unobserve(change_month_end, 'value')
    
# start observation
observe()

#--------------------------------------------------------------------
#Open form object:
with form_out:

    #prev. also output_county_breakdown
    h_box_footprints=HBox([output_per_station, output_per_station_per_facility])
    display(form, progress_bar, header_no_footprints, h_box_footprints)

#Display form:
display(widgets.HTML(style_scroll),form_out) 