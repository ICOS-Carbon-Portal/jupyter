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
from IPython.display import display, Math, clear_output
import datetime as dt
import copy
import os
warnings.simplefilter("ignore", FutureWarning)

if os.getcwd()[-8:] == 'eco_tool':
    import icos_data
    import plot_old
    import report_writer
    from icos_timeseries import IcosFrame
    import json_handler
    import icos2latex
    import idebug
else:
    from eco_tool import icos_data
    from eco_tool import plot_old
    from eco_tool import report_writer
    from eco_tool.icos_timeseries import IcosFrame
    from eco_tool import json_handler
    from eco_tool import icos2latex
    from eco_tool import idebug


class _AppDataRetriever:
    """
        Object to retrieve/read appdata settings.
        We use the same instance in other objects.
    """

    def __init__(self, app_config_file: str, user_cache_file: str,
                 user_config_file: str, debug: bool):
        self.debug = bool(debug)
        self.app_config_file = app_config_file
        self.user_cache_file = user_cache_file
        self.user_config_file = user_config_file
        self.cache = None
        self.app_config_dict = None

    def load_app_configs(self):
        if not self.app_config_dict:
            default_dict = {'_var2unit_map': {}}
            self.app_config_dict = self._load_json(default_dict=default_dict,
                                                   json_file=self.app_config_file)
        return self.app_config_dict

    def load_cache(self, refresh: bool = None):
        if refresh or not self.cache:
            default_dict = {'_last_station_id': '',
                            '_last_group': '',
                            '_groups': {}}
            self.cache = self._load_json(default_dict=default_dict,
                                         json_file=self.user_cache_file)
        return self.cache

    @staticmethod
    def _load_json(default_dict: dict = None,
                   json_file: str = None):

        return_dict = {}

        if default_dict is None:
            default_dict = {}
        try:
            return_dict = json_handler.read(path_to_json_file=json_file)
        except Exception as e:
            error_msg = f'Exception from "_AppDataRetriever._load_json()"!' \
                        f'\n\t\tCould not load the file: {json_file}\n\n\t\t{e}'
            raise OSError(error_msg)

        finally:

            for k, v in default_dict.items():
                return_dict[k] = return_dict.get(k, v)
        return return_dict

    def load_user_settings(self):

        return self._load_json(default_dict={},
                               json_file=self.user_config_file)


class AnalysisGui:
    # Colors of ipywidgets predefined styles
    widget_style_colors = {'text_color': '#FFFFFF', 'primary': '#2196F3',
                           'primary:active': '#1976D2', 'success': '#4CAF50',
                           'success:active': '#388E3C', 'info:active': '#0097A7',
                           'warning': '#FF9800', 'warning:active': '#F57C00',
                           'danger': '#F44336', 'danger:active': '#D32F2F'}

    @staticmethod
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

    @staticmethod
    def _get_width_layout(text: str = None):
        min_width = max(40, len(text) * 10)
        max_width = 'auto'
        this_layout = wd.Layout(min_width=f'{min_width}px',
                                max_width=max_width)
        return this_layout

    def __init__(self, theme: str = None, level: str = None, debug: bool = None):

        valid_themes = ['ES']
        if not theme:
            theme = 'ES'
        elif isinstance(theme, str) and theme.upper() in valid_themes:
            theme = theme.upper()
        else:
            warnings.warn(f"At this moment the choice theme = {theme}"
                          f"is not implemented. "
                          f"\nThe app will continue "
                          f"with theme = 'ES'.",
                          category=UserWarning)
            theme = 'ES'

        valid_levels = ['1']
        if not level:
            level = '1'
        elif not(isinstance(level, str) and level in valid_levels):
            warnings.warn(f"At this moment the choice level = {level} "
                          f"is not implemented. "
                          f"\nThe app will continue with level = '1'.",
                          category=UserWarning)
            level = '1'

        self.theme = theme
        self.level = level
        if bool(debug):
            self.debug = True
            self.debugger = idebug.IDebug(output='html')
        else:
            self.debug = False
            self.debugger = None

        # directories for appdata and user outputs
        appdata_dir = os.path.join(os.path.expanduser('~'), '.eco_tool_appdata')
        self.code_dir = os.path.join('.', 'eco_tool')
        output_dir = os.path.join(os.path.expanduser('~'), 'output')
        tex_files_dir = os.path.join(output_dir, 'eco_tool_tex_files')
        png_files_dir = os.path.join(output_dir, 'eco_tool_png_files')
        pdf_files_dir = os.path.join(output_dir, 'eco_tool_pdf_files')
        self.output_directories = {'tex_files': tex_files_dir,
                                   'png_files': png_files_dir,
                                   'pdf_files': pdf_files_dir}
        # app_files
        json_file = f'_unit_map_{theme}_{level}.json'
        self.app_config_file = os.path.join(appdata_dir, json_file)
        json_file = f'_user_var_config_{theme}_{level}.json'
        self.user_cache_file = os.path.join(appdata_dir, json_file)
        json_file = f'_default_settings_{theme}_{level}.json'
        self.user_config_file = os.path.join(appdata_dir, json_file)

        self.retriever = _AppDataRetriever(app_config_file=self.app_config_file,
                                           user_cache_file=self.user_cache_file,
                                           user_config_file=self.user_config_file,
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

    def _validate_batch_of_grp(self, cache_dict: dict = None) -> dict:
        # expects a dict like cache['_groups'][grp] see the 'save_group'
        # when variables are removed from a group with batches
        # we might get crashes
        var_ls = cache_dict['_group_vars']

        d = cache_dict['_batches']
        er_dict = {}
        for b_name in d.keys():
            for index, k in d[b_name].items():
                if isinstance(k, str):
                    continue
                for tool, v_ls in k.items():
                    if tool in ['split_plot', 'corr_plot', 'corr_table',
                                'statistics']:
                        if isinstance(v_ls, list) and not all(v in
                                                              var_ls for
                                                              v in v_ls):
                            if b_name not in er_dict.keys():
                                er_dict[b_name] = {}
                            if index not in er_dict[b_name].keys():
                                er_dict[b_name][index] = {}
                            er_dict[b_name][index][tool] = [x for x in v_ls if
                                                            x not in var_ls]
                    else:
                        # multi-plot
                        for x in v_ls:
                            if not all(v in var_ls for v in x[1]):
                                if b_name not in er_dict.keys():
                                    er_dict[b_name] = {}
                                if index not in er_dict[b_name].keys():
                                    er_dict[b_name][index] = {}
                                if tool in er_dict[b_name][index].keys():
                                    er_dict[b_name][index][tool].extend(
                                        [y for y in x[1] if y not in var_ls])
                                else:
                                    er_dict[b_name][index][tool] = [y for y in
                                                                    x[1] if y
                                                                    not in
                                                                    var_ls]
        return er_dict

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
                else:
                    self._help()

        option_ls = ['Start ', 'Group menu ', 'Configurations ', 'Help ']
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

    def get_data(self, grp: str = None) -> IcosFrame or None:
        d = self.get_data_dict
        if d:
            if grp and grp in d.keys():
                df = d[grp]['df']
            elif grp:
                df = None
            else:
                grp = list(d.keys())[-1]
                df = d[grp]['df']
        else:
            df = None
        return df

    @property
    def get_data_dict(self) -> dict:

        if self.report_writer is None:
            d = {}
        else:
            d = self.report_writer.stored_timeseries
        return d

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
            if 'run_configs' in settings.keys():
                end_shift = - settings['run_configs'].get('end_date', 0)
                start_shift = - settings['run_configs'].get('start_date', 8)
                fetch_shift = settings['run_configs'].get('fetch_date', 6)

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
                    b_ls = [wd.Button(description=name,
                                      style={'button_color': 'LightSeaGreen'},
                                      layout=AnalysisGui._get_width_layout(name))
                            for name in batches.keys()]
                    if b_ls:
                        all_title = 'Run all batch jobs'
                        all_layout = AnalysisGui._get_width_layout(all_title)
                        b_ls.append(wd.Button(description=all_title,
                                              style={'button_color':
                                                         'MediumSeaGreen'},
                                              layout=all_layout))
                    for bt in b_ls:
                        bt.on_click(batch_click)
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
                              f'icos_data.StationData.group_ts'
                              f'(var_tuple_ls={var_pid_ls},'
                              + f'\nstart_date= {stored_start}, '
                                f'\nend_date= {stored_end})',
                              type(stored_start), type(stored_end))
                        print('Traceback: ', traceback.format_exc())

            # Store the timeseries
            self.stored_timeseries[grp] = {'start': stored_start,
                                           'end': stored_end,
                                           'df': df}

            return df

        def batch_validation_errors(jobs):
            cache = self._load_cache()
            grp = group_drop.value
            error_ls = []
            if '_var_mismatch' in cache['_groups'][grp]:
                for b, v in cache["_groups"][grp]["_var_mismatch"].items():
                    if b in jobs or jobs == 'all':
                        error_ls.append((b, v))

            return error_ls

        def set_error_message(er_ls):
            tool2name_dict = {'split_plot': 'Split-plot',
                              'multi_plot': 'Multi-plot',
                              'corr_plot': 'Correlation plot (2 vars)',
                              'corr_table': 'Correlation table',
                              'statistics': 'Numerical Statistics'}
            grp = group_drop.value
            error_msg = f'<b>The group <i>{grp}</i> and it\'s ' \
                        f'batch jobs do not match.</b><br> '
            with out:
                print(er_ls)
            for e in er_ls:
                error_msg += f'The batch job <b><i>{e[0]}</i></b> include <br>'
                for index, tool_dict in e[1].items():
                    var_ls = []
                    for tool, var_ls in tool_dict.items():
                        error_msg += f'a <b><i>{tool2name_dict[tool]}</i></b> ' \
                                     f'(tool number {int(index)+1}) with ' \
                                     f'the variable(s): <br>'

                    for v in var_ls:
                        error_msg += f'<b><i>{v[0]}</i></b> (from {v[1]} of' \
                                     f' {v[2]}) <br>'
            error_msg += '<br><i> Probably the above variable has been removed ' \
                         'from the group, but not from the batch jobs</i><br>' \
                         'Suggestion: Either update the group and add the ' \
                         'variables, or update the batch jobs.'

            with out:
                clear_output()
                display(wd.HTML(error_msg))

        def batch_click(c):
            run_batch(jobs=c.description)

        def run_batch(jobs):
            if jobs == 'Run all batch jobs':
                jobs = 'all'

            if self.debug:
                with out:
                    print('run_batch()',
                          jobs,
                          group_drop.value)
            errors = batch_validation_errors(jobs)

            if errors:
                set_error_message(errors)
                return

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

        def run(c=None):
            def link(url, url_txt) -> str:
                return f'<a href="{url}" target="_blank">' \
                       f'<font color="DarkBlue">{url_txt}</font></a>'

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
                rep_title2 += f'{link(urls,products)} of {stations}.'
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
                        rep_title2 += f'{link(tup[1],tup[0])}, '
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
                    rep_title3 += f'Link to data:  {link(urls,urls)}.'
                else:
                    rep_title3 += 'Links to data:  '
                    for u in urls:
                        rep_title3 += f'{link(u,u)}.'

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
                title = f'Split-plot of variable group {grp}  (Timestamp: {today})'

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
                               path_to_json_file=self.user_cache_file)

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

            # By default we run all batch jobs of latest group.
            # this can be changed in configurations
            settings = self._load_user_settings()
            if 'run_configs' in settings.keys():
                auto_run = settings['run_configs'].get('auto_run', True)
            else:
                auto_run = True

            if self.debug:
                pass
            elif auto_run:
                if batch_jobs.children:
                    run_batch('all')
                else:
                    run()

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
                               path_to_json_file=self.app_config_file)
        except Exception as e:
            print(e)
        self.retriever.app_config_dict = app_dict

    def _set_cache(self,
                   cache_dict: dict = None):
        json_handler.write(data=cache_dict,
                           path_to_json_file=self.user_cache_file)
        self.report_writer = None
        self.retriever.cache = cache_dict

    def _help(self):
        # static help text
        def link(url, url_txt) -> str:
            return f'<a href="{url}" target="_blank">' \
                   f'<font color="DarkBlue">{url_txt}</font></a>'

        images_dir = os.path.join(self.code_dir, 'images')
        start_menu_png = os.path.join(images_dir, 'start_menu.png')
        group_menu_png = os.path.join(images_dir, 'group_menu.png')
        config_menu_png = os.path.join(images_dir, 'config_menu.png')
        with open(start_menu_png, 'rb') as f:
            start_img = wd.Image(value=f.read())
            start_img.layout.height = '28px'

        with open(group_menu_png, 'rb') as f:
            group_img = wd.Image(value=f.read())
            group_img.layout.height = '28px'

        with open(config_menu_png, 'rb') as f:
            config_img = wd.Image(value=f.read())
            config_img.layout.height = '28px'

        wide_layout = wd.Layout(width='auto', height='auto', max_width='80%')
        column_layout = wd.Layout(width='auto', height='auto', max_width='60%')
        p_class_txt = wd.HTML()
        p_class_txt.value = '<style> ' \
                            '    p.line_height {line-height: 1.3; } ' \
                            '</style>'
        p_class = '<p class="line_height">'
        main_txt1 = wd.HTML(disabled=True,
                            layout=wide_layout)
        main_txt2 = wd.HTML(disabled=True,
                            layout=wide_layout)
        start_txt = wd.HTML(disabled=True,
                            layout=column_layout)
        group_txt1 = wd.HTML(disabled=True,
                             layout=column_layout)
        group_txt2 = wd.HTML(disabled=True,
                             layout=column_layout)
        definition_txt = wd.HTML(disabled=True,
                                 layout=wd.Layout(width='auto', height='auto',
                                                  max_width='50%'))
        config_txt = wd.HTML(disabled=True,
                             layout=column_layout)
        margin_str = '&nbsp' * 6
        margin = wd.HTML(value=margin_str)
        link_cp = link("https://data.icos-cp.eu/portal/", "ICOS Carbon Portal")
        mail_cp = link("mailto:info@icos-cp.eu", "info@icos-cp.eu")
        mail_ad = link("mailto:anders.dahlner@nateko.lu.se",
                       "anders.dahlner@nateko.lu.se")

        widgets = wd.VBox([p_class_txt,
                           main_txt1,
                           wd.HBox([start_img, start_txt]),
                           wd.HBox([group_img, wd.VBox([group_txt1,
                                                        wd.HBox([margin,
                                                                 definition_txt]),
                                                        group_txt2])
                                    ]),
                           wd.HBox([config_img, config_txt]),
                           main_txt2])

        main_txt1.value = f'{p_class}<br>' \
                          'This application is aimed to ' \
                          'assist ' \
                          'principal investigators of ICOS Ecosystem stations ' \
                          'to quality check and analyse NRT data. ' \
                          'from stations.<br><br>' \
                          '</p>'
        start_txt.value = f'{p_class}The <i>Start</i>-menu is the ' \
                          f'standard view of the application, basically ' \
                          f'it is a report writer. Here the user can run ' \
                          f'reports to produce plots and statistics on ICOS ' \
                          f'data.<br></p>'
        group_txt1.value = f'{p_class}In the <i>Group</i>-menu the user can ' \
                           'create <i>groups of variables</i>.<br> '
        definition_txt.value = f'{p_class}<i><b>Definition: </b>' \
                               'A group of variables is a list of variables ' \
                               'where each variable is an ingested ' \
                               'variable<sup>1</sup> from one of the files ' \
                               '<b>ETC NRT Fluxes</b>, <b>ETC NRT Meteo</b>,' \
                               '<b>ETC NRT Meteosens</b>, of some ICOS ' \
                               'station.</i><br>'
        group_txt2.value = f'{p_class}In particular a group of variables may ' \
                           'contain variables from different station and ' \
                           'files.<br>' \
                           f'<u>{margin_str}{margin_str}{margin_str}</u><br>' \
                           '<sup>1</sup> <i>That a variable is ingested means ' \
                           'that it is previewable at the ' \
                           f'{link_cp}.'

        config_txt.value = f'{p_class}In the <i>Configurations</i>-menu the ' \
                           'user can:<br> ' \
                           f'{margin_str} - change the <i>Default settings</i> ' \
                           'on what data to fetch and manipulate ' \
                           'layouts of plots.<br>' \
                           f'{margin_str} - use the <i>Batch jobs</i> to set ' \
                           'up sequences of outputs, i.e. plots of statistics, ' \
                           'to produce. Here variables for the outputs are ' \
                           'selected from a group of variables.'

        main_txt2.value = f'<br>{p_class}For comments, questions, bug reports ' \
                          f'or ' \
                          'any other kind of feedback, ' \
                          f'please feel free to contact: {mail_cp} or ' \
                          f'{mail_ad}.</p>'

        display(widgets)

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

    def _edit_batch_jobs(self,
                         _group_name: str = None,
                         _batch_name: str = None) -> wd.VBox:
        if self.debug:
            print('*** _edit_batch_jobs()\n')

        def _get_multi_plot_auto() -> bool:
            settings = self._load_user_settings()
            multi_p_kwargs = settings.get('multi_plot_kwargs', {})
            return multi_p_kwargs.get('auto_axis', True)

        def reset_batch_gui(batch_name: str = None):

            if self.debug:
                debug_value(1, 'reset_batch_gui()', 'step 1',
                            f'batch_name = {batch_name}')
            init_batch_drop(batch_name)
            activate_gui('reset_gui')

            if self.debug:
                debug_value(1, 'reset_batch_gui()', '--- end ---')

        def init_tool_buttons():
            tool_ls = []
            for tool_name in tool_names:
                bt = wd.Button(description=tool_name,
                               style={'button_color': 'LightGreen'},
                               layout=AnalysisGui._get_width_layout(tool_name))
                bt.on_click(tool_click)
                tool_ls.append(bt)
            tool_buttons.children = tool_ls

        def init_group_drop():
            cache = self._load_cache()
            group_ls = list(cache['_groups'].keys())

            if self.debug:
                debug_value(0, f'init_group_drop()', '--- start ---',
                            f'group list = {group_ls}')
            if group_ls:
                group_ls = sorted(group_ls)
                group_drop.options = group_ls

        def set_group_value(group: str = None):
            # triggers other widgets at startup
            cache = self._load_cache()
            group_ls = group_drop.options
            if self.debug:
                debug_value(0, f'set_group_value()   --- Here we go ----',
                            f'group = {group}')

            if group and group in group_ls:
                group_drop.value = group
            else:
                grp = cache.get('_last_group', None)
                if grp and grp in group_ls:
                    group_drop.value = grp
                else:
                    group_drop.value = group_ls[0]

        def changed_group_drop(c):
            if self.debug:
                debug_value(2, f'changed_group_drop()')
            set_group_var_info()
            set_var_translation_dict()
            init_group_var_buttons(mode='delete')
            reset_batch_gui()

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
                debug_value(*debug_ls)
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

        def init_group_var_buttons(mode: str):
            if self.debug:
                debug_ls = [6, f'init_group_var_buttons()']
                debug_value(*debug_ls)

            if mode == 'create' and not var_buttons.children:
                var_list = list(get_var_translation_dict().items())
                var2unit_dict = get_var2unit_dict()
                btn_ls = []
                for v_name, var_ls in var_list[:-1]:
                    unit = var2unit_dict.get(var_ls[0], var2unit(var_ls))
                    btn = wd.Button(description=v_name,
                                    disabled=True,
                                    tooltip=unit,
                                    style={'button_color': 'LightSeaGreen'},
                                    layout=AnalysisGui._get_width_layout(v_name))
                    btn.on_click(var_button_click)
                    btn_ls.append(btn)
                v_name = 'Select all'
                btn = wd.Button(description=v_name,
                                disabled=True,
                                tooltip='',
                                style={'button_color': 'MediumSeaGreen'},
                                layout=AnalysisGui._get_width_layout(v_name))
                btn.on_click(var_button_click)
                btn_ls.append(btn)
                var_buttons.children = btn_ls
            elif mode == 'reset':
                for b in var_buttons.children:
                    b.icon = ''
            elif mode == 'delete':
                for b in var_buttons.children:
                    b.unobserve_all()
                    b.close()
                    del b

        def init_batch_drop(batch_name: str = None):
            cache = self._load_cache()
            group = group_drop.value
            if self.debug:
                debug_value(9, 'init_batch_drop()', 'step 1',
                            f'(input) batch_name = {batch_name}',
                            f'group = {group}',
                            f"cache['_groups']['{group}'] = "
                            f"{cache['_groups'][group]}")

            batch_dict = cache['_groups'][group].get('_batches',{})
            if self.debug:
                debug_value(9, 'init_batch_drop()', 'step 2',
                            f'batches = {batch_dict}')
            if batch_dict:
                batch_labels = sorted(list(batch_dict.keys()))
                batch_drop.options = [(k, batch_dict[k]) for k in batch_labels]
                if batch_name and batch_name in batch_dict.keys():
                    batch_drop.value = batch_dict[batch_name]
                    changed_batch_drop('reset_batch_gui')
                else:
                    batch_drop.value = list(batch_dict.values())[0]
            else:
                batch_drop.options = [('Press new...', 0)]
                #batch_drop.value = 0
                html_msg(text_ls=[f'Press "New", in order to create a batch '
                                  f'job for the group <i>{group}</i>.'])
            if self.debug:
                debug_value(9, 'init_batch_drop()', 'step 3',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch_drop.value}',
                            f'-- end--')

        def changed_batch_drop(c):
            if batch_drop.value:
                batch = batch_drop.value.copy()
            else:
                batch = 0
            if self.debug:
                debug_ls = [11, 'changed_batch_drop()', '- step 1 - batch '
                                                        'value changed, '
                                                        'reset displayed '
                                                        'selections',
                            f'c = {c}',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch}']
                debug_value(*debug_ls)

            if batch != 0:
                batch_version = batch.pop('_version', '0')
                set_batch_upd_dict(dict(_upd_mode='read_mode_with_batch',
                                        _tools=batch,
                                        _selected_tool_index=None,
                                        _version=batch_version))
            else:
                set_batch_upd_dict(dict(_upd_mode='read_mode_no_batch',
                                        _tools={}))
            set_user_guide()

            if self.debug:
                debug_ls = [11, 'changed_batch_drop()', '- step 2 - ',
                            f'upd_dict_log.value = {upd_dict_log.value}']
                debug_value(*debug_ls)

        def reset_selection(c):
            # TODO: check what has changed and divide the update accordingly

            batch_dict = get_batch_upd_dict()

            if self.debug:
                debug_ls = [13, f'reset_selection()',
                            f'c = {c}',
                            f'batch_dict = {batch_dict}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(*debug_ls)

            sel_tool_index = batch_dict.pop('_selected_tool_index', None)
            tools = batch_dict.get('_tools', {})
            sel_tools = [(tool2name_dict[k2], k1) for k1, v1 in tools.items() for
                         k2 in v1.keys()]
            sel_vars = format_tool_vars(tools)

            set_selections(sel_tool_ls=sel_tools,
                           sel_tool_index=sel_tool_index,
                           sel_var_ls=sel_vars)

            if batch_dict['_upd_mode'] in ['new', 'update']:
                reset_var_buttons()

        def format_tool_vars(tools):
            # formatting var list to selected_var widget
            if self.debug:
                debug_ls = [15, f'label_of_selected_var_row()',
                            f'tool_code = {tools}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(*debug_ls)

            sel_vars = []
            if tools:
                var_trans_dict = get_var_translation_dict()
                for index, tool_dict in tools.items():
                    for tool_code, tool_vars in tool_dict.items():
                        if isinstance(tool_vars, str):
                            # the case 'all'
                            label_ls = ['All variables']
                        elif tool_code != 'multi_plot':
                            # the case of list of var-lists
                            label_ls = [var_name for x in tool_vars for var_name
                                        in
                                        var_trans_dict.keys() if
                                        var_trans_dict[var_name] == x]
                        else:
                            # the case of list of axes and var-lists
                            label_ls = [var_name for x in tool_vars for y in x[1]
                                        for
                                        var_name in
                                        var_trans_dict.keys() if
                                        var_trans_dict[var_name] == y]
                        label_for_tool_vars = ', '.join(label_ls)
                        sel_vars.append((label_for_tool_vars, (index, tool_vars)))

            return sel_vars

        def set_selections(sel_tool_ls: list,
                           sel_tool_index: int = -1,
                           sel_var_ls: list = None):
            # Sometimes we want to set the index to None,
            # this is why we have default value -1.
            if self.debug:
                debug_ls = [16, f'set_selections()',
                            'step 1',
                            f'sel_tool_ls = {sel_tool_ls}',
                            f'sel_tool_index = {sel_tool_index}',
                            f'sel_var_ls = {sel_var_ls}']
                debug_value(*debug_ls)

            rows = 3 + (len(sel_tool_ls) // 2) * 2
            selected_tools.rows = rows
            selected_vars.rows = rows

            selected_tools.unobserve(changed_selected_tool, names='value')
            selected_tools.options = sel_tool_ls
            if isinstance(sel_tool_index, int) and sel_tool_index >= 0:
                selected_tools.value = sel_tool_index
            elif sel_tool_index is None:
                selected_tools.value = sel_tool_index
            selected_tools.observe(changed_selected_tool, names='value')

            if isinstance(sel_var_ls, list):
                selected_vars.options = sel_var_ls
            if selected_tools.value is not None:
                try:
                    ind = selected_tools.value
                    selected_vars.tooltip = selected_vars.options[ind][0]
                except:
                    if self.debug:
                        debug_ls = [16, f'set_selections()', 'exception',
                                    f'selected_vars.options = '
                                    f'{selected_vars.options}',
                                    f'ind = {selected_tools.value}']
                        debug_value(*debug_ls)
                    selected_vars.tooltip = ''
            else:
                selected_vars.tooltip = ''

            if self.debug:
                debug_ls = [16, f'set_selections()', 'end ',
                            f'selected_tools.value = {selected_tools.value}',
                            f'selected_tools.options = {selected_tools.options}',
                            f'selected_vars.options = {selected_vars.options}',
                            f'selected_vars.tooltip = {selected_vars.tooltip}']
                debug_value(*debug_ls)

        def changed_selected_tool(c):
            # Triggered when a tool is selected,
            # not triggered by tool buttons
            if self.debug:
                debug_value(112, f'changed_selected_tool() -- triggered tool',
                            f'c = {c}')

            # Depending on c.old we might have to modify the selection index
            selected_index = c.new

            # Also, in order to avoid more work than necessary we set
            upd_changed = False

            # In case of a deselected tool with no variables we must
            # clean up the selected_vars widget
            if isinstance(c.old, int):
                upd_dict = get_batch_upd_dict()
                tools = upd_dict.get('_tools', {})
                upd_dict['_tools'], upd_changed = cleanup_tools(tools)

                if upd_changed:
                    if isinstance(selected_index, int) and selected_index > c.old:
                        selected_index = selected_index - 1
                if upd_dict['_selected_tool_index'] != selected_index:
                    upd_dict['_selected_tool_index'] = selected_index
                    upd_changed = True

                if upd_changed:
                    # this will trigger reset_var_buttons()
                    set_batch_upd_dict(upd_dict)

            if selected_index is None:
                info_type = 'upd'
            else:
                sel_tools = list(selected_tools.options)
                tool_name = sel_tools[selected_index][0]
                info_type = name2tool_dict[tool_name]

            if info_type != 'multi_plot':
                reset_multi_plot_auto(hide=True)
            else:
                upd_dict = get_batch_upd_dict()
                var_codes = list(upd_dict['_tools'][selected_index].values())[0]
                axis_ls = [axis[0] for axis in var_codes]
                mp_auto_enable = not len(axis_ls) == 2
                mp_auto_value = not len(axis_ls) != len(set(axis_ls))
                reset_multi_plot_auto(hide=False,
                                      enable=mp_auto_enable,
                                      value=mp_auto_value)

            set_info_guide(info_type=info_type)

            if not upd_changed:
                reset_var_buttons()

        def set_info_guide(info_type: str = None):
            # set info text depending on update mode and tool
            # show/hide buttons etc
            # cases of info_type:
            # 'upd', 'new', 'update', multi_plot, 'corr_plot',
            # 'split_plot', 'corr_table', 'statistics'

            if self.debug:
                debug_value(129, f'set_info_guide()',
                            f'info_type = {info_type}')

            if info_type == 'reset_gui':
                msg_ls = ['<b>You are in <i>read mode</i>.</b> '
                          'Either select a group of variables or a ' 
                          'batch job, and choose <i>New</i>, or <i>Update</i>.']
            else:
                msg_ls = ['<b>You are in <i>update mode</i>.</b> ']
                if info_type == 'new':
                    msg_ls.extend(['To create a new batch job: ',
                                  '1. Choose at least one tool from the '
                                  'list of <i>Available tools</i>, and add some '
                                  'variables to it.',
                                   '2. Choose a name for the batch job. '])
                elif name_of_batch_job.value == 'Name of batch job':
                    msg_ls.append('Remember to choose a name for the '
                                  'batch job in the above area <b><i>Batch '
                                  'name<b></i>.')
                if info_type == 'update':
                    msg_ls.extend(['<b><i>To edit</i></b> the content of a tool: '
                                  'Select the tool to in the list above, '
                                  'and use the variable buttons to add or '
                                  'remove them from the tool.',
                                  '<b><i>To delete</i></b> the batch job, just press '
                                  '<b><i>Delete</i></b> without changing the '
                                  'content.'])
                elif info_type == 'multi_plot':
                    msg_ls.extend(['<b><i>Multi-plot</i></b> selected. ',
                                   'With a multi-plot you can plot several '
                                   'variables in the same figure.',
                                   'Please note that there are at most two '
                                   '$y$-axes, and <i>each axis will only hold '
                                   'variables of the same unit</i> (where '
                                   '"unitless" is regarded as a unit). ',
                                   'By default, variables are automatically '
                                   'distributed among the axes depending on '
                                   'their units. This behaviour can be '
                                   'changed with '
                                   f'<i>{multi_plot_auto_cb.description}</i>. ',
                                   'If unchecked, the first click on a '
                                   'variable will add it to the left $y$-axis, '
                                   'the second click will move it to the right '
                                   '$y$-axis provided both axis have the same '
                                   'unit.'])
                elif info_type == 'corr_plot':
                    msg_ls.extend(['<b><i>Correlation plot</i></b> selected.',
                                   'The correlation plot is used to plot two '
                                   'and only two, variables against each other. ',
                                   'The first selected variable is mapped to '
                                   'the $x$-axis while the second variable is '
                                   'mapped to the $y$-axis.'])
                elif info_type == 'split_plot':
                    msg_ls.extend(['<b><i>Split-plot</i></b> selected.',
                                   'With the split-plot you plot several '
                                   'variables in different but '
                                   'interconnected figures, having a shared '
                                   'zoom-tool.'])
                elif info_type == 'upd':
                    msg_ls.extend([f'Either select or add some tool to the '
                                   f'batch job.'])
                elif info_type in tool2name_dict.keys():
                    msg_ls.extend([f'<b><i>{tool2name_dict[info_type]}</i></b> '
                                   f'selected. <b>Please note that this tools is '
                                   f'not implemented at this moment. </b>',
                                   'No restriction on the variables.'])

            info_guide.value = '<br>'.join(msg_ls)

        def set_user_guide():
            if user_guide_container.layout.display == 'block':
                d = get_batch_upd_dict().get('_upd_mode', {'_upd_mode': ''})
                if d['_upd_mode'] == 'read_mode_no_batch':
                    user_guide.value = '<b>To create a batch job:</b><br>' \
                                       '1. Choose a group of variables. ' \
                                       '2. Press <i>New</i> and follow the ' \
                                       'directions.'
                elif d['_upd_mode'] == 'read_mode_with_batch':
                    user_guide.value = '<b>To create a batch job:</b><br>' \
                                       '1. Choose a group of variables.<br>' \
                                       '2. Press <i>New</i> and follow the ' \
                                       'directions.<br>' \
                                       '<b>To change or delete a batch ' \
                                       'job:</b><br>' \
                                       '1. Select the group of variables and ' \
                                       'the batch job.<br>' \
                                       '2. Press <i>Update</i>. and follow the ' \
                                       'directions.<br>' \
                                       '3. In case the batch job should be ' \
                                       'deleted, just press <i>Delete</i> ' \
                                       'without changing the content.'

        def reset_multi_plot_auto(hide: bool,
                                  enable: bool = None,
                                  value: bool = None):

            if self.debug:
                debug_value(131, 'reset_multi_plot_auto() - before',
                            f'hide = {hide}',
                            f'enable = {enable}',
                            f'multi_plot_auto_cb.disabled = '
                            f'{multi_plot_auto_cb.disabled}',
                            f'multi_plot_auto_cb.layout.display'
                            f' = {multi_plot_auto_cb.layout.display}',
                            f'multi_plot_auto_cb.value = '
                            f'{multi_plot_auto_cb.value}')
            if hide:
                multi_plot_auto_cb.layout.display = 'none'
                multi_plot_auto_cb.disabled = True
            else:
                multi_plot_auto_cb.layout.display = 'block'
                if isinstance(enable, bool):
                    multi_plot_auto_cb.disabled = not enable
                if isinstance(value, bool):
                    multi_plot_auto_cb.value = value

        def reset_var_buttons():
            tool_index = selected_tools.value
            if self.debug:
                debug_value(17, 'reset_var_buttons()   --- start ---',
                            f'  - index of selected_tools = {tool_index}')
            if tool_index is None:
                if self.debug:
                    debug_value(17, 'reset_var_buttons()   -- index = None',
                                '  -- deselecting and disabling all ',
                                'var-buttons and the "Up"-btn')
                move_up.disabled = True
                for btn in var_buttons.children:
                    btn.disabled = True
                    btn.icon = ''
            elif isinstance(tool_index, int):
                move_up.disabled = False
                upd_dict = get_batch_upd_dict()
                row_dict = upd_dict['_tools'][tool_index]
                var_trans_dict = get_var_translation_dict()
                for tool_code, var_codes in row_dict.items():
                    if self.debug:
                        debug_value(17, f'reset_var_buttons()  -- index '
                                        f'= {tool_index}',
                                    f'  --- tool_code = {tool_code}',
                                    f'  --- var_codes = {var_codes}')
                    if tool_code == 'multi_plot':
                        # for multi_plot var_codes look like this:
                        # [['%', [['SWC_1', 'ETC NRT Meteo', 'SE-Htm'],
                        #         ['SWC_2', 'ETC NRT Meteo', 'SE-Htm']]],
                        #  ['mmol mol-1', [['H2O', 'ETC NRT Fluxes', 'SE-Htm']]]]
                        axis_ls = [axis[0] for axis in var_codes]
                        if len(axis_ls) == 2:
                            y1, y2 = var_codes
                            _, y1_vars = y1
                            _, y2_vars = y2
                        elif len(axis_ls) == 1:
                            _, y1_vars = var_codes[0]
                            y2_vars = []
                        else:
                            y1_vars = []
                            y2_vars = []

                        for btn in var_buttons.children:
                            btn_var_code = var_trans_dict[btn.description]

                            if btn_var_code in y1_vars:
                                btn.icon = 'angle-double-left'
                                btn.disabled = False
                            elif btn_var_code in y2_vars:
                                btn.icon = 'angle-double-right'
                                btn.disabled = False
                            elif (len(axis_ls) == 2 and
                                  btn.tooltip not in axis_ls) or \
                                    btn.description == 'Select all':
                                btn.icon = ''
                                btn.disabled = True
                            else:
                                btn.icon = ''
                                btn.disabled = False

                    elif tool_code == 'corr_plot':
                        if self.debug:
                            debug_value(17, f'reset_var_buttons() --- restore '
                                            f'buttons ---')
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

        def move_selected(move_click):
            index = selected_tools.value
            if self.debug:
                debug_ls = [113, f'move_selected() click',
                            f'tool index = {index}']
                debug_value(*debug_ls)

            if index is not None:
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
                debug_value(114, f'tool_click()',
                            f'tool.description = {tool.description}',
                            f'tool.icon = {tool.icon}')
            if tool.icon:
                tool.style.button_color = "LightGreen"
                tool.icon = ''
                tool_added = False
            else:
                for btn in tool_buttons.children:
                    if btn != tool:
                        btn.style.button_color = "LightGreen"
                        btn.icon = ''
                tool.style.button_color = "Green"
                tool.icon = 'check'
                tool_added = True
            update_tool_list(add_tool=tool_added,
                             tool_name=tool.description)

        def update_tool_list(add_tool,
                             tool_name):
            # Similar to, but different from changed_selected_tool()
            # at this stage the tool is not in the upd_dict.
            if self.debug:
                debug_value(115, f'update_tool_list() -- input',
                            f'add_tool = {add_tool}',
                            f'tool_name = {tool_name}')

            # We must remove empty rows, in case this or another tool was
            # deselected without variables.
            tools = get_batch_upd_dict().get('_tools', {})
            tools, _ = cleanup_tools(tools)

            if self.debug:
                debug_value(115, f'update_tool_list()',
                            f'tools (cleaned) ={tools}')

            if add_tool:
                tool_code = name2tool_dict[tool_name]
                info_type = tool_code
                key = len(tools.keys())
                tools[key] = {tool_code: []}
                selected_tools.disabled = True
                if tool_code == 'multi_plot':
                    # A new multi-plot is added
                    new_multi_plot = True
                else:
                    new_multi_plot = False
            else:
                # Tool button is deselected
                info_type = 'upd'
                new_multi_plot = False
                key = None
                selected_tools.disabled = False

            if new_multi_plot:
                reset_multi_plot_auto(hide=False,
                                      enable=True,
                                      value=_get_multi_plot_auto())
            else:
                reset_multi_plot_auto(hide=True)

            update_batch_dict(dict(_tools=tools,
                                   _selected_tool_index=key))
            set_info_guide(info_type=info_type)

        def var_button_click(btn):

            upd_dict = get_batch_upd_dict()['_tools']
            row_index = selected_tools.value
            if self.debug:
                debug_ls = [116, f'var_button_click()',
                            f'btn.description = {btn.description}',
                            f'selected_tools.value = {row_index}',
                            f'before:'
                            f' - upd_dict[row_index] = {upd_dict[row_index]}']
                debug_value(*debug_ls)

            for tool_code, upd_var_codes in upd_dict[row_index].items():
                if self.debug:
                    debug_ls = [116, f'var_button_click() ***',
                                f'tool_code = {tool_code}',
                                f'upd_var_codes = {upd_var_codes}']
                    debug_value(*debug_ls)
                var_trans_dict = get_var_translation_dict()
                var_name = btn.description
                var_code = var_trans_dict[var_name]
                if var_code == 'All variables':
                    if upd_var_codes != 'all':
                        upd_var_codes = 'all'
                    else:
                        upd_var_codes = []
                elif tool_code != 'multi_plot':
                    if var_code in upd_var_codes:
                        upd_var_codes.remove(var_code)
                    else:
                        upd_var_codes.append(var_code)
                elif tool_code == 'multi_plot':
                    if self.debug:
                        debug_ls = [116, f'var_button_click()**** * * * ***',
                                    f'tool_code = {tool_code}',
                                    f'multi_plot_auto_cb.value = '
                                    f'{multi_plot_auto_cb.value}']
                        debug_value(*debug_ls)
                    unit = var2unit(var_code)
                    if multi_plot_auto_cb.value:
                        axis_of_var = None
                        # unit must match
                        for v in upd_var_codes:
                            if v[0] == unit:
                                axis_of_var = v
                                if var_code in v[1]:
                                    v[1].remove(var_code)
                                else:
                                    v[1].append(var_code)
                        if axis_of_var is None:
                            upd_var_codes.append((unit, [var_code]))
                    else:
                        if len(upd_var_codes) == 0:
                            upd_var_codes.append([unit, [var_code]])
                        elif len(upd_var_codes) == 1:
                            y_unit, y_vars = upd_var_codes[0]
                            if y_unit == unit and var_code not in y_vars:
                                # add var to the axis
                                y_vars.append(var_code)
                            elif y_unit == unit:
                                y_vars.remove(var_code)
                                if y_vars:
                                    # add var to new axis only when the
                                    # first axis has variables.
                                    upd_var_codes.append([unit, [var_code]])
                            else:
                                # add the var to a new axis
                                upd_var_codes.append([unit, [var_code]])
                        elif len(upd_var_codes) == 2:
                            y1, y2 = upd_var_codes
                            y1_unit, y1_vars = y1
                            y2_unit, y2_vars = y2
                            if y1_unit == unit and var_code in y1_vars:
                                # remove var from y1
                                y1_vars.remove(var_code)
                                if y2_unit == unit:
                                    # add var to y2
                                    y2_vars.append(var_code)
                            elif y1_unit == unit:
                                # the var is not in y1 and should
                                # be added to y1 provided it is not in y2
                                if y2_unit == unit:
                                    if var_code in y2_vars:
                                        # the var is in y2 and should be removed
                                        y2_vars.remove(var_code)
                                    else:
                                        # the var is added to y1
                                        y1_vars.append(var_code)
                                else:
                                    # the var is added to y1
                                    y1_vars.append(var_code)
                            elif y2_unit == unit:
                                if var_code in y2_vars:
                                    y2_vars.remove(var_code)
                                else:
                                    y2_vars.append(var_code)
                    # finally we only keep non-empty
                    upd_var_codes = [y for y in upd_var_codes if y[1]]
                    multi_plot_auto_cb.disabled = (len(upd_var_codes) == 2)
                    if self.debug:
                        debug_ls = [116, f'var_button_click()',
                                    f'tool_code = {tool_code}',
                                    f'multi_plot_auto_cb.value = '
                                    f'{multi_plot_auto_cb.value}']
                        debug_value(*debug_ls)

                upd_dict[row_index] = {tool_code: upd_var_codes}
                if self.debug:
                    debug_ls = [116, f'var_button_click()',
                                f'after:',
                                f' - upd_dict[row_index] = {upd_dict[row_index]}']
                    debug_value(*debug_ls)

                update_batch_dict(dict(_tools=upd_dict,
                                       _selected_tool_index=row_index))

        # def selections2batch_dict() -> dict:
        #     if self.debug:
        #         debug_ls = [117, f'selections2batch_dict()']
        #         debug_value(*debug_ls)
        #
        #     d = dict()
        #     t_ls = selected_tools.options
        #     v_ls = [v[1][1] for v in selected_vars.options]
        #     ind = range(len(t_ls))
        #     d['_tools'] = {k: {name2tool_dict[t_ls[k][0]]: v_ls[k]} for k in
        #     ind}
        #     d['_selected_tool_index'] = selected_tools.index
        #     return d

        def get_var2unit_dict():
            if self.debug:
                debug_value(32, f'get_var2unit_dict()')
            d = eval(var_to_unit_dict.value)
            if not(d and isinstance(d, dict)):
                d = self._load_app_configs().get('_var2unit_map', {})
                var_to_unit_dict.value = str(d)
            return d

        def var2unit(var, update: bool = False):
            var2unit_dict = get_var2unit_dict()
            if update or var[0] not in var2unit_dict.keys():
                pid = st_df.loc[(st_df.id == var[-1]) & (
                        st_df.specLabel == var[1])].dobj.values[0]
                meta = icos_data.StationData.icos_pid2meta(pid)
                var_unit_list = meta['varUnitList']
                var2unit_dict.update({v[0]: v[1] for v in var_unit_list})
                app_configs = self._load_app_configs()
                app_configs['_var2unit_map'].update(var2unit_dict)
                self._set_app_configs(app_dict=app_configs)
                var_to_unit_dict.value = str(var2unit_dict)

            unit = var2unit_dict[var[0]]
            if self.debug:
                debug_value(8, f'var2unit()', f'var = {var}',
                            f'return unit = {unit}')
            return unit

        def set_group_var_info():
            cache = self._load_cache()
            if self.debug:
                debug_ls = [4, f'set_group_var_info()']
                debug_value(*debug_ls)

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
                debug_value(*debug_ls)

            grp = group_drop.value
            if grp not in cache['_groups'].keys():
                return_val = ''
            else:
                var_tuples = cache['_groups'][grp]['_group_vars']
                var_ls = [v[0] for v in var_tuples]
                text_tag = 'b'
                separator = '<br>'
                margin = '&nbsp' * 10
                station_dict = AnalysisGui._var_tup2station_dict(var_tuples)

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
                                t1 = f'<{text_tag}>Variables (of ' \
                                     f'{prod} at {stn}): </{text_tag}>'
                            else:
                                t3 += f'{separator}{margin}<{text_tag}>{prod}: ' \
                                      f'</{text_tag}>' + \
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

        def debug_value(*text_list):

            caller_id = None
            if text_list:
                if isinstance(text_list[0], int):
                    caller_id, *text_list = text_list

            msg = self.debugger.debug_value(*text_list,
                                            external_id=caller_id,
                                            stack_start=2,
                                            stack_depth=5)
            if self.debug:
                with debug_out:
                    display(wd.HTML(msg))

        def html_msg(text_ls: list = None,
                     title: str = None,
                     error: bool = None,
                     show_user_guide: bool =None):
            if self.debug:
                debug_ls = [118, f'html_msg()']
                debug_value(*debug_ls)

            margin = '&nbsp' * 6  # html space

            if error:
                msg_title = 'Things to fix: '
                color = self.widget_style_colors['danger:active']
                emoji = '\u26a0\ufe0f'  # warning_emoji
            elif title:
                msg_title = title
                color = self.widget_style_colors['info:active']
                emoji = ''
            else:
                msg_title = 'Info: '
                color = self.widget_style_colors['info:active']
                emoji = ''

            msg = f'<span style="color:{color}">'
            msg += f'{margin}<h3>{msg_title} {emoji}</h3>'
            if isinstance(text_ls, list):
                msg += f'<h3>{margin}'
                msg += f'<br>{margin}'.join(text_ls)
                msg += '</h3></span>'
            if show_user_guide:
                user_guide.value = msg
            with out:
                clear_output()
                display(wd.HTML(msg))

        def html_error_msg(error_ls: list = None):
            if self.debug:
                debug_value(119, f'html_error_msg()')
            html_msg(text_ls=error_ls, error=True)

        def set_info_msg(error_ls=None):
            upd_dict = get_batch_upd_dict()
            upd_mode = upd_dict.get('_upd_mode', None)
            grp = group_drop.value

            if upd_mode == 'new':
                index = upd_dict['_selected_tool_index']
                index = str(index)
                if index in upd_dict['_tools'].keys():
                    tool = list(upd_dict['_tools'][index].keys())[0]
                else:
                    tool = None

                if tool == 'multi_plot':
                    info_ls = ['Please note that <i>Multi-plot</i> will '
                               'use at most <i>two $y$-axes</i> , and by '
                               'default the variables are divided according '
                               'to their unit.']
                elif tool == 'corr_plot':
                    info_ls = ['Please note that <i>Correlation-plot</i> '
                               'is a plot for <i>exactly two '
                               'variables</i>.',
                               'The first variable belongs to the '
                               'horizontal axis (the $x$-axis), while the '
                               'second variable '
                               'belongs to the vertical axis (the $y$-axis).']
                else:
                    info_ls = [f'To create a batch job for the group {grp}:',
                               '1. Select <i>tools</i> (one at a time) from '
                               'the list in <i>Available tools</i> below. '
                               'These will be displayed in the 1:st list to the '
                               'right of the label <i>Current setup</i>.',
                               '2. Select/deselect preferred variables for the '
                               'chosen tool. These will be displayed in the 2:st '
                               'list to the right of the label <i>Current'
                               ' setup</i>.',
                               '3. Choose a name for the batch job in '
                               'the area <span style="color:black">"Name of '
                               'batch job"</span>.',
                               '4. Press save.',
                               '',
                               '<b> - A batch job may contain several '
                               '<i>tools</i>.</b>',
                               '<b> - The list of the tools also represents the '
                               'order of execution of the batch job, and the '
                               'order of the variables will be the order of '
                               'presentation in plots, etc.</b>',
                               '<b> - To rearrange the order of execution '
                               'select a tool to the right of the '
                               '<i>"Up"</i>-button and click "Up".</b>']
            elif upd_mode == 'update':
                info_ls = ['In update mode you can:',
                           '1. Add or remove variables of a group.',
                           '2. Change the group name.',
                           '3. Delete the group.',
                           '',
                           '<b>The order of the variables is the order of '
                           'presentation in plots, etc.</b>',
                           '<b>Changes are logged in the file '
                           '"/appdata/cache_bak.json".</b>']
            else:
                info_ls = ['Steps',
                           'Start by choosing a group of variables. ',
                           'Use <i>New</i> to create a new batch job.',
                           'Use <i>Update</i> in case you wish to change or '
                           'delete a batch job.']

            margin = '&nbsp' * 3

            if info_ls:
                info_color = self.widget_style_colors['primary:active']
                msg = f'<span style="color:{info_color}">{margin}{margin}<h4>' \
                      f'{info_ls[0]}</h4><b>'

                for row in info_ls[1:]:
                    msg += f'{margin}{row}<br>'
                msg += '</b></span>'
            else:
                msg = ''

            if error_ls:
                warning_emoji = '\u26a0\ufe0f'
                error_color = self.widget_style_colors['danger:active']
                msg += f'<br><span style="color:{error_color}">{margin}{margin}'
                msg += f'<h3>To do: {warning_emoji}</h3><b>'
                for error in error_ls:
                    msg += f'{margin}{error}<br>'
                msg += '</b></span>'

            if error_ls and user_guide_container.layout.display == 'none':
                display_user_guide('display_guide')

            user_guide.value = msg

        def cleanup_tools(d: dict) -> (dict, bool):
            # returns "a clean tool-dict" and "dict has changed"
            if self.debug:
                debug_value(120, f'cleanup_tools() -- (before)',
                            f"upd_dict['_tools'] = {d}")

            if isinstance(d, dict) and d:
                d_copy = d.copy()
                for tool_number, tool_var in d_copy.items():
                    for t_name in tool_var.keys():
                        if not tool_var[t_name]:
                            d.pop(tool_number)
                        elif t_name == 'corr_plot' and len(tool_var[t_name]) != 2:
                            d.pop(tool_number)
                dict_has_changed = d != d_copy
                if dict_has_changed:
                    # reset the tool number
                    d = dict(zip(range(len(d.keys())), d.values()))
            else:
                dict_has_changed = False

            if self.debug:
                debug_value(120, f'cleanup_tools() -- (after)',
                            f'd = {d}',
                            f'dict_has_changed = {dict_has_changed}')

            return d, dict_has_changed

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
                            f'There is already a batch job called '
                            f'<i>{name}</i>,')
                        error_ls.append('please pick another name.')

            if error_ls:
                name_of_batch_job.style.text_color = 'red'
            else:
                name_of_batch_job.style.text_color = 'darkgreen'
                name_of_batch_job.layout = AnalysisGui._get_width_layout(name)

            if self.debug:
                debug_value(121, f'validate_name()',
                            f'name = {name}',
                            f'error_ls = {error_ls}')

            return error_ls

        def batch_name_changed(change):
            if self.debug:
                debug_value(122, f'batch_name_changed()',
                            f'change = {change}')

            if change.type == 'change':
                new_name = change.owner.value
                error_ls = validate_name(new_name)
                upd_dict = {}

                if error_ls:
                    if self.debug:
                        debug_value(122, f'batch_name_changed()',
                                    f'\t error_ls = {error_ls}')
                    upd_dict['_name_error'] = error_ls
                else:
                    if self.debug:
                        debug_value(122, f'batch_name_changed()',
                                    f'\t new_name={new_name}')
                    upd_dict['_new_name'] = new_name
                if self.debug:
                    debug_value(122, f'batch_name_changed()',
                                f'\t batch_drop.value={batch_drop.value}')
                update_batch_dict(upd_dict)

        def get_var_translation_dict() -> dict:
            if self.debug:
                debug_value(7, f'get_var_translation_dict()',
                            f'var_translation_dict.value = '
                            f'{var_translation_dict.value}')

            d = eval(var_translation_dict.value)
            return d

        def get_batch_upd_dict() -> dict:
            d = eval(upd_dict_log.value)
            if isinstance(d, dict):
                if '_tools' in d.keys():
                    d['_tools'] = {int(k): v for k, v in d['_tools'].items()}
            else:
                d = dict()

            if self.debug:
                debug_value(14, 'get_batch_upd_dict()', f'd ={d}')

            return d

        def set_batch_upd_dict(d: dict):
            if self.debug:
                debug_value(12, 'set_batch_upd_dict()', 'step 1', f'd ={d}')

            json_safe_dict = {k: v for k, v in d.items() if k != '_tools'}
            json_safe_dict['_tools'] = {str(k): v for k, v in d['_tools'].items()}

            upd_dict_log.value = str(json_safe_dict)
            if self.debug:
                debug_value(12, 'set_batch_upd_dict()', 'step 2',
                            f'upd_dict_log.value ={upd_dict_log.value}')

        def update_batch_dict(d: dict):
            if self.debug:
                debug_value(123, f'update_batch_dict()',
                            f'd = {d}')
            upd_dict = get_batch_upd_dict()
            for k, v in d.items():
                upd_dict[k] = v
            set_batch_upd_dict(upd_dict)

        # def set_batch_upd_selections(d: dict = None):
        #
        #
        #     if d is None:
        #         d = selections2batch_dict()
        #
        #     upd_dict = get_batch_upd_dict()
        #
        #     upd_dict['_tools'] = {str(k): v for k, v in d['_tools'].items()}
        #     upd_dict['_selected_tool_index'] = d.get('_selected_tool_index', -1)
        #     set_batch_upd_dict(upd_dict)

        def get_valid_batch():
            cache = self._load_cache()
            grp = group_drop.value
            b = batch_drop.label
            batch2validate = batch_drop.value.copy()

            if '_var_mismatch' in cache['_groups'][grp].keys():
                if b in cache['_groups'][grp]['_var_mismatch'].keys():
                    er_dict = cache["_groups"][grp]["_var_mismatch"][b]
                    if self.debug:
                        debug_ls = [128, f'validate_batch()',
                                    f'batch_drop.label = {batch_drop.label}',
                                    f'batch_drop.value = {batch2validate}',
                                    f'er_dict = {er_dict}']
                        debug_value(*debug_ls)

                    reindex = False
                    for index, tool_vars in er_dict.items():
                        for v_ls in tool_vars.values():
                            for v in v_ls:
                                for tool, val in batch2validate[index].items():
                                    if tool == 'multi_plot':
                                        for y in val:
                                            if v in y[1]:
                                                y[1].remove(v)
                                            if not y[1]:
                                                val.remove(y)
                                    else:
                                        if v in val:
                                            val.remove(v)
                                            if tool == 'corr_plot':
                                                val=[]
                                    if not val:
                                        batch2validate.pop(index)
                                        reindex = True

                    if reindex:
                        j = 0
                        d = {}
                        for i in batch2validate.keys():
                            if i != '_version':
                                d[str(j)] = batch2validate[i]
                                j += 1
                            else:
                                d[i] = batch2validate[i]

            return batch2validate

        def new_batch(c):

            with out:
                clear_output()

            upd_dict = {'_upd_mode': 'new',
                        '_version': 0,
                        '_orig_name': '',
                        '_new_name': '',
                        '_tools': {},
                        '_selected_tool_index': None}

            if self.debug:
                debug_ls = [124, 'new_batch()', f'upd_dict = {upd_dict}']
                debug_value(*debug_ls)

            set_batch_upd_dict(upd_dict)
            name_of_batch_job.value = "Name of batch job"
            activate_gui('new')

        def update_batch(c):
            if self.debug:
                debug_ls = [125, f'update_batch()',
                            f'batch_drop.label = {batch_drop.label}',
                            f'batch_drop.value = {batch_drop.value}']
                debug_value(*debug_ls)

            stored_batch = get_valid_batch()
            batch_version = int(stored_batch.pop('_version', 1))
            batch_upd = dict(_upd_mode='update',
                             _version=batch_version,
                             _tools=stored_batch,
                             _orig_name=batch_drop.label,
                             _new_name= batch_drop.label,
                             _selected_tool_index=None)
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
                debug_value(125, 'save_batch()', f'upd_dict = {upd_dict}')

            error_ls = validate_name(b_name)
            tool_dict, _ = cleanup_tools(upd_dict.get('_tools', {}))

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
                    debug_value(*debug_ls)

                cache['_groups'][grp]['_batches'] = batches
                d = cache['_groups'][grp]

                var_mismatch_dict = self._validate_batch_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)
                self._set_cache(cache_dict=cache)
                reset_batch_gui(batch_name=b_name)

        def cancel_batch(c):
            if self.debug:
                debug_value(126, 'cancel_batch()')

            reset_batch_gui()

        def delete_batch(c):

            upd_dict = eval(upd_dict_log.value)
            orig_tools = batch_drop.value.copy()
            orig_tools.pop('_version', None)

            b_name = upd_dict['_new_name']
            if self.debug:
                debug_ls = [127, 'delete_batch()',
                            f'b_name = {b_name}',
                            f'batch_drop.label = {batch_drop.label}']
                debug_value(*debug_ls)

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
                    debug_value(127, f'delete_batch()  --error-- ',
                                f'error_ls = {error_ls}',
                                f'orig_tools:  {orig_tools}',
                                f"upd_dict['_tools']: {upd_dict['_tools']}")

                return
            else:
                grp = group_drop.value
                cache = self._load_cache()
                batches = cache['_groups'][grp].get('_batches', {})
                batches.pop(b_name, None)
                cache['_groups'][grp]['_batches'] = batches
                d = cache['_groups'][grp]
                var_mismatch_dict = self._validate_batch_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)

                self._set_cache(cache_dict=cache)

                if self.debug:
                    debug_value(127, f'delete_batch() ',
                                f'deleted: {b_name}')
                reset_batch_gui()

        def clear_debug_list(c):
            with debug_out:
                clear_output()

        def display_user_guide(c):
            if c == 'display_guide':
                user_guide_container.selected_index = 0
                user_guide_container.layout.display = 'block'
                set_info_msg()
            elif user_guide_container.layout.display == 'none':
                user_guide_container.layout.display = 'block'
                set_info_msg()
            else:
                user_guide_container.layout.display = 'none'

        # activate/deactivate upd-widgets
        def activate_gui(action_id: str):
            if self.debug:
                debug_value(10, 'activate_gui()',
                            f'action_id = {action_id}')

            def set_widget_state(wd_input, disable: bool = None,
                                 tooltip: str = None, show_widget: bool = None):
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
                                set_widget_state(w, disable, tooltip, show_widget)
                        else:
                            if disable is not None and 'disabled' in wd_input.keys:
                                wd_input.disabled = disable
                            if tooltip is not None and 'tooltip' in wd_input.keys:
                                wd_input.tooltip = tooltip
                elif isinstance(wd_input, list):
                    for w in wd_input:
                        set_widget_state(w, disable, tooltip, show_widget)

            set_info_guide(info_type=action_id)

            set_widget_state(multi_plot_auto_cb, show_widget=False)

            update_enable_list = [selected_tools]
            update_disable_list = [group_drop, batch_drop]
            update_display_list = [name_row, tool_row, var_row, move_up]

            if any(tool_buttons.children):
                for tool in tool_buttons.children:
                    tool.icon = ''
                    tool.style.button_color = 'LightGreen'
            else:
                init_tool_buttons()

            if action_id in ['new', 'update']:
                # update mode
                init_group_var_buttons(mode='create')
                # reset_batch_gui update widgets..
                #        set_info_msg()

                name_of_batch_job.observe(batch_name_changed, 'value')
                set_widget_state(update_enable_list, disable=False)
                set_widget_state(update_disable_list, disable=True)
                set_widget_state(update_display_list, show_widget=True)

                set_widget_state(create_buttons, disable=True,
                                 tooltip='Disabled in update mode...')
                set_widget_state(save_btn,
                                 disable=False,
                                 tooltip='Save settings...')
                set_widget_state(cancel_btn,
                                 disable=False,
                                 tooltip='Cancel...')

                if self.debug:
                    debug_value(9999, 999, action_id, save_btn.disabled,
                                delete_btn.disabled, delete_btn)
                if action_id == 'update':
                    delete_btn.disabled = False
                    delete_btn.tooltip = 'Click to delete...'
                else:
                    delete_btn.disabled = True
                    delete_btn.tooltip = 'Delete...'
                    selected_tools.value = None
                    selected_tools.options = []
                    selected_vars.value = None
                    selected_vars.options = []
                if self.debug:
                    debug_value(99999, 9999, action_id, save_btn.disabled,
                                delete_btn.disabled, delete_btn)

            elif action_id == 'reset_gui':
                # read mode
                init_group_var_buttons(mode='reset')

                try:
                    name_of_batch_job.unobserve(batch_name_changed, 'value')
                except ValueError:
                    pass
                set_widget_state(update_enable_list, disable=True)
                set_widget_state(update_disable_list, disable=False)
                set_widget_state(update_display_list, show_widget=False)

                new_btn.disabled = False
                new_btn.tooltip = 'New batch job...'
                if not batch_drop.value or isinstance(batch_drop.value,
                                                      int):
                    upd_btn.disabled = True
                    upd_btn.tooltip = 'No batch job to update...'
                else:
                    # changed_batch_drop('reset_batch_gui')
                    upd_btn.disabled = False
                    upd_btn.tooltip = 'Update batch job...'

                set_widget_state(save_buttons, disable=True,
                                 tooltip='Enabled in update mode...')

        st_df = self.stations_df

        # Static lookup dictionary for tools
        tool_codes = ['split_plot', 'multi_plot', 'corr_plot',
                      'corr_table', 'statistics']
        tool_names = ['Split-plot', 'Multi-plot', 'Correlation plot (2 vars)',
                      'Correlation table', 'Numerical Statistics']
        tool2name_dict = dict(zip(tool_codes, tool_names))
        name2tool_dict = {v: k for k, v in tool2name_dict.items()}

        # Widgets
        out = wd.Output()
        debug_out = wd.Output()

        # layouts
        drop_layout = wd.Layout(width='auto',
                                height='40px')
        var_txt_layout = wd.Layout(width='99%',
                                   height='99%')
        full_layout = wd.Layout(width='99%',
                                height='99%')
        flex_layout = wd.Layout(width='99%',
                                display='inline-flex',
                                flex_flow='row wrap',
                                align_content='flex-start')
        label_layout = wd.Layout(min_width='125px')
        info_guide_layout = wd.Layout(width='99%',
                                      display='inline-flex',
                                      flex_flow='row wrap',
                                      align_content='flex-start')
        multi_auto_select_label_layout = wd.Layout(min_width='125px')

        # Control widgets:
        # - var_to_unit_dict
        #   is used to set the
        # - var_translation_dict
        #   maps button names to a variable of the group
        # - upd_dict_log (if debug-mode this is displayed in the user guide)
        #   keeps track on updates of the batch job
        var_to_unit_dict = wd.Textarea(value='{}', disabled=True)
        var_translation_dict = wd.Textarea(value='{}', disabled=True)
        upd_dict_log = wd.Textarea(value='{}',
                                   disabled=True,
                                   layout=flex_layout)
        upd_dict_log.observe(reset_selection, names='value')

        # 1:st row
        group_drop = wd.Dropdown(layout=drop_layout,
                                 description_tooltip='Group name')
        init_group_drop()
        if not group_drop.options:
            display(out)
            if self.debug:
                display(debug_out)
                debug_value(999, '--- There are no groups. ---')
            html_msg(text_ls=['First you need to create a group of ',
                              'variables using the "Group menu".'])
            return wd.VBox([out])

        group_drop.observe(changed_group_drop, names='value')
        batch_drop = wd.Dropdown(layout=drop_layout,
                                 description_tooltip='Name of batch job')
        batch_drop.observe(changed_batch_drop, names='value')

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
        new_btn.on_click(new_batch)

        upd_btn = wd.Button(description='Update',
                            icon='pen',
                            button_style='info')
        upd_btn.on_click(update_batch)
        save_btn = wd.Button(description='Save',
                             icon='save',
                             button_style='success')
        save_btn.on_click(save_batch)
        cancel_btn = wd.Button(description='Cancel',
                               icon='ban',
                               button_style='info')
        cancel_btn.on_click(cancel_batch)
        delete_btn = wd.Button(description='Delete',
                               icon='trash',
                               button_style='danger')
        delete_btn.on_click(delete_batch)
        user_guide_btn = wd.Button(description='User guide',
                                   disabled=False,
                                   icon='fa-info-circle',
                                   button_style='info',
                                   tooltip='Show user guide...')
        user_guide_btn.on_click(display_user_guide)

        create_buttons = wd.HBox([new_btn, upd_btn], layout=flex_layout)
        save_buttons = wd.HBox([save_btn, cancel_btn, delete_btn],
                               layout=flex_layout)
        row_list.append(wd.HBox([create_buttons, save_buttons, user_guide_btn],
                                layout=flex_layout))

        # 3:rd row User guide
        user_guide_container = wd.Accordion(selected_index=None,
                                            layout=wd.Layout(width='auto',
                                                             min_width='45%',
                                                             height='auto',
                                                             display='none'))
        # Help text to user
        user_guide = wd.HTMLMath(disabled=True,
                                 layout=wd.Layout(width='90%',
                                                  max_width='90%',
                                                  height='auto'))
        if self.debug:
            user_guide_container.children = [wd.VBox([user_guide,
                                                      upd_dict_log])]
        else:
            user_guide_container.children = [wd.VBox([user_guide])]
        user_guide_container.set_title(0, 'User guide')

        row_list.append(user_guide_container)

        # 4:th row. update section: Batch name
        name_label = wd.HTML(value='<b><i>Batch name: </i></b>',
                             layout=wd.Layout(min_width='125px'))
        name_of_batch_job = wd.Text(value='Name of batch job',
                                    layout=wd.Layout(min_width='200px'))

        name_row = wd.HBox([name_label, name_of_batch_job])
        row_list.append(name_row)

        # 5:th row. update section: Tools
        tool_label = wd.HTML('<b><i>Available tools: </i></b>',
                             layout=label_layout)
        tool_buttons = wd.HBox(layout=flex_layout)
        tool_row = wd.HBox([tool_label, tool_buttons])
        row_list.append(tool_row)

        # 6:th row. update section: Vars
        avail_variables_label = wd.HTML('<b><i>Available variables: </i></b>',
                                        layout=label_layout)
        var_buttons = wd.HBox(layout=flex_layout)
        var_row = wd.HBox([avail_variables_label, var_buttons])
        row_list.append(var_row)

        # 7:rd row. update section: Selections
        selection_label = wd.HTML('<b><i>Current setup: </i></b>',
                                  layout=label_layout)
        selected_tools_tooltip = "The tools are listed in order of execution." \
                                 "\nUse the Up-button (displayed in " \
                                 "update-mode)" \
                                 "\nto change the order of " \
                                 "\nexecution."
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

        # 8:rd row. info, special settings
        # Info regarding selected tool
        info_guide = wd.HTMLMath(layout=info_guide_layout)

        multi_plot_auto_cb = wd.Checkbox(description='Choose axis according to '
                                                     'unit',
                                         value=_get_multi_plot_auto(),
                                         layout=multi_auto_select_label_layout)

        # special_settings = wd.VBox([multi_plot_auto_cb, multi_plot_axis])
        info_box = wd.VBox([info_guide, multi_plot_auto_cb])
        row_list.append(info_box)

        # Trigger changed_group_drop that populate other widgets.
        set_group_value(group=_group_name)

        row_list.append(out)
        if self.debug:
            debug_btn = wd.Button(description='Clear debug list')
            debug_btn.on_click(clear_debug_list)
            row_list.append(debug_btn)
            row_list.append(debug_out)

        return_widget = wd.VBox(row_list)

        return return_widget

    def _default_settings(self):
        if self.debug:
            print('*** _user_configurations()\n')

        def init_general_settings():
            # set general values
            settings = self._load_user_settings()
            run_configs = settings.get('run_configs', {})
            latex_kwargs = settings.get('latex_kwargs', {})
            split_p_kwargs = settings.get('split_plot_kwargs', {})
            multi_p_kwargs = settings.get('multi_plot_kwargs', {})
            corr_p_kwargs = settings.get('corr_plot_kwargs', {})
            corr_t_kwargs = settings.get('corr_table_kwargs', {})
            statistics_kwargs = settings.get('statistics_kwargs', {})

            auto_run_cb.value = run_configs.get('auto_run', True)
            time_end_date.value = run_configs.get('end_date', 0)
            time_start_date.value = run_configs.get('start_date', 10)
            time_fetch_date.value = run_configs.get('fetch_date', 6)

            latex_font_style.value = latex_kwargs.get('font_style', 'Default')
            f_size = latex_kwargs.get('font_size', 'Default')
            latex_font_size.value = str(f_size)
            latex_use_exp_cb.value = latex_kwargs.get('use_exp', False)
            latex_changed()

            split_p_zoom_sliders.value = split_p_kwargs.get('zoom_sliders', 2)
            split_p_use_latex_cb.value = split_p_kwargs.get('use_latex', True)
            split_p_plotly_templates.value = split_p_kwargs.get('template',
                                                                'plotly')
            split_p_height.value = split_p_kwargs.get('height', 0)
            split_p_width.value = split_p_kwargs.get('width', 0)
            split_p_title_font.value = split_p_kwargs.get('title_font',
                                                          plotly_text_fonts[0])
            split_p_title_size.value = split_p_kwargs.get('title_size',
                                                          'Default')
            split_p_subtitle_size.value = split_p_kwargs.get('subtitle_size',
                                                             'Default')

            multi_p_auto_axis_cb.value = multi_p_kwargs.get('auto_axis', True)
            multi_p_use_latex_cb.value = multi_p_kwargs.get('use_latex', True)
            multi_p_plotly_templates.value = multi_p_kwargs.get('template',
                                                                'plotly')
            multi_p_height.value = multi_p_kwargs.get('height', 0)
            multi_p_width.value = multi_p_kwargs.get('width', 0)
            multi_p_title_font.value = multi_p_kwargs.get('title_font',
                                                          plotly_text_fonts[0])
            multi_p_title_size.value = multi_p_kwargs.get('title_size',
                                                          'Default')
            multi_p_subtitle_size.value = multi_p_kwargs.get('subtitle_size',
                                                             'Default')

            corr_p_use_latex_cb.value = corr_p_kwargs.get('use_latex', True)
            corr_p_plotly_templates.value = corr_p_kwargs.get('template',
                                                              'plotly')
            corr_p_height.value = corr_p_kwargs.get('height', 0)
            corr_p_width.value = corr_p_kwargs.get('width', 0)
            corr_p_title_font.value = corr_p_kwargs.get('title_font',
                                                        plotly_text_fonts[0])
            corr_p_title_size.value = corr_p_kwargs.get('title_size',
                                                        'Default')
            corr_p_subtitle_size.value = corr_p_kwargs.get('subtitle_size',
                                                           'Default')
            corr_p_color_scale_drop.value = corr_p_kwargs.get('color_scale',
                                                              'blues')

            corr_t_title_font.value = corr_t_kwargs.get('title_font',
                                                        plotly_text_fonts[0])
            corr_t_title_size.value = corr_t_kwargs.get('title_size',
                                                        'Default')
            corr_t_subtitle_size.value = corr_t_kwargs.get('subtitle_size',
                                                           'Default')
            corr_t_color_scale_drop.value = corr_t_kwargs.get('color_scale',
                                                              'blues')

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

        def latex_changed(c = None):
            latex = icos2latex.Translator(use_exp=latex_use_exp_cb.value,
                                          font_size=latex_font_size.value,
                                          font_style=latex_font_style.value)
            tex_str = '$\\qquad $ '*3 + \
                      latex.var_unit_to_latex(var_unit=("CO2", "\u00b5mol mol-1"))
            if self.debug:
                print('latex_changed()', f'tex_str = {tex_str}')

            with latex_output_area:
                clear_output()
                display(Math(tex_str))

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

            upd_dict = {'run_configs': {'auto_run': auto_run_cb.value,
                                        'start_date': time_start_date.value,
                                        'end_date': time_end_date.value,
                                        'fetch_date': time_fetch_date.value},
                        'latex_kwargs':
                            {'font_style': latex_font_style.value,
                             'font_size': latex_font_size.value,
                             'use_exp': latex_use_exp_cb.value},
                        'split_plot_kwargs':
                            {'zoom_sliders': split_p_zoom_sliders.value,
                             'use_latex': split_p_use_latex_cb.value,
                             'template': split_p_plotly_templates.value,
                             'title_font': split_p_title_font.value,
                             'title_size': split_p_title_size.value,
                             'subtitle_size': split_p_subtitle_size.value,
                             'width': split_p_width.value,
                             'height': split_p_height.value},
                        'multi_plot_kwargs':
                            {'auto_axis': multi_p_auto_axis_cb.value,
                             'use_latex': multi_p_use_latex_cb.value,
                             'template': multi_p_plotly_templates.value,
                             'title_font': multi_p_title_font.value,
                             'title_size': multi_p_title_size.value,
                             'subtitle_size': multi_p_subtitle_size.value,
                             'width': multi_p_width.value,
                             'height': multi_p_height.value},
                        'corr_plot_kwargs':
                            {'use_latex': corr_p_use_latex_cb.value,
                             'template': corr_p_plotly_templates.value,
                             'color_scale': corr_p_color_scale_drop.value,
                             'title_font': corr_p_title_font.value,
                             'title_size': corr_p_title_size.value,
                             'subtitle_size': corr_p_subtitle_size.value,
                             'width': corr_p_width.value,
                             'height': corr_p_height.value},
                        'corr_table_kwargs':

                            {'color_scale': corr_t_color_scale_drop.value,
                             'title_font': corr_t_title_font.value,
                             'title_size': corr_t_title_size.value,
                             'subtitle_size': corr_t_subtitle_size.value},
                        'statistics_kwargs': {}
                        }

            self.report_writer = None
            json_handler.update(data_piece=upd_dict,
                                path_to_json_file=self.user_config_file)
            init_general_settings()

        def cancel_general_settings(c):
            init_general_settings()

        def link(url, url_txt) -> str:
            return f'<a href="{url}" target="_blank">' \
                   f'<font color="DarkBlue">{url_txt}</font></a>'

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
        plotly_text_fonts = ["Arial", "Balto", "Courier New", "Droid Sans",
                             "Droid Serif", "Droid Sans Mono", "Gravitas One",
                             "Old Standard TT", "Open Sans", "Overpass",
                             "PT Sans Narrow", "Raleway", "Times New Roman"]
        plotly_text_sizes = ['Default', 6, 7, 8, 9, 10, 11, 12, 13, 14, 17]

        # common texts
        col_href = link("https://www.aao.org/eye-health/"
                        "diseases/what-is-color-blindness", "color deficiencies")
        color_ref = f'the color scale can be changed in order to ' \
                    f'ease variants of <b><i>{col_href}</i></b>.'
        plotly_templ_href = link("https://plotly.com/python/templates/",
                                 "Plotly template")
        plotly_templ_ref = f'The background color can be changed by switching ' \
                           f'the <b><i>{plotly_templ_href}</i></b>.<br>'
        height_or_width_min = 'Setting <b><i>Height</i></b> or '\
                              '<b><i>Width</i></b> to a value below '\
                              '200 will lead to plotly default '\
                              'value. '

        # common label widgets
        label_layout = wd.Layout(min_width='90px', max_width='220px')
        plotly_templ_label = wd.HTML(value='<b>Plotly template:</b>',
                                     layout=label_layout)
        use_latex_label = wd.HTML(value='<b> Use LaTeX</b>',
                                  layout=label_layout)
        height_label = wd.HTML(value='<b>Height:</b>',
                               layout=label_layout)
        width_label = wd.HTML(value='<b>Width:</b> ',
                              layout=label_layout)
        title_font_label = wd.HTML(value='<b>Title font:</b> ',
                                   layout=label_layout)
        title_size_label = wd.HTML(value='<b>Title size:</b> ',
                                   layout=label_layout)
        subtitle_size_label = wd.HTML(value='<b>Subtitle size:</b> ',
                                      layout=label_layout)
        color_scale_label = wd.HTML(value='<b>Plotly color scale:</b> ',
                                    layout=label_layout)

        # widgets
        cb_layout = wd.Layout(width='20px')
        int_drop_layout = wd.Layout(width='60px')
        size_drop_layout = wd.Layout(width='125px')
        font_drop_layout = size_drop_layout
        # wd.Layout(min_width='100px', max_width='145px')
        templ_drop_layout = size_drop_layout
        # wd.Layout(min_width='70px', max_width='110px')
        save_btn = wd.Button(description='Save',
                             icon='save',
                             button_style='danger',
                             )
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

        def_settings_guide = wd.HTML(value='<span>Here you can modify certain '
                                           'settings such as: what data to use, '
                                           'visualizations of different plots '
                                           'and texts. <br><i>Please note</i> '
                                           'that '
                                           'the <b>Save</b>-button below is '
                                           'enabled when a value is '
                                           'changed and the user press &lttab&gt '
                                           'or clicks outside the widget holding '
                                           'the value.</span')

        run_settings_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                           'When the user start the '
                                           'application, the default behaviour '
                                           'is to execute all batch jobs of '
                                           'the last edited group of variables, '
                                           'to change this switch of '
                                           '<b><i>Auto-run</i></b> below.<br> '
                                           'Plots and statistics outputs are '
                                           'based on values measured '
                                           'between the <i>start</i> '
                                           'and the <i>end dates</i>, '
                                           'displayed in the <b>Start</b> '
                                           'menu. '
                                           'Of course, the dates displayed in '
                                           'the start menu can be changed '
                                           'for each run. '
                                           'Here, you can modify the '
                                           '<i>default method on how to '
                                           'calculate these dates.</i> '
                                           '</span><br> '
                                           'The number at <b><i>End date</b></i> '
                                           'is the number of days '
                                           '<i>before today</i>, '
                                           'while <b><i>Start date</i></b> is '
                                           'the number of days <i>before the '
                                           'end date</i>. '
                                           '<span>The <b><i>Fetch date</i></b> '
                                           'denotes the number of days '
                                           '<i>before the start date</i>, it '
                                           'is a feature used to <i>speed up '
                                           're-calculations</i>. In case the '
                                           'user chose to change the report '
                                           'dates in a second run, the data '
                                           'between the fetch date and the end '
                                           'date of the first run will already '
                                           'be in RAM.'
                                           )
        auto_run_label = wd.HTML(value='<b>Auto-run</b>')
        auto_run_cb = wd.Checkbox(value=True,
                                  disabled=False,
                                  indent=False,
                                  layout=cb_layout)
        auto_sub_box = wd.HBox([auto_run_cb,
                                auto_run_label])

        time_end_date_label = wd.HTML(value='<b>End date: </b> ',
                                      layout=label_layout)
        time_end_date = wd.IntText(layout=int_drop_layout)
        time_end_date_box = wd.HBox([time_end_date_label,
                                     time_end_date])

        time_start_date_label = wd.HTML(value='<b>Start date: </b> ',
                                        layout=label_layout)
        time_start_date = wd.IntText(layout=int_drop_layout)
        time_start_date_box = wd.HBox([time_start_date_label,
                                       time_start_date])

        time_fetch_date_label = wd.HTML(value='<b>Fetch date: </b> ',
                                        layout=label_layout)
        time_fetch_date = wd.Dropdown(options=range(0, 15),
                                      layout=int_drop_layout)
        time_fetch_date_box = wd.HBox([time_fetch_date_label,
                                       time_fetch_date])
        run_box = wd.HBox([wd.VBox([run_settings_guide,
                                    auto_sub_box,
                                    time_end_date_box,
                                    time_start_date_box,
                                    time_fetch_date_box])
                           ])
        observe_pos_ls.append(auto_run_cb)
        observe_pos_ls.append(time_end_date)
        observe_pos_ls.append(time_start_date)
        observe_ordinary_ls.append(time_fetch_date)

        run_settings = wd.Accordion(children=[run_box],
                                    titles=('Run configurations',))

        latex_text1 = wd.HTML('<span><b>Guide:<br> <i>LaTeX settings</i></b> '
                              'applies to axis labels of plots.<br>For example, '
                              'if a plot represent CO2-measurements the y-axis '
                              'will, depending on the settings, look similar '
                              'to: </span>')
        latex_output_area = wd.Output()
        latex_text2 = wd.HTML('When <b><i>Keep exponents</i></b> is '
                              '<i>deselected</i> '
                              'negative exponents in units will be '
                              'converted into fractions.')
        latex_use_exp_label = wd.HTML('<b> Keep exponents</b>',
                                      layout=wd.Layout(min_width='160px'))
        latex_use_exp_cb = wd.Checkbox(value=True,
                                       disabled=False,
                                       indent=False,
                                       layout=cb_layout)
        latex_use_exp_box = wd.HBox([latex_use_exp_cb, latex_use_exp_label])
        latex_font_size_label = wd.HTML('<b>Font size: </b>',
                                        layout=label_layout)
        latex_font_size = wd.Dropdown(options=['Default', '6', '8', '10', '11',
                                               '12', '14', '17'],
                                      disabled=False,
                                      layout=wd.Layout(width='75px'))
        latex_font_size_box = wd.HBox([latex_font_size_label, latex_font_size])
        latex_font_style_label = wd.HTML('<b>Font style: </b>',
                                         layout=label_layout)
        latex_font_style = wd.Dropdown(options=[('Default', 'Default'),
                                                 ('Roman (serifs)', 'rm'),
                                                ('Sans Serif (no serifs)', 'sf'),
                                                ('Italic (serifs)', 'it'),
                                                ('Typewriter (serifs)', 'tt'),
                                                ('Bold (serifs)', 'bf')],
                                       layout=wd.Layout(width='150px'))
        latex_font_style_box = wd.HBox([latex_font_style_label,
                                        latex_font_style])

        observe_latex = [latex_use_exp_cb, latex_font_size, latex_font_style]
        observe_ordinary_ls.extend(observe_latex)

        latex_box = wd.VBox([latex_text1,
                             latex_output_area,
                             latex_text2,
                             wd.HBox([wd.VBox([latex_use_exp_box]),
                                      wd.VBox([latex_font_style_box,
                                               latex_font_size_box])
                                      ])
                             ])

        latex_settings = wd.Accordion(children=[latex_box],
                                      titles=('LaTeX settings',))

        split_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         'In a <b><i>Split-plot</i></b> you can '
                                         'visualize several variables '
                                         'in interconnected individual plots. '
                                         'The plots are connected using a '
                                         '<i>zoom-slider</i>. The value of '
                                         '<b><i>Split-plot grouping</i></b> is '
                                         'the number of graphs '
                                         'displayed before the '
                                         'first zoom-slider.<br>'
                                         f'{plotly_templ_ref}'
                                         f'{height_or_width_min}'
                                         'These values will be applied for each '
                                         'split-plot.<br>'
                                         '</span>')

        split_p_zoom_sliders_label = wd.HTML(value='<b>Split-plot grouping:</b>',
                                             layout=label_layout)
        split_p_zoom_sliders = wd.Dropdown(options=range(1, 10),
                                           layout=int_drop_layout)

        split_p_zoom_box = wd.HBox([split_p_zoom_sliders_label,
                                    split_p_zoom_sliders])

        split_p_use_latex_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           tooltip="Applies to the y-axis",
                                           layout=cb_layout)
        split_p_latex_box = wd.HBox([split_p_use_latex_cb, use_latex_label])

        split_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                               layout=templ_drop_layout)
        split_p_plotly_template_box = wd.HBox([plotly_templ_label,
                                               split_p_plotly_templates])

        split_p_height = wd.FloatText(layout=int_drop_layout)
        split_p_height_box = wd.HBox([height_label,
                                      split_p_height])

        split_p_width = wd.FloatText(layout=int_drop_layout)
        split_p_width_box = wd.HBox([width_label,
                                     split_p_width])

        split_p_title_font = wd.Dropdown(options=plotly_text_fonts,
                                         layout=font_drop_layout)
        split_p_title_font_box = wd.HBox([title_font_label,
                                          split_p_title_font])

        split_p_title_size = wd.Dropdown(options=plotly_text_sizes,
                                         layout=size_drop_layout)
        split_p_title_size_box = wd.HBox([title_size_label,
                                          split_p_title_size])

        split_p_subtitle_size = wd.Dropdown(options=plotly_text_sizes,
                                            layout=size_drop_layout)
        split_p_subtitle_size_box = wd.HBox([subtitle_size_label,
                                             split_p_subtitle_size])

        split_box = wd.VBox([split_plot_guide,
                             wd.HBox([wd.VBox([split_p_latex_box,
                                               split_p_plotly_template_box,
                                               split_p_zoom_box]),
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
        observe_ordinary_ls.append(split_p_title_font)
        observe_ordinary_ls.append(split_p_title_size)
        observe_ordinary_ls.append(split_p_subtitle_size)

        multi_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         'In a <b><i>Multi-plot</i></b> '
                                         'you can visualize several variables '
                                         'in one plot. '
                                         'The maximum number of y-axes is '
                                         'limited to 2, with maximum one unit '
                                         'per axis.<br>'
                                         'When selecting variables for a '
                                         'multi-plot they will, by default, '
                                         'be mapped to the y-axis '
                                         'according to their unit. '
                                         'However, this behaviour can be changed '
                                         'using '
                                         'the checkbox <b><i>Automatic axis '
                                         'selection</b></i>, in which case it is '
                                         'possible two have variables with the '
                                         'same unit on different axes.<br>'
                                         f'{plotly_templ_ref}'
                                         f'{height_or_width_min}<br>'
                                         '</span>')

        multi_p_auto_axis_label = wd.HTML(value='<b> Automatic axis '
                                                'selection</b>',
                                          label_layout=wd.Layout(min_width='80px',
                                                                 max_width=
                                                                 '160px'))
        multi_p_auto_axis_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           layout=cb_layout)
        multi_p_auto_axis_box = wd.HBox([multi_p_auto_axis_cb,
                                         multi_p_auto_axis_label])
        multi_p_use_latex_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           tooltip="Applies to the y-axes",
                                           layout=cb_layout)
        multi_p_latex_box = wd.HBox([multi_p_use_latex_cb,
                                     use_latex_label])

        multi_p_height = wd.FloatText(layout=int_drop_layout)
        multi_p_height_box = wd.HBox([height_label,
                                      multi_p_height])

        multi_p_width = wd.FloatText(layout=int_drop_layout)
        multi_p_width_box = wd.HBox([width_label,
                                     multi_p_width])
        multi_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                               layout=templ_drop_layout)
        multi_p_plotly_template_box = wd.HBox([plotly_templ_label,
                                               multi_p_plotly_templates])

        multi_p_title_font = wd.Dropdown(options=plotly_text_fonts,
                                         layout=font_drop_layout)
        multi_p_title_font_box = wd.HBox([title_font_label,
                                          multi_p_title_font])

        multi_p_title_size = wd.Dropdown(options=plotly_text_sizes,
                                         layout=size_drop_layout)
        multi_p_title_size_box = wd.HBox([title_size_label,
                                          multi_p_title_size])

        multi_p_subtitle_size = wd.Dropdown(options=plotly_text_sizes,
                                            layout=size_drop_layout)
        multi_p_subtitle_size_box = wd.HBox([subtitle_size_label,
                                             multi_p_subtitle_size])
        multi_box = wd.VBox([multi_plot_guide,
                             wd.HBox([wd.VBox([multi_p_latex_box,
                                               multi_p_auto_axis_box,
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
        observe_ordinary_ls.append(multi_p_auto_axis_cb)
        observe_ordinary_ls.append(multi_p_use_latex_cb)
        observe_ordinary_ls.append(multi_p_title_font)
        observe_ordinary_ls.append(multi_p_title_size)
        observe_ordinary_ls.append(multi_p_subtitle_size)

        multi_plot_settings = wd.Accordion(children=[multi_box],
                                           titles=('Multi-plot settings',))

        corr_plot_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                        'In a <b><i>Correlation plot</i></b> '
                                        'you can compare <i>two</i> variables '
                                        'against each other. <br>'
                                        f'{plotly_templ_ref}'
                                        f'{height_or_width_min}<br>'
                                        'The <b><i>Plotly color scale</i></b> '
                                        'is used in order to <i>visualize the '
                                        'sampling timestamps </i> of '
                                        f'the data, {color_ref}'
                                        '</span>')

        corr_p_use_latex_cb = wd.Checkbox(value=True,
                                          disabled=False,
                                          indent=False,
                                          tooltip="Applies to the x- and "
                                                  "y-axes",
                                          layout=cb_layout)

        corr_p_latex_box = wd.HBox([corr_p_use_latex_cb,
                                    use_latex_label])

        corr_p_height = wd.FloatText(layout=int_drop_layout)
        corr_p_height_box = wd.HBox([height_label,
                                     corr_p_height])

        corr_p_width = wd.FloatText(layout=int_drop_layout)
        corr_p_width_box = wd.HBox([width_label,
                                    corr_p_width])

        corr_p_title_font = wd.Dropdown(options=plotly_text_fonts,
                                        layout=font_drop_layout)
        corr_p_title_font_box = wd.HBox([title_font_label,
                                         corr_p_title_font])

        corr_p_title_size = wd.Dropdown(options=plotly_text_sizes,
                                        layout=size_drop_layout)
        corr_p_title_size_box = wd.HBox([title_size_label,
                                         corr_p_title_size])

        corr_p_subtitle_size = wd.Dropdown(options=plotly_text_sizes,
                                           layout=size_drop_layout)
        corr_p_subtitle_size_box = wd.HBox([subtitle_size_label,
                                            corr_p_subtitle_size])

        corr_p_color_scale_drop = wd.Dropdown(options=plotly_color_scales,
                                              value='blues',
                                              layout=font_drop_layout)
        corr_p_color_scale_box = wd.HBox([color_scale_label,
                                          corr_p_color_scale_drop])

        corr_p_plotly_templates = wd.Dropdown(options=plotly_templates,
                                              layout=templ_drop_layout)
        corr_p_plotly_template_box = wd.HBox([plotly_templ_label,
                                              corr_p_plotly_templates])
        corr_p_box = wd.VBox([corr_plot_guide,
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
        corr_plot_settings = wd.Accordion(children=[corr_p_box],
                                          titles=('Correlation-plot settings',))
        observe_ordinary_ls.append(corr_p_use_latex_cb)
        observe_ordinary_ls.append(corr_p_plotly_templates)
        observe_ordinary_ls.append(corr_p_color_scale_drop)
        observe_ordinary_ls.append(corr_p_title_font)
        observe_ordinary_ls.append(corr_p_title_size)
        observe_ordinary_ls.append(corr_p_subtitle_size)
        observe_height_width_ls.append(corr_p_width)
        observe_height_width_ls.append(corr_p_height)

        corr_table_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         'The <b><i>Correlation table</i></b> '
                                         'can be used to visualize linear '
                                         'dependency between multiple '
                                         'variables (assumed to have the same '
                                         'statistical distribution).<br>'
                                         'The <b><i>Plotly color scale</i></b> '
                                         'is used in order to visualize '
                                         'the correlation coefficients, '
                                         f'{color_ref}.'
                                         '</span>')
        corr_t_color_scale_drop = wd.Dropdown(options=plotly_color_scales,
                                              value='blues',
                                              layout=font_drop_layout)
        corr_t_color_scale_box = wd.HBox([color_scale_label,
                                          corr_t_color_scale_drop])
        corr_t_title_font = wd.Dropdown(options=plotly_text_fonts,
                                        layout=font_drop_layout)
        corr_t_title_font_box = wd.HBox([title_font_label,
                                         corr_t_title_font])

        corr_t_title_size = wd.Dropdown(options=plotly_text_sizes,
                                        layout=size_drop_layout)
        corr_t_title_size_box = wd.HBox([title_size_label,
                                         corr_t_title_size])

        corr_t_subtitle_size = wd.Dropdown(options=plotly_text_sizes,
                                           layout=size_drop_layout)
        corr_t_subtitle_size_box = wd.HBox([subtitle_size_label,
                                            corr_t_subtitle_size])

        corr_t_box = wd.VBox([corr_table_guide,
                              wd.HBox([wd.VBox([corr_t_color_scale_box]),
                                       wd.VBox([corr_t_title_font_box,
                                                corr_t_title_size_box,
                                                corr_t_subtitle_size_box]),
                                       ])
                              ])
        corr_table_settings = wd.Accordion(children=[corr_t_box],
                                           titles=('Correlation table settings',))
        observe_ordinary_ls.append(corr_t_color_scale_drop)
        observe_ordinary_ls.append(corr_t_title_font)
        observe_ordinary_ls.append(corr_t_title_size)
        observe_ordinary_ls.append(corr_t_subtitle_size)

        statistics_guide = wd.HTML(value='<span><b>Guide:</b><br>...............'
                                         '.............')
        statistics_settings = wd.Accordion(children=[statistics_guide],
                                           titles=('Numerical statistics '
                                                   'settings',))
        return_widget = wd.VBox([def_settings_guide,
                                 run_settings,
                                 latex_settings,
                                 split_plot_settings,
                                 multi_plot_settings,
                                 corr_plot_settings,
                                 corr_table_settings,
                                 statistics_settings,
                                 save_cancel_box])

        init_general_settings()

        return return_widget

    def _user_configurations(self):
        general_accordion = wd.Accordion(children=[self._default_settings()],
                                         titles=('Default settings',))
        batch_accordion = wd.Accordion(children=[self._edit_batch_jobs()],
                                       titles=('Batch jobs',))
        out = wd.Output()
        display(general_accordion, batch_accordion, out)

    def _edit_group_variables(self):
        if self.debug:
            print('*** _edit_group_variables()\n')

        def update_cache(group_dict):
            if self.debug:
                print('update_cache()', group_dict)

            # Structure of group_dict
            # group_dict = {'_upd_mode': 'new'| 'update'| 'delete',
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
            #  '_groups': {
            #      'Group 1': {
            #          '_group_vars': [['SWC_1', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_2', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_3', 'ETC NRT Meteo', 'Hyltemossa']],
            #          '_batches': {
            #              'flux stat': {
            #                  '0': {
            #                      'split_plot': [['SWC_1', 'ETC NRT Meteo',
            #                                      'Hyltemossa'],
            #                                     ['SWC_2', 'ETC NRT Meteo',
            #                                      'Hyltemossa']]}}}},
            #      'Group 2': {
            #          '_group_vars': [['SWC_1', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_2', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['SWC_3', 'ETC NRT Meteo', 'Hyltemossa'],
            #                          ['LE', 'ETC NRT Fluxes', 'Hyltemossa'],
            #                          ['LE_UNCLEANED','ETC NRT Fluxes',
            #                           'Hyltemossa'],
            #                          ['NEE','ETC NRT Fluxes', 'Hyltemossa'],
            #                          ['NEE_UNCLEANED','ETC NRT Fluxes',
            #                           'Hyltemossa']],
            #          '_batches': {
            #              'batch with error': {
            #                  '0': {
            #                      'split_plot': [['SWC_1', 'ETC NRT Meteo', 'Hyltemossa'],
            #                                     ['SWC_4', 'ETC NRT Meteo',
            #                                      'Hyltemossa']]}}},
            #          '_var_mismatch': {
            #              'batch with error': {
            #                  'split_plot': [['SWC_4', 'ETC NRT Meteo',
            #                                  'Hyltemossa']]}}}}}

            if '_upd_mode' not in group_dict.keys() or \
                    '_group_name' not in group_dict.keys():
                return

            grp = group_dict['_group_name']
            var_ls = group_dict['_var_list']
            old_grp = ''
            cache = self._load_cache()

            if group_dict['_upd_mode'] == 'new':
                cache['_groups'][grp] = {'_group_vars': var_ls}

                # update "last"-flags
                last_var_tuple = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station_id'] = last_var_tuple[-1]

            elif group_dict['_upd_mode'] == 'update':
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

            elif group_dict['_upd_mode'] == 'delete':
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

            # validate_batches
            if grp in cache['_groups'].keys() and '_batches' in \
                    cache['_groups'][grp].keys():
                d = cache['_groups'][grp]
                var_mismatch_dict = self._validate_batch_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)

            # Remove timeseries from local storage
            self._flush_store(grp)
            if old_grp:
                self._flush_store(old_grp)
            self._set_cache(cache_dict=cache)

        def init():

            val = set_group_drop('')

            if val == 'first_run':
                new_group(val)
                display_user_guide('display_guide')
            else:
                activate_gui('init_read_mode')

        def get_station_list():
            id_ls = list(st_df.id)
            name_ls = list(st_df.name)
            station_ls = list(set(zip(name_ls, id_ls)))
            station_ls = [(f'{v[0]} ({v[1]})', v[1]) for v in station_ls]
            station_ls.sort(key=lambda v: v[0].lower())
            return station_ls

        def set_station_drop():
            if self.debug:
                print('set_station_drop()')

            station_ls = get_station_list()

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
                spec_ls = ['Files...']
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
                var_dict = icos_data.StationData.icos_pid2meta(pid)['columns']
                var_ls = sorted([key for key in var_dict.keys() if key not in
                                 ['TIMESTAMP', 'TIMESTAMP_END']])
                var_info = [var_dict[key] for key in var_ls]
                if self.debug:
                    print(' - list(zip(var_ls, var_info)) = ',
                          list(zip(var_ls, var_info)))
                var_drop.options = list(zip(var_ls, var_info))
                var_drop.value = var_drop.options[0][1]

        def set_var_info_text(change):
            if self.debug:
                print('\nset_var_info_text()\nchange: ', change)

            # Show info of a variable
            if isinstance(change, dict):
                if isinstance(change['owner'], wd.Dropdown):
                    if var_drop.value == 'dummy':
                        return
                    else:
                        var_name = change['owner'].label
                        var_dict = change['owner'].value
                elif isinstance(change['owner'], wd.Checkbox):
                    var_name = change['owner'].description
                    var_drop.label = var_name
                    var_dict = var_drop.value
                    # var_dict = [x[1] for x in var_drop.options
                    #             if x[0] == var_name].pop()
                    var_drop.label = var_name
                    if self.debug:
                        print(f' - var_drop.options = {var_drop.options},'
                              f'\n- var_dict = {var_dict} ',
                              f'\n- change["owner"].description = '
                              f'{change["owner"].description} ')
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
                var_tuples = copy.deepcopy(upd_dict['_var_list'])
                text_tag = 'i'
                separator = ' || '
                margin = '&nbsp' * 42
                t1 = f'<{text_tag}>Variables in update mode: </{text_tag}>'
            else:
                grp = group_drop.value
                cache = self._load_cache()
                var_tuples = copy.deepcopy(cache['_groups'][grp]['_group_vars'])
                text_tag = 'b'
                separator = '<br>'

                t1 = f'<{text_tag}>Variables: </{text_tag}>'
                margin = '&nbsp' * 18

            # Next we rename possible duplicate variable names
            var_ls = [v[0] for v in var_tuples]
            n = len(var_ls)
            var_duplicates = {}
            for i, v in enumerate(var_ls):
                if i != n - 1 and v in var_ls[i + 1:]:
                    if v not in var_duplicates.keys():
                        var_duplicates[v] = [(i, 1)]
                    else:
                        count = var_duplicates[v][-1][1] + 1
                        var_duplicates[v].append((i, count))

                elif v in var_duplicates.keys():
                    count = var_duplicates[v][-1][1] + 1
                    var_duplicates[v].append((i, count))

            for v, i_ls in var_duplicates.items():
                for x in i_ls:
                    var_ls[x[0]] = f'{v}<sub>{x[1]}</sub>'
                    var_tuples[x[0]][0] = f'{v}<sub>{x[1]}</sub>'

            station_dict = AnalysisGui._var_tup2station_dict(var_tuples)
            if self.debug:
                print(f'get_group_var_text()\tvar_tuples = {var_tuples} ')
                print(f'get_group_var_text()\tstation_dict = {station_dict} ')

            t2 = f',<br>{margin}'.join([', '.join(var_ls[i:i + 12])
                                        for i in range(0, len(var_ls),
                                                       12)]) + '<br>'

            # Next we loop over stations and products to concatenate
            # a proper html text
            t3 = ''

            stn_ls = get_station_list()
            one_stn = (len(station_dict.keys()) == 1)
            rows = []
            for stn in station_dict.keys():
                stn_name = [s[0] for s in stn_ls if s[1] == stn].pop()
                if one_stn:
                    one_prod = (len(station_dict[stn].keys()) == 1)
                    if one_prod:
                        for prod in station_dict[stn].keys():
                            t3 = f'Here, all variables are from ' \
                                 f'<{text_tag}>{prod}</{text_tag}> '
                    else:
                        for prod in station_dict[stn].keys():
                            if not t3:
                                t3 += 'Where the variables '
                            else:
                                t3 += ', while '

                            prod_vars = station_dict[stn][prod]
                            last_var = prod_vars.pop()
                            var_row = ',<br>'.join(['</b>, <b>'.join(prod_vars[
                                                                     i:i + 12])
                                                    for i in range(0,
                                                                   len(prod_vars),
                                                                   12)])
                            if prod_vars:
                                t3 += f'<b>{var_row}</b> and ' \
                                      f'<b>{last_var}</b> are '
                            else:
                                t3 += f'<b>{last_var}</b> is '

                            t3 += f' from <{text_tag}>{prod}</{text_tag}> '
                        t3 += f'of the station ' \
                              f'<{text_tag}>{stn_name}</{text_tag}> ' \
                              f'(<{text_tag}>{stn}</{text_tag}>)'
                    t3 += '.'
                else:
                    t4 = ''
                    prods = []
                    for prod in station_dict[stn].keys():
                        if not t4:
                            t4 += f'Where the variables '
                        else:
                            t4 += f',<br>while '

                        prod_vars = station_dict[stn][prod]
                        last_var = prod_vars.pop()
                        var_row = ',<br>'.join(['</b>, <b>'.join(prod_vars[
                                                                   i:i + 12])
                                                for i in range(0, len(prod_vars),
                                                               12)])
                        if prod_vars:
                            t4 += f'<b>{var_row}</b> and <b>{last_var}</b> are '
                        else:
                            t4 += f'<b>{last_var}</b> is '

                        t4 += f' from <{text_tag}>{prod}</{text_tag}>'
                    t4 += f'of the station ' \
                          f'<{text_tag}>{stn_name}</{text_tag}> ' \
                          f'(<{text_tag}>{stn}</{text_tag}>)'
                    rows.append(t4)
            if rows:
                t3 = ';<br> '.join(rows) + '.'

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

        def new_group(click):
            if self.debug:
                print('new_group()')

            upd_group_dict = {'_upd_mode': 'new',
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
            upd_group_dict = {'_upd_mode': 'update',
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

            if not upd_group_dict['_upd_mode'] in ['new', 'update']:
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
                upd_group_dict['_upd_mode'] = 'delete'
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
            upd_mode = upd_dict['_upd_mode']

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
                        f'There is already a group called <i>{grp_name}</i>,')
                    error_ls.append('please pick another name.')
                elif upd_mode == 'update':
                    if grp_name != upd_dict['_saved_group_name']:
                        error_ls.append(
                            f'There is already a group called <i>{grp_name}</i>,')
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
            upd_mode = upd_group_dict['_upd_mode']

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
                info_color = self.widget_style_colors['primary:active']
                msg = f'<span style="color:{info_color}">{margin}{margin}<h4>' \
                      f'{info_ls[0]}</h4><b>'

                for row in info_ls[1:]:
                    msg += f'{margin}{row}<br>'
                msg += '</b></span>'
            else:
                msg = ''

            if error_ls:
                warning_emoji = '\u26a0\ufe0f'
                error_color = self.widget_style_colors['danger:active']
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
                new_group_btn.on_click(new_group, remove=True)
                save_group_btn.on_click(save_group, remove=False)
                delete_group_btn.on_click(delete_group, remove=False)
                cancel_group_btn.on_click(cancel_group, remove=False)
                var_info_btn.on_click(display_var_info, remove=False)
                user_guide_btn.on_click(display_user_guide, remove=False)

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
                user_guide_btn.disabled = False
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
                new_group_btn.on_click(new_group, remove=False)
                save_group_btn.on_click(save_group, remove=True)
                delete_group_btn.on_click(delete_group, remove=True)
                cancel_group_btn.on_click(cancel_group, remove=True)
                var_info_btn.on_click(display_var_info, remove=True)
                user_guide_btn.on_click(display_user_guide, remove=True)

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
                new_group_btn.tooltip = 'New group...'
                update_group_btn.tooltip = 'Update group...'
                var_info_btn.disabled = True
                user_guide_btn.disabled = True

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
        label_layout = wd.Layout(min_width='125px')

        # row 1
        group_label = wd.HTML('<b><i>Available groups: </i></b>',
                              layout=label_layout)
        group_drop = wd.Dropdown(layout=wd.Layout(width='148pt',
                                                  height='40px'),
                                 description_tooltip='Group name')
        group_box = wd.VBox([group_label, group_drop])

        station_label = wd.HTML('<b><i>ICOS Stations: </i></b>',
                                layout=label_layout)
        station_drop = wd.Dropdown(layout=drop_layout,
                                   description_tooltip='ICOS Station')
        station_box = wd.HBox([group_label, group_drop])
        product_label = wd.HTML('<b><i>Files: </i></b>',
                                layout=label_layout)
        spec_drop = wd.Dropdown(layout=drop_layout,
                                description_tooltip='File name')
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
        new_group_btn = wd.Button(description='New', icon='plus',
                                  button_style='primary')
        update_group_btn = wd.Button(description='Update', icon='pen',
                                     button_style='info')
        save_group_btn = wd.Button(description='Save', icon='save',
                                   button_style='success')
        cancel_group_btn = wd.Button(description='Cancel', icon='ban',
                                     button_style='info')
        delete_group_btn = wd.Button(description='Delete', icon='trash',
                                     button_style='danger')
        create_btns = wd.HBox([new_group_btn, update_group_btn])

        user_guide_btn = wd.Button(description='User guide',
                                   icon='fa-info-circle',
                                   button_style='info')
        var_info_btn = wd.Button(description='Variable info',
                                 icon='fa-info-circle',
                                 button_style='info')

        non_create_btns = wd.HBox([save_group_btn,
                                   cancel_group_btn,
                                   delete_group_btn])
        all_btns = wd.HBox([create_btns,
                            non_create_btns,
                            user_guide_btn,
                            var_info_btn])

        # Variable info-text
        var_info_text = wd.HTML(layout=wd.Layout(width='100%',
                                                 max_width='90%',
                                                 height='auto'))
        # Help text to user
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

        upd_box = wd.VBox([wd.HBox([user_guide_container,
                                    var_info_container]),
                           wd.HBox([station_drop, spec_drop]),
                           wd.HBox([group_name, group_vars_upd]),
                           var_box])

        # observe choices
        group_drop.observe(set_group_vars, names='value')

        # Init widgets
        init()

        if not self.debug:
            group_dict_log.layout.display = 'None'

        display(wd.VBox([wd.HBox([group_drop, g_vars]), all_btns, upd_box]))
