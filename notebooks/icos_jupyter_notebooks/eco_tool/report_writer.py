#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local storage of reports.
"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.1"
__date__ = "2023-06-11"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import datetime
from icoscp.cpb.dobj import Dobj
from ipywidgets import widgets as wd
import os
if os.getcwd()[-8:] == 'eco_tool':
    import gui
    import icos_data
    import plot
    import plot2
    from icos_timeseries import IcosFrame
    import json_handler as json_manager
else:
    from eco_tool import gui
    from eco_tool import icos_data
    from eco_tool import plot
    from eco_tool import json_handler as json_manager
    from multiprocessing import Pool
import warnings
warnings.simplefilter("ignore", FutureWarning)


class ReportWriter:

    def __init__(self, retriever, icos_info, debug_function=None,
                 multiproc: bool = None):

        self.debug = True if debug_function else False
        if self.debug:
            self.debug_value = debug_function
        else:
            self.debug_value = None

        self.retriever = retriever

        user_plot_settings = self._load_user_settings()
        if self.debug:
            self.debug_value(0, 'ReportWriter init',
                             f'user_plot_settings: {user_plot_settings}')
        self.plot = plot.Plot(debug_function=debug_function,
                              **user_plot_settings)

        self.icos_info = icos_info

        self.stations_df = self.icos_info.stations_df
        self.timestamp = datetime.datetime.today().strftime('YYYY-MM-DD')

        self.user_settings = self._load_user_settings()

        self.stored_timeseries = {}
        self.cached_reports = {}
        if self.debug:
            self.debug_out = wd.Output()

    def __del__(self):
        del self.plot
        del self.icos_info
        del self.stations_df

    def _load_cache(self) -> dict:
        return self.retriever.load_cache()

    def _load_json(self,
                   default_dict: dict = None,
                   json_file: str = None):
        if default_dict is None:
            default_dict = {}
        try:
            return_dict = json_manager.read(path_to_json_file=json_file)
        except Exception as e:
            return_dict = {}
            if self.debug:
                self.debug_value(1, '_load_json --- Exception',
                                 f'Check the file: {json_file}',
                                 f'exception = {e}')
        finally:
            for k, v in default_dict.items():
                return_dict[k] = return_dict.get(k, v)
        return return_dict

    def _load_user_settings(self) -> dict:
        return self.retriever.load_user_settings()

    def _report_header(self):
        # with out:
        #    display(wd.HTML(value='<h1>Generating report...</h1>'))
        pass

    def _get_stored_output(self,
                           group: str,
                           batch: str,
                           start_date,
                           end_date):
        if self.debug:
            self.debug_value(2, '_get_stored_output()',
                             f'group: {group}',
                             f'batch = {batch}'
                             f'start_date: {start_date}',
                             f'end_date = {end_date}')
        key2output = str((group, batch, start_date, end_date))
        if key2output in self.cached_reports.keys():
            out_ls = self.cached_reports[key2output]
        else:
            out_ls = []
        return out_ls

    def _get_data(self,
                  group: str,
                  start_date,
                  end_date):

        # Reuse timeseries if possible
        df = None
        stored_df = self.stored_timeseries.get(group, None)
        if stored_df:
            if stored_df['start'] <= start_date and stored_df['end'] >= end_date:
                # reuse df
                df = stored_df['df']
        if df is None:
            # we need to fetch the data
            settings = self._load_user_settings()
            if 'run_configs' in settings.keys():
                days = settings['run_configs'].get('fetch_date', 6)
            else:
                days = 6
            cache = self._load_cache()
            var_tuple_ls = cache['_groups'][group]['_group_vars']
            st_df = self.stations_df

            var_pid_ls = []
            for var, prod, stn in var_tuple_ls:
                # sampleheight needed for 'AS'
                pid = st_df.loc[(st_df.id == stn) & (st_df.specLabel ==
                                                     prod)].dobj.values[0]
                var_pid_ls.append((var, pid))

            stored_start = start_date + datetime.timedelta(days=-days)
            stored_end = end_date

            if self.debug:
                self.debug_value(3, '_get_data()',
                                 f'var_pid_ls = {var_pid_ls}')
            df = None
            try:
                df = icos_data.StationData.group_ts(var_tuple_ls=var_pid_ls,
                                                    start_date=stored_start,
                                                    end_date=stored_end)
            except Exception as e:
                if self.debug:
                    import traceback
                    self.debug_value(3, '_get_data() -- Exception',
                                     f'Error in call to '
                                     f'calling icos_data.StationData.group_ts()',
                                     f'-- var_tuple_ls = {var_pid_ls}',
                                     f'-- start_date = {stored_start}',
                                     f'-- end_date = {stored_end}',
                                     f'-- type(stored_start) = '
                                     f'{type(stored_start)}',
                                     f'-- type(stored_end) = {type(stored_end)}',
                                     f'Exception = {e}',
                                     f'Traceback:  {traceback.format_exc()}')

            # Store the timeseries, we only store one timeseries per group
            self.stored_timeseries[group] = {'start': stored_start,
                                             'end': stored_end,
                                             'df': df}
        return df

    def get_group_report(self, grp: str,
                         start_date,
                         end_date):
        pass

    def _title_of_report(self, grp: str,
                         batch_ls: list,
                         start_date,
                         end_date):
        df_of_group = self._get_data(grp,
                                     start_date,
                                     end_date)
        stns = df_of_group.icos_station_name
        products = df_of_group.icos_product
        urls = df_of_group.icos_accessUrl
        today = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        if len(batch_ls) == 1:
            rep_title1 = f'<h2>Report of batch job: <i>{batch_ls[0]}</i>.<br>' \
                         f'Group of variables: <i>{grp}</i>.<br>' \
                         f'Data collected at <i>{today}</i>.</h2><br>'
        else:
            batch_names = ', '.join(batch_ls)
            rep_title1 = f'<h2>Report of batch jobs: <i>{batch_names}</i>.<br>' \
                         f'Group of variables: <i>{grp}</i>.<br>' \
                         f'Data collected at <i>{today}</i>.</h2><br>'
        rep_title2 = 'Data from '
        rep_title3 = ''
        if all((isinstance(x, str) for x in [stns, products, urls])):
            rep_title2 += f'<a href="{urls}" target = "_blank">\
                        <font color="DarkBlue">{products}</font></a> of {stns}.'
        elif all((isinstance(x, list) for x in [stns, products, urls])) and \
                len(stns) == len(products) and len(products) == len(urls):
            n = len(stns)
            d = {}
            for i in range(n):
                s = stns[i]
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
                products =[products]
            rep_title2 += f'Data from {", ".join(products)}'

            if isinstance(stns, str):
                stns = [stns]
            rep_title2 += f' collected at {", ".join(stns)}.'
            rep_title2 = f'<h2>{rep_title2}</h2><br>'

            if isinstance(urls, str):
                urls = [urls]
            rep_title3 += 'Links to data:  '
            for u in urls:
                rep_title3 += f'<a href = "{u}" target = "_blank"> {u} </a>.'

        rep_title2 = f'<h3>{rep_title2}</h3>'
        report_title = rep_title1 + rep_title2 + rep_title3

        return wd.HTML(value=report_title)

    def get_batch_report(self,
                         group: str,
                         batch_ls: list,
                         start_date,
                         end_date):

        self._cleanup_stored_data()

        if isinstance(batch_ls, str):
            batch_ls = [batch_ls]

        out_dict = {'main_title': self._title_of_report(group, batch_ls,
                                                        start_date,
                                                        end_date)}
        for b in batch_ls:
            out_dict[b] = {'batch_title': wd.HTML(value=f'<h3>Result from '
                                                        f'<i>{b}</i></h3>')}
            out_dict[b]['result'] = self._get_single_batch_report(group,
                                                                  b,
                                                                  start_date,
                                                                  end_date)
        return out_dict

    def _cleanup_stored_data(self):
        # In the case the user did not restart the application
        # since yesterday old reports are removed.
        now = datetime.datetime.today().strftime('YYYY-MM-DD')
        if now != self.timestamp:
            self.timestamp = now
            self.cached_reports = {}
            self.stored_timeseries = {}

    def _var_list_to_output_texts(self, var_ls, tool) -> tuple:
        """
            Returns a tuple:
                (second_title, plot_title, legend_list),
            where
                second_title
                    is a string =   details of variables of the
                                    output of a tool
                                    (row below main title)
                plot_title
                    a string
                        the subtitle of the output of a tool,
                        exception --  tool = 'split_plot', where
                        the legend_list is used
                        (row in center above plot)

                legend_list = of legend titles
        """

        out = gui.AnalysisGui.var_tuple_ls_converter(var_ls=var_ls,
                                                     output='var_plot_texts',
                                                     var_plot_tool=tool,
                                                     debug_fun=self.debug_value)
        if self.debug:
            self.debug_value(888, '_var_list_to_output_texts  --- ',
                             f'out = {out}')
        return out

    def _get_single_batch_report(self,
                                 group: str,
                                 batch: str,
                                 start_date,
                                 end_date):
        if self.debug:
            self.debug_value(4, '_get_single_batch_report() ',
                             f'-- group = {group}',
                             f'-- batch = {batch}',
                             f'-- start_date = {start_date}',
                             f'-- end_date = {end_date}')

        result_ls = self._get_stored_output(group, batch, start_date, end_date)
        if result_ls:
            return result_ls

        df_of_group = self._get_data(group,
                                     start_date,
                                     end_date)
        data = df_of_group[start_date:end_date]
        group_unit_ls = df_of_group.icos_var_unit_ls
        df_grp_cols = list(df_of_group.columns)
        cache = self._load_cache()
        grp_vars = cache['_groups'][group]['_group_vars']
        batch_dict = cache['_groups'][group]['_batches'][batch]
        b = {k: v for k, v in batch_dict.items() if k != '_version'}
        for number, v in b.items():
            number = str(int(number)+1)
            if self.debug:
                self.debug_value(4, '_get_single_batch_report() ',
                                 f'-- number = {number}',
                                 f'-- v = {v}')
            for tool, tool_vars in v.items():
                if tool == 'split_plot':
                    if tool_vars == 'all':
                        df_of_batch_tool = data
                        unit_ls = group_unit_ls
                        var_ls = grp_vars
                    else:
                        # create filtered dataframe
                        var_ls = tool_vars
                        tool_cols = []
                        unit_ls = []
                        for tool_v in tool_vars:
                            index_of_var = grp_vars.index(tool_v)
                            tool_cols.append(df_grp_cols[index_of_var])
                            unit_ls.append(group_unit_ls[index_of_var])
                        df_of_batch_tool = data[tool_cols]
                    var_texts = self._var_list_to_output_texts(var_ls, tool)
                    second_title, _, legend_titles = var_texts

                    title = f'Output #{number} of {batch} - Split plot'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'units', 'title'],
                    #                       [df_of_batch_tool,
                    #                        unit_ls, title]))
                    #     fig = p.apply(func=self.plot.split_plot,
                    #                   kwds=kwargs)
                    fig = self.plot.split_plot(df=df_of_batch_tool,
                                               units=unit_ls,
                                               title=title,
                                               second_title=second_title,
                                               subtitles=legend_titles,
                                               legend_titles=legend_titles)
                    result_ls.append((tool, fig))
                elif tool == 'multi_plot':
                    yaxis1_vars = []
                    yaxis1 = []
                    unit1 = None
                    yaxis2_vars = []
                    yaxis2 = []
                    unit2 = None
                    legend_titles = []
                    var_texts = self._var_list_to_output_texts(tool_vars, tool)
                    second_title, plot_title, legend_ls = var_texts
                    for axis in tool_vars:
                        columns_of_axis = []
                        legend_titles.extend(legend_ls)
                        y_ax_vars = []
                        for var in axis[1]:
                            i = grp_vars.index(var)
                            columns_of_axis.append(df_grp_cols[i])
                            if var[0] not in y_ax_vars:
                                y_ax_vars.append(var[0])
                        if not yaxis1:
                            yaxis1_vars = columns_of_axis
                            unit1 = axis[0]
                            yaxis1 = y_ax_vars
                        else:
                            yaxis2_vars = columns_of_axis
                            unit2 = axis[0]
                            yaxis2 = y_ax_vars
                    df_of_batch_tool = data[yaxis1_vars + yaxis2_vars]
                    title = f'Output #{number} of {batch} - <b>Multi-plot</b>'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'yaxis1', 'yaxis2',
                    #                        'unit1', 'unit2',
                    #                        'title', 'subtitle'],
                    #                       [df_of_batch_tool,
                    #                        yaxis1, yaxis2,
                    #                        units1, units2,
                    #                        title, subtitle]))
                    #     fig = p.apply(func=self.plot.multi_plot,
                    #                   kwds=kwargs)
                    fig = self.plot.multi_plot(df=df_of_batch_tool,
                                               yaxis1_vars=yaxis1_vars,
                                               yaxis2_vars=yaxis2_vars,
                                               yaxis1=yaxis1,
                                               yaxis2=yaxis2,
                                               unit1=unit1,
                                               unit2=unit2,
                                               title=title,
                                               second_title=second_title,
                                               subtitle=plot_title,
                                               legend_titles=legend_titles)
                    result_ls.append((tool, fig))
                elif tool == 'corr_plot':
                    tool_cols = []
                    unit_ls = []
                    for tool_v in tool_vars:
                        i = grp_vars.index(tool_v)
                        tool_cols.append(df_grp_cols[i])
                        unit_ls.append(group_unit_ls[i])
                    df_of_batch_tool = data[tool_cols]
                    title = f'Output #{number} of {batch} - Correlation plot '
                    if self.debug:
                        self.debug_value(4, '_get_single_batch_report() --- ',
                                         f'tool_vars == {tool_vars}')
                    subtitle = f'{tool_vars[0][0]} vs {tool_vars[1][0]}'
                    if tool_vars[0][1] != tool_vars[1][1] and \
                            tool_vars[0][2] != tool_vars[1][2]:
                        subtitle += f' (from <i>{tool_vars[0][1]}</i> of ' \
                                    f'<i>{tool_vars[0][2]}</i>, and ' \
                                    f'<i>{tool_vars[1][1]}</i> of ' \
                                    f'<i>{tool_vars[1][2]}</i>, respectively)'
                    elif tool_vars[0][1]!=tool_vars[1][1]:
                        subtitle += f' (from <i>{tool_vars[0][1]}</i> and ' \
                                    f'<i>{tool_vars[1][1]}</i> of ' \
                                    f'<i>{tool_vars[0][2]}</i>, respectively)'
                    elif tool_vars[0][2]!=tool_vars[1][2]:
                        subtitle += f' (from <i>{tool_vars[0][1]}</i> ' \
                                    f'of <i>{tool_vars[0][2]}</i> and ' \
                                    f'<i>{tool_vars[1][2]}</i>, respectively)'
                    else:
                        subtitle += f' (from <i>{tool_vars[0][1]}</i> of ' \
                                    f'<i>{tool_vars[0][2]}</i>)'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'x_col', 'y_col',
                    #                        'units', 'title', 'subtitle'],
                    #                       [df_of_batch_tool,
                    #                        tool_cols[0], tool_cols[1],
                    #                        unit_ls, title, subtitle]))
                    #     fig = p.apply(func=self.plot.corr_plot,
                    #                   kwds=kwargs)

                    fig = self.plot.corr_plot(df=df_of_batch_tool,
                                              x_col=tool_cols[0],
                                              y_col=tool_cols[1],
                                              units=unit_ls,
                                              title=title,
                                              subtitle=subtitle)
                    result_ls.append((tool, fig))
                elif tool == 'corr_table':
                    result_ls.append((tool, 'Not implemented'))
                elif tool == 'statistics':
                    result_ls.append((tool, 'Not implemented'))
                else:
                    result_ls.append((tool, 'Not implemented'))

        key2output = str((group, batch, start_date, end_date))
        self.cached_reports[key2output] = result_ls

        return result_ls
