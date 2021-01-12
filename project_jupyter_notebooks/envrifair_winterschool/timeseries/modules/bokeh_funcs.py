def add_bokeh_label(fig, x_coor, y_coor, unit, txt_str, txt_font_size, alignment):
    
    """
    Project:       ICOS Carbon Portal
    Date created:  2020-08-19
    Last modified: 2020-08-19
    Developed by:  Karolina
    
    Definition:    Function that adds a label to a Bokeh plot at a defined location.
    
    Input:         1. Bokeh plot object (var_name: "fig", var_type: python object)
                   2. x coordinate of the bottom left part of the label (var_name: "x_coor", var_type: float)
                   3. y coordinate of the bottom left part of the label (var_name: "y_coor", var_type: float)
                   4. unit of x- & y-coordinates e.g. "screen" (var_name: "unit", var_type: string)
                   5. label content - text (var_name: "txt_str", var_type: string)
                   6. font size of text in label (var_name: "txt_font_size", var_type: float)
                   7. alignment of label based on x- & y-coord, e.g. "below" 
                     (var_name: "alignment", var_type: string)
    
    Output:       The function adds a label to an existent plot object but does not return any values.
    """
    
    #Import modules:
    from bokeh.models import Label
    
    #Set the label position:
    label_opts = dict(x=x_coor, y=y_coor, x_units=unit, y_units=unit)
    
    #Create the label object:
    caption = Label(text=txt_str, **label_opts)
    
    #Format label object - set label-text font size:
    caption.text_font_size = txt_font_size
    
    #Add label to plot:
    fig.add_layout(caption, alignment) 


#####################################################################################################################

#add interactive plot (optional)
def plot_icos_single_station_binary(dobj, var, glyph, color='#0F0C08'):
    
    
    #Import modules:
    import numpy as np
    import pandas as pd
    from bokeh.plotting import figure
    from bokeh.models import ColumnDataSource, HoverTool, Label, Legend
    
    #Dictionary for subscript transformations of numbers:
    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    
    #Check if dobj has data:
    if ((isinstance(dobj.get(), pd.DataFrame))&(var in dobj.get().columns.values)):
        
        #Get dataframe with data for current dobj:
        df = dobj.get()
        
        #Check if selected var is "st dev":
        if (any([sub_str in var for sub_str in ['Stdev']])):

            #Replace st dev-value "-9,999" to NaN:
            df[df[var] < 0] = np.nan
        
                
        #Check if column for selected variable includes only NaNs:
        if (df[var].isnull().all()==False):
        
            #Remove "-" from variable column name:
            new_var = var.replace('-','')

            #Replace var-column name in dataframe:
            df.rename(columns={var:new_var}, inplace=True)


            #Create a ColumnDataSource object:
            source = ColumnDataSource( data = df )


            #Check if variable has unit-info:
            if(dobj.info[1].unit.loc[dobj.info[1].colName==var].isnull().values[0]):
                unit = ''
            else:
                unit = '('+dobj.info[1].unit.loc[dobj.info[1].colName==var].values[0]+')'

            #Check if sampling height is empty:
            if(dobj.info[2].samplingHeight.values[0]):
                sampl_height = ' ('+ dobj.info[2].samplingHeight.values[0] +' m.a.g.l.)'
            else:
                sampl_height = ''



            #Create a figure object:
            p = figure(plot_width=900,
                       plot_height=400,
                       x_axis_label='Time (UTC)', 
                       y_axis_label=var.upper().translate(SUB)+' '+unit,
                       x_axis_type='datetime',
                       title = dobj.info[1].valueType.loc[dobj.info[1].colName==var].values[0]+'  -  '+
                       dobj.station + sampl_height,
                       tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')


            #Check glyph:
            if(glyph=='line'):

                #Create circle glyph:
                g0 = p.circle('TIMESTAMP',new_var, source=source, radius=.02, color=color)

                #Create line glyph:
                g1 = p.line('TIMESTAMP',new_var, source=source, line_width=1, color=color)

            else:

                #Create circle glyph:
                g2 = p.circle('TIMESTAMP',new_var, source=source, size=4, alpha=0.5, color=color)


            #Set title attributes:
            p.title.align = 'center'
            p.title.text_font_size = '13pt'
            p.title.offset = 15

            #Set label font style:
            p.xaxis.axis_label_text_font_style = 'normal'
            p.yaxis.axis_label_text_font_style = 'normal'
            p.xaxis.axis_label_standoff = 15 #Sets the distance of the label from the x-axis in screen units
            p.yaxis.axis_label_standoff = 15 #Sets the distance of the label from the y-axis in screen units

            #Set grid format:
            p.grid.grid_line_alpha = 0
            p.ygrid.band_fill_color = "olive"
            p.ygrid.band_fill_alpha = 0.1

            #Add label with copyright info:
            add_bokeh_label(p, 0, 10, 'screen', "© ICOS ERIC", '8pt', 'below')

            #Add label with license info:
            add_bokeh_label(p, 770, 24, 'screen', "CC4BY", '8pt', 'below')


            #Deactivate hover-tool, which is by default active:
            p.toolbar.active_inspect = None
            
            

            #Check if the selected variable is time:
            if (any([sub_string in var for sub_string in ['time', 'TIME']])):
                
                #Add hover tool:
                p.add_tools(HoverTool(tooltips=[("Time (UTC)","@TIMESTAMP{%Y-%m-%d %H:%M:%S}"),
                                                ("Time (UTC)", "@"+new_var+"{%Y-%m-%d %H:%M:%S}"),],
                                      formatters={"@TIMESTAMP": "datetime",
                                                  "@"+new_var: "datetime",},
                                      # display a tooltip whenever the cursor is vertically in line with a glyph
                                      mode="vline"))    
                
                
            else:
                #Add hover tool:
                p.add_tools(HoverTool(tooltips=[("Time (UTC)","@TIMESTAMP{%Y-%m-%d %H:%M:%S}"),
                                                (var, "@"+new_var+"{0.00}"),
                                                ("Flag", "@Flag"),
                                                ("NbPoints","@NbPoints"),
                                                ("Stdev", "@Stdev{0.00}"),],
                                      formatters={"@TIMESTAMP": "datetime",},
                                      # display a tooltip whenever the cursor is vertically in line with a glyph
                                      mode="vline"))    

            #return plot:
            return p
        
        else:
            return False
            
    else:
        return False
#####################################################################################################################

#interactive bokeh plot for pandas series
def plot_ps_timeseries(ps, glyph, title, xlabel, ylabel, color='#0F0C08'):
    
    
    #Import modules:
    import numpy as np
    import pandas as pd
    from bokeh.plotting import figure
    from bokeh.models import ColumnDataSource, HoverTool, Label, Legend
    
    #Dictionary for subscript transformations of numbers:
    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    
    #Check if pandas series has data:
    if (isinstance(ps, pd.Series)):
           
        #Check if column for selected variable includes only NaNs:
        if (ps.isnull().all()==False):
        
            #Create a ColumnDataSource object:
            #source = ColumnDataSource( data = ps )

            #Create a figure object:
            p = figure(plot_width=900,
                       plot_height=400,
                       x_axis_label=xlabel.upper(), 
                       y_axis_label=ylabel.upper().translate(SUB),
                       x_axis_type='datetime',
                       title = title,
                       tools='pan,box_zoom,wheel_zoom,undo,redo,reset,save')


            #Check glyph:
            if(glyph=='line'):

                #Create circle glyph:
                g0 = p.circle(ps.index, ps.values, radius=.02, color=color)

                #Create line glyph:
                g1 = p.line(ps.index, ps.values, line_width=1, color=color)

            else:

                #Create circle glyph:
                g2 = p.circle(ps.index, ps.values, size=4, alpha=0.5, color=color)


            #Set title attributes:
            p.title.align = 'center'
            p.title.text_font_size = '13pt'
            p.title.offset = 15

            #Set label font style:
            p.xaxis.axis_label_text_font_style = 'normal'
            p.yaxis.axis_label_text_font_style = 'normal'
            p.xaxis.axis_label_standoff = 15 #Sets the distance of the label from the x-axis in screen units
            p.yaxis.axis_label_standoff = 15 #Sets the distance of the label from the y-axis in screen units

            #Set grid format:
            p.grid.grid_line_alpha = 0
            p.ygrid.band_fill_color = "olive"
            p.ygrid.band_fill_alpha = 0.1

            #Add label with copyright info:
            add_bokeh_label(p, 0, 10, 'screen', "© ICOS ERIC", '8pt', 'below')

            #Add label with license info:
            add_bokeh_label(p, 770, 24, 'screen', "CC4BY", '8pt', 'below')


            #Deactivate hover-tool, which is by default active:
            p.toolbar.active_inspect = None
            
    
            #Add hover tool:
            p.add_tools(HoverTool(tooltips=[(xlabel,"@x{%Y-%m-%d %H:%M:%S}"),
                                            (ylabel, "@y{0.00}"),],
                                  formatters={"@x": "datetime",},
                                  # display a tooltip whenever the cursor is vertically in line with a glyph
                                  mode="vline"))    

            #return plot:
            return p
        
        else:
            return False
            
    else:
        return False