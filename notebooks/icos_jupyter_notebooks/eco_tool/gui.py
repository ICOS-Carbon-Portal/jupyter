#!/usr/bin/python

"""
    This is the main entry to run the
    Ecosystem notebook for PIs.
    In the gui the user can create
    groups of variables and plot setups to run

    The purpose is to run the program from
    a notebook on https://jupyter.icos-cp.eu/
    using
    >>> from eco_tool import gui
    >>> g = gui.IcosVarGui();
"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.2"
__date__ = "2023-06-11"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

from ipywidgets import widgets as wd
from IPython.display import display, Math, clear_output
import datetime as dt
import copy
import os

import warnings
warnings.simplefilter("ignore", FutureWarning)

_, work_dir = os.path.split(os.getcwd())
if work_dir == 'eco_tool':
    import icos_data
    import report_writer
    from icos_timeseries import IcosFrame
    import json_handler
    import icos2latex
    import trace_debug
else:
    from eco_tool import icos_data
    from eco_tool import report_writer
    from eco_tool.icos_timeseries import IcosFrame
    from eco_tool import json_handler
    from eco_tool import icos2latex
    from eco_tool import trace_debug


class _AppDataRetriever:
    """
        Object to retrieve/read appdata settings.
        We use the same instance in other objects.
    """

    def __init__(self, app_config_file: str, user_cache_file: str,
                 user_config_file: str, debug_function=None):

        self.debug = True if debug_function else False
        if self.debug:
            self.debug_value = debug_function
            self.debug_value(0, '_AppDataRetriever init with debugger')
        self.app_config_file = app_config_file
        self.user_cache_file = user_cache_file
        self.user_config_file = user_config_file
        self.cache = None
        self.app_config_dict = None

    def load_app_configs(self):
        if self.debug:
            self.debug_value(1, 'load_app_configs')

        if not self.app_config_dict:
            default_dict = {'_var2unit_map': {}}
            self.app_config_dict = self._load_json(default_dict=default_dict,
                                                   json_file=self.app_config_file)
        return self.app_config_dict

    def load_cache(self, refresh: bool = None):
        if self.debug:
            self.debug_value(2, 'load_cache', f'refresh = {refresh}')

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


class IcosVarGui:
    # Colors of ipywidgets predefined styles
    widget_style_colors = {'text_color': '#FFFFFF', 'primary': '#2196F3',
                           'primary:active': '#1976D2', 'success': '#4CAF50',
                           'success:active': '#388E3C', 'info:active': '#0097A7',
                           'warning': '#FF9800', 'warning:active': '#F57C00',
                           'danger': '#F44336', 'danger:active': '#D32F2F'}

    @property
    def help_dict(self):
        return {'group': {'read_header1': '<h3><span style="color:black">'
                                          'To create a group of '
                                          'variables: </span></h3>',
                          'read_body1': '<ol>'
                                        '<li> Press <b><i>New</i></b></li>'
                                        '<ul>'
                                        '<li> Select a station/stations </li>'
                                        '<li> Select a product/products </li>'
                                        '<li> Choose variables </li>'
                                        '</ul>'
                                        '<li> Choose a name for the group </li>'
                                        '<li> Press <b><i>Save</i></b></li>'
                                        '</ol>',
                          'read_header2': '<h3><span style="color:black">'
                                          'To edit a group of variables: </span>'
                                          '</h3>',
                          'read_body2': '<ol>'
                                        '<li> Select the group to change and '
                                        'press <b><i>Update</i></b></li>'
                                        '<li> Select or deselect variables'
                                        '</li>'
                                        '<li> Rename the group if needed'
                                        '</li>'
                                        '<li> Press <b><i>Save</i></b></li>'
                                        '</ol>',
                          'read_header3': '<h3><span style="color:black">'
                                          'To delete a group of variables: '
                                          '</span>'
                                          '</h3>',
                          'read_body3': '<ol>'
                                        '<li> Select the group and press '
                                        '<b><i>Update</i></b></li>'
                                        '<li> Click on the '
                                        '<b><i>Delete</i></b> button</li>'
                                        '</ol>',
                          'update_header': '<h3><span '
                                           'style="color:black">Update mode'
                                           '</span></h3>',
                          'update_body': 'Now you can'
                                         '<ul>'
                                         '<li> Choose station and product '
                                         'in order to add or remove variables '
                                         'from the group'
                                         '</li>'
                                         '<li> Rename the group</li>'
                                         '<li> Delete the group'
                                         '</ul>',
                          'new_header': '<h3><span '
                                        'style="color:black">New</span>'
                                        '</h3>',
                          'new_body': 'Steps to create a group of variables:'
                                      '<ol>'
                                      '<li> Select a station, or several '
                                      'stations, but one at a time</li>'
                                      '<li> Select a file/product, or '
                                      'several, but one at a time</li>'
                                      '<li> Select variables. Chosen '
                                      'variables are displayed at '
                                      '<span style="color:black"><i>'
                                      '"Variables in update mode"</i>'
                                      '</span></li>'
                                      '<li> Choose a name for your group of '
                                      'variables and press '
                                      '<b><i>Save</i></b></li>'
                                      '</ol>'
                                      '<br>'
                                      '<b><i>New user?</i></b> By adding '
                                      '<b><i>"+p"</i></b> to the end of '
                                      'the group name, you will '
                                      'get an example plot setup so you can see '
                                      'how some of the plots look like. '
                                      'It will appear as a button <b><i>Plot '
                                      'example</i></b> in the '
                                      '<b><i>Visualise</i></b>-menu.',
                          'new_user': '<b><i>New user?</i></b> By adding '
                                      '<b><i>"+p"</i></b> to the end of '
                                      'the group name, you will '
                                      'get an example plot setup so you can see '
                                      'how some of the plots look like. '
                                      'It will appear as a button <b><i>Plot '
                                      'example</i></b> in the '
                                      '<b><i>Visualise</i></b>-menu. Later on '
                                      'you can always remove or change it.',
                          'general': '<h4><i>General info on group '
                                     'variables</i></h4>'
                                     '<ul>'
                                     '<li> The order of the variables is the '
                                     'order of presentation in outputs, unless '
                                     'specified otherwise in plot setups'
                                     '</li>'
                                     '<li> You can combine variables from '
                                     'different files or stations'
                                     '</li>'
                                     '</ul>'},
                'plot_setup': {'multi_plot':
                                   'In a <b><i>Multi-plot</i></b> there is no '
                                   'limit '
                                   'on the number of variables to display '
                                   'in one plot. However, it is only possible '
                                   'to select variables of at most two '
                                   'different units divided on <i>two horizontal '
                                   'axes</i>. Moreover, by default the '
                                   'variables are divided according to their '
                                   'unit. <br>'
                                   'In the case $x_1$ is a variable on '
                                   'the left axis and $x_2$ is a variable '
                                   'of the same unit, which should be mapped '
                                   'to the right axis: '
                                   '<ol><li>'
                                   'First make sure the '
                                   'checkbox <i>Choose axis according to '
                                   'unit</i>, is unchecked</li>'
                                   '<li>'
                                   'Then click on the $x_2$-variable '
                                   'button twice </li>'
                                   '</ol>'
                                   'A selected variable which the icon '
                                   '$\\mathbb{<<}$ belongs to the left axis, '
                                   'while $\\mathbb{>>}$ indicates that it '
                                   'belongs to the right axis.',
                               'corr_plot':
                                   'Please note that <b><i>Correlation plot'
                                   '</i></b> '
                                   'is a plot for <i>exactly two '
                                   'variables</i>.<br>'
                                   'The first selected variable will be mapped  '
                                   'to the '
                                   'horizontal axis, the $x$-axis, while the '
                                   'second variable will be mapped to the '
                                   'vertical axis, the $y$-axis.',
                               'split_plot':
                                   'In a <b><i>Split-plot</i></b> you can '
                                   'visualise several variables '
                                   'in individual plots. The plots are '
                                   'connected using a <i>zoom-slider</i>, '
                                   'that zooms all plots. ',
                               'corr_table': 'Use the <b><i>Correlation '
                                             'table</i></b> in order to '
                                             'calculate the Pearson\'s '
                                             'correlation coefficient '
                                             'between variables. The value is '
                                             'visualised using a color scale '
                                             'that can be set in the '
                                             '<b><i>Settings</i></b>-menu.',
                               'statistics': '',
                               'read_header1': '<h3><span style="color:black">'
                                               'To create or edit a plot '
                                               'setup: </span></h3>',
                               'read_body1':
                                   '<ul>'
                                   '<li> '
                                   'Choose a group of variables in the upper '
                                   'left dropdown menu and, if applicable, the '
                                   'plot setup to change </li>'
                                   '<li>'
                                   'Press <b><i>New</i></b> or '
                                   '<b><i>Update</i></b></li>'
                                   '<li>'
                                   'Follow the instructions herein'
                                   '</li>'
                                   '</ul>',
                               'read_header2': '<h3><span style="color:black">' 
                                               'To delete a plot setup: '
                                               '</span></h3>',
                               'read_body2': '<ul>'
                                             '<li> Select the plot setup and '
                                             'press '
                                             '<b><i>Update</i></b></li>'
                                             '<li> Click on the '
                                             '<b><i>Delete</i></b> button</li>'
                                             '</ul>',
                               'new_header': '<h3><span style="color:black">' 
                                             'New'
                                             '</span></h3>',
                               'new_edit_body1':
                                   'A plot setup contains one, or several, '
                                   '<b><i>plot types</i></b>, where each plot '
                                   'type is applied to some variables of the '
                                   'group of variables. Each plot setup should '
                                   'have a name which is unique for the '
                                   'group of variables.<br>'
                                   '<i>To add a plot type</i> to the plot setup:'
                                   '<ul>'
                                   '<li>'
                                   'Select a <b><i>plot type</i></b> from the '
                                   'list below <span style="color:black">'
                                   '<b><i>Available plot types</i></b></span>. '
                                   'The plot type will be displayed in '
                                   'the 1:st area to the right of '
                                   '<span style="color:black">'
                                   '<b><i>Current setup</i></b></span>. '
                                   'Please note that this area is <i>locked '
                                   'while a new plot type is checked</i>. '
                                   '</li>'
                                   '<li>Select/deselect variables '
                                   'from <span style="color:black">'
                                   '<b><i>Available variables</i></b></span> in '
                                   'order to add or remove them from the '
                                   'plot type. These will be displayed in '
                                   'the 2:nd area to the right of '
                                   '<span style="color:black">'
                                   '<b><i>Current setup</i></b></span>.'
                                   '</li>'
                                   '<li>'
                                   'To add another plot type, just select it and '
                                   'choose variables for that plot type too.'
                                   '</li>'
                                   '</ul>'
                                   'To change variables of a plot type, '
                                   'or remove a plot type:'
                                   '<ul>'
                                   '<li>'
                                   'Select the plot type from the '
                                   'list to the right of <span '
                                   'style="color:black">'
                                   '<b><i>Available plot types</i></b></span>. '
                                   '</li><li>'
                                   'Add or remove variables using the variable '
                                   'buttons. </li>'
                                   '<li>'
                                   'A plot type without variables will be '
                                   'removed. '
                                   '</li>'
                                   '</ul>'
                                   'Before saving the plot setup it will need '
                                   'a name, this is entered in the area '
                                   '<span style="color:black"><b><i>Name of plot '
                                   'setup</i></b></span>.<br>',
                               'new_edit_body2':
                                   'The list of the plot types, of a plot setup, '
                                   'represents the order of execution, and '
                                   'the order of the variables will be the order '
                                   'of presentation in the outputs.<br>'
                                   'To rearrange the order of execution: '
                                   'Select a plot type in the setup and '
                                   'click the button <b><i>"Up"</i></b>.',
                               'edit_delete_header': '<h3><span style="color:'
                                                     'black">' 
                                                     'Update: </span></h3>',
                               'delete_body': 'To delete the plot setup '
                                              'just press delete without '
                                              'changing the content. ',
                               'new_edit_changes': '<b>Changes are logged in the '
                                                   'file '
                                                   f'"{self.user_cache_bak_file}"'
                                                   f'</b>'},
                'configs': {'run_configs': {},
                            'latex': {},
                            'split_plot': {},
                            'multi_plot': {},
                            'corr_plot': {},
                            'corr_table': {},
                            'statistics': {}},
                'technical': '<h4><i>Stored data - technical info'
                             '</i></h4>'
                             '<ul>'
                             '<li> Groups and plot setups are stored '
                             'in the file: '
                             f'"{self.user_cache_file}".'
                             '<br>'
                             'Changes are logged here: '
                             f'"{self.user_cache_bak_file}"'
                             '</li>'
                             '<li> Settings are stored in the file: '
                             f'"{self.user_config_file}".'
                             '<br>'
                             'Changes are logged here: '
                             f'"{self.user_config_bak_file}".'
                             '</li>'
                             '</ul>'
                             'If you like you can share these with a '
                             'colleague, in order to discuss findings or '
                             'setups etc.'
                }

    @staticmethod
    def var_tuple_ls_converter(var_ls: [] or (str, str, str) or [(str, str, str)],
                               output: str,
                               var_plot_type: str = None,
                               stn_name_id_ls: [(str, str)] = None,
                               debug_fun: callable = None) -> dict or list or str:
        """
            Converts var_ls into output as below.

            Inputs
            ------
            var_ls: list of tuples
                Either an empty list or a list of variables as in the
                list of variables of a groups, that is each element
                should be a tuple of the form
                    (variable, file, station)

            output: str
                output choices:         output of function:
                'var_list':         ->  []
                                        HTML-styled list of variables,
                                        these are of the form
                                            '<b>CO2</b>','<b>H</b>' etc
                                        or if a variable is repeated
                                            '<b>H<sub>1</sub></b>',
                                            '<b>H<sub>2</sub></b>' etc
                'station_dict':     ->  dict(dict(list()))
                                            outer key stations,
                                                inner key products
                                                    inner HTML-styled
                                                    list of variables,
                                                    as in 'var_list'
                'var_btns'          ->  (list(str), list(str, list)
                                        - The list contain strings of labels
                                        (Not HTML) for the var buttons of
                                        plot setups, of the format
                                            'H','CO2 (#1)', 'CO2 (#2)'
                                        - A list of tuples [(stn, prods-list)]
                'var_cont_upd':     ->  Formatted html text for group content
                                        in mode update.
                'var_cont_read':    ->  Formatted html text for group content
                                        in mode read.
                'var_plot_texts':     ->  (str, str, list)
                                        str1 = details of variables of the output
                                        of a plot type.
                                                (row below title)
                                        str2 = subtitle of the output
                                        of a plot type.
                                                (row above plot)
                                        list of legend titles

            var_plot_type: str
                Used with output=='var_plot_texts', that will have
                slight different outputs depending on plot type.
                Choices for var_plot_type:
                 'multi_plot', 'corr_plot', 'split_plot'
                 'corr_table', 'statistics'

            stn_name_id_ls: list(str, str)
                List of (station_name, station_id), needed for
                    output in  ['var_btns', 'var_cont_upd, 'var_cont_read']

            Returns
            dict list or str (depending on output)

        """

        if output in ['var_btns', 'var_plot_texts']:
            def format_var_index(v, ind):
                if ind is not None:
                    return f'{v} (#{ind})'
                return v
        else:
            def format_var_index(v, ind):
                if ind is not None:
                    return f'<b>{v}<sub>{ind}</sub></b>'
                return f'<b>{v}</b>'

        plot_axis = 0
        if var_ls:
            if isinstance(var_ls, list) or isinstance(var_ls, tuple):
                if all(isinstance(x, str) for x in var_ls):
                    var_tuples = [list(var_ls)]
                elif all(isinstance(y, str) for x in var_ls for y in x):
                    var_tuples = copy.deepcopy(var_ls)
                elif len(var_ls) == 2 and all(isinstance(y[1], list) for y in
                                              var_ls):
                    var_tuples = []
                    for y in var_ls:
                        if not plot_axis:
                            plot_axis = len(y[1])
                        var_tuples.extend(copy.deepcopy(y[1]))
                elif len(var_ls) == 1 and all(isinstance(y[1], list) for y in
                                              var_ls):
                    var_tuples = copy.deepcopy(var_ls[0][1])
                else:
                    return
            else:
                return
        else:
            return

        v_ls = [v[0] for v in var_tuples]
        count_ls = [1] * len(v_ls)
        if debug_fun:
            debug_fun(999, 'var_tuple_ls_converter() --- output ',
                      f'output = {output}',
                      f'var_tuples = {var_tuples}',
                      f'v_ls = {v_ls}',
                      f'count_ls = {count_ls}')
        i = 0
        while v_ls:
            var = v_ls.pop(0)
            var_format_index = count_ls.pop(0)
            try:
                next_index_of_var = v_ls.index(var)
            except ValueError:
                next_index_of_var = None
            if isinstance(next_index_of_var, int):
                fm_var = format_var_index(var, var_format_index)
                count_ls[next_index_of_var] += var_format_index
            elif var_format_index > 1:
                fm_var = format_var_index(var, var_format_index)
            else:
                fm_var = format_var_index(var, None)

            var_tuples[i][0] = fm_var
            i += 1
        fm_var_ls = [v[0] for v in var_tuples]

        if output == 'var_list':
            return fm_var_ls

        station_dict1 = {}
        station_dict2 = {}

        for v_tuple in var_tuples:
            st = v_tuple[-1]
            prod = v_tuple[-2]
            var = v_tuple[0]
            if var in fm_var_ls[: plot_axis]:
                if st not in station_dict1:
                    station_dict1[st] = {prod: [var]}
                elif prod not in station_dict1[st]:
                    station_dict1[st][prod] = [var]
                else:
                    station_dict1[st][prod].append(var)
            else:
                if st not in station_dict2:
                    station_dict2[st] = {prod: [var]}
                elif prod not in station_dict2[st]:
                    station_dict2[st][prod] = [var]
                else:
                    station_dict2[st][prod].append(var)

        if output == 'var_plot_texts':

            title_part_ls1 = []
            for stn in station_dict1.keys():
                txt = f'{stn}, '
                prod_var_ls = []
                for prod in station_dict1[stn].keys():
                    p_ls = prod.split(' ')
                    p_short = f'{p_ls[-1]}'
                    p_vars = station_dict1[stn][prod]
                    prod_var_ls.append(f'{p_short}: ' + ', '.join(p_vars))
                title_part_ls1.append(txt + ', '.join(prod_var_ls))

            title_part_ls2 = []
            split_plot_subtitles = []
            for stn in station_dict2.keys():
                txt = f'{stn}, '
                prod_var_ls = []
                for prod in station_dict2[stn].keys():
                    p_ls = prod.split(' ')
                    p_short = f'{p_ls[-1]}'
                    p_vars = station_dict2[stn][prod]
                    prod_var_ls.append(f'{p_short}: ' + ', '.join(p_vars))
                    split_plot_subtitles.extend([f'{p} (from <i>'
                                                   f'{p_short}</i> of '
                                                  f'<i>{stn}</i>)' for p in
                                                   p_vars])
                title_part_ls2.append(txt + ', '.join(prod_var_ls))

            legend_titles = fm_var_ls
            space = '&nbsp;' * 5
            match var_plot_type:

                case 'multi_plot':
                    if title_part_ls1 and title_part_ls2:

                        title_part = f'{space}<sub>Left axis - ' \
                                     f'{"; ".join(title_part_ls1)} </sub><br>' \
                                     f'{space}<sub>Right axis - ' \
                                     f'{"; ".join(title_part_ls2)} </sub><br>'
                    else:
                        title_part = f'{space}<sub>{"; ".join(title_part_ls2)} ' \
                                     f'</sub><br>'
                    subtitle = ''
                    # if plot_axis:
                    #     subtitle = ', '.join(fm_var_ls[: plot_axis])
                    #     subtitle += " || " + ', '.join(fm_var_ls[plot_axis:])
                    # else:
                    #     subtitle = ', '.join(fm_var_ls)
                case 'corr_plot':
                    title_part = f'{space}<sub>{title_part_ls2[0]} on the ' \
                                 f'<i>x</i>-axis, ' \
                                 f'and {title_part_ls2[1]} on the ' \
                                 f'<i>y</i>-axis. </sub><br>' \
                                 f'{space}<sub>Please note that ' \
                                 f'timescale of the measurements is ' \
                                 f'converted to the colorgrade starting from ' \
                                 f'the bottom.</sub>'
                    subtitle = f'{fm_var_ls[0]} vs {fm_var_ls[1]}'
                case 'split_plot':
                    subtitle = split_plot_subtitles
                    title_part = f'{space}<sub>{"; ".join(title_part_ls2)} ' \
                                 f'</sub>'
                case _:
                    subtitle = ''
                    title_part = f'{space}<sub>{"; ".join(title_part_ls2)} ' \
                                 f'</sub>'

            return title_part, subtitle, legend_titles
        else:
            station_dict = station_dict2

        match output:
            case 'station_dict':
                return station_dict
            case 'var_btns':
                separator = ''
            case 'var_cont_upd':
                var_txt = ', '.join(fm_var_ls)
                var_txt += '<hr>'
                var_txt = IcosVarGui.set_css(text=var_txt, css_type='tight')
                separator = '<hr>'
            case 'var_cont_read':
                var_txt = f'<b><i>Variables: </i></b>'
                var_txt += ', '.join(fm_var_ls)
                var_txt += '<hr>'
                var_txt = IcosVarGui.set_css(text=var_txt, css_type='tight')
                separator = '<hr>'
            case _:
                var_txt = ''
                separator = ''

        one_stn = (len(station_dict) == 1)
        stn_ls = stn_name_id_ls
        rows = []
        for stn in station_dict.keys():
            stn_name = [s[0] for s in stn_ls if s[1] == stn].pop()

            one_prod = (len(station_dict[stn].keys()) == 1)
            if debug_fun:
                debug_fun(999, 'var_tuple_ls_converter() --- station, prod ',
                          f'stn_name = {stn_name}',
                          f'one_stn = {one_stn}',
                          f'one_prod = {one_prod}')
            if one_stn and one_prod:
                for prod in station_dict[stn].keys():

                    main_title_txt = f'<i>All variables are from ' \
                                     f'<b>{prod}</b> of the station ' \
                                     f'<b>{stn_name}</b></i>'
                    if output == 'var_btns':
                        rows.append((main_title_txt, []))
                    else:
                        main_title_txt = '<hr>' + main_title_txt
                        rows.append(main_title_txt)
            else:
                if output != 'var_btns':
                    txt = f'<i>Variables from the station <b>{stn_name}</b></i> '
                    main_title_txt = '<hr>' + IcosVarGui.set_css(txt,
                                                                  'tight_header')
                else:
                    main_title_txt = f'<i><b>{stn_name}</b></i> '

                prod_var_ls = []
                for prod in station_dict[stn].keys():
                    p_vars = station_dict[stn][prod]
                    prod_title_txt = f'<b><i>{prod}: </i></b> &nbsp &nbsp'
                    last_var = p_vars.pop()
                    if p_vars:
                        var_row = ', '.join(p_vars)
                        prod_title_txt += f'{var_row} <i>and</i> {last_var}'
                    else:
                        prod_title_txt += f'{last_var}'
                    if output != 'var_btns':
                        prod_title_txt = IcosVarGui.set_css(prod_title_txt,
                                                             'tight')
                    prod_var_ls.append(prod_title_txt)
                if output == 'var_btns':
                    rows.append((main_title_txt, prod_var_ls))
                else:
                    rows.append(main_title_txt + ''.join(prod_var_ls))

        if output == 'var_btns':
            return fm_var_ls, rows
        else:
            title_txt = f'{separator}'.join(rows)
            return var_txt + title_txt

    @staticmethod
    def _get_width_layout(text: str = None):
        min_width = max(40, len(text) * 10)
        max_width = 'auto'
        this_layout = wd.Layout(min_width=f'{min_width}px',
                                max_width=max_width)
        return this_layout

    @staticmethod
    def _html_list(ls: list[str], numeric: bool = None) -> str:
        tag = 'ol' if numeric else 'ul'
        if not ls:
            out = ''
        elif len(ls) == 1:
            out = ls[0]
        else:
            out = f"<{tag}><li>{'</li><li>'.join(ls)}</li></{tag}>"
        return out

    @staticmethod
    def set_css(text: str, css_type: str = None):
        # we use a paragraph in order to set a nice style for the rows
        match css_type:
            case 'tight':
                return f'<p class="tight_line_height">{text}</p>'
            case 'tight_header':
                return f'<p class="tight_header">{text}</p>'
            case 'line':
                return f'<p class="line_height">{text}</p>'
            case _:
                return f'<p class="line_height">{text}</p>'

    def __init__(self, theme: str = None, level: str = None, debug: bool = None):

        valid_themes = ['ES']
        if not theme:
            theme = 'ES'
        elif isinstance(theme, str) and theme.upper() in valid_themes:
            theme = theme.upper()
        else:
            msg = f"The choice: theme = {theme}, is not implemented. " \
                  f"Switching to theme = 'ES'."
            warnings.warn(message=msg, category=UserWarning)
            theme = 'ES'

        valid_levels = ['1']
        if not level:
            level = '1'
        elif not (isinstance(level, str) and level in valid_levels):
            msg = f"The choice: level = {level} is not implemented. " \
                  f"Switching over to: level = '1'."
            warnings.warn(message=msg, category=UserWarning)
            level = '1'

        self.theme = theme
        self.level = level
        self.startup_output = wd.Output()
        display(self.startup_output)
        self.main_widget_container = wd.VBox()
        self.main_output = wd.Output()
        self.startup_html = wd.HTML()
        init_objects = [self.main_widget_container,
                        self.main_output,
                        self.startup_html]
        if bool(debug):
            self.debug = True
            self.debugger = trace_debug.IDebug(output='html',
                                               auto_refresh=False)
            self.debug_out = wd.Output()
            self.debug_html = wd.HTML()
            init_objects.append(self.debug_out)
        else:
            self.debug = False
            self.debugger = None
            self.debug_out = None
            self.debug_value = None
        self.startup_feed(txt='Building up graphical interface...')
        with self.startup_output:
            display(wd.VBox(init_objects))
        self.error_texts = wd.HTML(layout=wd.Layout(width='100%',
                                                    max_width='90%',
                                                    height='auto'))

        # directories for appdata and user outputs
        self.code_dir = os.path.join('.', 'eco_tool')

        output_dir = os.path.join(os.path.expanduser('~'), 'output')
        tool_output_dir = os.path.join(output_dir, 'eco_nrt_tool')
        appdata_dir = os.path.join(tool_output_dir, 'appdata')

        tex_files_dir = os.path.join(tool_output_dir, 'eco_plot_type_tex_files')
        png_files_dir = os.path.join(tool_output_dir, 'eco_plot_type_png_files')
        pdf_files_dir = os.path.join(tool_output_dir, 'eco_plot_type_pdf_files')
        self.output_directories = {'appdata': appdata_dir,
                                   'tex_files': tex_files_dir,
                                   'png_files': png_files_dir,
                                   'pdf_files': pdf_files_dir}
        # app_files
        json_file = f'_unit_map_{theme}_L{level}.json'
        self.app_config_file = os.path.join(appdata_dir, json_file)
        json_file = f'user_group_plot_setup_{theme}_L{level}.json'
        self.user_cache_file = os.path.join(appdata_dir, json_file)
        json_file = f'user_group_plot_setup_{theme}_L{level}_bak.json'
        self.user_cache_bak_file = os.path.join(appdata_dir, json_file)
        json_file = f'tool_settings_{theme}_L{level}.json'
        self.user_config_file = os.path.join(appdata_dir, json_file)
        json_file = f'tool_settings_{theme}_L{level}_bak.json'
        self.user_config_bak_file = os.path.join(appdata_dir, json_file)

        self.startup_feed(txt='Connecting to stored data...')
        self.retriever = _AppDataRetriever(app_config_file=self.app_config_file,
                                           user_cache_file=self.user_cache_file,
                                           user_config_file=self.user_config_file,
                                           debug_function=self.debug_value)
        self.cache = None
        self.icos_info = None
        self.stations_df = None
        self.report_writer = None
        self._reset_gui_data()

        # starts the app
        self.start_tool_app()

    def startup_feed(self, txt: str = None, obj: object = None):

        if self.startup_output:
            if txt:
                previous_value = self.startup_html.value
                if previous_value and previous_value[-4:] == '</p>':
                    new_value = f'{previous_value[:-4]}<br><i>{txt}</i></p>'
                else:
                    new_value = IcosVarGui.set_css(f'<i>{txt}</i>', 'tight')

                self.startup_html.value = new_value
                # with self.startup_output:
                #     previous_value += f'<br>{txt}'
                #     txt = IcosVarGui.set_css(txt, 'tight')
                #     display(wd.HTML(f'<i>{txt}</i>'))
            # elif obj:
            #     with self.startup_output:
            #         display(obj)
            else:
                with self.startup_output:
                    clear_output()
                self.startup_output = None
                self.startup_html = None

    def debug_value(self, *text_list):
        caller_id = None
        if text_list:
            if isinstance(text_list[0], int):
                caller_id, *text_list = text_list
        msg = self.debugger.debug_value(*text_list,
                                        timer_id=caller_id)
        if msg:
            self.debug_html.value = msg
            with self.debug_out:
                display(wd.HTML(msg))

    def _plot_setup_validation(self, grp, jobs: list, mode: str):
        def html_error_txt(er_dict: dict):
            if self.debug:
                plot_type2name_dict = {'split_plot': 'Split-plot',
                                       'multi_plot': 'Multi-plot',
                                       'corr_plot': 'Correlation plot (2 vars)',
                                       'corr_table': 'Correlation table',
                                       'statistics': 'Numerical Statistics'}
            else:
                plot_type2name_dict = {'split_plot': 'Split-plot',
                                       'multi_plot': 'Multi-plot',
                                       'corr_plot': 'Correlation plot'}

            er_plot_setups = sorted(list(er_dict.keys()),
                                    key=(lambda x: x.lower()))
            plot_setups = [f'<b><i>{ps}</i></b>' for ps in er_plot_setups]
            good_plot_setups = [ps for ps in jobs if ps not in er_plot_setups]
            good_bats = [f'<b><i>{ps}</i></b>' for ps in good_plot_setups]

            error_msg = f'<h4><b>Validation error:</b></h4> The group <b><i' \
                        f'>"{grp}"</i></b> and it\'s plot setups do not ' \
                        f'match.<br>'
            txt = IcosVarGui.set_css(text=error_msg,
                                     css_type='line')
            if mode == 'run':
                if len(jobs) == len(plot_setups):
                    error_msg = f'Can not generate output. '
                elif len(plot_setups) > 1:
                    error_msg = f'Skipping plot setups: ' \
                                f'{", ".join(plot_setups)}. ' \
                                f'Proceeding with plot setups: ' \
                                f'{", ".join(good_bats)}. '
                else:
                    error_msg = f'Skipping plot setup: {plot_setups[0]}.'
                error_msg += 'See the <b>suggestion</b> below on how to fix this.'
                txt += IcosVarGui.set_css(text=error_msg,
                                          css_type='line')
            elif mode == 'save_group':
                error_msg = f'The plot setup(s): {", ".join(plot_setups)}, ' \
                            f'will not run. To fix this, please consider the ' \
                            f'suggestion below. '
                txt += IcosVarGui.set_css(text=error_msg,
                                          css_type='line')
            if self.debug:
                self.debug_value(-151, '_plot_setup_validation() '
                                       'html_error_txt()',
                                 f'er_dict = {er_dict}')
            for bat, plot_type_rows in er_dict.items():
                error_msg = f'<br>Missmatch in plot setup <b><i>' \
                            f'"{bat}"</i></b>:<br>'
                txt += IcosVarGui.set_css(text=error_msg,
                                          css_type='line')
                for row in plot_type_rows:
                    for index, plot_type_dict in row.items():
                        plot_type_txt_ls = []
                        for plot_type, var_ls in plot_type_dict.items():
                            plot_type_txt = f'Tool number {int(index) + 1}, ' \
                                            f'a <b><i>' \
                                            f'{plot_type2name_dict[plot_type]}' \
                                            f'</i></b> ' \
                                            f'with contain the variable(s): '
                            var_texts = []
                            for var in var_ls:
                                var_texts.append(f'<b><i>{var[0]}</i></b> '
                                                 f'from <b>{var[1]}</b> of '
                                                 f'station the <b>{var[2]}</b>')
                            plot_type_txt += f'<ul><li>' \
                                             f'{"</li><li>".join(var_texts)}' \
                                             f'</li></ul>'
                            plot_type_txt = IcosVarGui.set_css(text=
                                                                 plot_type_txt,
                                                               css_type='line')
                            plot_type_txt_ls.append(plot_type_txt)
                        txt += f'<ul><li>{"</li><li>".join(plot_type_txt_ls)}' \
                               f'</li></ul>'
            error_msg = '<br><i>Probably the above variable(s) has been ' \
                        'removed from the group, but not from the plot ' \
                        'setups of the group</i><br>'
            txt += IcosVarGui.set_css(text=error_msg,
                                      css_type='line')
            error_msg = '<b><i>Suggestion</i></b>, either:' \
                        '<ol><li> ' \
                        '<ul>' \
                        '<li>Go to the <b><i>Group</i></b>-menu</li>' \
                        f'<li>Select group <b><i>{grp}</i></b> and ' \
                        f'choose <i>Update</i>.</li>' \
                        '<li>Add the missing variable(s) and ' \
                        'press <i>Save</i>.</li>' \
                        '</ul></li>' \
                        '<li><ul>' \
                        '<li>Go to the <b><i>Plot setups</i></b>-menu</li>' \
                        f'<li>Select each of the falsy plot setups: ' \
                        f'<b><i>{", ".join(plot_setups)}</i></b> and ' \
                        f'choose <i>Update</i></li>' \
                        '<li>When <i>Save</i> is chosen old group ' \
                        'variables will be removed.</li>' \
                        '</ul></li></ol><br>'
            txt += IcosVarGui.set_css(text=error_msg,
                                      css_type='line')
            return txt, good_plot_setups

        cache = self._load_cache()
        error_dict = {}
        if '_var_mismatch' in cache['_groups'][grp]:
            for ps, v in cache["_groups"][grp]["_var_mismatch"].items():
                if ps in jobs:
                    if ps not in error_dict:
                        error_dict[ps] = [v]
                    else:
                        error_dict[ps].append(v)

        return '' if not error_dict else html_error_txt(error_dict)

    def _clear_debug_list(self, c):
        with self.debug_out:
            clear_output()

    def _remove_debug_data(self, c):
        self.debugger.reset_trace()

    def _auto_refresh_debug_list(self, c):
        self.debugger.auto_refresh = not self.debugger.auto_refresh

    def _refresh_debug_list(self, c):
        msg = self.debugger.fetch_traces()
        if msg:
            self.debug_html.value = msg
            with self.debug_out:
                display(wd.HTML(msg))

    def _reset_gui_data(self):
        # reset non-persistent data
        self._load_cache(refresh=True)

        self.icos_info = icos_data.StationData(theme=self.theme,
                                               level=self.level)
        self.stations_df = self.icos_info.stations_df
        self.report_writer = None

    def _get_report_writer(self):

        rw = self.report_writer
        if rw is None:
            rw = report_writer.ReportWriter(retriever=self.retriever,
                                            icos_info=self.icos_info,
                                            debug_function=self.debug_value)
            self.report_writer = rw

        today = dt.datetime.today().strftime('YYYY-MM-DD')
        if rw.timestamp != today:
            self._reset_gui_data()
            self._get_report_writer()

        return self.report_writer

    def _station_name_id_ls(self) -> list:
        st_df = self.stations_df
        id_ls = list(st_df.id)
        name_ls = list(st_df.name)
        name_id_ls = list(set(zip(name_ls, id_ls)))
        name_id_ls.sort(key=lambda v: v[0].lower())
        return name_id_ls

    def _validate_plot_setup_of_grp(self, cache_dict: dict = None) -> dict:
        # expects a dict like cache['_groups'][grp] see the 'save_group'
        # when variables are removed from a group and the group has
        # plot_setups we might get crashes if the removed variables
        # belongs to some plot.
        g_vars = cache_dict.get('_group_vars', [])

        d = cache_dict.get('_plot_setups', {})
        er_dict = {}
        for ps_name in d.keys():
            for index, k in d[ps_name].items():
                if not isinstance(k, dict):
                    continue
                for p_type, v_ls in k.items():
                    if p_type in ['split_plot', 'corr_plot', 'corr_table',
                                  'statistics']:
                        if isinstance(v_ls, list) and not all(v in
                                                              g_vars for
                                                              v in v_ls):
                            if ps_name not in er_dict.keys():
                                er_dict[ps_name] = {}
                            if index not in er_dict[ps_name].keys():
                                er_dict[ps_name][index] = {}
                            er_dict[ps_name][index][p_type] = [x for x in v_ls if
                                                             x not in g_vars]
                    else:
                        # p_type multi-plot
                        for x in v_ls:
                            if not all(v in g_vars for v in x[1]):
                                if ps_name not in er_dict.keys():
                                    er_dict[ps_name] = {}
                                if index not in er_dict[ps_name].keys():
                                    er_dict[ps_name][index] = {}
                                if p_type in er_dict[ps_name][index].keys():
                                    er_dict[ps_name][index][p_type].extend(
                                        [y for y in x[1] if y not in g_vars])
                                else:
                                    er_dict[ps_name][index][p_type] = [y for y in
                                                                       x[1] if y
                                                                       not in
                                                                       g_vars]
        return er_dict

    def set_persistent_error(self, error_ls):

        if error_ls:
            margin = '&nbsp' * 3
            error_color = self.widget_style_colors['danger:active']

            span_start = f'<span style="color:{error_color}">'
            span_end = '</span>'

            if not self.error_texts.value:
                warning_emoji = '\u26a0\ufe0f'
                err_msg = f'{span_start}<h3>' \
                          f'List of data errors:{margin}{margin}' \
                          f'{warning_emoji}</h3>' \
                          f'{span_end}'
            else:
                err_msg = '<hr>'

            err_msg += f'<hr>{span_start}'
            if error_ls[0] == 'ACTION':
                err_msg += f'<h4>{margin}' \
                           f'{error_ls[1]}' \
                           f'</h4>'
                error_ls = error_ls[2:]
            else:
                err_msg += f'<h4>{margin}' \
                           f'{error_ls[0]}</h4>'
                error_ls = error_ls[1:]
            for error in error_ls:
                error = f'<b>{margin}{error}</b>'
                err_msg += IcosVarGui.set_css(error, 'tight')
            err_msg += f'{span_end}'
            self.error_texts.value += err_msg

    def start_tool_app(self):

        self.startup_feed(txt='Setting up main menu...')

        def display_errors(c):
            if self.debug:
                self.debug_value(200, 'display_errors()   ',
                                 f'c = {c}',
                                 f'error_container.get_title(0) = '
                                 f'{error_container.get_title(0)}')

            title = error_container.get_title(0)
            title_ls = title.split(' ')
            number_of_err = title_ls[-1]
            if number_of_err:
                title_ls[-1] = str((1 + int(number_of_err)))
            else:
                title_ls[-1] = '1'
            title = ' '.join(title_ls)
            error_container.set_title(0, title=title)

            if error_container.layout.display == 'none':
                error_container.layout.display = 'block'
                error_container.selected_index = 0

        def main_change(change):
            choice = change['new']
            with out:
                clear_output()
                if choice == 'Visualise ':
                    self._menu_visualise()
                elif choice == 'Group menu ':
                    self._menu_group()
                elif choice == 'Plot setups ':
                    self._menu_plot_setups()
                elif choice == 'Settings ':
                    self._menu_settings()
                elif choice == 'Help ':
                    self._menu_help()
                else:
                    self._menu_extract_data()

        option_ls = ['Visualise ', 'Group menu ', 'Plot setups ', 'Settings ',
                     'Help ', '*Extract data ']
        icon_ls = ['area-chart', 'list', 'table', 'cog', 'info-circle', 'wrench']

        main_widgets = []
        main_menu = wd.ToggleButtons(options=option_ls,
                                     button_style="success",
                                     style={'button_width': "100px"},
                                     tooltip=None,
                                     icons=icon_ls)
        error_container = wd.Accordion(children=[wd.VBox([self.error_texts])],
                                       selected_index=None,
                                       layout=wd.Layout(width='auto',
                                                        height='auto',
                                                        display='none'))
        error_container.set_title(0, 'Errors -- Number of errors: ')
        if self.debug:
            self.error_texts.observe(display_errors, names='value')

        main_widgets.append(wd.VBox([main_menu, error_container]))
        # we use a css paragraph in order to set a nice style for the rows
        p_css = wd.HTML(value='<head>'
                              '    <style>'
                              '        p.line_height {'
                              '            line-height: 1.3; '
                              '            margin-left: 10px} '
                              '        p.tight_header {'
                              '            line-height: 1.5; '
                              '            margin-left: 20px} '
                              '        p.tight_line_height {'
                              '            line-height: 1.15; '
                              '            margin-left: 30px} '
                              '    </style>'

                              '</head>')
        main_widgets.append(p_css)

        group_cache = self._load_cache()
        if group_cache['_groups'].keys():
            start_value = 'Visualise '
            self.startup_feed(txt='Generating visualisation...')
        else:
            # In the first run, there is no
            # group of variables.
            self.startup_feed(txt='No data to visualise, entering new '
                                  'group of variables...')
            start_value = 'Group menu '
        main_menu.value = start_value

        out = wd.Output()
        main_widgets.append(out)

        if self.debug:
            show_debug_cb = wd.Checkbox(description='Show debug widgets',
                                        value=False)
            show_plots_cb = wd.Checkbox(description='Show plots',
                                        value=True)
            auto_refresh_cb = wd.Checkbox(description='Auto refresh',
                                          value=self.debugger.auto_refresh)
            refresh_btn = wd.Button(description='Refresh')
            clear_debug_btn = wd.Button(description='Clear debug list')
            remove_debug_data_btn = wd.Button(description='Remove debug data')

            refresh_btn.on_click(self._refresh_debug_list)
            clear_debug_btn.on_click(self._clear_debug_list)
            remove_debug_data_btn.on_click(self._remove_debug_data)

            auto_refresh_cb.observe(self._auto_refresh_debug_list,
                                    names='value')
            main_widgets.append(wd.VBox([wd.HBox([show_debug_cb,
                                                  show_plots_cb,
                                                  auto_refresh_cb,
                                                  refresh_btn, clear_debug_btn,
                                                  remove_debug_data_btn]),
                                         self.debug_out]))

            def __show_debug(c):
                for y in [self.debug_out, show_plots_cb,
                          auto_refresh_cb, refresh_btn,
                          clear_debug_btn, remove_debug_data_btn]:
                    if isinstance(c, dict):
                        if c['new']:
                            y.layout.display = 'block'
                        else:
                            y.layout.display = 'none'
                    else:
                        y.layout.display = 'none'

            def __show_plots(c):
                if c['new']:
                    self.main_output.layout.display = 'block'
                else:
                    self.main_output.layout.display = 'none'

            show_debug_cb.observe(__show_debug,
                                  names='value')
            show_plots_cb.observe(__show_plots,
                                  names='value')
            __show_debug('init')

        main_widgets.append(self.main_output)
        main_menu.observe(main_change, "value")
        with out:
            if start_value == 'Visualise ':
                self._menu_visualise()
            else:
                self._menu_group()

        self.startup_feed(txt=None)
        display(wd.VBox(main_widgets))

    def get_data(self, grp: str = None) -> IcosFrame or None:
        reports = self._get_data_dict
        if reports:
            if grp and grp in reports.keys():
                icos_df = reports[grp]['df']
            elif grp:
                icos_df = None
            else:
                grp = list(reports.keys())[-1]
                icos_df = reports[grp]['df']
        else:
            icos_df = None
        return icos_df

    @property
    def _get_data_dict(self) -> dict:

        if self.report_writer is None:
            d = {}
        else:
            d = self.report_writer.stored_timeseries
        return d

    def _menu_visualise(self):

        if self.debug:
            self.debug_value(-33, '_menu_visualise()    *** Start ***')

        def set_info_msg(reason: str):
            color = self.widget_style_colors['info:active']
            msg = f'<span style="color:{color}">'
            msg_ls = ['<h3><i>To do:</i></h3>']
            if reason == 'no_group':
                msg_ls.append('<br>'
                              '<ol><li>'
                              'First create a <i>group of variables</i> '
                              'using the <b><i>Group menu</i></b>. <br>'
                              '<i>In other words:</i> specify <b><i>what '
                              'data</i></b> to analyse. '
                              '</li><li>'
                              'Next, create some <i>plot setup</i> using the menu'
                              '<b><i>Plot setups/i></b>. <br> '
                              '<i>In other words</i>: specify <b><i>how</i></b> '
                              'to analyse the data. '
                              '</li></ol>')
            else:
                # reason == 'no_plot_setup':
                msg_ls.append('<br>'
                              '<i>The group of variables '
                              f'<b>{group_drop.value}</b> '
                              'has no <b>plot setup</b></i>. Use the menu '
                              '<b><i>Plot setups</i></b> in order '
                              'to create a plot setup, in order to specify '
                              '<b><i>how</i></b> to analyse the data. ')

            for txt in msg_ls:
                msg += self.set_css(text=txt, css_type='line')
            msg += '</span>'

            with self.main_output:
                clear_output()
                display(wd.HTML(msg))

        def set_gui():
            cache = self._load_cache()
            # set group drop
            if not cache['_groups'].keys():
                set_info_msg('no_group')
                return False

            group_ls = list(cache['_groups'].keys())
            group_drop.options = sorted(group_ls, key=(lambda x: x.lower()))
            group_drop.observe(init_plot_setups,
                               names='value')
            if cache['_last_group']:
                group_drop.value = cache['_last_group']
            else:
                group_drop.value = group_drop.options[0]
            group_drop.disabled = False
            error_widget.layout.display = 'none'

            user_settings = self._load_user_settings()
            if 'run_configs' in user_settings.keys():
                end_shift = - user_settings['run_configs'].get('end_date', 0)
                start_shift = - user_settings['run_configs'].get('start_date', 8)
            else:
                end_shift = 0
                start_shift = -8
            end_date.value = dt.date.today() + dt.timedelta(days=end_shift)
            start_date.value = end_date.value + dt.timedelta(days=start_shift)

            return True

        def init_plot_setups(c):
            error_txt_widget.value = ''
            error_widget.layout.display = 'none'

            cache = self._load_cache()
            grp = group_drop.value
            if grp in cache['_groups'].keys() and \
                    '_plot_setups' in cache['_groups'][grp].keys():
                p_setups = cache['_groups'][grp].get('_plot_setups', {})
                if p_setups:
                    b_ls = [wd.Button(description=name,
                                      style=dict(button_color='LightSeaGreen'),
                                      layout=IcosVarGui._get_width_layout(name))
                            for name in p_setups.keys()]
                    if b_ls:
                        all_title = 'Run all'
                        all_layout = IcosVarGui._get_width_layout(all_title)
                        b_ls.append(wd.Button(description=all_title,
                                              icon='area-chart',
                                              button_style='success',
                                              layout=all_layout))
                    for bt in b_ls:
                        bt.on_click(plot_setup_click)
                    plot_setups.children = b_ls
                else:
                    set_info_msg('no_plot_setup')
                    plot_setups.children = []
            else:
                set_info_msg('no_plot_setup')
                plot_setups.children = []

        def date_changed(change):
            if change['owner'].description == 'End date':
                if change['new'] <= start_date.value:
                    end_date.value = change['old']
            elif change['owner'].description == 'Start date':
                if change['new'] >= end_date.value:
                    start_date.value = change['old']

        def plot_setup_click(c):
            run_plot_setup(jobs=c.description)

        def run_plot_setup(jobs):

            grp = group_drop.value
            if jobs == 'Run all':
                cache = self._load_cache()
                plot_setup_ls = list(cache['_groups'][grp]['_plot_setups'].keys())
            else:
                plot_setup_ls = [jobs]

            if self.debug:
                import time
                t1 = time.time()
                self.debug_value(-38, 'run_plot_setup() ',
                                 f'jobs = {jobs}',
                                 f'group = {grp}')

            validation_error = self._plot_setup_validation(grp=grp,
                                                           jobs=plot_setup_ls,
                                                           mode='run')

            with self.main_output:
                clear_output()
                if jobs == 'Run all':
                    temp_title = f'<i>Generating report to all plot setups ' \
                                 f'of variable group ' \
                                 f'<b>{group_drop.value}</b>...</i>'
                else:
                    temp_title = f'<i>Generating report of plot setup ' \
                                 f'<b>{jobs}</b> of variable group ' \
                                 f'<b>{group_drop.value}</b>...</i>'
                if validation_error:
                    error_txt_widget.value = validation_error[0]
                    error_widget.layout.display = 'block'
                    temp_title += f'<hr>{validation_error[0]}<hr>'
                    good_plot_setups = validation_error[1]
                    if good_plot_setups:
                        plot_setup_ls = good_plot_setups
                    else:
                        self.startup_feed(txt=temp_title)
                        display(wd.HTML(temp_title))
                        return
                if self.startup_output:
                    self.startup_feed(txt=temp_title)
                else:
                    display(wd.HTML(temp_title))

            rw = self._get_report_writer()
            self.startup_feed(txt='...')
            if self.debug:
                t2 = time.time()
                self.debug_value(-38, 'run_plot_setup() ',
                                 f'time = {t2 - t1}')
            report_dict = rw.get_plot_setup_report(group=group_drop.value,
                                                   plot_setup_ls=plot_setup_ls,
                                                   start_date=start_date.value,
                                                   end_date=end_date.value)
            if self.debug:
                t3 = time.time()
                self.debug_value(-38, 'run_plot_setup() ',
                                 f'rw time = {t3 - t2}')
            self.startup_feed(txt='......')
            with self.main_output:
                clear_output()
                display(report_dict['header'])
                for ps in plot_setup_ls:
                    outputs = report_dict[ps]
                    self.startup_feed(txt=f'Assembling plot setup {ps} ('
                                          f'{len(outputs)} outputs)...')
                    ii = 1
                    for plot_output in outputs:
                        if plot_output[0] in ['split_plot', 'multi_plot',
                                                   'corr_plot', 'corr_table']:
                            try:
                                self.startup_feed(txt=f'Building plot #{ii}...')
                                ii += 1
                                plot_output[1].show()
                            except Exception as e:
                                if self.debug:
                                    self.debug_value(-38, 'run_plot_setup()  -- '
                                                          'exception',
                                                     f'---Exception: {e}',
                                                     f'Errors run_plot_setup: ',
                                                     f'--- plot_output[0] = '
                                                     f'{plot_output[0]}',
                                                     f'--- plot_output[1] = '
                                                     f'{plot_output[1]}')
                        else:
                            if self.debug:
                                self.debug_value(-38, 'run_plot_setup() ',
                                                 f'Not implemented: '
                                                 f'{plot_output[0]} ')
            if self.debug:
                t4 = time.time()
                self.debug_value(-38, 'run_plot_setup() ',
                                 f'plot time = {t4 - t3}',
                                 f'total time = {t4 - t1}')

        # Main of configurations
        # ======================
        # Layouts
        common_layout = wd.Layout(width='165pt', height='40px')

        # Dropdowns
        group_label = wd.HTML('<b><i>Available groups: </i></b>',
                              layout=wd.Layout(width='auto'))
        group_drop = wd.Dropdown(layout=wd.Layout(width='auto',
                                                  height='40px'),
                                 description_tooltip='Group name')
        group_box = wd.HBox([group_label, group_drop])

        start_date = wd.DatePicker(description='Start date',
                                   layout=common_layout)

        end_date = wd.DatePicker(description='End date',
                                 layout=common_layout)

        rows = [wd.HBox([group_box, start_date, end_date])]
        plot_setups = wd.HBox()
        rows.append(plot_setups)
        error_txt_widget = wd.HTML(layout=wd.Layout(width='auto',
                                                    max_width='90%',
                                                    height='100%'),
                                   value='Variables: ',
                                   disabled=True)
        error_widget = wd.Accordion([error_txt_widget],
                                    titles=('Errors', '0'),
                                    selected_index=None,
                                    layout=wd.Layout(width='50%',
                                                     height='100%'))
        rows.append(error_widget)
        if set_gui():
            # observe changes
            start_date.observe(date_changed, "value")
            end_date.observe(date_changed, "value")

            display(wd.VBox(rows))

            # By default we run all plot setups of latest group.
            # this can be changed in configurations
            settings = self._load_user_settings()
            if 'run_configs' in settings.keys():
                auto_run = settings['run_configs'].get('auto_run', True)
            else:
                auto_run = True

            if self.debug:
                pass
            elif auto_run:
                if plot_setups.children:
                    run_plot_setup('Run all')

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
            self.debug_value(-40, '_set_app_configs **** _set_app_configs *** ',
                             f'exception: {e} ')

        self.retriever.app_config_dict = app_dict

    def _set_cache(self,
                   cache_dict: dict = None):
        json_handler.write(data=cache_dict,
                           path_to_json_file=self.user_cache_file)
        # self.report_writer = None
        self.retriever.cache = cache_dict

    def _menu_help(self):
        # static help text
        def link(url, url_txt) -> str:
            return f'<a href="{url}" target="_blank">' \
                   f'<font color="DarkBlue">{url_txt}</font></a>'

        images_dir = os.path.join(self.code_dir, 'images')
        visualise_png = os.path.join(images_dir, 'visualise.png')
        group_menu_png = os.path.join(images_dir, 'group_menu.png')
        plot_setup_png = os.path.join(images_dir, 'plot_setups.png')
        settings_menu_png = os.path.join(images_dir, 'settings_menu.png')
        extract_menu_png = os.path.join(images_dir, 'extract_menu.png')
        with open(visualise_png, 'rb') as f:
            visualise_img = wd.Image(value=f.read())
            visualise_img.layout.height = '28px'

        with open(group_menu_png, 'rb') as f:
            group_img = wd.Image(value=f.read())
            group_img.layout.height = '28px'

        with open(plot_setup_png, 'rb') as f:
            plot_setup_img = wd.Image(value=f.read())
            plot_setup_img.layout.height = '28px'

        with open(settings_menu_png, 'rb') as f:
            settings_img = wd.Image(value=f.read())
            settings_img.layout.height = '28px'

        with open(extract_menu_png, 'rb') as f:
            extract_img = wd.Image(value=f.read())
            extract_img.layout.height = '28px'

        wide_layout = wd.Layout(width='auto', height='auto', max_width='80%')
        column_layout = wd.Layout(width='auto', height='auto', max_width='60%')
        half_col_layout = wd.Layout(width='auto', height='auto', max_width='40%')
        three_col_layout = wd.Layout(width='auto', height='auto', max_width='33%')

        top_html = wd.HTML(disabled=True, layout=wide_layout)

        visualise_html = wd.HTML(disabled=True, layout=column_layout)

        group_html1 = wd.HTML(disabled=True, layout=column_layout)
        group_html2 = wd.HTML(disabled=True, layout=column_layout)
        grp_defn_html = wd.HTML(disabled=True, layout=column_layout)

        plot_setup_html1 = wd.HTML(disabled=True, layout=column_layout)
        plot_setup_html2 = wd.HTML(disabled=True, layout=column_layout)
        bat_defn_html = wd.HTML(disabled=True, layout=column_layout)

        settings_html = wd.HTML(disabled=True, layout=column_layout)

        extract_html = wd.HTML(disabled=True, layout=column_layout)

        new_grp_html = wd.HTML(disabled=True, layout=three_col_layout)
        upd_grp_html = wd.HTML(disabled=True, layout=three_col_layout)
        del_grp_html = wd.HTML(disabled=True, layout=three_col_layout)

        general_html = wd.HTML(disabled=True, layout=half_col_layout)
        technical_html = wd.HTML(disabled=True, layout=half_col_layout)

        end_html = wd.HTML(disabled=True, layout=wide_layout)

        margin_str = '&nbsp' * 6
        margin = wd.HTML(value=margin_str)

        link_product_fluxes = link('https://data.icos-cp.eu/objects/'
                                   '_Vb_c34v0nfTA_fG0kiIAmXM',
                                   'NRT ETC Fluxes')
        link_product_meteo = link('https://data.icos-cp.eu/objects/'
                                  'AOceWQsLL6wjS2fKUylSKsrY',
                                  'NRT ETC Meteo')
        link_product_meteosens = link('https://data.icos-cp.eu/objects/'
                                      'H51Y34JoWmUffyKoNIpDVg2I',
                                      'NRT ETC MeteoSens')
        link_etc_stations = link('https://www.icos-cp.eu/observations/'
                                 'ecosystem/stations', 'ICOS ETC Station')
        link_cp = link("https://data.icos-cp.eu/portal/", "ICOS Carbon Portal")
        mail_cp = link("mailto:info@icos-cp.eu", "info@icos-cp.eu")
        mail_ad = link("mailto:anders.dahlner@nateko.lu.se",
                       "anders.dahlner@nateko.lu.se")

        widgets = wd.VBox([top_html,
                           wd.HBox([visualise_img,
                                    visualise_html], layout=wide_layout),
                           wd.HBox([group_img,
                                    wd.VBox([group_html1,
                                             wd.HBox([margin,
                                                      grp_defn_html]),
                                             group_html2])
                                    ], layout=wide_layout),
                           wd.HBox([plot_setup_img,
                                    wd.VBox([plot_setup_html1,
                                             wd.HBox([margin,
                                                      bat_defn_html]),
                                             plot_setup_html2])
                                    ], layout=wide_layout),
                           wd.HBox([settings_img,
                                    settings_html],
                                   layout=wide_layout),
                           wd.HBox([extract_img,
                                    extract_html],
                                   layout=wide_layout),
                           wd.HBox([new_grp_html,
                                    upd_grp_html,
                                    del_grp_html],
                                   layout=wide_layout),
                           wd.HBox([general_html,
                                    technical_html],
                                   layout=wide_layout),
                           end_html])

        top_text = 'This application is aimed to assist principal ' \
                   'investigators of ICOS Ecosystem stations in the quality ' \
                   'control and analyse NRT data. <br><br>'
        top_html.value = IcosVarGui.set_css(text=top_text,
                                            css_type='line')

        visualise_text = 'The <b><i>Visualise</i></b>-menu is the standard ' \
                         'view of the application. This is were the user run ' \
                         'reports in order to produce plots and statistics ' \
                         'from the ICOS data.<br><br>'
        visualise_html.value = IcosVarGui.set_css(text=visualise_text,
                                                  css_type='line')

        group_text1 = 'In the <b><i>Group</i></b>-menu the user can create ' \
                      '<i>groups of variables</i>.<br>'
        group_html1.value = IcosVarGui.set_css(text=group_text1,
                                               css_type='line')

        grp_defn_text = '<i><b>Definition:</b> A <b>group of variables</b> ' \
                        'is a non-empty list of variables where each ' \
                        'variable is an ingested variable<sup>1</sup> from ' \
                        'one of the ' \
                        f'products <b>{link_product_fluxes}</b>, ' \
                        f'<b>{link_product_meteo}</b>, ' \
                        f'or <b>{link_product_meteosens}</b>, of some ' \
                        f'<b>{link_etc_stations}</b>.</i><br>'
        grp_defn_html.value = IcosVarGui.set_css(text=grp_defn_text,
                                                 css_type='line')
        group_text2 = 'In particular a group of variables may ' \
                      'contain variables from different station and ' \
                      'files.<br>' \
                      '<b><i>How to set up or edit a group ' \
                      'of variables</i></b> are described below. Moreover, ' \
                      'when the user is in <i>update mode</i>, more ' \
                      'detailed information is found in the ' \
                      '<b><i>User guide</i></b> of the <b><i>Group</i></b>-menu.' \
                      '<br>' \
                      f'<u>{margin_str}{margin_str}{margin_str}</u><br>' \
                      '<sup>1</sup> <i>That a variable is ingested means ' \
                      'that it is previewable at the ' \
                      f'{link_cp}.<br><br>'
        group_html2.value = IcosVarGui.set_css(text=group_text2,
                                               css_type='line')
        plot_setup_text1 = 'In the <b><i>Plot setups</i></b>-menu the user ' \
                           'create <i>plot setups</i>. <br>'
        plot_setup_html1.value = IcosVarGui.set_css(text=plot_setup_text1,
                                                    css_type='line')

        plot_setup_defn_text = '<i><b>Definition:</b> A <b>plot setup</b> ' \
                               'for a group of variables, is a list of ' \
                               '<i>plot types</i> where each plot type ' \
                               'consist of a selection of group ' \
                               'variables.<br>' \
                               'By a <b>plot type</b> we mean a ' \
                               'visualisation plot or a some statistical ' \
                               'tool, together with some variables ' \
                               'from the group of variables in order to ' \
                               'create an output.'
        bat_defn_html.value = IcosVarGui.set_css(text=plot_setup_defn_text,
                                                 css_type='line')

        plot_setup_text2 = '<i>How</i> to set up a plot setup is explained ' \
                           'in the <b><i>User guide</i></b> of the ' \
                           '<b><i>Plot setups</i></b>-menu.'
        plot_setup_html2.value = IcosVarGui.set_css(text=plot_setup_text2,
                                                    css_type='line')

        config_text = 'In the <b><i>Settings</i></b>-menu the user ' \
                      'can:<br> ' \
                      f'{margin_str} - change the <i>Default settings</i> ' \
                      'on what data to fetch and manipulate ' \
                      'layouts of plots.<br>' \
                      f'{margin_str} - use the <i>Plot setups</i> to set ' \
                      'up sequences of outputs, i.e. plots of statistics, ' \
                      'to produce. Here variables for the outputs are ' \
                      'selected from a group of variables.<br><br>'
        settings_html.value = IcosVarGui.set_css(text=config_text,
                                                 css_type='line')

        extract_text = 'The menu <b><i>Extract data</i></b> is a guidance ' \
                       'on how to extract data from the notebook in case a user ' \
                       'wish to look more into details of a dataset or run ' \
                       'tests not available in this application.<br><br>'
        extract_html.value = IcosVarGui.set_css(text=extract_text,
                                                css_type='line')

        new_grp_text = self.help_dict['group']['read_header1']
        new_grp_text += self.help_dict['group']['read_body1'] + '<br>'
        new_grp_html.value = IcosVarGui.set_css(text=new_grp_text,
                                                css_type='line')

        upd_grp_text = self.help_dict['group']['read_header2']
        upd_grp_text += self.help_dict['group']['read_body2'] + '<br>'
        upd_grp_html.value = IcosVarGui.set_css(text=upd_grp_text,
                                                css_type='line')

        del_grp_text = self.help_dict['group']['read_header3']
        del_grp_text += self.help_dict['group']['read_body3'] + '<br>'
        del_grp_html.value = IcosVarGui.set_css(text=del_grp_text,
                                                css_type='line')

        general_text = self.help_dict['group']['general'] + '<br>'
        general_html.value = IcosVarGui.set_css(text=general_text,
                                                css_type='line')

        technical_text = self.help_dict['technical'] + '<br>'
        technical_html.value = IcosVarGui.set_css(text=technical_text,
                                                  css_type='line')

        end_text = f'<br><hr><br>' \
                   f'<b><i>Contact</i></b> For comments, questions, ' \
                   f'suggestions, bug reports ' \
                   f'or any other kind of feedback, please feel free to ' \
                   f'contact: {mail_cp} or {mail_ad}.'
        end_html.value = IcosVarGui.set_css(text=end_text,
                                            css_type='line')

        display(widgets)

    def _menu_extract_data(self):

        def link(url, url_txt) -> str:
            return f'<a href="{url}" target="_blank">' \
                   f'<font color="DarkBlue">{url_txt}</font></a>'

        # we use a paragraph in order to set a nice style for the rows
        wide_layout = wd.Layout(width='auto', height='auto', max_width='80%')

        top_html = wd.HTML(disabled=True,
                           layout=wide_layout)
        example_html = wd.HTML(disabled=True,
                               layout=wide_layout)
        end_html = wd.HTML(disabled=True,
                           layout=wide_layout)

        link_cp = link("https://data.icos-cp.eu/portal/", "ICOS Carbon Portal")
        mail_cp = link("mailto:info@icos-cp.eu", "info@icos-cp.eu")
        mail_ad = link("mailto:anders.dahlner@nateko.lu.se",
                       "anders.dahlner@nateko.lu.se")

        widgets = wd.VBox([top_html,
                           example_html,
                           end_html])

        top_text = 'Besides from running reports as described in *<i>direction ' \
                   'to text to come</i>*, the user can also use this notebook ' \
                   'in order to extract data from the ICOS Carbon Portal. <br><br>'
        top_html.value = IcosVarGui.set_css(text=top_text,
                                            css_type='line')
        ex_txt1 = '<b><i>Example.</i></b><br> Suppose a user has created a ' \
                  'group of variables called ' \
                  '<i>fluxes</i> and a plot setup called <i>my plots</i> for ' \
                  'some variables of the group (the names themself are ' \
                  'insignificant, but we refer to them ' \
                  'below).<br><br>' \
                  '<b><i>Step 1. Run.</i></b><br>' \
                  'The user execute the code: <br>'
        out_txt = IcosVarGui.set_css(text=ex_txt1,
                                     css_type='tight')

        out_txt += '''<pre><code>
        import warnings
        warnings.simplefilter('ignore', FutureWarning)
        from eco_tool import gui
        g = gui.IcosVarGui(theme='ES');</code></pre>'''

        ex_txt2 = '<br><b><i>Step 2. Gathering data.</i></b><br> ' \
                  'The user select the group <i>fluxes</i> and hits the ' \
                  'button <i>my plots</i>.<br>' \
                  'This will display whatever output is related to the plot ' \
                  'setup <i>my plots</i>, between the ' \
                  '<b><i>Start date</i></b> and <b><i>End date</i></b>.<br> ' \
                  '<i><u>However</u>, in the background <b>all</b> ' \
                  'variables of the ' \
                  'group <b>fluxes</b> are gathered (actually they are ' \
                  'gathered between the <b>"Fetch date"</b> and ' \
                  '<b>End date</b>, the Fetch date is explained in ' \
                  'the <b>Run configurations</b> under the ' \
                  '<b>Settings</b>-menu).</i><br><br>'
        out_txt += IcosVarGui.set_css(text=ex_txt2,
                                      css_type='tight')

        ex_txt3 = '<b><i>Step 3. Extracting data. </i></b><br>The user opens a ' \
                  'new cell of the notebook and run the code: <br>'
        out_txt += IcosVarGui.set_css(text=ex_txt3,
                                      css_type='tight')

        out_txt += """<pre><code>
        df = g.get_data() # or df = g.get_data('fluxes'), in case the user
                          # have executed reports from other groups
                          </code></pre>"""

        ex_txt4 = '<br>Here <i><code>df</code></i> is an ' \
                  '<i><code>IcosFrame</code></i>, ' \
                  'which is a <i><code>pandas.DataFrame</code></i> together ' \
                  'with some ICOS-metadata that can be reached using the ' \
                  'properties: <br>'
        out_txt += IcosVarGui.set_css(text=ex_txt4,
                                      css_type='tight')

        out_txt += '''<pre><code>
        icos_meta -&gt; dict
        icos_accessUrl -&gt; str
        icos_pid -&gt; str
        icos_previousVersion -&gt; str
        icos_station_name -&gt; str
        icos_station_id -&gt; str
        icos_station_uri -&gt; str
        icos_product -&gt; str
        icos_citationBibTex -&gt; str
        icos_citationRis -&gt; str
        icos_citationString -&gt; str
        icos_title -&gt; str
        icos_columns -&gt; dict
        icos_var_unit_ls -&gt; list 
        </pre></code>'''
        ex_txt5 = 'Here, the user can run: <br>'
        out_txt += IcosVarGui.set_css(text=ex_txt5,
                                      css_type='tight')
        out_txt += '''<pre><code>
                import pandas as pd
                df = pd.Dataframe(df)
                </pre></code>'''
        ex_txt6 = 'in order to convert the data into an standard dataframe.' \
                  '<br><br>'
        out_txt += IcosVarGui.set_css(text=ex_txt6,
                                      css_type='tight')

        example_html.value = out_txt

        end_text = f'For comments, questions, suggestions, bug reports ' \
                   f'or any other kind of feedback, please feel free to ' \
                   f'contact: {mail_cp} or {mail_ad}.</p>'
        end_html.value = IcosVarGui.set_css(text=end_text,
                                            css_type='line')

        display(widgets)

    def _plot_type_settings(self):
        pass

    def _flush_memory(self, group: str = None,
                      plot_setup: str = None,
                      timeseries: bool = None,
                      plot_object: bool = None,
                      reports: bool = None):
        """
            Clear memory of stored timeseries dataframe or stored reports.

            group: str
                The group name.
                If not None, all timeseries of the group are removed,
                If None, all timeseries are removed.

            plot_setup: str
                When used the parameter group is needed
                - Use when a plot setup of the group is changed
                It will remove results from the plot_setup of the
                reports of the group

            timeseries: bool
                When True timeseries dataframe from previous run will
                be removed.
                Use when:
                - The user change anything of a group of variables
                - Run-settings (all timeseries should be removed)
                This will also remove reports of the group(s).

            plot_object: bool
                If True then reinitialise the plot object
                Use when:
                - Plot-settings (all reports should be removed)
                This will also reinitialise the reports.

            reports: bool
                If True stored reports from previous run will be removed
                Use when:
                - The user change anything of a plot setup of a group

        """
        if self.debug:
            self.debug_value(-36, '_flush_memory()   **** flush ****',
                             f' -- grp = {group}')

        if isinstance(self.report_writer, report_writer.ReportWriter):
            if timeseries:
                self.report_writer.remove_timeseries(group=group)
            elif reports or plot_setup:
                self.report_writer.remove_reports(group=group,
                                                  plot_setup=plot_setup)
            if plot_object:
                self.report_writer.reset_plot()

    def _menu_plot_setups(self,
                          _group_name: str = None,
                          _plot_setup_name: str = None):
        if self.debug:
            self.debug_value(-12, '_menu_plot_setups()  *** start ***')

        def _get_multi_plot_auto() -> bool:
            settings = self._load_user_settings()
            multi_p_kwargs = settings.get('multi_plot_kwargs', {})
            return multi_p_kwargs.get('auto_axis', True)

        def reset_plot_setup_gui(reason: str, plot_setup_name: str = None):

            if self.debug:
                self.debug_value(1, 'reset_plot_setup_gui()', 'step 1',
                                 f'plot_setup_name = {plot_setup_name}')
            init_plot_setup_drop(plot_setup_name)
            activate_gui(action_id='reset_gui', reason=reason)

            if self.debug:
                self.debug_value(1, 'reset_plot_setup_gui()', '--- end ---')

        def init_plot_type_buttons():
            plot_type_ls = []
            for plot_type_name in plot_type_names:
                bt = wd.Button(description=plot_type_name,
                               style={'button_color': 'LightGreen'},
                               layout=IcosVarGui._get_width_layout(
                                   plot_type_name))
                bt.on_click(plot_type_click)
                plot_type_ls.append(bt)
            plot_type_buttons.children = plot_type_ls

        def init_group_drop():
            cache = self._load_cache()
            group_ls = list(cache['_groups'].keys())

            if self.debug:
                self.debug_value(0, f'init_group_drop()', '--- start ---',
                                 f'group list = {group_ls}')
            if group_ls:
                group_ls = sorted(group_ls, key=(lambda x: x.lower()))
                group_drop.options = group_ls

        def set_group_value(group: str = None):
            # triggers other widgets at startup
            cache = self._load_cache()
            group_ls = group_drop.options
            if self.debug:
                self.debug_value(0, f'set_group_value() - Here we go --',
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
                self.debug_value(2, f'changed_group_drop()')
            set_group_var_info()
            init_var_translation()
            reset_plot_setup_gui(reason='changed_group_drop')

        def init_var_translation():
            """
                Set dictionary of labels for buttons and selected
                variables, also sets a description text of the variable
                mapping in the User Guide.
                The translation dict is of the form
                {"name of var button": (var,product,station)}
                in a one-to-one correspondence.
                The dictionary is temporarily stored in a widget which
                is not displayed.
            """
            grp = group_drop.value
            cache = self._load_cache()
            var_ls = cache['_groups'][grp]['_group_vars']
            stn_ls = self._station_name_id_ls()
            labels, descr_ls = IcosVarGui.var_tuple_ls_converter(
                var_ls=var_ls,
                output='var_btns',
                stn_name_id_ls=stn_ls,
                debug_fun=self.debug_value)
            if self.debug:
                self.debug_value(3, f'init_var_translation() - start -',
                                 f'group_drop.value = {group_drop.value}',
                                 f'var_ls = {var_ls}',
                                 f'labels = {labels}',
                                 f'descr_txt = {descr_ls}')
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
            translation_dict = dict(zip(labels, var_ls))
            translation_dict['Select all'] = 'All variables'
            translation_dict['description'] = descr_ls

            if self.debug:
                self.debug_value(3, f'init_var_translation() - end -',
                                 f'translation_dict = {translation_dict}')
            var_translation_dict.value = str(translation_dict)

        def var_translation_dict_changed(c):
            description_ls = list(get_var_translation_dict().items())[-1][1]
            if not description_ls or len(description_ls) == 1:
                var_description.value = ''
                return

            header_txt = '<h3>Variable origins and abbreviation mapping</h3>'
            st_txt = f'<i>Variables from station</i> '
            txt = ''
            for stn_prod_ls in description_ls:
                stn = st_txt + stn_prod_ls[0]
                prod_ls = stn_prod_ls[1]
                txt += IcosVarGui.set_css(stn, 'tight_header')
                for prod in prod_ls:
                    txt += IcosVarGui.set_css(prod, 'tight')

            info_color = self.widget_style_colors['primary:active']
            txt = f'<span style="color:{info_color}">{txt}</span>'
            var_description.value = header_txt + txt

        def init_group_var_buttons(mode: str):
            if self.debug:
                self.debug_value(6, f'init_group_var_buttons() ',
                                 f' -- input mode = {mode}',
                                 f' -- var_buttons.children = '
                                 f'{var_buttons.children}')

            if mode == 'create' and not var_buttons.children:
                var_list = list(get_var_translation_dict().items())[:-1]
                var2unit_dict = get_var2unit_dict()
                btn_ls = []
                for v_name, var_ls in var_list[:-1]:
                    unit = var2unit_dict.get(var_ls[0], var2unit(var_ls))
                    btn = wd.Button(description=v_name,
                                    disabled=True,
                                    tooltip=unit,
                                    style={'button_color': 'LightSeaGreen'},
                                    layout=IcosVarGui._get_width_layout(v_name))
                    btn.on_click(var_button_click)
                    btn_ls.append(btn)
                v_name = 'Select all'
                btn = wd.Button(description=v_name,
                                disabled=True,
                                tooltip='',
                                style={'button_color': 'MediumSeaGreen'},
                                layout=IcosVarGui._get_width_layout(v_name))
                btn.on_click(var_button_click)
                btn_ls.append(btn)
                var_buttons.children = btn_ls

            elif mode == 'reset':
                for b in var_buttons.children:
                    b.icon = ''
            elif mode == 'delete':
                var_buttons.children = []
            if self.debug:
                self.debug_value(6, f'init_group_var_buttons() -- end --',
                                 f' -- input mode = {mode}',
                                 f' -- var_buttons.children = '
                                 f'{var_buttons.children}')

        def init_plot_setup_drop(plot_setup_name: str = None):
            cache = self._load_cache()
            group = group_drop.value
            plot_setup_dict = cache['_groups'][group].get('_plot_setups', {})
            if self.debug:
                self.debug_value(9, 'init_plot_setup_drop() -- step 1',
                                 f'(input) plot_setup_name = {plot_setup_name}',
                                 f'group = {group}',
                                 f'plot_setup_dict = {plot_setup_dict}')
            if plot_setup_dict:
                plot_setup_labels = sorted(list(plot_setup_dict.keys()),
                                           key=(lambda x: x.lower()))
                plot_setup_drop.options = [(k, plot_setup_dict[k]) for k in
                                           plot_setup_labels]
                if plot_setup_name and plot_setup_name in plot_setup_labels:
                    plot_setup_label = plot_setup_name
                else:
                    plot_setup_label = plot_setup_labels[0]
                if self.debug:
                    self.debug_value(9, 'init_plot_setup_drop() -- step 2 - '
                                        f'plot_setup_label = {plot_setup_label}',
                                     f'plot_setup_drop.options = '
                                     f'{plot_setup_drop.options}')
                plot_setup_drop.label = plot_setup_label
            else:
                plot_setup_drop.options = [('Press new...', 0)]
                plot_setup_drop.value = 0
                html_msg(text_ls=[f'Press <i>New</i>, in order to create a plot '
                                  f'setup for the group <i>{group}</i>.'])
            if self.debug:
                self.debug_value(9, 'init_plot_setup_drop() -- step 3',
                                 f'plot_setup_drop.label = '
                                 f'{plot_setup_drop.label}',
                                 f'plot_setup_drop.value = '
                                 f'{plot_setup_drop.value}',
                                 f'-- end--')
            changed_plot_setup_drop('reset_plot_setup_gui')

        def changed_plot_setup_drop(c):
            if plot_setup_drop.value:
                plot_setup = plot_setup_drop.value.copy()
            else:
                plot_setup = 0
            if self.debug:
                self.debug_value(11, 'changed_plot_setup_drop()',
                                 '- step 1 - plot_setup value changed, '
                                 'reset displayed selections',
                                 f'c = {c}',
                                 f'plot_setup_drop.label = '
                                 f'{plot_setup_drop.label}',
                                 f'plot_setup_drop.value = {plot_setup}')

            if plot_setup != 0:
                plot_setup_version = plot_setup.pop('_version', '0')
                set_plot_setup_upd_dict(dict(_upd_mode=
                                             'read_mode_with_plot_setup',
                                             _plot_types=plot_setup,
                                             _selected_plot_type_index=None,
                                             _version=plot_setup_version))
            else:
                set_plot_setup_upd_dict(dict(_upd_mode='read_mode_no_plot_setup',
                                             _plot_types={}))

            set_user_guide_msg(info_type=plot_setup)

            if self.debug:
                self.debug_value(11, 'changed_plot_setup_drop()',
                                 '- step 2 - ',
                                 f'upd_dict_log.value = {upd_dict_log.value}')

        def reset_selection(c):
            # TODO: check what has changed and divide the update accordingly

            plot_setup_dict = get_plot_setup_upd_dict()

            if self.debug:
                self.debug_value(13, f'reset_selection()',
                                 f'c = {c}',
                                 f'plot_setup_dict = {plot_setup_dict}',
                                 f'plot_setup_drop.value = '
                                 f'{plot_setup_drop.value}')

            sel_plot_type_index = plot_setup_dict.pop('_selected_plot_type_index',
                                                      None)
            plot_types = plot_setup_dict.get('_plot_types', {})

            # we need to clean up deprecated plots
            temp_pt = {}
            i = 0
            deprecated_pt = False
            for idx, pt_row in plot_types.items():
                for pt_code, v_ls in pt_row.items():
                    if pt_code in plot_type2name_dict.keys():
                        temp_pt[i] = {pt_code: v_ls}
                        i += 1
                    elif sel_plot_type_index == idx:
                        deprecated_pt = True
                        sel_plot_type_index = None
            plot_types = temp_pt
            if deprecated_pt:
                plot_setup_dict['_plot_types'] = temp_pt
                set_plot_setup_upd_dict(plot_setup_dict)
                plot_types = temp_pt

            sel_plot_types = [(plot_type2name_dict[k2], k1) for k1, v1 in
                              plot_types.items() for
                              k2 in v1.keys()]
            sel_vars = format_plot_type_vars(plot_types)

            set_selections(sel_plot_type_ls=sel_plot_types,
                           sel_plot_type_index=sel_plot_type_index,
                           sel_var_ls=sel_vars)

            if plot_setup_dict['_upd_mode'] in ['new', 'update']:
                reset_var_buttons()

        def format_plot_type_vars(plot_types):
            # formatting var list to selected_var widget
            if self.debug:
                self.debug_value(15, f'label_of_selected_var_row()',
                                 f'plot_type_code = {plot_types}',
                                 f'plot_setup_drop.value = '
                                 f'{plot_setup_drop.value}')

            sel_vars = []
            if plot_types:
                var_trans_dict = get_var_translation_dict()
                var_trans_dict.pop('description')
                for index, plot_type_dict in plot_types.items():
                    for plot_type_code, plot_type_vars in plot_type_dict.items():
                        if isinstance(plot_type_vars, str):
                            # the case 'all'
                            label_ls = ['All variables']
                        elif plot_type_code != 'multi_plot':
                            # the case of list of var-lists
                            label_ls = [var_name for x in plot_type_vars for
                                        var_name in var_trans_dict.keys() if
                                        var_trans_dict[var_name] == x]
                        else:
                            # the case of list of axes and var-lists
                            label_ls = [var_name for x in plot_type_vars for y in x[1]
                                        for
                                        var_name in
                                        var_trans_dict.keys() if
                                        var_trans_dict[var_name] == y]
                        label_for_plot_type_vars = ', '.join(label_ls)
                        sel_vars.append(
                            (label_for_plot_type_vars, (index, plot_type_vars)))

            return sel_vars

        def set_selections(sel_plot_type_ls: list,
                           sel_plot_type_index: int = -1,
                           sel_var_ls: list = None):
            # Sometimes we want to set the index to None,
            # this is why we have default value -1.
            if self.debug:
                self.debug_value(16, f'set_selections()',
                                 'step 1',
                                 f'sel_plot_type_ls = {sel_plot_type_ls}',
                                 f'sel_plot_type_index = {sel_plot_type_index}',
                                 f'sel_var_ls = {sel_var_ls}')

            rows = 3 + (len(sel_plot_type_ls) // 2) * 2
            selected_plot_types.rows = rows
            selected_vars.rows = rows

            selected_plot_types.unobserve(changed_selected_plot_type,
                                          names='value')
            selected_plot_types.options = sel_plot_type_ls
            if isinstance(sel_plot_type_index, int) and sel_plot_type_index >= 0:
                selected_plot_types.value = sel_plot_type_index
            elif sel_plot_type_index is None:
                selected_plot_types.value = sel_plot_type_index
            selected_plot_types.observe(changed_selected_plot_type, names='value')

            if isinstance(sel_var_ls, list):
                selected_vars.options = sel_var_ls
            if selected_plot_types.value is not None:
                try:
                    ind = selected_plot_types.value
                    sel_vars = selected_vars.options[ind][0]
                except Exception as e:
                    sel_vars = ''
                    if self.debug:
                        self.debug_value(16, f'set_selections() ---- exception',
                                         f'--- Exception: {e}',
                                         f'selected_vars.options = '
                                         f'{selected_vars.options}',
                                         f'ind = {selected_plot_types.value}')
            else:
                sel_vars = ''
            description_ls = list(get_var_translation_dict().items())[-1][1]

            txt = sel_vars + '\n' if sel_vars else ''
            txt += 'Variable origins and abbreviation mapping\n'
            for stn_prod_ls in description_ls:
                stn = stn_prod_ls[0]
                prod_ls = stn_prod_ls[1]
                for x in ['&nbsp', '<b>', '<i>', '<u>', '</b>', '</i>', '</u>']:
                    stn = stn.replace(x, '')
                txt += f'\t{stn}  \n'
                for prod in prod_ls:
                    for x in ['&nbsp', '<b>', '<i>', '<u>', '</b>', '</i>',
                              '</u>']:
                        prod = prod.replace(x, '')
                    txt += f'\t \t{prod}\n'
            selected_vars.tooltip = txt

            if self.debug:
                self.debug_value(16, f'set_selections()', 'end ',
                                 f'selected_plot_types.value = '
                                 f'{selected_plot_types.value}',
                                 f'selected_plot_types.options = '
                                 f'{selected_plot_types.options}',
                                 f'selected_vars.options = '
                                 f'{selected_vars.options}',
                                 f'selected_vars.tooltip = '
                                 f'{selected_vars.tooltip}')

        def changed_selected_plot_type(c):
            # Triggered when a plot_type is selected,
            # not triggered by plot_type buttons
            if self.debug:
                self.debug_value(112,
                                 f'changed_selected_plot_type() triggered p_type',
                                 f'c = {c}')

            # Depending on c.old we might have to modify the selection index
            selected_index = c.new

            # Also, in order to avoid more work than necessary we set
            upd_changed = False

            # In case of a deselected plot_type with no variables we must
            # clean up the selected_vars widget
            if isinstance(c.old, int):
                upd_dict = get_plot_setup_upd_dict()
                plot_types = upd_dict.get('_plot_types', {})
                upd_dict['_plot_types'], upd_changed = cleanup_plot_types(
                    plot_types)

                if upd_changed:
                    if isinstance(selected_index, int) and selected_index > c.old:
                        selected_index = selected_index - 1
                if upd_dict['_selected_plot_type_index'] != selected_index:
                    upd_dict['_selected_plot_type_index'] = selected_index
                    upd_changed = True

                if upd_changed:
                    # this will trigger reset_var_buttons()
                    set_plot_setup_upd_dict(upd_dict)

            if selected_index is None:
                info_type = 'upd'
            else:
                sel_plot_types = list(selected_plot_types.options)
                plot_type_name = sel_plot_types[selected_index][0]
                info_type = name2plot_type_dict[plot_type_name]

            if info_type != 'multi_plot':
                reset_multi_plot_auto(hide=True)
            else:
                upd_dict = get_plot_setup_upd_dict()
                var_codes = list(
                    upd_dict['_plot_types'][selected_index].values())[0]
                axis_ls = [axis[0] for axis in var_codes]
                mp_auto_enable = not len(axis_ls) == 2
                mp_auto_value = not len(axis_ls) != len(set(axis_ls))
                reset_multi_plot_auto(hide=False,
                                      enable=mp_auto_enable,
                                      value=mp_auto_value)

            if self.debug:
                self.debug_value(112,
                                 f'changed_selected_plot_type() triggered '
                                 f'p_type 2',
                                 f'selected_index = {selected_index}',
                                 f'info_type = {info_type}',
                                 f'plot_type_name = {plot_type_name}')
            set_plot_type_info(info_type=info_type)

            if not upd_changed:
                reset_var_buttons()

        def set_plot_type_info(info_type: str = None):
            # set info text depending on update mode and plot_type
            # show/hide buttons etc
            # cases of info_type:
            # 'upd', 'new', 'update', multi_plot, 'corr_plot',
            # 'split_plot', 'corr_table', 'statistics'

            if self.debug:
                self.debug_value(129, f'set_plot_type_info()',
                                 f' -- info_type = {info_type}')

            if info_type == 'reset_gui':
                msg_ls = ['<b>You are in <i>read mode</i>.</b> '
                          'Either select a group of variables or a '
                          'plot setup, and choose <b><i>New</i></b>, '
                          'or <b><i>Update</i></b>. For more guidance, '
                          'please check the <b><i>User guide</i></b>.']
            else:
                msg_ls = ['<b>You are in <i>update mode</i>.</b> ']
                if info_type == 'new':
                    msg_ls.extend(['To create a new plot setup: ',
                                   '1. Choose at least one plot type from the '
                                   'list of <i>Available plot types</i>, and '
                                   'add some variables to it.',
                                   '2. Choose a name for the plot setup. '])
                elif name_of_plot_setup.value == 'Name of plot setup':
                    msg_ls.append('Name the plot setup in the area <b><i>Name of '
                                  'plot setup</i></b>.')
                if info_type == 'update':
                    msg_ls.extend(['<b><i>To edit</i></b> the content of a '
                                   'plot type: Select the plot type to in the '
                                   'list above, '
                                   'and use the variable buttons to add or '
                                   'remove them from the plot type.',
                                   '<b><i>To delete</i></b> the plot setup, '
                                   'just press '
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
                    msg_ls.extend([f'Either select or add some plot type to the '
                                   f'plot setup.'])
                elif info_type in plot_type2name_dict.keys():
                    msg_ls.extend([f'<b><i>{plot_type2name_dict[info_type]}'
                                   f'</i></b> '
                                   f'selected. <b>Please note that '
                                   f'this plot types is not implemented at '
                                   f'this moment. </b>',
                                   'No restriction on the variables.'])
                if self.debug:
                    self.debug_value(129, f'set_plot_type_info()  --- end ---',
                                     f' msg_lse = {msg_ls}')

            plot_type_info.value = '<br>'.join(msg_ls)
            set_user_guide_msg(info_type=info_type)

        def set_user_guide():
            if user_guide_container.layout.display == 'block':
                upd_mode = get_plot_setup_upd_dict().get('_upd_mode', '')
                if self.debug:
                    self.debug_value(1311, 'set_user_guide() ',
                                     f'upd_mode = {upd_mode}')
                if upd_mode == 'read_mode_no_plot_setup':
                    user_guide.value = '<H3><b>To create a plot ' \
                                       'setup:</b></H3><br>' \
                                       '1. Choose a group of variables. ' \
                                       '2. Press <i>New</i> and follow the ' \
                                       'directions.'
                elif upd_mode == 'read_mode_with_plot_setup':
                    user_guide.value = '<H3><b>To create a plot setup:</b></H3>' \
                                       '<br>'\
                                       '1. Choose a group of variables.<br>' \
                                       '2. Press <i>New</i> and follow the ' \
                                       'directions.<br>' \
                                       '<b>To change or delete a plot ' \
                                       'setup:</b><br>' \
                                       '1. Select the group of variables and ' \
                                       'the plot setup.<br>' \
                                       '2. Press <i>Update</i>. and follow the ' \
                                       'directions.<br>' \
                                       '3. In case the plot setup should be ' \
                                       'deleted, just press <i>Delete</i> ' \
                                       'without changing the content.'
                elif upd_mode == 'new':
                    user_guide.value = '<H3><b><i>New plot setup</i></b> ' \
                                       '</H3><br>' \
                                       'To create a new plot setup: ' \
                                       '<ol>' \
                                       '<li> Use a plot type buttons in the ' \
                                       'list of <i>Available plot types</i> ' \
                                       'to add a plot type to the plot setup, ' \
                                       'and add variables to the plot ' \
                                       'type.</li>' \
                                       '<li>Choose a name for the plot setup. ' \
                                       '</li> ' \
                                       '</ol> ' \
                                       'A plot setup can have several plot types.'
                elif upd_mode == 'update':
                    user_guide.value = '<H3><b><i>Update plot setup</i></b>' \
                                       '</H3><br>' \
                                       'To edit the content of a plot type: ' \
                                       '<ol><li> Use a plot type buttons in the ' \
                                       'list of <i>Available plot types</i> ' \
                                       'to add a plot type to the plot setup, ' \
                                       'and add variables to the plot ' \
                                       'type.</li>' \
                                       '<li>To change variables of a plot ' \
                                       'type, ' \
                                       'select the plot type in the list ' \
                                       '<b><i>Current setup</i></b>, ' \
                                       'and use the variable buttons to ' \
                                       'add or remove them from the plot ' \
                                       'type.' \
                                       '</li></ol>' \
                                       '<br><b><i>To delete</i></b> the plot ' \
                                       'setup, just press <b><i>Delete</i></b> ' \
                                       'without changing the content.'

        def reset_multi_plot_auto(hide: bool,
                                  enable: bool = None,
                                  value: bool = None):

            if self.debug:
                self.debug_value(131, 'reset_multi_plot_auto() - before',
                                 f'hide = {hide}', f'enable = {enable}',
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
            plot_type_index = selected_plot_types.value
            if self.debug:
                self.debug_value(17, 'reset_var_buttons()   --- start ---',
                                 f'  - index of selected_plot_types = '
                                 f'{plot_type_index}')
            if plot_type_index is None:
                if self.debug:
                    self.debug_value(17, 'reset_var_buttons()   -- index = None',
                                     '  -- deselecting and disabling all ',
                                     'var-buttons and the "Up"-btn')
                move_up.disabled = True
                for btn in var_buttons.children:
                    btn.disabled = True
                    btn.icon = ''
            elif isinstance(plot_type_index, int):
                move_up.disabled = False
                upd_dict = get_plot_setup_upd_dict()
                row_dict = upd_dict['_plot_types'][plot_type_index]
                var_trans_dict = get_var_translation_dict()
                var_trans_dict.pop('description')
                for plot_type_code, var_codes in row_dict.items():
                    if self.debug:
                        self.debug_value(17, f'reset_var_buttons()  -- index '
                                             f'= {plot_type_index}',
                                         f'  --- plot_type_code = '
                                         f'{plot_type_code}',
                                         f'  --- var_codes = {var_codes}')
                    if plot_type_code == 'multi_plot':
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

                    elif plot_type_code == 'corr_plot':
                        if self.debug:
                            self.debug_value(17,
                                             f'reset_var_buttons() --- restore '
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
            index = selected_plot_types.value
            if self.debug:
                self.debug_value(113, f'move_selected() click',
                                 f'plot_type index = {index}')

            if index is not None:
                upd_dict = get_plot_setup_upd_dict()['_plot_types']
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

                update_plot_setup_dict(dict(_plot_types=upd_dict,
                                            _selected_plot_type_index=new_index))

        def plot_type_click(plot_type):
            if self.debug:
                self.debug_value(114, f'plot_type_click()',
                                 f'plot_type.description = {plot_type.description}',
                                 f'tool.icon = {plot_type.icon}')
            if plot_type.icon:
                plot_type.style.button_color = "LightGreen"
                plot_type.icon = ''
                plot_type_added = False
            else:
                for btn in plot_type_buttons.children:
                    if btn != plot_type:
                        btn.style.button_color = "LightGreen"
                        btn.icon = ''
                plot_type.style.button_color = "Green"
                plot_type.icon = 'check'
                plot_type_added = True
            update_plot_type_list(add_plot_type=plot_type_added,
                                  plot_type_name=plot_type.description)

        def update_plot_type_list(add_plot_type,
                                  plot_type_name):
            # Similar to, but different from changed_selected_plot_type()
            # at this stage the plot_type is not in the upd_dict.
            if self.debug:
                self.debug_value(115, f'update_plot_type_list() -- input',
                                 f'add_plot_type = {add_plot_type}',
                                 f'plot_type_name = {plot_type_name}')

            # We must remove empty rows, in case this or another plot_type was
            # deselected without variables.
            plot_types = get_plot_setup_upd_dict().get('_plot_types', {})
            plot_types, _ = cleanup_plot_types(plot_types)

            if self.debug:
                self.debug_value(115, f'update_plot_type_list()',
                                 f'plot_types (cleaned) ={plot_types}')

            if add_plot_type:
                plot_type_code = name2plot_type_dict[plot_type_name]
                info_type = plot_type_code
                key = len(plot_types.keys())
                plot_types[key] = {plot_type_code: []}
                selected_plot_types.disabled = True
                if plot_type_code == 'multi_plot':
                    # A new multi-plot is added
                    new_multi_plot = True
                else:
                    new_multi_plot = False
            else:
                # Tool button is deselected
                info_type = 'upd'
                new_multi_plot = False
                key = None
                selected_plot_types.disabled = False

            if new_multi_plot:
                reset_multi_plot_auto(hide=False,
                                      enable=True,
                                      value=_get_multi_plot_auto())
            else:
                reset_multi_plot_auto(hide=True)

            update_plot_setup_dict(dict(_plot_types=plot_types,
                                        _selected_plot_type_index=key))
            set_plot_type_info(info_type=info_type)

        def var_button_click(btn):

            upd_dict = get_plot_setup_upd_dict()['_plot_types']
            row_index = selected_plot_types.value
            if self.debug:
                self.debug_value(116, f'var_button_click()',
                                 f'btn.description = {btn.description}',
                                 f'selected_plot_types.value = {row_index}',
                                 f'before:  - upd_dict[row_index] ='
                                 f' {upd_dict[row_index]}')

            for plot_type_code, upd_var_codes in upd_dict[row_index].items():
                if self.debug:
                    self.debug_value(116, f'var_button_click() ***',
                                     f'plot_type_code = {plot_type_code}',
                                     f'upd_var_codes = {upd_var_codes}')
                var_trans_dict = get_var_translation_dict()
                var_name = btn.description
                var_code = var_trans_dict[var_name]
                if var_code == 'All variables':
                    if upd_var_codes != 'all':
                        upd_var_codes = 'all'
                    else:
                        upd_var_codes = []
                elif plot_type_code != 'multi_plot':
                    if var_code in upd_var_codes:
                        upd_var_codes.remove(var_code)
                    else:
                        upd_var_codes.append(var_code)
                elif plot_type_code == 'multi_plot':
                    if self.debug:
                        self.debug_value(116, f'var_button_click() ****',
                                         f'plot_type_code = {plot_type_code}',
                                         f'multi_plot_auto_cb.value = '
                                         f'{multi_plot_auto_cb.value}')
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
                        self.debug_value(116, f'var_button_click()',
                                         f'plot_type_code = {plot_type_code}',
                                         f'multi_plot_auto_cb.value = '
                                         f'{multi_plot_auto_cb.value}')

                upd_dict[row_index] = {plot_type_code: upd_var_codes}
                if self.debug:
                    self.debug_value(116, f'var_button_click()',
                                     f'after:',
                                     f' - upd_dict[row_index] = '
                                     f'{upd_dict[row_index]}')

                update_plot_setup_dict(dict(_plot_types=upd_dict,
                                            _selected_plot_type_index=row_index))

        def get_var2unit_dict():
            if self.debug:
                self.debug_value(32, f'get_var2unit_dict()')
            d = eval(var_to_unit_dict.value)
            if not (d and isinstance(d, dict)):
                d = self._load_app_configs().get('_var2unit_map', {})
                var_to_unit_dict.value = str(d)
            return d

        def var2unit(var, update: bool = False):
            var2unit_dict = get_var2unit_dict()
            if update or var[0] not in var2unit_dict.keys():
                pid = st_df.loc[(st_df.id == var[-1]) & (
                        st_df.specLabel == var[1])].dobj.values[0]
                try:
                    meta = icos_data.StationData.icos_pid2meta(pid)
                except:
                    set_pid_error(pid, var)
                    return ''
                var_unit_list = meta['varUnitList']
                var2unit_dict.update({v[0]: v[1] for v in var_unit_list})
                app_configs = self._load_app_configs()
                app_configs['_var2unit_map'].update(var2unit_dict)
                self._set_app_configs(app_dict=app_configs)
                var_to_unit_dict.value = str(var2unit_dict)

            unit = var2unit_dict[var[0]]
            if self.debug:
                self.debug_value(8, f'var2unit()', f'var = {var}',
                                 f'return unit = {unit}')
            return unit

        def set_pid_error(pid, var):
            error_ls = [f'Data error! ',
                        f'Could not access the data object of: <i>{var[1]}</i>',
                        f'from the station {var[2]}. ',
                        f'Url to the landing page of the data object: '
                        f'<a href="{pid}" target="_blank">'
                        f'<font color="DarkBlue">{pid}</font></a>']
            set_user_guide_msg(error_ls=error_ls)

        def set_group_var_info():
            cache = self._load_cache()
            if self.debug:
                self.debug_value(4, f'set_group_var_info()')

            if isinstance(cache, dict) and '_groups' in cache.keys():
                grp = group_drop.value
                if grp in cache['_groups'].keys():
                    content_title = f'Content of group {grp}'
                    content_text = get_var_info_text(group=grp)
                else:
                    content_title = f'Content of a group goes here'
                    content_text = '<b>Variables of the group goes here.</b>'
            else:
                # No cache,
                content_title = f'Content of a group goes here'
                content_text = '<b>Variables of the group goes here.</b>'

            g_vars.set_title(0, content_title)
            group_vars.value = content_text

        def get_var_info_text(group: str = None):
            if self.debug:
                self.debug_value(5, f'get_var_info_text()')
            if group:
                cache = self._load_cache()
                var_tuples = copy.deepcopy(cache['_groups'][group]['_group_vars'])
                output_code = 'var_cont_read'
                stn_ls = self._station_name_id_ls()
                return IcosVarGui.var_tuple_ls_converter(var_ls=var_tuples,
                                                         output=output_code,
                                                         stn_name_id_ls=stn_ls,
                                                         debug_fun=
                                                          self.debug_value)

        def html_msg(text_ls: list = None,
                     title: str = None,
                     error: bool = None,
                     show_user_guide: bool = None):
            if self.debug:
                self.debug_value(118, f'html_msg()')

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

            txt = f'<span style="color:{color}">'
            txt += f'{margin}<h3>{msg_title} {emoji}</h3>'
            if isinstance(text_ls, list):
                txt += f'<h3>{margin}'
                txt += f'<br>{margin}'.join(text_ls)
                txt += '</h3>'
            txt += '</span>'
            if user_guide.value:
                user_guide.value += f'<br>{txt}'
            else:
                user_guide.value = txt
            if show_user_guide:
                user_guide.layout.display = 'block'
            with out:
                clear_output()
                txt = IcosVarGui.set_css(text=txt,
                                         css_type='line')
                display(wd.HTML(txt))

        def set_user_guide_msg(info_type=None, error_ls=None):
            if user_guide_container.layout.display == 'none':
                return
            upd_dict = get_plot_setup_upd_dict()
            upd_mode = upd_dict.get('_upd_mode', None)
            grp = group_drop.value
            if self.debug:
                self.debug_value(130, 'set_user_guide_msg()',
                                 f'upd_dict = {upd_dict}',
                                 f'upd_mode = {upd_mode}',
                                 f'grp = {grp}')
            message = ''
            if upd_mode == 'new':
                txt = self.help_dict['plot_setup']['new_header']
                txt += self.help_dict['plot_setup']['new_edit_body1'] + '<br>'
                txt += self.help_dict['plot_setup']['new_edit_body2'] + '<br>'
                txt += self.help_dict['plot_setup']['new_edit_changes'] + '<hr>'
                message += IcosVarGui.set_css(text=txt, css_type='line')
            elif upd_mode == 'update':
                txt = self.help_dict['plot_setup']['edit_delete_header']
                txt += self.help_dict['plot_setup']['new_edit_body1'] + '<br>'
                txt += self.help_dict['plot_setup']['new_edit_body2'] + '<br>'
                txt += self.help_dict['plot_setup']['delete_body'] + '<br>'
                txt += self.help_dict['plot_setup']['new_edit_changes'] + '<hr>'
                message += IcosVarGui.set_css(text=txt, css_type='line')
            else:
                txt = self.help_dict['plot_setup']['read_header1']
                txt += self.help_dict['plot_setup']['read_body1'] + '<br>'
                txt += self.help_dict['plot_setup']['read_header2'] + '<br>'
                txt += self.help_dict['plot_setup']['read_body2'] + '<br>'
                txt += self.help_dict['plot_setup']['new_edit_changes']
                message += IcosVarGui.set_css(text=txt, css_type='line')

            if info_type:
                plot_type = info_type
            else:
                index = upd_dict.get('_selected_plot_type_index', None)
                if index and index in upd_dict['_plot_types'].keys():
                    plot_type = list(upd_dict['_plot_types'][index].keys())[0]
                else:
                    plot_type = None

            if plot_type in ['multi_plot', 'corr_plot', 'split_plot',
                             'corr_table']:
                txt = self.help_dict['plot_setup'][plot_type]
                message += IcosVarGui.set_css(text=txt, css_type='line')

            if message:
                info_color = self.widget_style_colors['primary:active']
                message = f'<span style="color:{info_color}">' \
                      f'{message}</span>'

            if error_ls:
                margin = '&nbsp' * 3
                warning_emoji = '\u26a0\ufe0f'
                error_color = self.widget_style_colors['danger:active']
                txt = f'<span style="color:{error_color}">{margin}{margin}'
                txt += f'<h3>To do: {warning_emoji}</h3>'
                txt += f'<b>'
                for error in error_ls:
                    txt += f'{margin}{error}<br>'
                txt += '</b></span>'
                message += '<hr>' + IcosVarGui.set_css(text=txt,
                                                       css_type='line')

            if error_ls and user_guide_container.layout.display == 'none':
                display_user_guide('display_guide')

            user_guide.value = message

        def cleanup_plot_types(d: dict) -> (dict, bool):
            # returns "a clean plot type-dict" and boolean for "dict has changed"
            if self.debug:
                self.debug_value(120, f'cleanup_plot_types() -- (before)',
                                 f"upd_dict['_plot_types'] = {d}")

            if isinstance(d, dict) and d:
                d_copy = d.copy()
                for plot_type_number, plot_type_var in d_copy.items():
                    for t_name in plot_type_var.keys():
                        if not plot_type_var[t_name]:
                            d.pop(plot_type_number)
                        elif t_name == 'corr_plot' and len(plot_type_var[t_name]) != 2:
                            d.pop(plot_type_number)
                # allways reset the plot type number
                d = dict(zip(range(len(d.keys())), d.values()))
                dict_has_changed = (d != d_copy)
            else:
                dict_has_changed = False

            if self.debug:
                self.debug_value(120, f'cleanup_plot_types() -- (after)',
                                 f'd = {d}',
                                 f'dict_has_changed = {dict_has_changed}')

            return d, dict_has_changed

        def validate_name(name):
            cache = self._load_cache()
            grp = group_drop.value
            error_ls = []
            if not name or name == 'Name of plot setup':
                error_ls.append('Please choose a name for plot setup')
            elif not name[0].isalnum():
                error_ls.append('At least the first letter of the name')
                error_ls.append('must be an alfa numeric character.')
            elif grp in cache['_groups'].keys():
                plot_setups = cache['_groups'][grp].get('_plot_setups', {})
                if name in plot_setups.keys():
                    upd_dict = get_plot_setup_upd_dict()
                    if name != upd_dict['_orig_name']:
                        error_ls.append(
                            f'There is already a plot setup called '
                            f'<i>{name}</i>,')
                        error_ls.append('please pick another name.')

            if error_ls:
                name_of_plot_setup.style.text_color = 'red'
            else:
                name_of_plot_setup.style.text_color = 'darkgreen'
                name_of_plot_setup.layout = IcosVarGui._get_width_layout(name)

            if self.debug:
                self.debug_value(121, f'validate_name()',
                                 f'name = {name}',
                                 f'error_ls = {error_ls}')

            return error_ls

        def plot_setup_name_changed(change):
            if self.debug:
                self.debug_value(122, f'plot_setup_name_changed()',
                                 f'change = {change}',
                                 f'name = {change.owner.value}')

            if change.type == 'change':
                new_name = change.owner.value
                error_ls = validate_name(new_name)
                upd_dict = {}

                if error_ls:
                    if self.debug:
                        self.debug_value(122, f'plot_setup_name_changed()',
                                         f'\t error_ls = {error_ls}')
                    upd_dict['_name_error'] = error_ls
                else:
                    if self.debug:
                        self.debug_value(122, f'plot_setup_name_changed()',
                                         f'\t new_name={new_name}')
                    upd_dict['_new_name'] = new_name
                if self.debug:
                    self.debug_value(122, f'plot_setup_name_changed()',
                                     f'\t plot_setup_drop.value='
                                     f'{plot_setup_drop.value}')
                update_plot_setup_dict(upd_dict)

        def get_var_translation_dict() -> dict:
            if self.debug:
                self.debug_value(7, f'get_var_translation_dict()',
                                 f'var_translation_dict.value = '
                                 f'{var_translation_dict.value}')

            d = eval(var_translation_dict.value)
            return d

        def get_plot_setup_upd_dict() -> dict:
            d = eval(upd_dict_log.value)
            if isinstance(d, dict):
                if '_plot_types' in d.keys():
                    d['_plot_types'] = {int(k): v for k, v in
                                        d['_plot_types'].items()}
            else:
                d = dict()

            if self.debug:
                self.debug_value(14, 'get_plot_setup_upd_dict()', f'd ={d}')

            return d

        def set_plot_setup_upd_dict(d: dict):
            if self.debug:
                self.debug_value(12, 'set_plot_setup_upd_dict()', 'step 1',
                                 f'd ={d}')

            json_safe_dict = {k: v for k, v in d.items() if k != '_plot_types'}
            json_safe_dict['_plot_types'] = {str(k): v for k, v in
                                             d['_plot_types'].items()}

            upd_dict_log.value = str(json_safe_dict)
            if self.debug:
                self.debug_value(12, 'set_plot_setup_upd_dict()', 'step 2',
                                 f'upd_dict_log.value ={upd_dict_log.value}')

        def update_plot_setup_dict(d: dict):
            if self.debug:
                self.debug_value(123, f'update_plot_setup_dict()',
                                 f'd = {d}')
            upd_dict = get_plot_setup_upd_dict()
            for k, v in d.items():
                upd_dict[k] = v
            set_plot_setup_upd_dict(upd_dict)

        # def set_plot_setup_upd_selections(d: dict = None):
        #
        #
        #     if d is None:
        #         d = selections2plot_setup_dict()
        #
        #     upd_dict = get_plot_setup_upd_dict()
        #
        #     upd_dict['_plot_types'] = {str(k): v for k, v in
        #     d['_plot_types'].items()}
        #     upd_dict['_selected_plot_type_index'] =
        #     d.get('_selected_plot_type_index', -1)
        #     set_plot_setup_upd_dict(upd_dict)

        def get_valid_plot_setup():
            cache = self._load_cache()
            grp = group_drop.value
            ps = plot_setup_drop.label
            ps2validate = plot_setup_drop.value.copy()

            if '_var_mismatch' in cache['_groups'][grp].keys():
                if ps in cache['_groups'][grp]['_var_mismatch'].keys():
                    er_dict = cache["_groups"][grp]["_var_mismatch"][ps]
                    if self.debug:
                        self.debug_value(128, f'validate_plot_setup()',
                                         f'plot_setup_drop.label = '
                                         f'{plot_setup_drop.label}',
                                         f'plot_setup_drop.value = '
                                         f'{ps2validate}',
                                         f'er_dict = {er_dict}')
                    reindex = False
                    for index, plot_type_vars in er_dict.items():
                        for v_ls in plot_type_vars.values():
                            for v in v_ls:
                                for p_type, val in ps2validate[index].items():
                                    if p_type == 'multi_plot':
                                        for y in val:
                                            if v in y[1]:
                                                y[1].remove(v)
                                            if not y[1]:
                                                val.remove(y)
                                    else:
                                        if v in val:
                                            val.remove(v)
                                            if p_type == 'corr_plot':
                                                val = []
                                    if not val:
                                        ps2validate.pop(index)
                                        reindex = True

                    if reindex:
                        j = 0
                        d = {}
                        for i in ps2validate.keys():
                            if i != '_version':
                                d[str(j)] = ps2validate[i]
                                j += 1
                            else:
                                d[i] = ps2validate[i]
            return ps2validate

        def new_plot_setup(c):

            with out:
                clear_output()

            upd_dict = {'_upd_mode': 'new',
                        '_version': 0,
                        '_orig_name': '',
                        '_new_name': '',
                        '_plot_types': {},
                        '_selected_plot_type_index': None}

            if self.debug:
                self.debug_value(124, 'new_plot_setup()',
                                 f'upd_dict = {upd_dict}')

            set_plot_setup_upd_dict(upd_dict)
            name_of_plot_setup.value = "Name of plot setup"
            activate_gui('new')

        def update_plot_setup(c):
            if self.debug:
                self.debug_value(125, f'update_plot_setup()',
                                 f'plot_setup_drop.label = '
                                 f'{plot_setup_drop.label}',
                                 f'plot_setup_drop.value = '
                                 f'{plot_setup_drop.value}')

            stored_plot_setup = get_valid_plot_setup()
            plot_setup_version = int(stored_plot_setup.pop('_version', 1))
            plot_setup_upd = dict(_upd_mode='update',
                                  _version=plot_setup_version,
                                  _plot_types=stored_plot_setup,
                                  _orig_name=plot_setup_drop.label,
                                  _new_name=plot_setup_drop.label,
                                  _selected_plot_type_index=None)
            name_of_plot_setup.value = plot_setup_drop.label
            set_plot_setup_upd_dict(plot_setup_upd)
            activate_gui('update')

        def save_plot_setup(c):
            # Note: Avoid using `get_upd_dict()` here, some keys are
            # integers which is not "json-safe" of some reason.
            # The keys stored in  `upd_dict_log.value` are strings.
            upd_dict = eval(upd_dict_log.value)
            ps_name = upd_dict['_new_name']
            old_ps_name = upd_dict['_orig_name']
            grp = group_drop.value
            cache = self._load_cache()
            plot_setups = cache['_groups'][grp].get('_plot_setups', {})

            if self.debug:
                self.debug_value(125, 'save_plot_setup()',
                                 f'upd_dict = {upd_dict}')

            error_ls = validate_name(ps_name)
            plot_type_dict, _ = cleanup_plot_types(
                upd_dict.get('_plot_types', {}))

            if not plot_type_dict:
                error_ls.append('Please choose some plot type and variables.')

            if error_ls:
                html_msg(text_ls=error_ls, error=True)
            else:
                with out:
                    clear_output()

                config = plot_type_dict
                config['_version'] = str(int(upd_dict['_version']) + 1)

                plot_setups.pop(old_ps_name, None)
                plot_setups[ps_name] = config
                if self.debug:
                    self.debug_value(20, 'save_plot_setup()',
                                     f'plot_setups = {plot_setups}')

                cache['_groups'][grp]['_plot_setups'] = plot_setups
                d = cache['_groups'][grp]

                var_mismatch_dict = self._validate_plot_setup_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)
                    cache['_last_group'] = grp
                    vars_of_last_group = cache['_groups'][grp]['_group_vars']
                    cache['_last_station_id'] = vars_of_last_group[-1][-1]

                # cleaning up memory
                # we only have to fix the case:

                self._set_cache(cache_dict=cache)
                if old_ps_name:
                    self._flush_memory(group=grp, plot_setup=old_ps_name,
                                       reports=True)

                reset_plot_setup_gui(reason='saved_plot_setup',
                                     plot_setup_name=ps_name)

        def cancel_plot_setup(c):
            if self.debug:
                self.debug_value(126, 'cancel_plot_setup()')
            reset_plot_setup_gui(reason='cancel_plot_setup_upd')

        def delete_plot_setup(c):

            upd_dict = eval(upd_dict_log.value)
            orig_plot_types = plot_setup_drop.value.copy()
            orig_plot_types.pop('_version', None)
            orig_plot_types = {str(k): v for k, v in orig_plot_types.items()}
            ps_name = upd_dict['_new_name']
            if self.debug:
                self.debug_value(127, 'delete_plot_setup()',
                                 f'ps_name = {ps_name}',
                                 f'plot_setup_drop.label = '
                                 f'{plot_setup_drop.label}',
                                 f'orig_plot_types = {orig_plot_types}',
                                 f"upd_dict['_plot_types'] = "
                                 f"{upd_dict['_plot_types']}")

            validation_error_ls = []
            if upd_dict['_orig_name'] != ps_name:
                validation_error_ls.append('  - Name changed.')
            if upd_dict['_plot_types'] != orig_plot_types:
                validation_error_ls.append(
                    '  - Change of plot types or variables.')
            if validation_error_ls:
                error_ls = ['Deletion error:',
                            'To delete a plot setup, just choose update '
                            "and then delete - without changing it\'s content."]
                error_ls.extend(validation_error_ls)
                error_ls.append('Suggestion to delete: Press Cancel, '
                                'Update and Delete')
                html_msg(text_ls=error_ls, error=True)
                if self.debug:
                    self.debug_value(127, f'delete_plot_setup()  --error-- ',
                                     f'error_ls = {error_ls}',
                                     f'orig_plot_types:  {orig_plot_types}',
                                     f"upd_dict['_plot_types']: "
                                     f"{upd_dict['_plot_types']}")
                return
            else:
                grp = group_drop.value
                cache = self._load_cache()
                plot_setups = cache['_groups'][grp].get('_plot_setups', {})
                plot_setups.pop(ps_name, None)
                cache['_groups'][grp]['_plot_setups'] = plot_setups
                d = cache['_groups'][grp]
                var_mismatch_dict = self._validate_plot_setup_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)

                self._set_cache(cache_dict=cache)

                if self.debug:
                    self.debug_value(127, f'delete_plot_setup() ',
                                     f'deleted: {ps_name}')
                reset_plot_setup_gui(reason='delete_plot_setup')

        #        def clear_debug_list(c):
        #            with debug_out:
        #                clear_output()

        def display_user_guide(c):
            if c == 'display_guide':
                user_guide_container.selected_index = 0
                user_guide_container.layout.display = 'block'
            elif user_guide_container.layout.display == 'none':
                user_guide_container.layout.display = 'block'
                set_user_guide_msg()
            else:
                user_guide_container.layout.display = 'none'

        # activate/deactivate upd-widgets
        def activate_gui(action_id: str, reason: str = None):
            if self.debug:
                self.debug_value(10, 'activate_gui()',
                                 f'action_id = {action_id}',
                                 f'reason = {reason}')

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
                            if disable is not None:
                                if 'disabled' in wd_input.keys:
                                    wd_input.disabled = disable
                            if tooltip is not None and 'tooltip' in wd_input.keys:
                                wd_input.tooltip = tooltip
                elif isinstance(wd_input, list):
                    for w in wd_input:
                        set_widget_state(w, disable, tooltip, show_widget)

            set_plot_type_info(info_type=action_id)

            set_widget_state(multi_plot_auto_cb, show_widget=False)

            update_enable_list = [selected_plot_types]
            update_disable_list = [group_drop, plot_setup_drop]
            update_display_list = [name_row, plot_type_row, var_row, move_up]

            if any(plot_type_buttons.children):
                for p_type in plot_type_buttons.children:
                    p_type.icon = ''
                    p_type.style.button_color = 'LightGreen'
            else:
                init_plot_type_buttons()

            if action_id in ['new', 'update']:
                # update mode
                init_group_var_buttons(mode='create')
                # reset_plot_setup_gui update widgets..
                #        set_user_guide_msg()

                name_of_plot_setup.observe(plot_setup_name_changed, 'value')
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
                    self.debug_value(10, 'activate_gui() - upd 1',
                                     f'action_id = {action_id}',
                                     f'save_btn.disabled = {save_btn.disabled}',
                                     f'delete_btn.disabled = '
                                     f'{delete_btn.disabled}')
                if action_id == 'update':
                    delete_btn.disabled = False
                    delete_btn.tooltip = 'Click to delete...'
                else:
                    delete_btn.disabled = True
                    delete_btn.tooltip = 'Delete...'
                    selected_plot_types.value = None
                    selected_plot_types.options = []
                    selected_vars.value = None
                    selected_vars.options = []
                if self.debug:
                    self.debug_value(10, 'activate_gui() - upd 2',
                                     f'action_id = {action_id}',
                                     f'save_btn.disabled = {save_btn.disabled}',
                                     f'delete_btn.disabled = '
                                     f'{delete_btn.disabled}')

            elif action_id == 'reset_gui':
                # read mode
                if reason == 'changed_group_drop':
                    init_group_var_buttons(mode='delete')
                else:
                    init_group_var_buttons(mode='reset')

                try:
                    name_of_plot_setup.unobserve(plot_setup_name_changed, 'value')
                except ValueError:
                    pass
                set_widget_state(update_enable_list, disable=True)
                set_widget_state(update_disable_list, disable=False)
                set_widget_state(update_display_list, show_widget=False)

                new_btn.disabled = False
                new_btn.tooltip = 'New plot setup...'
                if not plot_setup_drop.value or isinstance(plot_setup_drop.value,
                                                           int):
                    upd_btn.disabled = True
                    upd_btn.tooltip = 'No plot setup to update...'
                else:
                    upd_btn.disabled = False
                    upd_btn.tooltip = 'Update plot setup...'

                set_widget_state(save_buttons, disable=True,
                                 tooltip='Enabled in update mode...')

        st_df = self.stations_df

        # Static lookup dictionary for plot types
        if self.debug:
            plot_type_codes = ['split_plot', 'multi_plot', 'corr_plot',
                               'corr_table', 'statistics']
            plot_type_names = ['Split-plot', 'Multi-plot',
                               'Correlation plot (2 vars)',
                               'Correlation table', 'Numerical Statistics']
        else:
            plot_type_codes = ['split_plot', 'multi_plot', 'corr_plot']
            plot_type_names = ['Split-plot', 'Multi-plot', 'Correlation plot']

        plot_type2name_dict = dict(zip(plot_type_codes, plot_type_names))
        name2plot_type_dict = {v: k for k, v in plot_type2name_dict.items()}

        # Widgets
        out = wd.Output()

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
        #   keeps track on updates of the plot setup
        var_to_unit_dict = wd.Textarea(value='{}', disabled=True)
        var_translation_dict = wd.Textarea(value='{}', disabled=True)
        var_translation_dict.observe(var_translation_dict_changed,
                                     names='value')
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
                self.debug_value(-12, '_menu_plot_setups()  *** init ***',
                                 '--- There are no groups. ---')
            msg = wd.HTML('<h3>First you need to create a group of '
                          'variables using the <b><i>Group menu</i></b></h3')
            return display(msg)

        group_drop.observe(changed_group_drop, names='value')
        plot_setup_drop = wd.Dropdown(layout=drop_layout,
                                      description_tooltip='Plot setups')
        plot_setup_drop.observe(changed_plot_setup_drop, names='value')

        group_vars = wd.HTML(layout=var_txt_layout,
                             value='Variables: ',
                             disabled=True)
        g_vars = wd.Accordion([group_vars],
                              titles=(group_vars.value, '0'),
                              selected_index=None,
                              layout=full_layout)
        row_list = [wd.HBox([group_drop, plot_setup_drop, g_vars],
                            layout=full_layout)]

        # 2:nd row update-buttons
        new_btn = wd.Button(description='New',
                            icon='plus',
                            button_style='primary',
                            layout=wd.Layout(width='100px'))
        new_btn.on_click(new_plot_setup)

        upd_btn = wd.Button(description='Update',
                            icon='pen',
                            button_style='info',
                            layout=wd.Layout(width='100px'))
        upd_btn.on_click(update_plot_setup)
        save_btn = wd.Button(description='Save',
                             icon='save',
                             button_style='success',
                             layout=wd.Layout(width='100px'))
        save_btn.on_click(save_plot_setup)
        cancel_btn = wd.Button(description='Cancel',
                               icon='ban',
                               button_style='info',
                               layout=wd.Layout(width='100px'))
        cancel_btn.on_click(cancel_plot_setup)
        delete_btn = wd.Button(description='Delete',
                               icon='trash',
                               button_style='danger',
                               layout=wd.Layout(width='100px'))
        delete_btn.on_click(delete_plot_setup)
        user_guide_btn = wd.Button(description='User guide',
                                   disabled=False,
                                   icon='fa-info-circle',
                                   button_style='info',
                                   tooltip='Show user guide...',
                                   layout=wd.Layout(width='100px'))
        user_guide_btn.on_click(display_user_guide)

        create_buttons = wd.HBox([new_btn, upd_btn])
        save_buttons = wd.HBox([save_btn, cancel_btn, delete_btn])
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
                                 layout=wd.Layout(width='auto',
                                                  max_width='59%',
                                                  height='auto'))
        var_description = wd.HTML(layout=wd.Layout(width='auto',
                                                   max_width='40%'))
        if self.debug:
            user_guide_container.children = [wd.VBox([wd.HBox([user_guide,
                                                               var_description]),
                                                      upd_dict_log])]
        else:
            user_guide_container.children = [wd.HBox([user_guide,
                                                      var_description])]
        user_guide_container.set_title(0, 'User guide')

        row_list.append(user_guide_container)

        # 4:th row. update section: plot setup
        name_label = wd.HTML(value='<b><i>Name of plot setup: </i></b>',
                             layout=wd.Layout(min_width='125px'))
        name_of_plot_setup = wd.Text(value='Name of plot setup',
                                     layout=wd.Layout(min_width='200px'))

        name_row = wd.HBox([name_label, name_of_plot_setup])
        row_list.append(name_row)

        # 5:th row. update section: Tools
        plot_type_label = wd.HTML('<b><i>Available plot types: </i></b>',
                                  layout=label_layout)
        plot_type_buttons = wd.HBox(layout=flex_layout)
        plot_type_row = wd.HBox([plot_type_label, plot_type_buttons])
        row_list.append(plot_type_row)

        # 6:th row. update section: Vars
        avail_variables_label = wd.HTML('<b><i>Available variables: </i></b>',
                                        layout=label_layout)
        var_buttons = wd.HBox(layout=flex_layout)
        var_row = wd.VBox([avail_variables_label, var_buttons])
        row_list.append(var_row)

        # 7:rd row. update section: Selections
        selection_label = wd.HTML('<b><i>Current setup: </i></b>')

        move_up = wd.Button(description='Up',
                            disabled=False,
                            icon='arrow-up',
                            tooltip='Move selected plot type...',
                            layout=wd.Layout(width='60px'))
        move_up.on_click(move_selected)

        left_selection_box = wd.VBox([selection_label, move_up],
                                     layout=wd.Layout(width='auto',
                                                      min_width='130px',
                                                      max_width='20%'))
        selected_plot_types = wd.Select(disabled=False,
                                        layout=wd.Layout(max_width='150px'))
        selected_plot_types.tooltip = "The plot types are listed in order " \
                                      "of execution." \
                                      "\nUse the Up-button (displayed in " \
                                      "update-mode)" \
                                      "\nto change the order of " \
                                      "\nexecution."
        selected_plot_types.observe(changed_selected_plot_type, names='value')

        selected_vars = wd.Select(disabled=True,
                                  layout=wd.Layout(width='auto',
                                                   min_width='20%',
                                                   max_width='80%'))

        row_list.append(wd.HBox([left_selection_box,
                                 selected_plot_types,
                                 selected_vars]))

        # 8:rd row. info, special settings
        # Info regarding selected plot type
        plot_type_info = wd.HTMLMath(layout=info_guide_layout)

        multi_plot_auto_cb = wd.Checkbox(description='Choose axis according to '
                                                     'unit',
                                         value=_get_multi_plot_auto(),
                                         layout=multi_auto_select_label_layout)

        # special_settings = wd.VBox([multi_plot_auto_cb, multi_plot_axis])
        info_box = wd.VBox([plot_type_info, multi_plot_auto_cb])
        row_list.append(info_box)

        # Trigger changed_group_drop that populate other widgets.
        set_group_value(group=_group_name)

        row_list.append(out)
        plot_setup_widget = wd.VBox(row_list)

        display(plot_setup_widget)

    def _menu_settings(self):
        if self.debug:
            self.debug_value(-10, '_menu_settings   *** start ***')

        def init_general_settings():
            # set general values
            settings = self._load_user_settings()
            stored_settings.value = str(settings)

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
            split_p_border_cb.value = split_p_kwargs.get('border', True)
            split_p_use_latex_cb.value = split_p_kwargs.get('use_latex', True)
            split_p_plotly_templates.value = split_p_kwargs.get('template',
                                                                'plotly')
            split_p_height.value = split_p_kwargs.get('height', 0)
            split_p_width.value = split_p_kwargs.get('width', 0)
            split_p_title_font.value = split_p_kwargs.get('title_font',
                                                          plotly_text_fonts[0])
            split_p_title_size.value = split_p_kwargs.get('title_size', 16)
            split_p_subtitle_size.value = split_p_kwargs.get('subtitle_size', 12)

            multi_p_auto_axis_cb.value = multi_p_kwargs.get('auto_axis', True)
            multi_p_border_cb.value = multi_p_kwargs.get('border', True)
            multi_p_use_latex_cb.value = multi_p_kwargs.get('use_latex', True)
            multi_p_plotly_templates.value = multi_p_kwargs.get('template',
                                                                'plotly')
            multi_p_height.value = multi_p_kwargs.get('height', 0)
            multi_p_width.value = multi_p_kwargs.get('width', 0)
            multi_p_title_font.value = multi_p_kwargs.get('title_font',
                                                          plotly_text_fonts[0])
            multi_p_title_size.value = multi_p_kwargs.get('title_size', 16)
            multi_p_subtitle_size.value = multi_p_kwargs.get('subtitle_size', 12)

            corr_p_border_cb.value = corr_p_kwargs.get('border', True)
            corr_p_use_latex_cb.value = corr_p_kwargs.get('use_latex', True)
            corr_p_plotly_templates.value = corr_p_kwargs.get('template',
                                                              'plotly')
            corr_p_height.value = corr_p_kwargs.get('height', 0)
            corr_p_width.value = corr_p_kwargs.get('width', 0)
            corr_p_title_font.value = corr_p_kwargs.get('title_font',
                                                        plotly_text_fonts[0])
            corr_p_title_size.value = corr_p_kwargs.get('title_size', 16)
            corr_p_subtitle_size.value = corr_p_kwargs.get('subtitle_size', 12)
            corr_p_color_scale_drop.value = corr_p_kwargs.get('color_scale',
                                                              'blues')

            corr_t_title_font.value = corr_t_kwargs.get('title_font',
                                                        plotly_text_fonts[0])
            corr_t_title_size.value = corr_t_kwargs.get('title_size', 16)
            corr_t_subtitle_size.value = corr_t_kwargs.get('subtitle_size', 12)
            corr_t_border_cb.value = corr_t_kwargs.get('border', True)
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

        def latex_changed(c=None):
            latex = icos2latex.Translator(use_exp=latex_use_exp_cb.value,
                                          font_size=latex_font_size.value,
                                          font_style=latex_font_style.value)
            tex_str = '$\\qquad $ ' * 3 + \
                      latex.var_unit_to_latex(var_unit=("CO2", "\u00b5mol mol-1"))
            if self.debug:
                self.debug_value(-11, 'latex_changed()',
                                 f'tex_str = {tex_str}')

            with latex_output_area:
                clear_output()
                display(Math(tex_str))

        def settings_changed(c):
            cancel_btn.disabled = False
            save_btn.disabled = False

        def height_or_width_changed(c):
            if c.new < 210:
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
                             'border': split_p_border_cb.value,
                             'use_latex': split_p_use_latex_cb.value,
                             'template': split_p_plotly_templates.value,
                             'title_font': split_p_title_font.value,
                             'title_size': split_p_title_size.value,
                             'subtitle_size': split_p_subtitle_size.value,
                             'width': split_p_width.value,
                             'height': split_p_height.value},
                        'multi_plot_kwargs':
                            {'auto_axis': multi_p_auto_axis_cb.value,
                             'border': multi_p_border_cb.value,
                             'use_latex': multi_p_use_latex_cb.value,
                             'template': multi_p_plotly_templates.value,
                             'title_font': multi_p_title_font.value,
                             'title_size': multi_p_title_size.value,
                             'subtitle_size': multi_p_subtitle_size.value,
                             'width': multi_p_width.value,
                             'height': multi_p_height.value},
                        'corr_plot_kwargs':
                            {'use_latex': corr_p_use_latex_cb.value,
                             'border': corr_p_border_cb.value,
                             'template': corr_p_plotly_templates.value,
                             'color_scale': corr_p_color_scale_drop.value,
                             'title_font': corr_p_title_font.value,
                             'title_size': corr_p_title_size.value,
                             'subtitle_size': corr_p_subtitle_size.value,
                             'width': corr_p_width.value,
                             'height': corr_p_height.value},
                        'corr_table_kwargs':

                            {'color_scale': corr_t_color_scale_drop.value,
                             'border': corr_t_border_cb.value,
                             'title_font': corr_t_title_font.value,
                             'title_size': corr_t_title_size.value,
                             'subtitle_size': corr_t_subtitle_size.value},
                        'statistics_kwargs': {}
                        }
            new_run_setting = upd_dict.get('run_configs', {})
            new_report_settings = [upd_dict.get('latex_kwargs', {}),
                                   upd_dict.get('split_plot_kwargs', {}),
                                   upd_dict.get('multi_plot_kwargs', {}),
                                   upd_dict.get('corr_plot_kwargs', {}),
                                   upd_dict.get('corr_table_kwargs', {}),
                                   upd_dict.get('statistics_kwargs', {})]

            settings = eval(stored_settings.value)
            if not isinstance(settings, dict):
                settings = dict()
            stored_run_setting = settings.get('run_configs', {})
            stored_report_settings = [settings.get('latex_kwargs', {}),
                                      settings.get('split_plot_kwargs', {}),
                                      settings.get('multi_plot_kwargs', {}),
                                      settings.get('corr_plot_kwargs', {}),
                                      settings.get('corr_table_kwargs', {}),
                                      settings.get('statistics_kwargs', {})]

            json_handler.update(data_piece=upd_dict,
                                path_to_json_file=self.user_config_file)
            # cleaning up memory
            if new_run_setting != stored_run_setting:
                self._flush_memory(group=None, timeseries=True)
            if new_report_settings != stored_report_settings:
                self._flush_memory(group=None, plot_object=True)

            init_general_settings()

        def cancel_general_settings(c):
            init_general_settings()

        def link(url, url_txt) -> str:
            return f'<a href="{url}" target="_blank">' \
                   f'<font color="DarkBlue">{url_txt}</font></a>'

        # lists of plotly: color-scales, templates, text-fonts, and text-sizes
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
        plotly_text_sizes = [6, 7, 8, 9, 10, 11, 12, 13,
                             14, 15, 16, 17, 18, 19, 20]

        # common texts
        col_href = link("https://www.aao.org/eye-health/"
                        "diseases/what-is-color-blindness", "color deficiencies")
        color_ref = f'the color scale can be changed in order to ' \
                    f'ease variants of <b><i>{col_href}</i></b>.'
        plotly_link_href = link("https://plotly.com/python/", "Plotly")
        plotly_templ_href = link("https://plotly.com/python/templates/",
                                 "Plotly template")
        plotly_templ_ref = f'The background color can be changed by switching ' \
                           f'the <b><i>{plotly_templ_href}</i></b>.<br>'
        height_or_width_min = 'Setting <b><i>Height</i></b> or ' \
                              '<b><i>Width</i></b> to a value below ' \
                              '210 will lead to plotly default ' \
                              'value. '

        # common label widgets
        label_layout = wd.Layout(min_width='90px', max_width='220px')
        plotly_templ_label = wd.HTML(value='<b>Plotly template:</b>',
                                     layout=label_layout)
        use_latex_label = wd.HTML(value='<b>Use LaTeX</b>',
                                  layout=label_layout)
        use_border_label = wd.HTML(value='<b>Plotting area border</b>',
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
        stored_settings = wd.Textarea(value='{}')
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
                             layout=wd.Layout(width='100px'))
        cancel_btn = wd.Button(description='cancel',
                               icon='cancel',
                               button_style='info',
                               layout=wd.Layout(width='100px'))
        save_btn.on_click(save_general_settings)
        cancel_btn.on_click(cancel_general_settings)
        save_cancel_box = wd.HBox([save_btn,
                                   cancel_btn])
        observe_ordinary_ls = []
        observe_pos_ls = []
        observe_height_width_ls = []

        txt = '<h3>Default settings</h3>'
        txt2 = '<span>Here you can modify certain ' \
               'settings such as: ' \
               '<i>what data to use, visualizations of different ' \
               'plots ' \
               'and texts</i>. All plots available are based on the ' \
               f'python package <b><i>{plotly_link_href}</i></b>.' \
               '<br>' \
               '<b><i>Please note</i></b> that the <b>Save</b>-button below is ' \
               'enabled when a value is changed and the user press ' \
               '<it><b>&lttab&gt</b> or <b>clicks outside</b> the widget ' \
               'holding the value</it>.<br>' \
               'Also, if you find problems related to any of these settings, ' \
               'do not hesitate to report this according to the description in ' \
               'the <it>Help</it> menu.</span>'
        txt += IcosVarGui.set_css(text=txt2, css_type='tight')
        def_settings_guide = wd.HTML(value=txt)

        txt_guide = '<h4>Guide:</h4>'
        txt2 = '<span>When the user start the application, the default ' \
               'behaviour is to execute all plot setups of the last edited ' \
               'group of variables, to change this switch of ' \
               '<b><i>Auto-run</i></b> below.<br> '
        txt3 = 'Plots and statistics outputs are based on values measured ' \
               'between the <i>start</i> and the <i>end dates</i>, displayed ' \
               'in the <b>Plot</b> menu. Of course, the dates displayed in ' \
               'the plot menu can be changed for each run. ' \
               'Here, you can modify the ' \
               '<i>default method on how to calculate these dates.</i> ' \
               '</span><br> '
        txt4 = 'The number at <b><i>End date</b></i> ' \
               'is the number of days <i>before today</i>, ' \
               'while <b><i>Start date</i></b> is the number of days ' \
               '<i>before the end date</i>. '
        txt5 = '<span>The <b><i>Fetch date</i></b> ' \
               'denotes the number of days <i>before the start date</i>, it ' \
               'is a feature used to <i>speed up re-calculations</i>. ' \
               'In case the user chose to change the report dates in a ' \
               'second run, then data between the fetch date and the end date ' \
               'of the first run will already be in memory.</span>'
        txt_guide += IcosVarGui.set_css(text=txt2, css_type='tight')
        txt_guide += IcosVarGui.set_css(text=txt3, css_type='tight')
        txt_guide += IcosVarGui.set_css(text=txt4, css_type='tight')
        txt_guide += IcosVarGui.set_css(text=txt5, css_type='tight')
        run_settings_guide = wd.HTML(value=txt_guide)
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
                                         'in individual plots. '
                                         'These plots are interconnected using a '
                                         '<i>zoom-slider</i> for the '
                                         '<i>time</i>-axis. '
                                         '<b><i>Split-plot grouping</i></b> is '
                                         'the number of plots '
                                         'displayed before the '
                                         'first zoom-slider, or more '
                                         'accurately the minimal number of '
                                         'plots before a zoom-slider.<br>'
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

        split_p_border_cb = wd.Checkbox(value=True,
                                        disabled=False,
                                        indent=False,
                                        tooltip="Sets a border around "
                                                "the plotting area",
                                        layout=cb_layout)
        split_p_border_box = wd.HBox([split_p_border_cb, use_border_label])

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

        split_p_height = wd.IntText(layout=int_drop_layout)
        split_p_height_box = wd.HBox([height_label,
                                      split_p_height])

        split_p_width = wd.IntText(layout=int_drop_layout)
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
                             wd.HBox([wd.VBox([split_p_border_box,
                                               split_p_latex_box,
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
        observe_ordinary_ls.append(split_p_border_cb)
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
        multi_p_border_cb = wd.Checkbox(value=True,
                                        disabled=False,
                                        indent=False,
                                        tooltip="Sets a border around "
                                                "the plotting area",
                                        layout=cb_layout)
        multi_p_border_box = wd.HBox([multi_p_border_cb, use_border_label])

        multi_p_use_latex_cb = wd.Checkbox(value=True,
                                           disabled=False,
                                           indent=False,
                                           tooltip="Applies to the y-axes",
                                           layout=cb_layout)
        multi_p_latex_box = wd.HBox([multi_p_use_latex_cb,
                                     use_latex_label])

        multi_p_height = wd.IntText(layout=int_drop_layout)
        multi_p_height_box = wd.HBox([height_label,
                                      multi_p_height])

        multi_p_width = wd.IntText(layout=int_drop_layout)
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
                             wd.HBox([wd.VBox([multi_p_border_box,
                                               multi_p_latex_box,
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
        observe_ordinary_ls.append(multi_p_border_cb)
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

        corr_p_border_cb = wd.Checkbox(value=True,
                                       disabled=False,
                                       indent=False,
                                       tooltip="Sets a border around "
                                               "the plotting area",
                                       layout=cb_layout)
        corr_p_border_box = wd.HBox([corr_p_border_cb, use_border_label])

        corr_p_use_latex_cb = wd.Checkbox(value=True,
                                          disabled=False,
                                          indent=False,
                                          tooltip="Applies to the x- and "
                                                  "y-axes",
                                          layout=cb_layout)

        corr_p_latex_box = wd.HBox([corr_p_use_latex_cb,
                                    use_latex_label])

        corr_p_height = wd.IntText(layout=int_drop_layout)
        corr_p_height_box = wd.HBox([height_label,
                                     corr_p_height])

        corr_p_width = wd.IntText(layout=int_drop_layout)
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
                              wd.HBox([wd.VBox([corr_p_border_box,
                                                corr_p_latex_box,
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
                                          titles=('Correlation plot settings',))
        observe_ordinary_ls.append(corr_p_use_latex_cb)
        observe_ordinary_ls.append(corr_p_border_cb)
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
        corr_t_border_cb = wd.Checkbox(value=True,
                                       disabled=False,
                                       indent=False,
                                       tooltip="Sets a border around "
                                               "the plotting area",
                                       layout=cb_layout)
        corr_t_border_box = wd.HBox([corr_t_border_cb, use_border_label])
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
                              wd.HBox([wd.VBox([corr_t_border_box,
                                                corr_t_color_scale_box]),
                                       wd.VBox([corr_t_title_font_box,
                                                corr_t_title_size_box,
                                                corr_t_subtitle_size_box]),
                                       ])
                              ])
        corr_table_settings = wd.Accordion(children=[corr_t_box],
                                           titles=('Correlation table settings',))
        observe_ordinary_ls.append(corr_t_color_scale_drop)
        observe_ordinary_ls.append(corr_t_border_cb)
        observe_ordinary_ls.append(corr_t_title_font)
        observe_ordinary_ls.append(corr_t_title_size)
        observe_ordinary_ls.append(corr_t_subtitle_size)

        statistics_guide = wd.HTML(value='<span><b>Guide:</b><br>'
                                         '<it>To be implemented</it>.</span>')
        statistics_settings = wd.Accordion(children=[statistics_guide],
                                           titles=('Numerical statistics '
                                                   'settings',))
        plot_area = wd.Output()
        settings_widget = wd.VBox([def_settings_guide,
                                   save_cancel_box,
                                   run_settings,
                                   latex_settings,
                                   split_plot_settings,
                                   multi_plot_settings,
                                   corr_plot_settings,
                                   corr_table_settings,
                                   statistics_settings,
                                   plot_area])

        init_general_settings()

        display(settings_widget)

    def _menu_group(self):
        if self.debug:
            self.debug_value(-12, '_menu_group()   *** start ***')

        def update_cache(group_dict):
            if self.debug:
                self.debug_value(-13, 'update_cache()',
                                 f'group_dict = {group_dict}')

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
            #          '_plot_setups': {
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
            #          '_plot_setups': {
            #              'plot_setup with error': {
            #                  '0': {
            #                      'split_plot': [['SWC_1', 'ETC NRT Meteo',
            #                                      'Hyltemossa'],
            #                                     ['SWC_4', 'ETC NRT Meteo',
            #                                      'Hyltemossa']]}}},
            #          '_var_mismatch': {
            #              'plot_setup with error': {
            #                  'split_plot': [['SWC_4', 'ETC NRT Meteo',
            #                                  'Hyltemossa']]}}}}}

            if '_upd_mode' not in group_dict.keys() or \
                    '_group_name' not in group_dict.keys():
                return

            upd_mode = group_dict['_upd_mode']
            grp = group_dict['_group_name']
            var_ls = group_dict['_var_list']
            old_grp = ''
            cache = self._load_cache()
            add_plot_setup = False

            if upd_mode == 'new':
                cache['_groups'][grp] = {'_group_vars': var_ls}
                if self.debug:
                    self.debug_value(-13, 'update_cache()',
                                     f'group_dict = {grp}', len(grp) > 2,
                                     grp[-2:] == '+p')
                if len(grp) > 2 and grp[-2:] == '+p':
                    cache['_groups'][grp]['_plot_setups'] = demo_plot_setup(
                        var_ls)

                # update "last"-flags
                last_var_tuple = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station_id'] = last_var_tuple[-1]
            elif upd_mode == 'update':
                if '_saved_group_name' in group_dict.keys():
                    old_grp = group_dict['_saved_group_name']
                    if grp != old_grp:
                        plot_setups = cache['_groups'][old_grp].get(
                            '_plot_setups', {})
                        cache['_groups'].pop(old_grp)
                        cache['_groups'][grp] = {'_plot_setups': plot_setups}

                cache['_groups'][grp]['_group_vars'] = var_ls
                # update "last"-flags
                last_var_tuple = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station_id'] = last_var_tuple[-1]
            elif upd_mode == 'delete':
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

            # validate_plot_setups
            if upd_mode == 'update' and '_plot_setups' in \
                    cache['_groups'][grp].keys():
                d = cache['_groups'][grp]
                var_mismatch_dict = self._validate_plot_setup_of_grp(d)
                if var_mismatch_dict:
                    cache['_groups'][grp]['_var_mismatch'] = var_mismatch_dict
                else:
                    cache['_groups'][grp].pop('_var_mismatch', None)

            self._set_cache(cache_dict=cache)

            # Remove timeseries and reports from local memory
            self._flush_memory(group=grp, timeseries=True)
            if old_grp:
                self._flush_memory(group=old_grp, timeseries=True)

        def demo_plot_setup(var_ls) -> dict:
            def var2unit(var):
                var2unit_dict = self._load_app_configs().get('_var2unit_map', {})
                if var[0] not in var2unit_dict.keys():
                    pid = st_df.loc[(st_df.id == var[-1]) & (
                            st_df.specLabel == var[1])].dobj.values[0]
                    try:
                        meta = icos_data.StationData.icos_pid2meta(pid)
                    except:
                        set_pid_error(pid, var)
                        return 'error'
                    var_unit_list = meta['varUnitList']
                    var2unit_dict.update({vu[0]: vu[1] for vu in var_unit_list})
                    app_configs = self._load_app_configs()
                    app_configs['_var2unit_map'].update(var2unit_dict)
                    self._set_app_configs(app_dict=app_configs)
                return var2unit_dict[var[0]]

            ps_name = 'Plot example'
            v_ls = copy.deepcopy(var_ls)
            multi_dict = {}
            for i in range(len(var_ls)):
                v = var_ls[i]
                u = var2unit(v)
                if u == 'error':
                    v_ls.pop(i)
                    continue
                if u in multi_dict.keys():
                    multi_dict[u].append(v)
                else:
                    multi_dict[u] = [v]

            multi_list = []
            if self.debug:
                self.debug_value(888, 'demo_plot_setup()',
                                 f'var_ls = {var_ls}',
                                 f'multi_dict = {multi_dict}')
            for k, v_ls in multi_dict.items():
                if len(v_ls) > 1:
                    multi_list.append([k, v_ls])
                if len(multi_list) == 2:
                    break

            if len(multi_list) < 2:
                for k, v_ls in multi_dict.items():
                    if [k, v_ls] not in multi_list:
                        multi_list.append([k, v_ls])
                    if len(multi_list) == 2:
                        break
            p_type = 0
            plot_setup_dict = {ps_name: {str(p_type): {'multi_plot': multi_list}}}

            split_ls = var_ls[:min(5, len(var_ls))]
            p_type += 1
            plot_setup_dict[ps_name][str(p_type)] = {"split_plot": split_ls}
            if len(var_ls) >= 2:
                corr_ls = var_ls[:2]
                p_type += 1
                plot_setup_dict[ps_name][str(p_type)] = {'corr_plot': corr_ls}
                if len(var_ls) >= 4:
                    corr_ls = var_ls[2:4]
                    p_type += 1
                    plot_setup_dict[ps_name][str(p_type)] = {'corr_plot': corr_ls}

            plot_setup_dict[ps_name]['_version'] = '1'
            return plot_setup_dict

        def init():

            val = set_group_drop('')

            if val == 'first_run':
                new_group(val)
                display_user_guide('display_guide')
            else:
                activate_gui('init_read_mode')

        def set_station_drop():
            if self.debug:
                self.debug_value(-14, 'set_station_drop()')

            station_ls = self._station_name_id_ls()
            station_ls = [(f'{v[0]} ({v[1]})', v[1]) for v in station_ls]

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

        def set_prod_drop(change):

            if station_drop.value == 'dummy':
                prod_ls = ['Files...']
                dobj_ls = ['dummy']
            else:
                df = st_df.loc[st_df.id == station_drop.value]
                p_ls = list(df.specLabel)
                d_ls = list(df.dobj)
                prod_ls = []
                dobj_ls = []
                err_obj_ls = []
                # these are ordered with respect to date
                for i in range(len(p_ls)):
                    if p_ls[i] not in prod_ls:
                        prod_ls.append(p_ls[i])
                        dobj_ls.append(d_ls[i])
                    else:
                        err_obj_ls.append((p_ls[i], d_ls[i]))
                if err_obj_ls:
                    emph_1 = '<font color="DarkBlue"><i>'
                    emph_2 = '</i></font>'
                    if len(err_obj_ls) > 1:
                        err_ls = [f'{emph_1}{e[0]}{emph_2} with url: '
                                  f'<a href="{e[1]}" target="_blank">'
                                  f'{emph_1}{e[1]}{emph_2}</a>'
                                  for e in err_obj_ls]
                        er_str = "</li><li>".join(err_ls)
                        txt1 = f'These data objects are old and should be ' \
                               f'deprecated: '
                        txt2 = f'<ol><li>{er_str}</li></ol>'

                    else:
                        file, pid = err_obj_ls[0]
                        url = f'<a href="{pid}" target="_blank">{pid}</a>'
                        txt1 = f'The data object ' \
                               f'{emph_1}{file}{emph_2} ' \
                               f'with url {emph_1}{url}{emph_2}'
                        txt2 = f'is old and should be deprecated.'

                    error_ls = ['ACTION', f'Data deprecation error at the '
                                          f'station '
                                          f'{emph_1}{station_drop.label}{emph_2}',
                                'There should only be one data object per file.',
                                txt1, txt2]
                    if self.debug:
                        self.set_persistent_error(error_ls=error_ls)

            if self.debug:
                self.debug_value(-1114, 'set_prod_drop()',
                                 f'change = {change}',
                                 f'station = {station_drop.label}',
                                 f'prod_ls = {prod_ls}',
                                 f'dobj_ls = {dobj_ls}')

            prod_drop_ls = list(zip(prod_ls, dobj_ls))
            prod_drop_ls.sort(key=lambda v: v[0].lower())
            if change in ['new', 'update']:
                grp = group_drop.value
                cache = self._load_cache()
                if not (grp and grp in cache['_groups'].keys()):
                    grp = cache['_last_group']
                try:
                    last_prod = cache['_groups'][grp]['_group_vars'][-1][1]
                    prod_label = last_prod if last_prod in prod_ls else ''
                except:
                    # case of first run, deleted groups or
                    # manually changed json
                    prod_label = ''
                    pass
            elif product_drop.label and product_drop.label in prod_ls:
                # case when in upd-mode and station has changed
                prod_label = product_drop.label
            else:
                # case when in upd-mode and station has changed, but from a
                # station with error in previous product
                upd_dict = get_temp_dict()
                prod_label = ''
                if isinstance(upd_dict, dict):
                    var_tuples = upd_dict.get('_var_list', [])
                    if var_tuples:
                        last_var = var_tuples[-1]
                        prod_label = last_var[1] if last_var[1] in prod_ls else ''
                if not prod_label:
                    # case when in upd-mode and station has changed, but from a
                    # station with error in previous product, and no var has
                    # been added.
                    grp = group_drop.value
                    cache = self._load_cache()
                    if not(grp and grp in cache['_groups'].keys()):
                        grp = cache['_last_group']
                    try:
                        last_prod = cache['_groups'][grp]['_group_vars'][-1][1]
                        prod_label = last_prod if last_prod in prod_ls else ''
                    except:
                        pass

            if not prod_label:
                # certainly the case of first run, deleted groups or
                # manually changed json
                prod_label = prod_ls[0]

            product_drop.options = prod_drop_ls
            product_drop.value = [y[1] for y in prod_drop_ls if y[0] ==
                                  prod_label].pop()

        def set_var_drop():
            def var_name_sort(var_name):
                # sorting the variables in
                # 1 alphabetic order where "_" is interpreted as space.
                # 2 in case of meteosens variable, the second digit goes first,
                # 3 'X_2_2_1' comes before 'X_10_2_1'
                var_parts = var_name.split('_')

                digit_ls = var_parts[-3:]
                if len(digit_ls) == 3 and all(i.isdigit() for i in digit_ls):
                    # we want to sort with respect to 2nd index,
                    # and also that 10, 1, 2, 3 is sorted as 1, 2, 3, 10
                    sorted_digits_ls = [format(f'{x:>3}') for x in
                                        [digit_ls[1], digit_ls[0], digit_ls[2]]]
                    # print(999, ' '.join(var_parts[:-3] + sorted_digits_ls))
                    return ' '.join(var_parts[:-3] + sorted_digits_ls)
                elif digit_ls[-1].isdigit():
                    digit_ls[-1] = format(f'{digit_ls[-1]:>3}')
                    return ' '.join(var_parts[:-3] + digit_ls)
                return ' '.join(var_parts)

            if self.debug:
                self.debug_value(-15, 'set_var_drop()',
                                 f'product_drop.options = '
                                 f'{product_drop.options}')

            # Menu of variables to show some info of a variable
            if product_drop.value == 'dummy':
                var_drop.options = [('Select a station...', 'dummy')]
                var_drop.value = var_drop.options[0][1]
            else:
                pid = product_drop.value
                try:
                    var_dict = icos_data.StationData.icos_pid2meta(pid)['columns']
                except:
                    error_prod = product_drop.label
                    if 'Error: ' not in error_prod:
                        drop_ls = list(product_drop.options)
                        prod_ls = [p[0] for p in drop_ls]
                        dobj_ls = [p[1] for p in drop_ls]
                        ind = prod_ls.index(error_prod)
                        prod_ls[ind] = f'Error: {error_prod}'
                        prod_drop_ls = list(zip(prod_ls, dobj_ls))
                        product_drop.options = prod_drop_ls
                        product_drop.value = prod_drop_ls[ind][1]
                        set_pid_error()
                    var_drop.options = [('Error in data object!', 'error')]
                    var_drop.value = var_drop.options[0][1]
                    return

                var_ls = sorted([key for key in var_dict.keys() if key not in
                                 ['TIMESTAMP', 'TIMESTAMP_END']],
                                key=var_name_sort)
                var_info = [var_dict[key] for key in var_ls]
                var_drop.options = list(zip(var_ls, var_info))
                var_drop.value = var_drop.options[0][1]
                set_var_info_text('')

        def set_pid_error(pid: str = None, var: tuple = None):

            if self.debug:
                self.debug_value(-88, 'set_pid_error() ', f'pid = {pid}',
                                 f'var = {var}',
                                 f'product_drop.options = '
                                 f'{product_drop.options}')
            if not (isinstance(pid, str) and isinstance(var, tuple)):
                prod_drop_ls = list(product_drop.options)
                er_prod_ls = []
                er_pid_ls = []
                selected_prod = ''
                selected_url = ''
                for p in prod_drop_ls:
                    if 'Error' in p[0]:
                        p0 = p[0][7:]
                        p1 = f'<a href="{p[1]}" target="_blank">{p[1]}</a>'
                        if p[0] == product_drop.label:
                            selected_prod = p0
                            selected_url = p1
                        er_prod_ls.append(p0)
                        er_pid_ls.append(p1)
                prod = ', '.join(er_prod_ls)
                if len(er_prod_ls) > 1:
                    pid = '<ol><li>'
                    pid += '</li><li>'.join(er_pid_ls)
                    pid += '</li></ol>'
                    s = 's'
                else:
                    pid = er_pid_ls[0]
                    s = ''
                st = station_drop.label
            elif isinstance(pid, str) and isinstance(var, tuple):
                prod = var[1]
                selected_prod = prod
                st = var[2]
                pid = f'<a href="{pid}" target="_blank">{pid}</a>'
                selected_url = pid
                s = ''
            else:
                return
            error_ls1 = ['ACTION',
                         f'Severe Data Error at the station <font '
                         f'color="DarkBlue">{st}</font>',
                         f'Could not access the data object of: '
                         f'<font color="DarkBlue"><i>{selected_prod}'
                         f'</i></font>',
                         f'Landing page of the data object: '
                         f'<font color="DarkBlue">{selected_url}</font>']
            error_ls2 = ['ACTION',
                         f'Severe Data Error at the station <font '
                         f'color="DarkBlue">{st}</font>',
                         f'Could not access the data object{s} of: '
                         f'<font color="DarkBlue"><i>{prod}.</i></font>',
                         f'Landing page{s} of the data object{s}: '
                         f'<font color="DarkBlue">{pid}</font>']
            if self.debug:
                error_ls2.append(f'The error will be stored in the error '
                                 f'widget, below the main menu.')
                self.set_persistent_error(error_ls=error_ls1)
            set_info_msg(error_ls=error_ls2)

        def set_var_info_text(change):
            if self.debug:
                self.debug_value(-16, 'set_var_info_text()',
                                 f'change: {change}')

            # Show info of a variable
            if isinstance(change, dict):
                if isinstance(change['owner'], wd.Dropdown):
                    if var_drop.value == 'dummy':
                        var_info_text.value = 'Here basic ' \
                                              'information on variables are ' \
                                              'given. Make sure you are in ' \
                                              'update mode, and then:' \
                                              '<ol>' \
                                              '<li><i>Select a ' \
                                              'station</i></li>' \
                                              '<li><i>Select a ' \
                                              'product' \
                                              '</i> ' \
                                              'Then the menu here will display ' \
                                              'variables of that product.'
                        return
                    elif var_drop.value == 'error':
                        var_info_text.value = 'Error in data object. See the ' \
                                              '<b><i>User guide</i></b> for ' \
                                              'details.'
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
                        self.debug_value(-16, 'set_var_info_text()',
                                         f' - var_drop.options = '
                                         f'{var_drop.options}',
                                         f' - var_dict = {var_dict} ',
                                         f' - change["owner"].description = '
                                         f'{change["owner"].description}')
                else:
                    var_info_text.value = ''
                    return

            else:
                # init call from set_var_drop
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
                self.debug_value(-17, 'set_group_drop() ',
                                 f' - cache.keys()  = '
                                 f'{cache.keys()}')

            # load from cache
            group_ls = list(cache['_groups'].keys())
            last_grp = cache['_last_group']

            if group_ls:
                group_ls = list(cache['_groups'].keys())
                group_drop.options = sorted(group_ls, key=(lambda x: x.lower()))
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

        def get_group_var_text(upd_mode: bool,
                               var_list: list = None):
            if self.debug:
                self.debug_value(-18, 'get_group_var_text() ',
                                 f' - upd_mode  = {upd_mode}')
            if upd_mode:
                if not var_list:
                    upd_dict = get_temp_dict()
                    var_tuples = copy.deepcopy(upd_dict['_var_list'])
                else:
                    var_tuples = copy.deepcopy(var_list)
                output_code = 'var_cont_upd'
            else:
                grp = group_drop.value
                cache = self._load_cache()
                var_tuples = copy.deepcopy(cache['_groups'][grp]['_group_vars'])
                output_code = 'var_cont_read'
            if not var_tuples:
                return ''

            stn_ls = self._station_name_id_ls()
            return IcosVarGui.var_tuple_ls_converter(var_ls=var_tuples,
                                                     output=output_code,
                                                     stn_name_id_ls=stn_ls,
                                                     debug_fun=self.debug_value)

        def set_group_vars(c):
            cache = self._load_cache()
            if self.debug:
                self.debug_value(-20, f'set_group_vars()',
                                 f'cache.keys() = {cache.keys()}')
            if isinstance(cache, dict):
                grp = group_drop.value
                if grp not in cache['_groups'].keys():
                    content_title = f'Content of a group goes here'
                    content_text = '<b>Variables of the group goes here.</b>'
                else:
                    content_title = f'Content of group {grp}'
                    content_text = get_group_var_text(upd_mode=False)
            else:
                content_title = f'Content of a group goes here'
                content_text = '<b>Variables of the group goes here.</b>'
            g_vars.set_title(0, content_title)
            group_vars.value = content_text

        def set_var_checkboxes(c):
            # Checkboxes for variables

            if self.debug:
                self.debug_value(-21, f'set_var_checkboxes()')
            # to make sure the drop has been updated, order matters...
            set_var_drop()

            if station_drop.value == 'dummy' or product_drop.value == 'dummy':
                var_label.value = ''
                var_cbs_box.children = []
                return
            elif 'Error' in product_drop.label:
                error_color = self.widget_style_colors['danger:active']
                err_msg = f'<span style="color:{error_color}">' \
                          f'Error in data object. See the ' \
                          '<b><i>User guide</i></b> for ' \
                          'details.</span>'
                var_label.value = err_msg
                var_cbs_box.children = []
                return

            station = station_drop.value
            spec = product_drop.label

            var_label.value = f'<b>Variables of {str(spec)} at {str(station)}</b>'

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
                self.debug_value(-22, f'get_temp_dict()',
                                 f'group_dict_log.value = '
                                 f'{group_dict_log.value}')

            temp_log = group_dict_log.value
            if temp_log:
                upd_group_dict = eval(temp_log)
            else:
                upd_group_dict = dict()

            return upd_group_dict

        def set_temp_dict(upd_dict):

            if self.debug:
                self.debug_value(-23, f'set_temp_dict()',
                                 f'upd_dict = {upd_dict}')

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
                upd_ls = [var_name, product_drop.label, station_drop.value]

                # Load group dict
                upd_group_dict = get_temp_dict()
                if cb.owner.value:
                    # add var to group dict
                    upd_group_dict['_var_list'].append(upd_ls)

                else:
                    if self.debug:
                        self.debug_value(-24, f'cb_changed()',
                                         f'upd_ls = {upd_ls}',
                                         f'upd_group_dict = {upd_group_dict}')
                    # Remove var from var group
                    upd_group_dict['_var_list'].remove(upd_ls)

                set_temp_dict(upd_group_dict)
                set_upd_variables()

        def set_upd_variables(mode=None, var_list=None):
            if mode == 'new':
                group_vars_upd.value = ''
            else:
                group_vars_upd.value = get_group_var_text(upd_mode=True,
                                                          var_list=var_list)

        def group_name_changed(change):

            if self.debug:
                self.debug_value(-25, 'group_name_changed() *** start ***')

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
                self.debug_value(-26, 'new_group() ')

            upd_group_dict = {'_upd_mode': 'new',
                              '_group_name': 'Group name',
                              '_var_list': []}

            set_temp_dict(upd_group_dict)

            group_name.value = 'Group name'
            set_upd_variables('new')
            activate_gui('new')

        def update_group(click):
            if self.debug:
                self.debug_value(-27, 'update_group() ')

            grp = group_drop.value
            cache = self._load_cache()
            var_ls = cache['_groups'][grp]['_group_vars']
            upd_group_dict = {'_upd_mode': 'update',
                              '_group_name': grp,
                              '_saved_group_name': grp,
                              '_var_list': var_ls}
            set_temp_dict(upd_group_dict)
            group_name.value = grp
            set_upd_variables('update', var_ls)
            activate_gui('update')

        def save_group(click):
            cache = self._load_cache()

            upd_group_dict = get_temp_dict()
            if self.debug:
                self.debug_value(-28, 'save_group() ',
                                 f'cache.keys(): {cache.keys()}',
                                 f'upd_group_dict: {upd_group_dict}')

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
                display_user_guide('display_guide')
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
                self.debug_value(-29, 'delete_group() ')

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
                error_ls.append(f'<b>Name error</b><br> {name_error}')

            if var_error:
                error_ls.append(f'<b>Variable error</b><br> {var_error}')

            if error_ls:
                error_ls.append('<br>To delete a group of variables:')
                error_ls.append(' 1. Select the group.')
                error_ls.append(' 2. Press <i>Update</i>')
                error_ls.append(' 3. Press <i>Delete</i>')
                error_ls.append('Don\'t change the content.')
                upd_group_dict['_delete_errors'] = error_ls
                set_temp_dict(upd_group_dict)
                display_user_guide('display_guide')
            else:
                upd_group_dict['_upd_mode'] = 'delete'
                update_cache(upd_group_dict)
                init()
                set_group_vars('')
                activate_gui('del')

        def cancel_group(click):
            if self.debug:
                self.debug_value(-30, 'cancel_group() ')
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

        def set_info_msg(upd_mode: str = None,
                         error_ls: list = None):
            """
                Messages on what to do and errors
            """
            if not upd_mode:
                upd_group_dict = get_temp_dict()
                upd_mode = upd_group_dict.get('_upd_mode', None)

            if upd_mode == 'new':
                msg = self.help_dict['group']['new_header']
                msg += self.help_dict['group']['new_body']
            elif upd_mode == 'update':
                msg = self.help_dict['group']['update_header']
                msg += self.help_dict['group']['update_body']
            else:
                msg = self.help_dict['group']['read_header1']
                msg += self.help_dict['group']['read_body1']
                msg += self.help_dict['group']['read_header2']
                msg += self.help_dict['group']['read_body2']
                msg += self.help_dict['group']['read_header3']
                msg += self.help_dict['group']['read_body3']
            msg += self.help_dict['group']['general']

            info_color = self.widget_style_colors['primary:active']
            msg = f'<span style="color:{info_color}">' \
                  f'{msg}</span>'

            if error_ls:
                margin = '&nbsp' * 3
                warning_emoji = '\u26a0\ufe0f'
                error_color = self.widget_style_colors['danger:active']

                err_msg = f'<span style="color:{error_color}">' \
                          f'<hr>{margin}{margin}'
                if error_ls[0] == 'ACTION':
                    err_msg += f'<h3>{warning_emoji} {error_ls[1]}' \
                               f' {warning_emoji} </h3><b>'
                    error_ls = error_ls[2:]
                else:
                    err_msg += f'<h3>To do: {warning_emoji}</h3><b>'

                for error in error_ls:
                    err_msg += f'{margin}{error}<br>'
                err_msg += '</b></span><hr>'
                msg = msg + err_msg

            user_guide.value = msg

            if error_ls and user_guide_container.layout.display == 'none':
                display_user_guide('display_guide')

        def set_reset_error_msg():
            upd_group_dict = get_temp_dict()
            error_ls = []
            for k in ['_name_error', '_var_error', '_delete_errors']:
                error_ls += upd_group_dict.get(k, [])

            set_info_msg(upd_mode=upd_group_dict.get('_upd_mode', None),
                         error_ls=error_ls)

        # ********************************
        # activate/deactivate upd-widgets
        def activate_gui(upd_active):
            if self.debug:
                self.debug_value(-31, 'activate_gui() ',
                                 f'upd_active = {upd_active}')
            set_info_msg(upd_mode=upd_active)

            if upd_active in ['new', 'update']:
                # update mode
                # init update widgets..
                update_group_btn.on_click(update_group, remove=True)
                new_group_btn.on_click(new_group, remove=True)
                save_group_btn.on_click(save_group, remove=False)
                delete_group_btn.on_click(delete_group, remove=False)
                cancel_group_btn.on_click(cancel_group, remove=False)
                var_info_btn.on_click(display_var_info, remove=False)

                set_station_drop()
                set_prod_drop(upd_active)
                set_var_checkboxes('')

                station_drop.observe(set_prod_drop, names='value')
                product_drop.observe(set_var_checkboxes, names='value')
                var_drop.observe(set_var_info_text, names='value')

                group_name.observe(group_name_changed, 'value')
                group_name.style.text_color = 'darkgreen'

                upd_box.layout.display = 'flex'

                for b in create_btns.children:
                    b.tooltip = 'Disabled in update mode...'
                    b.disabled = True
                group_drop.disabled = True
                save_group_btn.disabled = False
                cancel_group_btn.disabled = False
                var_info_btn.disabled = False
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

                station_drop.unobserve(set_prod_drop)
                product_drop.unobserve(set_var_checkboxes)
                var_drop.unobserve(set_var_info_text)
                group_name.unobserve(group_name_changed)
                var_info_container.layout.display = 'none'

                upd_box.layout.display = 'none'
                for b in create_btns.children:
                    b.disabled = False
                    update_group_btn.disabled = no_groups
                group_drop.disabled = False
                new_group_btn.tooltip = 'New group...'
                update_group_btn.tooltip = 'Update group...'
                var_info_btn.disabled = True

                for b in non_create_btns.children:
                    b.tooltip = 'Enabled in update mode...'
                    b.disabled = True
                group_dict_log.value = ''

        # Main of edit group vars
        # ====

        # Get station and product data
        st_df = self.stations_df

        # Layouts

        label_layout = wd.Layout(width='auto', min_width='125px')

        # row 1
        group_label = wd.HTML('<b><i>Available groups: </i></b>',
                              layout=wd.Layout(width='auto'))
        group_drop = wd.Dropdown(layout=wd.Layout(width='auto',
                                                  height='40px'),
                                 description_tooltip='Group name')
        group_box = wd.HBox([group_label, group_drop])

        group_vars = wd.HTML(layout=wd.Layout(width='auto',
                                              max_width='90%',
                                              height='100%'),
                             value='Variables: ',
                             disabled=True)
        g_vars = wd.Accordion([group_vars],
                              titles=(group_vars.value, '0'),
                              selected_index=None,
                              layout=wd.Layout(width='50%',
                                               height='100%'))
        rows = [wd.HBox([group_box, g_vars])]

        # row 2
        # Create group buttons
        new_group_btn = wd.Button(description='New', icon='plus',
                                  button_style='primary',
                                  layout=wd.Layout(width='100px'))
        update_group_btn = wd.Button(description='Update', icon='pen',
                                     button_style='info',
                                     layout=wd.Layout(width='100px'))
        save_group_btn = wd.Button(description='Save', icon='save',
                                   button_style='success',
                                   layout=wd.Layout(width='100px'))
        cancel_group_btn = wd.Button(description='Cancel', icon='ban',
                                     button_style='info',
                                     layout=wd.Layout(width='100px'))
        delete_group_btn = wd.Button(description='Delete', icon='trash',
                                     button_style='danger',
                                     layout=wd.Layout(width='100px'))
        create_btns = wd.HBox([new_group_btn, update_group_btn])

        user_guide_btn = wd.Button(description='User guide',
                                   disabled=False,
                                   icon='fa-info-circle',
                                   button_style='info',
                                   tooltip='Display or hide User guide',
                                   layout=wd.Layout(width='100px'))
        user_guide_btn.on_click(display_user_guide)

        var_info_btn = wd.Button(description='Var. info',
                                 icon='fa-info-circle',
                                 button_style='info',
                                 layout=wd.Layout(width='100px'))

        non_create_btns = wd.HBox([save_group_btn,
                                   cancel_group_btn,
                                   delete_group_btn])
        rows.append(wd.HBox([create_btns, non_create_btns,
                             user_guide_btn, var_info_btn]))

        # row 3 - guides
        # Help text for user
        user_guide = wd.HTMLMath(disabled=True,
                                 layout=wd.Layout(width='90%',
                                                  height='auto'))
        user_guide_container = wd.Accordion(selected_index=None,
                                            layout=wd.Layout(width='auto',
                                                             min_width='45%',
                                                             height='auto',
                                                             display='none'))
        group_dict_log = wd.Textarea(disabled=True)

        if self.debug:
            user_guide_container.children = [wd.VBox([user_guide,
                                                      group_dict_log])]
        else:
            user_guide_container.children = [wd.VBox([user_guide])]
        user_guide_container.set_title(0, 'User guide')
        # Variable info-text
        var_drop = wd.Dropdown(layout=wd.Layout(width='auto',
                                                max_width='148px'))
        var_info_text = wd.HTML(layout=wd.Layout(width='100%',
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
        rows.append(wd.HBox([user_guide_container, var_info_container]))

        # upd row 1-2
        station_label = wd.HTML('<b><i>ICOS Stations: </i></b>',
                                layout=label_layout)
        station_drop = wd.Dropdown(layout=wd.Layout(width='auto',
                                                    min_width='148px',
                                                    height='40px'),
                                   description_tooltip='ICOS Station')
        station_box = wd.VBox([station_label, station_drop])

        product_label = wd.HTML('<b><i>Files of station: </i></b>',
                                layout=label_layout)
        product_drop = wd.Dropdown(layout=wd.Layout(width='auto',
                                                    min_width='148px',
                                                    height='40px'),
                                   description_tooltip='File name')
        product_box = wd.VBox([product_label, product_drop])

        drop_box = wd.HBox([station_box, product_box],
                           layout=wd.Layout(width='auto',
                                            max_width='100%',
                                            display='inline-flex',
                                            flex_flow='row wrap',
                                            align_content='flex-start'))

        # Group stuff  n(children=[page1, page2], width=400)
        group_name_label = wd.HTML('<b><i>Name of group: </i></b>',
                                   layout=label_layout)
        group_name = wd.Text(layout=wd.Layout(width='auto'))
        left_upd_box = wd.VBox([drop_box,
                                group_name_label,
                                group_name],
                               layout=wd.Layout(width='auto',
                                                min_width='25%'))
        html_margin = wd.HTML(layout=wd.Layout(width='2%',
                                               min_width='10px'))

        group_var_label = wd.HTML('<b><i>Variables in update mode: </i></b>',
                                  layout=wd.Layout(width='auto',
                                                   min_width='150px'))
        group_vars_upd = wd.HTML(layout=wd.Layout(width='auto',
                                                  min_width='50%',
                                                  max_width='90%',
                                                  height='100%'),
                                 disabled=True)
        right_upd_box = wd.VBox([group_var_label,
                                 group_vars_upd],
                                layout=wd.Layout(width='67%'))
        upd_rows = [wd.HBox([left_upd_box,
                             html_margin,
                             right_upd_box])]

        # upd row 3
        # Container for checkboxes
        var_label = wd.HTML(style=dict(text_color='darkgreen'))
        var_cbs_box = wd.HBox(layout=wd.Layout(border='dashed 0.5px',
                                               width='100%',
                                               display='inline-flex',
                                               flex_flow='row wrap',
                                               align_content='flex-start'))
        var_box = wd.VBox([var_label, var_cbs_box])
        upd_rows.append(var_box)
        upd_box = wd.VBox(upd_rows)

        error_out = wd.Output()

        # observe choices
        group_drop.observe(set_group_vars, names='value')

        # Init widgets
        init()

        if not self.debug:
            group_dict_log.layout.display = 'None'

        display(wd.VBox([wd.VBox(rows), upd_box, error_out]))
