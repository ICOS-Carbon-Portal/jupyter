#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on:   Wed Oct 14 10:40:00 2020
    Description:  Functions that check numeric input.
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2019-10-14"

#########################################################################################


def is_int(var):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Mon Feb 03 13:30:00 2020
    Last Changed:     Mon Feb 03 13:30:00 2020
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes one parameter as input,
                      checks if it can be converted to an integer
                      and returns True or False correspondingly.
    
    Input parameters: string or int or float
    
    Output:           boolean value (True/False)
    
    """
    
    #Define and initialize control value:
    check = True
    
    #Check if input-value can be converted to an integer:
    try:
        val = int(var)
    
    #If input-value can not be converted to an integer:
    except ValueError:
        
        #Set control value to "False":
        check = False
    
    #Return control value:
    return check