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
__version__     = "0.1.2"
__maintainer__  = "ICOS Carbon Portal, elaborated products team"
__email__       = ['info@icos-cp.eu', 'ida.storm@nateko.lu.se']
__status__      = "rc1"
__date__        = "2021-06-22"


import requests
import datetime as dt
import pandas as pd
import stc_functions

stcDataPath='/data/project/stc/'

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
 
    def __init__(self, settings):
        
        """
        Initialize your Station Characterization object
      
        """
        
        self.settings = settings        # dictionary from the GUI with 
        self.stationId = None           # string with the station id
        self.stationName = None         # full name of station
        self.lat = None                 # float with latitude of station
        self.lon = None                 # float with longitude of station
        self.country = None             # string with the station's country name
        self.country_code = None             # string with the station's country name
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
        
        self.figures = {}               # dictionary to store figures and captions
                                        # use figures['1'] = [fig, caption] to get figure 1....
                                        # to add, see function add_figure() 
                                        
        # fucntions to generate the object attributes
        self._setStationData()
        self._setDateRange()
        self._setFootprint()
        self._setDistancesAndDegrees()
        self._setBinsAndLabels()
    

    def _setStationData(self):
        
        self.stationId = self.settings['stationCode']
        if 'icos' in self.settings.keys():
            # ICOS station
            
            self.stationName=self.settings['icos']['name']
            self.lat=self.settings['icos']['lat']
            self.lon=self.settings['icos']['lon']
            self.country_code = self.settings['icos']['country']
            
            #only going to be set for icos stations, not when only a STILT station
            self.stationClass=self.settings['icos']['icosclass']
            self.siteType=self.settings['icos']['siteType']            
        
            
        else:
            # STILT station:
            self.stationName=self.settings['stilt']['name']            
            self.lat=self.settings['stilt']['lat'] 
            self.lon=self.settings['stilt']['lon']
            
            # revers geocoding
            baseurl = 'https://nominatim.openstreetmap.org/reverse?format=json&'
            url = baseurl + 'lat=' + str(self.lat) + '&lon=' + str(self.lon) + '&zoom=3'
            r = requests.get(url=url)
            c = r.json()
            if not 'error' in c.keys():
                self.country_code = c['address']['country_code']
            
        if self.country_code:
            # API to reterive country information using country code. 
            url='https://restcountries.eu/rest/v2/alpha/' + self.country_code
            resp = requests.get(url=url)
            self.country_information = resp.json()
            self.country=self.country_information['name']

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
      
        #saved distances and degrees for ICOS stations:
        df_w_distances=pd.read_csv(stcDataPath+ "approved_stations_distances.csv")
        df_w_degrees=pd.read_csv(stcDataPath + "approved_stations_degrees.csv") 
    
        #if not saved distances to all 192000 cells, calculate it. 
        if self.stationId in df_w_degrees.keys().tolist():
            self.distances=df_w_distances[self.stationId]
            self.degrees=df_w_degrees[self.stationId]
        
        else:
            self.distances=stc_functions.distances_from_point_to_grid_cells(self.lat, self.lon, self.fpLat, self.fpLon)

            self.degrees=stc_functions.degrees_from_point_to_grid_cells(self.lat, self.lon, self.fpLat, self.fpLon)

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
        
    def add_figure(self, key, figure, caption):
        """
        add figures in the dictionary self.figures. To retrieve the figures
        you can use object.figure        

        Parameters
        ----------
        key : INT|STR :     figure number (1 = sensitivity, 2 = pointsource
                            3 = population, 4 = landcover_rose, 5 = multiple_variables
                            6 = seasonal, 7 = landcover_bar

        figure : OBjECT :   Matplotlib figure or smilar, needs to have a function
                            Object.show() and object.savefig('filename')            
        caption : STR :     String to be used as a caption text for example when
                            creating a pdf output
        Returns: None.
        
        """
        
        # humean readable key to value assignment
        short = {'1': 'sensitivity',
                 '2': 'pointsource',
                 '3': 'population',
                 '4': 'landcover_bar',
                 '5': 'seasonal',
                 '6': 'landcover_windrose',                 
                 '7': 'multivar'}
               
        self.figures[str(key)]=[figure, caption, short[str(key)]]
        
    
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
        
        
    