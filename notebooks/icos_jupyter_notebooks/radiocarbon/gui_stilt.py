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
import radiocarbon_object

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
stiltlist = sorted([(v['name'],k) for k,v in stiltstations.items() if not v['icos']])

# sort by the first element in the tuple (name)
# sort -> sort the list in place
icoslist.sort(key=lambda x:x[0])
stiltlist.sort(key=lambda x:x[0])
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
        s['timeOfDay'] = time_selection.value
        
        s['backgroundFilename'] = background_choice.value
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
    time_selection.value = s['timeOfDay']
    
    background_choice.value = s['backgroundFilename']
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
        
# observer functions

#---------------------------------------------------------

 
    
def change_stn_type(c):  
    
    update_button.disabled = True
    
    # make sure the new 'options' are not selected..
    unobserve()    
    if station_type.value=='STILT stations':        
        station_choice.options=stiltlist
    else:        
        station_choice.options= icoslist
    
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

    stn = c['new']
    years = sorted(stiltstations[stn]['years'])    
    years = [int(x) for x in years] 

    s_year.options=years            
    e_year.options=years
    
    if s_year.value!=e_year.value or s_month.value != e_month.value or e_day.value != s_day.value:

        update_button.disabled = False
    
    #triggers "change_yr" --> months populated
    

def change_yr(c):
    
    
    years = [x for x in s_year.options if x >= c['new']]
    e_year.options = years
        
    #extract month (remove last item, not a month)
    stn = station_choice.value   
    month = sorted(stiltstations[stn][str(s_year.value)]['months'][:-1])
    month = [int(x) for x in month]
    s_month.options= month
    
    #added
    e_month.options = month
    
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False
        
def change_yr_end(c):

    
    if s_year.value==e_year.value:
        month = [x for x in s_month.options if x >= s_month.value]        
        e_month.options = month
    else:
        # if different from start year, all months are up for choice!
        month = sorted(stiltstations[station_choice.value][str(s_year.value)]['months'][:-1])
        month = [int(x) for x in month]
        e_month.options = month

    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False
        
    

def change_mt(c):
    
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
        
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
  
        update_button.disabled = True
    else:

        update_button.disabled = False
        

def change_month_end(c):
    

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
            
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False
    

def change_day(c):
  
    #when change the day... if the same month and year (start) - update
    if s_year.value==e_year.value and s_month.value==e_month.value:

        day = [int(x) for x in s_day.options if x >= s_day.value]
        e_day.options = day
        
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False
    
def change_day_end(c):
    
    if s_year.value==e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False

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
    
    #check if there is content in the dictionary (uploaded file)
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
                radiocarbonObject.settings['output_folder'] = os.path.join('output', (radiocarbonObject.settings['date/time generated']+radiocarbonObject.stationId))
                if not os.path.exists('output'):
                    os.makedirs('output')

                os.mkdir(radiocarbonObject.settings['output_folder'])


                radiocarbon_functions.save_data(radiocarbonObject)

    updateProgress(f, 'finished')
    f.value = 6           
        
#-----------widgets definition -----------------

colorbar_choice_list= ['GnBu', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',\
                         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu','PuBu', 'YlGnBu', \
                         'PuBuGn', 'BuGn', 'YlGn']
 
style_bin = {'description_width': 'initial'}

#Create a Dropdown widget with station names:
#maybe let it be coded (ex GAT344), but shown options 

station_type=RadioButtons(
        options=['ICOS stations', 'STILT stations'],
        value='ICOS stations',
        description=' ',
        disabled=False)

station_choice = Dropdown(options = icoslist,
                   description = 'Station',
                   value=None,
                   disabled= False)

#Create a Dropdown widget with year values (start year):
s_year = Dropdown(options = [],
                  description = 'Start Year',
                  disabled= False,)

#Create a Dropdown widget with month values (start month):
s_month = Dropdown(options = [],
                   description = 'Start Month',
                   disabled= False,)

#Create a Dropdown widget with year values (end year):
e_year = Dropdown(options = [],
                  description = 'End Year',
                  disabled= False,)

#Create a Dropdown widget with month values (end month):
e_month = Dropdown(options = [],
                   description = 'End Month',
                   disabled= False,)

s_day = Dropdown(options = [],
                description = 'Start Day',
                disabled = False,)

e_day = Dropdown(options = [],
            description = 'End Day',
            disabled = False,)

options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]

time_selection= SelectMultiple(
    options=options_time_selection,
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    style=style_bin,
    description='Time of day',
    disabled=False)


station_type=RadioButtons(
        options=['ICOS stations', 'STILT stations'],
        value='ICOS stations',
        description=' ',
        disabled=False)


list_tuples_background=[('JFJ (720m model corrected) and MHD', 'JFJ720_MHD_1.csv'), ('JFJ (960m model corrected) and MHD', 'JFJ960_MHD_1.csv'), ('IZO and MHD', 'IZO_MHD_1.csv')]

background_choice = RadioButtons(
           options = list_tuples_background,
           value='JFJ720_MHD_1.csv',
           description=' ',
           disabled= False,)

background_choice.layout.width = '603px'

header_download = Output()
with header_download:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Download output:</p>'))

download_choice = RadioButtons(
    options=['yes', 'no'],
    description=' ',
    value='yes',
    disabled=False)
   
header_by_facility = Output()

with header_by_facility:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Nuclear contribution by facility:</p><br><p style="font-size:14px;">Should the contributions also be broken down by nuclear facility. If "yes", please specify the threshold (in permil) for inclusion.'))
    
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
    disabled=False)

header_resample = Output()
with header_resample:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Number of days to resample:</p><br><p style="font-size:14px;">0 means that the values will be displayed for the individual footprints'))
resample = BoundedIntText(
    value=7,
    min=0,
    step=1,
    description='Days:',
    disabled=False
)

resample_monthly = Checkbox(
    value=False,
    description='Monthly',
    disabled=False,
    indent=False
)

resample_monthly.layout.margin = '0px 0px 0px 20px' #top, right, bottom, left

header_upload = Output()

with header_upload:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Load settings from file (optional): </p>'))

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
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select STILT footprints: </p>'))

header_date_time = Output()
with header_date_time:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date and time: </p>'))

header_background = Output()
with header_background:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select background fit: </p>'))

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

#Add all widgets to a VBox:
#form = VBox([station_box, time_box, time_selection, update_button])

resample_choices = HBox([resample, resample_monthly])
update_buttons = HBox([file_name, update_button])
form = VBox([header_station,station_type,station_choice, header_date_time, time_box, time_selection,  header_resample, resample_choices, header_background,\
             background_choice, header_by_facility, \
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
display(form_out)    