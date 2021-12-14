import math
import re
import numpy as np
import pandas as pd
from icoscp.sparql.runsparql import RunSparql
from icoscp.station import station
from icoscp.cpb.dobj import Dobj
from ipywidgets import HBox, Layout
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt


data = {
    'station_ids': [],
    'station_names': [],
    'heights_per_id': {},
    'exclude': {'GAT': ['2.5'], 'HEL': ['2.5'], 'HPB': ['50.0'], 'JFJ': ['1.0', '2.0'],
                'HTM': ['3.5']}
}


def query_stations():
    # todo: edit this query to something more simple.
    query = \
        f'prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>\n' + \
        f'prefix prov: <http://www.w3.org/ns/prov#>\n' + \
        f'select ?dobj ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd\n' + \
        f'where {{\n' + \
        f'	VALUES ?spec {{<http://meta.icos-cp.eu/resources/cpmeta/atcMtoL2DataObject>}}\n' + \
        f'	?dobj cpmeta:hasObjectSpec ?spec .\n' + \
        f'	?dobj cpmeta:hasSizeInBytes ?size .\n' + \
        f'?dobj cpmeta:hasName ?fileName .\n' + \
        f'?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .\n' + \
        f'?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .\n' + \
        f'?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .\n' + \
        f'	FILTER NOT EXISTS {{[] cpmeta:isNextVersionOf ?dobj}}\n' + \
        f'	{{\n' + \
        f'		{{FILTER NOT EXISTS {{?dobj cpmeta:hasVariableName ?varName}}}}\n' + \
        f'		UNION\n' + \
        f'		{{\n' + \
        f'			?dobj cpmeta:hasVariableName ?varName\n' + \
        f'			FILTER (?varName = "WD" || ?varName = "WS")\n' + \
        f'		}}\n' + \
        f'	}}\n' + \
        f'}}\n' + \
        f'order by desc(?submTime)\n'
    return RunSparql(sparql_query=query, output_format='pandas').run()


def find_relevant_stations(process_data):
    # Get all distinct station ids from the sparql query.
    data['station_ids'] = sorted(list(set(process_data['fileName'].str[22:25])))
    for station_id in data['station_ids']:
        data['heights_per_id'][station_id] = []
        # These names will appear in the gui. They are a combination of
        # station name and station id.
        data['station_names'].append(station_id + ' ' + station.get(station_id).name)
        # Find all dataframe rows relevant to the station id.
        df_station_files = \
            process_data[process_data['fileName'].str.contains(station_id)]['fileName'].to_list()
        # Extract the different sampling heights
        # for the current station.
        for str_file in df_station_files:
            sampling_height = re.findall(r'[+-]?\d*\.\d*', str_file)[1]
            # Exclude sampling heights not meant for wind speed
            # measurements.
            if (station_id in data['exclude'].keys() and
                    sampling_height in data['exclude'][station_id]):
                continue
            data['heights_per_id'][station_id].append(sampling_height)
        # Sort sampling heights so they appear correctly in the gui.
        data['heights_per_id'][station_id] = sorted(data['heights_per_id'][station_id], key=float)
    return


def initialise():
    m_data = query_stations()
    find_relevant_stations(process_data=m_data)

    station_drop_down = widgets.Dropdown(description='Please choose station',
                                         style={'description_width': 'initial'},
                                         options=data['station_names'],
                                         value=None)

    def station_drop_down_handler(change):
        sampling_height_drop_down.options = data['heights_per_id'][change.new[0:3]]

    sampling_height_drop_down = widgets.Dropdown(description='and height',
                                                 style={'description_width': 'initial'},
                                                 options=[],
                                                 value=None,
                                                 layout=Layout(width='auto', margin='0 0 0 15px'))

    # def height_drop_down_handler(change):
    #     sampling_height_drop_down.options = data['heights_per_id'][change.new[0:3]]

    station_drop_down.observe(station_drop_down_handler, names='value')
    # sampling_height_drop_down.observe(height_drop_down_handler, names='value')

    my_button = widgets.Button(
        description='Update Plots',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click me',
        icon='check' # (FontAwesome names without the `fa-` prefix)
    )
    output = widgets.Output()
    box = HBox([station_drop_down, sampling_height_drop_down])
    display(box, my_button)

    @output.capture()
    def on_button_clicked(b):
        current_station_selection = station_drop_down.value[0:3]
        current_sampling_height_selection = sampling_height_drop_down.value
        print(current_station_selection, ' ', current_sampling_height_selection)
        output.clear_output()
        with output:
            get_data(station_id=current_station_selection,
                     sampling_height=current_sampling_height_selection)

    my_button.on_click(on_button_clicked)
    display(output)


def get_data(station_id, sampling_height):
    station_object = station.get(station_id)
    station_data = station_object.data()
    m_meta_data = station_data[(station_data['specLabel'] == 'ICOS ATC Meteo Release') &
                               (station_data['samplingheight'] == sampling_height)]
    # m_meta_data = station_data[station_data['specLabel'].str.contains('ICOS ATC Meteo Release')
    #                            and station_data['samplingheight'] == sampling_height]
    co2_meta_data = station_data[station_data['specLabel'].str.contains('ICOS ATC CO2 Release')]
    ch4_meta_data = station_data[station_data['specLabel'].str.contains('ICOS ATC CH4 Release')]
    m_data = pd.DataFrame
    for m_index, m_row in m_meta_data.iterrows():
    #     m_time_start = m_row['timeStart']
    #     m_time_end = m_row['timeEnd']
    #     m_sampling_height = m_row['samplingheight']
        m_data = Dobj(m_row['dobj']).data
        m_data = m_data[['WD', 'WS', 'TIMESTAMP']]
    #     co2_height_queried = co2_meta_data[
    #         co2_meta_data['samplingheight'] == m_sampling_height]
    #     for co2_index, co2_row in co2_height_queried.iterrows():
    #         co2_time_start = co2_row['timeStart']
    #         co2_time_end = co2_row['timeEnd']
    #         if co2_time_start <= m_time_start <= co2_time_end:
    #             # todo: configure for m_time_end ending in another co2 dobj.
    #             if m_time_end <= co2_time_end:
    #                 co2_dobj = Dobj(co2_row['dobj'])
    #                 co2_data = co2_dobj.data
    #                 co2_data = co2_data[['co2', 'TIMESTAMP']]
    #                 merger = pd.merge_asof(left=m_data, right=co2_data, left_on='TIMESTAMP',
    #                                        right_on='TIMESTAMP')
    #                 merger.dropna()
    #                 #                 ax = WindroseAxes.from_ax()
    #                 #                 ax.bar(merger['WD'], merger['WS'], bins=np.arange(0, 8, 1), nsector=36, normed=True, cmap=cm.Reds, opening=0.8)
    #                 #                 ax.set_xticklabels(['E', 'NE', 'N', 'NW',  'W', 'SW', 'S', 'SE'])
    #                 #                 ax.set_legend()
    #                 csv_file = m_sampling_height + '_zois.csv'
    #                 merger.to_csv(csv_file)
    #                 print('Using this', co2_dobj, 'digital object for sampling height of',
    #                       m_sampling_height, '->', csv_file)
    #                 break
    #             else:
    #                 print('Need to merge with other dataframes...')
    #         else:
    #             print('No Co2 data for sampling height of', m_sampling_height)
    #             continue
    #             # 2016-05-10 00:00:00
    pi = np.pi
    data = m_data
    data['wind_direction_in_radians'] = data['WD'].apply(lambda wind_direction: math.radians(
        wind_direction))
    fig, ax = plt.subplots(subplot_kw=dict(projection='polar'), figsize=(10, 10))
    ax.set_xticks(np.arange(0, 2 * pi, pi / 4))
    ax.set_xticklabels(['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'])
    ax.set_title("Wind Rose", fontsize=25)

    step_angle = pi / 12
    x_edges = np.arange(0, 2 * pi + step_angle, step_angle)
    y_edges = np.arange(0, math.ceil(data['WS'].max()), 1)

    x = data['wind_direction_in_radians']
    y = data['WS']
    X, Y = np.meshgrid(x_edges, y_edges)

    # x = γωνια
    # y = ακτινα
    H, x_edges, y_edges = np.histogram2d(x, y, bins=[x_edges, y_edges])
    H = H.T  # Let each row list bins with common y range.
    quad_mesh = ax.pcolormesh(X, Y, H, zorder=-1, vmin=0, vmax=H.max(),
                              cmap=plt.cm.get_cmap('Accent'))
    quad_mesh = ax.pcolormesh(X, Y, H, cmap=plt.cm.get_cmap('Reds'))

    # cbar_1 = fig.colorbar(mappable=quad_mesh_1)
    # cbar_2 = fig.colorbar(mappable=quad_mesh_2)

    ax.yaxis.labelpad = 1

    rlabels = ax.get_ymajorticklabels()

    ax.grid(True)
    plt.show()
