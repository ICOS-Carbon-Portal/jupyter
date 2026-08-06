#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on Wed Oct 14 16:40:00 2020
    The file contains function(s) that return a Bokeh colormap based
    on the value of a numeric input variable.
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-14"


######################################################################################################



def get_colormap(num_of_items):
      
    """
    Project:         'ICOS Carbon Portal'
    Created:          Fri Apr 04 17:00:00 2019
    Last Changed:     Fri Apr 04 17:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina Pantazatou
    
    Description:      Function that takes an integer representing the total number of
                      items that should receive a sepparate color and  returns a colormap
                      (i.e. a list of strings, where every string represents a different
                      color in hexadecimal code) with the same amount of colors.
                      The function uses color palettes (namely Colorblind & magma) from
                      the Bokeh visualization library and can return colormaps for
                      1 - 256 items.
                      
    Input parameters: Number of items to be colored in a sepparate color
                      (var_name: 'num_of_items', var_type: Integer)

    Output:           List of strings (colormap)
    
    """
    
    #Check input:
    if(isinstance(num_of_items, int)):
    
        #import module:
        from bokeh.palettes import all_palettes, Colorblind, magma

        #Check the number of items to be colored (1-2 items):
        if((num_of_items>0) and (num_of_items<3)):
            return ['#2b83ba','#fdae61'] #return colormap selection
        
        #Check the number of items to be colored (3-8 items):
        elif((num_of_items>2) and (num_of_items<9)):
            return all_palettes['Colorblind'][num_of_items] #return colormap selection
        
        #Check the number of items to be colored (9-256 items):
        elif((num_of_items>8) and (num_of_items<257)):
            return magma(num_of_items) #return colormap selection         
        
        #If the number of items exceeds the number 256:
        else:
            print('Error! Number of items to be colored is zero or higher than 256.')
    
    #If the input parameter is not an integer:
    else:
        print('Input is not an integer.')
        