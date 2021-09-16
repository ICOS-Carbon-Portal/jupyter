from bokeh.io import show, output_notebook, reset_output, export_png
from bokeh.plotting import figure as bokeh_figure
from bokeh.plotting import figure 
from bokeh.models import HoverTool,WheelZoomTool, PanTool, ResetTool
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend
reset_output()
output_notebook()    
import pandas as pd
import sys
import os
sys.path.append('../station_characterization')
import stc_functions as stc
from matplotlib import cm
import matplotlib
from datetime import datetime
import json

def variables_graph_bokeh(df, variables, variables_weights):

    p = bokeh_figure(plot_width=900,
               x_range=variables,
               plot_height=700, 
               y_axis_label='% of max',
               title = 'Selected station compared to reference stations',
               tools=[PanTool(), WheelZoomTool(), ResetTool(), HoverTool(tooltips=[("Percent of max", "$y"),])])

    list_stations = list(df['Station'])
    
    list_station_scores = []
    for station in list_stations:
        
        station_values=df.loc[df['Station'] == station]
        
        station_score = 0
        
        #except combined score (not in the dataframe with computed values) which is first in the variables list 
        for variable, variable_weight in zip(variables[1:], variables_weights):
            
            list_reverse_values = ['Population','Point source contribution', 'Anthropogenic contribution']
            if variable in list_reverse_values:
                
                station_score = station_score + ((100-station_values[variable].values[0]) * (variable_weight/100))
                
            else:
                station_score = station_score + (station_values[variable].values[0] * (variable_weight/100))
            
        list_station_scores.append(station_score)
    
    sorted_list_stations = [x for _,x in sorted(zip(list_station_scores,list_stations), reverse=True)]
    sorted_list_station_scores = [x for _,x in sorted(zip(list_station_scores,list_station_scores), reverse=True)]

    #want the total score to range between 0 (worst combined score) and 100 (best combined score)
    sorted_list_station_scores_normalized = []    
    for value in sorted_list_station_scores:
        normalized_value = (value - min(sorted_list_station_scores))/(max(sorted_list_station_scores) - min(sorted_list_station_scores))*100
        sorted_list_station_scores_normalized.append(normalized_value)

    # cmap - one color for each station that will have a line (best total score will have the darkest red)
    # +1 to avoid the lightest color which one can barely see. 
    cmap = cm.get_cmap('Reds_r',(len(sorted_list_stations)+1))

    index = 0
    for station, station_combined_score in zip(sorted_list_stations, sorted_list_station_scores_normalized):
        
        #get all the values for station (row in dataframe)
        station_values=df.loc[df['Station'] == station]
        
        station_values_list = [station_combined_score]
        
        #except combined score (not in the dataframe with computed values)
        for variable in variables[1:]:
            
            # in case of population, point source contirbution and anthropogenic contribution, want 
            # the value to be as low as possible. This should be reflected in the total score. Hence
            # the station with the lowest (for instance) anthropogenic contribution should have the highest score.
            # reverse that here: 
            list_reverse_values = ['Population','Point source contribution', 'Anthropogenic contribution']
            if variable in list_reverse_values:
                orig_value = station_values[variable].values[0]
                reversed_value = 100 - orig_value
                station_values_list.append(reversed_value)
            else:
                station_values_list.append(station_values[variable].values[0])
            color=matplotlib.colors.rgb2hex(cmap(index))     
            
        p.line(variables, station_values_list, name=station, line_width=1, color=color, legend_label=station)
        index = index + 1
        
    p.xaxis.major_label_orientation = "vertical"
    #Set title attributes:
    p.title.align = 'center'
    p.title.text_font_size = '13pt'
    p.title.offset = 15

    #Set label font style:
    p.xaxis.axis_label_text_font_style = 'normal'
    p.yaxis.axis_label_text_font_style = 'normal'
    p.xaxis.axis_label_standoff = 15 #Sets the distance of the label from the x-axis in screen units
    p.yaxis.axis_label_standoff = 15 #Sets the distance of the label from the y-axis in screen units

    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"

    #Set grid format:
    p.grid.grid_line_alpha = 0
    p.ygrid.band_fill_color = "olive"
    p.ygrid.band_fill_alpha = 0.1

    #Deactivate hover-tool, which is by default active:
    p.toolbar.active_inspect = None

    p.legend.location = "top_left"
    p.legend.click_policy="hide"

    show(p)
#also in stc_functions:
def normalized_dataframe(all_stations):

    df_2018 = pd.DataFrame(columns=['Station', 'Broad leaf forest','Coniferous forest','Mixed forest',\
                                    'Grass/shrubland','Cropland','Pasture','Urban', 'Ocean', 'Other', 'Unknown',
                                   'Sensitivity', 'Population', 'Point source contribution', 'Anthropogenic contribution'])

    #change paths later
    land_cover_2018=pd.read_csv(os.path.join('optimize_network','land_cover_2018.csv'))
    sens_pop_pointsouce_anthro = pd.read_csv(os.path.join('optimize_network','seasonal_table_values.csv'))

    index=0
    
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = stc.import_landcover_HILDA(year='2018')

    fp_pop= stc.import_population_data(year=2018)
    fp_point = stc.import_point_source_data()

    for station in all_stations:

        # get land cover data:
        if station in set(land_cover_2018.station):

            broad_leaf_forest_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'broad_leaf_forest'].iloc[0]
            coniferous_forest_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'coniferous_forest'].iloc[0]
            mixed_forest_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'mixed_forest'].iloc[0]
            ocean_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'ocean'].iloc[0]
            other_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'other'].iloc[0]
            grass_shrub_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'grass_shrub'].iloc[0] 
            cropland_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'cropland'].iloc[0]
            pasture_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'pasture'].iloc[0]
            urban_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'urban'].iloc[0] 
            unknown_station = land_cover_2018.loc[land_cover_2018['station'] == station, 'unknown'].iloc[0]

        else:

            date_range = pd.date_range(start='2018-01-01', end='2019-01-01', freq='3H')

            #not including midnight between dec 31 and jan 1
            date_range = date_range[:-1]

            nfp, fp_station, lon, lat, title = stc.read_aggreg_footprints(station, date_range)

            if fp_station is None:
                display(HTML('<p style="font-size:15px;">Not all footprints for ' + station + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to compute footprints for year 2018.</p>'))
                #continue
                break

            else:
                print('computing land cover values for ', station)

                broad_leaf_forest_station = (fp_station * broad_leaf_forest).sum()
                coniferous_forest_station = (fp_station * coniferous_forest).sum()
                mixed_forest_station = (fp_station * mixed_forest).sum()
                ocean_station = (fp_station * ocean).sum()
                other_station = (fp_station * other).sum()
                grass_shrub_station = (fp_station * grass_shrub).sum()
                cropland_station = (fp_station * cropland).sum()
                pasture_station = (fp_station * pasture).sum()
                urban_station = (fp_station * urban).sum()
                unknown_station = (fp_station * unknown).sum()

        # get the data for population, point sourcer contribution, anthropogenic contribution
        station_year = station + '_2018'
        if station_year in set(sens_pop_pointsouce_anthro.station_year):
            sens_station = sens_pop_pointsouce_anthro.loc[sens_pop_pointsouce_anthro['station_year'] == station_year, 'sens_whole'].iloc[0]
            pop_station = sens_pop_pointsouce_anthro.loc[sens_pop_pointsouce_anthro['station_year'] == station_year, 'pop_whole'].iloc[0]
            pointsource_station = sens_pop_pointsouce_anthro.loc[sens_pop_pointsouce_anthro['station_year'] == station_year, 'point_whole'].iloc[0]
            anthro_station = sens_pop_pointsouce_anthro.loc[sens_pop_pointsouce_anthro['station_year'] == station_year, 'anthro_whole'].iloc[0]
        else:

            date_range = pd.date_range(start='2018-01-01', end='2019-01-01', freq='3H')

            #not including midnight between dec 31 and jan 1
            date_range = date_range[:-1]

            nfp, fp_station, lon, lat, title = stc.read_aggreg_footprints(station, date_range)

            if fp_station is None:
                display(HTML('<p style="font-size:15px;">Not all footprints for ' + station + '. Use the <a href="https://stilt.icos-cp.eu/worker/" target="blank">STILT on demand calculator</a> to compute footprints for year 2018.</p>'))

                break

            else:
                
                print('computing values for ', station)

                sens_station = fp_station.sum()
                pop_station = (fp_station * fp_pop).sum()
                pointsource_station = (fp_station * fp_point).sum()

                #steps to get the modelled concentraion values of anthropogenic contributions
                timeselect_list=[0, 3, 6, 9, 12, 15, 18, 21]
                df_stilt_timeseries = stc.read_stilt_timeseries(station, date_range, timeselect_list)
                df_stilt_timeseries_mean = df_stilt_timeseries.mean()

                anthro_station = df_stilt_timeseries_mean['co2.industry']+df_stilt_timeseries_mean['co2.energy']+ \
                df_stilt_timeseries_mean['co2.transport']+ df_stilt_timeseries_mean['co2.others']


        df_2018.loc[index] = [station, broad_leaf_forest_station, coniferous_forest_station, \
                                  mixed_forest_station, grass_shrub_station, cropland_station, \
                                  pasture_station, urban_station, ocean_station, other_station, unknown_station,\
                                  sens_station, pop_station, pointsource_station, anthro_station]

        index = index + 1   


    #DONE GETTING ALL THE DATA: 
    #sensitivity is the first attribut (list_item[0]) in the each of the lists (one list per station)
    min_broad_leaf_forest=min(df_2018['Broad leaf forest'])
    range_broad_leaf_forest=max(df_2018['Broad leaf forest'])-min_broad_leaf_forest

    min_coniferous_forest=min(df_2018['Coniferous forest'])
    range_coniferous_forest=max(df_2018['Coniferous forest'])-min_coniferous_forest

    min_mixed_forest=min(df_2018['Mixed forest'])
    range_mixed_forest=max(df_2018['Mixed forest'])-min_mixed_forest

    min_grass_shrub=min(df_2018['Grass/shrubland'])
    range_grass_shrub=max(df_2018['Grass/shrubland'])-min_grass_shrub

    min_cropland=min(df_2018['Cropland'])
    range_cropland=max(df_2018['Cropland'])-min_cropland

    min_pasture=min(df_2018['Pasture'])
    range_pasture=max(df_2018['Pasture'])-min_pasture

    min_urban=min(df_2018['Urban'])
    range_urban=max(df_2018['Urban'])-min_urban

    min_ocean=min(df_2018['Ocean'])
    range_ocean=max(df_2018['Ocean'])-min_ocean
    
    min_other=min(df_2018['Other'])
    range_other=max(df_2018['Other'])-min_other

    min_unknown=min(df_2018['Unknown'])
    range_unknown=max(df_2018['Unknown'])-min_unknown

    min_sens=min(df_2018['Sensitivity'])
    range_sens=max(df_2018['Sensitivity'])-min_sens

    min_pop=min(df_2018['Population'])
    range_pop=max(df_2018['Population'])-min_pop

    min_point=min(df_2018['Point source contribution'])
    range_point=max(df_2018['Point source contribution'])-min_point

    min_anthro=min(df_2018['Anthropogenic contribution'])
    range_anthro=max(df_2018['Anthropogenic contribution'])-min_anthro


    df_saved_for_normalized=df_2018.copy()

    #for station in all_stations:   
    for station in df_saved_for_normalized['Station']:

        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Broad leaf forest', min_broad_leaf_forest, range_broad_leaf_forest)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Coniferous forest', min_coniferous_forest, range_coniferous_forest)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Mixed forest', min_mixed_forest, range_mixed_forest)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Grass/shrubland', min_grass_shrub, range_grass_shrub)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Cropland', min_cropland, range_cropland)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Pasture', min_pasture, range_pasture)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Urban', min_urban, range_urban)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Ocean', min_ocean, range_ocean)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Other', min_other, range_other)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Unknown', min_unknown, range_unknown)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Sensitivity', min_sens, range_sens)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Population', min_pop, range_pop)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Point source contribution', min_point, range_point)
        df_saved_for_normalized=stc.compute_normalized(df_saved_for_normalized, station, 'Anthropogenic contribution', min_anthro, range_anthro)
    return df_saved_for_normalized

def save_settings(settings, directory):
    
    now = datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S")

    output = os.path.join(os.path.expanduser('~'), 'output', directory, date_time)

    if not os.path.exists(output):
        os.makedirs(output)

    export_file=output + '/settings.json'

    # save settings as json file
    with open(export_file, 'w') as f:
        json.dump(settings, f, indent=4)