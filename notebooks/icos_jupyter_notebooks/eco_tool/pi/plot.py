#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Library for plotting ICOS data.
    
    Examples
    --------
    >>> # To produce 9 graphs of 9 variables, from a 
    >>> # dataframe df with an, interconected zoom slider 
    >>> # below every second graph, use:  
    >>> ### 1. On jupyter:
    >>> fig = multi_plot(df,2,units=unit_ls)
    >>> fig.show()
    ...
    >>> ### 2. On local computer:
    >>> from plotly.offline import plot
    >>> 
    >>> fig = multi_plot(df,2,units=unit_ls)
    >>> plot(f, include_mathjax='cdn')
    
"""

__author__      = ["Anders Dahlner"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPLv3+"
__version__     = "0.0.1"
__maintainer__  = "ICOS Carbon Portal, Elaborated products team"
__email__       = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pi import icos2latex


def multi_plot(df,n=0,**setting):
    """

        For a pandas dataframe df, with a datetime index, this function 
        returns a plotly figure containing separate graphs of each 
        column of df. The plots are interconnected through common 
        (empty) rangesliders (a zoom tool).
            
        Inputs: 
        - df: a pandas dataframe.
            It is assumed that df has a datatime index.
        - n: int
            n is the number of plots between each zoom slider.
            For n!=0, the number of sliders is given by 
                max(int("number of columns" / n),1)  
            for n=0, will only give one rangeslider in the end.
        
        Possible setting keys:
        - units: a list of strings or a list of tuples. 
            Where the k:th element correspond to the k:th column of df.
            In the case of a tuple (a,b) a is the variable and b is the 
            unit. 
        - title: str
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
    
    unit_ls = setting.pop('units',cols)
    unit_ls = unit_ls if isinstance(unit_ls,list) and len(unit_ls)==ncols else cols 

    debug = setting.pop('debug',False)
    debug = debug if isinstance(debug,bool) else False 

    title = setting.pop('title','') 
    title = title if isinstance(title,str) else ''

    use_latex = setting.pop('use_latex', True) 
    use_latex = use_latex if isinstance(use_latex,bool) else True
    
    latex_settings = setting.pop('latex_settings', {})  
    latex_settings = latex_settings if isinstance(latex_settings, dict) else {}
    
    latex = icos2latex.Translator(**latex_settings)
    
    if n==0:
        n = ncols
    # For n!=0 nsliders = max(int(ncols/n),1)
    
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
        if isinstance(unit_ls[c],tuple):
            if use_latex:
                y_label = latex.var_unit_to_latex(unit_ls[c][0], 
                                                  unit_ls[c][1])
            else:
                y_label = unit_ls[c][0] + ' ' + unit_ls[c][1]
        elif isinstance(unit_ls[c],str):
            if use_latex:
                
                y_label = latex.var_to_latex(unit_ls[c])
            else:
                y_label = unit_ls[c]
        else:
            y_label = ''
        
        if debug: 
            print(y_label)
        y_ax_labels.append(y_label)
            
        g_real = go.Scatter(x=df.index, y=df[col], name=col)
        
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
    row_heights = [0.45/(ncols)]*ncols
    labels = cols
    for x in empty_positions:
        row_heights.insert(x,0.12/ncols) 
        labels.insert(x,'')
        y_ax_labels.insert(x,'')

    fig = make_subplots(rows=number_of_subplots, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=vert_space, 
                        subplot_titles=labels,
                        row_heights=row_heights)
    
    fig.update_layout(height=fig_height, title=title)
    
    
    # Step 3. 
    # Add the graphs to the figure, and some styling
    fig.add_traces(graphs, 
                   rows=list(range(1,number_of_subplots+1)),
                   cols=[1]*number_of_subplots)
   
    # Remove all dates of each x-axis
    for x in range(1,number_of_subplots + 1):
        fig.update_xaxes(row=x, col=1, showticklabels= False)
        fig.update_yaxes(row=x, col=1, title_text= y_ax_labels[x-1])
    
    # Set font size 
    fig.update_annotations(font_size=12)

    # Step 4 (WA-2)
    # We will now create rangesliders from the empty graphs, 
    # adjust thickness compared to number of plots, 
    # make sure the xaxis has type 'date' and show 
    # the dates on this x-axis
    
    for pos in empty_positions:
        fig.update_xaxes(rangeslider= {'visible': True, 'thickness': vert_space}, 
                         type = 'date',
                         showticklabels= True,
                         row=pos, col=1)
    
    # Step 5 (WA-3)
    # We will now place the first graph G after each empty graph E 
    # over the graph E. That is: [G1,G2,E1,G3,G4,G5,E2,G6] -> [G1,G2,G3,G4,G5,G6]
    hidden_y_ax = ''
    
    for i,t in enumerate(fig.data):
        
        if hidden_y_ax:
            t.yaxis = hidden_y_ax
            hidden_y_ax = ''
            
        if t.name == 'hidden':
            hidden_y_ax = t.yaxis
            
        

    return fig
    