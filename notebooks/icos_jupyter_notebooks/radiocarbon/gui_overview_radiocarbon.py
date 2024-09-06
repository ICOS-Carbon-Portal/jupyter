import pandas as pd
import ipywidgets as widgets
from ipywidgets import Output, VBox
from IPython.core.display import display, HTML 
from IPython.display import clear_output
import folium
from icoscp_core.icos import meta, ATMO_STATION
from icoscp_core.icos import station_class_lookup
import pandas as pd
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

def overview_map(selected_year):
    
    clear_output()
    
    # Read CarbonPortal dataset extended with Reactor Types
    df = pd.read_csv("radiocarbon/facilities_GBq_year_2006_2022_upd_2024_09_04.csv", decimal=".")

    # Fetch and filter ICOS stations of interest
    atmo_class1 = [
        s for s in meta.list_stations(ATMO_STATION)
        if station_class_lookup().get(s.uri) == '1'
    ]
    atmo_class1 = pd.DataFrame(atmo_class1)

    # Color palette for reactor types
    color_palette = {
        "PWR": "#d62728",  # Red
        "BWR": "#ff7f0e",   # Orange
        "Mixed": "#2ca02c", # Green
        "Other":  "#1f77b4",   # Blue
    }
    
    # Define size scaling
    max_size_val = 6000
    size_scale = 70  # Adjust for folium (smaller scale compared to Plotly)
    min_size = 3     # Minimum size for the smallest point

    # Calculate sizes for the markers
    df['size'] = df[selected_year] / max_size_val
    df['size'] = df['size'].apply(lambda x: max(min_size, x * size_scale) if x <= 1 else size_scale)

    # Determine color based on reactor type
    def determine_color(facility_type):
        if "/" in facility_type:
            return color_palette["Mixed"]
        elif "PWR" in facility_type:
            return color_palette["PWR"]
        elif "BWR" in facility_type:
            return color_palette["BWR"]
        else:
            return color_palette["Other"]

    # Assign colors to facilities
    df['color'] = df['facility_type'].apply(determine_color)

    # Initialize the map
    map_center = [53, 11]
    map = folium.Map(location=map_center, zoom_start=5, tiles='CartoDB positron')

    # Add facility markers
    for i, row in df.iterrows():
        folium.CircleMarker(
            location=(row['lat'], row['lon']),
            radius=row['size'],
            color=row['color'],
            fill=True,
            fill_color=row['color'],
            fill_opacity=0.6,
            popup=f"{row['facility']} ({row['facility_type']}): {row[selected_year]:.2f} GBq {selected_year}",
        ).add_to(map)

    # Add ICOS stations as stars
    for i, row in atmo_class1.iterrows():
        folium.Marker(
            location=(row['lat'], row['lon']),
            icon=folium.Icon(color='blue', icon='cloud'),#prefix='fa'
            popup=f'<a href="{row["uri"]}" target="_blank">{row["name"]}</a>', max_width=300
        ).add_to(map)
        
        # Adding the bubble size legend
        bubble_lat = [43, 47, 50]  # Adjust latitudes for each bubble
        bubble_lon = -12
        bubble_lons = [bubble_lon, bubble_lon, bubble_lon]  # Same longitude for the legend
        bubble_sizes = [size_scale, size_scale/2, size_scale/10]
        bubble_names = [f"> {max_size_val} GBq/yr", f"{max_size_val/2:.0f} GBq/yr", f"{max_size_val/10:.0f} GBq/yr"]

        # Add bubble sizes as legend
        for lat, size, name in zip(bubble_lat, bubble_sizes, bubble_names):
            folium.CircleMarker(
                location=(lat, bubble_lon),
                radius=size,  # Size of the bubble
                color='#000000',
                fill=True,
                fill_color='#FFFFFF',
                fill_opacity=0.6,
            ).add_to(map)

            folium.Marker(
                location=(lat, bubble_lon-2),  
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 12pt; width: 1000px; white-space: nowrap;">{name}</div>'
                )
            ).add_to(map)

    # Add a legend manually (since Folium doesn't support legends directly)
    legend_html = '''
         <div style="position: fixed; 
         bottom: 50px; left: 50px; width: 190px; height: 140px; 
         background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
         ">&nbsp; <b>Legend</b><br>
         &nbsp; <i style="background:{PWR};opacity:0.6;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</i>&nbsp; PWR <br>
         &nbsp; <i style="background:{BWR};opacity:0.6;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</i>&nbsp; BWR <br>
         &nbsp; <i style="background:{Mixed};opacity:0.6;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</i>&nbsp; >1 reactor type <br>
         &nbsp; <i style="background:{Other};opacity:0.6;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</i>&nbsp; Other <br>
         &nbsp; <i class="fa fa-cloud" style="color:blue;"></i>&nbsp; ICOS Class 1 Stations
         </div>
         '''.format(**color_palette)

    map.get_root().html.add_child(folium.Element(legend_html))
    
    return map

# Load the data
nuclear_emissions = pd.read_csv('radiocarbon/facilities_GBq_year_2006_2022_upd_2024_09_04.csv')

# Find columns that can be converted to integers (i.e., years)
years = [col for col in nuclear_emissions.columns if col.isdigit()]

# Create a dropdown widget for selecting the year
year_dropdown = widgets.Dropdown(
    options=years,
    description='Select Year:',
    style={'description_width': 'initial'},
    layout = {'width': '200px', 'height': 'initial'}#layout=widgets.Layout(width='200px')
)

# Create an update button
update_button = widgets.Button(
    description='Update',
    button_style='primary',
    layout = {'width': '200px', 'height': 'initial'}#layout=widgets.Layout(width='100px')
)

# for output in Jupyter Notebook
plot_out = Output() 

# Define the function to call when the button is clicked
def on_update_button_clicked(b):
    
    selected_year = year_dropdown.value
    
    with plot_out:
        display(overview_map(selected_year))

# Link the button click event to the function
update_button.on_click(on_update_button_clicked)

# Display the dropdown and button
form_out = widgets.VBox([year_dropdown, update_button, plot_out])

display(widgets.HTML(style_scroll),form_out)  