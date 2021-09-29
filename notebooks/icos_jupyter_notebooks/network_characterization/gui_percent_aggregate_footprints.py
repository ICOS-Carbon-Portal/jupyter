
from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Textarea
import stiltStations
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

stiltstations = stiltStations.getStilt()

all_list = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items()])


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

def update_func(button_c):

    update_button.disabled = True
    now = datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S")
    #add options:
    download = download_choice.value
  
    station = station_choice.value
    
    date_range = pd.date_range(start=(str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value)), end=(str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value)), freq='3H')
    
    timeselect_list = list(time_selection.value)
    timeselect_string=[str(value) for value in timeselect_list]
    timeselect_string =':00, '.join(timeselect_string) + ':00'
    
    colorbar=colorbar_choice.value
    
    map_title1 = station + ':  average footprint logarithmic scale' + '\n ' + str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value) + ' to ' + (str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value) + '\nHours: ' + timeselect_string)
    
    map_title2 = station + ': percent of the average footprint sensitivity' + '\n ' + str(s_year.value) + '-' + str(s_month.value)  + '-' + str(s_day.value) + ' to ' + (str(e_year.value) + '-' + str(e_month.value)  + '-' + str(e_day.value) + '\nHours: ' + timeselect_string)
    
    date_range = functions.date_range_hour_filtered(date_range, timeselect_list)
    
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

    global df_sensitivity_sorted
    global df_compare_percent_choices
    footprint_0_90, df_sensitivity_sorted, df_compare_percent_choices = functions.footprint_show_percentages(station, fp, load_lat, load_lon, return_fp=True)

    if download:
        pngfile1='log_scale_footprint'
        pngfile2='percent_footprint_sensitivity'
    else:
        pngfile1=''
        pngfile2=''
    

    ###added: orig:
    functions.plot_maps(fp, load_lon, load_lat, colors=colorbar, unit='[ppm / ($\mu$mol / (m$^{2}$s))]', title=map_title1, pngfile=pngfile1, date_time_predefined=date_time, linlog='log10')
    
    functions.plot_maps(footprint_0_90, load_lon, load_lat, colors=(colorbar + '_r'), vmin=10, vmax=90, percent = True, unit='%', title=map_title2, pngfile=pngfile2, date_time_predefined=date_time)
 

    #functions.plot_maps(footprint_0_90_total_potential, load_lon, load_lat, colors='Blues', vmin=10, vmax=90, percent = True, unit='%', title=map_title2, pngfile=pngfile2, date_time_predefined=date_time)

    update_button.disabled = False
style_bin = {'description_width': 'initial'}

header_station = Output()

with header_station:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select site to analyze:</p>'))


station_choice = Dropdown(options = all_list,
                          value=None,
                          description='Sites with STILT runs',
                          style=style_bin,
                          disabled= False)

#station_choice.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

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
    disabled=False,
)


#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       #disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.layout.margin = '0px 0px 0px 160px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

update_button.on_click(update_func)


#### added for time selection #########

header_timeselect = Output()

with header_timeselect:
    display(HTML('<p style="font-size:15px;font-weight:bold;"><br>Select date range and hour(s) of the day for footprint aggregation:</p>'))


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


# observers:
def observe():    

    station_choice.observe(change_stn, 'value')
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
    
# start observation
observe()

year_box = VBox([s_year, e_year])
month_box = VBox([s_month, e_month])
day_box = VBox([s_day, e_day])

#the two vertical boxes next to each other in a horizontal box
#Add both time-related VBoxes to a HBox:
time_box = HBox([year_box, month_box, day_box])



form = VBox([header_station, station_choice, header_timeselect, time_box, time_selection, heading_map_specifications, colorbar_choice, header_download, download_choice, update_button])


form_out = Output()


with form_out:
    #here add the output also 
    display(form)
    
display(form_out) 