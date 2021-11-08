import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
from icoscp.station import station as station_data
from icoscp.cpb.dobj import Dobj
from numpy import loadtxt
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
        self.vmaxSens = None
        self.compareMinusBase = None
        self.noFootprints = []
        self.countryDict= {}

        # fucntions to generate the object attributes
        self._setNetworks()
        self._setCountryDict()
 

    def _setNetworks(self):
        
        self.baseNetwork, self.compareNetwork, self.noFootprints = functions.return_networks(self)

        if self.compareNetwork is not None:
            
            #otherwise remain None
            self.vmaxSens = np.max(self.compareNetwork)
            
            self.compareMinusBase = self.compareNetwork - self.baseNetwork
            
    def _setCountryDict(self):
        
        self.countryDict = functions.country_dict_landcover(self)
        


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
        