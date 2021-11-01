import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
from icoscp.station import station as station_data
from icoscp.cpb.dobj import Dobj
from numpy import loadtxt
import os

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

        # fucntions to generate the object attributes
        self._setNetworks()

    def _setNetworks(self):
        #, self.compareNetwork
        self.baseNetwork = functions.return_networks(self)
        #fp_mask_count_base_network, fp_mask_base_network, fp_max_base_network, lon, lat, list_none_footprints = functions.aggreg_2018_footprints_base_network(self)


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
        