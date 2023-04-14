
from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Textarea, Checkbox
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import loadtxt
import network_characterization_functions as functions
from numpy import loadtxt
import json
from datetime import datetime
data_folder = '/data/project/stc/footprints_2018_averaged'
# style to supress scrolling in the output 
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

list_2018_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if v['geoinfo']])
list_2018_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if not v['geoinfo']]
list_2018 = list_2018_not_located + list_2018_located 

def prepare_footprints_change(c):

    if prepared_footprints.value == False:
        
        station_choice.options = list_all
        
        station_choice.valuie = ''

        s_year.disabled = False
        s_month.disabled = False
        s_day.disabled = False

        e_year.disabled = False
        e_month.disabled = False
        e_day.disabled = False

        time_selection.disabled = False

    else:
       
        station_choice.options = list_2018

        s_year.disabled = True
        s_month.disabled = True
        s_day.disabled = True

        e_year.disabled = True
        e_month.disabled = True
        e_day.disabled = True

        time_selection.disabled = True

# observer functions
def change_stn(c): 
 
    years = sorted(stiltstations[station_choice.value]['years'])    
    years = [int(x) for x in years] 

    s_year.options=years 
    s_year.value = min(years)
    e_year.options=years
    e_year.value = min(years)
    
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

def update_func(button_c):

    update_button.disabled = True
    output.clear_output()
    
    now = datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S")
    download = download_choice.value
    station = station_choice.value
    
    if prepared_footprints.value:
        
        date_range = pd.date_range(start='2018-1-1', end=('2018-12-31'), freq='3H')
        timeselect_list = [0,3,6,9,12,15,18,21]
        timeselect_string='0:00, 3:00, 6:00, 9:00, 12:00, 15:00, 18:00, 21:00'

    else:
        date_range = pd.date_range(start=(str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value)), end=(str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value)), freq='3H')

        timeselect_list = list(time_selection.value)
        timeselect_string=[str(value) for value in timeselect_list]
        timeselect_string =':00, '.join(timeselect_string) + ':00'
        
    date_range = functions.date_range_hour_filtered(date_range, timeselect_list)
    
    colorbar=colorbar_choice.value
    
    if prepared_footprints.value:
  
        map_title1 = station + ':  average footprint logarithmic scale' + '\n 2018-1-1 to 2018-12-31\nHours: ' + timeselect_string

        map_title2 = station + ': percent of the average footprint sensitivity' + '\n 2018-1-1 to 2018-12-31\nHours: ' + timeselect_string
        
    else:
        map_title1 = station + ':  average footprint logarithmic scale' + '\n ' + str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value) + ' to ' + (str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value) + '\nHours: ' + timeselect_string)
    
        map_title2 = station + ': percent of the average footprint sensitivity' + '\n ' + str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value) + ' to ' + (str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value) + '\nHours: ' + timeselect_string)
    
    start_date=min(date_range)
    end_date=max(date_range)
    

    if start_date==pd.Timestamp(2018, 1, 1, 0) and end_date==pd.Timestamp(2018,12,31,0) and len(timeselect_list)==8:

        name_load_footprint_csv='fp_' + station + '.csv'
        fp=loadtxt(os.path.join(data_folder, name_load_footprint_csv), delimiter=',')
        
    else:

        nfp, fp, lon, lat, title = functions.read_aggreg_footprints(station, date_range)
        
        fp = fp[0]

    if fp is None:
        display(HTML('<p style="font-size:15px;">Not all footprints for ' + station + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to compute footprints for year 2018.</p>'))

    load_lat=loadtxt(os.path.join(data_folder, 'latitude.csv'), delimiter=',')
    load_lon=loadtxt(os.path.join(data_folder, 'longitude.csv'), delimiter=',')

    footprint_0_90 = functions.footprint_show_percentages(station, fp, load_lat, load_lon, return_fp=True)

    if download:
        pngfile1='log_scale_footprint'
        pngfile2='percent_footprint_sensitivity'
    else:
        pngfile1=''
        pngfile2=''
        
    with output:

        functions.plot_maps(fp, load_lon, load_lat, colors=colorbar, unit='[ppm / ($\mu$mol / (m$^{2}$s))]', title=map_title1, pngfile=pngfile1, date_time_predefined=date_time, linlog='log10')

        functions.plot_maps(footprint_0_90, load_lon, load_lat, colors=(colorbar + '_r'), vmin=10, vmax=90, percent = True, unit='%', title=map_title2, pngfile=pngfile2, date_time_predefined=date_time)
 
    update_button.disabled = False
style_bin = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

prepared_footprints = Checkbox(
    value=False,
    description='2018 aggregate footprint(s)',
    style=style_bin
)

header_station = Output()

with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select station to analyze:</p>'))


station_choice = Dropdown(options = list_all,
                          value=None,
                          description='Stations with STILT runs',
                          style=style_bin,
                          layout = {'height':'initial'},
                          disabled= False)

header_download = Output()

with header_download:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Download output:</p><p style="font-size:14px;">\
    If the user wishes to download the map it will end up in the "Output" folder on the home directory in a subfolder called "vis_average_footprints". </p>'))


download_choice = RadioButtons(
    options=[True, False],
    description=' ',
    value=True,
    disabled=False)

colorbar_choice_list= ['GnBu', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',\
                         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu','PuBu', 'YlGnBu', \
                         'PuBuGn', 'BuGn', 'YlGn']

heading_map_specifications = Output()

with heading_map_specifications:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;"><br>Map settings</p>'))
    
colorbar_choice = Dropdown(
    description='Colorbar:', 
    style=style_bin,
    options=colorbar_choice_list,
    layout = {'height':'initial'},
    disabled=False,
)

#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=False,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.layout.margin = '0px 0px 0px 160px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

update_button.on_click(update_func)

header_timeselect = Output()

with header_timeselect:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date range and hour(s) of the day for footprint aggregation:</p>'))


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

options_time_selection=[('0:00', 0), ('3:00', 3), ('06:00', 6), ('09:00', 9), ('12:00', 12), ('15:00', 15), ('18:00', 18), ('21:00', 21)]

time_selection= SelectMultiple(
    options=options_time_selection,
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    style=style_bin,
    description='Time of day',
    disabled=False)

# observers:
def observe():    

    station_choice.observe(change_stn, 'value')
    prepared_footprints.observe(prepare_footprints_change, 'value')
    s_year.observe(change_yr, 'value')
    s_month.observe(change_mt, 'value')    
    s_day.observe(change_day, 'value')
    e_year.observe(change_yr_end, 'value')
    e_month.observe(change_month_end, 'value')

    update_button.on_click(update_func)

def unobserve():    
    station_choice.unobserve(change_stn, 'value')
    s_year.unobserve(change_yr, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')    
    e_year.unobserve(change_yr_end, 'value')
    e_month.unobserve(change_month_end, 'value')
    e_day.unobserve(change_day_end, 'value')
    
# start observation
observe()

year_box = VBox([s_year, e_year])
month_box = VBox([s_month, e_month])
day_box = VBox([s_day, e_day])

time_box = HBox([year_box, month_box, day_box])

form = VBox([header_station, prepared_footprints, station_choice, header_timeselect, time_box, time_selection, heading_map_specifications, colorbar_choice, header_download, download_choice, update_button])

output = Output()
form_out = Output()

with form_out:
    #here add the output also 
    display(form, output)

display(widgets.HTML(style_scroll),form_out) 