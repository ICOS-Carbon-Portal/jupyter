#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on Wed Oct 14 16:40:00 2020
    Function that aligns primary, secondary and third y-axis
    in a Bokeh time-series plot.
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-14"

######################################################################################################


def set_yranges_3y(y1_min, y1_max, y2_min, y2_max, y3_min, y3_max, y1_step, y2_step, y3_step):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 10:30:00 2018
    Last Changed:     Tue May 07 10:30:00 2019
    Version:          1.0.0
    Author(s):        Karolina Pantazatou
    
    Description:      Function that takes the primary, secondary and third y-axis min/max
                      values as well as the step values for every y-axis as input parameters,
                      performs computations so that the three axes are alligned and returns
                      their corresponding RangeId objects.
                      Works only for Bokeh plots.
                      
    Input parameters: 1. Min value of primary y-axis (var_name: 'y1_min', var_type: Integer or Float)
                      2. Max value of primary y-axis (var_name: 'y1_max', var_type: Integer or Float)
                      3. Min value of secondary y-axis (var_name: 'y2_min', var_type: Integer or Float)
                      4. Max value of secondary y-axis (var_name: 'y2_max', var_type: Integer or Float)
                      5. Min value of third y-axis (var_name: 'y3_min', var_type: Integer or Float)
                      6. Max value of third y-axis (var_name: 'y3_max', var_type: Integer or Float)
                      7. Step of primary y-axis (var_name: 'y1_step', var_type: Integer or Float)
                      8. Step of secondary y-axis (var_name: 'y2_step', var_type: Integer or Float)
                      9. Step of third y-axis (var_name: 'y3_step', var_type: Integer or Float)

    Output:           Bokeh Plot yrange objects for primary and secondary y-axes.
    
    """
    
    #import modules:
    import numpy as np
    from bokeh.models import Range1d
          
    #yrange and tick function for plot with primary and secondary y-axis:
    yticks1 = np.arange(y1_min, y1_max + y1_step, y1_step)
    yticks2 = np.arange(y2_min, y2_max + y2_step, y2_step)
    yticks3 = np.arange(y3_min, y3_max + y3_step, y3_step)
    
    #Get the number of ticks per y-axis:
    y1_num_of_ticks = len(yticks1)
    y2_num_of_ticks = len(yticks2)
    y3_num_of_ticks = len(yticks3)

    #Get difference in total number of ticks between primary and secondary y-axis:  
    diff_12 = abs(len(yticks2)-len(yticks1))
    diff_13 = abs(len(yticks3)-len(yticks1))
    diff_23 = abs(len(yticks3)-len(yticks2))

    #Get how many times the step needs to be added to start and end:
    num_of_steps_12 = int(diff_12/2)
    num_of_steps_13 = int(diff_13/2)
    num_of_steps_23 = int(diff_23/2)
    
    
    #If the primary, secondary and 3rd y-axis have the same number of ticks:
    if((diff_12==0) and (diff_13==0) and (diff_23==0)):

        #Set the range of the 1st y-axis:
        y_range = Range1d(start=y1_min, end=y1_max)

        #Set the 2nd y-axis, range-name, range:
        extra_y_ranges_1 = Range1d(start=y2_min, end=y2_max)
        
        #Set the 3rd y-axis, range-name, range:
        extra_y_ranges_2 = Range1d(start=y3_min, end=y3_max)

        
        
    #if y-axis 1 is the axis with the highest number of ticks:
    elif(max(y1_num_of_ticks, y2_num_of_ticks, y3_num_of_ticks)==y1_num_of_ticks):
        
        #Check if the difference between y-axis 1 and the other axes is an even number:
        if((diff_12%2==0) and (diff_13%2==0)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min - (y2_step*num_of_steps_12),
                                       end=y2_max + (y2_step*num_of_steps_12))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min - (y3_step*num_of_steps_13), 
                                       end=y3_max + (y3_step*num_of_steps_13))

        
        #Check if the difference between y-axis 1 and the other axes is an odd number:
        elif((diff_12%2==1) and (diff_13%2==1)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min - (y2_step*(num_of_steps_12)),
                                       end=y2_max + (y2_step*(num_of_steps_12+1)))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min - (y3_step*(num_of_steps_13)),
                                       end=y3_max + (y3_step*(num_of_steps_13+1)))

            
        #Check if the difference between y-axis 1 and the other axes is an even/odd number:
        elif((diff_12%2==0) and (diff_13%2==1)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range: --- > even diff
            extra_y_ranges_1 = Range1d(start=y2_min - (y2_step*num_of_steps_12),
                                       end=y2_max + (y2_step*num_of_steps_12))
            
            #Set the 3rd y-axis, range-name, range: --- > odd diff
            extra_y_ranges_2 = Range1d(start=y3_min - (y3_step*(num_of_steps_13)),
                                       end=y3_max + (y3_step*(num_of_steps_13+1)))
         
        
        #Check if the difference between y-axis 1 and the other axes is an odd/even number:
        #I.e. (diff_12%2==1) and (diff_13%2==0)
        else:
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min, end=y1_max)

            #Set the 2nd y-axis, range-name, range: --- > odd diff
            extra_y_ranges_1 = Range1d(start=y2_min - (y2_step*(num_of_steps_12)),
                                       end=y2_max + (y2_step*(num_of_steps_12+1)))
            
            #Set the 3rd y-axis, range-name, range: --- > even diff
            extra_y_ranges_2 = Range1d(start=y3_min - (y3_step*num_of_steps_13), 
                                       end=y3_max + (y3_step*num_of_steps_13))
        
      
    
    #if y-axis 2 is the axis with the highest number of ticks:
    elif(max(y1_num_of_ticks, y2_num_of_ticks, y3_num_of_ticks)==y2_num_of_ticks):
        
        #Check if the difference between y-axis 2 and the other axes is an even number:
        if((diff_12%2==0) and (diff_23%2==0)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*num_of_steps_12),
                              end=y1_max+(y1_step*num_of_steps_12))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min, end=y2_max)
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min-(y3_step*num_of_steps_23),
                                       end=y3_max+(y3_step*num_of_steps_23))
            
            
        #Check if the difference between y-axis 2 and the other axes is an odd number:
        elif((diff_12%2==1) and (diff_23%2==1)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*(num_of_steps_12+1)),
                              end=y1_max+(y1_step*num_of_steps_12))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min, end=y2_max)
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min-(y3_step*(num_of_steps_23+1)),
                                       end=y3_max+(y3_step*num_of_steps_23))
      
            
        #Check if the difference between y-axis 2 and the other axes is an even/odd number:
        elif((diff_12%2==0) and (diff_23%2==1)):
            
            #Set the range of the 1st y-axis: --- > even diff
            y_range = Range1d(start=y1_min-(y1_step*num_of_steps_12),
                              end=y1_max+(y1_step*num_of_steps_12))

            #Set the 2nd y-axis, range-name, range: 
            extra_y_ranges_1 = Range1d(start=y2_min, end=y2_max)
            
            #Set the 3rd y-axis, range-name, range: --- > odd diff
            extra_y_ranges_2 = Range1d(start=y3_min-(y3_step*(num_of_steps_23+1)),
                                       end=y3_max+(y3_step*num_of_steps_23))
            
         
        #Check if the difference between y-axis 2 and the other axes is an odd/even number:
        #I.e. (diff_12%2==1) and (diff_23%2==0)
        else:
            
            #Set the range of the 1st y-axis: --- > odd diff
            y_range = Range1d(start=y1_min-(y1_step*(num_of_steps_12+1)),
                              end=y1_max+(y1_step*num_of_steps_12))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min, end=y2_max)
            
            #Set the 3rd y-axis, range-name, range: --- > even diff
            extra_y_ranges_2 = Range1d(start=y3_min-(y3_step*num_of_steps_23),
                                       end=y3_max+(y3_step*num_of_steps_23))
            
    
    
    #if y-axis 3 is the axis with the highest number of ticks:
    elif(max(y1_num_of_ticks, y2_num_of_ticks, y3_num_of_ticks)==y3_num_of_ticks):
        
        #Check if the difference between y-axis 3 and the other axes is an even number:
        if((diff_13%2==0) and (diff_23%2==0)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*num_of_steps_13),
                              end=y1_max+(y1_step*num_of_steps_13))

            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min-(y2_step*num_of_steps_23),
                                       end=y2_max+(y2_step*num_of_steps_23))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min, end=y3_max)
            
        
        #Check if the difference between y-axis 3 and the other axes is an odd number:
        elif((diff_13%2==1) and (diff_23%2==1)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*(num_of_steps_13+1)),
                              end=y1_max+(y1_step*num_of_steps_13))
            
            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min-(y2_step*(num_of_steps_23+1)),
                                       end=y2_max+(y2_step*num_of_steps_23))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min, end=y3_max)
            
            
            
        #Check if the difference between y-axis 3 and the other axes is an even/odd number:
        elif((diff_13%2==0) and (diff_23%2==1)):
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*num_of_steps_13),
                              end=y1_max+(y1_step*num_of_steps_13))
            
            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min-(y2_step*(num_of_steps_23+1)),
                                       end=y2_max+(y2_step*num_of_steps_23))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min, end=y3_max)
            
            
        #Check if the difference between y-axis 3 and the other axes is an odd/even number:
        #I.e. (diff_13%2==1) and (diff_23%2==0)
        else:
            
            #Set the range of the 1st y-axis:
            y_range = Range1d(start=y1_min-(y1_step*(num_of_steps_13+1)),
                              end=y1_max+(y1_step*num_of_steps_13))
            
            #Set the 2nd y-axis, range-name, range:
            extra_y_ranges_1 = Range1d(start=y2_min-(y2_step*num_of_steps_23),
                                       end=y2_max+(y2_step*num_of_steps_23))
            
            #Set the 3rd y-axis, range-name, range:
            extra_y_ranges_2 = Range1d(start=y3_min, end=y3_max)
        
    else:
        y_range = None
        extra_y_ranges_1 = None
        extra_y_ranges_2 = None
      
        
    #Return y-range for primary and secondary y-axes:
    return y_range, extra_y_ranges_1, extra_y_ranges_2
