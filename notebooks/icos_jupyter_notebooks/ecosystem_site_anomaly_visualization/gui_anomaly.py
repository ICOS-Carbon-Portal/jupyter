# Format read from https://peps.python.org/pep-0008/#imports.
# Standard library imports.
from datetime import date as current_date
from datetime import datetime
from pathlib import Path
import json
import os
import re
import urllib.request

# Related third party imports.
from IPython.core.display import display, HTML
from icoscp.sparql.runsparql import RunSparql
from icoscp.station import station
from ipywidgets import Dropdown, ColorPicker, HBox, Button, Output, RadioButtons, GridspecLayout
from matplotlib import pyplot as plt
import ipywidgets as widgets
import numpy as np
import pandas as pd
import requests

# Local application/library specific imports.
import plot_interface_anomaly

##############################################################################
# Note to developers/uploaders or to whom it may concern:
# The ecosystem_site_anomaly_visualization.ipynb notebook also comes as
# a package available for download from the ICOS data portal and can be
# found here: https://doi.org/10.18160/Q10G-9CTJ. Users can run this
# package locally in their own environments without any external data
# dependencies. In order to do so, users need to specify the
# `data_path` below:
#
# Path to the pre-processed flux data.
# Use this location to run the notebook package locally:
# data_path = 'ecosystem_site_anomaly_visualization/flux_data'
# Use this location to run the notebook on the ICOS Jupyter services
# (default):
data_path = '/data/project/flux_anomalies/flux_data'
#
# To ensure proper handling of permissions for file reading, writing,
# and linking on the ICOS Jupyter services, we have designated the
# "/home/user/output" directory as the destination for all notebook
# output. In case of a new version of the notebook package:
# https://doi.org/10.18160/Q10G-9CTJ we need to make sure that the
# notebook's output directory is set within the working directory
# instead.
#
# Use this location for the notebook's output when running the
# package locally ("output"):
# output_path = os.path.join('output')
# output_anomalies_path = os.path.join(
#     output_path, 'ecosystem-site-anomaly'
# )
# Use this location for the notebook's output on the ICOS Jupyter
# services ("/home/user/output/ecosystem-site-anomaly") (default):
output_path = os.path.join(os.path.expanduser('~'), 'output')
output_anomalies_path = os.path.join(
    output_path, 'ecosystem-site-anomaly'
)
if not os.path.exists(output_anomalies_path):
    os.makedirs(output_anomalies_path)
##############################################################################
button_color_able='#4169E1'
colors_negative_anomalies = {'GPP_DT_VUT_REF':'#115C0A',
                             'SW_IN_F':'#994C00',
                             'VPD_F':'#0F3957'}
colors_positive_anomalies = {'GPP_DT_VUT_REF':'#4ABF40',
                             'SW_IN_F':'#E07306',
                             'VPD_F':'#06BBE0'}

# site information for dropdowns and for the overview map. 
sites_dataframe = station.getIdList('ES')

path_ten = os.path.join(data_path, 'FULLSET_DD', 'ten_year')
path_twenty = os.path.join(data_path, 'FULLSET_DD', 'twenty_year')

# use data from one variable to list all the available sites:
data_2010_2020 = pd.read_csv(os.path.join(data_path, 'all_sites_2010_2020_GPP_DT_VUT_REF_v2.csv'))

# make a tuple for use in the dropdowns
list_all_2010_2020 = list(data_2010_2020.columns)[5:]
list_all_2010_2020 = sorted(list_all_2010_2020)
dropdown_tuple_2010_2020 = [(list(sites_dataframe.loc[sites_dataframe['id'] == (site_string.split('_')[0])]['name'])[0] + ' (' + site_string.split('_')[0] + ')', site_string) for site_string in list_all_2010_2020 if not 'std' in site_string]

# same as above but for the full reference period
data_2000_2020 = pd.read_csv(os.path.join(data_path, 'all_sites_2000_2020_GPP_DT_VUT_REF_v2.csv'))

list_all_2000_2020 = list(data_2000_2020.columns)[5:]
list_all_2000_2020 = sorted(list_all_2000_2020)
dropdown_tuple_2000_2020 = [(list(sites_dataframe.loc[sites_dataframe['id'] == (site_string.split('_')[0])]['name'])[0] + ' (' + site_string.split('_')[0] + ')', site_string) for site_string in list_all_2000_2020 if not 'std' in site_string]

# information (lat/lon) for the map
list_site_ids_2010_2020 = [column.split('_')[0] for column in data_2010_2020.columns[4:]]
list_site_ids_2000_2020 = [column.split('_')[0] for column in data_2000_2020.columns[4:]]

# filtered pandas dataframes. Contains lat and lon columns.
filtered_2010_2020 = sites_dataframe.loc[sites_dataframe['id'].isin(list_site_ids_2010_2020)]
filtered_2000_2020 = sites_dataframe.loc[sites_dataframe['id'].isin(list_site_ids_2000_2020)]

# the overview map will show from start, but the user can change this. 
global map_showing
map_showing = True

# get pandas dataframe with links to the different sites landing pages (and in turn citation strings):
query = '''
prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
prefix prov: <http://www.w3.org/ns/prov#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
select ?dobj ?hasNextVersion ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd
where {
VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/miscFluxnetArchiveProduct>}
?dobj cpmeta:hasObjectSpec ?spec .
BIND(EXISTS{[] cpmeta:isNextVersionOf ?dobj} AS ?hasNextVersion)
?dobj cpmeta:hasSizeInBytes ?size .
?dobj cpmeta:hasName ?fileName .
?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .
?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .
?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .
FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
FILTER( '2010-01-01T00:00:00.000Z'^^xsd:dateTime >= ?timeStart ) 
VALUES ?keyword {"Warm Winter 2020"^^xsd:string}
?dobj cpmeta:hasKeyword ?keyword
}
order by desc(?submTime)
'''
result = RunSparql(query, 'pandas')   # look at the documentation for different outputformats...
result.run()
df_ecosystem = result.data()

#--------definition of general functions--------------

def return_link_es_data(site_name):
    df_ecosystem_selected = df_ecosystem.loc[df_ecosystem['fileName'].str.contains(site_name)]
    
    link_landingpage = df_ecosystem_selected['dobj'].values[0]
    
    return link_landingpage

# get the data for the selected site
def return_year_data(reference_path, site_name, year, variable):
    
    str_date_start = str(year) + '0101'

    str_date_end = str(year) + '1231'

    for (path, dirs, files) in os.walk(reference_path):
        for file in files:

            if "checkpoint" not in file:

                if site_name in file:

                    df = pd.read_csv(path_ten + "/" + file)          

                    df_time = df.loc[(df['TIMESTAMP'] >= int(str_date_start)) &(df['TIMESTAMP'] <= int(str_date_end))]
                    
                    if variable == 'GPP_DT_VUT_REF':
                        variable_qc = 'NEE_VUT_REF_QC'
                    if variable == 'SW_IN_F':
                        variable_qc = 'SW_IN_F_QC'
                    if variable == 'VPD_F':
                        variable_qc = 'VPD_F_QC'

                    df_time = df_time[["TIMESTAMP", variable, variable_qc]]

                    month= [int(str(time)[4:6]) for time in list(df_time['TIMESTAMP'])]
                    df_time['month'] = month

                    day = [int(str(time)[6:8]) for time in list(df_time['TIMESTAMP'])]
                    df_time['day'] = day

                    df_time = df_time.drop(df_time[(df_time.month == 2) & (df_time.day == 29)].index)
                    
                    df_time_for_merge = pd.DataFrame()
                    
                    df_time_for_merge["TIMESTAMP"] = df_time["TIMESTAMP"]
                    
                    df_time_qc = df_time.loc[df_time[variable_qc] > 0.7]
                
                    df_time_qc_full = pd.merge(df_time_for_merge, df_time_qc, how='left', left_on="TIMESTAMP", right_on = "TIMESTAMP")

                    list_values = list(df_time_qc_full[variable])
                    
                    return list_values

#--------definition of event-functions--------------
# what happens when the reference time period is changed (2010-2020 or 2000-2020)
def change_reference_period(c): 

    # clear previous output
    output_plot_anomalies.clear_output()
    
    update_button.disabled = True
    color_a_pos.disabled = True
    color_b_pos.disabled = True
    color_a_neg.disabled = True
    color_b_neg.disabled = True
    variable_a.disabled = True
    variable_b.disabled = True
    
    # make sure the new 'options' are not selected by "unobserving" the widgets.
    unobserve()
    if reference_period.value=='2010-2020':        
        site_choice_a.options=dropdown_tuple_2010_2020
        site_choice_b.options=dropdown_tuple_2010_2020
    if reference_period.value=='2000-2020':       
        site_choice_a.options= dropdown_tuple_2000_2020
        site_choice_b.options= dropdown_tuple_2000_2020
    site_choice_a.value=None 
    site_choice_b.value=None 
    
    # reset the data fields
    s_year_a.options = []
    s_year_b.options = []

    # make sure future changes are observed again
    observe()
    
def change_site_a(c): 
    
    output_plot_anomalies.clear_output()
    
    update_button.disabled = False    
    color_a_pos.disabled = False
    color_a_neg.disabled = False
    selection = site_choice_a.value
    
    selected_site = selection.split("_")[0]
    
    selected_period = selection.split("_")[1]
    
    if selected_period == '2010':
        path_selected = path_ten
    else:
        path_selected = path_twenty
        
    for (path, dirs, files) in os.walk(path_selected):
        for file in files:

            if "checkpoint" not in file:

                if selected_site in file:

                    start_year = int(file[-20:-16])
                    
    years = list(range(start_year, 2021))

    s_year_a.options=years 
    s_year_a.value = min(years)
    variable_a.disabled = False
    
def change_site_b(c): 
    output_plot_anomalies.clear_output()
    
    if variable_a.value != variable_b.value:
        color_b_pos.disabled = False
        color_b_neg.disabled = False
    
    selection = site_choice_b.value
    
    selected_site = selection.split("_")[0]
    
    selected_period = selection.split("_")[1]
    
    if selected_period == '2010':
        path_selected = path_ten
    else:
        path_selected = path_twenty
        
    
    for (path, dirs, files) in os.walk(path_selected):
        for file in files:

            if "checkpoint" not in file:

                if selected_site in file:

                    start_year = int(file[-20:-16])
                    
    years = list(range(start_year, 2021))

    s_year_b.options=years 
    s_year_b.value = min(years)
    
    variable_b.disabled = False

def change_year_a(c):
    output_plot_anomalies.clear_output()

def change_year_b(c):
    output_plot_anomalies.clear_output()
    
def change_variable_a(c):
    output_plot_anomalies.clear_output()
    color_a_pos.value=colors_positive_anomalies[variable_a.value]
    color_a_neg.value=colors_negative_anomalies[variable_a.value]
    
    if site_choice_b.value is not None and variable_a.value != variable_b.value:
        color_b_pos.disabled = False
        color_b_neg.disabled = False
        reset_b_pos.disabled = False
        reset_b_neg.disabled = False
    else:
        color_b_pos.disabled = True
        color_b_neg.disabled = True
        reset_b_pos.disabled = True
        reset_b_neg.disabled = True
    
def change_variable_b(c):
    output_plot_anomalies.clear_output()
    if variable_a.value != variable_b.value:
        color_b_pos.disabled = False
        color_b_neg.disabled = False
        reset_b_pos.disabled = False
        reset_b_neg.disabled = False
        color_b_pos.value=colors_positive_anomalies[variable_b.value]
        color_b_neg.value=colors_negative_anomalies[variable_b.value]
        
    else:
        color_b_pos.disabled = True
        color_b_neg.disabled = True
        reset_b_pos.disabled = True
        reset_b_neg.disabled = True
        color_b_pos.value=color_a_pos.value
        color_b_neg.value=color_a_neg.value
            
def change_color_a_pos(c):
    if variable_a.value == variable_b.value:
        color_b_pos.value = color_a_pos.value
        
def change_color_a_neg(c):
    if variable_a.value == variable_b.value:
        color_b_neg.value = color_a_neg.value
    
def hide_map_func(button_c):
    hide_map_button.disabled = True
    if hide_map_button.description == 'Hide map':
        overview_map.clear_output()
        hide_map_button.description = 'Show map'
    
    else:
        with overview_map:
            map_of_sites = plot_interface_anomaly.map_of_sites(filtered_2010_2020, filtered_2000_2020)
            display(map_of_sites)
            
        hide_map_button.description = 'Hide map'
    hide_map_button.disabled = False

# what happens when the "color reset" buttons are clicked
def func_reset_a_pos(c):
    color_a_pos.value = colors_positive_anomalies[variable_a.value]
    
def func_reset_a_neg(c):
    color_a_neg.value = colors_negative_anomalies[variable_a.value]
    
def func_reset_b_pos(c):
    color_b_pos.value = colors_positive_anomalies[variable_b.value]
    
def func_reset_b_neg(c):
    color_b_neg.value = colors_negative_anomalies[variable_b.value]

# what happens when the tool is run (update button clicked) 
def update_func(button_c):
    
    # not able to use the update button while the tool is running:
    update_button.disabled = True
    
    # display the overview map 
    display(map_of_sites)
    
    # clear previous output
    output_citation.clear_output()
    message.clear_output()
    output_plot_anomalies.clear_output()
    
    # access the some of the variables from the gui-selection (some come later when they are used- access with .value).
    reference = reference_period.value
    variable_a_value = variable_a.value
    variable_b_value = variable_b.value
    
    # put colors into dictionaries which are passed to the functions. 
    colors_positive_anomalies_dict = {variable_b_value:color_b_pos.value, variable_a_value:color_a_pos.value}
    colors_negative_anomalies_dict = { variable_b_value:color_b_neg.value, variable_a_value:color_a_neg.value}
 
    # access the correct reference data depending on the gui-selection
    if reference == "2010-2020":
        path_selected = path_ten
        reference_string = '2010_2020'
    else:
        path_selected = path_twenty    
        reference_string = '2000_2020'
        
    
    site_a = site_choice_a.value
    selected_site_a = site_a.split("_")[0]
    
    # the file names only have the site name as an "id form".
    # here, use the id (selected_site_a - from the site choice widget) to access the full name
    # from the sites_dataframe (loaded using the carbon portal library icoscp.station module)
    selected_site_a_name = list(sites_dataframe.loc[sites_dataframe['id'] == selected_site_a]['name'])[0]
                            
    # get the url for the site landingpage to be used as a link with the output from running the tool.
    landingpage_site_a = return_link_es_data(selected_site_a)
    
    # use the url to the site landing page to access its metadata. 
    json_url = landingpage_site_a + '/json_file.json'
    json_url_response = urllib.request.urlopen(json_url)
    json_data = json.loads(json_url_response.read())
    citation_string_site_a = json_data['references']['citationString']
    
    # access the data for the slected year (to be compared to the selected reference data)
    year_a = s_year_a.value
    
    column_name_a = selected_site_a + "_" + str(year_a)
    
    # return year data is a function defined in this py-file. 
    values_site_a = return_year_data(path_selected, selected_site_a, year_a, variable_a_value)
    
    # reference data is pre-computed and accessed depending on what variable was selected. 
    # the pre-computed data has columns for all sites, for instance: Dk-Sor_2000_2020. The name of the file has both the variable name and reference period in the name, for instance: all_sites_2000_2020_SW_IN_F
    reference_data_a_df = pd.read_csv(os.path.join(data_path, 'all_sites_' + reference_string + '_' + variable_a_value + '_v2.csv'))
    reference_data_a = reference_data_a_df[selected_site_a + "_" + reference_string]
    reference_data_a_std = reference_data_a_df[selected_site_a + "_" + reference_string + '_std']
    reference_data_a_std_count = reference_data_a_df[selected_site_a + "_" + reference_string + '_std_count']
    reference_data_a_std_month = reference_data_a_df[selected_site_a + "_" + reference_string + '_std_month']
    reference_data_a_std_month_count = reference_data_a_df[selected_site_a + "_" + reference_string + '_std_month_count']
    
    # create the dataframe with only the data that is necessary to create the figures.
    # it has the daily average reference data and daily average data for the specific year and variable. 
    # create the empty dataframe to fill
    df_final = pd.DataFrame()
    
    # add and fill fields for month and day
    df_final['month'] =reference_data_a_df["month"]
    df_final['day'] = reference_data_a_df["day"]
    
    # dictionary with filed names (used in df_final and accessed in the plot py file
    reference_values_a_col_name = selected_site_a + "_" + reference_string + '_' + variable_a_value
    sd_a_col_name = selected_site_a + "_" + reference_string + '_' + variable_a_value + '_std'
    sd_a_col_name_count = selected_site_a + "_" + reference_string + '_' + variable_a_value + '_std_count'
    sd_a_month_col_name = selected_site_a + "_" + reference_string + '_' + variable_a_value + '_std_month'
    sd_a_month_col_name_count = selected_site_a + "_" + reference_string + '_' + variable_a_value + '_std_month_count'
    values_a_col_name = column_name_a + '_' + variable_a_value
    
    site_b = site_choice_b.value
    if site_b is not None:
        year_b = s_year_b.value
        selected_site_b = site_b.split("_")[0]
        reference_values_b_col_name =selected_site_b + "_" + reference_string + '_' + variable_b_value
        sd_b_col_name = selected_site_b + "_" + reference_string + '_' + variable_b_value + '_std'
        sd_b_col_name_count = selected_site_b + "_" + reference_string + '_' + variable_b_value + '_std_count'
        sd_b_month_col_name = selected_site_b + "_" + reference_string + '_' + variable_b_value + '_std_month'
        sd_b_month_col_name_count = selected_site_b + "_" + reference_string + '_' + variable_b_value + '_std_month_count'
        values_b_col_name = selected_site_b + "_" + str(year_b) + '_' + variable_b_value
        #True if (selection_dict["variable_a_value"] == selection_dict["variable_b_value"]) else False
    else:
        reference_values_b_col_name = None
        sd_b_col_name = None
        sd_b_col_name_count = None
        sd_b_month_col_name = None
        sd_b_month_col_name_count = None
        values_b_col_name = None

   
    df_final[reference_values_a_col_name] = reference_data_a
    df_final[sd_a_col_name] = reference_data_a_std
    df_final[sd_a_col_name_count] = reference_data_a_std_count
    df_final[sd_a_month_col_name] = reference_data_a_std_month
    df_final[sd_a_month_col_name_count] = reference_data_a_std_month_count
    
    
    # if a second site is selected
    if site_b is not None:     
            
        selected_site_b_name = list(sites_dataframe.loc[sites_dataframe['id'] == selected_site_b]['name'])[0]
                            
        landingpage_site_b = return_link_es_data(selected_site_b)
        
        json_url = landingpage_site_b + '/json_file.json'
        json_url_response = urllib.request.urlopen(json_url)
        json_data = json.loads(json_url_response.read())

        citation_string_site_b = json_data['references']['citationString']

        # set site_b to None in case the same site and year as site a
        if site_b == site_a and year_a == year_b and variable_a_value == variable_b_value:
            site_b = None
    
    # site b might NOW be None (see above lines) - "set site_b to None in case the same site and year as site a"
    # therefore, check if None again:
    if site_b is not None: 
        column_name_b = selected_site_b + "_" + str(year_b)
        values_site_b = return_year_data(path_selected, selected_site_b, year_b, variable_b_value)
        reference_data_b_df = pd.read_csv(os.path.join(data_path, 'all_sites_' + reference_string + '_' + variable_b_value + '_v2.csv'))
        
        reference_data_b = reference_data_b_df[selected_site_b + "_" + reference_string]
        reference_data_b_std = reference_data_b_df[selected_site_b + "_" + reference_string + '_std']
        reference_data_b_std_count = reference_data_b_df[selected_site_b + "_" + reference_string + '_std_count']
        reference_data_b_std_month = reference_data_b_df[selected_site_b + "_" + reference_string + '_std_month']
        reference_data_b_std_month_count = reference_data_b_df[selected_site_b + "_" + reference_string + '_std_month_count']
        
        df_final[reference_values_b_col_name] = reference_data_b
        df_final[sd_b_col_name] = reference_data_b_std
        df_final[sd_b_col_name_count] = reference_data_b_std_count
        df_final[sd_b_month_col_name] = reference_data_b_std_month
        df_final[sd_b_month_col_name_count] = reference_data_b_std_month_count
        
        # this order of the columns need to remain which is why column a is insert here
        df_final[values_a_col_name] = values_site_a
        df_final[values_b_col_name] = values_site_b
    else:
        # this order of the columns need to remain which is why column a is insert here
        df_final[values_a_col_name] = values_site_a
        selected_site_b = None
        selected_site_b_name = None
        year_b = None
    
    df_final.month = df_final.month.astype(int)
    df_final.day = df_final.day.astype(int)

    # date time string for the name of the saved file
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
    
    data_filename = \
        f'{output_anomalies_path}/flux_anomaly_data_{dt_string}.csv'

    number_cols = len(df_final.columns)
    
    semi_colons = ";" * number_cols
    # open a file with the specified filename and write meta data to it 
    f = open(data_filename, 'a')
    f.write('Reference period columns (columns without years in title): Averages and standard deviations of daily average values ("DD" in flux product) over the years '  + reference_string + ' for selected site(s)' + semi_colons + '\n')
    f.write('Analysed year(s) column(s) (column titel(s) contains the analysed year of selected site(s)): Daily average values ("DD" in flux product).;\n')
    f.write('Variable definitions (found in column titles: one or two of these variables):;\n')
    f.write('Gross Primary Production daytime in micromol/m2/s (GPP_DT_VUT_REF);\n')
    f.write('Shortwave incoming radiation in W/m2 (SW_IN_F);\n')
    f.write('Vapor pressure deficit in hPa (VPD_F);\n')
    f.write('Identify the selected year(s) for the site(s) based on the column heading ending with the variable name(s). The reference period(s) are provided with a dash indicating the start and end of each reference period.;\n')
    f.write('The column(s) ending with '_std_count' represent the number of times that a specific date (row) within the reference period was flagged. These flagged values were excluded from the calculation of the standard deviation value (found in columns ending with "_std").;\n')
    f.write('The column(s) ending with "_std_count_month" represent the number of times a day within a specific month (referenced in the"month" column) was flagged during the reference period. These flagged values were excluded from the calculation of the standard deviation value (found in columns ending with "_std_month"). Note that the values in these columns are the same when the month is the same.;\n')
    
    date_today = current_date.today()
    f.write('Date of file creation: '+ str(date_today) +';\n')
    f.write('Cite the data:; \n')
    f.write(citation_string_site_a + ';\n')
    if site_b is not None and variable_a_value != variable_b_value:
        
        f.write(citation_string_site_b + ';\n')
        
    f.write('Cite the notebook package if a figure is used:; \n')
    f.write('Storm, I., Klasen, V,, 2023. Ecosystem site anomalies notebook tool. ICOS ERIC - Carbon Portal. https://doi.org/10.18160/0GP0-HW10;\n')
    # Save the dataframe, so it can be downloaded as a csv-file in a
    # folder called "ecosystem_site_anomaly_visualization_output" under
    # "/home/user/output/" directory.
    df_final.to_csv(f,index=False, sep=";")

    # dictionary with the information from the gui to pass to the plot interface
    selection_dict = {"reference":reference,"selected_site_a":selected_site_a,"selected_site_a_name":selected_site_a_name,"year_a":year_a,"selected_site_b":selected_site_b,"selected_site_b_name":selected_site_b_name,"year_b":year_b,"variable_a_value":variable_a_value,"variable_b_value":variable_b_value, \
"reference_values_a": reference_values_a_col_name,
"sd_a": sd_a_col_name,
"sd_a_month":sd_a_month_col_name,
"reference_values_b": reference_values_b_col_name,
"sd_b": sd_b_col_name,
"sd_b_month":sd_b_month_col_name,
"values_a": values_a_col_name,
"values_b":values_b_col_name}
 
    # message which will change of the selections the user have done.
    # it shows the selected site names and links to their landing page(s).
    with message:

        if site_b is not None:
            
            display(HTML('<p style="font-size:16px"><b>Selected sites:</b><br><a href="' + landingpage_site_a +'" target="_blank">' + selected_site_a_name + '</a> (year ' + str(year_a) + ', ' + variable_a_value + \
                         ') and <a href="' + landingpage_site_b +'" target="_blank">' + selected_site_b_name +\
                        '</a> (year ' + str(year_b) + ', ' + variable_b_value + '). Their daily average daytime flux values are compared to those of the reference period ' + reference +'.</p>'))
        else:
            display(HTML('<p style="font-size:16px"><b>Selected site:</b><br><a href="' + landingpage_site_a +'" target="_blank">' + selected_site_a_name + '</a> (year ' + str(year_a) + ', ' + variable_a_value + \
                         '). Its daily average daytime flux values are compared to those of the reference period ' + reference +'.</p>'))
    
    # show the citation strings associated with the output figures
    with output_citation:
        
        # in case of two citation strings:
        # not two if site b is not defined, and not two if it is data from the same site. 
        if site_b is not None and citation_string_site_a!=citation_string_site_b:
        
            display(HTML('<p style="font-size:16px"><b>Citation:</b><br>' + citation_string_site_a + '<br>' + citation_string_site_b +'<br><br></p>'))
            
        # else only one citation string
        else:
            display(HTML('<p style="font-size:16px"><b>Citation:</b><br>' + citation_string_site_a +'<br><br></p>'))
        
        # specify output (yearly or monthly) - looks nicer to have in this widget than the next.
        display(HTML('<p style="font-size:16px"><b>Specify output:</b><br></p>'))
    
    with output_plot_anomalies:

        # Some updates to the dataframe to account for the flagged data
        
        # not show standard deviation values in case of no values
        # here when showing days in a month
        df_final[sd_a_col_name] = np.where(np.isnan(df_final[values_a_col_name]), np.nan, df_final[sd_a_col_name])
        # here when showing months in a year: all values in the month must be missing
        count_vals_per_month = df_final.groupby('month', dropna=True).count()
        # list of months that have no values:
        count_vals_per_month = count_vals_per_month.loc[count_vals_per_month[values_a_col_name] == 0]
        exclude_std_months = list(count_vals_per_month.index)         
        df_final[sd_a_month_col_name] = np.where(np.isin(df_final["month"], exclude_std_months), np.nan, df_final[sd_a_month_col_name])
   
        # not show standard deviation bar in case of too few values (set to five currently). Only up to 11 for individual days std.
        # assumes all reference periods will have enough values for the standard deviations for months
        df_final[sd_a_col_name] = np.where(df_final[sd_a_col_name_count]>5,  np.nan, df_final[sd_a_col_name])
                       
        if site_b is not None:

            # same updates made to the data associated with the second selection
            df_final[sd_b_col_name] = np.where(np.isnan(df_final[values_b_col_name]), np.nan, df_final[sd_b_col_name])
            count_vals_per_month = count_vals_per_month.loc[count_vals_per_month[values_b_col_name] == 0]
            exclude_std_months = list(count_vals_per_month.index)         
            df_final[sd_b_month_col_name] = np.where(np.isin(df_final["month"], exclude_std_months), np.nan, df_final[sd_b_month_col_name])
            
            df_final[sd_b_col_name] = np.where(df_final[sd_b_col_name_count]>5,  np.nan, df_final[sd_b_col_name])

        plot_interface_anomaly.plot_anomalies(df_final, data_filename, selection_dict, colors_positive_anomalies_dict, colors_negative_anomalies_dict)
            
    # after the tool is done running, it is possible to make a new tool run (hence the update buttn can be pressed given that the necessary widgets are populated)
    update_button.tooltip='Click to start the run'
    update_button.style.button_color=button_color_able  
    update_button.disabled = False
    
#-----------widgets definition -----------------
# in the order they appear in the GUI. 

style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height':'initial'}

hide_map_button = Button(description='Hide map',
                       disabled=False,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click to confirm selection',
                       layout = layout,
                       style = style)
hide_map_button.style.button_color='#40a837'

overview_map = Output()
with overview_map:
    map_of_sites = plot_interface_anomaly.map_of_sites(filtered_2010_2020, filtered_2000_2020)
    display(map_of_sites)

header_site = Output()
with header_site:
    display(HTML('<p style="font-size:15px;font-weight:bold;">Select reference period and sites/years to analyse: </p>'))
    
reference_period=RadioButtons(
        options=['2010-2020', '2000-2020'],
        value='2010-2020',
        layout = layout,
        style = style,
        disabled=False)

site_choice_a = Dropdown(options = dropdown_tuple_2010_2020,
                   description = 'Site a*',
                   value=None,
                   disabled= False,
                   layout = layout,
                   style = style)

#Create a Dropdown widget with year values (start year):
s_year_a = Dropdown(options = [],
                  description = 'Year a*',
                  disabled= False,
                   layout = layout,
                   style = style)

variable_a = Dropdown(options = [('Daytime Gross Primary Production (GPP_DT_VUT_REF)', "GPP_DT_VUT_REF"), ('Shortwave incoming radiation (SW_IN_F)', "SW_IN_F"), ('Vapor pressure deficit (VPD_F)', "VPD_F")],
                   description = 'Variable a*',
                   value ="GPP_DT_VUT_REF",
                   disabled= True,
                   layout = layout,
                   style = style)

color_a_pos = ColorPicker(
    disabled=True,
    value=colors_positive_anomalies['GPP_DT_VUT_REF'],
    description='Color positive:',
    layout = layout,
    style=style)

reset_a_pos = Button(disabled=False,
       tooltip='Click for default color',
       icon = 'redo')

reset_a_pos.layout.width='35px'

color_a_neg = ColorPicker(
    disabled = True,
    value=colors_negative_anomalies['GPP_DT_VUT_REF'],
    description='Color negative:',
    layout = layout,
    style=style)

reset_a_neg = Button(disabled=False,
       tooltip='Click for default color',
       icon = 'redo')
reset_a_neg.layout.width='35px'

site_choice_b = Dropdown(options = dropdown_tuple_2010_2020,
                   description = 'Site b (optional)',
                   value=None,
                   disabled= False,
                   layout = layout,
                   style = style)

#Create a Dropdown widget with year values (start year):
s_year_b = Dropdown(options = [],
                  description = 'Year b (optional)',
                  disabled= False,
                  layout = layout,
                  style = style)

variable_b = Dropdown(options = [('Daytime Gross Primary Production (GPP_DT_VUT_REF)', "GPP_DT_VUT_REF"), ('Shortwave incoming radiation (SW_IN_F)', "SW_IN_F"), ('Vapor pressure deficit (VPD_F)', "VPD_F")],
                  description = 'Variable b (optional)',
                  value = "GPP_DT_VUT_REF",
                  disabled= True,
                   layout = layout,
                   style = style)

color_b_pos = ColorPicker(
    disabled = True,
    value=colors_positive_anomalies['GPP_DT_VUT_REF'],
    description='Color positive if variable different than site a:',
    layout = layout,
    style=style)

reset_b_pos = Button(disabled=True,
       tooltip='Click for default color',
       icon = 'redo')

reset_b_pos.layout.width='35px'

color_b_neg = ColorPicker(
    disabled = True,
    value=colors_negative_anomalies['GPP_DT_VUT_REF'],
    description='Color negative if variable different than site a:',
    layout = layout,
    style=style)

reset_b_neg = Button(disabled=True,
       tooltip='Click for default color',
       icon = 'redo')

reset_b_neg.layout.width='35px'

#Create a Button widget to control execution:
update_button = Button(description='Confirm selection',
                       disabled=True,
                       button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click to confirm selection',
                       layout = layout,
                       style = style)

update_button.style.button_color=button_color_able

#-----------GUI structure -----------------
# structure how the output should be presented 

settings_grid_1 =GridspecLayout(5, 2)

settings_grid_1[0:1, 0:1] = header_site

settings_grid_1[1:2, 0:1] = reference_period

settings_grid_1[2:3, 0:1] = site_choice_a

settings_grid_1[2:3, 1:2] = site_choice_b

settings_grid_1[3:4, 0:1] = s_year_a
settings_grid_1[3:4, 1:2] = s_year_b

settings_grid_1[4:5, 0:1] = variable_a
settings_grid_1[4:5, 1:2] = variable_b

#### here start next
settings_grid_2 =GridspecLayout(2, 12)

# four columns 
settings_grid_2[0:1, 0:5] = color_a_pos 
settings_grid_2[0:1, 5:6] = reset_a_pos
settings_grid_2[0:1, 6:11] = color_b_pos 
settings_grid_2[0:1, 11:12] = reset_b_pos

settings_grid_2[1:2, 0:5] = color_a_neg 
settings_grid_2[1:2, 5:6] = reset_a_neg
settings_grid_2[1:2, 6:11] = color_b_neg
settings_grid_2[1:2, 11:12] = reset_b_neg


#Initialize form output:
form_out = Output()

#Initialize results output widgets:
message = Output()
output_citation = Output()
output_plot_anomalies = Output()
output_plot_anomalies.layout.width = '80%'

#-----------Observers -----------------
# what happens when change ex. change start year (s_year)
def observe():    
    reference_period.observe(change_reference_period, 'value')
    site_choice_a.observe(change_site_a, 'value')
    site_choice_b.observe(change_site_b, 'value')
    s_year_a.observe(change_year_a, 'value')
    s_year_b.observe(change_year_b, 'value')
    variable_a.observe(change_variable_a, 'value')
    variable_b.observe(change_variable_b, 'value')
    color_a_pos.observe(change_color_a_pos, 'value')
    color_a_neg.observe(change_color_a_neg, 'value')
    
    # What happens when the buttons are clicked: 
    update_button.on_click(update_func)
    hide_map_button.on_click(hide_map_func)
    reset_a_pos.on_click(func_reset_a_pos)
    reset_b_pos.on_click(func_reset_b_pos)
    reset_a_neg.on_click(func_reset_a_neg)
    reset_b_neg.on_click(func_reset_b_neg)
    
def unobserve():    
    reference_period.unobserve(change_reference_period, 'value')
    site_choice_a.unobserve(change_site_a, 'value')
    site_choice_b.unobserve(change_site_b, 'value')
    s_year_a.unobserve(change_year_a, 'value')
    s_year_b.unobserve(change_year_b, 'value')
    variable_a.unobserve(change_variable_a, 'value')
    variable_b.unobserve(change_variable_b, 'value')

# start observation
observe()
    
#Open form object:
with form_out:
    display(hide_map_button, overview_map, settings_grid_1, settings_grid_2, update_button, message, output_citation, output_plot_anomalies)

#Display form:
display(form_out)