# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 08:38:51 2020

@author: Claudio and Ida
"""

from ipywidgets import Dropdown, SelectMultiple, FileUpload, HBox, Text, VBox, \
    Button, Output, IntText, RadioButtons, IntProgress, GridspecLayout
from IPython.core.display import display, HTML
import settings
from icoscp.station import station as cpstation
import stationchar
import stc_functions
import os
import re
from datetime import datetime
import json
from icoscp.stilt import stiltstation
import ipywidgets as widgets
from matplotlib import pyplot as plt

button_color_able = '#4169E1'
button_color_disable = '#900D09'
output_path = os.path.join(os.path.expanduser('~'), 'output')
output_stc_path = os.path.join(
    output_path, 'station-characterization'
)
relative_stc_path = \
    f'../../{re.search("output.*", output_stc_path)[0]}'
# style to supress scrolling in the output
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

# access all stations with stiltruns (see in viewer here: https://stilt.icos-cp.eu/viewer/)
stiltstations = stiltstation.find()

# access the station information for the widgets, one list with all stations (list_all) and one limited to the ICOS labeled stations (list_all_icos)
list_all_located = sorted(
    [((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' (' + k + ')'), k)
     for k, v in stiltstations.items() if v['geoinfo']])
list_all_not_located = [(('In water' + ': ' + v['name'] + ' (' + k + ')'), k)
                        for k, v in stiltstations.items() if not v['geoinfo']]
list_all = list_all_not_located + list_all_located

list_all_icos_located = sorted(
    [((v['geoinfo']['name']['common'] + ': ' + v['name'] + ' (' + k + ')'), k)
     for k, v in stiltstations.items() if v['geoinfo'] if v['icos']])
list_all_icos_not_located = [
    (('In water' + ': ' + v['name'] + ' (' + k + ')'), k) for k, v in
    stiltstations.items() if not v['geoinfo'] if v['icos']]
list_all_icos = list_all_icos_not_located + list_all_icos_located


# read or set the parameters from the widgets
def get_settings():
    s = settings.getDict()
    try:
        s['stationCode'] = station_choice.value
        if stiltstations[s['stationCode']]['icos']:
            s['icos'] = cpstation.get(s['stationCode'][0:3].upper()).info()
        s['stilt'] = stiltstations[s['stationCode']]
        s['startYear'] = s_year.value
        s['startMonth'] = s_month.value
        s['startDay'] = s_day.value
        s['endYear'] = e_year.value
        s['endMonth'] = e_month.value
        s['endDay'] = e_day.value
        s['timeOfDay'] = time_selection.value
        s['binSize'] = bin_size.value
        s['binInterval'] = interval.value
        s['unit'] = unit_value.value
        s['labelPolar'] = landcover_windrose_label.value
        s['saveFigs'] = save_figs.value
        s['figFormat'] = fig_format.value

    except:
        return

    return s


# read or set the parameters from an uploaded file
def set_settings(s):
    if s['stationCode'] in list_all_icos:
        station_type.value = 'ICOS stations'
        station_choice.options = list_all_icos
        station_choice.value = s['stationCode']
    else:
        station_type.value = 'STILT stations'
        station_choice.options = list_all
        station_choice.value = s['stationCode']

    s_year.value = s['startYear']
    s_month.value = s['startMonth']
    s_day.value = s['startDay']
    e_year.value = s['endYear']
    e_month.value = s['endMonth']
    e_day.value = s['endDay']
    time_selection.value = s['timeOfDay']
    bin_size.value = s['binSize']
    interval.value = s['binInterval']
    unit_value.value = s['unit']
    landcover_windrose_label.value = s['labelPolar']
    save_figs.value = s['saveFigs']
    try:
        fig_format.value = s['figFormat']
    except:
        fig_format.value = 'pdf'


# check if it is a valid date range, enable/disable update button in accordance.
def check_date_range():
    if s_year.value == e_year.value and s_month.value == e_month.value and e_day.value == s_day.value:
        update_button.disabled = True
    else:
        update_button.disabled = False


# observer functions: things that happen when specific widgets changes
# ---------------------------------------------------------
def change_stn_type(c):
    # disable update button until date and time defined (see how these are reset below)
    update_button.disabled = True
    update_button.tooltip = 'Unable to run'
    update_button.style.button_color = button_color_disable

    # make sure the new 'options' are not selected..
    unobserve()
    if station_type.value == 'STILT stations':
        station_choice.options = list_all
    else:
        station_choice.options = list_all_icos

    station_choice.value = None

    # reset the data fields
    s_year.options = []
    e_year.options = []
    s_month.options = []
    e_month.options = []
    s_day.options = []
    e_day.options = []

    # make sure future changes are observed again
    observe()


def change_stn(c):
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'
    update_button.style.button_color = button_color_able

    years = sorted(stiltstations[station_choice.value]['years'])
    years = [int(x) for x in years]

    s_year.options = years
    s_year.value = min(years)
    e_year.options = years
    e_year.value = min(years)

    # triggers "change_yr" --> pupulates the month widgets based on STILT footprint availability


def change_yr(c):
    years = [x for x in s_year.options if x >= s_year.value]
    # extract available months
    month = sorted(
        stiltstations[station_choice.value][str(s_year.value)]['months'])
    month = [int(x) for x in month]
    s_month.options = month
    s_month.value = min(month)
    e_year.options = years
    e_month.options = month
    e_month.value = min(month)
    check_date_range()


def change_mt(c):
    # the day widget populated depending on what month it is (different number of days)
    month_days_30 = [4, 6, 9, 11]
    month_days_31 = [1, 3, 5, 7, 8, 10, 12]

    if s_month.value in month_days_31:
        s_day.options = list(range(1, 32))

    elif s_month.value in month_days_30:
        s_day.options = list(range(1, 31))
    else:
        s_day.options = list(range(1, 29))

    s_day.value = 1

    # when change start_month - change end day also (if same year and month OR the first time)
    if s_year.value == e_year.value and s_month.value > e_month.value:
        month = [int(x) for x in s_month.options if x >= s_month.value]
        e_month.options = month
        e_month.value = min(month)

        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options = day
        e_day.value = min(day)

    check_date_range()


def change_yr_end(c):
    if s_year.value == e_year.value:
        month = [x for x in s_month.options if x >= s_month.value]
        e_month.options = month
        e_month.value = min(month)
    else:
        # if different from start year, all months are up for choice!
        month = sorted(
            stiltstations[station_choice.value][str(e_year.value)]['months'])
        month = [int(x) for x in month]
        e_month.options = month
        e_month.value = min(month)

    if s_year.value == e_year.value and e_month.value == s_month.value:
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options = day
        e_day.value = min(day)
    else:
        month_days_30 = [4, 6, 9, 11]
        month_days_31 = [1, 3, 5, 7, 8, 10, 12]

        if e_month.value in month_days_31:
            e_day.options = list(range(1, 32))

        elif e_month.value in month_days_30:
            e_day.options = list(range(1, 31))

        else:
            e_day.options = list(range(1, 29))

        e_day.value = 1
    check_date_range()


def change_day(c):
    # when change the day... if the same month and year (start) - update
    if s_year.value == e_year.value and s_month.value == e_month.value:
        original_value = e_day.value
        allowed_days = [int(x) for x in s_day.options if x >= s_day.value]
        e_day.options = allowed_days

        if original_value in allowed_days:
            e_day.value = original_value
        else:
            e_day.value = min(allowed_days)
    check_date_range()


def change_month_end(c):
    if s_year.value == e_year.value and e_month.value == s_month.value:
        day = [x for x in s_day.options if x >= s_day.value]
        e_day.options = day
        e_day.value = min(day)
    else:
        month_days_30 = [4, 6, 9, 11]
        month_days_31 = [1, 3, 5, 7, 8, 10, 12]

        if e_month.value in month_days_31:
            e_day.options = list(range(1, 32))

        elif e_month.value in month_days_30:
            e_day.options = list(range(1, 31))

        else:
            e_day.options = list(range(1, 29))
        e_day.value = 1
    check_date_range()


def change_day_end(c):
    check_date_range()


def file_set_widgets(c):
    uploaded_file = file_name.value

    # If the content of the file is loaded as a dictionary or tuple
    # depends on the version of ipywidgets.
    # Case of Dictionary.
    if isinstance(uploaded_file, dict):
        settings_content = uploaded_file[list(uploaded_file.keys())[0]][
            'content']
    # Case of Tuple.
    else:
        settings_content = uploaded_file[0]['content'].tobytes()
    settings_dict = json.loads(settings_content)
    set_settings(settings_dict)


# ----------- start processing -----------------

def updateProgress(f, desc=''):
    # custom progressbar updates
    f.value += 1
    if not desc:
        f.description = 'step ' + str(f.value) + '/' + str(f.max)
    else:
        f.description = str(desc)


def update_func(button_c):
    # Define update function
    # This starts the process of creating the graphs
    # and, depending on the parameters, saving figures and pdf

    progress_bar.clear_output()
    header_no_footprints.clear_output()
    header_output.clear_output()
    result_sensitivity.clear_output()
    result_population.clear_output()
    result_pointsource.clear_output()
    result_land_cover_bar_graph.clear_output()
    result_seasonal_table.clear_output()
    header_advanced.clear_output()
    result_landcover_windrose.clear_output()
    result_multiple_variables_graph.clear_output()
    header_download.clear_output()

    update_button.disabled = True
    update_button.tooltip = 'Unable to run'
    update_button.style.button_color = button_color_disable

    with progress_bar:
        f = IntProgress(min=0, max=10, style=style)
        display(f)
        updateProgress(f, 'read footprint')

    # create a station characterization object with everything needed to create the output
    # the object will depend on the settings specified using the widgets (get_settings())
    global stc
    stc = stationchar.StationChar(get_settings())

    if stc.fp is None:

        with header_no_footprints:
            display(HTML(
                '<p style="font-size:16px">No footprints for selected date range.</p>'))
            f.value = 10
    else:

        # create an output folder (saved to the station characterization object) in case of the selection is made to save the figures.
        if stc.settings['saveFigs'] == 'yes':
            now = datetime.now()
            stc.settings['date/time generated'] = now.strftime(
                "%Y%m%d_%H%M%S_")

            output = os.path.join(
                output_stc_path,
                f'{stc.settings["date/time generated"]}{stc.stationId}'
            )
            if not os.path.exists(output):
                os.makedirs(output)

            stc.settings['output_folder'] = output

        # some first output from the tool related to selections made and properties of the selected station
        with header_output:
            degree_sign = u'\N{DEGREE SIGN}'
            station_name = stc.stationName
            station_code = stc.settings['stationCode']
            station_country = stc.country
            station_lat = stc.lat
            station_lon = stc.lon

            maps_bin_size = stc.settings['binSize']
            maps_bin_interval = stc.settings['binInterval']

            date_and_time_string = stc_functions.date_and_time_string_for_title(
                stc.dateRange, stc.settings['timeOfDay'])

            if 'icos' in stc.settings:
                station_class = stc.stationClass
                station_site_type = stc.siteType
                model_height = stc.settings['stilt']['alt']

                if stc.settings['icos']['siteType'] == 'mountain' or \
                        stc.settings['icos']['siteType'] == 'Mountain':
                    mountain_string = ' (might be different from station intake height since mountain station).'
                else:
                    mountain_string = '.'

                if station_site_type is not None:
                    display(HTML(
                        '<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                        ' station characterisation</p><p style="font-size:18px;"><br>' + station_name + ' (' + station_code + \
                        ') is a class ' + str(
                            station_class) + ' ICOS atmospheric station of the type ' + station_site_type.lower() + \
                        ' located in ' + station_country + ' (latitude: ' + str(
                            "%.2f" % station_lat) + \
                        degree_sign + 'N, ' + 'longitude: ' + str(
                            "%.2f" % station_lon) + \
                        degree_sign + 'E). The model height is ' + str(
                            model_height) + ' meters above ground' + mountain_string + '<br></p>'))
                else:
                    display(HTML(
                        '<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                        ' station characterisation</p><p style="font-size:18px;"><br>' + station_name + ' (' + station_code + \
                        ') is a class ' + str(
                            station_class) + ' ICOS atmospheric station (undefined station type) ' + \
                        ' located in ' + station_country + ' (latitude: ' + str(
                            "%.2f" % station_lat) + \
                        degree_sign + 'N, ' + 'longitude: ' + str(
                            "%.2f" % station_lon) + \
                        degree_sign + 'E). The model height is ' + str(
                            model_height) + ' meters above ground' + mountain_string + '<br></p>'))

            else:

                display(HTML(
                    '<p style="font-size:35px;font-weight:bold;"><br>' + station_name + \
                    ' station characterisation</p><p style="font-size:16px;">' + station_name + ' (' + station_code + \
                    ') is located in ' + station_country + ' (latitude: ' + str(
                        "%.2f" % station_lat) + \
                    degree_sign + 'N, ' + 'longitude: ' + str(
                        "%.2f" % station_lon) + degree_sign + 'E).<br></p>'))

            # added information that is redundant in the titles
            display(HTML(
                '<p style="font-size:18px;">Date range: ' + date_and_time_string + '<br></p>'))
            display(HTML('<p style="font-size:18px;">The map bins are ' + str(
                maps_bin_size) + ' degrees at ' + \
                         str(maps_bin_interval) + ' km increments</p>'))

        updateProgress(f, 'calculate sensitivity')
        with result_sensitivity:
            fig, caption = stc_functions.polar_graph(stc, 'sensitivity')
            stc.add_figure(1, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        updateProgress(f, 'process pointsource')
        with result_pointsource:
            fig, caption = stc_functions.polar_graph(stc,
                                                     'point source contribution',
                                                     colorbar='Purples')
            stc.add_figure(2, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        updateProgress(f, 'process population')
        with result_population:
            fig, caption = stc_functions.polar_graph(stc,
                                                     'population sensitivity',
                                                     colorbar='Greens')
            stc.add_figure(3, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        updateProgress(f, 'get landcover')
        with result_land_cover_bar_graph:
            fig, caption = stc_functions.land_cover_bar_graph(stc)
            stc.add_figure(4, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        updateProgress(f, 'seasonal table')
        with result_seasonal_table:
            fig, caption = stc_functions.seasonal_table(stc)
            stc.add_figure(5, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))

            # a seasonal table is not always created (requires the full year of footprints)
            try:
                display(fig)
                plt.close(fig)
            except:
                pass

        with header_advanced:
            display(HTML('<h2>Advanced figures</h2><br><p style="font-size:16px">\
                Please read the <a href="./station_characterization/specifications.pdf" target="_blank">\
                    specifications document</a> before attempting to interpret the following figures.</p>'))

        updateProgress(f, 'landcover windrose')
        with result_landcover_windrose:
            fig, caption = stc_functions.land_cover_polar_graph(stc)
            stc.add_figure(6, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        updateProgress(f, 'multiple variables')
        with result_multiple_variables_graph:
            fig, caption = stc_functions.multiple_variables_graph(stc)
            stc.add_figure(7, fig, caption)
            display(HTML(
                '<p style="font-size:16px;text-align:left;text-indent: 20px">' + caption + ' </p>'))
            display(fig)
            plt.close(fig)

        # make it possible to download all the content (including the final station characterization document) directly in the tool
        if stc.settings['saveFigs'] == 'yes':
            updateProgress(f, 'saving')
            fmt = fig_format.value
            stc_functions.save(stc, fmt)

            # create a html string for the download. Only links to files and documents that exist (for instance, if there is not footprints for the full year, the seasonal table will not be created.
            file_folder = stc.settings['output_folder'].split('/')[-1]

            pdf_file_name = stc.settings['date/time generated'] + stc.stationId + '.pdf'
            
            #os.path.join(stc.settings['output_folder'], (stc.settings['date/time generated']+stc.stationId+'.tex'))
            #pdf_file_path = os.path.join(stc.settings['output_folder'], (stc.settings['date/time generated']+stc.stationId+'.pdf'))
            pdf_file_path = f'{output_stc_path}/{file_folder}/{pdf_file_name}'
            
            pdf_file_path_relative = f'{relative_stc_path}/{file_folder}/{pdf_file_name}'
            
            print(pdf_file_path)
            
            if os.path.exists(pdf_file_path):

                html_string_pdf = '<h2>Download</h2><br>Full station characterization document:<br><a href=' + pdf_file_path_relative + ' target="_blank">' + pdf_file_name + '</a><br><br>Individual figures:<br>'

            else:

                html_string_pdf = '<h2>Download</h2><br><br>Individual figures:<br>'

            list_individual_figures = ['sensitivity', 'pointsource',
                                       'population', 'landcover_bar',
                                       'seasonal', 'landcover_polar',
                                       'multivar']

            html_string_individual_figures = ''
            for figure in list_individual_figures:
                path = os.path.join(
                    output_stc_path,
                    file_folder,
                    f'{figure}.{stc.settings["figFormat"]}'
                )
                relative_path = (
                    f'{relative_stc_path}/{file_folder}/'
                    f'{figure}.{stc.settings["figFormat"]}'
                )
                if os.path.exists(path):
                    html_string_individual_figures += (
                        '<a href='
                        f'{relative_path} target="_blank">{figure}.'
                        f'{stc.settings["figFormat"]}'
                        '</a><br>'
                    )
            settings_file_path = os.path.join(relative_stc_path, file_folder,
                                              'settings.json')
            html_string_settings = '<br><br>Settings:</br><a href=' + settings_file_path + ' target="_blank">settings.json</a><br>'

            with header_download:
                display(HTML(
                    html_string_pdf + html_string_individual_figures + html_string_settings))

        # make sure the progress bar is filled..
        updateProgress(f, 'finished')
        f.value = 10
    # after the tool is done running, it is possible to make a new tool run (hence the update button can be pressed given that the necessary widgets are populated)
    update_button.disabled = False
    update_button.tooltip = 'Click to start the run'
    update_button.style.button_color = button_color_able


# -----------widgets definition -----------------

style = {'description_width': 'initial'}
layout = {'width': 'initial', 'height': 'initial'}

header_station = Output()
with header_station:
    display(HTML(
        '<p style="font-size:15px;font-weight:bold;">Select station: </p>'))

# All stations, or limited to the labeled ICOS stations
station_type = RadioButtons(
    options=['ICOS stations', 'STILT stations'],
    value='ICOS stations',
    disabled=False)

station_choice = Dropdown(options=list_all_icos,
                          description='Station',
                          value=None,
                          disabled=False,
                          layout=layout,
                          style=style)

header_date_time = Output()
with header_date_time:
    display(HTML(
        '<p style="font-size:15px;font-weight:bold;"><br>Select date and time: </p>'))

# Create a Dropdown widget with year values (start year):
s_year = Dropdown(options=[],
                  description='Start Year',
                  disabled=False,
                  layout=layout)

# Create a Dropdown widget with month values (start month):
s_month = Dropdown(options=[],
                   description='Start Month',
                   disabled=False,
                   layout=layout)

# Create a Dropdown widget with year values (end year):
e_year = Dropdown(options=[],
                  description='End Year',
                  disabled=False,
                  layout=layout)

# Create a Dropdown widget with month values (end month):
e_month = Dropdown(options=[],
                   description='End Month',
                   disabled=False,
                   layout=layout)

s_day = Dropdown(options=[],
                 description='Start Day',
                 disabled=False,
                 layout=layout)

e_day = Dropdown(options=[],
                 description='End Day',
                 disabled=False,
                 layout=layout)

options_time_selection = [('0:00', 0), ('3:00', 3), ('06:00', 6),
                          ('09:00', 9), ('12:00', 12), ('15:00', 15),
                          ('18:00', 18), ('21:00', 21)]

time_selection = SelectMultiple(
    options=options_time_selection,
    value=[0, 3, 6, 9, 12, 15, 18, 21],
    description='Time of day',
    disabled=False,
    layout=layout,
    style=style)

header_bin_specifications = Output()
with header_bin_specifications:
    display(HTML(
        '<p style="font-size:15px;font-weight:bold;"><br>Select bin size and intervals: </p>'))

bin_size = Dropdown(options=[15, 30, 45, 60, 90, 180, 360],
                    description='Bin size (degrees)',
                    disabled=False,
                    layout=layout,
                    style=style)

interval = IntText(
    value=100,
    min=50,
    max=500,
    description='Interval (km)',
    disabled=False,
    step=50,
    layout=layout,
    style=style)

header_other = Output()
with header_other:
    display(HTML(
        '<p style="font-size:15px;font-weight:bold;"><br>Other specifications: </p>'))

# to explain the unit selection, a bit more information is needed
header_unit = Output()
with header_unit:
    display(HTML('<p style="font-size:12px;width: 250px;">\
    Select representation of surface influence in <b>percent</b> for optimal display of a single station or <b>absolute</b> values for \
    intercomparison between stations </p>'))

# selection percent/absolut:
unit_value = RadioButtons(
    description='',
    options=['percent', 'absolute'],
    value='percent',
    disabled=False,
    layout=layout,
    style=style)

# selection label landcover windrose:
landcover_windrose_label = RadioButtons(
    options=['yes', 'no'],
    value='yes',
    description='Labels to the land cover polar graph:',
    disabled=False,
    layout=layout,
    style=style)

save_figs = RadioButtons(
    options=['yes', 'no'],
    value='yes',
    description='Save the output:',
    disabled=False,
    layout=layout,
    style=style)

fig_format = RadioButtons(
    options=['pdf', 'png'],
    value='pdf',
    description='Format figures:',
    disabled=False,
    layout=layout,
    style=style)

header_filename = Output()
with header_filename:
    display(HTML(
        '<p style="font-size:15px;font-weight:bold;">Load settings from file (optional): </p>'))

file_name = FileUpload(
    accept='.json',
    # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False,  # True to accept multiple files upload else False
    layout={'width': 'initial', 'height': 'initial'})

# Create a Button widget to control execution:
update_button = Button(description='Run selection',
                       disabled=True,
                       button_style='danger',
                       # 'success', 'info', 'warning', 'danger' or ''
                       tooltip='Click to start the run',
                       layout=layout,
                       style=style)

update_button.style.button_color = button_color_able

# structure how the output should be presented
settings_grid_1 = GridspecLayout(3, 3)

settings_grid_1[0:1, 0:1] = header_station

settings_grid_1[1:2, 0:1] = station_type

settings_grid_1[2:3, 0:2] = station_choice

settings_grid_2 = GridspecLayout(3, 3)
settings_grid_2[0:1, 0:1] = header_date_time
settings_grid_2[1:2, 0:1] = s_year
settings_grid_2[1:2, 1:2] = s_month
settings_grid_2[1:2, 2:3] = s_day

settings_grid_2[2:3, 0:1] = e_year
settings_grid_2[2:3, 1:2] = e_month
settings_grid_2[2:3, 2:3] = e_day

settings_grid_3 = GridspecLayout(1, 3)
settings_grid_3[0:1, 0:1] = time_selection

settings_grid_4 = GridspecLayout(2, 3)
settings_grid_4[0:1, 0:1] = header_bin_specifications
settings_grid_4[1:2, 0:1] = bin_size
settings_grid_4[1:2, 1:2] = interval

settings_grid_5 = GridspecLayout(1, 3)
settings_grid_5[0:1, 0:1] = header_other

settings_grid_6 = GridspecLayout(1, 3)
settings_grid_6[0:1, 0:1] = header_unit
settings_grid_6[0:1, 1:2] = landcover_windrose_label
settings_grid_6[0:1, 2:3] = save_figs

settings_grid_7 = GridspecLayout(1, 3)
settings_grid_7[0:1, 0:1] = unit_value
settings_grid_7[0:1, 2:3] = fig_format

settings_grid_8 = GridspecLayout(2, 3)
settings_grid_8[0:1, 0:1] = header_filename
settings_grid_8[1:2, 0:1] = file_name
settings_grid_8[1:2, 2:3] = update_button

# Initialize form output:
form_out = Output()
# Initialize results output widgets:
progress_bar = Output()
header_no_footprints = Output()
header_output = Output()
result_sensitivity = Output()
result_population = Output()
result_pointsource = Output()
result_land_cover_bar_graph = Output()
result_seasonal_table = Output()
header_advanced = Output()
result_landcover_windrose = Output()
result_multiple_variables_graph = Output()
header_download = Output()


# --------------------------------------------------------------------

# OBSERVERS - what happens when change ex. change start year (s_year)
def observe():
    station_type.observe(change_stn_type, 'value')
    station_choice.observe(change_stn, 'value')
    s_year.observe(change_yr, 'value')
    s_month.observe(change_mt, 'value')
    s_day.observe(change_day, 'value')
    e_year.observe(change_yr_end, 'value')
    e_month.observe(change_month_end, 'value')
    e_day.observe(change_day_end, 'value')
    file_name.observe(file_set_widgets, 'value')

    # Call update-function when button is clicked:
    update_button.on_click(update_func)


def unobserve():
    station_type.unobserve(change_stn_type, 'value')
    station_choice.unobserve(change_stn, 'value')
    s_year.unobserve(change_yr, 'value')
    s_month.unobserve(change_mt, 'value')
    s_day.unobserve(change_day, 'value')
    e_year.unobserve(change_yr_end, 'value')
    e_month.unobserve(change_month_end, 'value')
    e_day.unobserve(change_day_end, 'value')


# start observation
observe()

# --------------------------------------------------------------------
# Open form object:
with form_out:
    h_box_1 = HBox([header_output])
    grid = GridspecLayout(2, 2)
    grid[0:1, 0:1] = result_sensitivity
    grid[0:1, 1:2] = result_pointsource
    grid[1:2, 0:1] = result_population
    grid[1:2, 1:2] = result_land_cover_bar_graph
    # table much "thinner" - make HBox rather than in grid
    h_box_2 = HBox([result_seasonal_table])
    # grid for the last two:
    h_box_3 = HBox([header_advanced])
    grid_2 = GridspecLayout(1, 4)
    grid_2[0:1, 0:2] = result_landcover_windrose
    grid_2[0:1, 2:4] = result_multiple_variables_graph

    update_buttons = HBox([file_name, update_button])

    display(settings_grid_1, settings_grid_2, settings_grid_3,
            settings_grid_4, settings_grid_5, settings_grid_6,
            settings_grid_7, settings_grid_8, progress_bar,
            header_no_footprints, h_box_1, grid, h_box_2, h_box_3, grid_2,
            header_download)

# Display form:
display(widgets.HTML(style_scroll), form_out)