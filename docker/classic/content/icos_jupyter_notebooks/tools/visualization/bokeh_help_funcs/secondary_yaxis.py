#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on Wed Oct 14 16:40:00 2020
    Function that aligns primary with secondary y-axis in 
    a Bokeh time-series plot.
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-14"


######################################################################################################
def set_yranges_2y(y1_min, y1_max, y2_min, y2_max, y1_step, y2_step ,new_yrange_name):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 10:30:00 2018
    Last Changed:     Tue May 07 10:30:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes the primary and secondary y-axis min/max values as well as
                      the step values for every y-axis and the secondary y-axis new range name as input
                      parameters, performs computations so that the two axes are alligned and returns
                      their corresponding RangeId objects. Works only for Bokeh plots.
                      
    Input parameters: 1. Min value of primary y-axis (var_name: 'y1_min', var_type: Integer or Float)
                      2. Max value of primary y-axis (var_name: 'y1_max', var_type: Integer or Float)
                      3. Min value of secondary y-axis (var_name: 'y2_min', var_type: Integer or Float)
                      4. Max value of secondary y-axis (var_name: 'y2_max', var_type: Integer or Float)
                      5. Step of primary y-axis (var_name: 'y1_step', var_type: Integer or Float)
                      6. Step of primary y-axis (var_name: 'y2_step', var_type: Integer or Float)
                      7. Name of new yrange object for secondary y-axis
                         (var_name: "new_yrange_name", var_type: Bokeh Plot yrange object)

    Output:           Bokeh Plot yrange objects for primary and secondary y-axes.
    
    """
    
    #import modules:
    import numpy as np
    from bokeh.models import Range1d
          
    #yrange and tick function for plot with primary and secondary y-axis:
    yticks1 = np.arange(y1_min, y1_max + y1_step, y1_step)
    yticks2 = np.arange(y2_min, y2_max + y2_step, y2_step)

    #Get difference in total number of ticks between primary and secondary y-axis:
    diff = abs(len(yticks2)-len(yticks1))

    #Get how many times the step needs to be added to start and end:
    num_of_steps = int(diff/2)
    
    #If the primary and the secondary y-axis have the same number of ticks:
    if(diff==0):

        #Set the range of the 1st y-axis:
        y_range = Range1d(start=y1_min, end=y1_max)

        #Set the 2nd y-axis, range-name, range:
        extra_y_ranges = {new_yrange_name: Range1d(start=y2_min, end=y2_max)}

        
    #If the primary y-axis has fewer ticks than the secondary y-axis:    
    elif(len(yticks2)>len(yticks1)):
    
        #If the difference in ticks between the two axes is an odd number:
        if(diff%2==1):

            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*(num_of_steps+1)),
                              end=y1_max+(y1_step*num_of_steps))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges = {new_yrange_name: Range1d(start=y2_min, end=y2_max)}

        #If the difference in ticks between the two axes is an even number:
        else:
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*num_of_steps), end=y1_max+(y1_step*num_of_steps))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges = {new_yrange_name: Range1d(start=y2_min, end=y2_max)}
            
            
    #If the primary y-axis has more ticks than the secondary y-axis, e.g. len(yticks1)>len(yticks2_test):
    else:
        
        #If the difference in ticks between the two axes is an odd number:
        if(diff%2==1):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges = {new_yrange_name: Range1d(start=y2_min - (y2_step*(num_of_steps)), end=y2_max + (y2_step*(num_of_steps+1)))}

        #If the difference in ticks between the two axes is an even number:
        else:
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges = {new_yrange_name: Range1d(start=y2_min - (y2_step*num_of_steps),
                                                       end=y2_max + (y2_step*num_of_steps))}
              
        
    #Return y-range for primary and secondary y-axes:
    return y_range, extra_y_ranges
######################################################################################################


