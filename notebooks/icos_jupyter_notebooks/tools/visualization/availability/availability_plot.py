#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description: This file contains functions to display an interactive
                 availability table for ICOS data products.
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-13"




################################################################################### 
########################## FUNCTIONS THAT CONTROL INPUT ###########################
################################################################################### 

#Function that controls if input variable is a list of dataframes:
def check_ls_of_DFs(df_ls):
    
    #Import modules:
    import pandas as pd
    
    #Declare & intitialize check-variable:
    check = False
    
    #Check if input variable is a list of dataframes:
    if isinstance(df_ls, list):
        
        #Check if list is empty:
        if(len(df_ls)>0):
        
            #Get a list with the data type of every item in the list:
            data_type_ls = list(set([type(df_ls[i]) for i in range(len(df_ls))]))

            #Check that every item in the list is a pandas dataframe:
            if((len(data_type_ls)==1) & (data_type_ls[0]==pd.core.frame.DataFrame)):

                #Check if number of dataframes exceed 8:
                if(len(df_ls)<9):

                    #Set value of check-variable:
                    check = True

                else:
                    print('Cannot display more than 8 layers!')#colorblind palette restriction

            else:
                print('Expected list of pandas dataframes as input, but got list of', *data_type_ls)
        
        else:
            print('List is empty!')
            
    else:
        print('Expected list as input, but got ', type(df_ls))
        
    
    #Return check-variable
    return check
###################################################################################


#Function that checks if list of layer names consists of strings and
#contains the same number of items with corresponding list of dataframes.
def check_ls_of_layernames(ls, df_ls):
    
    #Declare & intitialize check-variable:
    check = False
    
    #Check if list of layer names contains the same number of
    #items with corresponding list of dataframes:
    if(len(ls)==len(df_ls)):
    
        #Check if input variable is a list of strings:
        if isinstance(ls, list):

            #Get a list with the data type of every item in the list:
            data_type_ls = list(set([type(ls[i]) for i in range(len(ls))]))

            #Check that every item in the list is a string:
            if((len(data_type_ls)==1) & (data_type_ls[0]==str)):

                #Set value of check-variable:
                check = True

            else:
                print('Expected list of strings as input, but got list of', *data_type_ls)

        else:
            print('Expected list as input, but got ', type(ls))
            
    else:
        print('List of layer names does not include the same number of items with corresponding list of dataframes.')

    
    #Return check-variable
    return check
################################################################################### 

#Function checking that all input parameters are valid:
def check_input(df_ls, layer_ls):
    
    #Declare & initialize check variable:
    check = False
    
    #Call functions to check input variables:
    if((check_ls_of_DFs(df_ls)==True)&
       (check_ls_of_layernames(layer_ls, df_ls)==True)):
        
        #Set check-value:
        check = True
    
    #Return check-value:
    return check
   
################################################################################### 
############################ END OF CONTROL FUNCTIONS #############################
################################################################################### 

#Function that creates and returns a Bokeh rectangle glyph:
def create_rect_glyph(figure_obj, plot_attr_obj, cdatasource, color, layer_name):
    
    #Import module:
    from bokeh.transform import dodge
    
    return figure_obj.rect(dodge(plot_attr_obj.col_name_xaxis,
                                 plot_attr_obj.rect_dodge_x,
                                 range=figure_obj.x_range),
                           dodge(plot_attr_obj.col_name_yaxis,
                                 plot_attr_obj.rect_dodge_y,
                                 range=figure_obj.y_range),
                           plot_attr_obj.rect_width,
                           plot_attr_obj.rect_height,
                           source=cdatasource,
                           fill_alpha=plot_attr_obj.rect_fill_alpha,
                           color=color,
                           name=layer_name)
################################################################################### 

#Function that returns a color palette specially
#adjusted for color-challenged people:
def get_cb_pallete(x):
    
    #Import modules:
    import numbers
    from bokeh.palettes import Colorblind
    
    
    #Check if input parameter is a number:
    if(isinstance(x, numbers.Number) & (x>0) & (x<9)):

            if((x<4)):

                return Colorblind[3]

            else:
                return Colorblind[x]
    
    else:
        print('Input not an integer or index out of range for colorblind palette!')
        return None
###################################################################################     
            
            

def plot_table(df_list, layer_list, t_list, plot_attr_obj):
    
    #Import modules:
    from bokeh.io import show, output_notebook, reset_output
    from bokeh.models import ColumnDataSource, Label, Legend
    from bokeh.plotting import figure
    
    #Define output location:
    reset_output()
    output_notebook()
    
    #Check input parameters:
    if (check_input(df_list, layer_list)):

        #Create a columndatasource obj for every dataframe in list:
        cdatasourse_ls =[ColumnDataSource(df_list[i])
                         for i in range(len(df_list))]
        
        #Get list with colors (from Bokeh's Colorblind palette):
        cpalette = get_cb_pallete(len(df_list))


        #Create figure:
        p = figure(plot_width=plot_attr_obj.width,
                   plot_height=plot_attr_obj.height,
                   title=plot_attr_obj.title_text,
                   tools=['hover', 'wheel_zoom', 'pan', 'reset', 'box_zoom'],
                   y_range=plot_attr_obj.y_range)

        #Add one rectangle glyph per dataframe:
        glyph_ls = [(layer_list[i],
                     [create_rect_glyph(p,
                                        plot_attr_obj,
                                        cdatasourse_ls[i],
                                        cpalette[i],
                                        layer_list[i])])
                    for i in range(len(cdatasourse_ls))]


        #Set title attributes:
        p.title.align = plot_attr_obj.title_align
        p.title.text_font_size = plot_attr_obj.title_font_size
        p.title.offset = plot_attr_obj.title_offset

        #Set x- & y-axis labels:
        p.xaxis.axis_label = plot_attr_obj.xaxis_label
        p.yaxis.axis_label = plot_attr_obj.yaxis_label
        

        #Set label font style:
        p.xaxis.axis_label_text_font_style = plot_attr_obj.xaxis_label_font_style
        p.yaxis.axis_label_text_font_style = plot_attr_obj.yaxis_label_font_style
        p.xaxis.axis_label_standoff = plot_attr_obj.xaxis_label_standoff
        p.yaxis.axis_label_standoff = plot_attr_obj.yaxis_label_standoff
        p.yaxis.major_label_text_font_size = plot_attr_obj.yaxis_label_text_font_size

        #Set the copyright label position:
        label_opts = dict(x=0, y=10,
                          x_units='screen', y_units='screen')

        #Create a label object and format it:
        caption1 = Label(text="© ICOS ERIC", **label_opts)
        caption1.text_font_size = '8pt'

        #Add label to plot:
        p.add_layout(caption1, 'below')


        #List with variables for tooltip in hover-tool:
        tooltip_ls = [("Data", "$name")]

        #Process input list with dataframe column names for tooltip:
        hover_var_ls = [tooltip_ls.insert(i, (t_list[i][0], '@'+t_list[i][1]))
                        for i in range(len(t_list))]

        #Add hover-tool:
        p.hover.tooltips = tooltip_ls

        #if ((len(glyph_ls)>3) & (len(glyph_ls)<7)):
            
            #Create legend:
            #legend1 = Legend(items=glyph_ls[:3], location=plot_attr_obj.legend_location)
            #legend2 = Legend(items=glyph_ls[3:], location=plot_attr_obj.legend_location)
            
            #Add legends to figure:
            #p.add_layout(legend1, plot_attr_obj.legend_position)
            #p.add_layout(legend2, plot_attr_obj.legend_position)
        
        
        #elif ((len(glyph_ls)>3) & (len(glyph_ls)>6)):
            
            #Create legend:
            #legend1 = Legend(items=glyph_ls[:3], location=plot_attr_obj.legend_location)
            #legend2 = Legend(items=glyph_ls[3:5], location=plot_attr_obj.legend_location)
            #legend3 = Legend(items=glyph_ls[5:7], location=plot_attr_obj.legend_location)
            
            #Add legends to figure:
            #p.add_layout(legend1, plot_attr_obj.legend_position)
            #p.add_layout(legend2, plot_attr_obj.legend_position)
            #p.add_layout(legend3, plot_attr_obj.legend_position)
       

        #else:
            #Create legend:
            #legend = Legend(items=glyph_ls, location=plot_attr_obj.legend_location)

            #Add legend to figure:
            #p.add_layout(legend, plot_attr_obj.legend_position)

        #Format legend:
        #p.legend.orientation = plot_attr_obj.legend_orientation
        #p.legend.spacing = plot_attr_obj.legend_spacing #space between items
        #p.legend.click_policy=plot_attr_obj.legend_click_policy
        
        
        #Create legend:
        legend = Legend(items=glyph_ls, location=plot_attr_obj.legend_location)

        #Add legend to figure:
        p.add_layout(legend, plot_attr_obj.legend_position)

        #Format legend:
        p.legend.orientation = plot_attr_obj.legend_orientation
        p.legend.spacing = plot_attr_obj.legend_spacing #space between items
        p.legend.click_policy=plot_attr_obj.legend_click_policy
        p.legend.label_text_font_size = "9pt"
        p.legend.glyph_height= 18
        p.legend.glyph_width= 18
        p.legend.label_height= 18

        #Deactivate hover-tool, which is by default active:
        p.toolbar.active_inspect = None

        #Show plot:
        show(p)
        
    else:
        print('Cannot display plot!')