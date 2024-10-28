from sklearn import preprocessing
from sklearn.decomposition import PCA
from scipy.spatial.distance import pdist, squareform
import pandas as pd
pd.options.display.float_format = "{:,.2f}".format
import time
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from collections import Counter
import numpy as np
import seaborn as sns
import glob
import ipywidgets as widgets
from IPython.display import display, clear_output
from datetime import datetime
import json
from IPython.display import display, HTML
import matplotlib.pyplot as plt
import geopandas as gpd
import folium

# make pandas tables interactive.
pd.set_option('display.max_rows', 1000)
from itables import init_notebook_mode
init_notebook_mode(all_interactive=True)
import itables.options as opt
opt.lengthMenu = [15, 50, 100]
opt.maxRows = 1000
opt.maxBytes=0


def create_merged_attribute_file():
 

    # Directory where your CSV files are located
    csv_files_path = 'variable_files/*.csv'

    # List all CSV files in the directory
    csv_files = glob.glob(csv_files_path)

    # Initialize an empty list to hold dataframes
    dataframes = []

    # Load each CSV file into a dataframe and append it to the list
    for file in csv_files:

        if 'all_variables' in file:
            continue 

        df = pd.read_csv(file)

        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns = {'Unnamed: 0'}, axis = 1)

        # Common name for cities
        if 'City' in list(df.columns):
            df = df.rename(columns = {'City':'city_name'})

        if 'city' in list(df.columns):
            df = df.rename(columns = {'city':'city_name'})

        dataframes.append(df)

    # Merge all dataframes on the common column city_name
    merged_df = pd.merge(dataframes[0], dataframes[1], on='city_name')

    for i in range(2, len(dataframes)):
        merged_df = pd.merge(merged_df, dataframes[i], on='city_name')

    # Save the merged dataframe to a new CSV file
    merged_df.to_csv('variable_files/all_variables.csv', index=False, encoding = 'utf-8-sig')
    print('file variable_files/all_variables.csv re-created')


def column_selection(callback):
    merged_df = pd.read_csv('variable_files/all_variables.csv')
    
    general_info = {"Total population year 2018": "Total_pop",
                    "Share of the city containing 50% of the population":"area_50percent_pop",
                    "Area in km2": "area",
                    "Distance to closest city in km": "dist_closest_city",
                    "Share of times the wind is >2m/s Jan/Feb 2018 hours 9 - 18": "share_over_2m_s",
                    "Share of wind from dominant wind direction Jan/Feb 2018 hours 9 - 18 when wind is >2m/s": "dominant_wind_share",
                    "Average share of cloud cover (fraction between 0 and 1) at 11:00UTC year 2018": "share_cloud_over30percent",
                    "Average share of cloud cover (fraction between 0 and 1) at 11:00UTC year summer (J+J) 2018": "share_cloud_over30percent_summer",
                    "Average share of cloud cover (fraction between 0 and 1) at 11:00UTC year winter (J+F) 2018": "share_cloud_over30percent_winter"}

    land_cover_general_info = {  
        "Share of vegetation (%)": "vegetation",
        "The percent of edge cells for vegetated areas": "veg_share_edge_area",
        "Share of water in the buffer zone":"share_water_buffer",
        "Share of cropland in the buffer zone":"40_buffer",
        "Share of cropland in the buffer zone in the dominant wind direction. Only when wind is >2m/s.":"40_buffer_dom_wind",
        "Share of vegetation in the buffer zone":"share_vegetation_buffer"
    }
    
    land_cover_info = {
        10: "Trees",
        20: "Shrubland",
        30: "Grassland",
        40: "Cropland",
        50: "Built-up",
        60: "Bare / sparse vegetation",
        70: "Snow and ice",
        80: "Permanent water bodies",
        90: "Herbaceous wetland",
        100: "Moss and lichen"
    }


    co2_info_tno = {
        "Total emissions 2018 (kg)": "co2_ff_total",
        "Total emissions 2018 per km2": "co2_ff_total_km2",
        "Total emission 2018 per person": "co2_ff_total_pop",
        "Share of point source emissions": "co2_ff_share_point_sources_total",
        "Total non-point source emissions 2018 (kg)": "co2_ff_total_no_point",
        "Total non-point emission per km²": "co2_ff_total_no_point_km2",
        "Total non-point source emissions 2018": "co2_ff_total_no_point_pop",
        "Share of city area containing 50% of the emissions": "area_percentage",
        "Emission intensity 20km buffer zone": "co2_ff_total_20km_buffer_km2",
        "Emission intensity (kg CO2 / km2) within 20km buffer in the dominant wind direction (Jan/Feb 2018 hours 9 - 18). Only when wind is >2m/s.": "emiss_intensity_buff_dom_wind_jan_feb_9_18_2m_s",
        "Share of point sources in the buffer zone": "co2_ff_total_20km_buffer_share_point_sources",
        "Count point sources in the buffer zone": "co2_ff_total_20km_buffer_count_point_sources",
        "Public power (total share)": "co2_ff_A_share",
        "Public power (share point sources)": "co2_ff_share_point_sources_A",
        "Public power (count point sources)": "co2_ff_count_point_sources_A",
        "Industry (total share)": "co2_ff_B_share",
        "Industry (share point sources)": "co2_ff_share_point_sources_B",
        "Industry (count point sources)": "co2_ff_count_point_sources_B",
        "Other stationary combustions (total share)": "co2_ff_C_share",
        "Road transport (total share)": "co2_ff_F_share",
        "Shipping (total share)": "co2_ff_G_share",
        "Spatial uncertainty: % of the emissions": "share_uncertainty_total"
    }

    co2_info_odiac = {
        "Total emissions 2018 ODIAC (kg)": "co2_ff_total_ODIAC"
    }

    urban_topography_info = {
        "Mean building height in meters (based on a dataset with 100x100m grids)": "mean_built_up"
    }

    natural_topography_info = {
        "Share of flat areas (classes 24 and 34)": "share_flatness",
        "Average size of patches in km2 where elevation is within 20m": "Mean_20contour",
        "Standard deviation of patch sizes where elevation is within 20m": "Std_20contour",
        "Variability of patch sizes where elevation is within 20m": "Var_20contour",
        "Average Terrain Ruggedness index": "Mean_TRI"
    }
    
    radiocarbon_info = {
        "Average nuclear contamination winter (J+F) afternoons (12 and 15 UTC) in permil": "average_nuclear_contamination_permil_winter",
        "Share of days >0.5 permil nuclear contamination winter": "share_daily_average_over_0_5_permil_winter",
        "Share of days >0.3 permil nuclear contamination winter": "share_daily_average_over_0_3_permil_winter",
        "Average ffCO2 STILT signal winter": "average_modelled_ffco2_signal_winter",
        "Average ffCO2 STILT signal on days >0.5 permil nuclear contamination winter": "average_modelled_ffco2_signal_days_below_0_5permil_winter",
        "Average nuclear masking potential winter (%)": "nuclear_masking_potential_winter",
        "Average representation bias due to sample selection (>0.5 permil) winter (%)": "representation_bias_sample_selection_winter"
    }
        
        

    # Function to create checkboxes with labels and set layout
    def create_checkboxes(info_dict):
        checkboxes = []
        for description, column in info_dict.items():
            checkbox = widgets.Checkbox(
                value=False, 
                description=description, 
                layout=widgets.Layout(width='90%')  # Adjust the width as needed
            )
            checkboxes.append(checkbox)
        return checkboxes

    # Create checkboxes with tooltips and wider layout for each section
    general_checkboxes = create_checkboxes(general_info)
    land_cover_general_checkboxes = create_checkboxes(land_cover_general_info)
    co2_tno_checkboxes = create_checkboxes(co2_info_tno)
    co2_odiac_checkboxes = create_checkboxes(co2_info_odiac)
    urban_topography_checkboxes = create_checkboxes(urban_topography_info)
    natural_topography_checkboxes = create_checkboxes(natural_topography_info)
    radiocarbon_checkboxes = create_checkboxes(radiocarbon_info)
    
    # Add vegetation checkboxes
    list_vegetation_classes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    vegetation_checkboxes = []
    for vegetation in list_vegetation_classes:
        checkbox = widgets.Checkbox(
            value=False, 
            description=f'{land_cover_info[vegetation]} ({vegetation})',
            layout=widgets.Layout(width='90%')
        )
        vegetation_checkboxes.append(checkbox)

    # Add hourly NEE and CO2 offset checkboxes
    hourly_nee_checkboxes = []
    for hour in range(24):
        checkbox = widgets.Checkbox(
            value=False, 
            description=f'NEE average {hour}',
            layout=widgets.Layout(width='90%')
        )
        hourly_nee_checkboxes.append(checkbox)

    hourly_offset_checkboxes = []
    for hour in range(24):
        checkbox = widgets.Checkbox(
            value=False, 
            description=f'CO2 offset {hour}',
            layout=widgets.Layout(width='90%')
        )
        hourly_offset_checkboxes.append(checkbox)

    hourly_emission_checkboxes = []
    for hour in range(24):
        checkbox = widgets.Checkbox(
            value=False, 
            description=f'CO2 emission {hour}',
            layout=widgets.Layout(width='90%')
        )
        hourly_emission_checkboxes.append(checkbox)

    # Output area for displaying the resulting DataFrame
    output = widgets.Output()

    # Function to create the subset dataframe based on selected columns
    def create_subset(change=None):
        selected_columns = [general_info[cb.description] for cb in general_checkboxes if cb.value]
        selected_columns += [land_cover_general_info[cb.description] for cb in land_cover_general_checkboxes if cb.value]
        selected_columns += [co2_info_tno[cb.description] for cb in co2_tno_checkboxes if cb.value]
        selected_columns += [co2_info_odiac[cb.description] for cb in co2_odiac_checkboxes if cb.value]
        selected_columns += [urban_topography_info[cb.description] for cb in urban_topography_checkboxes if cb.value]
        selected_columns += [natural_topography_info[cb.description] for cb in natural_topography_checkboxes if cb.value]
        selected_columns += [radiocarbon_info[cb.description] for cb in radiocarbon_checkboxes if cb.value]
        selected_columns += [f'{vegetation}' for vegetation, cb in zip(list_vegetation_classes, vegetation_checkboxes) if cb.value]
        selected_columns += [f'NEE_average_{hour}' for hour, cb in enumerate(hourly_nee_checkboxes) if cb.value]
        selected_columns += [f'tCO2_offset_per_hour_{hour}' for hour, cb in enumerate(hourly_offset_checkboxes) if cb.value]
        selected_columns += [f'tCO2_rel_emission_per_hour_{hour}' for hour, cb in enumerate(hourly_emission_checkboxes) if cb.value]

        subset_df = merged_df[['city_name', 'Country'] + selected_columns]

        with output:
            clear_output()
            display(subset_df)
            display_selected_variables(subset_df)
        
        # Call the callback function with the subset_df
        callback(subset_df)

    # Attach the create_subset function to each checkbox
    for checkbox in (general_checkboxes + land_cover_general_checkboxes + co2_tno_checkboxes + co2_odiac_checkboxes +
                     urban_topography_checkboxes + natural_topography_checkboxes + radiocarbon_checkboxes + vegetation_checkboxes + 
                     hourly_nee_checkboxes + hourly_offset_checkboxes + hourly_emission_checkboxes):
        checkbox.observe(create_subset, 'value')

    # Function to load selections from JSON file
    def load_selections(json_data):
        selections = json.loads(json_data)
        for cb_list, info_dict in [
            (general_checkboxes, general_info), 
            (land_cover_general_checkboxes, land_cover_general_info), 
            (co2_tno_checkboxes, co2_info_tno), 
            (co2_odiac_checkboxes, co2_info_odiac), 
            (urban_topography_checkboxes, urban_topography_info), 
            (natural_topography_checkboxes, natural_topography_info),
            (radiocarbon_checkboxes, radiocarbon_info)
        ]:
            for cb in cb_list:
                cb.value = info_dict[cb.description] in selections

        for cb, veg in zip(vegetation_checkboxes, list_vegetation_classes):
            cb.value = str(veg) in selections

        for hour in range(24):
            hourly_nee_checkboxes[hour].value = f'NEE_average_{hour}' in selections
            hourly_offset_checkboxes[hour].value = f'tCO2_offset_per_hour_{hour}' in selections
            hourly_emission_checkboxes[hour].value = f'tCO2_rel_emission_per_hour_{hour}' in selections

    # Function to save selection to JSON file
    def save_selections():
        selections = []
        for cb_list, info_dict in [
            (general_checkboxes, general_info), 
            (land_cover_general_checkboxes, land_cover_general_info), 
            (co2_tno_checkboxes, co2_info_tno), 
            (co2_odiac_checkboxes, co2_info_odiac), 
            (urban_topography_checkboxes, urban_topography_info), 
            (natural_topography_checkboxes, natural_topography_info),
            (radiocarbon_checkboxes, radiocarbon_info)
        ]:
            selections += [info_dict[cb.description] for cb in cb_list if cb.value]

        selections += [str(veg) for veg, cb in zip(list_vegetation_classes, vegetation_checkboxes) if cb.value]

        for hour in range(24):
            if hourly_nee_checkboxes[hour].value:
                selections.append(f'NEE_average_{hour}')
            if hourly_offset_checkboxes[hour].value:
                selections.append(f'tCO2_offset_per_hour_{hour}')
            if hourly_emission_checkboxes[hour].value:
                selections.append(f'tCO2_rel_emission_per_hour_{hour}')

        filename = f'selection_{datetime.now().strftime("%Y_%m_%d_%H%M")}.json'
        with open(filename, 'w') as f:
            json.dump(selections, f)

    # Create file upload widget
    upload_widget = widgets.FileUpload(
        accept='.json',
        multiple=False
    )

    # Define file upload handling
    def handle_upload(change):
        json_data = upload_widget.value[0]['content'].tobytes()
        load_selections(json_data)


    upload_widget.observe(handle_upload, names='value')

    # Create save button
    save_button = widgets.Button(
        description='Save Selection',
        button_style='success'
    )
    save_button.on_click(lambda _: save_selections())

    # Create nested accordions for each section
    land_cover_accordion = widgets.Accordion(children=[
        widgets.VBox(vegetation_checkboxes)
    ])
    land_cover_accordion.set_title(0, 'Share land cover classes (%)')

    biogenic_accordion = widgets.Accordion(children=[
        widgets.VBox(hourly_nee_checkboxes),
        widgets.VBox(hourly_offset_checkboxes),
        widgets.VBox(hourly_emission_checkboxes)
    ])
    biogenic_accordion.set_title(0, 'NEE Average per Hour')
    biogenic_accordion.set_title(1, 'CO2 Offset per Hour')
    biogenic_accordion.set_title(2, 'Relative CO2 Emission per Hour')

    co2_accordion = widgets.Accordion(children=[
        widgets.VBox(co2_tno_checkboxes),
        widgets.VBox(co2_odiac_checkboxes)
    ])
    co2_accordion.set_title(0, 'TNO')
    co2_accordion.set_title(1, 'ODIAC')

    # Create the main accordion with nested structure for biogenic activity and CO2 emissions
    main_accordion = widgets.Accordion(children=[
        widgets.VBox(general_checkboxes),
        widgets.VBox([widgets.VBox(land_cover_general_checkboxes), land_cover_accordion]),
        co2_accordion,
        biogenic_accordion,
        widgets.VBox(urban_topography_checkboxes),
        widgets.VBox(natural_topography_checkboxes),
        widgets.VBox(radiocarbon_checkboxes)
    ])
    main_accordion.set_title(0, 'General')
    main_accordion.set_title(1, 'Land cover')
    main_accordion.set_title(2, 'CO2 Emissions')
    main_accordion.set_title(3, 'Biogenic Activity')
    main_accordion.set_title(4, 'Urban Topography')
    main_accordion.set_title(5, 'Natural Topography')
    main_accordion.set_title(6, 'Radiocarbon')

    # Display the main accordion, file upload widget, save button, and output
    display(upload_widget)
    display(save_button)
    display(main_accordion)
    display(output)

    # Initial display
    create_subset()

def display_selected_variables(df):
    
    dictionary_all_variables = {'NEE_average_0': 'Average NEE during January and February 2018 at 0', 'NEE_average_1': 'Average NEE during January and February 2018 at 1', 'NEE_average_2': 'Average NEE during January and February 2018 at 2', 'NEE_average_3': 'Average NEE during January and February 2018 at 3', 'NEE_average_4': 'Average NEE during January and February 2018 at 4', 'NEE_average_5': 'Average NEE during January and February 2018 at 5', 'NEE_average_6': 'Average NEE during January and February 2018 at 6', 'NEE_average_7': 'Average NEE during January and February 2018 at 7', 'NEE_average_8': 'Average NEE during January and February 2018 at 8', 'NEE_average_9': 'Average NEE during January and February 2018 at 9', 'NEE_average_10': 'Average NEE during January and February 2018 at 10', 'NEE_average_11': 'Average NEE during January and February 2018 at 11', 'NEE_average_12': 'Average NEE during January and February 2018 at 12', 'NEE_average_13': 'Average NEE during January and February 2018 at 13', 'NEE_average_14': 'Average NEE during January and February 2018 at 14', 'NEE_average_15': 'Average NEE during January and February 2018 at 15', 'NEE_average_16': 'Average NEE during January and February 2018 at 16', 'NEE_average_17': 'Average NEE during January and February 2018 at 17', 'NEE_average_18': 'Average NEE during January and February 2018 at 18', 'NEE_average_19': 'Average NEE during January and February 2018 at 19', 'NEE_average_20': 'Average NEE during January and February 2018 at 20', 'NEE_average_21': 'Average NEE during January and February 2018 at 21', 'NEE_average_22': 'Average NEE during January and February 2018 at 22', 'NEE_average_23': 'Average NEE during January and February 2018 at 23', 'tCO2_offset_per_hour_0': 'Total city-wide NEE during January and February 2018 at 0', 'tCO2_offset_per_hour_1': 'Total city-wide NEE during January and February 2018 at 1', 'tCO2_offset_per_hour_2': 'Total city-wide NEE during January and February 2018 at 2', 'tCO2_offset_per_hour_3': 'Total city-wide NEE during January and February 2018 at 3', 'tCO2_offset_per_hour_4': 'Total city-wide NEE during January and February 2018 at 4', 'tCO2_offset_per_hour_5': 'Total city-wide NEE during January and February 2018 at 5', 'tCO2_offset_per_hour_6': 'Total city-wide NEE during January and February 2018 at 6', 'tCO2_offset_per_hour_7': 'Total city-wide NEE during January and February 2018 at 7', 'tCO2_offset_per_hour_8': 'Total city-wide NEE during January and February 2018 at 8', 'tCO2_offset_per_hour_9': 'Total city-wide NEE during January and February 2018 at 9', 'tCO2_offset_per_hour_10': 'Total city-wide NEE during January and February 2018 at 10', 'tCO2_offset_per_hour_11': 'Total city-wide NEE during January and February 2018 at 11', 'tCO2_offset_per_hour_12': 'Total city-wide NEE during January and February 2018 at 12', 'tCO2_offset_per_hour_13': 'Total city-wide NEE during January and February 2018 at 13', 'tCO2_offset_per_hour_14': 'Total city-wide NEE during January and February 2018 at 14', 'tCO2_offset_per_hour_15': 'Total city-wide NEE during January and February 2018 at 15', 'tCO2_offset_per_hour_16': 'Total city-wide NEE during January and February 2018 at 16', 'tCO2_offset_per_hour_17': 'Total city-wide NEE during January and February 2018 at 17', 'tCO2_offset_per_hour_18': 'Total city-wide NEE during January and February 2018 at 18', 'tCO2_offset_per_hour_19': 'Total city-wide NEE during January and February 2018 at 19', 'tCO2_offset_per_hour_20': 'Total city-wide NEE during January and February 2018 at 20', 'tCO2_offset_per_hour_21': 'Total city-wide NEE during January and February 2018 at 21', 'tCO2_offset_per_hour_22': 'Total city-wide NEE during January and February 2018 at 22', 'tCO2_offset_per_hour_23': 'Total city-wide NEE during January and February 2018 at 23', 'tCO2_rel_emission_per_hour_0': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 0', 'tCO2_rel_emission_per_hour_1': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 1', 'tCO2_rel_emission_per_hour_2': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 2', 'tCO2_rel_emission_per_hour_3': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 3', 'tCO2_rel_emission_per_hour_4': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 4', 'tCO2_rel_emission_per_hour_5': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 5', 'tCO2_rel_emission_per_hour_6': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 6', 'tCO2_rel_emission_per_hour_7': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 7', 'tCO2_rel_emission_per_hour_8': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 8', 'tCO2_rel_emission_per_hour_9': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 9', 'tCO2_rel_emission_per_hour_10': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 10', 'tCO2_rel_emission_per_hour_11': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 11', 'tCO2_rel_emission_per_hour_12': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 12', 'tCO2_rel_emission_per_hour_13': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 13', 'tCO2_rel_emission_per_hour_14': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 14', 'tCO2_rel_emission_per_hour_15': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 15', 'tCO2_rel_emission_per_hour_16': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 16', 'tCO2_rel_emission_per_hour_17': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 17', 'tCO2_rel_emission_per_hour_18': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 18', 'tCO2_rel_emission_per_hour_19': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 19', 'tCO2_rel_emission_per_hour_20': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 20', 'tCO2_rel_emission_per_hour_21': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 21', 'tCO2_rel_emission_per_hour_22': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 22', 'tCO2_rel_emission_per_hour_23': 'Relative NEE during January and February 2018 compared to total CO2 emissions at 23', 'Total_pop': 'Total population year 2018', 'area_50percent_pop': 'Share of the city containing 50% of the population', 'area': 'Area in km2', 'dist_closest_city': 'Distance to closest city in km', 'share_over_2m_s':'Share of times the wind is >2m/s Jan/Feb 2018 hours 9 - 18','dominant_wind_share': 'Share of wind from dominant wind direction Jan/Feb 2018 hours 9 - 18 when wind is >2m/s', 'emiss_intensity_buff_dom_wind_jan_feb_9_18_2m_s': 'Emission intensity (kg CO2 / km2) within 20km buffer in the dominant wind direction (Jan/Feb 2018 hours 9 - 18). Only when wind is >2m/s.', 'share_cloud_over30percent':'Average share of cloud cover (fraction between 0 and 1) at 11:00UTC year 2018','share_cloud_over30percent_summer':'Average share of cloud cover (fraction between 0 and 1) at 11:00UTC summer (J+J) year 2018', 'share_cloud_over30percent_winter':'Average share of cloud cover (fraction between 0 and 1) at 11:00UTC winter (J+F) year 2018','vegetation': 'Share of vegetation (%)', 'veg_share_edge_area': "The percent of edge cells for vegetated areas", 'share_water_buffer': 'Share of water in the buffer zone', '40_buffer':'Share of cropland in the buffer zone', '40_buffer_dom_wind':'Share of cropland in the buffer zone in the dominant wind direction. Only when wind is >2m/s.','share_vegetation_buffer': 'Share of vegetation in the buffer zone', 10: 'Trees', 20:'Shrubland', 30:'Grassland', 40:'Cropland', 50: 'Built-up', 60: 'Bare / sparse vegetation', 70:'Snow and ice', 80: 'Permanent water bodies', 90: 'Herbaceous wetland', 100:'Moss and lichen', 'co2_ff_total': 'Total emissions 2018 (kg)', 'co2_ff_total_km2': 'Total emissions 2018 per km2', 'co2_ff_total_pop': 'Total emission 2018 per person', 'co2_ff_share_point_sources_total': 'Share of point source emissions', 'co2_ff_total_no_point': 'Total non-point source emissions 2018 (kg)', 'co2_ff_total_no_point_km2': 'Total non-point emission per km²', 'co2_ff_total_no_point_pop': 'Total non-point source emissions 2018', 'area_percentage': 'Share of city area containing 50% of the emissions', 'co2_ff_total_20km_buffer_km2': 'Emission intensity 20km buffer zone', 'co2_ff_total_20km_buffer_share_point_sources': 'Share of point sources in the buffer zone', 'co2_ff_total_20km_buffer_count_point_sources': 'Count point sources in the buffer zone', 'co2_ff_A_share': 'Public power (total share)', 'co2_ff_share_point_sources_A': 'Public power (share point sources)', 'co2_ff_count_point_sources_A': 'Public power (count point sources)', 'co2_ff_B_share': 'Industry (total share)', 'co2_ff_share_point_sources_B': 'Industry (share point sources)', 'co2_ff_count_point_sources_B': 'Industry (count point sources)', 'co2_ff_C_share': 'Other stationary combustions (total share)', 'co2_ff_F_share': 'Road transport (total share)', 'co2_ff_G_share': 'Shipping (total share)', 'share_uncertainty_total': 'Spatial uncertainty: % of the emissions', 'co2_ff_total_ODIAC': 'Total emissions 2018 ODIAC (kg)', 'mean_built_up': 'Mean building height in meters (based on a dataset with 100x100m grids)', 'share_flatness': 'Share of flat areas (classes 24 and 34)', 'Mean_20contour': 'Average size of patches in km2 where elevation is within 20m', 'Std_20contour': 'Standard deviation of patch sizes where elevation is within 20m', 'Var_20contour': 'Variability of patch sizes where elevation is within 20m', 'Mean_TRI': 'Average Terrain Ruggedness index', 'average_nuclear_contamination_permil_winter': 'Average nuclear contamination winter (J+F) afternoons (12 and 15 UTC)', 'share_daily_average_over_0_5_permil_winter':'Share of days >0.5 permil nuclear contamination winter', 'share_daily_average_over_0_3_permil_winter': 'Share of days >0.3 permil nuclear contamination winter', 'average_modelled_ffco2_signal_winter': 'Average ffCO2 STILT signal winter', 'average_modelled_ffco2_signal_days_below_0_5permil_winter': 'Average ffCO2 STILT signal on days >0.5 permil nuclear contamination winter', 'nuclear_masking_potential_winter': 'Average nuclear masking potential winter (%)', 'representation_bias_sample_selection_winter': 'Average representation bias due to sample selection (>0.5 permil) winter (%)'}

    html_content = ""

    # Iterate over each column in the DataFrame
    for column in df.columns:
        # Remove '_scaled' suffix if present to match dictionary keys
        column_name = column.removesuffix('_scaled')
        
        # Check if the (modified) column name exists in the dictionary
        if column_name in dictionary_all_variables:
            value = dictionary_all_variables[column_name]
            html_content += f"<b>{column_name}</b> : {value}<br>"

    # Display the HTML content
    display(HTML(html_content))
    
def subset_cities(subset_df_global, callback):
    
    # Extract unique countries
    unique_countries = sorted(subset_df_global['Country'].unique())

    # Create checkboxes for each country
    country_checkboxes = {}
    for country in unique_countries:
        country_checkboxes[country] = widgets.Checkbox(
            value=True,
            description=country,
            indent=False
        )

    # Function to update the selected countries
    def update_countries(change):
        filter_and_display()

    # Attach the update function to each checkbox
    for checkbox in country_checkboxes.values():
        checkbox.observe(update_countries, names='value')

    # Organize checkboxes in two columns
    def create_two_column_layout(checkboxes):
        items = list(checkboxes.values())
        n = len(items)
        left_column = widgets.VBox(items[:n//2])
        right_column = widgets.VBox(items[n//2:])
        return widgets.HBox([left_column, right_column])

    country_checkboxes_layout = create_two_column_layout(country_checkboxes)

    # Create a dropdown for selecting the column for percentile filtering
    columns_to_filter = [col for col in subset_df_global.columns if col not in ['Country', 'city_name']]
    column_dropdown = widgets.Dropdown(
        options=columns_to_filter,
        description='Select Column:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='50%')
    )

    # Create input boxes for setting the percentile range
    percentile_min_box = widgets.FloatText(
        value=0,
        min=0,
        max=100,
        step=0.1,
        description='Percentile Min:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='50%')
    )

    percentile_max_box = widgets.FloatText(
        value=100,
        min=0,
        max=100,
        step=0.1,
        description='Percentile Max:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='50%')
    )

    # Output area for displaying the resulting DataFrame
    output = widgets.Output()

    # Function to filter the DataFrame and display the result
    def filter_and_display():
        selected_countries = [country for country, checkbox in country_checkboxes.items() if checkbox.value]
        selected_column = column_dropdown.value
        percentile_min = percentile_min_box.value
        percentile_max = percentile_max_box.value

        # Filter based on selected countries
        filtered_df = subset_df_global[subset_df_global['Country'].isin(selected_countries)]

        # Further filter based on the selected column and percentile range
        if selected_column and not filtered_df.empty:
            min_threshold = filtered_df[selected_column].quantile(percentile_min / 100.0)
            max_threshold = filtered_df[selected_column].quantile(percentile_max / 100.0)
            filtered_df = filtered_df[
                (filtered_df[selected_column] >= min_threshold) & 
                (filtered_df[selected_column] <= max_threshold)
            ]

        with output:
            clear_output()
            display(filtered_df)
            print(f"Number of cities selected: {len(filtered_df)}")
        
        # Use the callback to update the global variable
        callback(filtered_df)

    # Attach the filter function to the dropdown and input boxes
    column_dropdown.observe(lambda change: filter_and_display(), names='value')
    percentile_min_box.observe(lambda change: filter_and_display(), names='value')
    percentile_max_box.observe(lambda change: filter_and_display(), names='value')

    # Display the widgets
    display(widgets.VBox([
        country_checkboxes_layout,
        column_dropdown,
        percentile_min_box,
        percentile_max_box,
        output
    ]))

    # Initial display
    filter_and_display()


    
# Function to scale the DataFrame
def scale_df(subset_df_filtered, callback):
    # List of columns to scale (excluding "city_name" and "Country")
    cols_for_scaling = [col for col in subset_df_filtered.columns if col not in ["city_name", "Country"]]

    # Create a copy of the dataframe to add scaled columns to
    subset_df_scaled = subset_df_filtered.copy()

    for column in cols_for_scaling:
        q1 = subset_df_filtered[column].quantile(0.1)
        q3 = subset_df_filtered[column].quantile(0.9)
        
        # Compute the scaled values
        scaled_column = (subset_df_filtered[column] - q1) / (q3 - q1)
        
        # Apply clipping to scale between 0 and 1
        scaled_column = np.clip(scaled_column, 0, 1)
        
        # Assign the scaled data back to the DataFrame with a new column name
        subset_df_scaled[column + '_scaled'] = scaled_column
        

    # Filter out only the scaled columns and keep 'city_name'
    scaled_cols = ['city_name'] + [col for col in subset_df_scaled.columns if "_scaled" in col]
    subset_df_scaled = subset_df_scaled[scaled_cols].copy()

    display(subset_df_scaled)
    
    # Use the callback to update the global variable
    callback(subset_df_scaled)

def invert_values(subset_df_scaled, callback):
    # Columns that should be checked by default
    default_checked_columns = {'dominant_wind_share_scaled', 'share_flatness_scaled', 'share_over_2m_s_scaled'}
    
    # Create checkboxes for each column in the DataFrame
    checkboxes = {}
    for column in subset_df_scaled.columns:
        if column != "city_name":  # Exclude "city_name" from inverting
            checked = column in default_checked_columns
            checkboxes[column] = widgets.Checkbox(value=checked, description=column, style={'description_width': 'initial'})
    
    # Output area for displaying the resulting DataFrame
    output = widgets.Output()
    
    # Function to update the displayed DataFrame
    def update_df(change=None):  # Allow `change` to be optional for initial call
        # Create a copy of the DataFrame to modify for display
        df_copy = subset_df_scaled.copy()
        
        # Check each column's checkbox status and invert values if checked
        for column, checkbox in checkboxes.items():
            if checkbox.value:
                df_copy[column] = 1 - df_copy[column]
        
        with output:
            clear_output()
            display(df_copy)
            display_selected_variables(df_copy)
            
        
        # Use the callback to update the global variable with the modified DataFrame
        callback(df_copy)
    
    # Link each checkbox to the update function
    for checkbox in checkboxes.values():
        checkbox.observe(update_df, 'value')
    
    # Display all checkboxes and the output area for the DataFrame
    display_widgets = widgets.VBox(list(checkboxes.values()))
    display(display_widgets, output)

    # Initial call to display the DataFrame with default inverted columns
    update_df()  # Call update_df initially to show the DataFrame right away


def weigh_variables_df(subset_df_scaled, callback):
    # Extract the column names, except the first one
    columns = subset_df_scaled.columns[1:]

    # Number of columns
    num_columns = len(columns)

    # Calculate the initial equal weight for each column
    initial_weight = 100 / num_columns

    # Create a dictionary to store the weight widgets and their initial values
    weight_widgets = {}
    weight_values = {}
    for column in columns:
        weight_widgets[column] = widgets.FloatText(
            value=initial_weight,
            min=0.0,
            max=100.0,
            step=0.01,
            description=column,
            style={'description_width': '300px'},  # Adjust width of the description
            layout=widgets.Layout(width='80%')  # Adjust width of the text box
        )
        weight_values[column] = initial_weight

    # Function to update weight values
    def update_weight_values(column):
        def _update(change):
            weight_values[column] = change.new
            total_weight = sum(weight_values.values())
            total_label.value = f'Total weight: {total_weight:.2f}%'
        return _update

    # Attach the update function to the widgets
    for column, widget in weight_widgets.items():
        widget.observe(update_weight_values(column), names='value')

    # Create a label to show the total weight
    total_label = widgets.Label(value=f'Total weight: {sum(weight_values.values()):.2f}%')

    # Create a button to apply the weights
    apply_button = widgets.Button(description='Run', button_style='primary')

    # Output area for displaying the final weighted DataFrame
    output = widgets.Output()

    # Function to apply weights and create the weighted DataFrame
    def apply_weights(b):
        total_weight = sum(weight_values.values())
        if not (99.9 <= total_weight <= 100.1):
            with output:
                clear_output()
                print("Total weight must be approximately 100%. Please adjust the weights.")
        else:
            subset_df_scaled_weighted = subset_df_scaled.copy()
            for column in columns:
                weight = weight_values[column] / 100
                subset_df_scaled_weighted[column] *= weight
            with output:
                clear_output()
                display(subset_df_scaled_weighted)
            # Call the callback function to update the global variable
            callback(subset_df_scaled_weighted)

    # Attach the function to the button
    apply_button.on_click(apply_weights)

    # Create a button to save weights to a JSON file
    save_button = widgets.Button(description="Save Weights", button_style='success')

    # Function to save weights to a JSON file
    def save_weights(b):
        weights = {column: weight for column, weight in weight_values.items()}
        filename = f'weights_{datetime.now().strftime("%Y_%m_%d_%H%M")}.json'
        with open(filename, 'w') as f:
            json.dump(weights, f)
        with output:
            clear_output()
            print(f"Weights saved to {filename}")

    # Attach the function to the save button
    save_button.on_click(save_weights)

    # Create a file upload widget for loading weights from a JSON file
    upload_widget = widgets.FileUpload(accept='.json', multiple=False)

    # Function to load weights from a JSON file
    def load_weights(change):
        file_info = upload_widget.value[0]
        weights_data = file_info['content'].tobytes().decode('utf-8')
        weights = json.loads(weights_data)
        for column, weight in weights.items():
            if column in weight_widgets:
                weight_widgets[column].value = weight

    # Attach the function to the upload widget
    upload_widget.observe(load_weights, names='value')

    # Display the widgets
    display(*weight_widgets.values(), total_label, upload_widget,  save_button, apply_button, output)

    # Initial total weight display
    total_label.value = f'Total weight: {sum(weight_values.values()):.2f}%'

# Function to create and display the challenge score DataFrame
def calculate_challenge_score(subset_df_scaled_inverted_weighted):
    # Widget to input the challenge name with a default value
    name_input = widgets.Text(
        value='your_challenge_name_here',
        description='Name of challenge:',
        placeholder='Enter challenge name',
        style={'description_width': 'initial'},
    )
    
    # Checkbox for saving as CSV
    save_csv_checkbox = widgets.Checkbox(
        value=False,
        description='Save as CSV',
        style={'description_width': 'initial'},
    )
    
    # Button to run the calculation
    run_button = widgets.Button(
        description='Run',
        button_style='primary'
    )
    
    # Output widget to display the DataFrame
    output = widgets.Output()
    
    # Function to execute when button is clicked
    def on_button_click(b):
        with output:
            output.clear_output()  # Clear previous outputs
            name_challenge_score = name_input.value
            
            # Copy the DataFrame and calculate the challenge score
            challenge_score = subset_df_scaled_inverted_weighted.copy()
            challenge_score[name_challenge_score] = challenge_score.select_dtypes(include='number').sum(axis=1) * 100
            
            # Keep only the city names and the final challenge score
            challenge_score = challenge_score[['city_name', name_challenge_score]]
            
            # Add ranking and quartile columns
            challenge_score['challenge_rank'] = challenge_score[name_challenge_score].rank(method='min', ascending=True)
            challenge_score['challenge_quartile'] = pd.qcut(challenge_score[name_challenge_score], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
            
            # Display the resulting DataFrame
            display(challenge_score)
            
            # Save as CSV if checkbox is checked
            if save_csv_checkbox.value:
                challenge_score.to_csv('challenge_score.csv', encoding='utf-8-sig', index=False)
                print("DataFrame saved as 'challenge_score.csv'")

    # Link the button click event to the function
    run_button.on_click(on_button_click)
    
    # Display widgets and output area
    display(name_input, save_csv_checkbox, run_button, output)


def create_similarity_matrix(subset_df_scaled_inverted_weighted, callback):
    # Define distance methods
    distance_methods = {
        "Euclidean distance": "euclidean",
        "Squared Euclidean distance": "sqeuclidean",
        "Minkowski distance": "minkowski",
        "City block (Manhattan) distance": "cityblock",
        "Cosine distance": "cosine"
    }

    # Sort city names and exclude initial selection
    initial_cities = ['Paris', 'Munich', 'Zurich']
    city_names = sorted([city for city in subset_df_scaled_inverted_weighted['city_name'] if city not in initial_cities])

    # Distance calculation dropdown
    distance_dropdown = widgets.Dropdown(
        options=distance_methods.items(),
        value="euclidean",
        description="Distance calculation method",
        style={'description_width': 'initial'},
    )

    # City dropdown for adding to selected list
    city_dropdown = widgets.Dropdown(
        options=city_names,
        description="Select city",
        style={'description_width': 'initial'}
    )
    
    # Button to add city to selected list
    add_city_button = widgets.Button(description="Add City", button_style="success")  # Green button

    # Display for selected cities
    selected_cities = initial_cities.copy()
    selected_cities_display = widgets.Select(
        options=selected_cities,
        description="Selected cities",
        style={'description_width': 'initial'},
        rows=5
    )
    
    # Button to remove city from selected list
    remove_city_button = widgets.Button(description="Remove City", button_style="danger")  # Red button

    # Add city to selected list
    def add_city(b):
        city = city_dropdown.value
        if city and city not in selected_cities:
            selected_cities.append(city)
            selected_cities.sort()
            selected_cities_display.options = selected_cities
            # Remove from main dropdown options
            city_dropdown.options = [c for c in city_names if c not in selected_cities]

    # Remove city from selected list
    def remove_city(b):
        city = selected_cities_display.value
        if city in selected_cities:
            selected_cities.remove(city)
            selected_cities_display.options = selected_cities
            # Add back to main dropdown options
            city_dropdown.options = sorted([c for c in city_names if c not in selected_cities])

    # Attach functions to buttons
    add_city_button.on_click(add_city)
    remove_city_button.on_click(remove_city)

    # Button to create similarity matrix
    create_button = widgets.Button(description='Run', button_style='primary')
    output = widgets.Output()

    # Function to create similarity matrix and capture it
    def calculate_similarity_matrix(b):
        clear_output(wait=True)

        # Calculate similarity matrix
        subset_df_scaled_indexed = subset_df_scaled_inverted_weighted.set_index('city_name')
        distance_calc = distance_dropdown.value
        scaled_cols = [col for col in subset_df_scaled_indexed.columns if "_scaled" in col]
        dists = pdist(subset_df_scaled_indexed[scaled_cols].to_numpy(), distance_calc)
        similarity_matrix = pd.DataFrame(
            squareform(dists),
            columns=subset_df_scaled_indexed.index,
            index=subset_df_scaled_indexed.index
        )
        
        # Call the callback function to update the global variable
        # need to be valeus between 0 and 1
        callback(similarity_matrix)
        # Convert to percentage similarity
        if distance_calc == 'euclidean':
            similarity_matrix = (1 - similarity_matrix) * 100
            similarity_matrix = similarity_matrix.round(2)


        # Display similarity matrix
        with output:
            clear_output()
            
            # Display subset for selected cities (all rows, selected columns)
            subset_matrix = similarity_matrix[selected_cities]
            print("\nSubset of Similarity Matrix for Selected Cities:")
            display(subset_matrix)
            print("\nFull Similarity Matrix:")
            display(similarity_matrix)

    # Attach the function to the button
    create_button.on_click(calculate_similarity_matrix)

    # Display widgets
    display(distance_dropdown, city_dropdown, add_city_button, selected_cities_display, remove_city_button, create_button, output)

def create_dendrogram(similarity_matrix, callback):
    # Dropdown for linkage method
    linkage_methods = ['ward', 'single', 'average', 'weighted', 'centroid', 'median']
    linkage_dropdown = widgets.Dropdown(
        options=linkage_methods,
        value='ward',
        description='Linkage method:',
        style={'description_width': 'initial'}
    )

    # Numeric text input for target number of clusters
    target_clusters_input = widgets.BoundedIntText(
        value=5,
        min=2,
        max=10,
        step=1,
        description='Target clusters:',
        style={'description_width': 'initial'}
    )

    # Checkbox to save the dendrogram as PNG
    save_dendrogram_checkbox = widgets.Checkbox(
        value=False,
        description='Save dendrogram as PNG'
    )

    # Output for the dendrogram plot
    output = widgets.Output()

    def run_dendrogram(*args):
        # Get user-selected options
        dendrogram_link = linkage_dropdown.value
        target_clusters = target_clusters_input.value
        save_dendrogram = save_dendrogram_checkbox.value

        list_num_clusters = []
        list_threshold_clusters = []

        # Calculate the linkage matrix
        dists = squareform(similarity_matrix.to_numpy())
        linkage_matrix = linkage(dists, dendrogram_link)

        # Determine range for threshold dynamically based on the linkage matrix
        range_from = linkage_matrix[:, 2].min()
        range_until = linkage_matrix[:, 2].max()
        
        # Testing for the best threshold to approximate the target number of clusters
        for threshold in np.arange(range_from, range_until, 0.01):
            # Generate a dendrogram to calculate the number of clusters at this threshold
            dendrogram_for_info = dendrogram(
                linkage_matrix,
                labels=list(similarity_matrix.columns),
                leaf_rotation=90,
                leaf_font_size=6,
                no_plot=True,  # Do not display during testing
                color_threshold=threshold
            )
            
            # do not want many non-assigned clusters.
            if dendrogram_for_info['leaves_color_list'].count('C0')/len(dendrogram_for_info['leaves_color_list']) < 0.7:

                # Count number of clusters
                num_clusters = len(set(dendrogram_for_info['leaves_color_list']))
                list_num_clusters.append(num_clusters)
                list_threshold_clusters.append(threshold)

        # Find the threshold that gives the closest number of clusters to the target
        closest_index = np.argmin(np.abs(np.array(list_num_clusters) - target_clusters))

        threshold_num_desired_clusters = list_threshold_clusters[closest_index]

        # Display the final dendrogram with the selected threshold
        with output:
            clear_output(wait=True)  # Clear any previous output
            fig, ax = plt.subplots(figsize=(25, 10))
            final_dendrogram = dendrogram(
                linkage_matrix,
                labels=list(similarity_matrix.columns),
                leaf_rotation=90,
                leaf_font_size=12,
                ax=ax,
                color_threshold=threshold_num_desired_clusters
            )
            ax.axhline(y=threshold_num_desired_clusters, color='black', linewidth=1)
            plt.show()

            # Save the dendrogram if the checkbox is selected
            if save_dendrogram:
                fig.savefig("dendrogram.png", bbox_inches='tight')
                print("Dendrogram saved as dendrogram.png")

            # Create clusters DataFrame
            clusters_df = pd.DataFrame({
                'city': final_dendrogram['ivl'],
                'cluster_dendrogram': final_dendrogram['leaves_color_list']
            })

            # Pass the clusters_df to the callback function
            callback(clusters_df)

        plt.close(fig)  # Close the figure to prevent extra output

    # Button to create the dendrogram
    create_button = widgets.Button(description='Generate Dendrogram')
    create_button.on_click(run_dendrogram)

    # Display the widgets
    display(linkage_dropdown, target_clusters_input, save_dendrogram_checkbox, create_button, output)

def cluster_map(clusters_dendrogram):
    # Load cities GeoDataFrame
    cities = gpd.read_file('cities.geojson')

    # Merge cities with the clusters_dendrogram DataFrame
    cities_join = pd.merge(cities, clusters_dendrogram, how='left', left_on='city_name', right_on='city')

    # Filter out rows where cluster_dendrogram is NaN
    cities_join = cities_join[cities_join['cluster_dendrogram'].notna()]

    # Create an interactive map with the joined DataFrame
    m = cities_join.explore(
        tiles=None,
        column='cluster_dendrogram',
        legend=True,  # show legend
        tooltip=False,  # hide tooltip
        popup=['cluster_dendrogram', 'city_name'],
        cmap='YlOrRd',  # Color map
        name="cities_join"
    )

    # Add custom faded tiles
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        name='Faded OpenStreetMap',
        opacity=0.3  # Adjust opacity for fading effect
    ).add_to(m)

    # Add ESRI satellite tiles
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        show=False,
        name='ESRI satellite'
    ).add_to(m)

    # Add layer control to the map
    folium.LayerControl().add_to(m)

    # Display the map directly in Jupyter Notebook
    return m  # Return the map object
