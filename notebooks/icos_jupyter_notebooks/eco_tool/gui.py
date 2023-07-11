#!/usr/bin/python

"""
    This is the main entry to run the
    Ecosystem notebook for PIs.
    In the gui the user can create
    groups of variables and batch jobs to run

    The purpose is to run the program from
    a notebook on https://jupyter.icos-cp.eu/
    using
    >>> from eco_tool import gui
    >>> g = gui.AnalysisGui();
"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.2"
__date__ = "2023-06-11"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import warnings

from ipywidgets import widgets as wd
from IPython.display import display, clear_output
from icoscp.cpb.dobj import Dobj
import datetime as dt

warnings.simplefilter("ignore", FutureWarning)
import os

if os.getcwd()[-8:] == 'eco_tool':
    import icos_data
    import plot_old
    import report_writer
    from icos_timeseries import IcosFrame
    import json_handler
    import icos2latex
else:
    from eco_tool import icos_data
    from eco_tool import plot_old
    from eco_tool import report_writer
    from eco_tool.icos_timeseries import IcosFrame
    from eco_tool import json_handler
    from eco_tool import icos2latex


def _var_tup2station_dict(var_tuples: list = None):
    """
    var_tuple: list of tuples
        Each tuple is of the form
            (variable, file, station)

     Returns
     a dictionary of the form

    """
    station_dict = {}
    for v_tuple in var_tuples:
        st = v_tuple[-1]
        prod = v_tuple[-2]
        var = v_tuple[0]
        if st in station_dict.keys():
            if prod in station_dict[st].keys():
                station_dict[st][prod].append(var)
            else:
                station_dict[st][prod] = [var]
        else:
            station_dict[st] = {prod: [var]}
    return station_dict


def _get_layout(text: str = None):
    min_width = max(40, len(text) * 8)
    max_width = min(150, len(text) * 9 + 12)
    this_layout = wd.Layout(min_width=f'{min_width}px',
                            max_width=f'{max_width}px')
    return this_layout


class _AppDataRetriever:
    """
        Object to retrieve appdata settings.
        We use the same instance in other objects.
    """

    def __init__(self, app_config_file: str, user_cache_file: str,
                 user_config_file: str, settings_dir: str, debug: bool):
        if debug:
            self.debug = True
        else:
            self.debug = False
        self.app_config_file = app_config_file
        self.user_cache_file = user_cache_file
        self.user_config_file = user_config_file
        self.settings_dir = settings_dir
        self.cache = None

    def load_app_configs(self):
        default_dict = {'_var2unit_map': {}}
        return self._load_json(default_dict=default_dict,
                               json_file=self.app_config_file)

    def load_cache(self, refresh: bool = None):
        if refresh or not self.cache:
            default_dict = {'_last_station_id': '',
                            '_last_group': '',
                            '_groups': {}}
            self.cache = self._load_json(default_dict=default_dict,
                                         json_file=self.user_cache_file)
        return self.cache

    def _load_json(self,
                   default_dict: dict = None,
                   json_file: str = None):

        return_dict = {}

        if default_dict is None:
            default_dict = {}
        try:
            return_dict = json_handler.read(json_file=json_file,
                                            settings_dir=self.settings_dir)
        except Exception as e:
            print('Exception from "_load_json()"!')
            print(f'\nCheck the file: {self.settings_dir}/{json_file}\n\n',
                  e)
        finally:

            for k, v in default_dict.items():
                return_dict[k] = return_dict.get(k, v)
        return return_dict

    def load_user_settings(self):

        return self._load_json(default_dict={},
                               json_file=self.user_config_file)


class AnalysisGui:
    # Colors of ipywidgets predefined styles
    ipyw_style_colors = {'text_color': '#FFFFFF', 'primary': '#2196F3',
                         'primary:active': '#1976D2', 'success': '#4CAF50',
                         'success:active': '#388E3C', 'info:active': '#0097A7',
                         'warning': '#FF9800', 'warning:active': '#F57C00',
                         'danger': '#F44336', 'danger:active': '#D32F2F'}

    def __init__(self, theme=None, level=None, debug=None):
        if not theme:
            theme = 'ES'
        if not level:
            level = '1'
        self.theme = theme
        self.level = level
        self.debug = True if debug else False

        self.app_config_file = f'_app_config_{theme}.json'
        self.user_cache_file = f'user_var_config_{theme}.json'
        self.user_config_file = f'user_app_config_{theme}.json'
        self.settings_dir = 'eco_tool/appdata'
        self.retriever = _AppDataRetriever(app_config_file=self.app_config_file,
                                           user_cache_file=self.user_cache_file,
                                           user_config_file=self.user_config_file,
                                           settings_dir=self.settings_dir,
                                           debug=self.debug)

        self.cache = None
        self.stored_timeseries = None
        self.icos_info = None
        self.stations_df = None
        self.report_writer = None

        self._reset_gui_data()
        self.go()

    def _reset_gui_data(self):
        # reset non-persistent data
        self._load_cache(refresh=True)
        self.stored_timeseries = {}

        self.icos_info = icos_data.StationData(theme=self.theme,
                                               level=self.level)
        self.stations_df = self.icos_info.stations_df
        self.report_writer = None

    def _get_report_writer(self):

        if self.report_writer is None:
            self.report_writer = report_writer.ReportWriter(self.retriever,
                                                            self.icos_info,
                                                            self.debug)
        else:
            today = dt.datetime.today().strftime('YYYY-MM-DD')
            if self.report_writer.timestamp == today:
                return self.report_writer
            else:
                self._reset_gui_data()
                self._get_report_writer()

        return self.report_writer

    def go(self):

        def main_change(change):
            choice = change['new']
            with out:
                clear_output()
                if choice == 'Start ':
                    self._start()
                elif choice == 'Group menu ':
                    self._edit_group_variables()
                elif choice == 'Configurations ':
                    self._user_configurations()
                elif choice == 'Help ':
                    self._help()
                else:
                    self._edit_group_variables_new()

        if self.debug:
            option_ls = ['Start ', 'Group menu ',
                         'Configurations ', 'G2', 'Help ']
            icon_ls = ['area-chart', 'list', 'cog', 'ban', 'info-circle']

        else:
            option_ls = ['Start ', 'Group menu ',
                         'Configurations ', 'Help ']
            icon_ls = ['area-chart', 'list', 'cog', 'info-circle']

        main = wd.ToggleButtons(options=option_ls,
                                button_style="success",
                                style={'button_width': "120px"},
                                tooltip=None,
                                icons=icon_ls)

        group_cache = self._load_cache()
        if group_cache['_groups'].keys():
            start_value = 'Start '
        else:
            # In the first run, there are no
            # group of variables.
            start_value = 'Group menu '
        main.value = start_value

        out = wd.Output()
        main.observe(main_change, "value")
        with out:
            if start_value == 'Start ':
                self._start()
            else:
                self._edit_group_variables()

        display(wd.VBox([main, out]))

    def _start(self):

        if self.debug:
            print('*** _start()\n')

        def set_gui():
            cache = self._load_cache()
            # set group drop
            if not cache['_groups'].keys():
                with out:
                    clear_output()
                    msg = 'First you need to create a group of variables ' \
                          'using the "Group menu"'
                    display(wd.HTML(msg))
                    return False

            group_drop.options = list(cache['_groups'].keys())
            group_drop.observe(init_batch_jobs,
                               names='value')
            if cache['_last_group']:
                group_drop.value = cache['_last_group']
            else:
                group_drop.value = group_drop.options[0]
            group_drop.disabled = False

            # tool settings
            settings = self._load_user_settings()
            end_shift = 0
            start_shift = -8
            fetch_shift = 6
            if 'time_configs' in settings.keys():
                end_shift = - settings['time_configs'].get('end_date', 0)
                start_shift = - settings['time_configs'].get('start_date', 8)
                fetch_shift = settings['time_configs'].get('fetch_date', 6)

            end_date.value = dt.date.today() + dt.timedelta(days=end_shift)
            start_date.value = end_date.value + dt.timedelta(days=start_shift)
            days.value = fetch_shift
            return True

        def init_batch_jobs(c):
            cache = self._load_cache()
            grp = group_drop.value
            if grp in cache['_groups'].keys() and \
                    '_batches' in cache['_groups'][grp].keys():
                batches = cache['_groups'][grp].get('_batches', {})
                if batches:
                    b_ls = [wd.Button(description=b_name,
                                      style={'button_width': '100px',
                                             'button_color': 'LightSeaGreen'},
                                      layout=_get_layout(b_name))
                            for b_name in batches.keys()]
                    if b_ls:
                        all_title = 'Run all batch jobs'
                        b_ls.append(wd.Button(description=all_title,
                                              style={'button_width': '100px',
                                                     'button_color':
                                                         'MediumSeaGreen'},
                                              layout=_get_layout(all_title)))
                    for bt in b_ls:
                        bt.on_click(run_batch)
                    batch_jobs.children = b_ls

        def days_changed(change):
            start_date.value = end_date.value + dt.timedelta(days=-days.value)

        def date_changed(change):
            if change['owner'].description == 'End date':
                if change['new'] <= start_date.value:
                    end_date.value = change['old']
            elif change['owner'].description == 'Start date':
                if change['new'] >= end_date.value:
                    start_date.value = change['old']

        def get_data():
            with out:
                display(wd.HTML(value='<h1>Generating report...</h1>'))
            grp = group_drop.value
            cache = self._load_cache()
            var_tuple_ls = cache['_groups'][grp]['_group_vars']

            start = start_date.value
            end = end_date.value

            # Reuse timeseries if possible
            store = self.stored_timeseries.get(grp, None)
            if isinstance(store, dict):
                if store['start'] <= start and store['end'] >= end:
                    df = store['df']
                    return df

            var_pid_ls = []
            st_df = self.stations_df
            for var, prod, stn in var_tuple_ls:
                # sampleheight needed for 'AS'

                pid = st_df.loc[(st_df.id == stn) & (st_df.specLabel ==
                                                     prod)].dobj.values[0]
                var_pid_ls.append((var, pid))

            stored_start = start + dt.timedelta(days=-days.value)
            stored_end = end + dt.timedelta(days=2)
            if self.debug:
                with out:
                    print(var_pid_ls)

            df = None
            try:
                df = icos_data.StationData.group_ts(var_tuple_ls=var_pid_ls,
                                                    start_date=stored_start,
                                                    end_date=stored_end)
            except Exception:
                if self.debug:
                    import traceback
                    with out:
                        print('-- Error in call: \n',
                              f'icos_data.StationData.group_ts(var_tuple_ls={var_pid_ls},'
                              + f'\nstart_date= {stored_start}, \nend_date= {stored_end})',
                              type(stored_start), type(stored_end))
                        print('Traceback: ', traceback.format_exc())

            # Store the timeseries
            self.stored_timeseries[grp] = {'start': stored_start,
                                           'end': stored_end,
                                           'df': df}

            return df

        def run_batch(c):
            if c == 0 or c.description == 'Run all batch jobs':
                jobs = 'all'
            else:
                jobs = c.description

            if self.debug:
                with out:
                    print('run_batch()',
                          jobs,
                          group_drop.value)

            with out:
                clear_output()
                if jobs == 'all':
                    temp_title = f'Generating report to all batch jobs ' \
                                 f'of variable group {group_drop.value}...'
                else:
                    temp_title = f'Generating report of batch(es) {jobs} ' \
                                 f'of variable group {group_drop.value}...'
                display(wd.HTML(temp_title))

            rw = self._get_report_writer()

            if jobs == 'all':
                cache = self._load_cache()
                grp = group_drop.value
                batch_ls = list(cache['_groups'][grp]['_batches'].keys())
            else:
                batch_ls = [jobs]

            report_dict = rw.get_batch_report(group=group_drop.value,
                                              batch_ls=batch_ls,
                                              start_date=start_date.value,
                                              end_date=end_date.value)
            with out:
                clear_output()
                display(report_dict['main_title'])
                for b in batch_ls:
                    display(report_dict[b]['batch_title'])
                    for tool_result in report_dict[b]['result']:
                        if tool_result[0] in ['split_plot', 'multi_plot',
                                              'corr_plot']:
                            try:
                                tool_result[1].show()
                            except Exception:
                                print('ERROR in run_batch ---- ', tool_result[0])
                                print('ERROR in run_batch ---- ', tool_result[1])
                        else:
                            if self.debug:
                                print(f'Not implemented: {tool_result[0]} ')
                            pass

        def run(c):
            with out:
                clear_output()
            df = get_data()
            if self.debug:
                print(df)
                with out:
                    print(type(df))

            # Generating report title
            grp = group_drop.value
            stations = df.icos_station_name
            products = df.icos_product
            urls = df.icos_accessUrl
            today = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            rep_title1 = f'<h1>Report for the variable group: <font color="DodgerBlue">{grp}</font>, {today}.</h1><br>'
            rep_title2 = 'Data from '
            rep_title3 = ''
            if all((isinstance(x, str) for x in [stations, products, urls])):
                rep_title2 += f'<a href="{urls}" target = "_blank">\
                <font color="DarkBlue">{products}</font></a> of {stations}.'
            elif all(
                    (isinstance(x, list) for x in [stations, products, urls])) and \
                    len(stations) == len(products) and len(products) == len(urls):
                n = len(stations)
                d = {}
                for i in range(n):
                    s = stations[i]
                    p = products[i]
                    u = urls[i]
                    v = (p, u)
                    if s in d.keys():
                        if v not in d[s]:
                            d[s].append(v)
                    else:
                        d[s] = [v]
                last_char = ''
                for s, v in d.items():
                    rep_title2 += last_char
                    for tup in v:
                        rep_title2 += f'<a href="{tup[1]}" target = "_blank">\
                        <font color="DarkBlue">{tup[0]}</font></a>, '
                    rep_title2 += f' of {s}'
                    last_char = ';<br>'
                rep_title2 += '.'
            else:
                if isinstance(products, str):
                    rep_title2 += f'Data from {products}'
                else:
                    rep_title2 += f'Data from {", ".join(products)}'

                if isinstance(stations, str):
                    rep_title2 += f' collected at {stations}.'
                elif len(set(stations)) == 1:
                    rep_title2 += f' collected at {stations[0]}.'
                else:
                    rep_title2 += f' collected at {", ".join(stations)}.'
                rep_title2 = f'<h2>{rep_title2}</h2><br>'

                if isinstance(urls, str):
                    rep_title3 += f'Link to data:  <a href="{urls}">{urls}</a>.'
                else:
                    rep_title3 += 'Links to data:  '
                    for u in urls:
                        rep_title3 += f'<a href = "{u}" target = "_blank"> {u} </a>.'

            rep_title2 = f'<h3>{rep_title2}</h3>'
            report_title = rep_title1 + rep_title2 + rep_title3

            with out:
                clear_output()
                report = wd.HTML(value=report_title)
                display(report)

            if tool_drop.value == 'Split-plot':
                sliders = int(plot_sliders.value)
                var_units = df.icos_var_unit_ls
                data = df[start_date.value:end_date.value]
                title = f'Split plot of variable group {grp}  (Timestamp: {today})'

                with out:
                    plot_old.split_plot(data,
                                        n=sliders,
                                        units=var_units,
                                        title=title).show()

        def save():
            # clear local storage
            self._flush_store('')
            cache = self._load_cache()
            json_handler.write(data=cache,
                               json_file=self.user_cache_file,
                               settings_dir=self.settings_dir)

        # Main of configurations
        # ======================

        # Layouts

        right_aligned_column = wd.Layout(display='flex',
                                         # Possible values of display:flex, grid
                                         flex_flow='column',
                                         # Pos. values of flex_flow:row,column
                                         align_items='flex-end')
        # Pos values of  align_items: center, flex-start, flex-end, stretch

        common_layout = wd.Layout(width='148pt', height='30px')

        # Dropdowns

        group_drop = wd.Dropdown(description='Groups',
                                 layout=common_layout)
        batch_jobs = wd.HBox()
        tool_drop = wd.Dropdown(description='Tools',
                                options=['Split-plot',
                                         'Multi-plot'
                                         'Correlation plot',
                                         'Correlation table'],
                                layout=common_layout)

        plot_sliders = wd.Dropdown(description="Plot sliders",
                                   options=range(1, 10),
                                   layout=common_layout)

        days = wd.Dropdown(description="Max days",
                           options=range(1, 100),
                           layout=common_layout)

        start_date = wd.DatePicker(description='Start date',
                                   layout=common_layout)

        end_date = wd.DatePicker(description='End date',
                                 layout=common_layout,
                                 tooltip='Default is yesterday')

        # tool_buttons = wd.ToggleButtons(button_style="success",
        #                                 tooltip='settings')
        # add_btn = wd.Button(description='Add setting',
        #                     icon='plus',
        #                     button_style='primary')
        # save_btn = wd.Button(description='Save setting',
        #                      icon='save',
        #                      button_style='success')
        # info_btn = wd.Button(description='Info',
        #                      icon='fa-info-circle',
        #                      button_style='info')

        # toolbox = wd.VBox([wd.HBox([tool_buttons]), wd.VBox([save_btn, add_btn])])

        run_btn = wd.Button(description="Run", icon='area-chart',
                            button_style='success')  #####, layout=center_layout)

        out = wd.Output()

        if set_gui():
            # observe changes
            run_btn.on_click(run)
            days.observe(days_changed, "value")
            start_date.observe(date_changed, "value")
            end_date.observe(date_changed, "value")

            display(wd.VBox([wd.HBox([group_drop, tool_drop, run_btn]),
                             wd.HBox([start_date, end_date]),
                             # layout=right_aligned_column),
                             batch_jobs,
                             out]))  # layout=right_aligned_column))

            if self.debug:
                pass
            else:
                if batch_jobs.children:
                    run_batch(0)
                else:
                    run(0)

    def _load_app_configs(self):
        return self.retriever.load_app_configs()

    def _load_cache(self, refresh: bool = None):
        return self.retriever.load_cache(refresh=refresh)

    def _load_user_settings(self):
        return self.retriever.load_user_settings()

    def _set_app_configs(self,
                         app_dict: dict = None):
        try:
            json_handler.write(data=app_dict,
                               json_file=self.app_config_file,
                               settings_dir=self.settings_dir)
        except Exception as e:
            print(e)
        return

    def _set_cache(self,
                   cache_dict: dict = None):
        json_handler.write(data=cache_dict,
                           json_file=self.user_cache_file,
                           settings_dir=self.settings_dir)
        self.report_writer = None
        self.retriever.cache = cache_dict

    def _help(self):
        # static help text
        with open('./eco_tool/images/GroupMenu.png', 'rb') as f:
            group_menu = f.read()
        group_img = wd.Image(value=group_menu)
        group_img.layout.height = '28px'

        user_guide = wd.HTMLMath(disabled=True,
                                 layout=wd.Layout(width='auto', height='auto'))
        user_guide.value = f'''This application is aimed to help 
        principal investigators (PI) to analyse near real time variables of ICOS 
        stations. There are two main blocks:
        <br>
        <br>
        <div><img src="./pi/images/Tools.png" alt="Group menu" style="width: 
        120px;"/>  In the tools view you can setup different methods to 
        investigate variables of a group.            
        </div>
        <br>
        <br>
        <div><img src="./pi/images/GroupMenu.png" alt="Group menu" style="width: 
        120px;"/>  In the group view you can create groups of variables.
           
         </div>
        
        <br> 
        In the Tools menu    
        The starting point for a new user is...
                        Use the Group menu to create groups of variables.
        <br>
        <br>
        For questions or feedback, please contact $\\tt info@icos-cp.eu$ or 
        $\\tt anders.dahlner@nateko.lu.se$'''

        display(user_guide)

    def _tool_settings(self):
        pass

    def _flush_store(self, grp):
        """
        When the user change a group of variables the local
        storage of timeseries should be removed. When the
        user change run settings the local storage should be
        cleared.

        grp: str
            the group name

        """
        if self.debug:
            print('*** _flush_store()\n')

        if grp:
            self.stored_timeseries.pop(grp, None)
        else:
            self.stored_timeseries.clear()

    def _edit_batch_jobs(self):
        global iii
        iii = 0
        if self.debug:
            print('*** _edit_batch_jobs()\n')

        def init(group_name: str = None,
                 batch_name: str = None):

            if self.debug:
                debug_ls = [0, 'init()', 'step 1',
                            f'group_name = {group_name}',
                            f'batch_name = {batch_name}']
                debug_value(debug_ls)

            there_are_groups = init_group_drop(group_name)

            if there_are_groups:
                if self.debug:
                    debug_ls = [0, 'init()', 'step 2 ',
                                f'batch_name = {batch_name}']
                    debug_value(debug_ls)
                changed_group_drop(c=None, batch_name=batch_name)
                activate_gui('init')
            else:
                if self.debug:
                    debug_ls = [0, 'init()', 'step 2 (no groups)',
                                f'there_are_groups = {there_are_groups}']
                    debug_value(debug_ls)
                html_msg(text_ls=['First you need to create a group of ',
                                  'variables using the group menu'])
            if self.debug:
                debug_ls = [0, 'init()', '--- end ---']
                debug_value(debug_ls)

            return there_are_groups

        def init_tool_buttons():
            tool_ls = []
            for tool in tool2name_dict.values():
                bt = wd.Button(description=tool,
                               style={'button_width': '100px',
                                      'button_color': 'LightGreen'},
                               layout=_get_layout(tool))
                bt.on_click(tool_click)
                tool_ls.append(bt)
            tool_buttons.children = tool_ls

        def init_group_drop(group: str = None):
            cache = self._load_cache()
            group_ls = list(cache['_groups'].keys())

            if self.debug:
                debug_ls = [1, f'init_group_drop()', '- step 1',
                            f'group list = {group_ls}']
                debug_value(debug_ls)

            if group_ls:
                group_ls = sorted(group_ls)
                group_drop.options = group_ls
                if group and group in group_ls:
                    group_drop.value = group
                elif cache['_last_group']:
                    group_drop.value = cache['_last_group']
                else:
                    group_drop.value = group_ls[0]

                if self.debug:
                    debug_ls = [1, f'init_group_drop()', '- step 2',
                                f' value = {group_drop.value}',
                                '---- end --- ']
                    debug_value(debug_ls)

                return True
            else:
                return False

        def changed_group_drop(c, batch_name: str = None):
            if self.debug:
                debug_ls = [2, f'changed_group_drop()',
                            f'batch_name = {batch_name}']
                debug_value(debug_ls)

            set_var_translation_dict()
            set_group_var_info()
            init_group_var_buttons()
            init_batch_drop(batch_name)
            activate_gui('changed_group_drop')

        def set_var_translation_dict():
            """
                Dictionary of labels for buttons and selected variables.
                The translation dict is of the form
                {(var,product,station): "name of var button"}
                in a one-to-one correspondence.
                The dictionary is temporarily stored in a widget which
                is not displayed.
            """

            if self.debug:
                debug_ls = [3, f'set_var_translation_dict()']
                debug_value(debug_ls)
            grp = group_drop.value
            cache = self._load_cache()
            var_ls = cache['_groups'][grp]['_group_vars']
            one_stn = len(set(ls[2] for ls in var_ls)) == 1
            one_prod = len(set(ls[1] for ls in var_ls)) == 1

            translation_dict = {}
            for v_ls in var_ls:
                var_name = v_ls[0]
                var_name_description = []
                if not one_prod:
                    var_name_description.append(v_ls[1])
                if not one_stn:
                    var_name_description.append(v_ls[2])
                if var_name_description:
                    var_name += f' ({", ".join(var_name_description)})'
                translation_dict[var_name] = v_ls

            translation_dict['Select all'] = 'All variables'
            var_translation_dict.value = str(translation_dict)

        def init_group_var_buttons():
            if self.debug:
                debug_ls = [6, f'init_group_var_buttons()']
                debug_value(debug_ls)

            var_list = list(get_var_translation_dict().items())
            var_buttons.children = []
            btn_ls = []
            for var_name, var_ls in var_list[:-1]:
                btn = wd.Button(description=var_name,
                                disabled=True,
                                tooltip=var2unit(var_ls),
                                style={'button_color': 'LightSeaGreen'},
                                layout=_get_layout(var_name))
                btn.on_click(var_button_click)
                btn_ls.append(btn)
            var_name = 'Select all'
            btn = wd.Button(description=var_name,
                            disabled=True,
                            tooltip='',
                            style={'button_color': 'MediumSeaGreen'},
                            layout=_get_layout(var_name))
            btn.on_click(var_button_click)
            btn_ls.append(btn)
            var_buttons.children = btn_ls

        def init_batch_drop(batch_name: str = None):
            cache = self._load_cache()
            group = group_drop.value
            if self.debug:
                debug_ls = [9, 'init_batch_drop()', 'step 1',
                            f'(input) batch_name = {batch_name}',
                            f'group = {group}',
                            f"cache['_groups']['{group}'] = "
                            f"{cache['_groups'][group]}"]
                debug_value(debug_ls)

            if '_batches' in cache['_groups'][group].keys():
                batch_dict = cache['_groups'][group]['_batches']

                if self.debug:
                    debug_ls = [9, 'init_batch_drop()', 'step 2',
                                f'batches = {batch_dict}']
                    debug_value(debug_ls)

                batch_labels = sorted(list(batch_dict.keys()))

                batch_drop.options = [(k, batch_dict[k]) for k in batch_labels]
                if batch_name and batch_name in batch_dict.keys():
                    batch_drop.value = batch_dict[batch_name]
                    changed_batch_drop('init')
                else:
                    batch_drop.value = list(batch_dict.values())[0]
            else:
                batch_drop.options = [('Press new...', 0)]
                batch_drop.value = 0
                html_msg(text=f'Press "New", in order to create a batch job for '
                              f'the group <it>{group}.</it>.')
            if self.debug:
                debug_ls = [9, 'init_batch_drop()', 'step 3',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch_drop.value}',
                            f'-- end--']
                debug_value(debug_ls)

        def changed_batch_drop(c):
            batch = batch_drop.value.copy()

            if self.debug:
                debug_ls = [11, 'changed_batch_drop()', '- step 1 - batch '
                                                        'value changed, '
                                                        'reset displayed '
                                                        'selections',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch}']
                debug_value(debug_ls)

            if batch != 0:
                batch_version = batch.pop('_version', '0')
                set_batch_upd_dict(dict(_tools=batch,
                                        _selected_tool_index=None,
                                        _version=batch_version))
            else:
                set_batch_upd_dict(dict(_tools={}))

            if self.debug:
                debug_ls = [11, 'changed_batch_drop()', '- step 2 - ',
                            f'upd_dict_log.value = {upd_dict_log.value}']
                debug_value(debug_ls)

        def reset_selection(c):
            if self.debug:
                debug_ls = [13, f'reset_selection()',
                            f'c = {c}']
                debug_value(debug_ls)

            batch_dict = get_batch_upd_dict()

            if self.debug:
                debug_ls = [13, f'reset_selection()',
                            f'batch_dict = {batch_dict}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(debug_ls)

            sel_tool_index = batch_dict.pop('_selected_tool_index', -1)
            tools = batch_dict.get('_tools', {})
            sel_tools = [(tool2name_dict[k2], k1) for k1, v1 in tools.items() for
                         k2 in v1.keys()]
            sel_vars_of_tool = []
            for index, tool_dict in tools.items():
                for tool_code, tool_vars in tool_dict.items():
                    sel_vars_of_tool.append((label_of_var_row(tool_code,
                                                              tool_vars),
                                             (index, tool_vars)))

            set_selections(sel_tool_ls=sel_tools,
                           sel_tool_index=sel_tool_index,
                           sel_var_ls=sel_vars_of_tool)

            reset_var_buttons()

        def label_of_var_row(tool_code: str = None,
                             batch_vars=None):
            if self.debug:
                debug_ls = [15, f'label_of_var_row()',
                            f'tool_code = {tool_code}',
                            f'batch_vars = {batch_vars}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(debug_ls)

            var_trans_dict = get_var_translation_dict()

            if isinstance(batch_vars, str):
                # the case 'all'
                label_ls = ['All variables']
            elif tool_code != 'multi_plot':
                # the case of list of var-lists
                label_ls = [var_name for x in batch_vars for var_name in
                            var_trans_dict.keys() if
                            var_trans_dict[var_name] == x]
            else:
                # the case of list of axes and var-lists
                label_ls = [var_name for x in batch_vars for y in x[1] for
                            var_name in
                            var_trans_dict.keys() if
                            var_trans_dict[var_name] == y]

            return ', '.join(label_ls)

        def set_selections(sel_tool_ls: list,
                           sel_tool_index: int = -1,
                           sel_var_ls: list = None):
            # Sometimes we want to set the index to None,
            # this is why we have default value -1.
            if self.debug:
                debug_ls = [16, f'set_selections()',
                            f'sel_tool_ls = {sel_tool_ls}',
                            f'sel_tool_index = {sel_tool_index}',
                            f'sel_var_ls = {sel_var_ls}']
                debug_value(debug_ls)

            rows = ((3 + len(sel_tool_ls)) // 2) * 2

            selected_tools.unobserve(changed_selected_tool, names='value')
            selected_tools.options = sel_tool_ls
            if isinstance(sel_tool_index, int) and sel_tool_index >= 0:
                selected_tools.value = sel_tool_index
            elif sel_tool_index is None:
                selected_tools.value = sel_tool_index
            selected_tools.observe(changed_selected_tool, names='value')
            selected_tools.rows = rows
            if isinstance(sel_var_ls, list):
                selected_vars.options = sel_var_ls
            selected_vars.rows = rows

        def changed_selected_tool(c):
            if self.debug:
                debug_ls = [112, f'changed_selected_tool()',
                            f'c.old = {c.old}',
                            f'c.new = {c.new}']
                debug_value(debug_ls)
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print('changed_selected_tool()\t c=', c)

            # Clean up the selection_var widget
            ### TODO Use Upd_dict instead.
            if ('', (c.old, [])) in selected_vars.options:
                tool_ls = list(selected_tools.options)
                sel_vars = list(selected_vars.options)
                sel_vars.remove(('', (c.old, [])))
                tool_ls.pop(c.old)
                tool_ls = [(t[0], tool_ls.index(t)) for t in tool_ls]
                sel_vars = [(v[0], (sel_vars.index(v), v[1][1])) for v in
                            sel_vars]
                selected_tools.unobserve(changed_selected_tool, names='value')
                selected_tools.options = tool_ls
                selected_vars.options = sel_vars
                if c.new is None:
                    value = None
                elif c.new > c.old:
                    value = c.new - 1
                else:
                    value = c.new
                selected_tools.value = value
                selected_tools.observe(changed_selected_tool, names='value')
            reset_var_buttons()

        def reset_var_buttons():
            tool_index = selected_tools.value
            if self.debug:
                debug_ls = [17, 'reset_var_buttons()',
                            f'  - index of selected_tools = {tool_index}']
            if tool_index is None:
                if self.debug:
                    debug_ls.append('  -- index = None')
                    debug_ls.append('  -- deselecting and disabling all '
                                    'var-buttons and the "Up"-btn')
                move_up.disabled = True
                for btn in var_buttons.children:
                    btn.disabled = True
                    btn.icon = ''
            elif isinstance(tool_index, int):
                if self.debug:
                    debug_ls.append(f'  -- index = {tool_index}')
                move_up.disabled = False
                upd_dict = get_batch_upd_dict()
                row_dict = upd_dict['_tools'][tool_index]
                var_trans_dict = get_var_translation_dict()
                for tool_code, var_codes in row_dict.items():
                    if self.debug:
                        debug_ls.append(f'  --- case of tool_code = {tool_code}')
                        debug_ls.append(f'  --- var_codes = {var_codes}')
                    if tool_code == 'multi_plot':
                        if self.debug:
                            debug_ls.append('  ---- Multi-plot can not handle '
                                            'more than 2 units.')
                        # for multi_plot var_codes look like this:
                        # [['%', [['SWC_1', 'ETC NRT Meteo', 'SE-Htm'],
                        #         ['SWC_2', 'ETC NRT Meteo', 'SE-Htm']]],
                        #  ['mmol mol-1', [['H2O', 'ETC NRT Fluxes', 'SE-Htm']]]]
                        var_ls = [v for axis in var_codes for v in axis[1]]
                        unit_ls = [axis[0] for axis in var_codes]
                        for btn in var_buttons.children:
                            if self.debug:
                                debug_ls.append(f'  ----- unit_ls = {unit_ls}')
                                debug_ls.append(f'  ----- btn.tooltip = '
                                                f'{btn.tooltip}')
                            if var_trans_dict[btn.description] in var_ls:
                                btn.icon = 'check'
                                btn.disabled = False
                                if self.debug:
                                    debug_ls.append(f'  ----- Button '
                                                    f'"{btn.description}" '
                                                    f'enabled and checked')
                            elif (len(var_codes) == 2 and
                                  btn.tooltip not in unit_ls) or \
                                    btn.description == 'Select all':
                                btn.icon = ''
                                btn.disabled = True
                                if self.debug:
                                    debug_ls.append(f'  ----- Button '
                                                    f'{btn.description} disabled')

                            else:
                                btn.icon = ''
                                btn.disabled = False
                    elif tool_code == 'corr_plot':
                        if self.debug:
                            debug_ls.append(f'  ---- Corr-plot can only have 2 '
                                            f'vars.')
                        for btn in var_buttons.children:
                            if var_trans_dict[btn.description] in var_codes:
                                btn.icon = 'check'
                                btn.disabled = False
                            elif len(var_codes) == 2 or \
                                    btn.description == 'Select all':
                                btn.icon = ''
                                btn.disabled = True
                            else:
                                btn.icon = ''
                                btn.disabled = False
                    else:
                        if var_codes == 'all':
                            for btn in var_buttons.children:
                                if btn.description == 'Select all':
                                    btn.icon = 'check'
                                    btn.disabled = False
                                else:
                                    btn.icon = ''
                                    btn.disabled = True
                        else:
                            for btn in var_buttons.children:
                                if var_trans_dict[btn.description] in var_codes:
                                    btn.icon = 'check'
                                    btn.disabled = False
                                else:
                                    btn.icon = ''
                                    btn.disabled = False
            if self.debug:
                debug_ls.append('--- end ---')
                debug_value(debug_ls)

        def move_selected(c):
            index = selected_tools.value
            if self.debug:
                debug_ls = [112, f'move_selected()',
                            f'tool index = {index}',
                            f'c.old = {c.old}',
                            f'c.new = {c.new}']
                debug_value(debug_ls)

            if index is None:
                return
            else:
                upd_dict = get_batch_upd_dict()['_tools']
                keys = len(upd_dict.keys())
                if index > 0:
                    new_index = index - 1
                    down_val = upd_dict[index - 1]
                    upd_dict[new_index] = upd_dict[index]
                    upd_dict[index] = down_val
                else:
                    new_index = keys - 1
                    down_val = upd_dict.pop(index)
                    upd_dict = {k - 1: v for k, v in upd_dict.items()}
                    upd_dict[new_index] = down_val

                update_batch_dict(dict(_tools=upd_dict,
                                       _selected_tool_index=new_index))

        def tool_click(tool):
            if self.debug:
                debug_ls = [112, f'tool_click()',
                            f'tool.description = {tool.description}',
                            f'tool.icon = {tool.icon}']
                debug_value(debug_ls)

            if tool.icon:
                tool.style.button_color = "LightGreen"
                tool.icon = ''
                add_tool = False
            else:
                for btn in tool_buttons.children:
                    if btn != tool:
                        btn.style.button_color = "LightGreen"
                        btn.icon = ''
                tool.style.button_color = "Green"
                tool.icon = 'check'
                add_tool = True
            tool_selections(add_tool, tool.description)

        def tool_selections(add_tool,
                            tool_name):
            selection_dict = get_batch_upd_dict()
            # remove empty rows
            tools = cleanup_tools(selection_dict.get('_tools', {}))
            if self.debug:
                debug_ls = [112, f'tool_selections()',
                            f'add_tool = {add_tool}',
                            f'tool_name = {tool_name}',
                            f'selection_dict = {selection_dict}',
                            f'tools (cleaned) ={tools}']
                debug_value(debug_ls)

            if add_tool:
                key = len(tools.keys())
                tools[key] = {name2tool_dict[tool_name]: []}
                selected_tools.disabled = True
            else:
                key = None
                selected_tools.disabled = False

            update_batch_dict(dict(_tools=tools,
                                   _selected_tool_index=key))

        def var_button_click(btn):

            if self.debug:
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print('var_button_click(btn)')
            upd_dict = get_batch_upd_dict()['_tools']
            row_index = selected_tools.value
            if self.debug:
                debug_ls = [112, f'var_button_click()',
                            f'btn.description = {btn.description}',
                            f'row_index = {row_index}',
                            f'before:'
                            f' - upd_dict[row_index] = {upd_dict[row_index]}']
                debug_value(debug_ls)

            for tool_code, selected_var_codes in upd_dict[row_index].items():
                var_trans_dict = get_var_translation_dict()
                var_name = btn.description
                var_code = var_trans_dict[var_name]
                if var_code == 'All variables':
                    if selected_var_codes != 'all':
                        selected_var_codes = 'all'
                    else:
                        selected_var_codes = []
                elif tool_code != 'multi_plot':
                    if var_code in selected_var_codes:
                        selected_var_codes.remove(var_code)
                    else:
                        selected_var_codes.append(var_code)
                elif tool_code == 'multi_plot':
                    unit = var2unit(var_code)
                    axis_of_var = None
                    for v in selected_var_codes:
                        if v[0] == unit:
                            axis_of_var = v
                            if var_code in v[1]:
                                v[1].remove(var_code)
                            else:
                                v[1].append(var_code)
                    if axis_of_var is None:
                        selected_var_codes.append((unit, [var_code]))
                    elif len(axis_of_var[1]) == 0:
                        selected_var_codes.remove(axis_of_var)
                upd_dict[row_index] = {tool_code: selected_var_codes}
                if self.debug:
                    debug_ls = [112, f'var_button_click()',
                                f'after:',
                                f' - upd_dict[row_index] = {upd_dict[row_index]}']
                    debug_value(debug_ls)

                update_batch_dict(dict(_tools=upd_dict,
                                       _selected_tool_index=row_index))

        def selections2batch_dict() -> dict:
            if self.debug:
                debug_ls = [112, f'selections2batch_dict()']
                debug_value(debug_ls)

            d = dict()
            t_ls = selected_tools.options
            v_ls = [v[1][1] for v in selected_vars.options]
            ind = range(len(t_ls))
            d['_tools'] = {k: {name2tool_dict[t_ls[k][0]]: v_ls[k]} for k in ind}
            d['_selected_tool_index'] = selected_tools.index
            return d

        def var2unit(var):
            if self.debug:
                debug_ls = [8, f'var2unit()',
                            f'var = {var}']
                debug_value(debug_ls)

            app_configs = self._load_app_configs()
            var2unit_dict = app_configs['_var2unit_map']
            update_var2units = False

            if isinstance(var2unit_dict, dict):
                if var[0] not in var2unit_dict.keys():
                    update_var2units = True
            else:
                update_var2units = True

            if update_var2units:
                pid = st_df.loc[(st_df.id == var[-1]) & (
                        st_df.specLabel == var[1])].dobj.values[0]
                do = Dobj(pid)
                meta = IcosFrame.trim_icos_meta(do.meta)
                var_unit_list = meta['varUnitList']
                var2unit_dict.update({v[0]: v[1] for v in var_unit_list})
                app_configs['_var2unit_map'].update(var2unit_dict)
                self._set_app_configs(app_dict=app_configs)
            if self.debug:
                debug_ls = [8, f'var2unit()',
                            f' - return unit = {var2unit_dict[var[0]]}']
                debug_value(debug_ls)
            return var2unit_dict[var[0]]

        def set_group_var_info():
            cache = self._load_cache()
            if self.debug:
                debug_ls = [4, f'set_group_var_info()']
                debug_value(debug_ls)

            if isinstance(cache, dict):
                grp = group_drop.value
                if grp not in cache['_groups'].keys():
                    # Container title...
                    cont_title = f'Content of a group goes here'
                    g_vars.set_title(0, cont_title)
                    group_vars.value = '<b>Variables: </b>'
                    return

                # Generate HTML-text for the variables
                var_text = get_group_var_info_text(upd_mode=False)

                # Container title...
                cont_title = f'Content of group {grp}'
                g_vars.set_title(0, cont_title)
                group_vars.value = var_text
            else:
                # No cache,
                cont_title = f'Content of a group goes here'
                g_vars.set_title(0, cont_title)
                group_vars.value = 'Variables: '

        def get_group_var_info_text(upd_mode):
            cache = self._load_cache()
            if self.debug:
                debug_ls = [5, f'get_group_var_info_text()']
                debug_value(debug_ls)

            grp = group_drop.value
            if grp not in cache['_groups'].keys():
                return_val = ''
            else:
                var_tuples = cache['_groups'][grp]['_group_vars']
                var_ls = [v[0] for v in var_tuples]
                text_tag = 'b'
                separator = '<br>'
                margin = '&nbsp' * 10
                station_dict = _var_tup2station_dict(var_tuples)

                # We loop over stations and products to concatenate
                # a proper text in html
                t1 = f'<{text_tag}>Variables: </{text_tag}>'
                t2 = ', '.join(var_ls)
                t3 = ''
                if upd_mode and len(t1 + t2) > 100:
                    t2 += '<br>'
                    first_break = 0
                else:
                    first_break = 1

                one_stn = (len(station_dict.keys()) == 1)
                for stn in station_dict.keys():
                    if one_stn:
                        t1 = f'<{text_tag}>Variables (of {stn}): </{text_tag}>'
                        one_prod = (len(station_dict[stn].keys()) == 1)
                        for prod in station_dict[stn].keys():
                            if one_prod:
                                t1 = f'<{text_tag}>Variables (of {prod} at {stn}): </{text_tag}>'
                            else:
                                t3 += f'{separator}{margin}<{text_tag}>{prod}: </{text_tag}>' + \
                                      ", ".join(station_dict[stn][prod])
                                if not upd_mode:
                                    t3 += f'{separator}'
                            if upd_mode and len(t3) + len(
                                    t1 + t2) * first_break > 100:
                                first_break = 0
                                t3 += '<br>'
                    else:
                        t3 += f'{separator}{margin}<{text_tag}>Station {stn}</{text_tag}> '
                        for prod in station_dict[stn].keys():
                            t3 += f'{separator}{margin}<{text_tag}>{prod}: </{text_tag}>'
                            t3 += ", ".join(station_dict[stn][prod])
                        if upd_mode:
                            if len(t3) + len(t1 + t2) * first_break > 100:
                                t3 += '<br>'
                        else:
                            t3 += '<br>'

                if t3:
                    t3 += f'{margin}<i>(In order of appearance)</i>'
                return_val = t1 + t2 + t3
            return return_val

        def debug_value(text_list: list = None):
            global iii
            iii += 1

            if isinstance(text_list, str):
                text_list = [99, '-- start --', text_list]

            margin = '&nbsp' * 6  # html space
            color_num = text_list[0]
            r_col = (41 * color_num) % 200
            g_col = (101 * color_num) % 177
            b_col = (137 * color_num) % 151
            debug_instance = f'<b>{text_list[0]} - {text_list[1]}' \
                             f' -- iii ={iii} --</b>'
            msg = f'<span style="color:rgb({r_col}, {g_col}, {b_col})"; ' \
                  f'"font-size:12.0pt">'
            msg += f'{margin} - {debug_instance} {margin}</span>'
            msg += f'<span style="color:rgb({r_col}, {g_col}, {b_col})"; ' \
                   f'"font-size:10.0pt">'
            row_label = f'<br>{margin} -- {debug_instance} {margin} -- '
            msg += f'{row_label}'.join(text_list[2:])
            msg += '</span>'
            with debug_out:
                display(wd.HTML(msg))

        def html_msg(text: str = None, text_ls: list = None,
                     title: str = None,
                     error: bool = None):
            if self.debug:
                debug_ls = [112, f'html_msg()']
                debug_value(debug_ls)

            margin = '&nbsp' * 6  # html space
            if isinstance(text, str):
                if isinstance(text_ls, list):
                    text_ls.insert(0, text)
                else:
                    text_ls = [text]

            if error:
                msg_title = 'Things to fix: '
                color = self.ipyw_style_colors['danger:active']
                emoji = '\u26a0\ufe0f'  # warning_emoji
            elif title:
                msg_title = title
                color = self.ipyw_style_colors['info:active']
                emoji = ''
            else:
                msg_title = 'Info: '
                color = self.ipyw_style_colors['info:active']
                emoji = ''

            msg = f'<span style="color:{color}">'
            msg += f'{margin}<h3>{msg_title} {emoji}</h3>'
            if isinstance(text_ls, list):
                msg += f'<h3>{margin}'
                msg += f'<br>{margin}'.join(text_ls)
                msg += '</h3></span>'
            with out:
                clear_output()
                display(wd.HTML(msg))

        def html_error_msg(error_ls: list = None):
            if self.debug:
                debug_ls = [112, f'html_error_msg()']
                debug_value(debug_ls)
            html_msg(text_ls=error_ls, error=True)

        def cleanup_tools(d: dict):
            if self.debug:
                debug_ls = [112, f'cleanup_tools()',
                            f'd (before) = {d}']
                debug_value(debug_ls)
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print(f'cleanup_tools() \n\td = {d}')

            if isinstance(d, dict):
                d_copy = d.copy()
                for tool_number, tool_var in d_copy.items():
                    for t_name in tool_var.keys():
                        if not tool_var[t_name]:
                            d.pop(tool_number)
                        elif t_name == 'corr_plot' and len(tool_var[t_name]) != 2:
                            d.pop(tool_number)
                # reset the tool number
                d = dict(zip(range(len(d.keys())), d.values()))
            if self.debug:
                debug_ls = [112, f'cleanup_tools()',
                            f'd (after) = {d}']
                debug_value(debug_ls)
            return d

        def validate_name(name):
            cache = self._load_cache()
            grp = group_drop.value
            error_ls = []
            if not name or name == 'Name of batch job':
                error_ls.append('Please choose a name for batch job')
            elif not name[0].isalnum():
                error_ls.append('At least the first letter of the name')
                error_ls.append('must be an alfa numeric character.')
            elif grp in cache['_groups'].keys():
                batches = cache['_groups'][grp].get('_batches', {})
                if name in batches.keys():
                    upd_dict = get_batch_upd_dict()
                    if name != upd_dict['_orig_name']:
                        error_ls.append(
                            f'There is already a batch job called <it'
                            f'>{name}</i>,')
                        error_ls.append('please pick another name.')

            if error_ls:
                name_of_batch_job.style.text_color = 'red'
            else:
                name_of_batch_job.style.text_color = 'darkgreen'
                name_of_batch_job.layout = _get_layout(name)

            if self.debug:
                debug_ls = [112, f'validate_name()',
                            f'name = {name}',
                            f'error_ls = {error_ls}']
                debug_value(debug_ls)

            return error_ls

        def batch_name_changed(change):

            if self.debug:
                debug_ls = [112, f'validate_name()',
                            f'change = {change}']
                debug_value(debug_ls)
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print('batch_name_changed()\t', change)

            if change.type == 'change':
                new_name = change.owner.value
                error_ls = validate_name(new_name)
                upd_dict = {}

                if error_ls:
                    if self.debug:
                        iii += 1
                        print(f'\n\t -- iii ={iii} --')
                        print(f'batch_name_changed()\t error_ls={error_ls}')
                    upd_dict['_name_error'] = error_ls
                else:
                    if self.debug:
                        iii += 1
                        print(f'\n\t -- iii ={iii} --')
                        print(f'batch_name_changed()\t new_name={new_name}')
                    upd_dict['_new_name'] = new_name
                if self.debug:
                    iii += 1
                    print(f'\n\t -- iii ={iii} --')
                    print(111144444, 'batch_name_changed()\t', batch_drop.value)
                update_batch_dict(upd_dict)

        def get_var_translation_dict() -> dict:
            if self.debug:
                debug_ls = [7, f'get_var_translation_dict()']
                debug_value(debug_ls)

            return eval(var_translation_dict.value)

        def get_batch_upd_dict() -> dict:
            if self.debug:
                debug_ls = [14, f'get_batch_upd_dict()']
                debug_value(debug_ls)
            d = eval(upd_dict_log.value)

            if isinstance(d, dict):
                if '_tools' in d.keys():
                    d['_tools'] = {int(k): v for k, v in d['_tools'].items()}
            else:
                d = dict()
            return d

        def set_batch_upd_dict(d: dict):
            if self.debug:
                debug_ls = [12, 'set_batch_upd_dict()', 'step 1', f'd ={d}']
                debug_value(debug_ls)

            json_safe_dict = {k: v for k, v in d.items() if k != '_tools'}
            json_safe_dict['_tools'] = {str(k): v for k, v in d['_tools'].items()}

            upd_dict_log.value = str(json_safe_dict)
            if self.debug:
                debug_ls = [12, 'set_batch_upd_dict()', 'step 2',
                            f'upd_dict_log.value ={upd_dict_log.value}']
                debug_value(debug_ls)

        def update_batch_dict(d: dict = None):
            if self.debug:
                debug_ls = [112, f'update_batch_dict()',
                            f'd = {d}']
                debug_value(debug_ls)
            upd_dict = get_batch_upd_dict()
            for k, v in d.items():
                upd_dict[k] = v
            set_batch_upd_dict(upd_dict)

        def set_batch_upd_selections(d: dict = None):

            if self.debug:
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print('set_batch_upd_selections()')
                print(f'\tinput_param d = {d}')

            if d is None:
                d = selections2batch_dict()
                if self.debug:
                    iii += 1
                    print(f'\n\t -- iii ={iii} --')
                    print(f'\tafter selections2batch_dict d = {d}')

            upd_dict = get_batch_upd_dict()
            if self.debug:
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print(f'\tupd_dict = {upd_dict}')

            upd_dict['_tools'] = {str(k): v for k, v in d['_tools'].items()}
            upd_dict['_selected_tool_index'] = d.get('_selected_tool_index', -1)
            if self.debug:
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print(f'\tupd_dict = {upd_dict}')
            set_batch_upd_dict(upd_dict)

        def new_batch(c):
            if self.debug:
                debug_ls = [112, f'new_batch()']
                debug_value(debug_ls)
            set_batch_upd_dict({'_version': 0,
                                '_orig_name': '',
                                '_new_name': '',
                                '_tools': {},
                                '_selected_tool_index': None})
            name_of_batch_job.value = "Name of batch job"
            activate_gui('new')

        def update_batch(c):
            if self.debug:
                debug_ls = [112, f'update_batch()',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(debug_ls)

            if self.debug:
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print('update_batch() ', batch_drop.label, batch_drop.value,
                      type(batch_drop.value))
            batch_upd = dict()
            stored_batch = batch_drop.value.copy()
            batch_upd['_version'] = int(stored_batch.pop('_version', 1))
            batch_upd['_tools'] = stored_batch
            batch_upd['_orig_name'] = batch_drop.label
            batch_upd['_new_name'] = batch_drop.label
            batch_upd['_selected_tool_index'] = None
            name_of_batch_job.value = batch_drop.label
            set_batch_upd_dict(batch_upd)
            activate_gui('update')

        def save_batch(c):
            # Note: Avoid using `get_upd_dict()` here, some keys are
            # integers which is not "json-safe" of some reason.
            # The keys stored in  `upd_dict_log.value` are strings.
            upd_dict = eval(upd_dict_log.value)
            b_name = upd_dict['_new_name']
            grp = group_drop.value
            cache = self._load_cache()
            batches = cache['_groups'][grp].get('_batches', {})

            if self.debug:
                debug_ls = [20, 'save_batch()', f'upd_dict = {upd_dict}']
                debug_value(debug_ls)
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')

            error_ls = validate_name(b_name)
            tool_dict = cleanup_tools(upd_dict.get('_tools', {}))

            if not tool_dict:
                error_ls.append('Please choose some tool and variables.')

            if error_ls:
                html_error_msg(error_ls)
            else:
                with out:
                    clear_output()

                config = tool_dict
                config['_version'] = str(int(upd_dict['_version']) + 1)

                old_batch = upd_dict['_orig_name']
                batches.pop(old_batch, None)
                batches[b_name] = config
                if self.debug:
                    debug_ls = [20, 'save_batch()', f'batches = {batches}']
                    debug_value(debug_ls)

                cache['_groups'][grp]['_batches'] = batches
                self._set_cache(cache_dict=cache)
                init(grp, b_name)
                activate_gui('save')

        def cancel_batch(c):
            if self.debug:
                debug_ls = [112, 'cancel_batch()']
                debug_value(debug_ls)

            activate_gui('cancel')

        def delete_batch(c):
            if self.debug:
                debug_ls = [112, 'delete_batch()']
                debug_value(debug_ls)

            upd_dict = eval(upd_dict_log.value)
            orig_tools = batch_drop.value.copy()
            orig_tools.pop('_version', None)

            b_name = upd_dict['_new_name']

            if self.debug:
                global iii
                iii += 1
                print(f'\n\t -- iii ={iii} --')
                print(f'delete_batch()\n\tb_name = {b_name}')
                print(f'\tbatch_drop.label = {batch_drop.label}')

            error_ls = []
            if upd_dict['_orig_name'] != b_name:
                error_ls.append('  - Name changed')
            if upd_dict['_tools'] != orig_tools:
                error_ls.append('  - Change of tools or variables')
            if error_ls:
                error_ls.insert(0, 'Deletion error:')
                error_ls.insert(1, 'To delete a batch job, just choose '
                                   'update and then delete - without '
                                   'changing it\'s content.')
                error_ls.insert(-1, 'Suggestion to delete: Press Cancel, '
                                    'Update and '
                                    'Delete')
                html_msg(text_ls=error_ls, error=True)
                if self.debug:
                    iii += 1
                    print(f'\n\t -- iii ={iii} --')
                    print('delete_batch()\n\t --error-- ', error_ls)
                    print('orig_tools: ', orig_tools)
                    print("upd_dict['_tools']: ", upd_dict['_tools'])

                return
            else:
                grp = group_drop.value
                cache = self._load_cache()
                batches = cache['_groups'][grp].get('_batches', {})
                batches.pop(b_name, None)
                cache['_groups'][grp]['_batches'] = batches

                self._set_cache(cache_dict=cache)

                if self.debug:
                    iii += 1
                    print(f'\n\t -- iii ={iii} --')
                    print('delete_batch()\n\t deleted:', b_name)
                init(grp)
                activate_gui('delete')

            # activate/deactivate upd-widgets

        def activate_gui(upd_active: str):
            if self.debug:
                debug_ls = [10, 'activate_gui()',
                            f'upd_active = {upd_active}']
                debug_value(debug_ls)

            def set_state(wd_input,
                          disable: bool = None,
                          tooltip: str = None,
                          show_widget: bool = None):

                if isinstance(wd_input, wd.Widget):
                    if show_widget is not None and 'layout' in wd_input.keys:
                        if 'display' in wd_input.layout.keys:
                            if show_widget:
                                wd_input.layout.display = 'block'
                            else:
                                wd_input.layout.display = 'none'
                            show_widget = None

                    if {disable, tooltip, show_widget} != {None}:
                        if 'children' in wd_input.keys:
                            for w in wd_input.children:
                                set_state(w, disable, tooltip, show_widget)
                        else:
                            if disable is not None and 'disabled' in wd_input.keys:
                                wd_input.disabled = disable
                            if tooltip is not None and 'tooltip' in wd_input.keys:
                                wd_input.tooltip = tooltip
                elif isinstance(wd_input, list):
                    for w in wd_input:
                        set_state(w, disable, tooltip, show_widget)

            with out:
                clear_output()
            update_enable_list = [selected_tools]
            update_disable_list = [group_drop, batch_drop]
            update_display_list = [name_of_batch_job, tool_row, var_row, move_up]

            if any(tool_buttons.children):
                for tool in tool_buttons.children:
                    tool.icon = ''
                    tool.style.button_color = 'LightGreen'
            else:
                init_tool_buttons()

            if upd_active in ['new', 'update']:
                # update mode
                # init update widgets..
                #        set_info_msg()

                # turn observers on/off
                upd_btn.on_click(update_batch, remove=True)
                new_btn.on_click(new_batch, remove=True)
                save_btn.on_click(save_batch, remove=False)
                delete_btn.on_click(delete_batch, remove=False)
                cancel_btn.on_click(cancel_batch, remove=False)

                name_of_batch_job.observe(batch_name_changed, 'value')
                try:
                    group_drop.unobserve(changed_group_drop, names='value')
                except ValueError:
                    pass
                try:
                    batch_drop.unobserve(changed_batch_drop, names='value')
                except ValueError:
                    pass

                set_state(update_enable_list, disable=False)
                set_state(update_disable_list, disable=True)
                set_state(update_display_list, show_widget=True)

                # help_btn.on_click(display_user_guide, remove=False)
                set_state(create_buttons, disable=True,
                          tooltip='Disabled in update mode...')
                set_state(save_btn, disable=False, tooltip='Save settings...')
                set_state(cancel_btn, disable=False, tooltip='Cancel...')

                # help_btn.disabled = False
                if upd_active == 'update':
                    delete_btn.disabled = False
                    delete_btn.tooltip = 'Delete...'
                else:
                    selected_tools.value = None
                    selected_tools.options = []
                    selected_vars.value = None
                    delete_btn.disabled = True
                    delete_btn.tooltip = 'Delete...'
            elif upd_active == 'changed_group_drop':
                # read mode
                if batch_drop.value is None or isinstance(batch_drop.value, int):
                    upd_btn.on_click(update_batch, remove=True)
                    set_state(upd_btn, disable=True)
                else:
                    changed_batch_drop('init')
                    set_state(upd_btn, disable=False)
                    upd_btn.on_click(update_batch, remove=False)
            else:
                # read mode
                if upd_active != 'init':
                    with out:
                        clear_output()

                if batch_drop.value is None or isinstance(batch_drop.value, int):
                    upd_btn.on_click(update_batch, remove=True)
                    set_state(upd_btn, disable=True)
                else:
                    changed_batch_drop('init')
                    set_state(upd_btn, disable=False)
                    upd_btn.on_click(update_batch, remove=False)

                # reset update interaction widgets
                # turn observers on/off
                new_btn.on_click(new_batch, remove=False)
                save_btn.on_click(save_batch, remove=True)
                delete_btn.on_click(delete_batch, remove=True)
                cancel_btn.on_click(cancel_batch, remove=True)
                group_drop.observe(changed_group_drop, names='value')
                batch_drop.observe(changed_batch_drop, names='value')

                try:
                    name_of_batch_job.unobserve(batch_name_changed, 'value')
                except ValueError:
                    pass

                set_state(update_enable_list, disable=True)
                set_state(update_disable_list, disable=False)
                set_state(update_display_list, show_widget=False)

                # upd_dict_log.value = '{}'
                set_state(new_btn, disable=False)

                new_btn.tooltip = 'New batch job...'
                upd_btn.tooltip = 'Update batch job...'
                #        help_btn.disabled = False
                set_state(save_buttons, disable=True,
                          tooltip='Enabled in update mode...')

        st_df = self.stations_df

        # Static lookup dictionary for tools
        tool2name_dict = {'split_plot': 'Split-plot',
                          'multi_plot': 'Multi-plot',
                          'corr_plot': 'Correlation plot (2 vars)',
                          'corr_table': 'Correlation table',
                          'statistics': 'Numerical Statistics'}
        name2tool_dict = {v: k for k, v in tool2name_dict.items()}

        # Widgets
        # Control widgets:
        # - var_translation_dict
        #   maps button names to a variable of the group
        # - upd_dict_log
        #   keeps track on updates of the batch job
        var_translation_dict = wd.Textarea(disabled=True)
        upd_dict_log = wd.Textarea(value='{}',
                                   disabled=True)
        upd_dict_log.observe(reset_selection, names='value')

        # layouts
        drop_layout = wd.Layout(width='auto',
                                height='40px')
        var_txt_layout = wd.Layout(width='99%',
                                   height='100%')
        full_layout = wd.Layout(width='100%',
                                height='100%')
        flex_layout = wd.Layout(width='100%',
                                display='inline-flex',
                                flex_flow='row wrap',
                                align_content='flex-start')
        label_layout = wd.Layout(min_width='125px')

        # 1:st row
        group_drop = wd.Dropdown(layout=drop_layout)
        batch_drop = wd.Dropdown(layout=drop_layout)
        group_vars = wd.HTML(layout=var_txt_layout,
                             value='Variables: ',
                             disabled=True)
        g_vars = wd.Accordion([group_vars],
                              titles=(group_vars.value, '0'),
                              selected_index=None,
                              layout=full_layout)
        row_list = [wd.HBox([group_drop, batch_drop, g_vars],
                            layout=full_layout)]

        # 2:nd row update-buttons
        new_btn = wd.Button(description='New',
                            icon='plus',
                            button_style='primary')
        upd_btn = wd.Button(description='Update',
                            icon='pen',
                            button_style='info')
        save_btn = wd.Button(description='Save',
                             icon='save',
                             button_style='success')
        cancel_btn = wd.Button(description='Cancel',
                               icon='ban',
                               button_style='info')
        delete_btn = wd.Button(description='Delete',
                               icon='trash',
                               button_style='danger')
        create_buttons = wd.HBox([new_btn, upd_btn])
        save_buttons = wd.HBox([save_btn, cancel_btn, delete_btn])
        row_list.append(wd.HBox([create_buttons, save_buttons],
                                layout=flex_layout))

        # 3:rd row. update section: Batch name
        name_of_batch_job = wd.Text(value='Name of batch job',
                                    layout=_get_layout('Name of batch job'))
        row_list.append(name_of_batch_job)

        # 4:rd row. update section: Tools
        tool_label = wd.HTML('<b><i>Available tools: </i></b>',
                             layout=label_layout)
        tool_buttons = wd.HBox()
        tool_row = wd.HBox([tool_label, tool_buttons])
        row_list.append(tool_row)

        # 5:rd row. update section: Vars
        var_label = wd.HTML('<b><i>Available variables: </i></b>',
                            layout=label_layout)
        var_buttons = wd.HBox(layout=flex_layout)
        var_row = wd.HBox([var_label, var_buttons])
        row_list.append(var_row)

        # 6:rd row. update section: Selections
        selection_label = wd.HTML('<b><i>Current setup: </i></b>',
                                  layout=label_layout)
        selected_tools_tooltip = """The tools are listed in order of """ \
                                 """execution.\n - New tools are inserted """ \
                                 """above selected row, \nor below all if """ \
                                 """none is selected."""
        selected_tools = wd.Select(disabled=False,
                                   layout=wd.Layout(max_width='150px'),
                                   tooltip=selected_tools_tooltip)
        selected_tools.observe(changed_selected_tool, names='value')

        move_up = wd.Button(description='Up',
                            disabled=False,
                            icon='arrow-up',
                            tooltip='Move selected tool...',
                            layout=wd.Layout(width='60px'))
        move_up.on_click(move_selected)
        selected_vars = wd.Select(disabled=True,
                                  layout=wd.Layout(max_width='80%'))

        left_selection_box = wd.VBox([selection_label, move_up],
                                     layout=label_layout)
        row_list.append(wd.HBox([left_selection_box,
                                 selected_tools,
                                 selected_vars]))

        out = wd.Output()
        debug_out = wd.Output()

        # load_data()
        if not init():
            display(out)
            if self.debug:
                display(debug_out)
            # init returns error text if there are no variable groups
            return out

        row_list.append(out)
        if self.debug:
            row_list.append(debug_out)

        return_widget = wd.VBox(row_list)

        return return_widget

    def _user_configurations(self):
        if self.debug:
            print('*** _user_configurations()\n')

        def init_general_settings():
            # set general values
            settings = self._load_user_settings()

            time_configs = settings.get('time_configs', {})
            latex_kwargs = settings.get('latex_kwargs', {})
            split_plot_kwargs = settings.get('split_plot_kwargs', {})
            multi_plot_kwargs = settings.get('multi_plot_kwargs', {})
            corr_plot_kwargs = settings.get('corr_plot_kwargs', {})
            corr_table_kwargs = settings.get('corr_table_kwargs', {})
            statistics_kwargs = settings.get('statistics_kwargs', {})

            latex_font.value = latex_kwargs.get('font_style', 'rm')
            latex_size.value = latex_kwargs.get('font_size', 8)
            latex_use_exp_cb.value = latex_kwargs.get('use_exp', False)
            latex_changed(0)

            split_p_zoom_sliders.value = split_plot_kwargs.get('zoom_sliders', 2)
            split_p_use_latex_cb.value = split_plot_kwargs.get('use_latex', True)
            split_p_height.value = split_plot_kwargs.get('height', 0)
            split_p_width.value = split_plot_kwargs.get('width', 0)
            split_p_title_font.value = split_plot_kwargs.get('title_font',
                                                             plotly_fonts[0])
            split_p_title_size.value = split_plot_kwargs.get('title_size',
                                                             'Default')
            split_p_subtitle_size.value = split_plot_kwargs.get('subtitle_size',
                                                                'Default')

            multi_p_use_latex_cb.value = multi_plot_kwargs.get('use_latex', True)
            multi_p_height.value = multi_plot_kwargs.get('height', 0)
            multi_p_width.value = multi_plot_kwargs.get('width', 0)

            corr_p_use_latex_cb.value = corr_plot_kwargs.get('use_latex', True)
            corr_p_height.value = corr_plot_kwargs.get('height', 0)
            corr_p_width.value = corr_plot_kwargs.get('width', 0)

            time_end_date.value = time_configs.get('end_date', 0)
            time_start_date.value = time_configs.get('start_date', 10)
            time_fetch_date.value = time_configs.get('fetch_date', 6)

            for w in observe_latex:
                w.observe(latex_changed, names='value')

            for w in observe_ordinary_ls:
                w.observe(settings_changed, names='value')

            for w in observe_pos_ls:
                w.observe(positive, names='value')
            for w in observe_height_width_ls:
                w.observe(height_or_width_changed, names='value')

            cancel_btn.disabled = True
            save_btn.disabled = True

        def latex_changed(c):
            latex = icos2latex.Translator(use_exp=latex_use_exp_cb.value,
                                          font_size=latex_size.value,
                                          font_style=latex_font.value)
            var_unit = ("CO2", "\u00b5mol mol-1")
            latex_text2.value = '$\qquad \qquad \qquad$' + \
                                latex.var_unit_to_latex(var_unit=var_unit)

        def settings_changed(c):
            cancel_btn.disabled = False
            save_btn.disabled = False

        def height_or_width_changed(c):
            if c.new < 200:
                c.owner.value = 0
            else:
                settings_changed(c)

        def positive(c):
            if c.new < 0:
                c.owner.value = 0
            else:
                settings_changed(c)

        def save_general_settings(c):

            upd_dict = {'time_configs': {'start_date': time_start_date.value,
                                         'end_date': time_end_date.value,
                                         'fetch_date': time_fetch_date.value},
                        'latex_kwargs':
                            {'font_style': latex_font.value,
                             'font_size': latex_size.value,
                             'use_exp': latex_use_exp_cb.value},
                        'split_plot_kwargs':
                            {'zoom_sliders': split_p_zoom_sliders.value,
                             'use_latex': split_p_use_latex_cb.value,
                             'template': split_p_plotly_templates.value,
                             'width': split_p_width.value,
                             'height': split_p_height.value},
                        'multi_plot_kwargs':
                            {'use_latex': multi_p_use_latex_cb.value,
                             'template': multi_p_plotly_templates.value,
                             'width': multi_p_width.value,
                             'height': multi_p_height.value},
                        'corr_plot_kwargs':
                            {'use_latex': corr_p_use_latex_cb.value,
                             'template': corr_p_plotly_templates.value,
                             'color_scale': corr_p_color_scale_drop.value,
                             'width': corr_p_width.value,
                             'height': corr_p_height.value},
                        'corr_table_kwargs':
                            {'use_latex': True,
                             'width': 0,
                             'height': 0},
                        'statistics_kwargs': {}
                        }

            self.report_writer = None
            json_handler.update(data_piece=upd_dict,
                                json_file=self.user_config_file,
                                settings_dir=self.settings_dir)
            init_general_settings()

        def cancel_general_settings(c):
            init_general_settings()

        # plotly color-scales
        plotly_color_scales = ['aggrnyl', 'agsunset', 'blackbody', 'bluered',
                               'blues', 'blugrn', 'bluyl', 'brwnyl', 'bugn',
                               'bupu', 'burg', 'burgyl', 'cividis',
                               'darkmint', 'electric', 'emrld', 'gnbu',
                               'greens', 'greys', 'hot', 'inferno', 'jet',
                               'magenta', 'magma', 'mint', 'orrd', 'oranges',
                               'oryel', 'peach', 'pinkyl', 'plasma',
                               'plotly3', 'pubu', 'pubugn', 'purd',
                               'purp', 'purples', 'purpor', 'rainbow',
                               'rdbu', 'rdpu', 'redor', 'reds', 'sunset',
                               'sunsetdark', 'teal', 'tealgrn', 'turbo',
                               'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
                               'ylorrd', 'algae', 'amp', 'deep', 'dense',
                               'gray', 'haline', 'ice', 'matter', 'solar',
                               'speed', 'tempo', 'thermal', 'turbid',
                               'armyrose', 'brbg', 'earth', 'fall', 'geyser',
                               'prgn', 'piyg', 'picnic', 'portland',
                               'puor', 'rdgy', 'rdylbu', 'rdylgn',
                               'spectral', 'tealrose', 'temps', 'tropic',
                               'balance', 'curl', 'delta', 'oxy', 'edge',
                               'hsv', 'icefire', 'phase', 'twilight',
                               'mrybm', 'mygbm']
        plotly_templates = ['plotly', 'plotly_white', 'plotly_dark',
                            'ggplot2', 'seaborn', 'simple_white', 'none']
        plotly_fonts = ["Arial", "Balto", "Courier New", "Droid Sans",
                        "Droid Serif", "Droid Sans Mono", "Gravitas One",
                        "Old Standard TT", "Open Sans", "Overpass",
                        "PT Sans Narrow", "Raleway", "Times New Roman"]
        plotly_sizes = ['Default', 6, 8, 10, 11, 12, 14, 17]

        # widgets
        drop_layout = wd.Layout(width='55px')
        save_btn = wd.Button(description='Save',
                             icon='save',
                             button_style='danger')
        cancel_btn = wd.Button(description='cancel',
                               icon='cancel',
                               button_style='info')
        save_btn.on_click(save_general_settings)
        cancel_btn.on_click(cancel_general_settings)
        save_cancel_box = wd.HBox([save_btn,
                                   cancel_btn])
        observe_ordinary_ls = []
        observe_pos_ls = []
        observe_height_width_ls = []

        time_start_end_date_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                                  'Plots and statistics are '
                                                  'based on values measured '
                                                  'between the <b>start</b> '
                                                  'and <b>end dates</b>, '
                                                  'displayed in the <b>Start</b> '
                                                  'menu. </span> <br>'
                                                  'These dates can be changed '
                                                  'within each run, however '
                                                  'their default values are '
                                                  'calculated using the below '
                                                  'methods.')
        time_fetch_date_guide = wd.HTML(value='<span>The <b>fetch date</b> '
                                              'is used to <i>speed up '
                                              'computations</i>.</span> '
                                              'In case of a re-calculation based '
                                              'on a longer time series, '
                                              'the data between the fetch and '
                                              'the end date is already in RAM.')
        time_end_date_label = wd.HTML(value='<b>End date =</b> The number '
                                            'of days <i>before</i> today:')
        time_end_date = wd.IntText(layout=drop_layout)
        time_end_date_box = wd.HBox([time_end_date_label,
                                     time_end_date])

        time_start_date_label = wd.HTML(value='<b>Start date =</b> The number '
                                              'of days <i>before</i> the '
                                              'end date:')
        time_start_date = wd.IntText(layout=drop_layout)
        time_start_date_box = wd.HBox([time_start_date_label,
                                       time_start_date])

        time_fetch_date_label = wd.HTML(value='<b>Fetch date =</b> '
                                              'The number of days '
                                              '<i>before</i> the start date:')
        time_fetch_date = wd.Dropdown(options=range(0, 15),
                                      layout=drop_layout)
        time_fetch_date_box = wd.HBox([time_fetch_date_label,
                                       time_fetch_date])
        time_date_box = wd.HBox([wd.VBox([time_start_end_date_guide,
                                          time_end_date_box,
                                          time_start_date_box,
                                          time_fetch_date_guide,
                                          time_fetch_date_box])
                                 ])
        observe_pos_ls.append(time_end_date)
        observe_pos_ls.append(time_start_date)
        observe_ordinary_ls.append(time_fetch_date)

        time_length_settings = wd.Accordion(children=[time_date_box],
                                            titles=('Length of time series',))

        latex_text1 = wd.HTML('<span><b>Guide:</b><br>'
                              '<b><i>LaTeX settings</i></b> '
                              'applies to the axes of all '
                              'plots.<br>For example, if the plot '
                              'represent CO2-measurements the y-axis will, '
                              'depending on the settings, look '
                              'similar to: </span>')
        latex_text2 = wd.HTMLMath('$\qquad \qquad \qquad$' +
                                  '$ {CO_2}\\ (\\mu{mol}/{mol})$ ')
        latex_text3 = wd.HTML('When <b><i>Keep exponents</i></b> deselected '
                              'negative exponents in units will be '
                              'converted into fractions.')
        latex_use_exp_label = wd.HTML('<b>Keep exponents: </b>')
        latex_use_exp_cb = wd.Checkbox(value=True,
                                       disabled=False,
                                       indent=False,
                                       layout=_get_layout('Keep exponents '
                                                          'xxxxx'))
        latex_size = wd.Dropdown(options=[6, 8, 10, 11,
                                          12, 14, 17],
                                 description='Font size',
                                 value=8,
                                 disabled=False,
                                 layout=_get_layout('Font size 2222'))
        latex_font = wd.Dropdown(options=[('Roman (serifs, default)', 'rm'),
                                          ('Sans Serif (no serifs)', 'sf'),
                                          ('Italic (serifs)', 'it'),
                                          ('Typewriter (serifs)', 'tt'),
                                          ('Bold (serifs)', 'bf'),
                                          ('Normal', 'normal')],
                                 description='Font style',
                                 value='rm', disabled=False,
                                 layout=_get_layout('Font style Roman (serifs, '
                                                    'default)'))
        observe_latex = [latex_use_exp_cb, latex_size, latex_font]
        observe_ordinary_ls.extend(observe_latex)

        latex_box = wd.VBox([latex_text1,
                             latex_text2,
                             latex_text3,
                             wd.HBox([wd.VBox([wd.HBox([latex_use_exp_label,
                                                        latex_use_exp_cb])
                                               ]),
                                      wd.VBox([latex_font,
                                               latex_size])
                                      ])
                             ])

        latex_settings = wd.Accordion(children=[latex_box],
                                      titles=('LaTeX settings',))

        split_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         '<b><i>Split plot grouping</i></b> is '
                                         'the number of graphs '
                                         'displayed before the '
                                         'first zoom-slider in a split '
                                         'plot.<br>'
                                         'The <b><i>Height</i></b> and '
                                         '<i><b>Width</i></b> values will be '
                                         'applied for each split plot '
                                         '(values below 200 lead plotly '
                                         'default value).<br>'
                                         '</span>')
        split_p_zoom_sliders_label = wd.HTML(value='<b>Split plot grouping:</b>')
        split_p_zoom_sliders = wd.Dropdown(options=range(1, 10),
                                           layout=drop_layout)

        split_p_zoom_box = wd.HBox([split_p_zoom_sliders_label,
                                    split_p_zoom_sliders])

        split_p_use_latex_label = wd.HTML(value='<b>Use LaTeX:</b>')
        split_p_use_latex_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           tooltip="Applies to the y-axis")
        split_p_latex_box = wd.HBox([split_p_use_latex_label,
                                     split_p_use_latex_cb])

        split_p_plotly_templates_lbl = wd.HTML(value='<b>Plotly templates:</b> ')
        split_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                               value='plotly')
        split_p_plotly_template_box = wd.HBox([split_p_plotly_templates_lbl,
                                               split_p_plotly_templates])

        split_p_height_label = wd.HTML(value='<b>Height:</b>')
        split_p_height = wd.IntText(layout=_get_layout('9999999999'))
        split_p_height_box = wd.HBox([split_p_height_label,
                                      split_p_height])
        split_p_width_label = wd.HTML(value='<b>Width:</b> ')
        split_p_width = wd.IntText(layout=_get_layout('9999999999'))
        split_p_width_box = wd.HBox([split_p_width_label,
                                     split_p_width])
        split_p_title_font_label = wd.HTML(value='<b>Title font:</b> ')
        split_p_title_font = wd.Dropdown(options=plotly_fonts)
        split_p_title_font_box = wd.HBox([split_p_title_font_label,
                                          split_p_title_font])
        split_p_title_size_label = wd.HTML(value='<b>Title size:</b> ')
        split_p_title_size = wd.Dropdown(options=plotly_sizes)
        split_p_title_size_box = wd.HBox([split_p_title_size_label,
                                          split_p_title_size])
        split_p_subtitle_size_label = wd.HTML(value='<b>Subtitle size:</b> ')
        split_p_subtitle_size = wd.Dropdown(options=plotly_sizes)
        split_p_subtitle_size_box = wd.HBox([split_p_subtitle_size_label,
                                             split_p_subtitle_size])

        split_box = wd.VBox([split_plot_guide,
                             wd.HBox([wd.VBox([split_p_latex_box,
                                               split_p_plotly_template_box,
                                               split_p_zoom_box
                                               ]),
                                      wd.VBox([split_p_title_font_box,
                                               split_p_title_size_box,
                                               split_p_subtitle_size_box,
                                               split_p_height_box,
                                               split_p_width_box])
                                      ])
                             ])
        split_plot_settings = wd.Accordion(children=[split_box],
                                           titles=('Split-plot settings',))
        observe_ordinary_ls.append(split_p_zoom_sliders)
        observe_ordinary_ls.append(split_p_plotly_templates)
        observe_ordinary_ls.append(split_p_use_latex_cb)
        observe_height_width_ls.append(split_p_width)
        observe_height_width_ls.append(split_p_height)

        multi_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         'In a <b><i>multi plot</i></b> '
                                         'you can visualize several variables '
                                         'in one plot. Variables of the same '
                                         '<i>unit</i> will be mapped into the '
                                         'same y-axis. The maximum of '
                                         'units for a multi plot, '
                                         'and hence y-axes is limited to 2.<br>'
                                         'The <b><i>Height</i></b> and '
                                         '<b><i>Width</i></b> values will be '
                                         'applied for each split plot '
                                         '(values below 200 lead plotly '
                                         'default value).<br>'
                                         '</span>')
        multi_p_use_latex_label = wd.HTML(value='<b>Use LaTeX:</b>')
        multi_p_use_latex_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           tooltip="Applies to the y-axes")
        multi_p_latex_box = wd.HBox([multi_p_use_latex_label,
                                     multi_p_use_latex_cb])

        multi_p_height_label = wd.HTML(value='<b>Height:</b>')
        multi_p_height = wd.IntText(layout=_get_layout('9999999999'))
        multi_p_height_box = wd.HBox([multi_p_height_label,
                                      multi_p_height])
        multi_p_width_label = wd.HTML(value='<b>Width:</b> ')
        multi_p_width = wd.IntText(layout=_get_layout('9999999999'))
        multi_p_width_box = wd.HBox([multi_p_width_label,
                                     multi_p_width])
        multi_p_plotly_templates_label = wd.HTML(
            value='<b>Plotly templates:</b> ')
        multi_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                               value='plotly')
        multi_p_plotly_template_box = wd.HBox([multi_p_plotly_templates_label,
                                               multi_p_plotly_templates])
        multi_p_title_font_label = wd.HTML(value='<b>Title font:</b> ')
        multi_p_title_font = wd.Dropdown(options=plotly_fonts)
        multi_p_title_font_box = wd.HBox([multi_p_title_font_label,
                                          multi_p_title_font])
        multi_p_title_size_label = wd.HTML(value='<b>Title size:</b> ')
        multi_p_title_size = wd.Dropdown(options=plotly_sizes)
        multi_p_title_size_box = wd.HBox([multi_p_title_size_label,
                                          multi_p_title_size])
        multi_p_subtitle_size_label = wd.HTML(value='<b>Subtitle size:</b> ')
        multi_p_subtitle_size = wd.Dropdown(options=plotly_sizes)
        multi_p_subtitle_size_box = wd.HBox([multi_p_subtitle_size_label,
                                             multi_p_subtitle_size])
        multi_box = wd.VBox([multi_plot_guide,
                             wd.HBox([wd.VBox([multi_p_latex_box,
                                               multi_p_plotly_template_box]),
                                      wd.VBox([multi_p_title_font_box,
                                               multi_p_title_size_box,
                                               multi_p_subtitle_size_box,
                                               multi_p_height_box,
                                               multi_p_width_box])
                                      ])
                             ])
        observe_height_width_ls.append(multi_p_width)
        observe_height_width_ls.append(multi_p_height)
        observe_ordinary_ls.append(multi_p_plotly_templates)
        observe_ordinary_ls.append(multi_p_use_latex_cb)

        multi_plot_settings = wd.Accordion(children=[multi_box],
                                           titles=('Multi-plot settings',))

        corr_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                        'In a <b><i>Correlation plot</i></b> '
                                        'you can compare <i>two</i> variables '
                                        'against each other. <br>'
                                        'The <b><i>Height</i></b> and '
                                        '<b><i>Width</i></b> values will be '
                                        'applied for each split plot '
                                        '(values below 200 lead plotly '
                                        'default value).<br>'
                                        'The <b><i>Plotly template</i></b> '
                                        'reflects '
                                        'the background colors etc.<br>'
                                        'The <b><i>Plotly color scale</i></b> '
                                        'is used in order to visualize '
                                        'the timestamps of the sampling of '
                                        'the data.</span>')
        corr_p_use_latex_label = wd.HTML(value='<b>Use LaTeX:</b>')
        corr_p_use_latex_cb = wd.Checkbox(value=True,
                                          disabled=False,
                                          indent=False,
                                          tooltip="Applies to the x- and "
                                                  "y-axes")
        corr_p_latex_box = wd.HBox([corr_p_use_latex_label,
                                    corr_p_use_latex_cb])

        corr_p_height_label = wd.HTML(value='<b>Height:</b>')
        corr_p_height = wd.IntText(layout=_get_layout('9999999999'))
        corr_p_height_box = wd.HBox([corr_p_height_label,
                                     corr_p_height])
        corr_p_width_label = wd.HTML(value='<b>Width:</b> ')
        corr_p_width = wd.IntText(layout=_get_layout('9999999999'))
        corr_p_width_box = wd.HBox([corr_p_width_label,
                                    corr_p_width])
        corr_p_title_font_label = wd.HTML(value='<b>Title font:</b> ')
        corr_p_title_font = wd.Dropdown(options=plotly_fonts)
        corr_p_title_font_box = wd.HBox([corr_p_title_font_label,
                                         corr_p_title_font])
        corr_p_title_size_label = wd.HTML(value='<b>Title size:</b> ')
        corr_p_title_size = wd.Dropdown(options=plotly_sizes)
        corr_p_title_size_box = wd.HBox([corr_p_title_size_label,
                                         corr_p_title_size])
        corr_p_subtitle_size_label = wd.HTML(value='<b>Subtitle size:</b> ')
        corr_p_subtitle_size = wd.Dropdown(options=plotly_sizes)
        corr_p_subtitle_size_box = wd.HBox([corr_p_subtitle_size_label,
                                            corr_p_subtitle_size])
        corr_p_color_scale_label = wd.HTML(value='<b>Plotly color scale:</b> ')
        corr_p_color_scale_drop = wd.Dropdown(options=plotly_color_scales,
                                              value='blues')
        corr_p_color_scale_box = wd.HBox([corr_p_color_scale_label,
                                          corr_p_color_scale_drop])
        corr_p_plotly_templates_label = wd.HTML(value='<b>Plotly templates:</b> ')
        corr_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                              value='plotly')
        corr_p_plotly_template_box = wd.HBox([corr_p_plotly_templates_label,
                                              corr_p_plotly_templates])
        corr_box = wd.VBox([corr_plot_guide,
                            wd.HBox([wd.VBox([corr_p_latex_box,
                                              corr_p_plotly_template_box,
                                              corr_p_color_scale_box]),
                                     wd.VBox([corr_p_title_font_box,
                                              corr_p_title_size_box,
                                              corr_p_subtitle_size_box,
                                              corr_p_height_box,
                                              corr_p_width_box]),
                                     ])
                            ])
        corr_plot_settings = wd.Accordion(children=[corr_box],
                                          titles=('Correlation-plot settings',))
        observe_ordinary_ls.append(corr_p_use_latex_cb)
        observe_ordinary_ls.append(corr_p_plotly_templates)
        observe_ordinary_ls.append(corr_p_color_scale_drop)
        observe_height_width_ls.append(corr_p_width)
        observe_height_width_ls.append(corr_p_height)

        corr_table_settings = wd.Accordion(children=[split_box],
                                           titles=('Correlation table settings',))
        statistics_settings = wd.Accordion(children=[split_box],
                                           titles=(
                                           'Numerical statistics settings',))

        general_accordion = wd.Accordion(children=[wd.VBox([time_length_settings,
                                                            latex_settings,
                                                            split_plot_settings,
                                                            multi_plot_settings,
                                                            corr_plot_settings,
                                                            corr_table_settings,
                                                            statistics_settings,
                                                            save_cancel_box])],
                                         titles=('Default settings',))
        batch_accordion = wd.Accordion(children=[self._edit_batch_jobs()],
                                       titles=('Batch jobs',))

        out = wd.Output()
        init_general_settings()
        display(general_accordion, batch_accordion, out)

    def _edit_group_variables(self):
        if self.debug:
            print('*** _edit_group_variables()\n')

        def update_cache(group_dict):
            if self.debug:
                print('update_cache()', group_dict)

            # Structure of group_dict
            # group_dict = {'_change': 'new'| 'update'| 'delete',
            #               '_group_name': '<some groupname>',
            #               '_saved_group_name': 'old name of group',
            #               '_var_list': [['var1','spec1','some station'],
            #                             ['var2','spec2','some station']],
            #               '_delete_errors': [],
            #               '_name_error': [],
            #               '_var_error': []}

            # Structure of cache dict:
            # {'_last_station_id': 'Hyltemossa',
            #  '_last_group': 'Group 1',
            #  '_groups': {'Group 1': [['SWC_1', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_2', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_3', 'ETC NRT Meteo', 'Hyltemossa']],
            #              'LCA' : [['LE', 'ETC NRT Fluxes', 'Hyltemossa'],
            #                       ['LE_UNCLEANED', 'ETC NRT Fluxes',
            #                       'Hyltemossa'],
            #                       ['NEE', 'ETC NRT Fluxes', 'Hyltemossa'],
            #                       ['NEE_UNCLEANED', 'ETC NRT Fluxes',
            #                       'Hyltemossa']],
            #              'Another group': [['SWC_1', 'ETC NRT Meteo',
            #                                'Hyltemossa'],
            #                                ['SWC_2', 'ETC NRT Meteo',
            #                                'Hyltemossa'],
            #                                ['SWC_3', 'ETC NRT Meteo',
            #                                'Hyltemossa'],
            #                                ['LE', 'ETC NRT Fluxes',
            #                                'Hyltemossa'],
            #                                ['LE_UNCLEANED','ETC NRT Fluxes',
            #                                'Hyltemossa'],
            #                                ['NEE','ETC NRT Fluxes',
            #                                'Hyltemossa'],
            #                                ['NEE_UNCLEANED','ETC NRT Fluxes',
            #                                'Hyltemossa']]}}

            if '_change' not in group_dict.keys() or \
                    '_group_name' not in group_dict.keys():
                return

            grp = group_dict['_group_name']
            var_ls = group_dict['_var_list']
            old_grp = ''
            cache = self._load_cache()

            if group_dict['_change'] == 'new':
                cache['_groups'][grp] = {'_group_vars': var_ls}

                # update "last"-flags
                last_var_tuple = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station_id'] = last_var_tuple[-1]

            elif group_dict['_change'] == 'update':
                if '_saved_group_name' in group_dict.keys():
                    old_grp = group_dict['_saved_group_name']
                    if grp != old_grp:
                        batches = cache['_groups'][old_grp].get('_batches', {})
                        cache['_groups'].pop(old_grp)
                        cache['_groups'][grp] = {'_batches': batches}

                cache['_groups'][grp]['_group_vars'] = var_ls
                # update "last"-flags
                last_var_tuple = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station_id'] = last_var_tuple[-1]

            elif group_dict['_change'] == 'delete':
                if grp in cache['_groups'].keys():
                    cache['_groups'].pop(grp)
                    if cache['_last_group'] == grp:
                        # change to the "last flags", if needed
                        group_ls = list(cache['_groups'].keys())
                        if group_ls:
                            last_group = group_ls[-1]
                            cache['_last_group'] = last_group
                            last_group_vars = cache['_groups'][last_group][
                                '_group_vars']
                            cache['_last_station_id'] = last_group_vars[-1][-1]
                        else:
                            cache['_last_group'] = ''
                            cache['_last_station_id'] = ''

            # Remove timeseries from local storage
            self._flush_store(grp)
            if old_grp:
                self._flush_store(old_grp)
            self._set_cache(cache_dict=cache)

        def init():

            val = set_group_drop('')

            if val == 'first_run':
                create_group(val)
                display_user_guide('display_guide')
            else:
                activate_gui('init_read_mode')

        def set_station_drop():
            if self.debug:
                print('set_station_drop()')

            id_ls = list(st_df.id)
            name_ls = list(st_df.name)
            station_ls = list(set(zip(name_ls, id_ls)))
            station_ls.sort(key=lambda v: v[0].lower())

            # Try to use station from last added variable
            upd_dict = get_temp_dict()
            stn = None
            try:
                stn = upd_dict['_var_list'][-1][-1]
            except:
                # This is the case for a new group
                # try to use the last station
                try:
                    cache = self._load_cache()
                    stn = cache['_last_station_id']
                except:
                    # This is the case if there are no groups or 
                    # if the last used group was deleted
                    pass
            finally:
                if not stn:
                    station_ls.insert(0, ('Choose a station', 'dummy'))
                    stn = 'dummy'
                elif station_ls[0] == ('Choose a station', 'dummy'):
                    station_ls.pop(0)
                station_drop.options = station_ls
                station_drop.value = stn

        def set_spec_drop(change):

            cache = self._load_cache()
            if station_drop.value == 'dummy':
                spec_ls = ['Products...']
                dobj_ls = ['dummy']
            else:
                df = st_df.loc[st_df.id == station_drop.value]
                spec_ls = list(df.specLabel)
                dobj_ls = list(df.dobj)

            spec_drop_ls = list(zip(spec_ls, dobj_ls))
            spec_drop_ls.sort(key=lambda v: v[0].lower())
            spec_drop.options = spec_drop_ls

            if change == 'new':
                spec_drop.value = spec_drop.options[0][1]
            elif change == 'update':
                grp = group_drop.value
                last_spec_in_var_list = cache['_groups'][grp]['_group_vars'][
                    -1][1]
                spec_drop.value = [y[1] for y in spec_drop_ls if
                                   y[0] == last_spec_in_var_list].pop()
            elif isinstance(change, dict) and change['new']:
                grp = change['new']
                try:
                    last_spec_in_var_list = cache['_groups'][grp][
                        '_group_vars'][-1][1]
                    spec_drop.value = [y[1] for y in spec_drop_ls if
                                       y[0] == last_spec_in_var_list].pop()
                except:
                    pass
            else:
                spec_drop.value = spec_drop.options[0][1]

            if not spec_drop.value:
                spec_drop.value = spec_drop.options[0][1]

        def set_var_drop(change):

            if self.debug:
                print('set_var_drop()')

            # Menu of variables to show some info of a variable
            if spec_drop.value == 'dummy':
                var_drop.options = [('Variables...', 'dummy')]
                var_drop.value = var_drop.options[0][1]
            else:
                pid = spec_drop.value
                var_dict = self.icos_info.icos_product_meta(pid)
                var_ls = sorted([key for key in var_dict.keys() if key not in
                                 ['TIMESTAMP', 'TIMESTAMP_END']])
                var_info = [var_dict[key] for key in var_ls]
                var_drop.options = list(zip(var_ls, var_info))
                var_drop.value = var_drop.options[0][1]

        def set_var_info_text(change):
            if self.debug:
                print('\nset_var_info_text()\nchange: ', change)

            # Show info of a variable
            if isinstance(change, dict):
                if change['name'] == 'value' and change['new']:
                    if isinstance(change['owner'], wd.Dropdown):
                        if var_drop.value == 'dummy':
                            return
                        else:
                            var_name = change['owner'].label
                            var_dict = change['owner'].value
                    elif isinstance(change['owner'], wd.Checkbox):
                        var_name = change['owner'].description
                        var_dict = [x[1] for x in var_drop.options
                                    if x[0] == var_name].pop()
                        var_drop.value = var_dict
                    else:
                        return
                else:
                    return
            else:
                var_name = var_drop.label
                var_dict = var_drop.value

            try:
                name = var_dict['name'][0].upper() + var_dict['name'][1:]
            except:
                name = ''
            try:
                unit = var_dict['unit']
            except:
                unit = ''
            try:
                label = var_dict['label'][0].upper() + var_dict['label'][1:]
            except:
                label = ''
            try:
                comment = var_dict['comment']
                comment = comment[0].upper() + comment[1:]
            except:
                comment = ''

            text = f"<b>Basics of the variable <i>{var_name}</i></b> <br>"
            if name:
                text += f"<b>Name:</b> {name}. "
            if unit:
                text += f"<b> Unit:</b> {unit}.<br>"
            if label:
                text += f"<b>Label:</b> {label}. "
            if comment:
                text += f"<b>Comments:</b> {comment}."

            var_info_text.value = text

        def set_group_drop(change):
            cache = self._load_cache()
            if self.debug:
                print('set_group_drop()', cache.keys())

            # load from cache
            group_ls = list(cache['_groups'].keys())
            last_grp = cache['_last_group']

            if group_ls:
                group_drop.options = group_ls
                if last_grp:
                    group_drop.value = last_grp
                else:
                    group_drop.value = group_drop.options[0]
            else:
                group_drop.options = ['No groups loaded...']
                group_drop.value = group_drop.options[0]
                group_drop.disabled = True
                return 'first_run'
            return ''

        def get_group_var_text(upd_mode):
            if self.debug:
                print('get_group_var_text()\tmode: ', upd_mode)

            if upd_mode:
                upd_dict = get_temp_dict()
                var_tuples = upd_dict['_var_list']
                var_ls = [v[0] for v in var_tuples]
                text_tag = 'i'
                separator = ' || '
                margin = '&nbsp' * 2
            else:
                grp = group_drop.value
                cache = self._load_cache()
                var_tuples = cache['_groups'][grp]['_group_vars']
                var_ls = [v[0] for v in var_tuples]
                text_tag = 'b'
                separator = '<br>'
                margin = '&nbsp' * 10

            station_dict = _var_tup2station_dict(var_tuples)

            # We loop over stations and products to concatenate
            # a proper text in html
            t1 = f'<{text_tag}>Variables: </{text_tag}>'
            t2 = ', '.join(var_ls)
            t3 = ''
            if upd_mode and len(t1 + t2) > 100:
                t2 += '<br>'
                first_break = 0
            else:
                first_break = 1

            one_stn = (len(station_dict.keys()) == 1)
            for stn in station_dict.keys():
                if one_stn:
                    t1 = f'<{text_tag}>Variables (of {stn}): </{text_tag}>'
                    one_prod = (len(station_dict[stn].keys()) == 1)
                    for prod in station_dict[stn].keys():
                        if one_prod:
                            t1 = f'<{text_tag}>Variables (of {prod} at {stn}): </{text_tag}>'
                        else:
                            t3 += f'{separator}{margin}<{text_tag}>{prod}: </{text_tag}>' + \
                                  ", ".join(station_dict[stn][prod])
                            if not upd_mode:
                                t3 += f'{separator}'
                        if upd_mode and len(t3) + len(
                                t1 + t2) * first_break > 100:
                            first_break = 0
                            t3 += '<br>'
                else:
                    t3 += f'{separator}{margin}<{text_tag}>Station {stn}</{text_tag}> '
                    for prod in station_dict[stn].keys():
                        t3 += f'{separator}{margin}<{text_tag}>{prod}: </{text_tag}>'
                        t3 += ", ".join(station_dict[stn][prod])
                    if upd_mode:
                        if len(t3) + len(t1 + t2) * first_break > 100:
                            t3 += '<br>'
                    else:
                        t3 += '<br>'

            if t3:
                t3 += f'{margin}<i>(In order of appearance)</i>'
            return t1 + t2 + t3

        def set_group_vars(c):
            cache = self._load_cache()
            if self.debug:
                print('set_group_vars()\tcache.keys(): ', cache.keys())
            if isinstance(cache, dict):
                grp = group_drop.value
                if grp not in cache['_groups'].keys():
                    # Container title...
                    cont_title = f'Content of a group goes here'
                    g_vars.set_title(0, cont_title)
                    group_vars.value = '<b>Variables: </b>'
                    return

                # Generate HTML-text for the variables
                var_text = get_group_var_text(upd_mode=False)

                # Container title...
                cont_title = f'Content of group {grp}'
                g_vars.set_title(0, cont_title)
                group_vars.value = var_text
            else:
                # No cache,
                cont_title = f'Content of a group goes here'
                g_vars.set_title(0, cont_title)
                group_vars.value = 'Variables: '

        def set_var_checkboxes(c):
            # Checkboxes for variables

            if self.debug:
                print('set_var_checkboxes()')

            if station_drop.value == 'dummy' or spec_drop.value == 'dummy':
                return

            station = station_drop.value
            spec = spec_drop.label

            var_label.value = f'<b><font color="darkgreen">Variables of {str(spec)} at {str(station)}</b>'

            # We need to find vars that are part of the group
            upd_group_dict = get_temp_dict()
            if upd_group_dict:
                var_ls = upd_group_dict['_var_list']
            else:
                var_ls = []
                try:
                    grp = group_drop.label
                    cache = self._load_cache()
                    if grp in cache['_groups']:
                        var_ls = cache['_groups'][grp]['_group_vars'].copy()
                except:
                    pass

            selected_ls = [y[0] for y in var_ls if
                           y[1] == spec and y[2] == station]

            checkbox_ls = []
            for var_option in var_drop.options:
                var = var_option[0]
                var_selected = bool(var in selected_ls)
                cb = wd.Checkbox(description=var, value=var_selected,
                                 disabled=False, indent=False,
                                 layout=wd.Layout(width='160px'))
                checkbox_ls.append(cb)
                cb.observe(cb_changed)

            var_cbs_box.children = checkbox_ls

        def get_temp_dict():

            if self.debug:
                print('get_temp_dict()\t', group_dict_log.value)

            temp_log = group_dict_log.value
            if temp_log:
                upd_group_dict = eval(temp_log)
            else:
                upd_group_dict = dict()

            return upd_group_dict

        def set_temp_dict(upd_dict):

            if self.debug:
                print('\nset_temp_dict()\t', upd_dict)

            upd_group_dict = get_temp_dict()

            for key, val in upd_dict.items():
                upd_group_dict[key] = val

            if upd_group_dict['_var_list']:
                upd_group_dict['_var_error'] = []

            group_dict_log.value = str(upd_group_dict)

            set_reset_error_msg()

        def cb_changed(cb):
            # 1. Fix the variable widget list
            # 2. Update upd_group_dict

            set_var_info_text(cb)

            if cb.name == 'value':

                var_name = str(cb.owner.description)

                upd_ls = [var_name, spec_drop.label, station_drop.value]

                # Load group dict 
                upd_group_dict = get_temp_dict()

                if cb.owner.value:
                    # add var to group dict
                    upd_group_dict['_var_list'].append(upd_ls)

                else:
                    if self.debug:
                        print('cb_changed()\t',
                              '\nupd_ls: ', upd_ls,
                              '\nupd_group_dict: ', upd_group_dict)
                    # Remove var from var group
                    upd_group_dict['_var_list'].remove(upd_ls)

                set_temp_dict(upd_group_dict)
            set_upd_variables()

        def set_upd_variables():
            group_vars_upd.value = get_group_var_text(upd_mode=True)

        def group_name_changed(change):

            if self.debug:
                print('group_name_changed()')

            if change.name == 'value':
                new_name = change.owner.value
                upd_group_dict = get_temp_dict()
                upd_mode = upd_group_dict['_change']

                error_ls = validate_name(upd_group_dict, new_name)
                upd_group_dict['_name_error'] = error_ls

                # Change the upd status
                upd_group_dict['_group_name'] = new_name

                # Rename the group-key to the var-list (if any)
                prev_name = upd_group_dict['_group_name']
                if prev_name and new_name != prev_name and \
                        prev_name in upd_group_dict.keys():
                    upd_group_dict[new_name] = upd_group_dict[prev_name]
                    upd_group_dict.pop(prev_name)
                set_temp_dict(upd_group_dict)

        # *************************
        # create-upd-delete-events
        #
        # new and update data is stored in the dictionary 
        # handled by get_temp_dict()/set_temp_dict(dict)

        def create_group(click):
            if self.debug:
                print('create_group()')

            upd_group_dict = {'_change': 'new',
                              '_group_name': 'Group name',
                              '_var_list': []}

            set_temp_dict(upd_group_dict)

            group_name.value = 'Group name'
            set_upd_variables()
            activate_gui('new')

        def update_group(click):
            if self.debug:
                print('update_group()')

            grp = group_drop.value
            cache = self._load_cache()
            upd_group_dict = {'_change': 'update',
                              '_group_name': grp,
                              '_saved_group_name': grp,
                              '_var_list': cache['_groups'][grp]['_group_vars']}

            set_temp_dict(upd_group_dict)

            group_name.value = grp
            set_upd_variables()
            activate_gui('update')

        def save_group(click):
            cache = self._load_cache()

            upd_group_dict = get_temp_dict()
            if self.debug:
                print(f'save_group()\t cache.keys(): {cache.keys()}')
                print(f'save_group()\t upd_group_dict: {upd_group_dict}')

            if not upd_group_dict['_change'] in ['new', 'update']:
                return

            # Valid name?
            name_error_ls = validate_name(upd_group_dict,
                                          upd_group_dict['_group_name'])
            upd_group_dict['_name_error'] = name_error_ls

            # Valid vars?
            var_error_ls = validate_vars(upd_group_dict)
            upd_group_dict['_var_error'] = var_error_ls

            if name_error_ls or var_error_ls:
                # Don't save the data
                set_temp_dict(upd_group_dict)
            else:
                # save group data
                update_cache(upd_group_dict)
                # reset gui
                init()
                set_group_vars('')
                activate_gui('save')

        def delete_group(click):

            cache = self._load_cache()
            if self.debug:
                print('save_group()')

            upd_group_dict = get_temp_dict()

            grp = upd_group_dict['_group_name']
            old_grp_name = upd_group_dict['_saved_group_name']

            error_ls = []
            var_error = ''
            name_error = ''
            if grp != old_grp_name:
                name_error = f'Original name: {old_grp_name}. New name: {grp}.'

            if old_grp_name in cache['_groups'].keys():
                upd_vars = upd_group_dict['_var_list']
                if upd_vars != cache['_groups'][old_grp_name]['_group_vars']:
                    var_error = '''Group variables are different from the 
                    stored variables'''

            if name_error:
                error_ls.append(f'<b>Name error</b> {name_error}')

            if var_error:
                error_ls.append(f'<b>Variable error</b> {var_error}')

            if error_ls:
                error_ls.append('<br>To delete a group of variables:')
                error_ls.append(' 1. Select the group.')
                error_ls.append(' 2. Press <i>Update</i>')
                error_ls.append(' 3. Press <i>Delete</i>')
                error_ls.append('Don\'t change the content.')
                upd_group_dict['_delete_errors'] = error_ls
                set_temp_dict(upd_group_dict)
                set_reset_error_msg()
            else:
                upd_group_dict['_change'] = 'delete'
                update_cache(upd_group_dict)
                init()
                set_group_vars('')
                activate_gui('del')

        def cancel_group(click):
            if self.debug:
                print('cancel_group()')

            activate_gui('cancel')

        # Validations     
        def validate_name(upd_dict, grp_name):

            cache = self._load_cache()
            upd_mode = upd_dict['_change']

            error_ls = []

            # Validate suggested name
            if not grp_name or grp_name == 'Group name':
                error_ls.append(
                    'Please, choose a name for the group of variables.')
            elif not grp_name[0].isalnum():
                error_ls.append('At least the first letter of the group')
                error_ls.append('name must be an alfa numeric character.')
            elif grp_name in cache['_groups'].keys():
                if upd_mode == 'new':
                    error_ls.append(
                        f'There is already a group called <it>{grp_name}</i>,')
                    error_ls.append('please pick another name.')
                elif upd_mode == 'update':
                    if grp_name != upd_dict['_saved_group_name']:
                        error_ls.append(
                            f'There is already a group called <it>{grp_name}</i>,')
                        error_ls.append('please pick another name.')

            if error_ls:
                group_name.style.text_color = 'red'
            else:
                group_name.style.text_color = 'darkgreen'

            return error_ls

        def validate_vars(upd_dict):
            if upd_dict['_var_list']:
                error_ls = []
            else:
                error_ls = ['Please add some variables to the group.']

            return error_ls

        def display_var_info(c):
            if var_info_container.layout.display == 'none':
                var_info_container.layout.display = 'block'
            else:
                var_info_container.layout.display = 'none'

        def display_user_guide(c):

            if c == 'display_guide':
                user_guide_container.selected_index = 0
                user_guide_container.layout.display = 'block'
            elif user_guide_container.layout.display == 'none':
                user_guide_container.layout.display = 'block'
            else:
                user_guide_container.layout.display = 'none'

        # Messages on what to do and errors
        def set_info_msg(error_ls=None):
            upd_group_dict = get_temp_dict()
            upd_mode = upd_group_dict['_change']

            if upd_mode == 'new':
                info_ls = ['How to create a group of variables:',
                           '1. Select your station.',
                           '2. Select a file/product.',
                           '3. Select variables.',
                           'Chosen variables are displayed beside the text '
                           '<span style="color:black">"Variables in update '
                           'mode:"</span> below. ',
                           '4. Choose a name for your group of variables in '
                           'the area <span style="color:black">"Group '
                           'name"</span>.',
                           '5. Save.',
                           '',
                           '</b>The order of the variables is the order of presentation in plots, etc.<b>',
                           '</b>You can combine variables from different files or stations.<b>',
                           '</b>Last entered station, and file/product, will be preselected next time.<b>']
            elif upd_mode == 'update':
                info_ls = ['In update mode you can:',
                           '1. Add or remove variables of a group.',
                           '2. Change the group name.',
                           '3. Delete the group.',
                           '',
                           '</b>The order of the variables is the order of presentation in plots, etc.<b>',
                           '</b>Changes are logged in the file "/appdata/cache_bak.json".<b>']
            else:
                info_ls = []

            margin = '&nbsp' * 3

            if info_ls:
                info_color = self.ipyw_style_colors['primary:active']
                msg = f'<span style="color:{info_color}">{margin}{margin}<h4>' \
                      f'{info_ls[0]}</h4><b>'

                for row in info_ls[1:]:
                    msg += f'{margin}{row}<br>'
                msg += '</b></span>'
            else:
                msg = ''

            if error_ls:
                warning_emoji = '\u26a0\ufe0f'
                error_color = self.ipyw_style_colors['danger:active']
                msg += f'<br><span style="color:{error_color}">{margin}{margin}'
                msg += f'<h3>To do: {warning_emoji}</h3><b>'
                for error in error_ls:
                    msg += f'{margin}{error}<br>'
                msg += '</b></span>'

            if error_ls and user_guide_container.layout.display == 'none':
                display_user_guide('display_guide')

            user_guide.value = msg

        def set_reset_error_msg():
            upd_group_dict = get_temp_dict()
            error_keys = ['_name_error', '_var_error', '_delete_errors']

            error_ls = []
            for k in upd_group_dict.keys():
                if k in error_keys:
                    error_ls += upd_group_dict[k]

            if error_ls:
                set_info_msg(error_ls)
            else:
                set_info_msg()

        # ********************************
        # activate/deactivate upd-widgets
        def activate_gui(upd_active):
            if self.debug:
                print('activate_gui()\t', get_temp_dict())

            if upd_active in ['new', 'update']:
                # update mode
                # init update widgets..
                set_info_msg()
                update_group_btn.on_click(update_group, remove=True)
                create_group_btn.on_click(create_group, remove=True)
                save_group_btn.on_click(save_group, remove=False)
                delete_group_btn.on_click(delete_group, remove=False)
                cancel_group_btn.on_click(cancel_group, remove=False)
                var_info_btn.on_click(display_var_info, remove=False)
                help_btn.on_click(display_user_guide, remove=False)

                set_station_drop()
                set_spec_drop(upd_active)
                set_var_drop('')
                set_var_info_text('')
                set_var_checkboxes('')

                var_drop.observe(set_var_info_text, names='value')
                station_drop.observe(set_spec_drop, names='value')
                spec_drop.observe(set_var_drop, names='value')
                spec_drop.observe(set_var_checkboxes, names='value')
                group_name.observe(group_name_changed, 'value')

                upd_box.layout.display = 'flex'

                for b in create_btns.children:
                    b.tooltip = 'Disabled in update mode...'
                    b.disabled = True
                group_drop.disabled = True
                save_group_btn.disabled = False
                cancel_group_btn.disabled = False
                var_info_btn.disabled = False
                help_btn.disabled = False
                save_group_btn.tooltip = 'Save settings...'
                cancel_group_btn.tooltip = 'Cancel...'
                if upd_active == 'update':
                    delete_group_btn.disabled = False
                    delete_group_btn.tooltip = 'Delete...'
                else:
                    delete_group_btn.disabled = True
                    delete_group_btn.tooltip = 'Delete...'
            else:
                # read mode
                # turn off observers
                cache = self._load_cache()
                no_groups = not cache['_groups'].keys()
                update_group_btn.on_click(update_group, remove=no_groups)
                create_group_btn.on_click(create_group, remove=False)
                save_group_btn.on_click(save_group, remove=True)
                delete_group_btn.on_click(delete_group, remove=True)
                cancel_group_btn.on_click(cancel_group, remove=True)
                var_info_btn.on_click(display_var_info, remove=True)
                help_btn.on_click(display_user_guide, remove=True)

                station_drop.unobserve(set_spec_drop)
                spec_drop.unobserve(set_var_drop)
                spec_drop.unobserve(set_var_checkboxes)
                group_name.unobserve(group_name_changed)
                var_drop.unobserve(set_var_info_text)

                upd_box.layout.display = 'none'
                for b in create_btns.children:
                    b.disabled = False
                    update_group_btn.disabled = no_groups
                group_drop.disabled = False
                create_group_btn.tooltip = 'New group...'
                update_group_btn.tooltip = 'Update group...'
                var_info_btn.disabled = True
                help_btn.disabled = True

                for b in non_create_btns.children:
                    b.tooltip = 'Enabled in update mode...'
                    b.disabled = True
                group_dict_log.value = ''

        # Main of edit group vars
        # ====

        # Get station and product data
        st_df = self.stations_df

        # Layouts
        drop_layout = wd.Layout(width='auto', height='40px')
        var_txt_layout = wd.Layout(width='99%', height='100%')
        grp_txt_layout = wd.Layout(width='148pt', height='28px')

        # Dropdowns
        group_drop = wd.Dropdown(layout=wd.Layout(width='148pt',
                                                  height='40px'))
        station_drop = wd.Dropdown(layout=drop_layout)
        spec_drop = wd.Dropdown(layout=drop_layout)
        var_drop = wd.Dropdown(layout=wd.Layout(width='148pt',
                                                flex='inline-flex',
                                                align="flex-end"))

        # Group stuff  n(children=[page1, page2], width=400)
        group_vars = wd.HTML(layout=var_txt_layout,
                             value='Variables: ',
                             disabled=True)
        g_vars = wd.Accordion([group_vars],
                              titles=(group_vars.value, '0'),
                              selected_index=None,
                              layout=wd.Layout(width='100%', height='100%'))
        group_vars_upd = wd.HTML(layout=var_txt_layout,
                                 value='Variables in update mode: ',
                                 disabled=True,
                                 style={'text_color': 'darkgreen'})
        group_name = wd.Text(layout=grp_txt_layout)
        group_dict_log = wd.Textarea(disabled=True)
        # to hide... layout = wd.Layout(display = 'none'))

        # Container for checkboxes
        var_label = wd.HTML()
        var_cbs_box = wd.HBox(layout=wd.Layout(border='dashed 0.5px',
                                               width='100%',
                                               display='inline-flex',
                                               flex_flow='row wrap',
                                               align_content='flex-start'))
        var_box = wd.VBox([var_label, var_cbs_box])

        # Create group buttons
        create_group_btn = wd.Button(description='New', icon='plus',
                                     button_style='primary')
        update_group_btn = wd.Button(description='Update', icon='pen',
                                     button_style='info')
        save_group_btn = wd.Button(description='Save', icon='save',
                                   button_style='success')
        cancel_group_btn = wd.Button(description='Cancel', icon='ban',
                                     button_style='info')
        delete_group_btn = wd.Button(description='Delete', icon='trash',
                                     button_style='danger')
        create_btns = wd.HBox([create_group_btn, update_group_btn])

        help_btn = wd.Button(description='User guide',
                             icon='fa-info-circle',
                             button_style='info')
        var_info_btn = wd.Button(description='Variable',
                                 icon='fa-info-circle',
                                 button_style='info')

        non_create_btns = wd.HBox(
            [save_group_btn, cancel_group_btn, delete_group_btn])
        btns = wd.HBox([create_btns, non_create_btns, help_btn, var_info_btn])

        # Variable info-text
        var_info_text = wd.HTML(layout=wd.Layout(width='100%',
                                                 max_width='90%',
                                                 height='auto'))
        # Text to user
        user_guide = wd.HTMLMath(disabled=True,
                                 layout=wd.Layout(width='90%',
                                                  max_width='90%',
                                                  height='auto'))

        var_info_container = wd.Accordion(children=[wd.VBox([var_drop,
                                                             var_info_text])],
                                          selected_index=None,
                                          layout=wd.Layout(width='auto',
                                                           min_width='45%',
                                                           height='auto',
                                                           display='none'))
        var_info_container.set_title(0, 'Variable info')

        user_guide_container = wd.Accordion(selected_index=None,
                                            layout=wd.Layout(width='auto',
                                                             min_width='45%',
                                                             height='auto',
                                                             display='none'))

        if self.debug:
            user_guide_container.children = [wd.VBox([user_guide,
                                                      group_dict_log])]
        else:
            user_guide_container.children = [wd.VBox([user_guide])]
        user_guide_container.set_title(0, 'User guide')

        upd_box = wd.VBox([wd.HBox([station_drop, spec_drop]),
                           wd.HBox([user_guide_container, var_info_container]),
                           wd.HBox([group_name, group_vars_upd]),
                           var_box])

        # observe choices
        group_drop.observe(set_group_vars, names='value')

        # Init widgets
        init()

        if not self.debug:
            group_dict_log.layout.display = 'None'

        display(wd.VBox([wd.HBox([group_drop, g_vars]), btns, upd_box]))
