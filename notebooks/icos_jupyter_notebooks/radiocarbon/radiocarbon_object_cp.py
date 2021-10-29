import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
from icoscp.station import station as station_data
from icoscp.cpb.dobj import Dobj

import radiocarbon_functions

class RadiocarbonObjectMeasCp():
    
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
        

        #needed in ex C++ else not variable within class. also ex is a string. type.
        self.settings = settings        # dictionary from the GUI 
        self.stationId = None           # string with the station id
        self.stationName = None         # full name of station
        self.lat = None                 # float with latitude of station
        self.lon = None                 # float with longitude of station
        self.country = None             # string with the station's country name
        self.stationClass = None        # string with station class (1 or 2 or none)
        self.siteType = None            # string with station type (mountain etc. or none) 
        
        self.measuredData = None

        # fucntions to generate the object attributes
        self._setStationData()
        
        self._setMeasuredData()
    
    #possibly add to stilt and cpstation - full country name. Only code from cplibrary,
    #only lat and lon from stilt
    def _setStationData(self):
            
        self.stationId = self.settings['stationCode']  

        if 'icos' in self.settings.keys():
            
            self.stationName=self.settings['icos']['name']
            self.lat=self.settings['icos']['lat']
            self.lon=self.settings['icos']['lon']
            
            #only going to be set for icos stations, not when only a STILT station
            self.stationClass=self.settings['icos']['icosclass']
            self.siteType=self.settings['icos']['siteType']
   
        #only STILT station:
        else:
            self.stationName=self.settings['stilt']['name']  
            
            # API to reterive country name using reverse geocoding of station lat/lon
            self.lat=self.settings['stilt']['lat'] 
            self.lon=self.settings['stilt']['lon']
            
        if self.settings['stilt']['geoinfo']:

            self.country=self.settings['stilt']['geoinfo']['name']['common']
        else:
            self.country='Location in water'
            
 
            
    def _setMeasuredData(self):
        
        
        #only get the 14C release:
        selected_station_all=station_data.get(self.settings['codeMeasCP'])
        
        radiocarbon_data= selected_station_all.data()[selected_station_all.data().spec=='http://meta.icos-cp.eu/resources/cpmeta/atcC14L2DataObject']
        
        self.measuredData=Dobj(radiocarbon_data.dobj.values[0]).data
        
        #modelled data for the same date ranges:
        self.df_for_export, self.df_for_plot = radiocarbon_functions.radiocarbon_cp_results(self)

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
        