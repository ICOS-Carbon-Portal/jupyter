# -*- coding: utf-8 -*-
"""
Created 2021-08-11

@author: Claudio and Ida 

"""

from ipywidgets import Dropdown, SelectMultiple, HBox, VBox, Button, Output, IntText, RadioButtons,IntProgress,IntSlider, GridspecLayout,FileUpload, BoundedIntText, Textarea, Checkbox, Select, BoundedIntText, Layout
import stiltStations
from IPython.core.display import display, HTML 
from icoscp.station import station as cpstation
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import optimize_network_functions as onf
import json
from icoscp.stilt import stiltstation

stiltstations= stiltstation.find()
# error in geocoder - located ZSF in Austria rather than Germany 
stiltstations['ZSF']['geoinfo']['name']['common'] = 'Germany'

list_2018_located = sorted([((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if v['geoinfo']])
list_2018_not_located = [(('In water' + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>11 if not v['geoinfo']]
list_2018 = list_2018_not_located + list_2018_located 
"""
stiltstations = stiltStations.getStilt()


all_list_2018 = sorted([((v['country'] + ': ' + v['name'] + ' ('+ k + ')'),k) for k,v in stiltstations.items() if '2018' in v['years'] if len(v['2018']['months'])>12])
"""

def disable_enable_update_button():    

    if len(selected_network_sites.options)>0 and total_int.value==100:

        update_button.disabled = False
       
    else:
        update_button.disabled = True

def set_settings(s):
    
    selected_network_sites.options = [station for station in list_2018 if station[1] in s['sites_to_compare']] 
    
    broad_leaf_forest.value = s["broad_leaf_forest"]
    broad_leaf_forest_int.value= s["broad_leaf_forest_int"]
    coniferous_forest.value = s["coniferous_forest"] 
    coniferous_forest_int.value = s["coniferous_forest_int"]
    mixed_forest.value = s["mixed_forest"]
    mixed_forest_int.value = s["mixed_forest_int"] 
    ocean.value = s["ocean"]
    ocean_int.value = s["ocean_int"]
    other.value = s["other"]
    other_int.value = s["other_int"]
    grass_shrub.value = s["grass_shrub"]
    grass_shrub_int.value = s["grass_shrub_int"]
    cropland.value = s["cropland"]
    cropland_int.value = s["cropland_int"]
    pasture.value = s["pasture"]
    pasture_int.value = s["pasture_int"]
    urban.value = s["urban"]
    urban_int.value = s["urban_int"]
    sens.value = s["sens"]
    sens_int.value = s["sens_int"] 
    pop.value = s["pop"]
    pop_int.value = s["pop_int"]
    point.value = s["point"]
    point_int.value = s["point_int"]
    anthro.value = s["anthro"]
    anthro_int.value = s["anthro_int"]
    total_int.value = s["total_int"]

def change_sites_network_options(c):

    current_selection = [station_tuple[1] for station_tuple in selected_network_sites.options]
    selection = set(list(sites_network_options.value) + current_selection)     
    selection_tuplelist = [station for station in list_2018 if station[1] in selection]
    selected_network_sites.options = sorted(selection_tuplelist)
    disable_enable_update_button()

def change_selected_network_sites(c):
    
    selected_network_sites.options = [station_tuple for station_tuple in selected_network_sites.options if station_tuple[1] not in selected_network_sites.value]
    
#change the weighting
def change_total(c):

    possible_variables = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, sens, pop, point, anthro]
    
    possible_variables_weights = [broad_leaf_forest_int, coniferous_forest_int, mixed_forest_int, ocean_int, other_int, grass_shrub_int, cropland_int, pasture_int, urban_int, sens_int, pop_int, point_int, anthro_int]

    total_weight_assigned = 0
    for possible_variable, possible_variable_weight in zip(possible_variables, possible_variables_weights):
        if possible_variable.value:
            total_weight_assigned = total_weight_assigned + possible_variable_weight.value 
            possible_variable_weight.disabled = False
        else:
            possible_variable_weight.disabled = True
    
    total_int.value = total_weight_assigned
        
    disable_enable_update_button()
    
def change_total_checkbox(c):

    possible_variables = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, sens, pop, point, anthro]
    
    possible_variables_weights = [broad_leaf_forest_int, coniferous_forest_int, mixed_forest_int, ocean_int, other_int, grass_shrub_int, cropland_int, pasture_int, urban_int, sens_int, pop_int, point_int, anthro_int]

    total_weight_assigned = 0
    for possible_variable, possible_variable_weight in zip(possible_variables, possible_variables_weights):
        if possible_variable.value:
            total_weight_assigned = total_weight_assigned + possible_variable_weight.value  
            possible_variable_weight.disabled = False
            
        else:
            possible_variable_weight.disabled = True
    
    total_int.value = total_weight_assigned
        
    disable_enable_update_button()

def file_set_widgets(c):
    
    uploaded_file = file_name.value
    
    #check if there is content in the dictionary (uploaded file)
    if bool(uploaded_file):
        settings_file=uploaded_file[list(uploaded_file.keys())[0]]['content']
        settings_json = settings_file.decode('utf8').replace("'", '"')
        settings_dict = json.loads(settings_json)
        set_settings(settings_dict)

#clear all the output when run the tool again
def clear_all_output():
    output_multiple_var_graph.clear_output()

#----------- start processing -----------------

def update_func(button_c):
    
    update_button.disabled = True
    clear_all_output()
    
    sites_compare=[station_tuple[1] for station_tuple in selected_network_sites.options]
    
    #want to have a combined score first (this combined score will also rank in what order the stations are shown
    variables_compare = ['Combined score']
    
    variables_weights = []

    possible_variables = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, sens, pop, point, anthro]
    
    possible_variables_weights = [broad_leaf_forest_int, coniferous_forest_int, mixed_forest_int, ocean_int, other_int, grass_shrub_int, cropland_int, pasture_int, urban_int, sens_int, pop_int, point_int, anthro_int]
    
    possible_variables_name = ['Broad leaf forest','Coniferous forest','Mixed forest', 'Ocean', 'Other', 'Grass/shrubland','Cropland','Pasture','Urban','Sensitivity', 'Population', \
                          'Point source contribution', 'Anthropogenic contribution']
    
    for possible_variable, possible_variable_name, possible_variable_weight in zip(possible_variables,possible_variables_name, possible_variables_weights) :
        
        # if check box for a variable is checked (True), add it to the list of variables being passed to the function
        if possible_variable.value:
            
            variables_compare.append(possible_variable_name)
            variables_weights.append(possible_variable_weight.value)
            
    # all values currently computed for normalized_dataframe    
    global df_saved_for_normalized
    global df_2018
    df_saved_for_normalized, df_2018 = onf.normalized_dataframe(sites_compare)

    
    with output_multiple_var_graph:
        
        onf.variables_graph_bokeh(df_saved_for_normalized, variables_compare, variables_weights)
       
    if download_settings.value:
        
        vbox_1 = VBox([header_broad_leaf_forest, HBox([broad_leaf_forest, broad_leaf_forest_int])])
        vbox_2 = VBox([header_coniferous_forest, HBox([coniferous_forest, coniferous_forest_int])])
        vbox_3 = VBox([header_mixed_forest, HBox([mixed_forest, mixed_forest_int])])
        vbox_4 = VBox([header_ocean, HBox([ocean, ocean_int])])
        vbox_5 = VBox([header_other, HBox([other, other_int])])
        vbox_6 = VBox([header_grass_shrub, HBox([grass_shrub, grass_shrub_int])])
        vbox_7 = VBox([header_cropland, HBox([cropland, cropland_int])])
        vbox_8 = VBox([header_pasture, HBox([pasture, pasture_int])])
        vbox_9 = VBox([header_urban, HBox([urban, urban_int])])
        vbox_10 = VBox([header_sens, HBox([sens, sens_int])])
        vbox_11 = VBox([header_pop, HBox([pop, pop_int])])
        vbox_12 = VBox([header_point, HBox([point, point_int])])
        vbox_13 = VBox([header_anthro, HBox([anthro, anthro_int])])
        vbox_14 = VBox([header_total_int, total_int])
        
        settings = {"sites_to_compare": sites_compare, "broad_leaf_forest":broad_leaf_forest.value, "broad_leaf_forest_int": broad_leaf_forest_int.value, "coniferous_forest":coniferous_forest.value, "coniferous_forest_int":coniferous_forest_int.value, "mixed_forest": mixed_forest.value, "mixed_forest_int":mixed_forest_int.value, "ocean": ocean.value, "ocean_int":ocean_int.value, "other":other.value, "other_int":other_int.value, "grass_shrub":grass_shrub.value, "grass_shrub_int":grass_shrub_int.value, "cropland":cropland.value, "cropland_int":cropland_int.value, "pasture":pasture.value, "pasture_int":pasture_int.value, "urban":urban.value, "urban_int":urban_int.value, "sens":sens.value, "sens_int":sens_int.value, "pop":pop.value, "pop_int":pop_int.value,"point":point.value, "point_int":point_int.value, "anthro":anthro.value, "anthro_int": anthro_int.value, "total_int":total_int.value}

        onf.save_settings(settings, directory='optimize_network')
   
    update_button.disabled = False
        
#-----------widgets definition ----------------
    
style_bin = {'description_width': 'initial'}

heading_site_selection = Output()

with heading_site_selection:
    display(HTML('<p style="font-size:20px;font-weight:bold;">Select sites to compare</p>'))

heading_sites_network_options = Output()

with heading_sites_network_options:
    display(HTML('<p style="font-size:15px;">Options (footprints available for 2018)</p>'))
    
sites_network_options= SelectMultiple(
    options=list_2018,
    rows=14,
    style=style_bin,
    description='',
    disabled=False) 

sites_network_options.layout.margin = '0px 0px 0px 0px'

heading_selected_network_sites  = Output()
with heading_selected_network_sites:
    display(HTML('<p style="font-size:15px;">Current selection (click to deselect):</p>'))

heading_selected_network_sites.layout.margin = '0px 0px 0px 70px'

selected_network_sites = SelectMultiple(
    options=(),
    style=style_bin,
    rows=14,
    description='',
    disabled=False) 

selected_network_sites.layout.margin = '0px 0px 0px 70px'


heading_weighting = Output()



with heading_weighting:
    display(HTML('<p style="font-size:20px;font-weight:bold;">Select variables and weightings</p><p style="font-size:15px;"><br>All checked variables will be included in the graph. Set a value from 0-100 to indicate their importance relative to the other variables. The total for all variables need to add up to 100. The weighting will not affect the look of the graph, only the ranking table.<br></p>'))
    
heading_weighting.layout.margin = '50px 0px 0px 0px' #top, right, bottom, left

header_broad_leaf_forest = Output()
with header_broad_leaf_forest:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Broad leaf forest</p>'))
broad_leaf_forest = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
broad_leaf_forest_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_coniferous_forest = Output()
with header_coniferous_forest:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Coniferous forest</p>'))
coniferous_forest = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
coniferous_forest_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_mixed_forest = Output()
with header_mixed_forest:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Mixed forest</p>'))
mixed_forest = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
mixed_forest_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_ocean = Output()
with header_ocean:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Ocean</p>'))
ocean = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
ocean_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_other = Output()
with header_other:
    display(HTML('<p style="font-size:15px;margin-left:5em;">Other</p>'))
other = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
other_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_grass_shrub = Output()
with header_grass_shrub:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Grass/shrubland</p>'))
grass_shrub = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
grass_shrub_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_cropland = Output()
with header_cropland:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Cropland</p>'))
cropland = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
cropland_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_pasture = Output()
with header_pasture:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Pasture</p>'))
pasture = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
pasture_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_urban = Output()
with header_urban:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Urban</p>'))
urban = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
urban_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))
 
header_sens = Output()
with header_sens:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Sensitivity</p>'))
sens = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
sens_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_pop = Output()
with header_pop:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Population </p>'))
pop = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
pop_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_point = Output()
with header_point:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Point source</p>'))
point = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
point_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_anthro = Output()
with header_anthro:
    display(HTML('<p style="font-size:15px;margin-left:4em;">Anthropogenic</p>'))
anthro = Checkbox(value=True, indent=True, layout=Layout(width='110px'))
anthro_int=BoundedIntText(value=0, max =100,min=0, layout=Layout(width='60px'))

header_total_int = Output()
with header_total_int:
    display(HTML('<p style="font-size:15px;margin-left:5em;font-weight:bold;">Total</p>'))
total_int = BoundedIntText(value=0, max=1000, min=0, indent=True, layout=Layout(width='110px'), disabled=True)

total_int.layout.margin = '0px 0px 0px 90px' #top, right, bottom, left

header_download = Output()
with header_download:
    display(HTML('<p style="font-size:15px;">Download settings</p>'))
header_download.layout.margin = '50px 0px 0px 40px' #top, right, bottom, left

download_settings = Checkbox(value=True, description='')
download_settings.layout.margin = '0px 0px 0px 40px' #top, right, bottom, left

header_filename = Output()
with header_filename:
    display(HTML('<p style="font-size:15px;">Load settings from file (optional)</p>'))

header_filename.layout.margin = '50px 0px 0px 0px' #top, right, bottom, left

file_name= FileUpload(accept='.json',multiple=False)

#Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click me',)

update_button.layout.margin = '0px 0px 0px 600px' #top, right, bottom, left
royal='#4169E1'
update_button.style.button_color=royal

box_site_options = VBox([heading_sites_network_options, sites_network_options])
box_site_selection = VBox([heading_selected_network_sites, selected_network_sites])
box_site_combined = HBox([box_site_options,box_site_selection])

vbox_1 = VBox([header_broad_leaf_forest, HBox([broad_leaf_forest, broad_leaf_forest_int])])
vbox_2 = VBox([header_coniferous_forest, HBox([coniferous_forest, coniferous_forest_int])])
vbox_3 = VBox([header_mixed_forest, HBox([mixed_forest, mixed_forest_int])])
vbox_4 = VBox([header_ocean, HBox([ocean, ocean_int])])
vbox_5 = VBox([header_other, HBox([other, other_int])])
vbox_6 = VBox([header_grass_shrub, HBox([grass_shrub, grass_shrub_int])])
vbox_7 = VBox([header_cropland, HBox([cropland, cropland_int])])
vbox_8 = VBox([header_pasture, HBox([pasture, pasture_int])])
vbox_9 = VBox([header_urban, HBox([urban, urban_int])])
vbox_10 = VBox([header_sens, HBox([sens, sens_int])])
vbox_11 = VBox([header_pop, HBox([pop, pop_int])])
vbox_12 = VBox([header_point, HBox([point, point_int])])
vbox_13 = VBox([header_anthro, HBox([anthro, anthro_int])])
vbox_14 = VBox([header_total_int, total_int])

hbox_variables1 = HBox([vbox_1,vbox_2,vbox_3,vbox_4, vbox_5])
hbox_variables2 = HBox([vbox_6,vbox_7,vbox_8,vbox_9])
hbox_variables3 = HBox([vbox_10,vbox_11,vbox_12, vbox_13, vbox_14])

vbox_settings1 = VBox([header_filename,file_name])
vbox_settings2 = VBox([header_download,download_settings])

hbox_settings = HBox([vbox_settings1, vbox_settings2])

#Add all widgets to a VBox:
form = VBox([heading_site_selection, box_site_combined, heading_weighting, hbox_variables1, hbox_variables2, hbox_variables3,hbox_settings, update_button])

#Initialize form output:
form_out = Output()

output_multiple_var_graph = Output()


#--------------------------------------------------------------------

# observers:
def observe():    

    sites_network_options.observe(change_sites_network_options, 'value')
    selected_network_sites.observe(change_selected_network_sites, 'value')
    
    #when change the int value, calculate the new total. If total == 100, enable update button to be clicked
    broad_leaf_forest_int.observe(change_total, 'value')
    coniferous_forest_int.observe(change_total, 'value')
    mixed_forest_int.observe(change_total, 'value') 
    ocean_int.observe(change_total, 'value')
    other_int.observe(change_total, 'value')
    grass_shrub_int.observe(change_total, 'value')
    cropland_int.observe(change_total, 'value')
    pasture_int.observe(change_total, 'value')
    urban_int.observe(change_total, 'value')
    sens_int.observe(change_total, 'value')
    pop_int.observe(change_total, 'value')
    point_int.observe(change_total, 'value')
    anthro_int.observe(change_total, 'value')
    
    
    broad_leaf_forest.observe(change_total, 'value')
    coniferous_forest.observe(change_total, 'value')
    mixed_forest.observe(change_total, 'value') 
    ocean.observe(change_total, 'value')
    other.observe(change_total, 'value')
    grass_shrub.observe(change_total, 'value')
    cropland.observe(change_total, 'value')
    pasture.observe(change_total, 'value')
    urban.observe(change_total, 'value')
    sens.observe(change_total, 'value')
    pop.observe(change_total, 'value')
    point.observe(change_total, 'value')
    anthro.observe(change_total, 'value')

    file_name.observe(file_set_widgets, 'value')

    update_button.on_click(update_func)

    
# start observation
observe()


#--------------------------------------------------------------------

#Open form object:
with form_out:
        
    display(form, output_multiple_var_graph)

#Display form:
display(form_out)    