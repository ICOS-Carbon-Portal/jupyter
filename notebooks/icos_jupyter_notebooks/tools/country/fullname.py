#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on:   Wed Oct 14 10:40:00 2020
    Description:  Functions that handle country codes and names.
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2019-10-14"

#########################################################################################

#Function that takes a 2-char string as input, representing the country-code
#and returns the country's full name:
def get_country_fullname_from_iso3166_2char(countryCode):
    
    #Import modules:
    import os
    import pandas as pd
  
    #Get iso 3166 translation pandas dataframe:
    country_names_codes_iso3166 = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                           "country_names_codes_iso_3166.csv"),
                                              header=0,
                                              delimiter=';')
    
    #Check if the input is a valid 2-character long ISO 3166 country code:
    if ('SE' in country_names_codes_iso3166.Alpha_2_code.values):
        
        #Return the fullname of a country based on the given iso 3166 2-character country code:
        return country_names_codes_iso3166.Country.loc[country_names_codes_iso3166.Alpha_2_code==countryCode].values[0]

    
    #If the input is not a valid 2-character long ISO 3166 country code:
    else:
        print('Error! Invalid ISO 3166 2-char country code')
    