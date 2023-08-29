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
    >>> fig = multi_plot(df, n=2, units=unit_ls)
    >>> fig.show()
    ...
    >>> ### 2. On local computer:
    >>> from plotly.offline import plot
    >>>
    >>> fig = multi_plot(df,n=2,units=unit_ls)
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

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from eco_tool import icos2latex


class Plot:

    def __init__(self, **kwargs):
        """
        Keys of settings:
        -----------------
        - debug: bool
                    If true, messages will be printed.
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
        debug = kwargs.pop('debug', False)

        if isinstance(debug, bool):
            self.debug = debug
        else:
            self.debug = False

        latex_settings = kwargs.pop('latex_kwargs', {})
        self.latex = icos2latex.Translator(**latex_settings)
        if self.debug:
            print(f'plot, latex_settings = {latex_settings}')

        if self.debug:
            print(f'plot2, self.latex = {self.latex}')
        self.corr_plot_settings = kwargs.pop('corr_plot_kwargs', dict())
        self.corr_table_settings = kwargs.pop('corr_table_kwargs', dict())
        self.multi_plot_settings = kwargs.pop('multi_plot_kwargs', dict())
        self.split_plot_settings = kwargs.pop('split_plot_kwargs', dict())
        if self.debug:
            print('corr_plot_settings: ', self.corr_plot_settings)
            print('corr_table_settings: ', self.corr_table_settings)
            print('multi_plot_settings: ', self.multi_plot_settings)
            print('split_plot_settings: ', self.split_plot_settings)

        self.plotly_color_scales = ['aggrnyl', 'agsunset', 'blackbody', 'bluered',
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
        self.plotly_templates = ['plotly', 'plotly_white', 'plotly_dark',
                                 'ggplot2', 'seaborn', 'simple_white', 'none']

    def corr_plot(self, df,
                  x_col: str,
                  y_col: str,
                  units: list = None,
                  title: str = None,
                  subtitle: str = None):
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

        if self.debug:
            print(df.head, x_col, y_col, units, title, subtitle)
        if title is None:
            title = f'Correlation plot of {x_col} and {y_col}.'
        if subtitle is None:
            subtitle = f'{x_col} (on the <i>x</i>-axis) vs  ' \
                       f'{y_col} (on the <i>y</i>-axis) ' \

        if not isinstance(units, list):
            units = [x_col, y_col]

        # load general settings for corr-plot
        use_latex = self.corr_plot_settings.get('use_latex', True)
        width = self.corr_plot_settings.get('width', None)
        if not isinstance(width, int):
            width = None
        elif width < 200:
            width = None
        height = self.corr_plot_settings.get('height', None)
        if not isinstance(height, int):
            height = None
        elif height < 200:
            height = None
        template = self.corr_plot_settings.get('template', None)
        if template not in self.plotly_templates:
            template = 'plotly'
        color_scale = self.corr_plot_settings.get('color_scale', None)
        if color_scale not in self.plotly_color_scales:
            color_scale = "blues"

        df = df.copy()
        if 'TIMESTAMP' not in [c.upper() for c in df.columns]:
            df.reset_index(inplace=True)

        if all(isinstance(x, tuple) for x in units):
            if use_latex and self.latex is not None:
                x_label = self.latex.var_unit_to_latex(var_unit=units[0])
                y_label = self.latex.var_unit_to_latex(var_unit=units[1])
            else:
                x_label = units[0][0] + ' ' + units[0][1]
                y_label = units[1][0] + ' ' + units[1][1]
        elif all(isinstance(x, str) for x in units):
            if use_latex and self.latex is not None:
                x_label = self.latex.var_to_latex(var=units[0])
                y_label = self.latex.var_to_latex(var=units[1])
            else:
                x_label = units[0]
                y_label = units[1]

        fig = go.Figure(px.scatter(df, x=x_col, y=y_col,
                                   trendline="ols",
                                   color=df.index,
                                   color_continuous_scale=color_scale,
                                   title=title),
                        layout={'title': {'text': title+'aaaaa',
                                          'y': 0.9,
                                          'x': 0.1,
                                          #'xanchor': 'left',
                                          'yanchor': 'top'},
                                'template': template})

        fig.update_layout(title=title,
                          height=height,
                          width=width,
                          annotations=[dict(xref='paper',
                                            yref='paper',
                                            x=0.5, y=1.05,
                                            showarrow=False,
                                            text=subtitle)],
                          xaxis=dict(title=x_label,
                                     zeroline=True,
                                     zerolinecolor='black'),
                          yaxis=dict(title=y_label,
                                     zeroline=True,
                                     zerolinecolor='black')
                          )

        if len(df) > 14:
            last_date = str(df['TIMESTAMP'].values.max())[:16]
            first_date = str(df['TIMESTAMP'].values.min())[:16]
            tick_ind = [0, 1, 2,
                        3, 4, 5,
                        len(df) - 9, len(df) - 8, len(df) - 7,
                        len(df) - 6, len(df) - 5, len(df) - 4,
                        len(df) - 3, len(df) - 2, len(df) - 1]
            tick_text = ['', '', '',
                         '', '', f"<sub>Sampled on <br>{first_date}</sub>",
                         f"<sub>Sampled on <br>{last_date}</sub>", '', '',
                         '', '', '',
                         '', '', '']
        else:
            tick_ind = [0, 1]
            tick_text = ['', '']

        colorbar_height = 0.8 * height if height else None

        fig.update_layout(coloraxis_colorbar=dict(title="Color mapping<br>",
                                                  tickvals=tick_ind,
                                                  ticktext=tick_text,
                                                  lenmode="pixels",
                                                  len=colorbar_height))
        return fig

    def multi_plot(self, df,
                   yaxis1: list(),
                   units1: list() = None,
                   yaxis2: list() = None,
                   units2: list() = None,
                   title: str = None,
                   subtitle: str = None):
        df = df.copy()

        if 'TIMESTAMP' not in df.columns:
            if 'TIMESTAMP' in [c.upper() for c in df.columns]:
                df.rename(columns={c: 'TIMESTAMP' for c in df.columns
                                   if c.upper() == 'TIMESTAMP'},
                          inplace=True)
            else:
                df.reset_index(inplace=True)
                df.rename(columns={'index': 'TIMESTAMP'},
                          inplace=True)

        if not(isinstance(units1, list) and len(units1) == len(yaxis1)):
            units1 = yaxis1
        if yaxis2 is None:
            yaxis2 = []
        if not (isinstance(units2, list) and len(units2) == len(yaxis2)):
            units2 = yaxis2
        if title is None:
            title = f'Multiplot plot of {", ".join(yaxis1.extend(yaxis2))}.'
        if subtitle is None:
            subtitle = f'Multiplot plot of {", ".join(yaxis1.extend(yaxis2))}.'
        if title == subtitle:
            subtitle = ''

        # load general settings for corr-plot
        use_latex = self.multi_plot_settings.get('use_latex', True)
        if use_latex:
            lat = self.latex
        else:
            lat = False
        if self.debug:
            print('in multi-plot')
            print(use_latex)
            print(lat)

        width = self.multi_plot_settings.get('width', None)
        if not isinstance(width, int):
            width = None
        elif width < 200:
            width = None
        height = self.multi_plot_settings.get('height', None)
        if not isinstance(height, int):
            height = None
        elif height < 200:
            height = None
        template = self.multi_plot_settings.get('template', None)
        if template not in self.plotly_templates:
            template = 'plotly'

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_layout(title_text=title,
                          width=width,
                          height=height,
                          template=template)

        # Fix labels for y-axes
        y_labels = []
        unit_ls = [units1]
        if units2:
            unit_ls.append(units2)
        for u in unit_ls:
            if all(isinstance(x, tuple) for x in u):
                y_unit = u[0][1]
                y_vars = [u[i][0] for i in range(len(u))
                          if all(u[i][0] != u[j][0] for j in range(i))]
                if lat:
                    y_unit = lat.unit_to_latex(unit=y_unit,
                                               no_dollar=True)
                    y_vars = [lat.var_to_latex(var=y,
                                               no_dollar=True) for y in y_vars]
                    y_label = f'${", ".join(y_vars)}\\ \\left({y_unit}\\right)$'
                else:
                    y_label = f'{", ".join(y_vars)}\\ ({y_unit})'
            elif all(isinstance(x, str) for x in u):
                if lat:
                    y_vars = [lat.var_to_latex(var=y,
                                               no_dollar=True) for y in u]
                    y_label = f'${", ".join(y_vars)}$'
                else:
                    y_label = f'{", ".join(u)}'
            else:
                y_label = ''
            y_labels.append(y_label)

        for i in range(len(yaxis1)):
            c = yaxis1[i]
            # plotting y1-axis
            fig.add_trace(go.Scatter(x=df.TIMESTAMP,
                                     y=df[c],
                                     name=f"{c}"),
                          secondary_y=False)

        for i in range(len(yaxis2)):
            c = yaxis2[i]
            # plotting y2-axis
            fig.add_trace(go.Scatter(x=df.TIMESTAMP,
                                     y=df[c],
                                     name=f"{c}"),
                          secondary_y=True)

        # Set x-axis title
        fig.update_xaxes(title_text="Time")

        # Set y-axes titles
        fig.update_yaxes(title_text=f"{y_labels[0]}", secondary_y=False)
        if yaxis2:
            fig.update_yaxes(title_text=f"{y_labels[1]}", secondary_y=True)

        return fig

    def split_plot(self, df,
                   units: list = None,
                   title: str = None,
                   n: int = None,
                   **setting):
        """

            For a pandas dataframe df, with a datetime index, this function
            returns a plotly figure containing separate graphs of each
            column of df. The plots are interconnected through common
            (empty) rangesliders (a zoom tool).

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
        ncols = len(cols)

        if isinstance(units, list) and len(units) == ncols:
            unit_ls = units
        else:
            unit_ls = cols

        title = title if isinstance(title, str) else ''

        # load general settings for corr-plot
        use_latex = self.split_plot_settings.get('use_latex', True)
        if use_latex:
            lat = self.latex
        else:
            lat = False

        width = self.split_plot_settings.get('width', None)
        if not isinstance(width, int):
            width = None
        elif width < 200:
            width = None
        height = self.split_plot_settings.get('height', None)
        if not isinstance(height, int):
            height = None
        elif height < 200:
            height = None
        subtitle_size = self.split_plot_settings.get('subtitle_size', None)
        if not isinstance(subtitle_size, int):
            subtitle_size = None
        template = self.split_plot_settings.get('template', None)
        if template not in self.plotly_templates:
            template = 'plotly'
        n = self.split_plot_settings.get('zoom_sliders', None)
        if not (isinstance(n, int) and n >= 0):
            n = 2
        elif n == 0:
            n = ncols
        n = min(n, ncols)

        if n == 0:
            n = ncols
        # for n!=0 nsliders = max(int(ncols/n),1)

        # Step 1.
        # We create a list of graphs where
        # every n:th graph is empty (WA-1)
        graphs = []
        y_ax_labels = []
        g_empty = go.Scatter(name='hidden')
        slider_no = 1
        pos = 0
        empty_positions = []

        for c in range(ncols):
            col = cols[c]

            # formatting y-axis labels
            if isinstance(unit_ls[c], tuple):
                if lat:
                    y_label = lat.var_unit_to_latex(var_unit=unit_ls[c])
                else:
                    y_label = unit_ls[c][0] + ' ' + unit_ls[c][1]
            elif isinstance(unit_ls[c], str):
                if lat:
                    y_label = lat.var_to_latex(unit_ls[c])
                else:
                    y_label = unit_ls[c]
            else:
                y_label = ''

            if self.debug:
                print('split-plot, y-labels: ', unit_ls[c], y_label)
            y_ax_labels.append(y_label)

            g_real = go.Scatter(x=df.index,
                                y=df[col],
                                name=col)

            graphs.append(g_real)

            pos += 1
            if pos % n == 0 and ncols - c > n:
                # (WA-1)
                # We place the empty graph right before the last real graph.
                graphs.insert(-1, g_empty)
                empty_positions.append(len(graphs) - 1)
                slider_no += 1

        # (WA-1)
        # Finally we put an empty graph right beefore the last real graph
        graphs.insert(-1, g_empty)
        empty_positions.append(len(graphs) - 1)

        # Step 2.
        # Next, we create a figure for the graphs.
        number_of_subplots = len(graphs)
        if height is None:
            fig_height = number_of_subplots * 175 + slider_no * 5
        else:
            fig_height = max(number_of_subplots * 175 + slider_no * 5, height)

        vert_space = 0.15 * (1 / (number_of_subplots - 1))

        # Labels and heights for each graph
        row_heights = [0.45 / ncols] * ncols
        labels = cols
        for x in empty_positions:
            row_heights.insert(x, 0.12 / ncols)
            labels.insert(x, '')
            y_ax_labels.insert(x, '')

        fig = make_subplots(rows=number_of_subplots, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=vert_space,
                            subplot_titles=labels,
                            row_heights=row_heights)
        for i in fig['layout']['annotations']:
            i['font']['size'] = 10

        fig.update_layout(template=template,
                          height=fig_height,
                          width=width,
                          title=title)

        # Step 3.
        # Add the graphs to the figure, and some styling
        fig.add_traces(graphs,
                       rows=list(range(1, number_of_subplots + 1)),
                       cols=[1] * number_of_subplots)

        # Remove all dates of each x-axis
        for x in range(1, number_of_subplots + 1):
            fig.update_xaxes(row=x, col=1, showticklabels=False)
            fig.update_yaxes(row=x, col=1, title_text=y_ax_labels[x - 1])

        # Set font size
        fig.update_annotations(font_size=18)

        # Step 4 (WA-2)
        # We will now create rangesliders from the empty graphs,
        # adjust thickness compared to number of plots,
        # make sure the xaxis has type 'date' and show
        # the dates on this x-axis

        for pos in empty_positions:
            fig.update_xaxes(rangeslider={'visible': True, 'thickness': vert_space},
                             type='date',
                             showticklabels=True,
                             row=pos, col=1)

        # Step 5 (WA-3)
        # We will now place the first graph G after each empty graph E
        # over the graph E. That is: [G1,G2,E1,G3,G4,G5,E2,G6] -> [G1,G2,G3,G4,G5,G6]
        hidden_y_ax = ''

        for _, t in enumerate(fig.data):

            if hidden_y_ax:
                t.yaxis = hidden_y_ax
                hidden_y_ax = ''

            if t.name == 'hidden':
                hidden_y_ax = t.yaxis

        return fig
