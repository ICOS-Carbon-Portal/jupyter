# Format read from https://peps.python.org/pep-0008/#imports.
# Standard library imports.
import calendar
import os
import re

# Related third party imports.
from IPython.core.display import display, HTML
from cyclebars import cyclebars, cyclebars_anomalies
from ipywidgets import interact, fixed, interact_manual
from matplotlib import pyplot as plt
import folium
import ipywidgets as widgets
import numpy as np
import pandas as pd

# Local application/library specific imports.


def temporal_scope_year_month_radio_buttons():
    return widgets.RadioButtons(
        options=['year', 'month'],
        value='year',
        description='Temporal scope',
        style= {'description_width': 'initial'},
        disabled=False
    )

def month_dropdown(description = 'Month: '):
    return widgets.Dropdown(
        options=[(month, number) for (month, number) in zip(list(calendar.month_name)[1:], range(1,13))],
        description=description,
        disabled=False
    )

def sd_checkbox():
    return widgets.Checkbox(
        value=True,
        description='include standard deviation bars',
        disabled=False,
        indent=False
    )

def make_plot_anomalies(df,
                        temporal_scope = 'year',
                        month = 1,
                        plot_with_sd = True,
                       ):

    single_plot = True if (selection_dict["values_b"] == None) else False
    same_variable = True if (selection_dict["variable_a_value"] == selection_dict["variable_b_value"]) else False

    reference_a = selection_dict["reference_values_a"]
    reference_a_std = selection_dict["sd_a"]
    reference_a_std_month = selection_dict["sd_a_month"]
    values_a = selection_dict["values_a"]
    agg_anom_columns = [values_a, reference_a, reference_a_std, reference_a_std_month]

    if not single_plot:
        reference_b = selection_dict["reference_values_b"]
        reference_b_std = selection_dict["sd_b"]
        reference_b_std_month = selection_dict["sd_b_month"]
        values_b = selection_dict["values_b"]
        agg_anom_columns.extend([values_b, reference_b, reference_b_std, reference_b_std_month])

    ### aggregate according to scope
    if temporal_scope == 'year':

        # column with the standard deviation values based on the difference in the monthly mean values
        reference_a_std_scope_specific = reference_a_std_month
        if 'reference_b_std' in locals():
            reference_b_std_scope_specific = reference_b_std_month

        d_agg_anom_mean = {col: 'mean' for col in agg_anom_columns}

        df = df.groupby(['month']).agg(d_agg_anom_mean).reset_index()

        bintype = 'month'

        if selection_dict["selected_site_b"] is not None:
            if same_variable:
                legendTitle = 'Mean monthly ' + selection_dict["variable_a_value"]  + ' at '+\
                    selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')' + ' (left, top) & ' + selection_dict["variable_b_value"] + ' at ' +\
                    selection_dict["selected_site_b_name"] + ' (' + str(selection_dict["year_b"]) + ')' + ' (right, bottom)'
            else:
                legendTitle_a = 'Mean monthly ' + selection_dict["variable_a_value"]  + ' at '+\
                    selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')'
                legendTitle_b = 'Mean monthly ' + selection_dict["variable_b_value"] + ' at ' +\
                    selection_dict["selected_site_b_name"] + ' (' + str(selection_dict["year_b"]) + ')'

        else:
            legendTitle = 'Mean monthly ' + selection_dict["variable_a_value"] + ' at ' +\
                selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')'
        time_unit = 'month(s)'

    elif temporal_scope == 'month':

        # column with the standard deviation values based on the difference in the monthly mean values
        reference_a_std_scope_specific = reference_a_std
        if 'reference_b_std' in locals():
            reference_b_std_scope_specific = reference_b_std

        df = df[df.month == month]
        # does not change anything as already daily values (would be needed if we had multiple values for different times of the day though).
        d_agg_anom = {col: 'mean' for col in agg_anom_columns}
        df = df.groupby(['day']).agg(d_agg_anom).reset_index()

        # check if all zeros in any of the columns (fails if so with error: "ValueError: 'vertices' must be 2D with shape (M, 2). Your input has shape (0,)." 
        # The error was discovered for Hainich Jan 2018. It happens here: posAnomalyAngle = radians((totalPositiveAnomaly/totalValues)*180)
        for df_column in df.columns:
            if df[df_column].sum() == 0:
                return display(HTML('<p style="font-size:16px">0 for all days in the selected month</p>'))

        bintype = 'day'
        if selection_dict["selected_site_b"] is not None:
            if same_variable:
                legendTitle = 'Mean daily ' + selection_dict["variable_a_value"] + ' for ' + calendar.month_name[month] + ' at ' +\
                    selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')' + ' (left, top) & ' + selection_dict["variable_b_value"] + ' at ' +\
                    selection_dict["selected_site_b_name"] + ' (' + str(selection_dict["year_b"]) + ')' + ' (right, bottom)'
            else:
                legendTitle_a = 'Mean daily ' + selection_dict["variable_a_value"] + ' for ' + calendar.month_name[month] + ' at ' +\
                    selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')'
                legendTitle_b = 'Mean daily ' + selection_dict["variable_b_value"] + ' at ' +\
                    selection_dict["selected_site_b_name"] + ' (' + str(selection_dict["year_b"]) + ')'

        else:
            legendTitle = 'Mean daily ' + selection_dict["variable_a_value"] + ' for ' + calendar.month_name[month] + ' at ' +\
                selection_dict["selected_site_a_name"] + ' (' + str(selection_dict["year_a"]) + ')'
        time_unit = 'day(s)'
    else:
        return 'Choose a temporal scope!'

    if single_plot:
        output = cyclebars_anomalies(
            data = df,
            labels = bintype,
            values_a = values_a,
            reference_values_a = reference_a,
            reference_standard_deviation_a = reference_a_std_scope_specific if plot_with_sd else None,
            middle_labels = True,
            color_positive_anomalies = colors_positive_anomalies[selection_dict["variable_a_value"]],
            color_negative_anomalies = colors_negative_anomalies[selection_dict["variable_a_value"]],
            color_standard_deviation = '#4D4D4D',
            plot_legends=False,
            pie_offset=0,
        )
    else:
        if same_variable:
            output = cyclebars_anomalies(
                data = df,
                labels = bintype,
                values_a = values_a,
                reference_values_a = reference_a,
                reference_standard_deviation_a = reference_a_std_scope_specific if plot_with_sd else None,
                values_b = values_b,
                reference_values_b = reference_b,
                reference_standard_deviation_b = reference_b_std_scope_specific if plot_with_sd else None,
                middle_labels = True,
                color_positive_anomalies = colors_positive_anomalies[selection_dict["variable_a_value"]],
                color_negative_anomalies = colors_negative_anomalies[selection_dict["variable_a_value"]],
                color_standard_deviation = '#4D4D4D',
                plot_legends=False,
                pie_offset=0,
            )
        else:
            output_a = cyclebars_anomalies(
                data = df,
                labels = bintype,
                values_a = values_a,
                reference_values_a = reference_a,
                reference_standard_deviation_a = reference_a_std_scope_specific if plot_with_sd else None,
                middle_labels = True,
                color_positive_anomalies = colors_positive_anomalies[selection_dict["variable_a_value"]],
                color_negative_anomalies = colors_negative_anomalies[selection_dict["variable_a_value"]],
                color_standard_deviation = '#4D4D4D',
                plot_legends=False,
                pie_offset=0,
            )
            output_b = cyclebars_anomalies(
                data = df,
                labels = bintype,
                values_a = values_b,
                reference_values_a = reference_b,
                reference_standard_deviation_a = reference_b_std_scope_specific if plot_with_sd else None,
                middle_labels = True,
                color_positive_anomalies = colors_positive_anomalies[selection_dict["variable_b_value"]],
                color_negative_anomalies = colors_negative_anomalies[selection_dict["variable_b_value"]],
                color_standard_deviation = '#4D4D4D',
                plot_legends=False,
                pie_offset=0,
            )

    if single_plot:
        ### legend for single plot
        mean_values_a = np.round(df[values_a].mean(),2)
        mean_ref_a = np.round(df[reference_a].mean(),2)
        anomalies_a = df[values_a]-df[reference_a]
        positive_anomalies_a = []
        negative_anomalies_a = []
        for a in anomalies_a:
            if a>0:
                positive_anomalies_a.append(a)
            elif a<0:
                negative_anomalies_a.append(-a)
        mean_positive_anomalies_a = np.round(np.mean(positive_anomalies_a),2) if positive_anomalies_a else '-'
        mean_negative_anomalies_a = np.round(np.mean(negative_anomalies_a),2) if negative_anomalies_a else '-'
        means_a = [mean_values_a, mean_ref_a, mean_positive_anomalies_a, mean_negative_anomalies_a]

        labels_a = [' (' + str(selection_dict["year_a"]) + ')',
                    ' (' + selection_dict["reference"] + ')',
                    ' average positive anomaly (' + str(len(positive_anomalies_a)) + ' ' + time_unit + ')',
                    ' average negative anomaly (' + str(len(negative_anomalies_a)) + ' ' + time_unit + ')']


        colors = ['#BFBFBF','#BFBFBF',colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]
        edgecolors = [colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]*2

        legendLabels = [str(mean) + label for (label, mean) in zip(labels_a, means_a)]
        patches = [plt.Rectangle((0,0),1,1, facecolor=(colors+colors)[i], edgecolor=(edgecolors+edgecolors)[i], linewidth=4) for i in range(4)]
        output[0].legend(
            patches, legendLabels,
            title=legendTitle,
            title_fontsize=16,
            fontsize=15,
            loc='lower center',
            ncols=4
        )
    else:
        if same_variable:
            ### legend for double plot
            mean_values_a = np.round(df[values_a].mean(),2)
            mean_values_b = np.round(df[values_b].mean(),2)
            mean_ref_a = np.round(df[reference_a].mean(),2)
            mean_ref_b = np.round(df[reference_b].mean(),2)

            anomalies_a = df[values_a]-df[reference_a]
            positive_anomalies_a = []
            negative_anomalies_a = []
            for a in anomalies_a:
                if a>0:
                    positive_anomalies_a.append(a)
                elif a<0:
                    negative_anomalies_a.append(-a)
            mean_positive_anomalies_a = np.round(np.mean(positive_anomalies_a),2) if positive_anomalies_a else '-'
            mean_negative_anomalies_a = np.round(np.mean(negative_anomalies_a),2) if negative_anomalies_a else '-'

            anomalies_b = df[values_b]-df[reference_b]
            positive_anomalies_b = []
            negative_anomalies_b = []
            for a in anomalies_b:
                if a>0:
                    positive_anomalies_b.append(a)
                elif a<0:
                    negative_anomalies_b.append(-a)
            mean_positive_anomalies_b = np.round(np.mean(positive_anomalies_b),2) if positive_anomalies_b else '-'
            mean_negative_anomalies_b = np.round(np.mean(negative_anomalies_b),2) if negative_anomalies_b else '-'

            means_a = [mean_values_a, mean_ref_a, mean_positive_anomalies_a, mean_negative_anomalies_a]
            means_b = [mean_values_b, mean_ref_b, mean_positive_anomalies_b, mean_negative_anomalies_b]

            labels_a = [' (' + str(selection_dict["year_a"]) + ')',
                        ' (' + selection_dict["reference"] + ')',
                        ' average positive anomaly (' + str(len(positive_anomalies_a)) + ' ' + time_unit + ')',
                        ' average negative anomaly (' + str(len(negative_anomalies_a)) + ' ' + time_unit + ')']

            labels_b = [' (' + str(selection_dict["year_b"]) + ')',
                        ' (' + selection_dict["reference"] + ')',
                        ' average positive anomaly (' + str(len(positive_anomalies_b)) + ' ' + time_unit + ')',
                        ' average negative anomaly (' + str(len(negative_anomalies_b)) + ' ' + time_unit + ')']

            edgecolors = [colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]*2
            colors = ['#BFBFBF','#BFBFBF',colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]

            legendLabels = [str(mean) + label for (label, mean) in zip(labels_a+labels_b, means_a+means_b)]
            patches = [plt.Rectangle((0,0),1,1, facecolor=(colors+colors)[i], edgecolor=(edgecolors+edgecolors)[i], linewidth=4) for i in range(8)]
            output[0].legend(
                patches, legendLabels,
                title=legendTitle,
                title_fontsize=16,
                fontsize=15,
                loc='center',
                bbox_to_anchor=(0.5,0.49),
                ncols=4)
        else:
            ### legend for plot a
            mean_values_a = np.round(df[values_a].mean(),2)
            mean_ref_a = np.round(df[reference_a].mean(),2)
            anomalies_a = df[values_a]-df[reference_a]
            positive_anomalies_a = []
            negative_anomalies_a = []
            for a in anomalies_a:
                if a>0:
                    positive_anomalies_a.append(a)
                elif a<0:
                    negative_anomalies_a.append(-a)
            mean_positive_anomalies_a = np.round(np.mean(positive_anomalies_a),2) if positive_anomalies_a else '-'
            mean_negative_anomalies_a = np.round(np.mean(negative_anomalies_a),2) if negative_anomalies_a else '-'
            means_a = [mean_values_a, mean_ref_a, mean_positive_anomalies_a, mean_negative_anomalies_a]

            labels_a = [' (' + str(selection_dict["year_a"]) + ')',
                        ' (' + selection_dict["reference"] + ')',
                        ' average positive anomaly (' + str(len(positive_anomalies_a)) + ' ' + time_unit + ')',
                        ' average negative anomaly (' + str(len(negative_anomalies_a)) + ' ' + time_unit + ')']

            colors = ['#BFBFBF','#BFBFBF',colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]
            edgecolors = [colors_positive_anomalies[selection_dict["variable_a_value"]], colors_negative_anomalies[selection_dict["variable_a_value"]]]*2

            legendLabels = [str(mean) + label for (label, mean) in zip(labels_a, means_a)]
            patches = [plt.Rectangle((0,0),1,1, facecolor=(colors+colors)[i], edgecolor=(edgecolors+edgecolors)[i], linewidth=4) for i in range(4)]
            output_a[0].legend(
                patches, legendLabels,
                title=legendTitle_a,
                title_fontsize=16,
                fontsize=15,
                loc='lower center',
                ncols=4
            )
            ### legend for plot b
            mean_values_b = np.round(df[values_b].mean(),2)
            mean_ref_b = np.round(df[reference_b].mean(),2)
            anomalies_b = df[values_b]-df[reference_b]
            positive_anomalies_b = []
            negative_anomalies_b = []
            for a in anomalies_b:
                if a>0:
                    positive_anomalies_b.append(a)
                elif a<0:
                    negative_anomalies_b.append(-a)
            mean_positive_anomalies_b = np.round(np.mean(positive_anomalies_b),2) if positive_anomalies_b else '-'
            mean_negative_anomalies_b = np.round(np.mean(negative_anomalies_b),2) if negative_anomalies_b else '-'
            means_b = [mean_values_b, mean_ref_b, mean_positive_anomalies_b, mean_negative_anomalies_b]

            labels_b = [' (' + str(selection_dict["year_b"]) + ')',
                        ' (' + selection_dict["reference"] + ')',
                        ' average positive anomaly (' + str(len(positive_anomalies_b)) + ' ' + time_unit + ')',
                        ' average negative anomaly (' + str(len(negative_anomalies_b)) + ' ' + time_unit + ')']


            colors = ['#BFBFBF','#BFBFBF',colors_positive_anomalies[selection_dict["variable_b_value"]], colors_negative_anomalies[selection_dict["variable_b_value"]]]
            edgecolors = [colors_positive_anomalies[selection_dict["variable_b_value"]], colors_negative_anomalies[selection_dict["variable_b_value"]]]*2


            legendLabels = [str(mean) + label for (label, mean) in zip(labels_b, means_b)]
            patches = [plt.Rectangle((0,0),1,1, facecolor=(colors+colors)[i], edgecolor=(edgecolors+edgecolors)[i], linewidth=4) for i in range(4)]
            output_b[0].legend(
                patches, legendLabels,
                title=legendTitle_b,
                title_fontsize=16,
                fontsize=15,
                loc='lower center',
                ncols=4
            )

    output_path = os.path.join(os.path.expanduser('~'), 'output')
    output_anomalies_path = os.path.join(
        output_path,
        'ecosystem_site_anomaly_visualization_output'
    )
    relative_anomalies_path = \
        f'../../{re.search("output.*", output_anomalies_path)[0]}'
    # download files
    #if same_variable:
    if not 'legendTitle_a' in locals():
        # create a name for the save file based on the title. Must do this to link to the file for download.
        replacements = {' ': '_', '(': '_', ')': '_', '&':'_', ',': '_'}
        replaced_chars = [replacements.get(char, char) for char in legendTitle+'wrt_'+selection_dict["reference"]]
        name_save = ''.join(replaced_chars)
        name_save = name_save.replace("__", "_")

        file_path = f'{output_anomalies_path}/{name_save}.png'
        relative_file_path = f'{relative_anomalies_path}/{name_save}.png'
        output[0].savefig(file_path)

        if os.path.exists(file_path):
            html_string = '<br>Access figure <a href=' + relative_file_path + ' target="_blank">here</a>.<br>'
            display(HTML('<p style="font-size:16px">' + html_string))

    else:

        replacements = {' ': '_', '(': '_', ')': '_', '&':'_', ',': '_'}
        replaced_chars = [replacements.get(char, char) for char in legendTitle_a+'wrt_'+selection_dict["reference"]]
        name_save = ''.join(replaced_chars)
        name_save = name_save.replace("__", "_")

        file_path = f'{output_anomalies_path}/{name_save}.png'
        relative_file_path = f'{relative_anomalies_path}/{name_save}.png'
        output_a[0].savefig(file_path)

        if os.path.exists(file_path):
            html_string = '<br>Access figure for site a <a href=' + relative_file_path + ' target="_blank">here</a>.'
            display(HTML('<p style="font-size:16px">' +  html_string))

        # two different figures output, here is site b:
        replacements = {' ': '_', '(': '_', ')': '_', '&':'_', ',': '_'}
        replaced_chars = [replacements.get(char, char) for char in legendTitle_b+'wrt_'+selection_dict["reference"]]
        name_save = ''.join(replaced_chars)
        name_save = name_save.replace("__", "_")

        file_path = f'{output_anomalies_path}/{name_save}.png'
        relative_file_path = f'{relative_anomalies_path}/{name_save}.png'
        output_b[0].savefig(file_path)

        if os.path.exists(file_path):
            html_string = '<br>Access figure for site a <a href=' + relative_file_path + ' target="_blank">here</a>.'
            display(HTML('<p style="font-size:16px">' +  html_string))

    # link to the csv-file (already saved in gui_anomaly)
    file_path = data_filename
    relative_file_path = \
        f'../../{re.search("output.*", file_path)[0]}'
    if os.path.exists(file_path):
        html_string = 'Access the data used to create the figure(s) <a href=' + relative_file_path + ' target="_blank">here</a>.<br>'
        display(HTML('<p style="font-size:16px">' + html_string))

def interact_with_make_plot_anomalies(scope, df):
    if scope == 'year':
        interact_manual(
            make_plot_anomalies,
            df = fixed(df),
            temporal_scope = fixed('year'),
            month = fixed(0),
            plot_with_sd = sd_checkbox(),
        )
    elif scope == 'month':
        interact_manual(
            make_plot_anomalies,
            df = fixed(df),
            temporal_scope = fixed('month'),
            plot_with_sd = sd_checkbox(),
            month = month_dropdown()
        )

def plot_anomalies(df, filename, dictionary, colors_positive_anomalies_dict,colors_negative_anomalies_dict): # add plot_with_sd
    global selection_dict
    selection_dict = dictionary
    global colors_positive_anomalies
    colors_positive_anomalies = colors_positive_anomalies_dict
    global colors_negative_anomalies
    colors_negative_anomalies = colors_negative_anomalies_dict
    global data_filename
    data_filename = filename

    interact(
        interact_with_make_plot_anomalies,
        scope = temporal_scope_year_month_radio_buttons(),
        df = fixed(df)
    )

def map_of_sites(df_shortterm=pd.DataFrame, df_longterm=pd.DataFrame):
    m = folium.Map()
    light_tiles = folium.TileLayer(
        tiles='CartoDB positron',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        max_zoom=19,
        name='cartodbpositron',
        overlay = False,
        control=True,
    )
    m = folium.Map(tiles='CartoDB positron')
    dark_tiles = folium.TileLayer(
        tiles='CartoDB dark_matter',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        max_zoom=19,
        name='cartodbdarkmatter',
        overlay = False,
        control=True
    ).add_to(m)
    satellite_tiles = folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False,
        control = True
    ).add_to(m)

    short_term_sites = folium.FeatureGroup('sites 2010-2020')
    for i, site in df_shortterm.iterrows():
        folium.CircleMarker(
            [site.lat, site.lon],
            tooltip = site.id,
            popup = site['name'] + ', (' + site.country + '), 2010-2020, <a href="' + site.uri + '" target="_blank">Data Landing Page</a>',
            fill_color = 'orange', fill_opacity=0.8, weight=1, color='#fff', radius=8
        ).add_to(short_term_sites)
    long_term_sites = folium.FeatureGroup('sites 2000-2020')
    for i, site in df_longterm.iterrows():
        folium.CircleMarker(
            [site.lat, site.lon],
            tooltip = site.id,
            popup = site['name'] + ', (' + site.country + '), 2000-2020, <a href="' + site.uri + '" target="_blank">Data Landing Page</a>',
            fill_color = 'magenta', fill_opacity=0.6, weight=1, color='#fff', radius=8
        ).add_to(long_term_sites)
    short_term_sites.add_to(m)
    long_term_sites.add_to(m)

    southwest_corner = [min(float(df_shortterm.lat.min()), float(df_longterm.lat.min())), min(float(df_shortterm.lon.min()), float(df_longterm.lon.min()))]
    northeast_corner = [max(float(df_shortterm.lat.max()), float(df_longterm.lat.max())), max(float(df_shortterm.lon.max()), float(df_longterm.lon.max()))]
    bounding_box = [southwest_corner, northeast_corner]
    m.fit_bounds(bounding_box)
    folium.LayerControl().add_to(m)
    return m