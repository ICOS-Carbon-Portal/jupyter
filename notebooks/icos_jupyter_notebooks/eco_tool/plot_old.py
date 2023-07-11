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

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from eco_tool import icos2latex


#class Plot():
_plotly_color_scales = ['aggrnyl', 'agsunset', 'blackbody', 'bluered',
                        'blues', 'blugrn', 'bluyl', 'brwnyl', 'bugn',
                        'bupu', 'burg', 'burgyl', 'cividis', 'darkmint',
                        'electric', 'emrld', 'gnbu', 'greens', 'greys',
                        'hot', 'inferno', 'jet', 'magenta', 'magma',
                        'mint', 'orrd', 'oranges', 'oryel', 'peach',
                        'pinkyl', 'plasma', 'plotly3', 'pubu', 'pubugn',
                        'purd', 'purp', 'purples', 'purpor', 'rainbow',
                        'rdbu', 'rdpu', 'redor', 'reds', 'sunset',
                        'sunsetdark', 'teal', 'tealgrn', 'turbo',
                        'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd',
                        'algae', 'amp', 'deep', 'dense', 'gray', 'haline',
                        'ice', 'matter', 'solar', 'speed', 'tempo',
                        'thermal', 'turbid', 'armyrose', 'brbg', 'earth',
                        'fall', 'geyser', 'prgn', 'piyg', 'picnic',
                        'portland', 'puor', 'rdgy', 'rdylbu', 'rdylgn',
                        'spectral', 'tealrose', 'temps', 'tropic',
                        'balance', 'curl', 'delta', 'oxy', 'edge', 'hsv',
                        'icefire', 'phase', 'twilight', 'mrybm', 'mygbm']
_plotly_templates = ['plotly', 'plotly_white', 'plotly_dark', 'ggplot2',
                     'seaborn', 'simple_white', 'none']

def corr_plot(df, x_col: str = None, y_col: str = None, **kwargs):
    """
            For a pandas dataframe df, this function
            returns a plotly figure with a scatter plot of
            two columns.

            Inputs:
            -------
            - df: a pandas dataframe.
            - x_col: str
                name of variable for the x-axis
            - y_col:str
                name of variable for the y-axis

            Keys of settings:
            -----------------
            - title: str
            - color_scale: str
                an element of _plotly_templates,
                otherwise "plotly" is used
            - use_latex: bool
                Default is True. This applies to the title of the y-axis.
            - latex_setting: dict
                See pi.icos2latex for details.

    """

    title = kwargs.pop('title', None)
    if title is None:
        title = f'Correlation plot of {x_col} and {y_col}.'
    subtitle = kwargs.pop('subtitle', None)
    if subtitle is None:
        subtitle = f'{x_col} vs {y_col} (<i>colors: light = early timestamp, ' \
                f'dark latest timestamp</i>)'
    units = kwargs.pop('units', None)
    if not isinstance(units, list):
        units = [(x_col,1), (y_col,2)]
    width = kwargs.pop('width', None)
    height = kwargs.pop('height', None)
    template = kwargs.pop('template', None)
    color_scale = kwargs.pop('color_scale', None)
    if color_scale not in _plotly_color_scales:
        color_scale = "blues"
    use_latex = kwargs.pop('use_latex', True)
    latex_settings = kwargs.pop('latex_settings', {})
    latex = icos2latex.Translator(**latex_settings)

    df = df.copy()
    if 'TIMESTAMP' not in [c.upper() for c in df.columns]:
        df.reset_index(inplace=True)

    if all(isinstance(x, tuple) for x in units):
        if use_latex:
            x_label = latex.var_unit_to_latex(var_unit=units[0])
            y_label = latex.var_unit_to_latex(var_unit=units[1])
        else:
            x_label = units[0][0] + ' ' + units[0][1]
            y_label = units[1][0] + ' ' + units[1][1]
    elif all(isinstance(x, str) for x in units):
        if use_latex:
            x_label = latex.var_to_latex(var=units[0])
            y_label = latex.var_to_latex(var=units[1])
        else:
            x_label = units[0]
            y_label = units[1]

    fig = px.scatter(df, x=x_col, y=y_col,
                     trendline="ols",
                     color=df.index,
                     color_continuous_scale=color_scale,
                     title=title)
    fig.update_layout(height=height,
                      width= width,
                      annotations=[dict(xref='paper',
                                        yref='paper',
                                        x=0.5, y=1.15,
                                        showarrow=False,
                                        text=subtitle)],
                      xaxis=dict(title=x_label,
                                 zeroline=True,
                                 zerolinecolor='black'),
                      yaxis=dict(title=y_label,
                                 zeroline=True,
                                 zerolinecolor='black')
                      )

    if len(df) > 11:
        last_date = str(df['TIMESTAMP'].values.max())[:16]
        first_date = str(df['TIMESTAMP'].values.min())[:16]
        tick_ind = [0, 1, 2, 3, 4, 5,
                    len(df) - 6, len(df) - 5, len(df) - 4, len(df) -
                    3, len(df) - 2,
                    len(df) - 1]
        tick_text = ['', '', '', '', '', f"Sampled on <br>{first_date}",
                     f"Sampled on <br>{last_date}", '', '', '', '', '']
    else:
        tick_ind = [0, 1]
        tick_text = ['', '']

    colorbar_height = 0.6 * height if height else None

    fig.update_layout(coloraxis_colorbar=dict(title="Color mapping",
                                              tickvals=tick_ind,
                                              ticktext=tick_text,
                                              lenmode="pixels",
                                              len=colorbar_height))

    return fig


def _multi_plot_2_y_axis(df, **kwargs):

    title = kwargs.pop('title', 'title')
    units1 = kwargs.pop('units1', 'yaxis1')
    units2 = kwargs.pop('units2', 'yaxis2')
    yaxis1 = kwargs.pop('yaxis1', [])
    yaxis2 = kwargs.pop('yaxis2', [])
    font_size = kwargs.pop('font_size', None)
    font_family = kwargs.pop('font_family', None)
    text_color = kwargs.pop('color', None)
    width = kwargs.pop('width', None)
    height = kwargs.pop('height', None)
    graph_style = kwargs.pop('graph_style', None)
    template = kwargs.pop('template', 'plotly')
    if template not in _plotly_templates:
        template = "plotly"

    use_latex = kwargs.pop('use_latex', True)
    latex_settings = kwargs.pop('latex_settings', {})
    latex = icos2latex.Translator(**latex_settings)

    fig = go.Figure()

    # cols = list(df.columns)
    # cols.remove('TIMESTAMP')
    # for col in cols:
    #     f = df[['TIMESTAMP', col]]
    #     y_ax_labels = []
    #
    #     # formatting y-axis labels
    #     if isinstance(unit_ls[col], tuple):
    #         if use_latex:
    #             y_label = latex.var_unit_to_latex(var_unit=unit_ls[col])
    #         else:
    #             y_label = unit_ls[col][0] + ' ' + unit_ls[col][1]
    #     elif isinstance(unit_ls[col], str):
    #         if use_latex:
    #
    #             y_label = latex.var_to_latex(unit_ls[col])
    #         else:
    #             y_label = unit_ls[col]
    #     else:
    #         y_label = ''

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    var_ls = []
    unit = latex.unit_to_latex(unit=units1[0][1])
    for i in range(len(yaxis1)):
        c = yaxis1[i]
        # formatting y-axis labels
        if isinstance(units1[i], tuple):
            if use_latex:
                var_ls.append(latex.var_to_latex(var=units1[i][0]))
        fig.add_trace(go.Scatter(x=df.TIMESTAMP,
                                 y=df[c],
                                 name=f"{c}"),
                      secondary_y=False)
    unit = f'$({unit.replace("$","")})$'
    y1_label = f'{", ".join(var_ls)}, {unit}'.replace('$, $', ',\ ')

    if yaxis2:
        var_ls = []
        unit = latex.unit_to_latex(unit=units2[0][1])
        for i in range(len(yaxis2)):
            c = yaxis2[i]
            # formatting y-axis labels
            if isinstance(units2[i], tuple):
                if use_latex:
                    var_ls.append(latex.var_to_latex(var=units2[i][0]))
            fig.add_trace(
                go.Scatter(x=df.TIMESTAMP, y=df[c], name=f"{c}"),
                secondary_y=True,
            )
        unit = f'$({unit.replace("$", "")})$'
        y2_label = f'{", ".join(var_ls)}, {unit}'.replace('$, $', ',\ ')

    # Add figure title
    fig.update_layout(title_text=title, width=800, height=400)

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(title_text=f"{y1_label}", secondary_y=False)
    if yaxis2:
        fig.update_yaxes(title_text=f"{y2_label}", secondary_y=True)

    return fig


def multi_plot(df, **kwargs):
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

    return _multi_plot_2_y_axis(df, **kwargs)

    # font_size = kwargs.pop('font_size', None)
    # font_family = kwargs.pop('font_family', None)
    # text_color = kwargs.pop('color', None)
    # width = kwargs.pop('width', None)
    # height = kwargs.pop('height', None)
    # graph_style = kwargs.pop('graph_style', None)
    # template = kwargs.pop('template', None)
    # if template not in _plotly_templates:
    #     template = "plotly"
    # unit_ls = kwargs.pop('units', None)
    # if unit_ls is None:
    #     unit_ls = df.columns
    # elif all(isinstance(x, tuple) for x in unit_ls):
    #     try:
    #         unit_dict = {t[0]: t[1] for t in unit_ls}
    #     except:
    #         unit_dict = {}
    #         unit_ls = df.columns
    # else:
    #     unit_dict = {}
    #
    # title = kwargs.pop('title', '')
    # debug = kwargs.pop('debug', False)
    #
    # template = kwargs.pop('template', True)
    # use_latex = kwargs.pop('use_latex', True)
    # latex_settings = kwargs.pop('latex_settings', {})
    # latex = icos2latex.Translator(**latex_settings)
    #
    # number_of_y_axes = len(set(v for v in unit_dict.values()))
    #
    # fig = go.Figure()
    #
    # cols = list(df.columns)
    # cols.remove('TIMESTAMP')
    # for col in cols:
    #     f = df[['TIMESTAMP', col]]
    #     y_ax_labels = []
    #
    #     # formatting y-axis labels
    #     if isinstance(unit_ls[col], tuple):
    #         if use_latex:
    #             y_label = latex.var_unit_to_latex(var_unit=unit_ls[col])
    #         else:
    #             y_label = unit_ls[col][0] + ' ' + unit_ls[col][1]
    #     elif isinstance(unit_ls[col], str):
    #         if use_latex:
    #
    #             y_label = latex.var_to_latex(unit_ls[col])
    #         else:
    #             y_label = unit_ls[col]
    #     else:
    #         y_label = ''
    #
    #     if debug:
    #         print(unit_ls[col], y_label)
    #     y_ax_labels.append(y_label)
    #
    #     g_real = go.Scatter(x=df.index,
    #                         y=df[col],
    #                         name=col)
    #
    #     graphs.append(g_real)
    #
    #
    #     fig.add_trace(
    #         go.Scatter(x=f.TIMESTAMP,
    #                    y=f[col],
    #                    mode=graph_style,
    #                    marker=dict(symbol="circle",
    #                                sizeref=30),
    #                    name=col))
    #
    #     fig.update_layout(template=template,
    #                       hovermode="x unified",
    #                       height=height,
    #                       width=width)
    #
    # y_title = go.layout.yaxis.Title(font=dict(family=font_family,
    #                                           size=font_size,
    #                                           color=text_color),
    #                                 text=', '.join(cols))
    #
    # fig.update_yaxes(title=y_title)
    # fig.update_xaxes(title_text='Timestamp',
    #                  title_font_family=font_family,
    #                  title_font_size=font_size,
    #                  title_font_color=text_color)
    # return fig


def split_plot(df, n=0,
               units=None,
               title: str = None,
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

        Keys of settings:
        -----------------
        - use_latex: bool
            Default is True. This applies to the title of the y-axis.
        - latex_setting: dict
            See pi.icos2latex for details.

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

    debug = setting.pop('debug', False)
    debug = debug if isinstance(debug, bool) else False

    template = setting.pop('template', 'plotly')
    use_latex = setting.pop('use_latex', True) 
    use_latex = use_latex if isinstance(use_latex, bool) else True
    
    latex_settings = setting.pop('latex_settings', {})  
    latex_settings = latex_settings if isinstance(latex_settings, dict) else {}
    latex = icos2latex.Translator(**latex_settings)
    
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
            if use_latex:
                y_label = latex.var_unit_to_latex(var_unit=unit_ls[c])
            else:
                y_label = unit_ls[c][0] + ' ' + unit_ls[c][1]
        elif isinstance(unit_ls[c], str):
            if use_latex:
                y_label = latex.var_to_latex(unit_ls[c])
            else:
                y_label = unit_ls[c]
        else:
            y_label = ''
        
        if debug: 
            print(unit_ls[c], y_label)
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
    
    if latex:
        del latex
        
    # (WA-1)
    # Finally we put an empty graph right beefore the last real graph
    graphs.insert(-1, g_empty)
    empty_positions.append(len(graphs) - 1)

    # Step 2. 
    # Next, we create a figure for the graphs. 
    number_of_subplots = len(graphs)
    fig_height = number_of_subplots * 175 + slider_no * 5
    vert_space = 0.15 * (1 / (number_of_subplots - 1))   
    
    # Labels and heights for each graph
    row_heights = [0.45/ncols]*ncols
    labels = cols
    for x in empty_positions:
        row_heights.insert(x, 0.12/ncols)
        labels.insert(x, '')
        y_ax_labels.insert(x, '')

    fig = make_subplots(rows=number_of_subplots, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=vert_space, 
                        subplot_titles=labels,
                        row_heights=row_heights)
    
    fig.update_layout(template=template,
                      height=fig_height,
                      title=title)
    
    # Step 3.
    # Add the graphs to the figure, and some styling
    fig.add_traces(graphs, 
                   rows=list(range(1, number_of_subplots+1)),
                   cols=[1]*number_of_subplots)
   
    # Remove all dates of each x-axis
    for x in range(1, number_of_subplots + 1):
        fig.update_xaxes(row=x, col=1, showticklabels=False)
        fig.update_yaxes(row=x, col=1, title_text=y_ax_labels[x-1])
    
    # Set font size 
    fig.update_annotations(font_size=12)

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
    