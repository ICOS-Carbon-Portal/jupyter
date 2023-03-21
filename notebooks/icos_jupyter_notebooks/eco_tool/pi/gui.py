#!/usr/bin/python

"""
    This is the main entry to run the Ecosystem notebook for PIs.

    edit_group_variables()
    tools()

    Examples
    --------
    >>> from pi import gui
    >>> g = gui.AnalysisGui()
    ...
"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.2"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import warnings
import pandas as pd
from ipywidgets import widgets as wd, HBox, VBox, Layout
from IPython.display import display, clear_output

warnings.simplefilter("ignore", FutureWarning)
from icoscp.cpb.dobj import Dobj
from pi import icos_data, plot
from pi import cache as cache_manager


class AnalysisGui:
    # Colors of ipywidgets predefined styles
    ipyw_style_colors = {'text_color': '#FFFFFF',
                         'primary': '#2196F3',
                         'primary:active': '#1976D2',
                         'success': '#4CAF50',
                         'success:active': '#388E3C',
                         'info:active': '#0097A7',
                         'warning': '#FF9800',
                         'warning:active': '#F57C00',
                         'danger': '#F44336',
                         'danger:active': '#D32F2F'}

    def _help(self):
        # static help.
        with open('./pi/images/Groupmenu.png', 'rb') as f:
            groupmenu = f.read()
        group_img = wd.Image(value=groupmenu)
        group_img.layout.height = '28px'

        user_guide = wd.HTMLMath(disabled=True,
                                 layout=Layout(width='auto', height='auto'))
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

    def _edit_group_variables(self):

        debug = self.debug

        def load_cache():

            try:
                c = cache_manager.read(json_file=self.json_file,
                                       settings_dir=self.settings_dir)
            except:
                # broken cache
                pass

            if not c:
                c = {'_last_station': '',
                     '_last_group': '',
                     '_groups': {'_labels': []}}

            return c

        def update_cache(group_dict):
            if debug:
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
            # {'_last_station': 'Hyltemossa', 
            #  '_last_group': 'Group 1',
            #  '_groups': {'_labels': ['Group 1', 'LCA', 'Another group'],
            #              'Group 1': [['SWC_1', 'ETC NRT Meteo','Hyltemossa'], 
            #                          ['SWC_2', 'ETC NRT Meteo','Hyltemossa'], 
            #                          ['SWC_3', 'ETC NRT Meteo','Hyltemossa']],
            #              'LCA' : [['LE','ETC NRT Fluxes','Hyltemossa'], 
            #                       ['LE_UNCLEANED','ETC NRT Fluxes','Hyltemossa'],
            #                       ['NEE','ETC NRT Fluxes','Hyltemossa'], 
            #                       ['NEE_UNCLEANED','ETC NRT Fluxes','Hyltemossa']],
            #              'Another group': [['SWC_1', 'ETC NRT Meteo','Hyltemossa'], 
            #                                ['SWC_2', 'ETC NRT Meteo','Hyltemossa'], 
            #                                ['SWC_3', 'ETC NRT Meteo','Hyltemossa'],
            #                                ['LE','ETC NRT Fluxes','Hyltemossa'], 
            #                                ['LE_UNCLEANED','ETC NRT Fluxes','Hyltemossa'], 
            #                                ['NEE','ETC NRT Fluxes','Hyltemossa'], 
            #                                ['NEE_UNCLEANED','ETC NRT Fluxes','Hyltemossa']]}}

            if '_change' not in group_dict.keys() or '_group_name' not in group_dict.keys():
                return

            grp = group_dict['_group_name']
            var_ls = group_dict['_var_list']

            if group_dict['_change'] == 'new':
                cache['_groups']['_labels'].append(grp)
                cache['_groups'][grp] = var_ls
                # update "last"-flags
                last_var = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station'] = last_var[2]

            elif group_dict['_change'] == 'update':
                if '_saved_group_name' in group_dict.keys():
                    old_grp = group_dict['_saved_group_name']

                    if grp != old_grp:
                        cache['_groups']['_labels'].remove(old_grp)
                        cache['_groups'].pop(old_grp)
                if grp not in cache['_groups']['_labels']:
                    cache['_groups']['_labels'].append(grp)
                cache['_groups'][grp] = var_ls
                # update "last"-flags
                last_var = var_ls[-1]
                cache['_last_group'] = grp
                cache['_last_station'] = last_var[2]

            elif group_dict['_change'] == 'delete':
                if grp in cache['_groups']['_labels']:
                    cache['_groups']['_labels'].remove(grp)
                    last_var = cache['_groups'].pop(grp)
                    if cache['_last_group'] == grp:
                        # change to the last group data, if possible
                        if len(cache['_groups']['_labels']) > 0:
                            last_group = cache['_groups']['_labels'][-1]
                            cache['_last_group'] = last_group
                            last_group_vars = cache['_groups'][last_group]
                            cache['_last_station'] = last_group_vars[-1][2]
                        else:
                            cache['_last_group'] = ''
                            cache['_last_station'] = ''

            cache_manager.write(data=cache,
                                json_file_name=self.json_file,
                                settings_dir=self.settings_dir)

        def init():

            val = set_group_drop('')

            if val == 'first_run':
                create_group(val)
                display_user_guide('display_guide')
            else:
                activate_gui('init_read_mode')

        def set_station_drop():
            if debug:
                print('set_station_drop()', cache.keys())

            id_ls = list(st_df.id)
            name_ls = list(st_df.name)
            station_ls = list(set(zip(name_ls, id_ls)))
            station_ls.sort(key=lambda v: v[0].lower())

            # Try to use station from last added variable
            upd_dict = get_temp_dict()
            try:
                stn = upd_dict['_var_list'][-1][2]
            except:
                # This is the case for a new group
                # try to use the last station
                try:
                    stn = cache['_last_station']
                except:
                    # This is the case if there are no groups or 
                    # if the last used group was deleted
                    stn = None
            finally:
                if not stn:
                    station_ls.insert(0, ('Choose a station', 'dummy'))
                    stn = 'dummy'
                elif station_ls[0] == ('Choose a station', 'dummy'):
                    station_ls.pop(0)
                station_drop.options = station_ls
                station_drop.value = stn

        def set_spec_drop(change):

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
                last_spec_in_var_list = cache['_groups'][grp][-1][1]
                spec_drop.value = [y[1] for y in spec_drop_ls if
                                   y[0] == last_spec_in_var_list].pop()
            elif isinstance(change, dict) and change['new']:
                grp = change['new']
                try:
                    last_spec_in_var_list = cache['_groups'][grp][-1][1]
                    spec_drop.value = [y[1] for y in spec_drop_ls if
                                       y[0] == last_spec_in_var_list].pop()
                except:
                    pass
            else:
                spec_drop.value = spec_drop.options[0][1]

            if not spec_drop.value:
                spec_drop.value = spec_drop.options[0][1]

        def set_var_drop(change):
            if debug:
                print('set_var_drop()', cache.keys())

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
            if debug:
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
            if debug:
                print('set_group_drop()', cache.keys())

            # load from cache
            if isinstance(cache, dict):
                try:
                    group_drop.options = cache['_groups']['_labels']
                    group_drop.value = cache['_last_group']
                except:
                    # broken cache
                    pass

            if not group_drop.options:
                group_drop.options = ['No groups loaded...']
                group_drop.value = group_drop.options[0]
                group_drop.disabled = True
                return 'first_run'
            return ''

        def set_group_vars(c):
            if debug:
                print('set_group_vars', cache.keys())

            if isinstance(cache, dict):
                try:
                    grp = group_drop.value
                    if grp not in cache['_groups'].keys():
                        grp = ''
                        # Container title...
                        cont_title = f'Content of a group goes here'
                        g_vars.set_title(0, cont_title)
                        group_vars.value = 'Variables: '

                        return

                    var_tuples = cache['_groups'][grp]
                    var_ls = [v[0] for v in var_tuples]

                    station_dict = {}
                    for v in var_tuples:
                        if v[2] in station_dict.keys():
                            if v[1] in station_dict[v[2]].keys():
                                station_dict[v[2]][v[1]].append(v[0])
                            else:
                                station_dict[v[2]][v[1]] = [v[0]]
                        else:
                            station_dict[v[2]] = {v[1]: [v[0]]}

                    var_text = ''

                    for stn in station_dict.keys():
                        if len(station_dict.keys()) == 1:
                            for spec in station_dict[stn].keys():
                                if len(station_dict[stn].keys()) == 1:
                                    var_text = f'Variables (of {spec} at {stn}): ' + ', '.join(
                                        var_ls)
                                elif var_text:
                                    var_text += f'; {spec}: {", ".join(station_dict[stn][spec])}'
                                else:
                                    var_text = f'Variables (of {stn}): ' + ', '.join(
                                        var_ls) + f' ({spec}: {", ".join(station_dict[stn][spec])}'
                            if len(station_dict[stn].keys()) > 1:
                                var_text += ')'

                        else:
                            for spec in station_dict[stn].keys():
                                if var_text == '':
                                    prsent_station = stn
                                    var_text = f'Variables: ' + ', '.join(
                                        var_ls) + f' (({stn}) {spec}: {", ".join(station_dict[stn][spec])}'
                                elif stn == prsent_station:
                                    var_text += f'; {spec}: {", ".join(station_dict[stn][spec])}'
                                else:
                                    var_text += f' || ({stn}) {spec}: {", ".join(station_dict[stn][spec])}'
                    if len(station_dict.keys()) > 1:
                        var_text += ')'

                    # Container title...
                    cont_title = f'Content of group {grp}'
                    g_vars.set_title(0, cont_title)
                    group_vars.value = var_text
                except:
                    # Container title...
                    cont_title = f'Content of a group goes here'
                    g_vars.set_title(0, cont_title)
                    group_vars.value = 'Variables: '
            else:
                # Container title...
                cont_title = f'Content of a group goes here'
                g_vars.set_title(0, cont_title)
                group_vars.value = 'Variables: '

        def set_var_checkboxes(c):
            # Ceckboxes for variables

            if debug:
                print('set_var_checkboxes()\t', cache.keys())

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
                try:
                    grp = group_drop.label
                    if grp in cache['_groups']:
                        var_ls = cache['_groups'][grp].copy()
                except:
                    var_ls = []

            selected_ls = [y[0] for y in var_ls if
                           y[1] == spec and y[2] == station]

            checkbox_ls = []
            for var_option in var_drop.options:
                var = var_option[0]
                var_selected = bool(var in selected_ls)
                cb = wd.Checkbox(description=var, value=var_selected,
                                 disabled=False, indent=False,
                                 layout=Layout(width='160px'))
                checkbox_ls.append(cb)
                cb.observe(cb_changed)

            var_cbs_box.children = checkbox_ls

        def get_temp_dict():

            if debug:
                print('get_temp_dict()\t', group_dict_log.value)

            temp_log = group_dict_log.value
            if temp_log:
                upd_group_dict = eval(temp_log)
            else:
                upd_group_dict = dict()

            return upd_group_dict

        def set_temp_dict(upd_dict):

            if debug:
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

            ls = str(group_vars_upd.value).split('Variables in update mode: ')
            var_widget_ls = ls[1].split(', ')

            if cb.name == 'value':

                var_name = str(cb.owner.description)

                upd_ls = [var_name, spec_drop.label, station_drop.value]

                # Load group dict 
                upd_group_dict = get_temp_dict()

                if cb.owner.value:
                    # 1. add var to var widget list
                    var_widget_ls.append(var_name)

                    # 2. add var to group dict
                    upd_group_dict['_var_list'].append(upd_ls)

                else:
                    # 1. Remove var from var widget list
                    var_widget_ls.remove(var_name)

                    # 2. Remove var from var group
                    upd_group_dict['_var_list'].remove(upd_ls)

                set_temp_dict(upd_group_dict)

                if '' in var_widget_ls:
                    var_widget_ls.remove('')
                group_vars_upd.value = 'Variables in update mode: ' + ', '.join(
                    var_widget_ls)

        def group_name_changed(change):

            if debug:
                print('group_name_changed()\t', cache.keys())

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
            if debug:
                print('create_group()\t', cache.keys())

            upd_group_dict = {'_change': 'new',
                              '_group_name': 'Group name',
                              '_var_list': []}

            set_temp_dict(upd_group_dict)

            group_vars_upd.value = 'Variables in update mode: '
            group_name.value = 'Group name'

            activate_gui('new')

        def update_group(click):

            if debug:
                print('update_group()\t', cache.keys())

            grp = group_drop.value
            upd_group_dict = {'_change': 'update',
                              '_group_name': grp,
                              '_saved_group_name': grp,
                              '_var_list': cache['_groups'][grp]}

            set_temp_dict(upd_group_dict)

            vars_to_update = \
                f'Variables in update mode:{group_vars.value.split(":")[1]}'.split(
                    " (")[0]
            group_vars_upd.value = vars_to_update
            group_name.value = grp

            activate_gui('update')

            return

        def save_group(click):
            nonlocal cache

            upd_group_dict = get_temp_dict()
            if debug:
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
                cache = load_cache()
                init()
                set_group_vars('')
                activate_gui('save')

        def delete_group(click):

            if debug:
                print('save_group()\t', cache.keys())

            # Note: The delete btn is only available in update mode: 'update'
            upd_group_dict = get_temp_dict()

            grp = upd_group_dict['_group_name']
            old_grp_name = upd_group_dict['_saved_group_name']

            error_ls = []
            if grp != old_grp_name:
                error_ls.append('To delete a group don\'t change it\'s name.')

            if old_grp_name in cache['_groups']['_labels'] and old_grp_name in \
                    cache['_groups'].keys():
                if upd_group_dict['_var_list'] != cache['_groups'][old_grp_name]:
                    error_ls.append(
                        'To delete a group don\'t change it\'s name or the variables.')

            if error_ls:
                error_ls.append(
                    'Try to <i>Cancel</i>, <i>Update</i> and <i>Delete</i>,')
                error_ls.append('without changing the content.')
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
            if debug:
                print('cancel_group()\t', cache.keys())

            activate_gui('cancel')

        # Validations     
        def validate_name(upd_dict, grp_name):

            upd_mode = upd_dict['_change']

            error_ls = []

            # Validate suggested name
            if not grp_name or grp_name == 'Group name':
                error_ls.append(
                    'Please, choose a name for the group of variables.')
            elif not grp_name[0].isalnum():
                error_ls.append('At least the first letter of the group')
                error_ls.append('name must be an alfa numeric character.')
            elif grp_name in cache['_groups']['_labels']:
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

            margin = '&nbsp&nbsp&nbsp'

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
                msg += f'<br><span style="color:{error_color}">{margin}{margin}<h3>To do: {warning_emoji}</h3><b>'
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
            if debug:
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
                # group_vars_upd.observe(set_var_checkboxes,'value')

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
                no_groups = not cache['_groups']['_labels']
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

        # Main
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
        var_drop = wd.Dropdown(layout=Layout(width='148pt',
                                             flex='inline-flex',
                                             align="flex-end"))

        # Group stuff  n(children=[page1, page2], width=400)
        group_vars = wd.HTML(layout=var_txt_layout,
                             value='Variables: ',
                             disabled=True)
        g_vars = wd.Accordion([group_vars],
                              titles=(group_vars.value, '0'),
                              selected_index=None,
                              layout=Layout(width='100%', height='100%'))
        group_vars_upd = wd.HTML(layout=var_txt_layout,
                                 value='Variables in update mode: ',
                                 disabled=True,
                                 style={'text_color': 'darkgreen'})
        group_name = wd.Text(layout=grp_txt_layout)
        group_dict_log = wd.Textarea(
            disabled=True)  # layout = Layout(display = 'none'))

        # Container for checkboxes
        var_label = wd.HTML()
        var_cbs_box = HBox(layout=Layout(border='dashed 0.5px',
                                         width='100%',
                                         display='inline-flex',
                                         flex_flow='row wrap',
                                         align_content='flex-start'))
        var_box = VBox([var_label, var_cbs_box])

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
        create_btns = HBox([create_group_btn, update_group_btn])

        help_btn = wd.Button(description='User guide',
                             icon='fa-info-circle',
                             button_style='info')
        var_info_btn = wd.Button(description='Variable',
                                 icon='fa-info-circle',
                                 button_style='info')

        non_create_btns = HBox(
            [save_group_btn, cancel_group_btn, delete_group_btn])
        btns = HBox([create_btns, non_create_btns, help_btn, var_info_btn])

        # Variable info-text
        var_info_text = wd.HTML(layout=Layout(width='100%',
                                              max_width='90%',
                                              height='auto'))
        # Text to user
        user_guide = wd.HTMLMath(disabled=True,
                                 layout=Layout(width='90%',
                                               max_width='90%',
                                               height='auto'))

        var_info_container = wd.Accordion(children=[VBox([var_drop,
                                                          var_info_text])],
                                          selected_index=None,
                                          layout=Layout(width='auto',
                                                        min_width='45%',
                                                        height='auto',
                                                        display='none'))
        var_info_container.set_title(0, 'Variable info')

        user_guide_container = wd.Accordion(selected_index=None,
                                            layout=Layout(width='auto',
                                                          min_width='45%',
                                                          height='auto',
                                                          display='none'))
        user_guide_container.set_title(0, 'User guide')

        if debug:
            user_guide_container.children = [VBox([user_guide,
                                                   group_dict_log])]
        else:
            user_guide_container.children = [VBox([user_guide])]

        upd_box = VBox([HBox([station_drop, spec_drop]),
                        HBox([user_guide_container, var_info_container]),
                        HBox([group_name, group_vars_upd]),
                        var_box])

        # observe choices
        group_drop.observe(set_group_vars, names='value')

        # Init cache dict
        cache = load_cache()

        # Init widgets
        init()

        if not debug:
            group_dict_log.layout.display = 'None'

        display(VBox([HBox([group_drop, g_vars]), btns, upd_box]))

    def _tools(self, group_cache):
        # run part

        def load_cache(group_cache=None):

            if not group_cache:
                try:
                    group_cache = cache_manager.read(json_file=self.json_file,
                                                     settings_dir=self.settings_dir)
                except:
                    # broken cache
                    pass

            if not group_cache:
                group_cache = {'_last_station': '',
                               '_last_group': '',
                               '_groups': {'_labels': []}}

            if '_tools' not in group_cache.keys():
                group_cache['_tools'] = {}

            # If there is a group we set some default values for the tools.
            # '_last_run': '2' means that the last "run" used the settings in '2'
            # and '2': ['Split plot', 2 ,5], says that the setting use 
            # - The tool: 'Split plot' 
            # - with a slider after every second variable of the group
            # - The data is 5 days back until now. 
            for x in group_cache['_groups']['_labels']:
                if x not in group_cache['_tools']:
                    group_cache['_tools'][x] = {'_last_run': '2',
                                                '1': ['Split plot', 5, 7],
                                                '2': ['Split plot', 2, 5]}
            return group_cache

        def set_gui():

            # set group drop

            if cache['_groups']['_labels']:
                group_drop.options = cache['_groups']['_labels']
            else:
                group_drop.options = ['No groups loaded...']

            if cache['_last_group'] and cache[
                '_last_group'] in group_drop.options:
                group_drop.value = cache['_last_group']
            else:
                group_drop.value = group_drop.options[0]

            group_drop.disabled = False

            # tool settings 
            try:
                grp = group_drop.value
                last_settings = cache['_tools'][grp]['_last_run']
                setting_ls = [x for x in cache['_tools'][grp][last_settings]]
                tool_drop.value = setting_ls[0]
                plot_sliders.value = setting_ls[1]
                days.value = setting_ls[2]
            except:
                tool_drop.value = tool_drop.options[0]
                plot_sliders.value = 5
                days.value = 5
            tool_settings('')

        def tool_settings(change):
            # The toggle buttons are settings for what to run and how. 
            # Example: a plot with sliders for every 3:ed variable, 
            #          with a perspective for 7 days back.

            grp = group_drop.value

            if change == '':
                # Init the toggle buttons on what to run

                if not grp in cache['_tools'].keys():
                    return

                    # Note the space...
                selected_setting = cache['_tools'][grp]['_last_run'] + ' '

                # Note we add a space to the label in order to have a nice icon for selection
                tool_ls = [str(x) + ' ' for x in cache['_tools'][grp].keys() if
                           x != '_last_run']
                tool_buttons.options = tool_ls
                tool_buttons.value = selected_setting
                tool_buttons.style.button_width = "50px"
                tool_buttons.tooltip = 'settings'
            else:
                selected_setting = change['new']
                tool_ls = tool_buttons.options

                # Set the values for the choice
                setting_ls = [x for x in cache['_tools'][grp][selected_setting]]
                tool_drop.value = setting_ls[0]
                plot_sliders.value = setting_ls[1]
                days.value = setting_ls[2]

            # Finallys we set the icons according to selection (we do this 
            # because it is hard to detect if there are only two choices...)
            selected_index = tool_ls.index(selected_setting)
            icons_ls = ['square-o'] * (len(tool_ls) - 1)
            icons_ls.insert(selected_index, 'check-square-o')
            tool_buttons.icons = icons_ls

        def get_data():
            grp = group_drop.value
            var_tuple_ls = cache['_groups'][grp]
            stations = {x[2] for x in var_tuple_ls}

            data_dict = {}
            for stn in stations:
                data_dict[stn] = {}
                data_dict[stn]['id'] = st_df.loc[(st_df.id == stn)].id.values[0]
                speces = {x[1] for x in var_tuple_ls if x[2] == stn}
                for spec in speces:
                    data_dict[stn][spec] = {}
                    pid = st_df.loc[(st_df.id == stn) & (
                            st_df.specLabel == spec)].dobj.values[0]

                    # variables of pid
                    var_ls = [x[0] for x in var_tuple_ls if
                              x[2] == stn and x[1] == spec]
                    data_dict[stn][spec]['vars'] = var_ls

                    do = Dobj(pid)
                    df = do.data
                    cols = var_ls + ['TIMESTAMP']
                    data_dict[stn][spec]['data'] = df[cols]

                    col_meta_ls = do.meta['specificInfo'][
                        'columns'] if 'specificInfo' in do.meta.keys() and 'columns' in \
                                      do.meta['specificInfo'] else None

                    var_meta = {}
                    for v in var_ls:
                        for col in col_meta_ls:
                            if col['label'] == v:
                                var_meta[v] = {}
                                try:
                                    var_meta[v]['unit'] = col['valueType']['unit']
                                except:
                                    var_meta[v]['unit'] = 'No unit'
                                try:
                                    label = col['valueType']['quantityKind'][
                                        'label']
                                    var_meta[v]['label'] = label[
                                                               0].upper() + label[
                                                                            1:]
                                except:
                                    var_meta[v]['label'] = ''
                    data_dict[stn][spec]['meta'] = var_meta

            # Rename columns if there are stations or products involved
            # Are the more than 1 station?
            if len(data_dict.keys()) > 1:
                for stn in data_dict.keys():
                    stn_short = data_dict[stn]['id']

                    # are there more than one speces?
                    if len(data_dict[stn].keys()) > 2:
                        for spec in data_dict[stn]:
                            if spec != 'id':
                                spec_short = spec.split(' ')[-1]

                                new_col_names = {
                                    var: f'{stn_short}_{spec_short}_{var}'
                                    for var in data_dict[stn][spec]['vars']
                                    if var != 'TIMESTAMP'}
                                # new_col_names['TIMESTAMP'] = 'TIMESTAMP'

                                df = data_dict[stn][spec]['data']
                                data_dict[stn][spec]['data'] = df.rename(
                                    columns=new_col_names)

                    else:
                        for spec in data_dict[stn]:
                            if spec != 'id':
                                new_col_names = {var: f'{stn_short}_{var}'
                                                 for var in
                                                 data_dict[stn][spec]['vars']
                                                 if var != 'TIMESTAMP'}
                                # "new_col_names['TIMESTAMP'] = 'TIMESTAMP'

                                df = data_dict[stn][spec]['data']
                                data_dict[stn][spec]['data'] = df.rename(
                                    columns=new_col_names)
            else:
                for stn in data_dict.keys():
                    # are there more than one speces?
                    if len(data_dict[stn].keys()) > 2:
                        for spec in data_dict[stn]:
                            if spec != 'id':
                                spec_short = spec.split(' ')[-1]
                                new_col_names = {var: f'{spec_short}_{var}'
                                                 for var in
                                                 data_dict[stn][spec]['vars']
                                                 if var != 'TIMESTAMP'}

                                df = data_dict[stn][spec]['data']
                                data_dict[stn][spec]['data'] = df.rename(
                                    columns=new_col_names)

            return data_dict

        def run(c):
            data_dict = get_data()

            # TODO: fix meta....
            df = pd.DataFrame()
            for stn in data_dict.keys():
                for spec in data_dict[stn].keys():
                    if spec != 'id':
                        if df.empty:
                            df = data_dict[stn][spec]['data']
                        else:
                            df = df.merge(data_dict[stn][spec]['data'],
                                          how='inner', on='TIMESTAMP')

            df.set_index('TIMESTAMP', inplace=True, drop=True)

            if tool_drop.value == 'Split plot':
                with out:
                    clear_output()
                    plot.multi_plot(df, int(plot_sliders.value)).show()

        def save():
            cache_manager.write(data=cache,
                                json_file_name=self.json_file,
                                settings_dir=self.settings_dir)
            load_cache()

        # Layouts
        drop_layout = wd.Layout(width='148pt%', height='30px')
        right_aligned_column = Layout(display='flex',
                                      # Possible values of display:flex, grid
                                      flex_flow='column',
                                      # Pos. values of flex_flow:row,column
                                      align_items='flex-end')  # Pos values of align_items: center, flex-start, flex-end, stretch

        # Dropdowns
        group_drop = wd.Dropdown(description='Groups', layout=drop_layout)
        tool_drop = wd.Dropdown(description='Tools',
                                options=['Split plot',
                                         'Correlation plot',
                                         'Correlation table'],
                                layout=drop_layout)
        plot_sliders = wd.IntSlider(description="Plot sliders",
                                    min=0,
                                    max=10,
                                    step=1,
                                    layout=drop_layout)
        days = wd.Dropdown(description="Days",
                           options=range(1, 100),
                           layout=drop_layout)
        tool_buttons = wd.ToggleButtons(button_style="success",
                                        tooltip='settings')
        add_btn = wd.Button(description='Add setting',
                            icon='plus',
                            button_style='primary')
        save_btn = wd.Button(description='Save setting',
                             icon='save',
                             button_style='success')
        info_btn = wd.Button(description='Info',
                             icon='fa-info-circle',
                             button_style='info')

        toolbox = wd.VBox([wd.HBox([tool_buttons]), wd.HBox([save_btn, add_btn])])

        run_btn = wd.Button(description="Run", icon='area-chart',
                            button_style='success')  #####, layout=center_layout)

        st_df = self.stations_df
        cache = load_cache()
        set_gui()

        # observe changes
        run_btn.on_click(run)
        tool_buttons.observe(tool_settings, "value")
        out = wd.Output()

        display(
            VBox([HBox([VBox([group_drop, run_btn], layout=right_aligned_column),
                        VBox([tool_drop, plot_sliders],
                             layout=right_aligned_column),
                        days, toolbox]),
                  out]))

    def go(self):

        # In the first run, there are no groups.
        try:
            group_cache = cache_manager.read(json_file=self.json_file,
                                             settings_dir=self.settings_dir)
            ok_cache = group_cache['_groups']['_labels'] != []
        except:
            # broken cache
            ok_cache = False
            group_cache = {}
            pass

        if ok_cache:
            start_value = 'Tools '
        else:
            start_value = 'Group menu '

        main = wd.ToggleButtons(options=['Tools ',
                                         'Group menu ',
                                         'Help '],
                                value=start_value,
                                button_style="success",
                                tooltip='settings')
        main.icons = ['area-chart', 'list', 'info-circle']
        main.style.button_width = "120px"
        main.tooltip = 'Run or edit...'

        def main_change(change):
            choice = change['new']
            with out:
                clear_output()
                if choice == 'Tools ':
                    self._tools(group_cache)
                elif choice == 'Group menu ':
                    clear_output()
                    self._edit_group_variables()
                else:
                    clear_output()
                    self._help()

        main.observe(main_change, "value")
        out = wd.Output()
        with out:

            if ok_cache:
                self._tools(group_cache)
            else:
                self._edit_group_variables()

        display(VBox([main, out]))

    def __init__(self, theme=None, level=None, debug=None):
        if not theme:
            theme = 'ES'
        if not level:
            level = '1'
        if not debug:
            debug = False

        self.json_file = f'cache_{theme}.json'
        self.settings_dir = 'appdata'
        self.theme = theme
        self.debug = debug
        self.icos_info = icos_data.StationData(theme=theme, level=level)
        self.stations_df = self.icos_info.stations_df
        self.go()
