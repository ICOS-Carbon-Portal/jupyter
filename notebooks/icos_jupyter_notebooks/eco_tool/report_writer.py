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
            self.debug_value(0, 'ReportWriter init')
        else:
            self.debug_value = None

        self.retriever = retriever

        self.plot = None
        self.icos_info = icos_info

        self.stations_df = self.icos_info.stations_df
        self.timestamp = datetime.datetime.today().strftime('YYYY-MM-DD')

        self.user_settings = self._load_user_settings()

        self.stored_timeseries = {}
        self.cached_reports = {}
        if self.debug:
            self.debug_out = wd.Output()
        self.reset_plot()

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
                           plot_setup: str,
                           start_date,
                           end_date):
        if self.debug:
            self.debug_value(2, '_get_stored_output()',
                             f'group: {group}',
                             f'plot_setup = {plot_setup}'
                             f'start_date: {start_date}',
                             f'end_date = {end_date}')
        date_key = str((start_date, end_date))
        out_ls = []
        if group in self.cached_reports.keys():
            if plot_setup in self.cached_reports[group].keys():
                if date_key in self.cached_reports[group][plot_setup].keys():
                    out_ls = self.cached_reports[group][plot_setup][date_key]
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
                         plot_setup_ls: list,
                         start_date,
                         end_date):
        df_of_group = self._get_data(grp,
                                     start_date,
                                     end_date)
        stns = df_of_group.icos_station_name
        stn_ids = df_of_group.icos_station_id
        products = df_of_group.icos_product
        urls = df_of_group.icos_accessUrl
        today = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        if len(plot_setup_ls) == 1:
            rep_header = f'<h2>Report of plot setup: <i>' \
                         f'{plot_setup_ls[0]}</i></h2>'
        else:
            plot_setup_names = ', '.join(plot_setup_ls)
            rep_header = f'<h2>Report of plot setups: <i>' \
                         f'{plot_setup_names}</i></h2>'
        rep_title = f'<table style="text-align:left; line-height: 1.15; ' \
                    f'            margin-left: 30px">' \
                    f'     <tr>' \
                    f'         <td style="padding-right: 30px">' \
                    f'              <b>Group of variables:</b> </td>' \
                    f'         <td><i>{grp}</i></td>' \
                    f'     </tr>' \
                    f'     <tr>' \
                    f'         <td style="padding-right: 30px">' \
                    f'              <b>Start date:</b></td>' \
                    f'         <td><i>{start_date}</i></td>' \
                    f'     </tr>' \
                    f'     <tr>' \
                    f'         <td style="padding-right: 30px">' \
                    f'              <b>End date:</b></td>' \
                    f'         <td><i>{end_date}</i></td>' \
                    f'     </tr>' \
                    f'     <tr>' \
                    f'         <td style="padding-right: 30px">' \
                    f'              <b>Execution timestamp:</b></td> ' \
                    f'         <td><i>{today}</i></td>' \
                    f'     </tr>' \
                    f'</table>'

        data_descr_ls = []
        links_ls = []
        if all((isinstance(x, str) for x in [stns, stn_ids, products, urls])):
            data_descr_ls.append(f'<a href="{urls}" target = "_blank">'
                                 f'<font color="DarkBlue">{products}'
                                 f'</font></a> of {stns} ({stn_ids})')
        elif all((isinstance(x, list) for x in [stns, stn_ids, products,
                                                urls])) and \
                len(stns) == len(stn_ids) == len(products) and \
                len(products) == len(urls):
            stns = [f'{s[0]} ({s[1]})' for s in zip(stns, stn_ids)]
            d = {}
            for k, v in list(zip(stns, list(zip(products, urls)))):
                if k in d.keys():
                    d[k].append(v)
                else:
                    d[k] = [v]

            for s, v_ls in d.items():
                data_of_station_ls = []

                for tup in v_ls:
                    data_of_station_ls.append(f'<a href="{tup[1]}" target = '
                                              f'"_blank">'
                                              f'<font color="DarkBlue">{tup[0]}'
                                              f'</font></a>')

                data_descr_ls.append(', '.join(data_of_station_ls) + f' of {s}')
        else:
            if isinstance(products, str):
                products = [products]
            data_descript = f'Data from {", ".join(products)}'
            if isinstance(stns, str):
                stns = [stns]
            data_descript += f', collected at {", ".join(stns)}'
            data_descr_ls.append(data_descript)

            if isinstance(urls, str):
                urls = [urls]

            for u in urls:
                links_ls.append(f'<a href = "{u}" target = "_blank"> {u} </a>')

        if not links_ls:
            data_description = f'<h4>' \
                               f'<table style="text-align:left; ' \
                               f'              line-height: 1.15">' \
                               f'     <tr>' \
                               f'         <td>Data from  </td>' \
                               f'         <td>{data_descr_ls.pop(0)}</td>' \
                               f'     </tr>'
            while data_descr_ls:
                data_description += f'     <tr>' \
                                    f'         <td></td>' \
                                    f'         <td>{data_descr_ls.pop(0)}</td>' \
                                    f'     </tr>'
            data_description += '</table>'
        else:
            data_description = 'Data from ' + '; <br>'.join(data_descr_ls) + \
                '<br>Links to data: ' + ', '.join(links_ls)
        data_description = f'<h4>{data_description}</h4>'

        report_title = f'<div style="text-align:left; ' \
                       f'            line-height: 0.7;' \
                       f'            padding-bottom: 0px">' \
                       f'{rep_header}' \
                       f'{rep_title}{data_description}' \
                       f'</div>'

        return wd.HTML(value=report_title)

    def get_plot_setup_report(self,
                              group: str,
                              plot_setup_ls: list,
                              start_date,
                              end_date):

        self._cleanup_stored_data()

        if isinstance(plot_setup_ls, str):
            plot_setup_ls = [plot_setup_ls]

        out_dict = {'header': self._title_of_report(group, plot_setup_ls,
                                                    start_date,
                                                    end_date)}
        for ps in plot_setup_ls:
            out_dict[ps] = self._get_single_plot_setup_report(group,
                                                              ps,
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

    def _var_list_to_output_texts(self, var_ls, plot_type) -> tuple:
        """
            Returns a tuple:
                (second_title, plot_title, legend_list),
            where
                second_title
                    is a string =   details of variables of the
                                    output of a plot_type
                                    (row below main title)
                plot_title
                    a string
                        the subtitle of the output of a plot_type,
                        exception --  plot_type = 'split_plot', where
                        the legend_list is used
                        (row in center above plot)

                legend_list = of legend titles
        """

        out = gui.IcosVarGui.var_tuple_ls_converter(var_ls=var_ls,
                                                    output='var_plot_texts',
                                                    var_plot_type=plot_type,
                                                    debug_fun=self.debug_value)
        if self.debug:
            self.debug_value(888, '_var_list_to_output_texts  --- ',
                             f'out = {out}')
        return out

    def _get_single_plot_setup_report(self,
                                      group: str,
                                      plot_setup: str,
                                      start_date,
                                      end_date):
        if self.debug:
            self.debug_value(4, '_get_single_plot_setup_report() ',
                             f'-- group = {group}',
                             f'-- plot_setup = {plot_setup}',
                             f'-- start_date = {start_date}',
                             f'-- end_date = {end_date}')

        result_ls = self._get_stored_output(group, plot_setup, start_date,
                                            end_date)
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
        plot_setup_dict = cache['_groups'][group]['_plot_setups'][plot_setup]
        b = {k: v for k, v in plot_setup_dict.items() if k != '_version'}
        for number, v in b.items():
            number = str(int(number)+1)
            if self.debug:
                self.debug_value(4, '_get_single_plot_setup_report() ',
                                 f'-- number = {number}',
                                 f'-- v = {v}')
            for p_type, p_type_vars in v.items():
                if p_type == 'split_plot':
                    if p_type_vars == 'all':
                        df_of_plot_setup_p_type = data
                        unit_ls = group_unit_ls
                        var_ls = grp_vars
                    else:
                        # create filtered dataframe
                        var_ls = p_type_vars
                        p_type_cols = []
                        unit_ls = []
                        for p_type_v in p_type_vars:
                            index_of_var = grp_vars.index(p_type_v)
                            p_type_cols.append(df_grp_cols[index_of_var])
                            unit_ls.append(group_unit_ls[index_of_var])
                        df_of_plot_setup_p_type = data[p_type_cols]
                    var_texts = self._var_list_to_output_texts(var_ls, p_type)
                    second_title, subtitles, legend_titles = var_texts

                    title = f'Output #{number} of {plot_setup} - ' \
                            f'<b>Split-plot</b>'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'units', 'title'],
                    #                       [df_of_plot_setup_p_type,
                    #                        unit_ls, title]))
                    #     fig = p.apply(func=self.plot.split_plot,
                    #                   kwds=kwargs)
                    fig = self.plot.split_plot(df=df_of_plot_setup_p_type,
                                               units=unit_ls,
                                               title=title,
                                               second_title=second_title,
                                               subtitles=subtitles)
                    result_ls.append((p_type, fig))
                elif p_type == 'multi_plot':
                    yaxis1_vars = []
                    yaxis1 = []
                    unit1 = None
                    yaxis2_vars = []
                    yaxis2 = []
                    unit2 = None
                    legend_titles = []
                    var_texts = self._var_list_to_output_texts(p_type_vars, p_type)
                    second_title, plot_title, legend_ls = var_texts
                    for axis in p_type_vars:
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
                    df_of_plot_setup_p_type = data[yaxis1_vars + yaxis2_vars]
                    title = f'Output #{number} of {plot_setup} - ' \
                            f'<b>Multi-plot</b>'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'yaxis1', 'yaxis2',
                    #                        'unit1', 'unit2',
                    #                        'title', 'subtitle'],
                    #                       [df_of_plot_setup_p_type,
                    #                        yaxis1, yaxis2,
                    #                        units1, units2,
                    #                        title, subtitle]))
                    #     fig = p.apply(func=self.plot.multi_plot,
                    #                   kwds=kwargs)
                    fig = self.plot.multi_plot(df=df_of_plot_setup_p_type,
                                               yaxis1_vars=yaxis1_vars,
                                               yaxis2_vars=yaxis2_vars,
                                               yaxis1=yaxis1,
                                               yaxis2=yaxis2,
                                               unit1=unit1,
                                               unit2=unit2,
                                               title=title,
                                               second_title=second_title,
                                               # subtitle=plot_title,
                                               legend_titles=legend_titles)
                    result_ls.append((p_type, fig))
                elif p_type == 'corr_plot':
                    p_type_cols = []
                    unit_ls = []
                    for p_type_v in p_type_vars:
                        i = grp_vars.index(p_type_v)
                        p_type_cols.append(df_grp_cols[i])
                        unit_ls.append(group_unit_ls[i])
                    df_of_plot_setup_p_type = data[p_type_cols]
                    title = f'Output #{number} of {plot_setup} - ' \
                            f'<b>Correlation plot</b>'
                    if self.debug:
                        self.debug_value(4, '_get_single_plot_setup_report() --- ',
                                         f'p_type_vars == {p_type_vars}')
                    subtitle = f'{p_type_vars[0][0]} vs {p_type_vars[1][0]}'
                    if p_type_vars[0][1] != p_type_vars[1][1] and \
                            p_type_vars[0][2] != p_type_vars[1][2]:
                        subtitle += f' (from <i>{p_type_vars[0][1]}</i> of ' \
                                    f'<i>{p_type_vars[0][2]}</i>, and ' \
                                    f'<i>{p_type_vars[1][1]}</i> of ' \
                                    f'<i>{p_type_vars[1][2]}</i>, respectively)'
                    elif p_type_vars[0][1]!=p_type_vars[1][1]:
                        subtitle += f' (from <i>{p_type_vars[0][1]}</i> and ' \
                                    f'<i>{p_type_vars[1][1]}</i> of ' \
                                    f'<i>{p_type_vars[0][2]}</i>, respectively)'
                    elif p_type_vars[0][2]!=p_type_vars[1][2]:
                        subtitle += f' (from <i>{p_type_vars[0][1]}</i> ' \
                                    f'of <i>{p_type_vars[0][2]}</i> and ' \
                                    f'<i>{p_type_vars[1][2]}</i>, respectively)'
                    else:
                        subtitle += f' (from <i>{p_type_vars[0][1]}</i> of ' \
                                    f'<i>{p_type_vars[0][2]}</i>)'

                    # with Pool(processes=2) as p:
                    #     kwargs = dict(zip(['df',
                    #                        'x_col', 'y_col',
                    #                        'units', 'title', 'subtitle'],
                    #                       [df_of_plot_setup_p_type,
                    #                        p_type_cols[0], p_type_cols[1],
                    #                        unit_ls, title, subtitle]))
                    #     fig = p.apply(func=self.plot.corr_plot,
                    #                   kwds=kwargs)

                    fig = self.plot.corr_plot(df=df_of_plot_setup_p_type,
                                              x_col=p_type_cols[0],
                                              y_col=p_type_cols[1],
                                              units=unit_ls,
                                              title=title,
                                              subtitle=subtitle)
                    result_ls.append((p_type, fig))
                elif p_type == 'corr_table':
                    if p_type_vars == 'all':
                        df_of_plot_setup_p_type = data
                        var_ls = grp_vars
                    else:
                        # create filtered dataframe
                        var_ls = p_type_vars
                        p_type_cols = []
                        for p_type_v in p_type_vars:
                            index_of_var = grp_vars.index(p_type_v)
                            p_type_cols.append(df_grp_cols[index_of_var])
                        df_of_plot_setup_p_type = data[p_type_cols]
                    var_texts = self._var_list_to_output_texts(var_ls, p_type)
                    second_title, _, legend_titles = var_texts

                    title = f'Output #{number} of {plot_setup} - Correlation ' \
                            f'table'
                    fig = self.plot.corr_table(df=df_of_plot_setup_p_type,
                                               title=title,
                                               second_title=second_title,
                                               legend_titles=legend_titles)

                    result_ls.append((p_type, fig)) #(p_type, 'Not implemented'))
                elif p_type == 'statistics':
                    result_ls.append((p_type, 'Not implemented'))
                else:
                    result_ls.append((p_type, 'Not implemented'))

        date_key = str((start_date, end_date))
        upd_dict = {group: {plot_setup: {date_key: result_ls}}}
        self.cached_reports.update(upd_dict)
        return result_ls

    def remove_reports(self, group: str = None, plot_setup: str = None):
        if group:
            if plot_setup and group in self.cached_reports.keys():
                self.cached_reports[group].pop(plot_setup, None)
                if not self.cached_reports[group]:
                    self.cached_reports.pop(group)
            elif group in self.cached_reports.keys():
                self.cached_reports.pop(group)
        else:
            self.cached_reports = {}

    def remove_timeseries(self, group: str = None):
        if group:
            self.stored_timeseries.pop(group, None)
        else:
            self.stored_timeseries = {}
        self.remove_reports(group=group)

    def reset_plot(self):
        user_plot_settings = self._load_user_settings()
        if self.debug:
            self.debug_value(10, 'reset_plot()',
                             f'user_plot_settings = {user_plot_settings}')
        self.remove_reports()
        self.plot = plot.Plot(debug_function=self.debug_value,
                              **user_plot_settings)
