# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio
"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress, GridspecLayout
import stiltStations
from IPython.core.display import display, HTML 
import settings
from icoscp.station import station as cpstation

#added
import stationchar
import stc_functions

import os
import matplotlib.pyplot as plt


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
        s['titles'] = include_labels.value
        s['labelPolar'] = landcover_windrose_label.value
        s['saveFigs'] = save_figs.value
    except:
        return    
    
    return s

def setSettings(s):
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
    include_labels.value = s['titles']
    landcover_windrose_label.value = s['labelPolar']
    save_figs.value = s['saveFigs']

# observer functions

#---------------------------------------------------------
def change_stn_type(c):    
    
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

    
#----------- start processing -----------------
def update_func(button_c):
# Define update function
# This starts the process of creating the graphs
# and, depending on the parameters, saving figures and pdf
    
    import time
    start_time = time.time()
    #settings also includes infromation from cpstation (if icos station) or stiltstations (if stilt station)
    settings = getSettings()  

    #before also passed settings['stationCode']
    stationCharObject=stationchar.StationChar(settings)
    
   
    
    with header_output:
        header_output.clear_output()
        degree_sign=u'\N{DEGREE SIGN}'
        station_name=stationCharObject.stationName 
        station_country=stationCharObject.country
        station_lat=stationCharObject.lat
        station_lon=stationCharObject.lon

        if 'icos' in stationCharObject.settings:
            station_class=stationCharObject.stationClass
            station_site_type=stationCharObject.siteType
            
            display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                         ' station characterization</p><p style="font-size:18px;"><br>'+ station_name +\
                         ' is a class ' + str(station_class) + ' ICOS atmospheric station of the type ' + station_site_type.lower() + \
                         ' located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) +\
                         degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) +\
                         degree_sign + 'E).</p>'))

        else:
            
            display(HTML('<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                         ' station characterization</p><p style="font-size:16px;">' + station_name + \
                         ' is located in ' + station_country + ' (latitude: ' + str("%.2f" % station_lat) +\
                         degree_sign + 'N, ' + 'longitude: ' + str("%.2f" % station_lon) + degree_sign + 'E).</p>'))
            
        f = IntProgress(min=0, max=8, description='Loading:')

        display(f) 

        f.value += 1

    with result_sensitivity:
        
        result_sensitivity.clear_output()
        
        #handle text as text. 
        sensitivity_map, sensitivity_text=stc_functions.map_representation_polar_graph_upd(stationCharObject, 'sensitivity')
        
        display(HTML('<p style="font-size:16px;text-align:center">'  + sensitivity_text + ' </p>'))
        sensitivity_map.show()
        f.value += 1
    with result_population:
        result_population.clear_output()
        population_map, population_text=stc_functions.map_representation_polar_graph_upd(stationCharObject, 'point source contribution', colorbar='Purples')
        display(HTML('<p style="font-size:16px;text-align:center">'  + population_text + ' </p>'))
        population_map.show()
        f.value += 1
        
    with result_pointsource:
        result_pointsource.clear_output()
        pointsource_map, pointsource_text =stc_functions.map_representation_polar_graph_upd(stationCharObject, 'population sensitivity', colorbar='Greens')
        display(HTML('<p style="font-size:16px;text-align:center">'  + pointsource_text + ' </p>'))
        pointsource_map.show()
        f.value += 1

        
    with result_land_cover_bar_graph:
        result_land_cover_bar_graph.clear_output()
        landcover_bar_graph, landcover_bar_graph_text=stc_functions.land_cover_bar_graph_upd(stationCharObject)
        display(HTML('<p style="font-size:16px;text-align:center">'  + landcover_bar_graph_text + ' </p>'))
        landcover_bar_graph.show()
        f.value += 1
    with result_seasonal_table:
        result_seasonal_table.clear_output()
        seasonal_table=stc_functions.create_seasonal_table_upd(stationCharObject)
        try:
            seasonal_table.show()
        except:
            pass
        f.value += 1
        
    
    with header_advanced:
        header_advanced.clear_output()
        display(HTML('<p style="font-size:35px;font-weight:bold;">Advanced figures</p><p style="font-size:16px;"><br>\
            We advice careful reading of the specifications before attempting to understand the following figures.</p>'))
    
    with result_landcover_windrose:
        result_landcover_windrose.clear_output()
        landcover_windrose,landcover_windrose_text=stc_functions.landcover_polar_graph_upd(stationCharObject)
        display(HTML('<p style="font-size:16px;text-align:center">'  + landcover_windrose_text + ' </p>'))
        landcover_windrose.show()
        f.value += 1
        
    with result_multiple_variables_graph:
        result_multiple_variables_graph.clear_output()
        multiple_variables_graph, multiple_variables_graph_text= stc_functions.multiple_variables_graph_upd(stationCharObject)
        display(HTML('<p style="font-size:16px;text-align:center">'  + multiple_variables_graph_text + ' </p>'))
        multiple_variables_graph.show()
        #to see the time it takes to run the whole station characterization
        #print(time.time() - start_time)
        f.value += 1
      
    """
    if settings['saveFigs']=='yes':
        figures_to_save=[sensitivity_map, population_map, pointsource_map, landcover_bar_graph, seasonal_table, landcover_windrose, multiple_variables_graph]
        texts_to_save =[sensitivity_text,population_text,pointsource_text, '', landcover_windrose_text, multiple_variables_graph_text]
        
        index=1
        for figure, text in zip(figures_to_save, texts_to_save):

            
            if not os.path.exists('figures_upd'):
                os.mkdir('figures_upd')
            plotdir='figures_upd'
            pngfile=station_name+'_figure_' + str(index)
            #fig.savefig(plotdir+'/'+pngfile+'.pdf',dpi=100,bbox_inches='tight')
            plt.savefig(plotdir+'/'+pngfile+ '.pdf', dpi=100, bbox_inches='tight')
            #plt.close(figure)
            
            text_file=plotdir + '/' + station_name + '_text_' + str(index) +'.txt'
            open_file= open(text_file, "w")
            open_file.write(text)
            open_file.close() 
            
            index=index+1
            """

        
        
#-----------widgets definition -----------------
    
style_bin = {'description_width': 'initial'}

#Create a Dropdown widget with station names:
#maybe let it be coded (ex GAT344), but shown options 

#added
station_type=RadioButtons(
        options=['ICOS stations', 'STILT stations'],
        value='ICOS stations',
        description=' ',
        disabled=False)


#prev: station_name_code_for_dropdown
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
        description='Add labels to the land cover polar graph:',
        style=style_bin,
        disabled=False)

#selection include titles or not
include_labels =RadioButtons(
        options=['yes', 'no'],
        value='yes',
        description='Add titles to the figures:',
        style=style_bin,
        disabled=False)


save_figs=RadioButtons(
        options=['yes', 'no'],
        style=style_bin,
        value='no',
        description= 'Do you want to save the figures:',
        disabled=False)


#Create a Button widget to control execution:
update_button = Button(description='Update',
                       disabled=False,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)


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
v_box_2 = VBox([header_style, include_labels, landcover_windrose_label])
v_box_3 = VBox([header_save_figs, save_figs, update_button])
bin_box_2 = HBox([v_box_1, v_box_2, v_box_3])

#Add all widgets to a VBox:
form = VBox([station_box, time_box, time_selection, header_bin_specifications, bin_box_1,bin_box_2])

#Set font of all widgets in the form:
station_choice.layout.width = '603px'
time_box.layout.margin = '25px 0px 10px 0px'
year_box.layout.margin = '0px 0px 0px 0px'
update_button.layout.margin = '50px 0px 0px 50px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

#Initialize form output:
form_out = Output()

#Initialize results output widgets:
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
    
    #Call update-function when button is clicked:
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


    display(form, h_box_1, grid, h_box_2, h_box_3, grid_2)


#Display form:
display(form_out)    