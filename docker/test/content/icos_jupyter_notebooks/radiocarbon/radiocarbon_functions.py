# Standard libraries
import os
import math
import json
import warnings
from datetime import date as current_date, timedelta
import datetime as dt

# Data manipulation
import numpy as np
import pandas as pd
import xarray as xr

# Plotting and visualization
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.pyplot import figure
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import seaborn

# Bokeh for interactive plots
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.io import show, output_notebook, reset_output, export_png

# Geospatial tools
import cartopy
import cartopy.feature as cfeature
import cartopy.crs as ccrs
from pyproj import Geod

# Map visualization
import folium
import branca

# ICOS Carbon Portal API
from icoscp.sparql import sparqls
from icoscp.dobj import Dobj
from icoscp.sparql.runsparql import RunSparql
from icoscp.station import station as station_data

# STILT footprint
from icoscp_stilt import stilt
from icoscp_stilt import stiltstation

# NetCDF for working with scientific data
import netCDF4 as cdf
from netCDF4 import Dataset

# IPython widgets
from ipywidgets import IntProgress
from IPython.core.display import display, HTML
display(HTML("<style>.container { width:90% !important; }</style>"))

# Suppress warnings
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

folder_w_data = 'radiocarbon'

# nuclear emissions
nuclear_emissions ='facilities_GBq_year_2006_2022_upd_2024_09_04.csv'

# find the latest year of nuclear emission data:
df = pd.read_csv(os.path.join(folder_w_data, nuclear_emissions))
max_year = max([int(col) for col in df.columns if col.isdigit()])

#parameters used to estimate nuclear contamination.
#updated from 0.238 to 0.226 September 2024 according to Fabian Maier's work.
Aabs = 0.226
#molar mass C in gram
Mc = 12

reset_output()
output_notebook()

# function to get nuclear emission data from the csv-file to our STILT model grid
# this could be modified to fit with other model grids.
def access_nuclear_emission_data():
    
    # Load the data
    df = pd.read_csv(os.path.join(folder_w_data, nuclear_emissions))

    # Define bounding box coordinates and grid resolution
    lat_min, lat_max = 33.0, 73.0  # Latitude bounds
    lon_min, lon_max = -15.0, 35.0  # Longitude bounds
    nrows, ncols = 480, 400  # Grid resolution (number of rows and columns)

    # Create the grid
    lat_bins = np.linspace(lat_min, lat_max, nrows + 1)
    lon_bins = np.linspace(lon_min, lon_max, ncols + 1)
    lat_center = (lat_bins[:-1] + lat_bins[1:]) / 2
    lon_center = (lon_bins[:-1] + lon_bins[1:]) / 2

    # Extract and convert the years to integers
    years = [int(col) for col in df.columns if col.isdigit()]

    # Initialize the geod object based on the WGS84 ellipsoid
    geod = Geod(ellps="WGS84")

    # Calculate the area of each grid cell using geodetic methods
    def calculate_geodetic_area(lat1, lon1, lat2, lon2):
        # This function returns the area in square meters
        area, _ = geod.polygon_area_perimeter([lon1, lon2, lon2, lon1, lon1], [lat1, lat1, lat2, lat2, lat1])
        return area  # area in m^2

    # Initialize an array for grid cell areas
    area_data = np.zeros((len(lat_center), len(lon_center)))

    # Loop through each grid cell and calculate the area
    for i in range(len(lat_center)):
        for j in range(len(lon_center)):
            lat1, lat2 = lat_bins[i], lat_bins[i+1]
            lon1, lon2 = lon_bins[j], lon_bins[j+1]
            area_data[i, j] = calculate_geodetic_area(lat1, lon1, lat2, lon2)

    # Initialize an empty xarray DataArray with zeros for the entire grid and years
    grid = xr.DataArray(
        np.zeros((len(lat_center), len(lon_center), len(years))),
        coords=[lat_center, lon_center, years],
        dims=['lat', 'lon', 'year'],
        name='emissions'
    )

    # Create a list to store facility information
    facility_info = []

    # Assign emissions to the grid cells and save facility info
    for _, row in df.iterrows():
        # Find the grid cell indices for the current facility
        lat_idx = np.searchsorted(lat_bins, row['lat']) - 1
        lon_idx = np.searchsorted(lon_bins, row['lon']) - 1

        # Check if the indices are within the grid bounds
        if 0 <= lat_idx < nrows and 0 <= lon_idx < ncols:
            # Add the emission data to the appropriate grid cell for each year
            for year in years:
                emission_value = float(row[str(year)])  # Convert the emission value to float
                grid[lat_idx, lon_idx, grid.coords['year'] == year] += emission_value

            # Store the facility name and its corresponding grid cell indices
            facility_info.append([row['facility'], lat_idx, lon_idx])

    # Convert facility information to a DataArray
    facility_da = xr.DataArray(
        data=facility_info,
        dims=['facility', 'info'],  # 'facility' is just the index name here
        name='facility_info'
    )

    # Add the area slice to the xarray
    grid_area = xr.DataArray(
        area_data,
        coords=[lat_center, lon_center],
        dims=['lat', 'lon'],
        name='area'
    )

    # Combine the grid, area, and facility DataArrays into a Dataset
    combined_grid = xr.Dataset({'emissions': grid, 'area': grid_area, 'facility_info': facility_da})
    
    return combined_grid
    
#resample the delta 14C data in the radiocarbonObject to be what the user has specified (monthly or specific number of days)
#this will not happen when resample is set to 0.
#returns dataframes (to radiocarbon_object) with the resampled data that is added to the object that is being created. 

def resampled_modelled_radiocarbon(df, resample):

    # Store original column names
    original_columns = {col: col for col in df.columns if col != 'date'}

    # Set the resample format string
    format_string = 'M' if resample == -1 else f'{resample}D'
    
    # Determine the column to check for NaN count
    check_nan_column = 'delta_14c_nuclear' if 'delta_14c_nuclear' in df.columns else df.columns[1]

    # Define the base aggregation dictionary
    agg_dict = {
        **{col: 'mean' for col in df.columns if col != 'date'},
        'date': ['first', 'last', 'size']
    }

    # Add NaN count aggregation for the chosen column
    if check_nan_column in df.columns:
        agg_dict[check_nan_column] = ['mean', lambda x: np.isnan(x).sum()]

    # Resample and aggregate the data
    #resampled_df = df.resample(format_string, on='date').agg(agg_dict)
    resampled_df = df.resample(format_string, on='date', label='left').agg(agg_dict)

    # Flatten the MultiIndex in the columns
    resampled_df.columns = [
        col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in resampled_df.columns
    ]

    # Rename the date columns and the NaN count column for clarity
    rename_dict = {
        'date_first': 'date_start',
        'date_last': 'date_end',
        'date_size': 'count_footprints',
        f'{check_nan_column}_<lambda_0>': 'count_nan_footprints'  # Correct reference for count_nan column
    }

    resampled_df.rename(columns=rename_dict, inplace=True)
    
    # Rename columns back to their original names (e.g., removing '_mean')
    resampled_df.rename(columns={f"{col}_mean": col for col in original_columns.values()}, inplace=True)
    
    # Format date columns to 'yyyy-mm-dd'
    resampled_df['date_start'] = resampled_df['date_start'].dt.strftime('%Y-%m-%d')
    resampled_df['date_end'] = resampled_df['date_end'].dt.strftime('%Y-%m-%d')

    # Adjust the main index date to also be in 'yyyy-mm-dd' format
    resampled_df.index = resampled_df.index.strftime('%Y-%m-%d')
    
    # Duplicate rows and shift dates for display purposes
    resampled_df = resampled_df.reset_index()

    df_display = pd.concat([resampled_df, resampled_df])
    df_display = df_display.sort_values('date')
    df_display['date'] = list(df_display.date.values[1:]) + [df_display['date_end'].max()]

    return resampled_df, df_display


def plot_radiocarbon_bokhe(radiocarbonObject):
    station_name = radiocarbonObject.settings['stilt']['name']
    station = radiocarbonObject.stationId
    
    string_start_end_date = ', ' + str(radiocarbonObject.settings['startYear']) + '-' + str(radiocarbonObject.settings['startMonth']) + '-' + str(radiocarbonObject.settings['startDay']) + ' to ' + str(radiocarbonObject.settings['endYear']) + '-' + str(radiocarbonObject.settings['endMonth']) + '-' + str(radiocarbonObject.settings['endDay'])
        
    if station_name != '':
        for_title = '∆14C at ' + station_name + ' (' + station + ')' + string_start_end_date
    else:
        for_title = '∆14C at ' + station + string_start_end_date

    
    if radiocarbonObject.dfDelta14CStationResampleDisplay is not None:
        df = radiocarbonObject.dfDelta14CStationResampleDisplay
        df['date'] = pd.to_datetime(df['date'])
        df['date_start'] = pd.to_datetime(df['date_start'])
        df['date_end'] = pd.to_datetime(df['date_end'])
        # Define tooltips for resampled data
        tooltips = [
            ('Start date', '@date_start{%Y-%m-%d}'),
            ('End date', '@date_end{%Y-%m-%d}'),
            ('Background Δ14C', '@Background{0.2f}'),
            ('Fossil fuel Δ14C', '@Fossil{0.2f}'),
            ('Nuclear Δ14C', '@Nuclear{0.2f}'),
            ('Modelled Δ14C', '@Modelled{0.2f}'),
            ('# footprints', '@count_footprints{0f}'),
            ('# NaN footprint', '@count_nan_footprints{0f}')
        ]
        formatters = {
            '@date': 'datetime',
            '@date_start': 'datetime',
            '@date_end': 'datetime'
            
        }
    else:
        df = radiocarbonObject.dfDelta14CStation
        # Define tooltips for non-resampled data
        tooltips = [
            ('UTC', '@date{%Y-%m-%d %H:%M}'),
            ('Background Δ14C', '@Background{0.2f}'),
            ('Fossil fuel Δ14C', '@Fossil{0.2f}'),
            ('Nuclear Δ14C', '@Nuclear{0.2f}'),
            ('Modelled Δ14C', '@Modelled{0.2f}')
        ]
        formatters = {
            '@date': 'datetime'
        }

    # Prepare the data for Bokeh
    source = ColumnDataSource(data={
        'date': df.date,
        'Background': df['delta_14C_background'],
        'Fossil': df['delta_14c_fossil'],
        'Nuclear': df['delta_14c_nuclear'],
        'Modelled': df['delta_14c_nuclear_corrected'],
        'date_start': df.get('date_start', [None]*len(df)),#only in case of existing (resampled data)
        'date_end': df.get('date_end', [None]*len(df)),#only in case of existing (resampled data)
        'count_footprints': df.get('count_footprints', [None]*len(df)),#only in case of existing (resampled data)
        'count_nan_footprints': df.get('count_nan_footprints', [None]*len(df))#only in case of existing (resampled data)
    })

    # Create the figure with adjusted size and labels
    p = figure(x_axis_type='datetime', plot_width=1000, plot_height=500, title=for_title,
               x_axis_label='Time (UTC)', y_axis_label='Δ14C [‰]',
               tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')

    # Add line plots with specific styles
    p.line('date', 'Background', source=source, legend_label='Background Δ14C', color='#984ea3', line_width=1, name='delta_14C_background')
    p.line('date', 'Fossil', source=source, legend_label='Fossil fuel Δ14C', color='black', line_width=1, name='Fossil')
    p.line('date', 'Nuclear', source=source, legend_label='Nuclear Δ14C', color='#e41a1c', line_width=1, name='Nuclear')
    p.line('date', 'Modelled', source=source, legend_label='Modelled Δ14C', color='#0072B2', line_width=3, name='Modelled')

    # Customize the hover tool
    hover = HoverTool(
        tooltips=tooltips,
        formatters=formatters,
        renderers=[p.select({'name': 'Nuclear'})[0]],  # Only display tooltip for the Nuclear line
        mode='vline'
    )

    p.add_tools(hover)

    # Customize the title
    p.title.align = 'center'
    p.title.text_font_size = '13pt'
    p.title.offset = 15

    # Customize axis labels
    p.xaxis.axis_label_text_font_style = 'normal'
    p.yaxis.axis_label_text_font_style = 'normal'
    p.xaxis.axis_label_standoff = 15
    p.yaxis.axis_label_standoff = 15
    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"

    # Customize the grid
    p.grid.grid_line_alpha = 0
    p.ygrid.band_fill_color = "olive"
    p.ygrid.band_fill_alpha = 0.1

    # Deactivate the hover tool by default
    p.toolbar.active_inspect = None

    # Customize the legend
    p.legend.location = 'top_left'
    p.legend.click_policy = "hide"

    # Output to notebook or file
    output_notebook()  # Use this if running in a Jupyter notebook
    # output_file("delta_14c_components.html")  # Use this to save to a file

    # Show the plot
    show(p)

def plot_nuclear_contamination_by_facility_bokhe(radiocarbonObject):
    station_name = radiocarbonObject.settings['stilt']['name']
    station = radiocarbonObject.stationId 
    threshold = radiocarbonObject.threshold
    
    # Calculate the mean of all columns except 'date'
    facility_means = radiocarbonObject.dfDelta14CFacility.loc[:, radiocarbonObject.dfDelta14CFacility.columns != 'date'].mean()

    # Filter facilities where the mean is greater than threshold
    facilities_to_plot = facility_means[facility_means > threshold].index.tolist()
    
    # add to the radiocarbon object
    radiocarbonObject.dfFacilitiesOverThreshold = len(facilities_to_plot)
    radiocarbonObject.dfFacilitiesOverThresholdList = facilities_to_plot
    
    if len(facilities_to_plot) == 0:
        f"No nuclear facilities contributing > {radiocarbonObject.settings['threshold']} permil"
        return radiocarbonObject

    string_start_end_date =  ', ' + str(radiocarbonObject.settings['startYear']) + '-' + str(radiocarbonObject.settings['startMonth']) + '-' + str(radiocarbonObject.settings['startDay']) + ' to ' + str(radiocarbonObject.settings['endYear']) + '-'+str(radiocarbonObject.settings['endMonth']) + '-'+str(radiocarbonObject.settings['endDay'])
    
    if station_name != '':
        for_title = '∆14C at ' + station_name + ' (' + station + ') by nuclear facility (>' + str(threshold) + ' permil)' + string_start_end_date
    else:
        for_title = '∆14C at ' + station + ' by nuclear facility (>' + str(threshold) + ' permil) ' + string_start_end_date

    # in case of aggregated data
    if radiocarbonObject.dfDelta14CFacilityResampleDisplay is not None:
        filtered_df = radiocarbonObject.dfDelta14CFacilityResampleDisplay[['date', 'date_start', 'date_end', 'count_footprints', 'count_nan_footprints'] + facilities_to_plot]
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        filtered_df['date_start'] = pd.to_datetime(filtered_df['date_start'])
        filtered_df['date_end'] = pd.to_datetime(filtered_df['date_end'])

        tooltips = [
            ('Start date', '@date_start{%Y-%m-%d}'),
            ('End date', '@date_end{%Y-%m-%d}'),
            ('# footprints', '@count_footprints{0f}'),
            ('# NaN footprint', '@count_nan_footprints{0f}')
        ]

        formatters = {
            '@date': 'datetime',
            '@date_start': 'datetime',
            '@date_end': 'datetime'     
        }
        
        id_vars = ['date', 'date_start', 'date_end', 'count_footprints', 'count_nan_footprints']
            
    else:
        filtered_df = radiocarbonObject.dfDelta14CFacility[['date'] + facilities_to_plot]
        
        tooltips = [('UTC','@date{%Y-%m-%d %H:%M}')]
        
        formatters = {
            '@date': 'datetime'
        }
        
        id_vars = ['date']

    # Melt the DataFrame to long format
    melted_df = pd.melt(filtered_df, id_vars=id_vars, var_name='Facility', value_name='Value')
    
    # for display in the graph
    facility_means = facility_means.round(2)

    # Calculate the average of the total modeled concentration
    total_avg_value = radiocarbonObject.dfDelta14CStation['delta_14c_nuclear'].mean()
    total_avg_value_rounded = round(total_avg_value, 2)  # Proper rounding

    # Define a color palette from matplotlib and convert to hex format
    num_facilities = len(facilities_to_plot) 
    cmap = cm.get_cmap('tab20', num_facilities)
    colors = [mcolors.to_hex(cmap(i)) for i in range(num_facilities)]

    # Create the figure with adjusted size and labels
    p = figure(x_axis_type='datetime', plot_width=1000, plot_height=500, title=for_title,
               x_axis_label='Time (UTC)', y_axis_label='Δ14C [‰]',
               tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')

    i = 0
    # Plot lines for each facility that meets the threshold
    for facility in facilities_to_plot:  # Skip 'date' column

        # Filter the data for the current facility
        facility_data = melted_df[melted_df['Facility'] == facility]
        
        # Prepare the data source for Bokeh
        facility_source = ColumnDataSource(facility_data)

        # Add the line to the plot
        renderer = p.line('date', 'Value', source=facility_source, legend_label=f"{facility} ({facility_means[facility]} permil)",
                          color=colors[i], line_width=2,
                          name=facility)

        # Add a HoverTool for this facility
        hover = HoverTool(
            tooltips= tooltips + [
                ('Facility', facility),
                ('Value', '@Value{0.2f}')
            ],
            formatters=formatters,
            renderers=[renderer],  # Attach hover to this specific line
            mode='vline'
        )

        p.add_tools(hover)
        
        i = i + 1

    # Add the total modeled concentration line
    if radiocarbonObject.dfDelta14CFacilityResampleDisplay is not None:
        total_source = ColumnDataSource(radiocarbonObject.dfDelta14CStationResampleDisplay[['date', 'delta_14c_nuclear']])
    else:
        total_source = ColumnDataSource(radiocarbonObject.dfDelta14CStation[['date', 'delta_14c_nuclear']])
        
    p.line('date', 'delta_14c_nuclear', source=total_source, legend_label=f"Nuclear Δ14C total ({total_avg_value_rounded} permil)",
           color='red', line_width=2, line_dash='solid', name='Nuclear Total')

    # Final customizations for the plot
    p.title.align = 'center'
    p.title.text_font_size = '13pt'
    p.title.offset = 15

    # Customize axis labels
    p.xaxis.axis_label_text_font_style = 'normal'
    p.yaxis.axis_label_text_font_style = 'normal'
    p.xaxis.axis_label_standoff = 15
    p.yaxis.axis_label_standoff = 15
    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"

    # Customize the grid
    p.grid.grid_line_alpha = 0
    p.ygrid.band_fill_color = "olive"
    p.ygrid.band_fill_alpha = 0.1

    # Deactivate the hover tool by default
    p.toolbar.active_inspect = None

    # Customize the legend
    p.legend.location = 'top_left'
    p.legend.click_policy = "hide"

    # Output to notebook or file
    output_notebook()  # Use this if running in a Jupyter notebook
    # output_file("nuclear_contributions_by_facility.html")  # Use this to save to a file

    # Show the plot
    show(p)

    return radiocarbonObject

def plot_radiocarbon_bokhe_model_meas(radiocarbonObjectMeas):
    df = radiocarbonObjectMeas.df_for_plot

    station = radiocarbonObjectMeas.stationId
    station_name = radiocarbonObjectMeas.settings['stilt']['name']

    if station_name != '':
        for_title = '∆14C at ' + station_name + ' (' + station + ')' 
    else:
        for_title = '∆14C at ' + station

    # Ensure datetime format is correct for Bokeh
    df['date'] = pd.to_datetime(df['date'])
    df['date_start'] = pd.to_datetime(df['date_start'])
    df['date_end'] = pd.to_datetime(df['date_end'])

    # Prepare the data for Bokeh
    source = ColumnDataSource(data={
        'date': df['date'],
        'Background': df['delta14C_background'],
        'Fossil': df['delta14C_fossil_fuel'],
        'Nuclear': df['delta14C_nuclear'],
        'Modelled': df['delta14C_modelled'],
        'Measured': df['Measurement_value'],
        'Std. Measured Δ14C': df['Std_deviation_measurement'],
        'date_start': df['date_start'],
        'date_end': df['date_end'],
        'count': df.get('count', [None]*len(df)),
        'count_nan': df.get('count_nan', [None]*len(df))
    })

    # Create the figure with adjusted size and labels
    p = figure(x_axis_type='datetime', plot_width=1000, plot_height=500, title=for_title,
               x_axis_label='Time (UTC)', y_axis_label='Δ14C [‰]',
               tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')

    # Add line plots with specific styles
    p.line('date', 'Background', source=source, legend_label='Background Δ14C', color='#984ea3', line_width=1, name='Background')
    p.line('date', 'Fossil', source=source, legend_label='Fossil fuel Δ14C', color='black', line_width=1, name='Fossil')
    p.line('date', 'Nuclear', source=source, legend_label='Nuclear Δ14C', color='#e41a1c', line_width=1, name='Nuclear')
    p.line('date', 'Modelled', source=source, legend_label='Modelled Δ14C', color='#0072B2', line_width=3, name='Modelled')
    p.line('date', 'Measured', source=source, legend_label='Measured Δ14C', color='green', line_width=3, name='Measured')

    # Update tooltips to display the full datetime
    tooltips = [
        ('Start UTC', '@date_start{%F %T}'),  # %F = YYYY-MM-DD, %T = HH:MM:SS
        ('End date', '@date_end{%F %T}'),
        ('Background Δ14C', '@Background{0.2f}'),
        ('Fossil fuel Δ14C', '@Fossil{0.2f}'),
        ('Nuclear Δ14C', '@Nuclear{0.2f}'),
        ('Modelled Δ14C', '@Modelled{0.2f}'),
        ('Measured Δ14C', '@Measured{0.2f}'),
        ('Std. Measured Δ14C', '@{Std. Measured Δ14C}{0.2f}'),  # Fix here
        ('# footprints', '@count{0f}'),
        ('# NaN footprint', '@count_nan{0f}')
    ]

    # Make sure to update formatters for the new datetime formatting
    formatters = {
        '@date_start': 'datetime',
        '@date_end': 'datetime',
        '@date': 'datetime'
    }

    # Add the hover tool with datetime format in tooltips
    hover = HoverTool(
        tooltips=tooltips,
        formatters=formatters,
        renderers=[p.select({'name': 'Measured'})[0]],  # Only display tooltip for the Modelled line
        mode='vline'
    )

    # Add hover tool to plot
    p.add_tools(hover)

    # Show the plot
    output_notebook()  # or output_file("delta_14c_components.html")
    show(p)

def nuclear_contamination_by_facility_map(radiocarbonObject):
    
    if radiocarbonObject.dfFacilitiesOverThreshold == 0:

        return
    
    # Filter facilities based on the average value threshold
    facilities_to_plot = radiocarbonObject.dfDelta14CFacility.loc[:, radiocarbonObject.dfDelta14CFacility.columns != 'date'].mean() > radiocarbonObject.threshold
    filtered_df = radiocarbonObject.dfDelta14CFacility[['date'] + facilities_to_plot[facilities_to_plot].index.tolist()]

    # Calculate average values for each facility
    avg_values = filtered_df.drop(columns=['date']).mean()
    avg_values = avg_values[facilities_to_plot[facilities_to_plot].index]
    avg_values = avg_values.round(2)

    # Load the emissions data
    df_emissions = pd.read_csv(os.path.join(folder_w_data, nuclear_emissions))

    # Initialize lists for latitude and longitude
    lats = []
    lons = []

    # Create a list for facilities that we want to include
    facilities_to_include = filtered_df.columns[1:]

    # Loop over the filtered facilities to get latitudes and longitudes
    for facility in facilities_to_include:
        lat = df_emissions[df_emissions['facility'] == facility]['lat'].values
        lon = df_emissions[df_emissions['facility'] == facility]['lon'].values

        # Ensure lat and lon are extracted correctly
        if len(lat) > 0 and len(lon) > 0:
            lats.append(lat[0])
            lons.append(lon[0])
        else:
            lats.append(None)
            lons.append(None)

    # Create the DataFrame with map information
    map_info = pd.DataFrame({
        'facility': facilities_to_include,
        'average_influence': avg_values[facilities_to_include].values,
        'lat': lats,
        'lon': lons
    })
    

    # Create a base map centered around the average latitude and longitude
    mean_lat = map_info['lat'].mean()
    mean_lon = map_info['lon'].mean()

    # Initialize the map
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=5)

    # Add Esri World Imagery layer
    esri_satellite = folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite'
    )
    esri_satellite.add_to(m)


    # Add markers for each facility in the map_info DataFrame
    for _, row in map_info.iterrows():
        popup_text = f"Name: {row['facility']}<br>Average influence (permil): {row['average_influence']:.2f}"
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='red', icon='map-marker')  # Customize marker icon and color
        ).add_to(m)


    STILT_station = stiltstation.get(id=radiocarbonObject.stationId )

    # Ensure that the 'icos' and 'uri' keys exist and that 'uri' is a list
    icos_info = STILT_station.info.get('icos', {})
    station_url = None
    if isinstance(icos_info, dict) and 'uri' in icos_info and isinstance(icos_info['uri'], list) and len(icos_info['uri']) > 0:
        station_url = icos_info['uri'][0]

    # Construct the popup text for the STILT station
    if station_url:
        popup_text = f"Station ID: {STILT_station.id}<br>Station name: <a href='{station_url}' target='_blank'>{STILT_station.name}</a>"
    else:
        popup_text = f"Station ID: {STILT_station.id}<br>Station name: {STILT_station.name}"

    # Add the marker for the STILT station
    folium.Marker(
        location=[STILT_station.lat, STILT_station.lon],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color='blue', icon='cloud')  # Customize marker icon and color
    ).add_to(m)

    # Add Layer Control to switch between tile layers
    folium.LayerControl().add_to(m)

    # Save the map to an HTML file
    #m.save('facilities_map.html')

    # Display the map in a Jupyter notebook (if you're using one)
    display(m)


def get_modelled_ts(radiocarbonObject):

    STILT_station = stiltstation.get(id=radiocarbonObject.stationId)

    STILT_co2 = STILT_station.get_ts(radiocarbonObject.dateRange.min(), radiocarbonObject.dateRange.max(), columns = 'co2')
    
    if len(STILT_co2) == 0:
        
        return STILT_co2

    STILT_co2 = STILT_co2[STILT_co2.index.hour.isin(radiocarbonObject.settings['timeOfDay'])]
    
    STILT_co2 = STILT_co2[STILT_co2.index.isin(radiocarbonObject.dateRange)]

    # this will be needed
    STILT_co2['fossil_fuel'] = STILT_co2['co2.fuel.coal'] + STILT_co2['co2.fuel.oil'] + STILT_co2['co2.fuel.gas'] 

    # only need the modelled concentration (co2.stilt) and the fossil fuel component (fossil_fuel)
    STILT_co2 = STILT_co2[['co2.stilt','fossil_fuel']]
    
    return STILT_co2

def get_nuclear_contamination(radiocarbonObject, STILT_co2_and_background):
    
    # radiocarbon emission grid for all years. Access specific year in loop. 
    fp_nuclear_emissions = access_nuclear_emission_data()
    
    facility_info = fp_nuclear_emissions.facility_info.values.tolist()
    
    # Prepare a Series for the 'co2.stilt' values, indexed by date
    modelled_concentration_series = STILT_co2_and_background['co2.stilt'] / 1000000

    dates = list(radiocarbonObject.dateRange)
    # Initialize a DataFrame to store the nuclear contributions for each facility
    df_nuclear_facilities = pd.DataFrame({
        'date': dates
    })

    # Initialize an empty array for total nuclear contribution  
    nuclear_contributions = np.full(len(dates), np.nan)

    i = 0
    
    st = stiltstation.get(id=radiocarbonObject.stationId)
    
    date_range = radiocarbonObject.dateRange


    # Iterate through the dates
    first = True
    
    use_latest_available_emission = False

    for date in radiocarbonObject.dateRange:
        
        if first or date.year != data_year:

            data_year = date.year
            
            if data_year > max_year:

                use_latest_available_emission = True
                data_year = max_year
                
            fp_Gbq = fp_nuclear_emissions.sel(year=data_year).emissions
            
            fp_bq_s = (fp_Gbq*1000000000)/31536000
            
            fp_bq_s_m2 = fp_bq_s / fp_nuclear_emissions.area.values
            
            first = False
            
        
        try:
            
            modelled_concentration = modelled_concentration_series.loc[date]
            
            if not np.isnan(modelled_concentration):
            
                # access only one footprint if use the same start- and end date. 
                # use isel (index select) to get the array of that first (and only) footprint.
                fp = st.get_fp(date, date).isel(time=0)

                # Vectorized calculation for the entire grid at once
                nuclear_contribution_grid = (((fp_bq_s_m2 * fp.foot.values) / 
                                              (modelled_concentration * Mc * Aabs))) * 1000#.values

                # Sum the contributions for this date and store in the array
                nuclear_contributions[i] = nuclear_contribution_grid.sum()

                # Extract contributions for each facility
                if radiocarbonObject.settings['facilityInclusion']:

                    for facility, lat_idx, lon_idx in facility_info:
                        # Get the value for this facility's grid cell on this date
                        value = nuclear_contribution_grid[int(lat_idx), int(lon_idx)]

                        # Add the value to the DataFrame
                        if facility not in df_nuclear_facilities.columns:
                            df_nuclear_facilities[facility] = np.nan  # Initialize column with NaN

                        df_nuclear_facilities.at[i, facility] = value

                else:

                    if radiocarbonObject.settings['facilityInclusion']:

                        for facility, lat_idx, lon_idx in facility_info:

                            df_nuclear_facilities.at[i, facility] = value
                        
        except:
            # df_nuclear_facilites and nuclear_totals already pre-filled with NaN values. If no footprint is available, it will stay that way. 
            pass

        i = i + 1

    if use_latest_available_emission:
        print(f'Using nuclear emissions from {max_year}')
    # The resulting DataFrame `df_nuclear_facilities` will have one row per date and one column per facility, along with the 'date' column.

    # Dataframe with the total nuclear contribution
    df_nuclear_total = pd.DataFrame({
        'date': dates,
        'delta_14c_nuclear': nuclear_contributions
    })
    
    return df_nuclear_total, df_nuclear_facilities


def find_closest_date_value(target_date, background_df):
    """
    Find the closest date in background_df that has a non-NaN 'FIT' value.
    """
    closest_row = background_df.iloc[(background_df['DateTime'] - target_date).abs().argsort()[:1]]
    return closest_row['FIT'].values[0]

    
#create dataframes with delta14C, used in radiocarbon_object. Returned and added to the radiocarbonObject
def delta_radiocarbon_dataframes(radiocarbonObject):

    station=radiocarbonObject.stationId
    station_name=radiocarbonObject.settings['stilt']['name']
    date_range=radiocarbonObject.dateRange
    timeselect=radiocarbonObject.settings['timeOfDay']
    background_filename=radiocarbonObject.settings['backgroundFilename']
    
    facility_inclusion=radiocarbonObject.settings['facilityInclusion']
    threshold=radiocarbonObject.settings['threshold']
    
    # df with total modelled concentraiton in one column, and the fossil fuel component in another column
    # for date in date range. 
    modelled_co2 = get_modelled_ts(radiocarbonObject)
    
    if len(modelled_co2) == 0:
        
        if facility_inclusion:
            return None, None
        else: 
            return None
        
    
    # access background delta 14C values
    background_values = pd.read_csv(os.path.join(folder_w_data, background_filename))
    
    #########################
    # merge modelled and background.

    # Ensure the 'date' index in STILT_co2 is in datetime format
    modelled_co2.index = pd.to_datetime(modelled_co2.index)

    # Convert the 'DateTime' column in background_values to datetime format
    background_values['DateTime'] = pd.to_datetime(background_values['DateTime'])

    # Extract the date part only for merging
    modelled_co2['date_only'] = modelled_co2.index.date
    background_values['date_only'] = background_values['DateTime'].dt.date

    # Perform the merge operation
    merged_df = pd.merge(modelled_co2.reset_index(), background_values[['date_only', 'FIT']],
                         left_on='date_only', right_on='date_only', how='left')

    # Drop the 'date_only' column and reset the index
    merged_df.drop(columns=['date_only'], inplace=True)

    # Rename the 'FIT' column to 'delta_14C_background'
    merged_df.rename(columns={'FIT': 'delta_14C_background'}, inplace=True)
    
    # Fill NaN values in 'delta_14C_background' using both forward and backward fill
    merged_df['delta_14C_background'].fillna(method='ffill', inplace=True)
    merged_df['delta_14C_background'].fillna(method='bfill', inplace=True)
    
    # For rows still with NaN, find the closest date with a valid 'FIT' value
    nan_rows = merged_df['delta_14C_background'].isna()
    if nan_rows.any():
        for idx in merged_df[nan_rows].index:
            target_date = merged_df.at[idx, 'date']
            closest_value = find_closest_date_value(target_date, background_values)
            merged_df.at[idx, 'delta_14C_background'] = closest_value

    # Set the index back to the original date index
    STILT_co2_and_background = merged_df.set_index('date')
    
    # calculate the not nuclear corrected modelled delta 14C values
    STILT_co2_and_background['delta_14c_not_nuclear_corrected'] = (STILT_co2_and_background['fossil_fuel'] / STILT_co2_and_background['co2.stilt'])*(STILT_co2_and_background['delta_14C_background'] + 1000) -STILT_co2_and_background['delta_14C_background']

    # flip signs
    STILT_co2_and_background['delta_14c_not_nuclear_corrected'] = STILT_co2_and_background['delta_14c_not_nuclear_corrected'] * -1

    # FOSSIL DELTA 14C here already - cannot calculate without knowing the nuclear though? 
    STILT_co2_and_background['delta_14c_fossil'] =STILT_co2_and_background['delta_14c_not_nuclear_corrected'] - STILT_co2_and_background['delta_14C_background']

    #df_nuclear_facilities empty in case of 
    df_nuclear_total, df_nuclear_facilities = get_nuclear_contamination(radiocarbonObject, STILT_co2_and_background)

    # Ensure the 'date' column in df_nuclear_total is in datetime format
    df_nuclear_total['date'] = pd.to_datetime(df_nuclear_total['date'])

    # Merge the dataframes on the 'date' field
    merged_df = pd.merge(STILT_co2_and_background.reset_index(), df_nuclear_total, on='date', how='left')

    # Drop the redundant 'date' column from df_nuclear_total if needed
    #merged_df.drop(columns=['date'], inplace=True)

    # Now, merged_df contains all rows from STILT_co2_final, 
    # with the 'nuclear' field from df_nuclear_total where available
    merged_df['delta_14c_nuclear_corrected'] = merged_df['delta_14c_not_nuclear_corrected'] + merged_df['delta_14c_nuclear']

    
    if facility_inclusion:
    
        return merged_df, df_nuclear_facilities
    
    else:
        
        return merged_df
    
    
# MEASURED DATA FROM CP IN COMBINATION WITH MODELLING OF DELTA14C.
#get the list of stations with radiocarbon measurement data at the Carbon Portal server. 
#takes a while, potential improvement? 
def list_station_tuples_w_radiocarbon_data():
       
    sparql = RunSparql()
    sparql.format = 'pandas'
    sparql.query = open(os.path.join(folder_w_data, 'c14.sparql'), 'r').read()
    df_stations_w_radiocarbon_data_cp = sparql.run() 
    
    list_of_tuples_for_dropdown=[]
    
    for index, row in df_stations_w_radiocarbon_data_cp.iterrows():
        station_name = row['stationName']
        station_id = row['stationId']
        sampling_height = int(float(row['samplingHeight']))
        
        display = station_name + ' (' + str(sampling_height) + 'm)'
        
        values_dictionary = {'station_code': station_id, 'sampling_height':sampling_height}
        
        if not (station_id == 'JFJ' and sampling_height == 10):
        
            list_of_tuples_for_dropdown.append((display, values_dictionary)) 

    return list_of_tuples_for_dropdown
    
def radiocarbon_cp_results(radiocarbonObjectMeas):
    
    stilt_station = radiocarbonObjectMeas.stationId
    timeselect_list = radiocarbonObjectMeas.settings['timeOfDay']
    timeselect_list_sting=', '.join(str(x) for x in timeselect_list)
    background_filename = radiocarbonObjectMeas.settings['backgroundFilename']
    background_values = pd.read_csv(os.path.join(folder_w_data, background_filename))
    background_values['DateTime'] = pd.to_datetime(background_values['DateTime'])


    download_option = radiocarbonObjectMeas.settings['downloadOption']
    meas_station = radiocarbonObjectMeas.stationId[0:3]
    meas_sampling_height = radiocarbonObjectMeas.settings['samplingHeightMeas']
   
    stilt_station_alt=radiocarbonObjectMeas.settings['stilt']['alt']
    stilt_station_name=radiocarbonObjectMeas.settings['stilt']['name']
    stilt_station_lat=radiocarbonObjectMeas.lat
    stilt_station_lon=radiocarbonObjectMeas.lon
    
    date_today= current_date.today()

    #dataframe with all the measurements. Loop over.
    radiocarbon_data= radiocarbonObjectMeas.measuredData

    #before SamplingStartDate and SamplingEndDate (date_start, date_end)
    df_for_export = pd.DataFrame(columns=['date_start_model','date_end_model','date_start_meas','date_end_meas','Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled','count', 'count_nan'])
    
    #this dataframe is added to twice for each measurement (since integrated - start and end data)
    #the 'date' column will first get the same value as SamplingStartDate and the second time the 
    #same value as SamplingEndDate
    df_for_plot = pd.DataFrame(columns=['date', 'date_start','date_end','Measurement_value','Std_deviation_measurement','delta14C_background', 'delta14C_nuclear','delta14C_fossil_fuel', 'delta14C_modelled', 'count', 'count_nan'])
    
    index=0
    #the plot dataframe will be added to twice in each loop (start - and end time same values for line in graph
    #across integration time. 
    index_plot=0
    
    if 'dateStart' in radiocarbonObjectMeas.settings:
        user_date_range_start = pd.to_datetime(radiocarbonObjectMeas.settings['dateStart'])
        user_date_range_end = pd.to_datetime(radiocarbonObjectMeas.settings['dateEnd'])
    else:
        user_date_range_start=pd.Timestamp(2006, 1, 1)
        user_date_range_end=pd.Timestamp(2030, 1, 1)
        
    f = IntProgress(min=0, max=len(radiocarbon_data['14C'])) # instantiate the bar
    display(f) 
    
    first=True
    
    #access many at the same time (all the entries - one for each radiocarbon measurement)
    #for each entry at the carbon portal (not all will be used - only when footprints for the same time period)
    for (radiocarbon_measurement, measurement_start_date, integration_time, std_deviation) in zip(radiocarbon_data['14C'], radiocarbon_data['TIMESTAMP'], radiocarbon_data['IntegrationTime'], radiocarbon_data['WeightedStdErr']):
        
        f.value += 1
    
        #want to keep the original date for the export.
        measurement_start_date_model = measurement_start_date

        if measurement_start_date.hour not in timeselect_list or measurement_start_date.minute>0 or measurement_start_date.second>0:

            updated_hour=min(timeselect_list, key=lambda x:abs(x-measurement_start_date.hour))

            measurement_start_date_model = dt.datetime(int(measurement_start_date.year), int(measurement_start_date.month), int(measurement_start_date.day), updated_hour, 0, 0)

        measurement_end_date_model = measurement_start_date_model + timedelta(days=int(integration_time))
        measurement_end_date = measurement_start_date + timedelta(days=int(integration_time))
        
        if measurement_start_date>user_date_range_start and measurement_end_date<user_date_range_end:
            
            full_range = pd.date_range(start=measurement_start_date_model, end=measurement_end_date_model, freq='3H')
            date_range_measured = full_range[full_range.hour.isin(timeselect_list)]
            
            if date_range_measured.empty:
                print('no footprints for date range of measured concentration (',min(date_range_measured), 'to', max(date_range_measured), ')')
                continue

            # added to radiocarbon object since it is needed in the get_modelled_ts (used also by passing radiocarbonObject)
            # could not be added to the object when it was created as the date range is defined by what measurements are available.
            radiocarbonObjectMeas.dateRange = date_range_measured
            if not hasattr(radiocarbonObjectMeas, 'settings'):
                radiocarbonObject.settings = {}
            radiocarbonObjectMeas.settings['timeOfDay'] = timeselect_list
            
            modelled_concentration = get_modelled_ts(radiocarbonObjectMeas) #read_stilt_timeseries(stilt_station, date_range_measured)

            if len(modelled_concentration) == 0:
                continue 
            # date, delta_14c_nuclear
            df_nuclear_total, df_nuclear_facility = get_nuclear_contamination(radiocarbonObjectMeas, modelled_concentration)
            
            shift_nuclear=df_nuclear_total["delta_14c_nuclear"].mean()
            count = len(df_nuclear_total)
            count_nan = df_nuclear_total['delta_14c_nuclear'].isna().sum()
            

            # find dates to filter the df with background
            closest_start_date = background_values.loc[
                (background_values['DateTime'] - measurement_start_date_model).abs().idxmin(), 'DateTime'
            ]

            closest_end_date = background_values.loc[
                (background_values['DateTime'] - measurement_end_date_model).abs().idxmin(), 'DateTime'
            ]

            # Filter the DataFrame between the closest start and end dates
            filtered_df = background_values[
                (background_values['DateTime'] >= closest_start_date) & (background_values['DateTime'] <= closest_end_date)
            ]

            # Calculate the average of the "FIT" column
            shift_background = filtered_df['FIT'].mean()
            
            ######
            # shift modelled nuclear corrected
            
            shift_modelled_not_nuclear_corrected = (modelled_concentration["fossil_fuel"].mean() / modelled_concentration["co2.stilt"].mean()) * (shift_background + 1000) - shift_background 
            
            # flip signs:
            shift_modelled_not_nuclear_corrected = shift_modelled_not_nuclear_corrected * -1
            
            shift_fossil_fuel = shift_modelled_not_nuclear_corrected  - shift_background
            
            shift_modelled_nuclear_corrected = shift_modelled_not_nuclear_corrected + shift_nuclear

            df_for_export.loc[index] = [measurement_start_date_model, measurement_end_date_model, measurement_start_date, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled_nuclear_corrected, count, count_nan]

            #index to move to the next row for the next integrated sample 
            index=index+1  
            
            df_for_plot.loc[index_plot] = [measurement_start_date_model, measurement_start_date_model, measurement_end_date, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled_nuclear_corrected, count, count_nan]

            index_plot = index_plot + 1

            #measurement_end_date into date column. otherwise same values as above record.
            df_for_plot.loc[index_plot] = [measurement_end_date_model, measurement_start_date_model, measurement_end_date_model, radiocarbon_measurement, std_deviation,shift_background, shift_nuclear, shift_fossil_fuel, shift_modelled_nuclear_corrected, count, count_nan]
            index_plot = index_plot + 1
            
    return df_for_export, df_for_plot
       
               
# DATA FROM UPLOADED FILE (PROVIDED BY HEIDELBERG --> not in version that goes on exploretest.
def dropdown_stations_from_file(radiocarbon_data, location, sampling_height, crl):
    
    unique_location_elevation_crl=radiocarbon_data.groupby([location,sampling_height, crl]).size().reset_index().rename(columns={0:'count'})
    
    stations_list= unique_location_elevation_crl[location].tolist()

    location_height_list= unique_location_elevation_crl[sampling_height].tolist()

    #'CRL_sampler'
    crl_sampler_list= unique_location_elevation_crl[crl].tolist()
    
    list_of_tuples_for_dropdown=[]

    for (station_code, location_height, crl_sampler) in zip(stations_list, location_height_list, crl_sampler_list):

        display_name= station_code + ' (' + str(location_height) + 'm, ' + str(crl_sampler) + ' CRL)'

        #return many values for the user selected option (code, crl sampler, location height all to be used later also)
        value_dictionary = {'station_code': station_code, 'crl_sampler': crl_sampler, 'location_height':location_height}

        station_tuple_for_dropdown=(display_name, value_dictionary)

        if len(station_code)==3:
            list_of_tuples_for_dropdown.append(station_tuple_for_dropdown)
        
        
    return list_of_tuples_for_dropdown

def save_data(radiocarbonObject, meas_cp=False):

    def save_json(data, file_path):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def save_csv(dataframe, columns, file_name):
        file_path = os.path.join(radiocarbonObject.settings['output_folder'], file_name)
        dataframe[columns].to_csv(file_path, index=False)

    # Save settings to a JSON file
    settings_file = os.path.join(
        radiocarbonObject.settings['output_folder'],
        f"{radiocarbonObject.settings['date/time generated']}{radiocarbonObject.stationId}_settings.json"
    )
    save_json(radiocarbonObject.settings, settings_file)

    # Define the file path for the README.txt file
    readme_file_path = os.path.join(radiocarbonObject.settings['output_folder'], 'README.txt')
    
    if meas_cp:
        filename = "df14C_model_measure.csv"
    else:
        filename = "dfDelta14CStation.csv"

    # Prepare the text to write to the README.txt file
    readme_content = f"""
This folder contains a file called {filename} which contains the modelled Δ14C components at different dates/times at a selected STILT station. These have been derived from STILT model runs and data on emissions from nuclear facilities.

More information about Δ14C and its components can be found in Levin et al., 2003: https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2003GL018477.

Information about the data on emissions from nuclear facilities is available here: https://meta.icos-cp.eu/objects/Qa5PvLgEeiXW3IRAfTU5d_Oo.

More information about the STILT transport model used can be found here: https://meta.icos-cp.eu/objects/CXlfZnsBKibuov6SkJ8eIlVX.

Station details:
- STILT footprints code: {radiocarbonObject.stationId}
- STILT altitude above ground: {radiocarbonObject.settings['stilt']['alt']} m
- STILT position latitude: {radiocarbonObject.lat}°N
- STILT position longitude: {radiocarbonObject.lon}°E
"""

    if meas_cp:
        # Save the main station data
        station_columns = list(radiocarbonObject.df_for_export.columns)
        save_csv(radiocarbonObject.df_for_export, station_columns, filename)
        
        readme_content += f"""Measured 14C data is collected from ICOS: https://meta.icos-cp.eu/resources/cpmeta/atcC14L2DataObject    
    """
    else:
        
        # Save the main station data
        station_columns = ['date', 'delta_14C_background', 'delta_14c_fossil', 'delta_14c_nuclear', 'delta_14c_nuclear_corrected']
        save_csv(radiocarbonObject.dfDelta14CStation, station_columns, 'dfDelta14CStation.csv')

        # Save facilities data if there are facilities over the threshold
        if radiocarbonObject.dfFacilitiesOverThreshold > 0:
            facilities_columns = ['date'] + radiocarbonObject.dfFacilitiesOverThresholdList
            save_csv(radiocarbonObject.dfDelta14CFacility, facilities_columns, 'dfDelta14CSFacility.csv')

            readme_content += f"""
    This folder also contains a file called "dfDelta14CFacility.csv", which shows the nuclear component for each facility contributing above a specified threshold. The average is given across all dates/times stored in the file.

    Specified threshold: {radiocarbonObject.settings['threshold']}
    """

        # Save resampled station data
        if radiocarbonObject.dfDelta14CStationResample is not None:
            resample_columns = [
                'date_start', 'date_end', 'count_footprints', 'count_nan_footprints', 
                'delta_14C_background', 'delta_14c_fossil', 
                'delta_14c_nuclear', 'delta_14c_nuclear_corrected'
            ]
            save_csv(radiocarbonObject.dfDelta14CStationResample, resample_columns, 'dfDelta14CStationResample.csv')

            readme_content += f"""
    The file "dfDelta14CStationResample.csv" is based on "dfDelta14CStation.csv" but contains averages for all components between the dates in "date_start" and "date_end". The "count_footprints" field indicates the number of timesteps in "dfDelta14CStation.csv" that have been averaged, while "count_nan_footprints" indicates missing timesteps due to the lack of footprints. Missing footprints are common for mountain stations.
    """

            # Save resampled facilities data if there are facilities over the threshold
            if radiocarbonObject.dfFacilitiesOverThreshold > 0:
                resample_facilities_columns = ['date_start', 'date_end', 'count_footprints', 'count_nan_footprints'] + radiocarbonObject.dfFacilitiesOverThresholdList
                save_csv(radiocarbonObject.dfDelta14CFacilityResample, resample_facilities_columns, 'dfDelta14CSFacilityResample.csv')

                readme_content += f"""
    The file "dfDelta14CFacilityResample.csv" is similar to "dfDelta14CStationResample.csv" but contains averages from "dfDelta14CFacility.csv".
    """

    # Write the content to the README.txt file
    with open(readme_file_path, 'w') as f:
        f.write(readme_content)

    
def display_info_html_table(radiocarbonObject, meas_data=False, cp_private=False):
    
    stilt_station = radiocarbonObject.stationId
    stilt_station_alt = radiocarbonObject.settings['stilt']['alt']
    stilt_station_lat = radiocarbonObject.settings['stilt']['lat']
    stilt_station_lon = radiocarbonObject.settings['stilt']['lon']
    date_today = current_date.today()
    background_filename = radiocarbonObject.settings['backgroundFilename']
    
    if meas_data==False:
        
        min_date_range = min(radiocarbonObject.dateRange)
        max_date_range = max(radiocarbonObject.dateRange)
        sting_min_date_range = str(min_date_range.year) + '-' + str(min_date_range.month) + '-' + str(min_date_range.day)
        sting_max_date_range = str(max_date_range.year) + '-' + str(max_date_range.month) + '-' + str(max_date_range.day)

        html_date_range = '<b>Footprint selection (date range):</b> ' + sting_min_date_range + ' to ' + sting_max_date_range + '<br>'
        
        timeselect_list = radiocarbonObject.settings['timeOfDay']
        timeselect_string=[str(value) for value in timeselect_list]
        timeselect_string =':00, '.join(timeselect_string) + ':00 (UTC)<br>'
        
        html_timeselect_string = '<b>Footprint selection (hours):</b> ' + timeselect_string
        
        html_meas_station = ''
        
        flask_string = ''
        
        clr_string = ''
        
        string_start_end_date = ''
        
        background_info_string = ''
        
        
    else:
        
        html_timeselect_string = ''
        html_date_range = ''
        
        if 'clrSampler' in radiocarbonObject.settings:
            clr_string= '<b>CLR Sampler</b>: ' + radiocarbonObject.settings['clrSampler'] 
        else:
            clr_string = ''
    
        if cp_private:
            meas_station = radiocarbonObject.settings['icos']['name']
            background_info_string = '<br>The background represents the marinenatural ∆14C levels and is based on measurements at stations supposedly not influenced directly by nuclear power plants and fossil fuel emissions. The measurements have been used to establish harmonic fit curves. The fitted data was provided by Ingeborg Levin at <a href="https://www.icos-cal.eu/crl" target="_blank">the Central Radiocarbon Laboratory in Heidelberg</a>. The curve is based on measurements from MHD (Mace Head). Improved background curves may become available in the future and it is an ongoing discussion what background is best to use.'

        else:
            background_info_string = ''
            meas_station = stilt_station[0:3]
        try:
            meas_sampling_height = radiocarbonObject.settings['samplingHeightMeas']
            
        except:
            meas_sampling_height = ''
            
        html_meas_station = '<br><b>Location (measurements):</b> ' + meas_station + '<br><b>Sampling height, elevation above ground (measurements):</b> ' + str(meas_sampling_height) + 'm<br>'
        
        if 'TIMESTAMP' in radiocarbonObject.measuredData.columns:
            start_date_column = 'TIMESTAMP'
           
        else:
            
            start_date_column = radiocarbonObject.settings['startDateColumn']
            
            
        if 'flask' in radiocarbonObject.settings:
            
            flask_string = '<br><b>Measurements from flask</b>: ' + str(radiocarbonObject.settings['flask']) 
            
        else:
            flask_string = ''
            
        
        #will happen for ICOS CP data - for date range in title
        #use this for the HTML display instead. 
        if 'TIMESTAMP' in radiocarbonObject.measuredData.columns:
            start_date_start = pd.Timestamp(min(radiocarbonObject.measuredData['TIMESTAMP']))
            end_date_start = max(radiocarbonObject.measuredData['TIMESTAMP'])
            
            #need to locate the correct integrationtime to know when the last sample ENDED. .
            end_date_start_integration_time = radiocarbonObject.measuredData.loc[radiocarbonObject.measuredData['TIMESTAMP'] == end_date_start, 'IntegrationTime']

            end_date_end =  pd.Timestamp(end_date_start) + timedelta(days=int(end_date_start_integration_time))
            #no end date column, rather column "IntegrationTime". End date = start_date + IntegrationTime
            
           
        #will happen for uploaded data - for date range in title
        else:
            
            start_date_column = radiocarbonObject.settings['startDateColumn']
            end_date_column = radiocarbonObject.settings['endDateColumn']
            
            start_date_start = pd.Timestamp(min(radiocarbonObject.measuredData[start_date_column]))
            end_date_end = pd.Timestamp(max(radiocarbonObject.measuredData[end_date_column]))
            
        #use year, month, day... don't want the hour in the title 
        if cp_private:
            string_start_end_date =  '<br><b>Date range measurements</b>: ' + str(start_date_start.year) + '-' + str(start_date_start.month) + '-' + str(start_date_start.day) + ' to ' + str(end_date_end.year) + '-' + str(end_date_end.month) + '-' + str(end_date_end.day)  + '<br>If the date range in the graph is different, footprints are missing. Compute footprints <a href="https://stilt.icos-cp.eu/worker/" target="_blank">here</a>.'
            
        else:
            string_start_end_date =  '<br><b>Date range measurements</b>: ' + str(start_date_start.year) + '-' + str(start_date_start.month) + '-' + str(start_date_start.day) + ' to ' + str(end_date_end.year) + '-' + str(end_date_end.month) + '-' + str(end_date_end.day)  + '<br>If the date range in the graph is different, "Pick start date" and "Pick end date" is the restricting factor or footprints are missing. Compute footprints <a href="https://stilt.icos-cp.eu/worker/" target="_blank">here</a>.'
          

    display(HTML('<p style="font-size:15px;"><b>Information relevant for analysis (also included in the README-file if the data is downloaded)</b><br><br> '\
    'Yearly average radiocarbon emissions data from <a href="https://europa.eu/radd/" target="_blank">RADD</a> for countries in the European Union are complemented with reports for UK and Swiss facilities. For Ukraine and Russia, the estimates are based on energy production statistics from the IAEA. We used the same approach as Zazzeri et al. 2018, where emission factors for the release of 14C for different reactor types are listed. Furthermore, for all facilities with pressurized water reactors, an estimated 28% of the 14C is released as CO2 (Zazzeri et al., 2018).<br><br>' + \
    '<b>STILT transport model used to generate footprints:</b><br><ul><li>10 days backward simulation</li><li>1/8° longitude x 1/12° latitude resolution</li><li>Meteorological data from ECMWF: 3 hourly operational analysis/forecasts on 0.25 x 0.25 degree</li></ul>' +\
    '<b>STILT footprints code:</b> ' + stilt_station + '<br><b>STILT altitude above ground:</b> ' + str(stilt_station_alt) + 'm<br>' + \
    '<b>STILT position latitude:</b> ' + str(stilt_station_lat) + '°N<br>' + '<b>STILT position longitude:</b> ' + str(stilt_station_lon) + '°E<br>' + html_date_range + html_timeselect_string + flask_string + html_meas_station +  clr_string + string_start_end_date +\
    '<br><b>∆14C background file</b>: ' + background_filename + background_info_string + '<br><br><b>Date of analysis:</b> ' + str(date_today) + '</p>'))
    