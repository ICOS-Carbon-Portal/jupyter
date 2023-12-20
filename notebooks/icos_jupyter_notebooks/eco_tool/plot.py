#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Library for plotting ICOS data.

    Examples
    --------
    >>> # To produce 9 graphs of 9 variables, from a
    >>> # dataframe df with an interconnected zoom slider
    >>> # below every second graph, use:
    >>> ### 1. On jupyter:
    >>> fig = split_plot(df, n=2, units=unit_ls)
    >>> fig.show()
    ...
    >>> ### 2. On local computer:
    >>> from plotly.offline import plot
    >>>
    >>> fig = split_plot(df,n=2,units=unit_ls)
    >>> plot(fig, include_mathjax='cdn')
"""

__credits__ = "ICOS Carbon Portal"
__author__ = ["Anders Dahlner"]
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = "2023-06-14"

from typing import List, Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import copy
from eco_tool import icos2latex


class Plot:

    __plotly_color_scales = ['aggrnyl', 'agsunset', 'blackbody', 'bluered',
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
    __plotly_templates = ['plotly', 'plotly_white', 'plotly_dark',
                          'ggplot2', 'seaborn', 'simple_white', 'none']

    __plotly_text_fonts = ["Arial", "Balto", "Courier New", "Droid Sans",
                           "Droid Serif", "Droid Sans Mono", "Gravitas One",
                           "Old Standard TT", "Open Sans", "Overpass",
                           "PT Sans Narrow", "Raleway", "Times New Roman"]
    __plotly_text_sizes = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

    def __init__(self, **kwargs):
        """
            Keys of settings:
            -----------------
            - debug_function
                        If not None, messages will be
                        sent to this function.
            - latex_kwargs: dict
                        Settings for LaTeX, see eco_tool.icos2latex for details.
            - corr_plot: dict
                        Plotly settings for corr_plot
            - corr_table: dict
                        Plotly settings for corr_table
            - multi_plot: dict
                        Plotly settings for multi_plot
            - split_plot: dict
                        Plotly settings for split_plot
        """
        debug_function = kwargs.pop('debug_function', None)
        self.debug = True if debug_function else False
        if self.debug:
            self.debug_value = debug_function
            self.debug_value(0, 'Plot init',
                             f'kwargs = {kwargs}')

        latex_settings = kwargs.pop('latex_kwargs', {})
        self.latex = icos2latex.Translator(debug=debug_function,
                                           **latex_settings)

        self.corr_plot_settings = kwargs.pop('corr_plot_kwargs', dict())
        self.corr_table_settings = kwargs.pop('corr_table_kwargs', dict())
        self.multi_plot_settings = kwargs.pop('multi_plot_kwargs', dict())
        self.split_plot_settings = kwargs.pop('split_plot_kwargs', dict())

        self.corr_plot_layout = None
        self.corr_table_layout = None
        self.multi_plot_layout = None
        self.split_plot_layout = None

    def _corr_plot_layout_dict(self, use_latex: bool) -> dict:
        if self.debug:
            self.debug_value(1, '_corr_plot_layout()',
                             f'self.corr_plot_settings = '
                             f'{self.corr_plot_settings}',
                             f'self.corr_plot_layout = {self.corr_plot_layout}')

        if not self.corr_plot_layout:
            settings = self.corr_plot_settings
            margins = dict(b=35,  # default = 80
                           t=120,  # default = 100
                           l=80,  # default = 80
                           r=80)  # default = 80

            plot_width = settings.get('width', None)
            if not isinstance(plot_width, int) or plot_width < 210:
                tot_width = None
            else:
                plot_width = max(210, min(plot_width, 1000))
                w_margins = margins['l'] + margins['r']
                tot_width = w_margins + plot_width
                tot_width = max(tot_width, 600)

            plot_height = settings.get('height', None)
            if not isinstance(plot_height, int) or plot_height < 210:
                tot_height = None
            else:
                plot_height = max(210, min(plot_height, 800))
                h_margins = margins['t'] + margins['b']
                tot_height = h_margins + plot_height
                tot_height = max(tot_height, 360)

            template = settings.get('template', 'plotly')
            if template not in Plot.__plotly_templates:
                template = None

            title_font = settings.get('title_font', 'Arial')
            if title_font not in Plot.__plotly_text_fonts:
                title_font = 'Arial'

            title_size = settings.get('title_size', 14)
            if title_size not in Plot.__plotly_text_sizes:
                title_size = 14

            subtitle_size = settings.get('subtitle_size', 10)
            if subtitle_size not in Plot.__plotly_text_sizes:
                subtitle_size = 10
            legend_title_size = min(subtitle_size + 1, title_size)

            color_scale = settings.get('color_scale', "blues")
            if color_scale not in Plot.__plotly_color_scales:
                color_scale = "blues"
            colorbar_height = int(0.8 * plot_height) if plot_height else 200

            use_border = settings.get('border', True)
            if use_border or not isinstance(use_border, bool):
                border_color = 'black' if template != 'plotly_dark' else 'white'
                border_size = 1.5
            else:
                border_color = None
                border_size = None

            #second_title_size = min(subtitle_size + 1, title_size)
            if use_latex:
                x_title = 'title of x-axis'
                y_title = 'title of y-axis'
            else:
                x_title = {'text': 'title of x-axis',
                           'font': {'family': title_font,
                                    'size': subtitle_size}}
                y_title = {'text': 'title of y-axis',
                           'font': {'family': title_font,
                                    'size': subtitle_size}}
            # axis layouts:
            xaxis_layout = dict(
                mirror=True,
                anchor='y',
                domain=[0.0, 0.94],
                title=x_title,
                zeroline=True,
                zerolinecolor='black')

            yaxis_layout = dict(
                mirror=True,
                anchor='x',
                domain=[0.0, 1.0],
                title=y_title,
                zeroline=True,
                zerolinecolor='black')

            if use_border:
                xaxis_layout['ticks'] = 'outside'
                xaxis_layout['showline'] = True
                xaxis_layout['linecolor'] = border_color
                xaxis_layout['linewidth'] = border_size
                yaxis_layout['ticks'] = 'outside'
                yaxis_layout['showline'] = True
                yaxis_layout['linecolor'] = border_color
                yaxis_layout['linewidth'] = border_size

            temp_layout = dict(
                title=dict(
                    text='main title of corr-plot template',
                    font=dict(
                        family=title_font,
                        size=title_size),
                    x=0.05,
                    xref='container',
                    yref='paper',
                ),
                margin=margins,
                annotations=[dict(
                    font=dict(
                        family=title_font,
                        size=subtitle_size),
                    text='subtitle of corr-plot template',
                    showarrow=False,
                    x=0.47,
                    xref='paper',
                    y=1.1,
                    yref='paper')
                    # dict(
                    #     font=dict(
                    #         family=title_font,
                    #         size=second_title_size),
                    #     text=' ',  # second_title of corr-table template',
                    #     showarrow=False,
                    #     x=0.01,
                    #     xref='paper',
                    #     y=1.12,
                    #     yanchor='bottom',
                    #     yref='y domain',
                    #     align='left')
                ],
                xaxis=xaxis_layout,
                yaxis=yaxis_layout,
                coloraxis=dict(
                    colorscale=color_scale,
                    colorbar=dict(
                        title=dict(
                            text='Color mapping<br><br>',
                            font=dict(
                                family=title_font,
                                size=legend_title_size)),
                        lenmode="pixels",
                        len=colorbar_height))
            )

            if tot_height:
                temp_layout['height'] = tot_height
            if tot_width:
                temp_layout['width'] = tot_width
            if template:
                temp_layout['template'] = template
            self.corr_plot_layout = temp_layout

        if self.debug:
            self.debug_value(1, '_corr_plot_layout ',
                             f'self.corr_plot_layout = {self.corr_plot_layout}')
        return copy.deepcopy(self.corr_plot_layout)

    def _corr_table_layout_dict(self) -> dict:
        if self.debug:
            self.debug_value(5, '_corr_table_layout_dict()',
                             f'self.corr_table_settings = '
                             f'{self.corr_table_settings}',
                             f'self.corr_table_layout = {self.corr_table_layout}')

        if not self.corr_table_layout:
            settings = self.corr_table_settings
            margins = dict(b=35,  # default = 80
                           t=120,  # default = 100
                           l=80,  # default = 80
                           r=80)  # default = 80

            plot_width = settings.get('width', None)
            if not isinstance(plot_width, int) or plot_width < 210:
                tot_width = None
            else:
                plot_width = max(210, min(plot_width, 1000))
                w_margins = margins['l'] + margins['r']
                tot_width = w_margins + plot_width
                tot_width = max(tot_width, 600)

            plot_height = settings.get('height', None)
            if not isinstance(plot_height, int) or plot_height < 210:
                tot_height = None
            else:
                plot_height = max(210, min(plot_height, 800))
                h_margins = margins['t'] + margins['b']
                tot_height = h_margins + plot_height
                tot_height = max(tot_height, 360)

            template = settings.get('template', 'plotly')
            if template not in Plot.__plotly_templates:
                template = None

            title_font = settings.get('title_font', 'Arial')
            if title_font not in Plot.__plotly_text_fonts:
                title_font = 'Arial'

            title_size = settings.get('title_size', 14)
            if title_size not in Plot.__plotly_text_sizes:
                title_size = 14

            subtitle_size = settings.get('subtitle_size', 10)
            if subtitle_size not in Plot.__plotly_text_sizes:
                subtitle_size = 10

            color_scale = settings.get('color_scale', "blues")
            if color_scale not in Plot.__plotly_color_scales:
                color_scale = "blues"

            use_border = settings.get('border', True)
            if not isinstance(use_border, bool):
                use_border = True
            if use_border:
                border_color = 'black' if template != 'plotly_dark' else 'white'
                border_size = 1.5
            else:
                border_color = None
                border_size = None

            # axis layouts:
            xaxis_layout = dict(
                side='top',
                mirror=True,
                domain=[0.0, 0.94],
                title={'text': 'title of x-axis',
                       'font': {'family': title_font,
                                'size': subtitle_size}},
                zeroline=True,
                zerolinecolor='black')

            yaxis_layout = dict(
                side='left',
                mirror=True,
                domain=[0.0, 1.0],
                title={'text': 'title of y-axis',
                       'font': {'family': title_font,
                                'size': subtitle_size}},
                zeroline=True,
                zerolinecolor='black')

            if use_border:
                xaxis_layout['ticks'] = 'outside'
                xaxis_layout['showline'] = True
                xaxis_layout['linecolor'] = border_color
                xaxis_layout['linewidth'] = border_size
                yaxis_layout['ticks'] = 'outside'
                yaxis_layout['showline'] = True
                yaxis_layout['linecolor'] = border_color
                yaxis_layout['linewidth'] = border_size

            colorbar_height = int(0.8 * tot_height) if tot_height else 200

            second_title_size = min(subtitle_size + 1, title_size)
            legend_title_size = min(subtitle_size + 1, title_size)
            temp_layout = dict(
                title=dict(
                    text='main title of corr-table template',
                    font=dict(
                        family=title_font,
                        size=title_size),
                    x=0.05,
                    xref='container',
                    yref='paper',
                ),
                margin=margins,
                annotations=[dict(
                    font=dict(
                        family=title_font,
                        size=subtitle_size),
                    text='',
                    showarrow=False,
                    x=0.47,
                    xref='paper',
                    y=1.1,
                    yref='paper'),
                    dict(
                         font=dict(
                             family=title_font,
                             size=second_title_size),
                         text=' ',  # second_title of corr-table template',
                         showarrow=False,
                         x=0.01,
                         xref='paper',
                         y=1.12,
                         yanchor='bottom',
                         yref='y domain',
                         align='left')
                ],
                xaxis=xaxis_layout,
                yaxis=yaxis_layout,
                coloraxis=dict(
                    colorscale=color_scale,
                    colorbar=dict(
                        title=dict(
                            text='Color mapping<br><br>',
                            font=dict(
                                family=title_font,
                                size=legend_title_size)),
                        lenmode="pixels",
                        len=colorbar_height))
            )
            if tot_height:
                temp_layout['height'] = tot_height
            if tot_width:
                temp_layout['width'] = tot_width
            if template:
                temp_layout['template'] = template
            self.corr_table_layout = temp_layout
        if self.debug:
            self.debug_value(5, '_corr_table_layout() ',
                             f'self.corr_table_layout = {self.corr_table_layout}')
        return copy.deepcopy(self.corr_table_layout)

    def _multi_plot_layout_dict(self, use_latex: bool) -> dict:
        if self.debug:
            self.debug_value(2, '_multi_plot_layout_dict()',
                             f'self.multi_plot_settings = '
                             f'{self.multi_plot_settings}',
                             f'self.multi_plot_layout = {self.multi_plot_layout}')

        if not self.multi_plot_layout:
            settings = self.multi_plot_settings

            margins = dict(b=30,  # default = 80
                           t=125,  # default = 100
                           l=80,  # default = 80
                           r=80)  # default = 80

            plot_width = settings.get('width', None)
            if not isinstance(plot_width, int) or plot_width < 210:
                tot_width = None
            else:
                plot_width = max(210, min(plot_width, 1000))
                w_margins = margins['l'] + margins['r']
                tot_width = w_margins + plot_width
                tot_width = max(tot_width, 600)

            plot_height = settings.get('height', None)
            if not isinstance(plot_height, int) or plot_height < 210:
                tot_height = None
            else:
                plot_height = max(210, min(plot_height, 800))
                h_margins = margins['t'] + margins['b']
                tot_height = h_margins + plot_height
                tot_height = max(tot_height, 360)

            template = settings.get('template', 'plotly')
            if template not in Plot.__plotly_templates:
                template = None

            title_font = settings.get('title_font', 'Arial')
            if title_font not in Plot.__plotly_text_fonts:
                title_font = 'Arial'

            title_size = settings.get('title_size', 14)
            if title_size not in Plot.__plotly_text_sizes:
                title_size = 14

            subtitle_size = settings.get('subtitle_size', 10)
            if subtitle_size not in Plot.__plotly_text_sizes:
                subtitle_size = 10
            second_title_size = min(subtitle_size + 1, title_size)
            legend_title_size = min(subtitle_size + 1, title_size)

            color_scale = settings.get('color_scale', "blues")
            if color_scale not in Plot.__plotly_color_scales:
                color_scale = "blues"
            colorbar_height = int(0.8 * plot_height) if plot_height else 200

            use_border = settings.get('border', True)
            if not isinstance(use_border, bool):
                use_border = True
            if use_border:
                border_color = 'black' if template != 'plotly_dark' else 'white'
                border_size = 1.5
            else:
                border_color = None
                border_size = None

            if use_latex:
                y1_title = 'title of left y-axis'
                y2_title = 'title of right y-axis'
            else:
                y1_title = {'text': 'title of left y-axis',
                            'font': {'family': title_font,
                                     'size': subtitle_size}}
                y2_title = {'text': 'title of right y-axis',
                            'font': {'family': title_font,
                                     'size': subtitle_size}}

            # axis layouts:
            xaxis_layout = dict(
                mirror=True,
                anchor='y',
                domain=[0.0, 0.85],
                title={'text': 'Timestamp UTC',
                       'font': {'family': title_font,
                                'size': subtitle_size}},
                zeroline=True,
                zerolinecolor='black')

            yaxis_layout = dict(
                mirror=True,
                anchor='x',
                domain=[0.0, 1.0],
                title=y1_title,
                zeroline=True,
                zerolinecolor='black')
            yaxis2_layout = dict(
                mirror=True,
                anchor='x',
                overlaying='y',
                side='right',
                domain=[0.0, 1.0],
                title=y2_title,
                zeroline=True,
                zerolinecolor='darkgray')

            if use_border:
                xaxis_layout['ticks'] = 'outside'
                xaxis_layout['showline'] = True
                xaxis_layout['linecolor'] = border_color
                xaxis_layout['linewidth'] = border_size
                yaxis_layout['ticks'] = 'outside'
                yaxis_layout['showline'] = True
                yaxis_layout['linecolor'] = border_color
                yaxis_layout['linewidth'] = border_size
                yaxis2_layout['ticks'] = 'outside'
                yaxis2_layout['showline'] = True
                yaxis2_layout['linecolor'] = border_color
                yaxis2_layout['linewidth'] = border_size

            temp_layout = dict(
                title=dict(
                    text='',    # main title of multi-plot template',
                    font=dict(
                        family=title_font,
                        size=title_size),
                    x=0.05,
                    xref='container',
                    yref='paper',
                ),
                margin=margins,
                annotations=[
                    dict(
                        font=dict(
                            family=title_font,
                            size=subtitle_size),
                        text='',       # subtitle of multi-plot template',
                        showarrow=False,
                        x=0.47,
                        xanchor='center',
                        xref='paper',
                        y=1.03,
                        yanchor='bottom',
                        yref='paper'),
                    dict(
                        font=dict(
                            family=title_font,
                            size=second_title_size),
                        text='',       # second_title of multi-plot template',
                        showarrow=False,
                        x=0.06,
                        xref='paper',
                        y=1.12,
                        yanchor='bottom',
                        yref='paper',
                        align='left')
                ],
                xaxis=xaxis_layout,
                yaxis=yaxis_layout,
                yaxis2=yaxis2_layout,
                legend=dict(
                    x=1.1,
                    xanchor='right',
                    yanchor='top',
                    title=dict(
                        text='Variables',
                        font=dict(
                            family=title_font,
                            size=legend_title_size)),
                    font=dict(              # used for the variables
                        family=title_font,
                        size=subtitle_size)) #, color="black"))
                )

            if tot_height:
                temp_layout['height'] = tot_height
            if tot_width:
                temp_layout['width'] = tot_width
            if template:
                temp_layout['template'] = template
            self.multi_plot_layout = temp_layout

        if self.debug:
            self.debug_value(2, '_multi_plot_layout_dict ',
                             f'self.multi_plot_layout = {self.multi_plot_layout}')
        return copy.deepcopy(self.multi_plot_layout)

    def _split_plot_layout_dict(self, use_latex: bool) -> dict:
        if self.debug:
            self.debug_value(3, '_split_plot_layout_dict()',
                             f'self.split_plot_settings = '
                             f'{self.split_plot_settings}',
                             f'self.split_plot_layout = {self.split_plot_layout}')

        if not self.split_plot_layout:
            settings = self.split_plot_settings
            margins = dict(b=35,  # default = 80
                           t=120,  # default = 100
                           l=60,  # default = 80
                           r=60)  # default = 80

            width = settings.get('width', None)
            if not isinstance(width, int) or width < 210:
                tot_width = None
            else:
                tot_width = width + margins['l'] + margins['r']

            height = settings.get('height', None)
            if not isinstance(height, int) or height < 210:
                height = None

            template = settings.get('template', 'plotly')
            if template not in Plot.__plotly_templates:
                template = None

            # color adjustments
            if template == 'plotly_dark':
                slider_color = 'white'
            elif template in ['plotly_white', 'simple_white', 'none']:
                slider_color = 'gray'
            else:
                slider_color = None

            use_border = settings.get('border', True)
            if not isinstance(use_border, bool):
                use_border = True
            if use_border:
                border_color = 'black' if template != 'plotly_dark' else 'white'
                border_size = 1.5
            else:
                border_color = None
                border_size = None

            title_font = settings.get('title_font', 'Arial')
            if title_font not in Plot.__plotly_text_fonts:
                title_font = 'Arial'

            title_size = settings.get('title_size', 14)
            if title_size not in Plot.__plotly_text_sizes:
                title_size = 14

            subtitle_size = settings.get('subtitle_size', 10)
            if subtitle_size not in Plot.__plotly_text_sizes:
                subtitle_size = 10

            # axis definitions:
            xaxis_layout = dict(domain=[0.0, 0.94],
                                type='date',
                                mirror=True,
                                title=dict(text='Timestamp UTC',
                                           font=dict(family=title_font,
                                                     size=subtitle_size)),
                                showticklabels=True,
                                rangeslider=dict(visible=True,
                                                 bgcolor=slider_color))
            yaxis_layout = dict(mirror=True,
                                fixedrange=False,
                                zeroline=False)
            if use_border:
                xaxis_layout['ticks'] = 'outside'
                xaxis_layout['showline'] = True
                xaxis_layout['linewidth'] = border_size
                xaxis_layout['linecolor'] = border_color
                yaxis_layout['ticks'] = 'outside'
                yaxis_layout['showline'] = True
                yaxis_layout['linewidth'] = border_size
                yaxis_layout['linecolor'] = border_color

            if use_latex:
                yaxis_layout['title'] = 'title of y-axis'
            else:
                yaxis_layout['title'] = {'text': 'title of y-axis',
                                         'font': {'family': title_font,
                                                  'size': subtitle_size}}
            # setting layout
            temp_layout = dict(
                title=dict(text=' ',  # main title of split-plot template',
                           font=dict(
                               family=title_font,
                               size=title_size),
                           x=0.05,
                           xref='container',
                           yref='paper'),
                margin=margins,
                showlegend=False,
                annotations=[
                    dict(
                        font=dict(
                            family=title_font,
                            size=subtitle_size),
                        text=' ',   # subtitle of split-plot template',
                        showarrow=False,
                        x=0.47,
                        xanchor='center',
                        xref='paper',
                        y=0.03,
                        yanchor='bottom',
                        yref='paper')
                ],
                xaxis=xaxis_layout,
                yaxis=yaxis_layout
                )
                # showlegend=False
                # legend=dict(
                #     x=1.08,
                #     xanchor='right',
                #     yanchor='top',
                #     title=dict(
                #         text='Variables',
                #         font=dict(
                #             family=title_font,
                #             size=legend_title_size)),
                #     font=dict(              # used for the variables
                #         family=title_font,
                #         size=subtitle_size)) #, color="black"))

            if height:
                # will be recalculated every time
                temp_layout['height'] = height
            if tot_width:
                temp_layout['width'] = tot_width
            if template:
                temp_layout['template'] = template
            self.split_plot_layout = temp_layout
        if self.debug:
            self.debug_value(3, '_split_plot_layout() ',
                             f'self.split_plot_layout = {self.split_plot_layout}')
        return copy.deepcopy(self.split_plot_layout)

    def corr_plot(self, df,
                  x_col: str,
                  y_col: str,
                  units: list = None,
                  title: str = None,
                  subtitle: str = None) -> go.Figure:
        """
            For a pandas dataframe df, this function
            returns a plotly figure with a scatter plot of
            two columns.

            Inputs:
            -------
            - df: a pandas dataframe.
                    Mandatory.
            - x_col: str
                    Mandatory. Column name of `df` for the x-axis variable
            - y_col:str
                    Mandatory. Column name of `df` for the y-axis variable
            - units: list
                    A list to provide titles for the axes, either
                    of the form
                        [(var_name_x, unit of x), (var_name_y, unit of y)]
                    or
                        [var_name_x, var_name_y]
                    if left empty [x_col, y_col] is used
            - title: str
                    Main title of the plot.
            - subtitle: str
                    Subtitle of the plot.

        """

        df = df.copy()
        if 'TIMESTAMP' not in [c.upper() for c in df.columns]:
            df.reset_index(inplace=True)
        df = df[['TIMESTAMP', x_col, y_col]]

        if self.debug:
            self.debug_value(11, 'corr_plot ',
                             f'df.head = {df.head}',
                             f'x_col = {x_col}',
                             f'y_col = {y_col}',
                             f'units = {units}',
                             f'title = {title}'
                             f'subtitle = {subtitle}')

        # load general settings for corr-plot
        use_latex = self.corr_plot_settings.get('use_latex', True)
        if not isinstance(use_latex, bool):
            use_latex = True

        layout_dict = self._corr_plot_layout_dict(use_latex)

        if title is None:
            title = f'Correlation plot of {x_col} and {y_col}.'

        if subtitle is None:
            subtitle = f'{x_col} (on the <i>x</i>-axis) vs  ' \
                       f'{y_col} (on the <i>y</i>-axis) '

        if not isinstance(units, list):
            units = [x_col, y_col]
        if all(isinstance(x, tuple) for x in units):
            if use_latex and self.latex is not None:
                x_label = self.latex.var_unit_to_latex(var_unit=units[0])
                y_label = self.latex.var_unit_to_latex(var_unit=units[1])
            else:
                x_label = f'{units[0][0]} ({units[0][1]})'
                y_label = f'{units[1][0]} ({units[1][1]})'
        elif all(isinstance(x, str) for x in units):
            if use_latex and self.latex is not None:
                x_label = self.latex.var_to_latex(var=units[0])
                y_label = self.latex.var_to_latex(var=units[1])
            else:
                x_label = units[0]
                y_label = units[1]
        else:
            x_label = x_col
            y_label = y_col

        if self.debug:
            self.debug_value(11, 'corr_plot ',
                             f'use_latex = {use_latex}',
                             f'x_label ={x_label}',
                             f'y_label ={y_label}')

        # ticks for color legend
        ticks = len(df)
        if ticks > 18:
            last_date = str(df['TIMESTAMP'].values.max())[:16]
            first_date = str(df['TIMESTAMP'].values.min())[:16]
            tick_ind = [0, 1, 2,
                        3, 4, 5,
                        6, 7, 8,
                        ticks - 9, ticks - 8, ticks - 7,
                        ticks - 6, ticks - 5, ticks - 4,
                        ticks - 3, ticks - 2, ticks - 1]
            tick_text = ['', '', '',
                         '', '', '',
                         '', '', f"<sub>Sampled on <br>{first_date}</sub>",
                         f"<br><sub>Sampled on <br>{last_date}</sub>", '', '',
                         '', '', '',
                         '', '', '']
        else:
            tick_ind = [0, 1]
            tick_text = ['', '']

        layout_dict['coloraxis']['colorbar']['tickvals'] = tick_ind
        layout_dict['coloraxis']['colorbar']['ticktext'] = tick_text
        layout_dict['title']['text'] = title
        layout_dict['annotations'][0]['text'] = subtitle
        if use_latex:
            layout_dict['xaxis']['title'] = x_label
            layout_dict['yaxis']['title'] = y_label
        else:
            layout_dict['xaxis']['title']['text'] = x_label
            layout_dict['yaxis']['title']['text'] = y_label

        fig = go.Figure(px.scatter(df, x=x_col, y=y_col,
                                   trendline="ols",
                                   color=df.index))
        fig.update(layout=layout_dict)
        if self.debug:
            self.debug_value(11, 'corr_plot - end',
                             f'fig.layout = {fig.layout}')
        return fig

    def corr_table(self, df,
                   title: str = None,
                   second_title: str = None,
                   legend_titles: list = None) -> go.Figure:
        """
            For a pandas dataframe df, this function
            returns a plotly figure with a correlation table.

            Inputs:
            -------
            - df: a pandas dataframe.
                    Mandatory.
            - title: str
                    Main title of the plot.
            - subtitle: str
                    Subtitle of the plot.

        """
        cols = list(df.columns)
        df_corr = df.corr()

        if self.debug:
            self.debug_value(12, 'corr_table ',
                             f'df.head = {df.head}',
                             f'title = {title}'
                             f'subtitle = {second_title}',
                             f'legend_titles = {legend_titles}')
        if title is None:
            cols = list(df.columns)
            title = f'Correlation table {", ".join(cols)}'

        layout_dict = self._corr_table_layout_dict()
        layout_dict['title']['text'] = title
        if isinstance(second_title, str):
            layout_dict['annotations'][1]['text'] = second_title

        colorscale = layout_dict['coloraxis']['colorscale']

        fig = px.imshow(df_corr,
                        color_continuous_scale=colorscale,
                        text_auto='.3f',
                        x=legend_titles, y=legend_titles,
                        aspect="auto")
        fig.update(layout=layout_dict)

        if self.debug:
            self.debug_value(12, 'corr_table - end',
                             f'fig.layout = {fig.layout}')
        return fig

    def multi_plot(self, df,
                   yaxis1_vars: list,
                   yaxis1: list = None,
                   unit1: str = None,
                   yaxis2_vars: list = None,
                   yaxis2: list = None,
                   unit2: str = None,
                   title: str = None,
                   second_title: str = None,
                   #subtitle: str = None,
                   legend_titles: list = None) -> go.Figure:
        """
            Plot several variables in one plotly Figure,
            with one or two y axes.

            Inputs:
            -------
            - df: a pandas dataframe

            - yaxis1_vars: list
                column names for left axis

            - yaxis1: list
                labels for left axis variables

            - unit1: str
                 unit for left axis variables

            - yaxis2_vars: list
                column names for right axis

             - yaxis2: list
                labels for right axis variables

            - unit2: str
                unit for right axis variables

            - title: str
                main title of plot

           - second_title: str
                title text below main title using subtitle-size

            Removed - subtitle: str
            Removed     subtitle of plot, placed below main

            - legend_titles: list
                titles for renaming legend variables

        """
        df = df.copy()
        if self.debug:
            self.debug_value(15, 'multi_plot() -- start ',
                             f'yaxis1 = {yaxis1}', f'yaxis2 = {yaxis2}',
                             f'unit1 = {unit1}', f'unit2 = {unit2}',
                             f'title = {title}',
                             f'second_title = {second_title}',
                             #f'subtitle = {subtitle}'
                             f'legend_titles = {legend_titles}')

        if not (isinstance(yaxis1_vars, list)):
            raise TypeError(f'The input parameter yaxis1_vars is supposed to be '
                            f'a list.')

        if 'TIMESTAMP' not in df.columns:
            if 'TIMESTAMP' in [c.upper() for c in df.columns]:
                df.rename(columns={c: 'TIMESTAMP' for c in df.columns
                                   if c.upper() == 'TIMESTAMP'},
                          inplace=True)
            else:
                df.reset_index(inplace=True)
                df.rename(columns={'index': 'TIMESTAMP'},
                          inplace=True)
        use_latex = self.multi_plot_settings.get('use_latex', True)
        if not isinstance(use_latex, bool):
            use_latex = True
        layout_dict = self._multi_plot_layout_dict(use_latex=use_latex)

        if not(isinstance(yaxis1, list)):
            yaxis1 = yaxis1_vars
        if not isinstance(unit1, str):
            unit1 = None
        if yaxis2_vars is None:
            yaxis2_vars = []
        if not(isinstance(yaxis2, list)):
            yaxis2 = yaxis2_vars
        if not isinstance(unit2, str):
            unit2 = None
        plot_vars = yaxis1_vars.copy()
        plot_vars.extend(yaxis2_vars)

        if not isinstance(title, str):
            title = f'Multiplot plot of {", ".join(plot_vars)}.'
        if not isinstance(second_title, str):
            second_title = ''
        # if not isinstance(subtitle, str):
        #     subtitle = f'Multiplot plot of {", ".join(plot_vars)}.'
        # if title == subtitle:
        #     subtitle = ''
        title += f'<br>{second_title}'

        if not isinstance(legend_titles, list):
            y1_legend_names = yaxis1_vars
            y2_legend_names = yaxis2_vars
        else:
            y1_legend_names = legend_titles[:len(yaxis1_vars)]
            y2_legend_names = legend_titles[len(yaxis1_vars):]

        if self.debug:
            self.debug_value(15, 'multi_plot()', f'use_latex={use_latex}',
                             f'y1_legend_names = {y1_legend_names}',
                             f'y2_legend_names = {y2_legend_names}',
                             f'layout={layout_dict}')

        # Fix labels for y-axes
        if use_latex:
            y1_label = self.latex.var_unit_to_latex(var_ls=yaxis1, unit=unit1)
            if yaxis2:
                y2_label = self.latex.var_unit_to_latex(var_ls=yaxis2, unit=unit2)
            else:
                y2_label = ''
        else:
            y1_label = ', '.join(yaxis1)
            if unit1:
                y1_label = f'{y1_label} ({unit1})'
            if yaxis2:
                y2_label = ', '.join(yaxis2)
                if unit2:
                    y2_label = f'{y2_label} ({unit2})'
            else:
                y2_label = ''

        layout_dict['title']['text'] = title
        layout_dict['annotations'][0]['text'] = ''  # subtitle
        layout_dict['annotations'][1]['text'] = ''  # second_title
        if use_latex:
            layout_dict['yaxis']['title'] = y1_label
            layout_dict['yaxis2']['title'] = y2_label
        else:
            layout_dict['yaxis']['title']['text'] = y1_label
            layout_dict['yaxis2']['title']['text'] = y2_label

        # height = layout_dict.get('height', 210)

        # if height:
        #    if isinstance(height, int):
        #        height = max(210, min(height, 800))
        #    else:
        #        height = 210

        #    if 'margin' in layout_dict.keys():
        #        margins = layout_dict['margin'].get('t', 135) + \
        #                  layout_dict['margin'].get('b', 30)
        #    else:
        #        margins = 165
        #    plot_height = height
        #    tot_height = margins + plot_height
        #    if self.debug:
        #        self.debug_value(818, f'margins={margins}', f'tot_height = '
        #                                                    f'{tot_height}' )
        #    layout_dict['height'] = max(tot_height, 360)
        #else:
        #    #layout_dict.pop('margin', None)
        #    pass
        #    #layout_dict['yaxis']['automargin'] = 'height+top+bottom'
        #    #layout_dict['yaxis2']['automargin'] = 'height+top+bottom'
        #width = layout_dict.get('width', 210)
        #if width:
        #    if isinstance(width, int) and width <= 800:
        #        width = max(210, width)
        #        if 'margin' in layout_dict.keys():
        #            margins = layout_dict['margin'].get('l', 30) + \
        #                      layout_dict['margin'].get('r', 30)
        #        else:
        #            margins = 60
        #        plot_width = width
        #        tot_height = margins + plot_width
        #        layout_dict['width'] = max(tot_height, 360)
        #    else:
        #        pass
        #        #layout_dict['width'] = None
        #else:
        #    pass
        #    # layout_dict['xaxis']['automargin'] = 'width+left+right'

        # xaxis = layout_dict.pop('xaxis', None)
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]],
                            subplot_titles=['', ''],
                            ) #figure=go.Figure(layout=layout_dict))
        # add plots to figure
        for i in range(len(yaxis1_vars)):
            df_col = yaxis1_vars[i]
            legend_col = y1_legend_names[i]
            # plotting y1-axis
            fig.add_trace(go.Scatter(x=df.TIMESTAMP,
                                     y=df[df_col],
                                     name=f"{legend_col}"),
                          secondary_y=False)

        for i in range(len(yaxis2_vars)):
            df_col = yaxis2_vars[i]
            legend_col = y2_legend_names[i]
            # plotting y2-axis
            fig.add_trace(go.Scatter(x=df.TIMESTAMP,
                                     y=df[df_col],
                                     name=f"{legend_col}"),
                          secondary_y=True)
        fig.update(layout=layout_dict, overwrite=True)
        # layout_dict['title']['text'] = title
        # layout_dict['annotations'][0]['text'] = subtitle
        # layout_dict['annotations'][1]['text'] = second_title
        # if use_latex:
        #     layout_dict['yaxis']['title'] = y1_label
        #     layout_dict['yaxis2']['title'] = y2_label
        # else:
        #     layout_dict['yaxis']['title']['text'] = y1_label
        #     layout_dict['yaxis2']['title']['text'] = y2_label
        #
        # height = layout_dict.get('height', None)
        # if isinstance(height, int):
        #     height = max(210, min(height, 800))
        # else:
        #     height = 210
        #
        # if 'margin' in layout_dict.keys():
        #     margins = layout_dict['margin'].get('t', 150) + \
        #               layout_dict['margin'].get('b', 50)
        # else:
        #     margins = 200
        # plot_height = height
        # tot_height = margins + plot_height
        # layout_dict['height'] = max(tot_height, 360)
        #fig_layout = fig.to_dict()['layout']
        #fig.update_yaxes(automargin='width+height+left+top+right+bottom')
        #fig_layout['xaxis'] = xaxis
        #template = fig_layout['template']['data']['scatter']
        #fig_layout['template']['data'] = {'scatter': template}
        #fig.update(layout=fig_layout, overwrite=True)
        #fig.update(layout=fig_layout)

        if self.debug:
            self.debug_value(15, 'multi_plot',
                             f'fig.layout = {fig.layout}')
        return fig

    def split_plot(self, df,
                   units: list = None,
                   title: str = None,
                   second_title: str = None,
                   subtitles: list[str] = None) -> go.Figure:
        """

            For a pandas dataframe df, with a datetime index, this function
            returns a plotly figure containing separate graphs of each
            column of df. The plots are interconnected through common
            a zoom tool on the x-axis.   

            Inputs:
            -------
            - df: a pandas dataframe.
                It is assumed that df has a datatime index.
            - n: int
                n is the number of plots between each zoom slider.
                For n!=0, the number of sliders is given by
                    max(int("number of columns" / n),1)
                for n=0, will only give one rangeslider in the end.
            - units: a list of strings or a list of tuples.
                Where the k:th element correspond to the k:th column of df.
                In the case of a tuple (a,b) a is the variable and b is the
                unit.
            - title: str
            - second_title: str
                A secondary text below the title
            - subtitles: list of strings

            Notes:
            - It is assumed that df.index is a datetime-index that will
                be a common x-axis, df.columns are the y-axises
            - To create the empty rangesliders are not that obvious.
                In the below workaround we create empty graphs in a
                specific order with rangesliders, and then we place
                "real graphs" on top of the empty graphs.
                For details, see the workaroun-references (WA-1), (WA-2)
                and (WA-3) below.
        """

        # validate inputs etc
        if not isinstance(df, pd.DataFrame) or df.empty:
            return make_subplots()

        df = df.copy()
        cols = list(df.columns)
        no_cols = len(cols)

        if isinstance(units, list) and len(units) == no_cols:
            unit_ls = units
        else:
            unit_ls = cols

        if not isinstance(title, str):
            title = ''

        if not isinstance(second_title, str):
            second_title = ''
        title += f'<br>{second_title}'

        if isinstance(subtitles, list) and len(subtitles) == no_cols and \
                all(isinstance(s, str) for s in subtitles):
            subtitles = subtitles
        else:
            subtitles = cols

        # load general settings for split-plot

        use_latex = self.split_plot_settings.get('use_latex', True)
        if not isinstance(use_latex, bool):
            use_latex = True

        layout = self._split_plot_layout_dict(use_latex=use_latex)

        n = self.split_plot_settings.get('zoom_sliders', None)

        if not (isinstance(n, int) and n >= 0):
            n = 2
        elif n == 0:
            n = no_cols
        n = min(n, no_cols)

        if n == 0:
            n = no_cols
        n = min(n, no_cols)

        # for n!=0 nsliders = max(int(no_cols/n),1)

        # Step 1.
        # We create a list of graphs where
        # every n:th graph is empty (WA-1)
        graphs = []
        y_ax_labels = []
        g_empty = go.Scatter(name='hidden')
        slider_no = 1
        pos = 0
        empty_positions = []

        for c in range(no_cols):
            col = cols[c]
            subtitle = subtitles[c]
            # formatting y-axis labels
            if isinstance(unit_ls[c], tuple):
                if use_latex:
                    y_label = self.latex.var_unit_to_latex(var_unit=unit_ls[c])
                else:
                    y_label = f'{unit_ls[c][0]} ({unit_ls[c][1]})'
            elif isinstance(unit_ls[c], str):
                if use_latex:
                    y_label = self.latex.var_to_latex(unit_ls[c])
                else:
                    y_label = unit_ls[c]
            else:
                y_label = ''

            y_ax_labels.append(y_label)

            g_real = go.Scatter(x=df.index,
                                y=df[col],
                                name=subtitle)

            graphs.append(g_real)

            pos += 1
            if pos % n == 0 and no_cols - c > n:
                # (WA-1)
                # We place the empty graph right before the last real graph.
                graphs.insert(-1, g_empty)
                empty_positions.append(len(graphs) - 1)
                slider_no += 1

        # (WA-1)
        # Finally we put an empty graph right before the last real graph
        graphs.insert(-1, g_empty)
        empty_positions.append(len(graphs) - 1)

        # Step 2.
        # Next, we create a figure for the graphs.
        number_of_subplots = len(graphs)
        # We need to calculate the height of the figure, in this
        # case the 'height' of the figures layout refer to the height
        # of the Figure object, other heights (such as the height of the
        # individual traces) are calculated using the Figure height.
        ### a ) We want the individual trace height to be like in the
        ### settings - between 250 and 800
        height = layout.get('height', None)
        if isinstance(height, int):
            height = max(210, min(height, 800))
        else:
            height = 210

        # The total height is given by:
        #   tot_height = margins + plot_height
        # where,
        #   margins = margin_top + margin_bottom
        # and
        #   plot_height = no_cols * trace_h
        #   plot_height += slider_no * ranger_h
        #   plot_height += (no_cols - 1) * vert_space
        # here:
        # 1. trace_h is the height of an individual
        #    trace (that is we want it to be `height`),
        # 2. ranger_h is the height of the rangesliders,
        #    we set:  ranger_h = 0.05 * trace_h
        # 3. vert_space is the space between traces, we set
        #    vert_space = 0.2 * trace_h
        # set
        if 'margin' in layout.keys():

            margins = layout['margin'].get('t', 150) + \
                      layout['margin'].get('b', 50)
        else:
            margins = 200

        plot_height = (no_cols + 0.055 * (slider_no + no_cols) +
                       0.2 * (slider_no + no_cols - 2)) * height
        tot_height = margins + plot_height
        layout['height'] = max(tot_height, 360)

        # Now, the portion of the plot area that is occupied by one trace
        # can be simplified to
        # 1 / (no_cols +
        #      0.055 * (slider_no + no_cols) +
        #      0.2 * (slider_no + no_cols - 2))  =
        # 200/(200 * no_cols +
        #     11 * (slider_no + no_cols) +
        #     40 * (slider_no + no_cols - 2)) =
        # 200/(251 * no_cols + 51 * slider_no - 80)
        # However, plotly use a list for the height of traces,
        row_heights = [200/(251 * no_cols + 51 * slider_no - 80)] * no_cols
        # slider 5%:  [20 /(25 *no_cols + 5 * slider_no - 8)] * no_cols

        # Plotly use a number instead of a list for the vertical
        # space between the traces:
        if no_cols > 1:
            vert_space = 0.2 / (no_cols + slider_no - 2)
            # there are `no_cols - 1` spaces between the traces
            # and `slider_no`of empty traces
        else:
            vert_space = 0
        ranger_height = 0.055 / (slider_no + no_cols)

        # Labels and heights for each graph

        for x in empty_positions:
            row_heights.insert(x, 0.0 / no_cols)
            subtitles.insert(x, '')
            y_ax_labels.insert(x, '')

        layout['title']['text'] = title
        xaxis_layout = layout.pop('xaxis', {})
        yaxis_layout = layout.get('yaxis')
        if self.debug:
            self.debug_value(16, 'split_plot()',
                             f'xaxis_layout = {xaxis_layout}',
                             f'yaxis_layout = {yaxis_layout}')
        annotation_layout = layout.pop('annotations', {})

        fig = make_subplots(rows=number_of_subplots, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=vert_space,
                            subplot_titles=subtitles,
                            row_heights=row_heights,
                            figure=go.Figure(layout=layout))
        fig_layout = fig.to_dict()['layout']
        fig_annotations = fig_layout['annotations']
        for anno in fig_annotations:
            anno['x'] = annotation_layout[0]['x']
            anno['y'] = anno['y'] + annotation_layout[0]['y']/no_cols
            anno['font'] = annotation_layout[0]['font']

        if self.debug:
            self.debug_value(16, 'split_plot() 999999999999',
                             f'fig_annotations = {fig_annotations}',
                             f'annotation_layout = {annotation_layout}')
        #annotation_layout[1]['text'] = second_title
        #fig_annotations.append(annotation_layout[1])
        fig_layout['annotations'] = fig_annotations
        template = fig_layout['template']['data']['scatter']
        fig_layout['template']['data'] = {'scatter': template}
        fig.update(layout=fig_layout, overwrite=True)

        if self.debug:
            self.debug_value(99, 'split_plot()  -- ',
                             f'layout = {layout}',
                             f'fig.layout = {fig.layout}')

        # Step 3.
        # Add the graphs to the figure, and some styling
        fig.add_traces(graphs,
                       rows=list(range(1, number_of_subplots + 1)),
                       cols=[1] * number_of_subplots)

        # Step 4 (WA-2)
        # We will update each x- and y-axes and
        # now create rangesliders from the empty graphs,
        # adjust thickness compared to number of plots,
        # make sure the xaxis has type 'date' and show
        # the dates on this x-axis

        if self.debug:
            self.debug_value(99, 'split_plot()  -- 1 ',
                             f'fig.to_dict()["layout"] = '
                             f'{fig.to_dict()["layout"]}')
        for row in range(1, number_of_subplots + 1):
            y_ax = copy.deepcopy(yaxis_layout)
            if isinstance(y_ax['title'], dict):
                y_ax['title']['text'] = y_ax_labels[row - 1]
            else:
                y_ax['title'] = y_ax_labels[row - 1]
            fig.update_yaxes(y_ax, row=row, col=1)

            x_ax = copy.deepcopy(xaxis_layout)
            if self.debug:
                self.debug_value(99, 'split_plot()  -- xax before',
                                 f'x_ax = {x_ax}',
                                 f'row = {row} (of {number_of_subplots})')

            if row != empty_positions[-1]: # number_of_subplots:
                x_ax.pop('title', None)
                if self.debug:
                    self.debug_value(99, 'split_plot()  -- xax removed title',
                                     f'x_ax = {x_ax}',
                                     f'row = {row} (of {number_of_subplots})')

            if row not in empty_positions:
                x_ax.pop('rangeslider', None)
            else:
                x_ax['rangeslider']['thickness'] = ranger_height
            if self.debug:
                self.debug_value(99, 'split_plot()  -- xax after',
                                 f'x_ax = {x_ax}',
                                 f'row = {row} (of {number_of_subplots})')

            fig.update_xaxes(x_ax, row=row, col=1)

        if self.debug:
            self.debug_value(99, 'split_plot()  -- 2 ',
                             f'fig.to_dict()["layout"] = '
                             f'{fig.to_dict()["layout"]}')

        # Step 5 (WA-3)
        # We will now place the first graph G after each empty graph E
        # over the graph E. That is:
        #   [G1,G2,E1,G3,G4,G5,E2,G6] -> [G1,G2,G3,G4,G5,G6]
        hidden_y_ax = ''

        for _, t in enumerate(fig.data):

            if hidden_y_ax:
                t.yaxis = hidden_y_ax
                hidden_y_ax = ''

            if t.name == 'hidden':
                hidden_y_ax = t.yaxis

        return fig
