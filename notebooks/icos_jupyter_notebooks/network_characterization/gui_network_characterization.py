# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida 

"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Textarea
import stiltStations
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import network_characterization_functions as functions

import json

stiltstations = stiltStations.getStilt()

#for base network it is only possible to choose between ICOS stations:
icos_list = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>12 if v['icos']])

#for the compare network any site with STILT runs is possible
#however, it must have 12 months worth of data to show up in the dropdown
all_list = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>12])

def set_settings(s):

    sites_base_network_options.value = s['baseNetwork']   
    sites_compare_network_options.value = s['compareNetwork'] 
    colorbar_choice.value = s['colorBar']
    threshold_option.value = s['percent']
    area_type.value = s['countryDefinition'] 
    country_options.value = s['countries']
    breakdown_type.value = s['weighing']
    download_output_option.value = s['download']

def change_selected_stations(c): 
 
    if len(sites_base_network_options.value)>0:
        update_button.disabled = False
    else:
        update_button.disabled = True
        
def change_stations_compare_network(c):
    
    list_compare_network = list(sites_compare_network_options.value)
    
    list_compare_network_string = ', '.join([str(station_code) for station_code in list_compare_network])
    
    list_selected_compare_network.value= list_compare_network_string
    
    
def change_stations_base_network(c):
    
    list_base_network = list(sites_base_network_options.value)
    
    list_base_network_string = ', '.join([str(station_code) for station_code in list_base_network])
    
    list_selected_base_network.value= list_base_network_string

def file_set_widgets(c):
    
    uploaded_file = file_name.value
    
    #check if there is content in the dictionary (uploaded file)
    if bool(uploaded_file):
        settings_file=uploaded_file[list(uploaded_file.keys())[0]]['content']
        settings_json = settings_file.decode('utf8').replace("'", '"')
        settings_dict = json.loads(settings_json)
        set_settings(settings_dict)
        
#----------- start processing -----------------

#clear all the output
def clear_all_output():
    output_summed_sens_fp.clear_output()
    output_aggreg_fp_see_not_see.clear_output()
    output_summed_fp_see_not_see.clear_output()
    output_summed_sens_fp_uploaded_fp.clear_output()
    output_aggreg_fp_see_not_see_uploaded_fp.clear_output()
    output_breakdown_countries.clear_output()
    output_header_landcover_section.clear_output()
    breakdown_landcover_output.clear_output()
    output_header_landcover_section.clear_output()
    output_aggreg_fp_see_not_see_uploaded_fp.clear_output()
    output_summed_fp_see_not_see_uploaded_fp.clear_output()
    output_summed_sens_fp_uploaded_fp.clear_output()
    
def update_func(button_c):
    
    update_button.disabled = True
    clear_all_output()

    sites_base_network=list(sites_base_network_options.value)
    sites_compare_network = list(sites_compare_network_options.value)
    
    threshold_percent = str(threshold_option.value)
    threshold_int = threshold_option.value/100
    
    download_output=download_output_option.value
    colorbar=colorbar_choice.value
    
    #countries for combination with ancillary data
    countries_keys=list(country_options.value)
    countries = []
    if area_type.value == 'Land':

        dictionary_land={'Belgium': 'Belgium', 'Czech Republic':'Czech_Rep', 'Denmark': 'Denmark', 'Estonia':'Estonia', 'Finland':'Finland', 'France':'France','Germany':'Germany', 'Hungary':'Hungary', 'Italy':'Italy', 'Netherlands':'Netherland','Norway':'Norway', 'Poland':'Poland','Spain':'Spain','Sweden':'Sweden', 'Switzerland':'Switzerlan','UK':'UK'}
        
        for country in countries_keys:
            countries.append(dictionary_land[country])
            
    #land + eez:
    else:
        
        dictionary_land_eez={'Belgium': 'Belgiu_eez', 'Czech Republic':'Czech_Rep', 'Denmark': 'Denmar_eez', 'Estonia':'Estoni_eez', 'Finland':'Finlan_eez', 'France':'France_eez','Germany':'Germa_eez', 'Hungary':'Hungary', 'Italy':'Italy_eez', 'Netherlands':'Nether_eez','Norway':'Norway_eez', 'Poland':'Poland_eez','Spain':'Spain_eez','Sweden':'Swe_eez', 'Switzerland':'Switzerlan','UK':'UK_eez'}
                
        for country in countries_keys:
            countries.append(dictionary_land_eez[country])
                   

    breakdown = breakdown_type.value

    fp_combined_base_network, fp_mask_count_base_network, fp_mask_base_network, lon, lat = functions.aggreg_2018_footprints_base_network(sites_base_network, threshold_int)
    
    
    if download_output:

        functions.save_map_texts(sites_base_network, threshold_int, sites_compare_network)

        settings = {"baseNetwork": list(sites_base_network_options.value), "compareNetwork": list(sites_compare_network_options.value), "colorBar": colorbar_choice.value, "percent": threshold_option.value, "countryDefinition": area_type.value , "countries": list(country_options.value), "weighing": breakdown_type.value, "download": download_output_option.value}

        functions.save_settings(settings)

    if len(sites_compare_network)>0:      
        
        fp_combined_compare_network, fp_mask_count_compare_network, fp_mask_compare_network, lon, lat = functions.aggreg_2018_footprints_compare_network(sites_base_network, sites_compare_network, threshold_int)
       
        vmax_see_not_see = np.max(fp_mask_count_compare_network)
        vmax_sens = np.max(fp_combined_compare_network)
        
    else:
        vmax_see_not_see= None
        vmax_sens=None

        sites_compare_network = ''
   
    with output_summed_sens_fp:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint (' + threshold_percent  + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint'
        
        else:
            pngfile = ''
            
        functions.plot_maps(fp_combined_base_network, lon, lat, linlog='', colors=colorbar, pngfile=pngfile, directory='figures_2018', unit = 'ppm /(μmol / (m²s)))', vmax=vmax_sens) 

    with output_aggreg_fp_see_not_see:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint mask (' + threshold_percent + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint_mask'

        else:
            pngfile = ''

        functions.plot_maps(fp_mask_base_network, lon, lat, vmax=1, vmin=0.001, colors=colorbar, pngfile=pngfile,directory='figures_2018', mask=True)
        
    with output_summed_fp_see_not_see:

        display(HTML('<p style="font-size:16px;text-align:center">Base network footprint mask count (' + threshold_percent + '%)</p>'))

        if download_output:
            pngfile = 'base_network_footprint_mask_count'


        else:
            pngfile = ''
        #vmin - 0.001
        functions.plot_maps(fp_mask_count_base_network, lon, lat, vmax=vmax_see_not_see, vmin=0.001, colors=colorbar, pngfile=pngfile, directory='figures_2018', unit='count')

    #HERE IF there is a compare network in addition to base network
    if len(sites_compare_network)>0:

        with output_summed_sens_fp_uploaded_fp:
            
            if download_output:
                pngfile = 'compare_network_footprint'

            else:
                pngfile = ''
    
            display(HTML('<p style="font-size:16px;text-align:center">Compare network footprint (' + threshold_percent + '%)</p>'))
            
            functions.plot_maps(fp_combined_compare_network, lon, lat, linlog='', colors=colorbar,pngfile=pngfile, directory='figures_2018', unit= 'ppm /(μmol / (m²s)))')        

       
        with output_aggreg_fp_see_not_see_uploaded_fp:
            
            if download_output:
                pngfile = 'compare_network_footprint_mask'


            else:
                pngfile = ''
     
            display(HTML('<p style="font-size:16px;text-align:center">Compare network footprint mask (' + threshold_percent + '%)</p>'))

            functions.plot_maps(fp_mask_compare_network, lon, lat, vmin=0.001, colors=colorbar, pngfile=pngfile,directory='figures_2018', mask=True)


        with output_summed_fp_see_not_see_uploaded_fp:
            
            
            if download_output:
                pngfile = 'compare_network_footprint_mask_count'


            else:
                pngfile = '' 
            
            display(HTML('<p style="font-size:16px;text-align:center;">Compare network footprint mask count (' + threshold_percent + '%)</p>'))

            functions.plot_maps(fp_mask_count_compare_network, lon, lat, vmin=1, colors=colorbar, pngfile=pngfile, directory='figures_2018', unit='count')

        with output_breakdown_countries:

            functions.breakdown_countries_compare_network(fp_mask_base_network, fp_mask_compare_network) 

        with output_header_landcover_section:
            
            if len(countries)==0:
                
                pass
            
            else:
                display(HTML('<p style="font-size:20px;text-align:left;font-weight:bold;"><br>Land cover breakdown and population</p>'))


        with breakdown_landcover_output:
           
            functions.breakdown_landcover_compare_network(countries, fp_combined_base_network, fp_mask_base_network, fp_combined_compare_network, fp_mask_compare_network, breakdown)

            
    else:
        with output_breakdown_countries:
            
            functions.breakdown_countries_base_network(fp_mask_base_network, fp_combined_base_network) 


        with output_header_landcover_section:
            

            if len(countries)==0:
                pass
            else:
                display(HTML('<p style="font-size:20px;text-align:left;font-weight:bold;"><br>Land cover breakdown and population</p>'))


        with breakdown_landcover_output:
            
            functions.breakdown_landcover(countries, fp_combined_base_network, fp_mask_base_network, breakdown)
            
    update_button.disabled = False
#-----------widgets definition ----------------
    
style_bin = {'description_width': 'initial'}


colorbar_choice_list= ['GnBu', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',\
                         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu','PuBu', 'YlGnBu', \
                         'PuBuGn', 'BuGn', 'YlGn']

heading_sites_base_network_options = Output()

with heading_sites_base_network_options:
    display(HTML('<p style="font-size:16px;font-weight:bold;">Select sites for base network</p>'))
    


sites_base_network_options= SelectMultiple(
    options=icos_list,
    style=style_bin,
    description='',
    disabled=False) 

list_selected_base_network=Textarea(
    value='',
    style=style_bin,
    placeholder='',
    description='Base network stations:',
    disabled=False
)

threshold_option = BoundedIntText(
    value=50,
    min=1,
    max=99,
    step=1,
    style=style_bin,
    description='Percent footprint(s):',
    disabled=False
)

threshold_option.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

heading_file_upload = Output()
with heading_file_upload:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;">Select sites/points of interests for compare network (optional)</p>'))
    
heading_file_upload.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left
    
sites_compare_network_options = SelectMultiple(options = all_list,
                   disabled= False)

sites_compare_network_options.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

list_selected_compare_network =Textarea(
    value='',
    style=style_bin,
    placeholder='',
    description='Compare network stations:',
    disabled=False
)

list_selected_compare_network.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left


heading_map_specifications = Output()

with heading_map_specifications:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;"><br>Map settings</p>'))
    
colorbar_choice = Dropdown(
    description='Colorbar:', 
    style=style_bin,
    options=colorbar_choice_list,
    disabled=False,
)

header_land_cover = Output()
with header_land_cover:
    display(HTML('<p style="font-size:16px;font-weight:bold;"><br>Land cover and population within <br>network(s)</p>'))
    
heading_country_options = Output()
with heading_country_options:
    display(HTML('<p style="font-size:14px;">Choose what country/countries run the analysis for: </p>'))

countries = ['Belgium', 'Czech Republic','Denmark', 'Estonia','Finland','France', 'Germany','Hungary', 'Italy', 'Netherlands', 'Norway','Poland','Spain','Sweden','Switzerland', 'UK']
country_options= SelectMultiple(
    options=countries,
    style=style_bin,
    description='',
    disabled=False)

header_area_type = Output()
with header_area_type:
    display(HTML('<p style="font-size:14px;">Choose between getting the land cover<br>breakdown of the land covered, or to include<br>the EEZ (exclusive economic zone): </p>'))

header_area_type.layout.margin = '0px 0px 0px 70px' #top, right, bottom, left

area_type=RadioButtons(
        options=['Land', 'Land + EEZ'],
        value='Land',
        description=' ',
        disabled=False)

area_type.layout.margin = '0px 0px 0px 50px' #top, right, bottom, left

heading_breakdown_choice = Output()
with heading_breakdown_choice:
    display(HTML('<p style="font-size:14px;">Choose between using the footprint masks and<br>sensitivity weighted footprints to compute the<br>ancillary data values:</p>'))

heading_breakdown_choice.layout.margin = '30px 0px 0px 0px' #top, right, bottom, left

breakdown_type=RadioButtons(
        options=[('Footprint', 'sens'), ('Footprint mask', 'mask')],
        value='sens',
        description=' ',
        disabled=False)

download_output_heading = Output()

with download_output_heading:
    
    display(HTML('<p style="font-size:16px;font-weight:bold;">Download output</p>'))
      
download_output_option=RadioButtons(
        options=[('No', False), ('Yes', True)],
        description=' ',
        disabled=False)

header_filename = Output()

with header_filename:
    display(HTML('<p style="font-size:16px;font-weight:bold;">Load settings from file (optional)</p>'))


file_name= FileUpload(
    accept='.json',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)


#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.layout.margin = '0px 0px 0px 160px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

box_base_network = VBox([heading_sites_base_network_options, sites_base_network_options, list_selected_base_network])
box_compare_network = VBox([heading_file_upload, sites_compare_network_options, list_selected_compare_network])

base_compare_combined = HBox([box_base_network, box_compare_network])

box_map_settings = HBox([colorbar_choice, threshold_option])

box_land_cover_headings = HBox([heading_country_options, header_area_type])
box_land_cover_choices = HBox([country_options, area_type])

final_row = HBox([file_name, update_button])
#Add all widgets to a VBox:
form = VBox([base_compare_combined, heading_map_specifications, box_map_settings, header_land_cover, box_land_cover_headings, box_land_cover_choices, heading_breakdown_choice, breakdown_type, download_output_heading, download_output_option, header_filename, final_row])

#Initialize form output:
form_out = Output()

output_summed_sens_fp = Output()
output_summed_sens_fp_uploaded_fp = Output()

output_summed_fp_see_not_see = Output()
output_summed_fp_see_not_see_uploaded_fp = Output()

output_aggreg_fp_see_not_see = Output()
output_aggreg_fp_see_not_see_uploaded_fp = Output()
output_breakdown_countries = Output()
breakdown_landcover_output = Output()
output_header_landcover_section = Output()

#--------------------------------------------------------------------

# OBSERVERS - what happens when change area type (between land and land + eez)
#area_type.observe(change_area_type, 'value')

sites_base_network_options.observe(change_selected_stations, 'value')
sites_base_network_options.observe(change_stations_base_network, 'value')

sites_compare_network_options.observe(change_stations_compare_network, 'value')

file_name.observe(file_set_widgets, 'value')

update_button.on_click(update_func)


#--------------------------------------------------------------------

#Open form object:
with form_out:

    if 'output_summed_sens_fp_uploaded_fp' in locals():
        
        box_footprints_sens = HBox([output_summed_sens_fp, output_summed_sens_fp_uploaded_fp])
        box_footprints_summed = HBox([output_summed_fp_see_not_see, output_summed_fp_see_not_see_uploaded_fp])
        box_footprints_aggreg = HBox([output_aggreg_fp_see_not_see, output_aggreg_fp_see_not_see_uploaded_fp])

        display(form, box_footprints_sens, box_footprints_summed, box_footprints_aggreg, output_breakdown_countries, output_header_landcover_section, breakdown_landcover_output)
        
    else:
        
        display(form, output_summed_sens_fp, output_summed_fp_see_not_see, output_aggreg_fp_see_not_see, output_breakdown_countries, output_header_landcover_section, breakdown_landcover_output)



#Display form:
display(form_out)    