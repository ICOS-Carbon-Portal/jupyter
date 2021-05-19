# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida
"""

from ipywidgets import Dropdown, SelectMultiple, FileUpload, HBox, Text, VBox, Button, Output, IntText, RadioButtons,IntProgress, GridspecLayout
import stiltStations
from IPython.core.display import display, HTML 
import settings
from icoscp.station import station as cpstation


import stationchar
import stc_functions

import os
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

def get_settings():
    s = settings.getDict()    
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
        s['binSize'] = bin_size.value
        s['binInterval'] = interval.value
        s['unit'] = unit_value.value
        s['labelPolar'] = landcover_windrose_label.value
        s['saveFigs'] = save_figs.value
        s['figFormat'] = fig_format.value
        
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
    bin_size.value = s['binSize']
    interval.value = s['binInterval'] 
    unit_value.value = s['unit']
    landcover_windrose_label.value = s['labelPolar']
    save_figs.value = s['saveFigs']
    try:
        fig_format.value = s['figFormat']
    except:
        fig_format.value = 'pdf'


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
 
    update_button.disabled = False

        
    stn = c['new']
    years = sorted(stiltstations[stn]['years'])    
    years = [int(x) for x in years] 

    s_year.options=years            
    e_year.options=years
    
    #triggers "change_yr" --> months populated
    

def change_yr(c):
    
    years = [x for x in s_year.options if x >= c['new']]
    e_year.options = years
        
    #extract month (remove last item, not a month)
    stn = station_choice.value   
    month = sorted(stiltstations[stn][str(s_year.value)]['months'][:-1])
    month = [int(x) for x in month]
    s_month.options= month
    
    e_month.options = month    

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

def change_yr_end(c):
    
    if s_year.value==e_year.value:
        month = [x for x in s_month.options if x >= s_month.value]        
        e_month.options = month
    else:
        # if different from start year, all months are up for choice!
        month = sorted(stiltstations[station_choice.value][str(s_year.value)]['months'][:-1])
        month = [int(x) for x in month]
        e_month.options = month

def change_day(c):
    
    #when change the day... if the same month and year (start) - update
    if s_year.value==e_year.value and s_month.value==e_month.value:
        #print(s_day.options)
        day = [int(x) for x in s_day.options if x >= s_day.value]
        e_day.options = day
    

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
    
    # Define update function
    # This starts the process of creating the graphs
    # and, depending on the parameters, saving figures and pdf
   
    progress_bar.clear_output()
    header_no_footprints.clear_output()
    header_output.clear_output()
    result_sensitivity.clear_output()
    result_population.clear_output()
    result_pointsource.clear_output()
    result_land_cover_bar_graph.clear_output()
    result_seasonal_table.clear_output()
    header_advanced.clear_output()
    result_landcover_windrose.clear_output()
    result_multiple_variables_graph.clear_output()
    
    with progress_bar:
        f = IntProgress(min=0, max=10, style=style_bin)
        display(f)
        updateProgress(f, 'read footprint')
        
    global stc
    stc=stationchar.StationChar(get_settings())
    
    if stc.fp is None:
        
        with header_no_footprints:
            display(HTML('<p style="font-size:16px">No footprints for selected date range.</p>'))
            f.value = 10
    else:


        if stc.settings['saveFigs'] == 'yes':
            now = datetime.now()
            stc.settings['date/time generated'] =  now.strftime("%Y%m%d_%H%M%S_")
            stc.settings['output_folder'] = os.path.join('output', (stc.settings['date/time generated']+stc.stationId))
            if not os.path.exists('output'):
                os.makedirs('output')

            os.mkdir(stc.settings['output_folder'])

        with header_output:
            degree_sign=u'\N{DEGREE SIGN}'
            station_name=stc.stationName 
            station_code=stc.settings['stationCode']
            station_country=stc.country
            station_lat=stc.lat
            station_lon=stc.lon

            maps_bin_size=stc.settings['binSize']
            maps_bin_interval=stc.settings['binInterval'] 


            #date and time:
            date_and_time_string=stc_functions.date_and_time_string_for_title(stc.dateRange, stc.settings['timeOfDay'])

            if 'icos' in stc.settings:
                station_class=stc.stationClass
                station_site_type=stc.siteType
                model_height=stc.settings['stilt']['alt']

                ##
                if stc.settings['icos']['siteType']=='mountain' or stc.settings['icos']['siteType']=='Mountain':
                    mountain_string = ' (might be different from station intake height since mountain station.'
                else:
                    mountain_string = '.'


                display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name +  \
                         ' station characterisation</p><p style="font-size:18px;"><br>'+ station_name + ' (' + station_code +\
                             ') is a class ' + str(station_class) + ' ICOS atmospheric station of the type ' + station_site_type.lower() + \
                             ' located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) +\
                             degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) +\
                             degree_sign + 'E). The model height is ' + str(model_height)+ ' meters above ground' + mountain_string + '<br></p>'))

            else:

                display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                         ' station characterisation</p><p style="font-size:16px;">' + station_name + ' (' + station_code +\
                             ') is located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) +\
                             degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) + degree_sign + 'E).<br></p>'))

            #added information that is redundant in the titles
            display(HTML('<p style="font-size:18px;">Date range: ' + date_and_time_string + '<br></p>'))
            display(HTML('<p style="font-size:18px;">The map bins are ' + str(maps_bin_size) + ' degrees at ' +\
                         str(maps_bin_interval) + ' km increments</p>'))


        updateProgress(f, 'calculate sensitivity')
        with result_sensitivity:
          
            fig, caption = stc_functions.polar_graph(stc, 'sensitivity')
            stc.add_figure(1, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)

        updateProgress(f, 'process pointsource')
        with result_population:
            fig, caption=stc_functions.polar_graph(stc, 'point source contribution', colorbar='Purples')
            stc.add_figure(2, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)

        updateProgress(f, 'process population')
        with result_pointsource:
            fig, caption =stc_functions.polar_graph(stc, 'population sensitivity', colorbar='Greens')
            stc.add_figure(3, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)

        updateProgress(f, 'get landcover')
        with result_land_cover_bar_graph:
            fig, caption=stc_functions.land_cover_bar_graph(stc)
            stc.add_figure(4, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)

        updateProgress(f, 'seasonal table')
        with result_seasonal_table:
            fig, caption=stc_functions.seasonal_table(stc)
            stc.add_figure(5, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))

            try:
                display(fig)
            except:
                pass

        with header_advanced:
            display(HTML('<h2>Advanced figures</h2><br>\
                Please read the <a href="./station_characterization/specifications.pdf" target="_blank">\
                    specifications document</a> before attempting to interpret the following figures.'))

        updateProgress(f, 'landcover windrose')
        with result_landcover_windrose:
            fig, caption=stc_functions.landcover_polar_graph(stc)
            stc.add_figure(6, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)


        updateProgress(f, 'multiple variables')
        with result_multiple_variables_graph:
            fig, caption= stc_functions.multiple_variables_graph(stc)
            stc.add_figure(7, fig, caption)
            display(HTML('<p style="font-size:16px">'  + caption + ' </p>'))
            display(fig)

        if stc.settings['saveFigs'] == 'yes':
            updateProgress(f, 'saving')   
            fmt=fig_format.value
            stc_functions.save(stc, fmt)

        # make sure the progress bar is filled..
        updateProgress(f, 'finished')
        f.value = 10
        

#-----------widgets definition -----------------
    
style_bin = {'description_width': 'initial'}

header_filename = Output()

with header_filename:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Load settings from file (optional): </p>'))


file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)

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


bin_size = Dropdown(options = [15, 30, 60, 90, 180, 360],
            description = 'Bin size (degrees)', style=style_bin,
            disabled = False,)

interval = IntText(
        value=100,
        min=50,
        max=500,
        description='Interval (km)',
        disabled=False,
        step=50)

#selection percent/absolut: 
unit_value=RadioButtons(
        options=['percent', 'absolute'],
        value='percent',
        style=style_bin,
        disabled=False)

#selection label landcover windrose: 
landcover_windrose_label =RadioButtons(
        options=['yes', 'no'],
        value='yes',
        description='Labels to the land cover polar graph:',
        style=style_bin,
        disabled=False)

save_figs=RadioButtons(
        options=['yes', 'no'],
        style=style_bin,
        value='yes',
        description= 'Save the output:',
        disabled=False)

fig_format=RadioButtons(
        options=['pdf', 'png'],
        style=style_bin,
        value='pdf',
        description= 'Format figures:',
        disabled=False)


#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

royal='#4169E1'
update_button.style.button_color=royal
update_button.layout.margin = '0px 0px 0px 160px' #top, right, bottom, left


#this is just text that is put in a Vbox (vertical box) ABOVE (verticla) the station selection
#("Select here station and time range")
header_station = Output()
with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station: </p>'))

header_date_time = Output()
with header_date_time:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date and time: </p>'))

#added
header_bin_specifications = Output()
with header_bin_specifications:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select bin size and intervals: </p>'))


header_unit = Output()
with header_unit:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Unit: </p><p style="font-size:12px;width: 250px;">\
    Select representation of surface influence in <b>percent</b> for optimal display of a single station or <b>absolute</b> values for \
    intercomparison between stations </p>'))

header_style = Output()
with header_style:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br><br></p>'))

header_save_figs = Output()
#to make it align with the other texts.
with header_save_figs:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br><br></p>'))

#vertical box with the heading (header_station) and the station dropdown
station_box = VBox([header_station,station_type,station_choice, header_date_time])

#NOTE vertical - start year above end year
year_box = VBox([s_year, e_year])
month_box = VBox([s_month, e_month])
day_box = VBox([s_day, e_day])

#the two vertical boxes next to each other in a horizontal box
#Add both time-related VBoxes to a HBox:
time_box = HBox([year_box, month_box, day_box])

#added
bin_box_1 = HBox([bin_size, interval])
h_box_1 = HBox([header_unit, header_style])
v_box_1 = VBox([header_unit, unit_value])
v_box_2 = VBox([header_style, landcover_windrose_label])
v_box_3 = VBox([header_save_figs, save_figs, fig_format])
bin_box_2 = HBox([v_box_1, v_box_2, v_box_3])

#Set font of all widgets in the form:
station_choice.layout.width = '603px'
time_box.layout.margin = '25px 0px 10px 0px'
year_box.layout.margin = '0px 0px 0px 0px'

#Initialize form output:
form_out = Output()

#Initialize results output widgets:
progress_bar = Output()
header_no_footprints = Output()
header_output = Output()    
result_sensitivity = Output()    
result_population = Output()    
result_pointsource = Output()    
result_land_cover_bar_graph = Output()    
result_seasonal_table = Output()    
header_advanced = Output()    
result_landcover_windrose = Output()    
result_multiple_variables_graph = Output()


#--------------------------------------------------------------------

# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():    
    station_type.observe(change_stn_type, 'value')
    station_choice.observe(change_stn, 'value')
    s_year.observe(change_yr, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_year.observe(change_yr_end, 'value')
    e_month.observe(change_month_end, 'value')
    
    file_name.observe(file_set_widgets, 'value')
    
    #Call update-function when button is clicked:
    #added
    #update_button_file.on_click(update_func_file)
    update_button.on_click(update_func)

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
    
    h_box_1=HBox([header_output])
    grid=GridspecLayout(2, 2)
    grid[0:1, 0:1] = result_sensitivity
    grid[0:1, 1:2] = result_population
    grid[1:2, 0:1] = result_pointsource
    grid[1:2, 1:2] = result_land_cover_bar_graph
    #table much "thinner" - make HBox rather than in grid 
    h_box_2=HBox([result_seasonal_table])
    #grid for the last two:
    h_box_3=HBox([header_advanced])
    grid_2 = GridspecLayout(1, 4)
    grid_2[0:1, 0:2] = result_landcover_windrose
    grid_2[0:1, 2:4] = result_multiple_variables_graph
    
    update_buttons = HBox([file_name, update_button])
    selection_menu = VBox([station_box, time_box, time_selection, header_bin_specifications, bin_box_1,bin_box_2, header_filename, update_buttons])

    display(selection_menu, progress_bar, header_no_footprints, h_box_1, grid, h_box_2, h_box_3, grid_2)

#Display form:
display(form_out)    