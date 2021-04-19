#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""    
    The Station characterization module is used to create an object based on
    user input information (settings). The basic settings 
    from the user is in turn used to generate additional information/data
    and the final result is an object that has all the attributes necessary to
    run the station characterization function in stc_functions. 
    
    Example usage:
    import stc_functions
    myStation=StationChar('HTM')
    
    # to generate a map with sensitivity binned in accordance with interval and degree user settings 
    map_representation_polar_graph_upd(myStation, 'sensitivity')
    
"""

__author__      = ["Ida Storm"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.1"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'ida.storm@nateko.lu.se']
__status__      = "rc1"
__date__        = "2020-12-28"


import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
import radiocarbon_functions


class RadiocarbonObject():
    
    """ 
    Create a station footprint object. Based on user input to gui_footprint, all the information 
    needed to output the maps and table are needed. This includes information about the STILT station/footprints
    as well as the user-defined date range and threshold for the average footprint.
    """
    #could pass only settings - has stationId
    #forced to put in
    def __init__(self, settings):
        
        """
        Initialize your Footprint object
        """
        self.settings = settings        # dictionary from the GUI with 
        self.stationId = None           # string with the station id
        self.stationName = None         # full name of station
        self.lat = None                 # float with latitude of station
        self.lon = None                 # float with longitude of station
        self.country = None             # string with the station's country name
        self.stationClass = None        # string with station class (1 or 2 or none)
        self.siteType = None            # string with station type (mountain etc. or none) 
        self.dateRange = None           # date range for average footprint specified by users
        self.fp = None                  # numpy array 400 columns 480 rows (192000 cells) STILT footprint grid given daterange
        self.fpLat = None               # numpy array with STILT grid lat-values (480)
        self.fpLon = None               # numpy array with STILT grid lon-values (400)
        self.threshold = None           # threshold for footprint 
        self.resample = None            # mumber of days to resample (int)
        
        self.dfDelta14CStation = None   # dataframe with delta radiocarbon for all the date/times the user specified
        self.dfDelta14CFacility = None  # dataframe with delta radiocarbon from nuclear contamination by indicidual facilities 
        
        self.dfDelta14CStationResample = None
        self.dfDelta14CStationResampleBokeh = None
        
        #specified in function plot_nuclear_contamination_by_facility_bokhe (radiocarbon_functions)
        self.dfFacilitiesOverThreshold= None
        
        self.dfDelta14CFacilityResample= None
        self.dfDelta14CFacilityResampleBokeh=None
        

        # fucntions to generate the object attributes
        self._setStationData()
        self._setDateRange()
        self._setFootprint()
        self._setDfs()
    
    #possibly add to stilt and cpstation - full country name. Only code from cplibrary,
    #only lat and lon from stilt
    def _setStationData(self):
        
        self.stationId = self.settings['stationCode']  
        self.threshold = self.settings['threshold']
        
        #if True that it is an ICOS station.
        #if self.settings['icos']:
        if 'icos' in self.settings.keys():
            
            self.stationName=self.settings['icos']['name']
            self.lat=self.settings['icos']['lat']
            self.lon=self.settings['icos']['lon']
            
            #only going to be set for icos stations, not when only a STILT station
            self.stationClass=self.settings['icos']['icosclass']
            self.siteType=self.settings['icos']['siteType']
            
            # API to reterive country name using country code. 
            url='https://restcountries.eu/rest/v2/alpha/' + self.settings['icos']['country']
            resp = requests.get(url=url)
            country_information=resp.json()
            self.country=country_information['name']
        
        #only STILT station:
        else:
            self.stationName=self.settings['stilt']['name']  
            
            # API to reterive country name using reverse geocoding of station lat/lon
            self.lat=self.settings['stilt']['lat'] 
            self.lon=self.settings['stilt']['lon']
            
            url='https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=' + str(self.lon) + '&longitude=' + str(self.lat) + '12&localityLanguage=en'
            resp = requests.get(url=url)
            country_information=resp.json()
            self.country=country_information['countryName']

    def _setDateRange(self):
        """
        Pandas dataframe with the dates/times for all footprints (every three 
        hours: 0, 3, 6, 9 etc.) from the start- and end date specified in 
        settings by the user. 
        """
        
        start_date=dt.datetime(self.settings['startYear'],self.settings['startMonth'],self.settings['startDay'],0)
        end_date=dt.datetime(self.settings['endYear'],self.settings['endMonth'],self.settings['endDay'],0)

        self.dateRange = radiocarbon_functions.date_range_hour_filtered(start_date, end_date, self.settings['timeOfDay'])
    def _setFootprint(self):
        """
        Generate an average footprint (fp) given the user date range.
        Only footprints that the users are interested in is used (timeselect). 
        fpLat and fpLon corresponding to the average footprint are also set here. 
        """
 
        nfp, self.fp, self.fpLon, self.fpLat, title= radiocarbon_functions.read_aggreg_footprints(self.stationId, self.dateRange)
    
    def _setDfs(self):
        
        if self.fp is not None:
            #no need to return, but makes more clear that assigns to the radiocarbon object
            if self.settings['facilityInclusion']:
                self.dfDelta14CStation, self.dfDelta14CFacility = radiocarbon_functions.delta_radiocarbon_dataframes(self)
            else:
                self.dfDelta14CStation = radiocarbon_functions.delta_radiocarbon_dataframes(self)

            if self.settings['resample'][0]!= 'M':

                days_resample = int(self.settings['resample'][0])

            else:
                days_resample = -1

            if days_resample > 0 or self.settings['resample'][0]== 'M':


                self.dfDelta14CStationResample, self.dfDelta14CStationResampleBokeh = radiocarbon_functions.resampled_modelled_radiocarbon(self)

            #resample only if set to resample, and facilities over the specified threshold (by facility)
            if self.settings['resample'][0]== 'M'or (days_resample>0 and self.dfDelta14CFacility is not None):

                if self.settings['facilityInclusion']: 

                    self.dfDelta14CFacilityResample, self.dfDelta14CFacilityResampleBokeh = radiocarbon_functions.resampled_modelled_radiocarbon_facility(self)


            
if __name__ == "__main__":
    """
    execute only if run as a script
    get a full list from the CarbonPortal SPARQL endpoint
    and create a list of station objects    
    """
    msg = """
    You have chosen to run this as a standalone script.
    usually you would use it to create a footprint
    object to be used in when running the graphical
    user interface footprint_gui. 
    """
    print(msg)
        
        
    