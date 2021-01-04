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
__date__        = "2020-12-03"

import settings
import json
from icoscp.station import station
import requests
import datetime as dt
import pandas as pd
import stc_functions

#need settings in an object.
#second class? BinLabels.. object available within station
class StationChar():
    
    """ 
    Create a station characterization object. This class intends to create 
    an instance of a station characterization, providing information
    needed to run station characterization functions. The object will look
    different depending on what information is provided in settings 
    (station, date range, binning specifications for the output maps etc)

    Attributes include latitude and longitude of the station. Given that  
    the object myStationChar is created, this is an example of its use:
    
    myStationChar.lat -> returns latitude as float. 
    
    all object attributes are listed in def __init__
    """
    #could pass only settings - has stationId
    #forced to put in
    def __init__(self, settings):
        
        """
        Initialize your Station Characterization object
      
        """
        #needed in ex C++ else not variable within class. also ex is a string. type.
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
        self.fpLon = None               # # numpy array with STILT grid lon-values (400)
        self.distances = None           # distances from station to all cells in the STILT grid 
        self.degrees = None             # degree angle between station and all cells in the STILT grid 
        
        #own class? --> script. provide lat and lon + gridsize. general.get distances and angels. general. "version 2".
        self.intervalBins = None        # numpy array with the bin intervals for the maps
        self.intervalLabels = None      # list with the bin labels for the maps 
        self.dirBins = None             # numpy array with the direction bins for the maps
        self.dirLabels = None           # list with the direction labels for the maps
        
        # fucntions to generate the object attributes
        self._setStationData()
        self._setDateRange()
        self._setFootprint()
        self._setDistancesAndDegrees()
        self._setBinsAndLabels()
    
    #possibly add to stilt and cpstation - full country name. Only code from cplibrary,
    #only lat and lon from stilt
    def _setStationData(self):
        
        self.stationId = self.settings['stationCode']  
        
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

        self.dateRange = stc_functions.date_range_hour_filtered(start_date, end_date, self.settings['timeOfDay'])
    def _setFootprint(self):
        """
        Generate an average footprint (fp) given the user date range.
        Only footprints that the users are interested in is used (timeselect). 
        fpLat and fpLon corresponding to the average footprint are also set here. 
        """
        nfp, self.fp, self.fpLon, self.fpLat, title= stc_functions.read_aggreg_footprints(self.stationId, self.dateRange)

    #station_lat, station_lon, grid_lat, grid_lon
    def _setDistancesAndDegrees(self):
        """
        Distances and degrees from the station to all cells in the STILT grid.
        The information is used to bin the footprints based on angle and distance 
        to station. For the labelled atmoshperic stations (as of 2020-07-15)
        this is pre-calculated and accessed from csv-files. If it is any other
        station, these values are calculated and set as attributes. The 
        calculated values are also appended to the csv-files. 
        """
      
        df_w_distances=pd.read_csv("approved_stations_distances.csv")
        df_w_degrees=pd.read_csv("approved_stations_degrees.csv")
        
        #same as degrees
        list_distance_columns=df_w_distances.columns.tolist()

        station_reduced = self.stationId[0:3]
        matched_station = [idx for idx in list_distance_columns if idx[0:3] == station_reduced]    
    
        #if not saved distances to all 192000 cells, calculate it. 
        if matched_station:
            self.distances=df_w_distances[matched_station[0]]
            self.degrees=df_w_degrees[matched_station[0]]
        
        else:
            self.distances=stc_functions.distances_from_point_to_grid_cells(self.lat, self.lon, self.fpLat, self.fpLon)
            df_w_distances[station]=self.distances
            df_w_distances.to_csv("approved_stations_distances.csv")
            
            self.degrees=stc_functions.degrees_from_point_to_grid_cells(self.lat, self.lon, self.fpLat, self.fpLon)
            df_w_degrees[station]=self.degrees
            df_w_degrees.to_csv("approved_stations_degrees.csv")
            
    #or other class... but belongs to object station characterization as much as distances and degrees to footprint?   
    #can now remove "define_bins_landcover_polar_graph"
    def _setBinsAndLabels(self):
        """
        Given the user specified intervals and degree-binning for the output
        maps, bin arrays and labels are generated for both distance from station
        and degree angle in relation to station. The labels are only used
        within the function (heading for columns in pandas dataframe).
        """
        km_intervals = self.settings['binInterval']
        bin_size = self.settings['binSize']
        self.intervalBins, self.intervalLabels, self.dirBins, self.dirLabels = stc_functions.define_bins_maprose(km_intervals, bin_size)
    
if __name__ == "__main__":
    """
    execute only if run as a script
    get a full list from the CarbonPortal SPARQL endpoint
    and create a list of station objects    
    """
    msg = """
    You have chosen to run this as a standalone script.
    usually you would use it to create a station characterization
    class to be used in when running station characterization functions 
    in stc_functions. It is also used when pusing the update button in the GUI at 
    ICOS exploredata (exploredata.icos-cp.eu). 
    """
    print(msg)
        
        
    