#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Functions that take a numeric variable as input
                      and return the nearest integer by ±10, ±20 or ±100.
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-10-13"




############################## round down 10 ############################

def rounddown_10(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 10:30:00 2019
    Last Changed:     Tue May 07 10:30:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      floors it down to the closest "10".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #import module:
    import math
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):
    
        #Return rounded value:
        return int(math.ceil(x / 10.0)) * 10 -10
    
    #If input parameter is NOT numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
############################################################################


def roundup_10(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 10:30:00 2018
    Last Changed:     Tue May 07 10:30:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      rounds it up to the closest "10".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #import module:
    import math
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):
    
        #Return rounded value:
        return int(math.ceil(x / 10.0)) * 10
    
    #If input parameter is NOT numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
############################################################################


############################### round down 20 ##############################

def rounddown_20(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 09:00:00 2019
    Last Changed:     Tue May 07 09:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      floors it to the nearest "20".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #Import module:
    import math
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):
    
        #If the 2nd digit from the decimal point is an even number:
        if(int(x/10.0)%2==0):

            return(int(x / 10.0) * 10) - 20

        #If the 2nd digit from the decimal point is an odd number:
        else:

            return(int(x / 10.0) * 10) - 10
        
    #If input parameter is not numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
############################################################################

def roundup_20(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 09:00:00 2019
    Last Changed:     Tue May 07 09:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      rounds it up to the closest "20".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #Import module:
    import math
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):
    
        #for positive numbers, multiples of 20.0:
        if((x>=0)&(((x/10.0)%20)%2 == 0)):  
            return int(math.ceil(x / 10.0)) * 10 +20

        #for positive numbers with an even number as 2nd digit:
        elif((x>0)&(int(x/10.0)%2==0)):
            return int(math.ceil(x / 10.0)) * 10 +10

        #for positive and negative numbers, whose 2nd digit
        #is an odd number (except for i in [-1,-9]):
        elif(int(x/10.0)%2!=0):
            return int((x / 10.0)) * 10 +10

        #for negative numbers, whose 1st or 2nd digit is an even number:
        elif((x<-10) & (int(x)%2==0)):   
            return int((x / 10.0)) * 10 +20

        else:
            return 0
    
    #If input parameter is NOT numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
############################################################################


############################### round down 100 #############################
def rounddown_100(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 09:00:00 2019
    Last Changed:     Tue May 07 09:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      floors it to the nearest "100".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #Import module:
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):

        #If the number is an integral multiple of 100:
        if(((x/100.0)%2==0) or (x<=0) or (x==100)):

            return(int(x / 100.0) * 100) - 100
        
        #If the input number is NOT an integral multiple of 100:
        else:

            return(int(x / 100.0) * 100)

    #If input parameter is not numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
##############################################################################


def roundup_100(x):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Tue May 07 09:00:00 2019
    Last Changed:     Tue May 07 09:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina
    
    Description:      Function that takes a number as input and
                      rounds it up to the nearest "100".
                      
    Input parameters: Number (var_name: 'x', var_type: Integer or Float)

    Output:           Float
    
    """
    
    #Import modules:
    import math
    import numbers
    
    #Check if input parameter is numeric:
    if(isinstance(x, numbers.Number)==True):
        
        #for integral mulitples of 100 and for the
        #special cases of 100, 0 and -100:
        if(((x/100.0)%2==0) or (x==100) or (x==-100)):  
            return int(math.ceil(x / 100.0)) * 100 + 100

        else:
            return int(math.ceil(x / 100.0)) * 100
    
    #If input parameter is not numeric, prompt an error message:
    else:
        print("Input parameter is not numeric!")
##############################################################################