import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
from icoscp.station import station as station_data
from icoscp.cpb.dobj import Dobj
from numpy import loadtxt
import numpy as np
import os
import numpy as np

import network_characterization_functions as functions

folder_tool_fps = '/data/project/stc/footprints_2018_averaged'

class NetworkObj():
    
    """ 
    Create a network object. Based on user input to gui_network_characterization, all the information 
    needed to output the maps and table are needed. 
    """

    def __init__(self, settings):
        
        """
        Initialize your Network object
        """
        
        self.settings = settings        # dictionary from the GUI 
       
        self.loadLat = loadtxt(os.path.join(folder_tool_fps, 'latitude.csv'), delimiter=',')
        self.loadLon = loadtxt(os.path.join(folder_tool_fps, 'longitude.csv'), delimiter=',')
        self.baseNetwork = None
        self.compareNetwork = None
        self.vmaxPercentile = 99.5
        self.vmaxSens = None
        self.compareMinusBase = None
        self.noFootprints = []
        self.countryDict= {}

        # fucntions to generate the object attributes
        self._setDateRange()
        self._setNetworks()
        self._setVmax()
        self._setCountryDict()
 
    def _setNetworks(self):
        
        self.baseNetwork, self.compareNetwork, self.noFootprints, self.dateTime = functions.return_networks(self)
        
        if self.compareNetwork is not None:
         
            self.compareMinusBase = self.compareNetwork - self.baseNetwork 
            
            
    def _setVmax(self):
        
        df_values_fp = pd.DataFrame()
        
        
        if self.compareNetwork is not None:
            
            df_values_fp['sensitivity']=self.compareNetwork.flatten()
            
            df_values_fp_over_zero = df_values_fp[df_values_fp['sensitivity'] > 0] 

            self.vmaxSens = np.percentile(df_values_fp_over_zero['sensitivity'],self.vmaxPercentile)
        
        else:
            
            if self.baseNetwork is not None:
            
                df_values_fp['sensitivity']=self.baseNetwork.flatten()

                df_values_fp_over_zero = df_values_fp[df_values_fp['sensitivity'] > 0] 

                self.vmaxSens = np.percentile(df_values_fp_over_zero['sensitivity'],self.vmaxPercentile)


    def _setCountryDict(self):
        
        if self.baseNetwork is not None:
        
            self.countryDict = functions.country_dict_landcover(self)
        
    def _setDateRange(self):
        
        date_range = pd.date_range(start=(str(self.settings['startYear']) + '-' + str(self.settings['startMonth']) + '-' + str(self.settings['startDay'])), end=(str(self.settings['endYear']) + '-' + str(self.settings['endMonth']) + '-' + str(self.settings['endDay'])), freq='3H')
        
        self.dateRange = functions.date_range_hour_filtered(date_range, self.settings['timeOfDay'])


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
        