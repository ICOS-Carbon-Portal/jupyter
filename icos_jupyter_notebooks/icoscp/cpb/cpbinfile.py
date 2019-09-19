#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on Fri Aug  9 10:40:27 2019
    Use an ICOS digital object id to query the sparql endpoint
    for infos, and create the "payload" to retrieve the binary data
"""

__author__ = "Claudio D'Onofrio"
__credits__ = ["ICOS Carbon Portal Dev Team"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Claudio D'Onofrio"
__email__ = ["claudio.donofrio at nateko.lu.se", 'info@icos-cp.eu']
__status__ = "Development"


import requests
import struct
import pandas as pd
from icoscp.sparql.runsparql import RunSparql
import icoscp.sparql.sparqls as sparqls
from icoscp.cpb import dtype_dict

class CpBinFile():
    """ Use an ICOS digital object id to query the sparql endpoint
        for infos, and create the "payload" to retrieve the binary data
    """
    
    def __init__(self, digitalObject = '', columNumbers=[]):  
    
        self._dobj = digitalObject  # pid
        self._colSelected = columNumbers   # which columns to extract, empty=all        
        self._colNames = []         # contains columNames for colSelected
        self._colNamesAll = []      # contains all column names from dobj
        self._endian = 'big'        # default "big"
        self._dobjValid = False         
        self._info1 = None          # sparql query object           
        self._info2 = None          # sparql query objcect format
        self._colSchema = None      # format of columns (read struct bin data)        
        self._dtypeStruct = None    # format of columns (read struct bin data)
        self._dtypeNumpy = None     # format of columns (read struct bin data)
        self._json = None           # holds the "payload" for requests
        self._rawData = None        # 1D array of data
        self._dataPandas = None      # shaped numpy array of data
        self._server = 'https://data.icos-cp.eu/portal/tabular'
        
        self.__getPayload()
        
    #-----------
    @property
    def dobj(self):
        return self._dobj
    
    @dobj.setter
    def dobj(self, digitalObject):
        self._dobj = digitalObject
        self._dobjValid = False
        self.__getPayload()
    #-----------
    @property
    def valid(self):
        return self._dobjValid
    #-----------
    @property
    def columNumbers(self):
        return self._colSelected

    @columNumbers.setter
    def columNumbers(self, columNumbers=[]):
        self._colSelected = columNumbers  
        self._dobjValid = False
        self.__getPayload()
    #-----------
    @property
    def colNames(self):
        if self._dobjValid:            
            return self.__getColNames()
        return None  
    #----------
    @property
    def colNamesAll(self):
        if self._dobjValid:
            return self._info2['colName']
        return None  
    #-----------
    @property
    def info(self):
        if self._dobjValid:
            return [self._info1, self._info2]
        return None 
    #-----------

# -------------------------------------------------    
    def getData(self):        
        self.__getData()        
        if not self._dobjValid:
            return self._dobjValid       
        return self._dataPandas
    

# -------------------------------------------------    
    def __getPayload(self):
        """ this function is executed 
            1. within the constructor of the class
            2. set/change dobjId
            3. set/change the columNumbers
            if the query is succesfull,  we know there is data
            in binary form available.
            Output: self._dobjValid (Bool) = [True|False]
        """
        self.__queryCpEndpoint()
        if self._dobjValid:
            self._json = {'tableId':self._info1['dobj'][0].split('/')[-1],
                          'schema':{'columns':self._colSchema,
                                    'size':int(self._info1['nRows'][0])},
                                    'columnNumbers':self.columNumbers,
                                    'subFolder':self._info2['objFormat'][0].split('/')[-1]
                  }
            
        return self._dobjValid
# -------------------------------------------------        
    def __queryCpEndpoint(self):
        """ this function sends predefined sparql queries to the cp endpoint
            a single digital object is interrogated to check
            if a binary data representation is available
            if successfule _dobjValid is "True"
        """
        if not self._dobj:
            return self._dobj

        sparql = RunSparql()
        # -------------------------------------------------
        # get information about the digital objcect and if 
        # there is a dataset with format specification
        sparql.query = sparqls.cpbGetInfo(self._dobj)
        sparql.format = 'pandas'
        sparql.run()
        self._info1 = sparql.data()
        if not len(self._info1): 
            self._dobjValid=False
            return

        # -------------------------------------------------
        # get the information about the underlying format
        # from the previous query -> sparql.data....
        sparql.query = sparqls.cpbGetSchemaDetail(self._info1['objSpec'][0])
        sparql.run()  
        self._info2 = sparql.data()
        
        # the lenght of info2 will be equal to "all" columns..
        # by default set the selected columns to all
        
        if not len(self._info2):
            self._dobjValid = False
            return
        elif not self._colSelected:
            self._colSelected = list(range(0,len(self._info2)))

        # -------------------------------------------------
        # create the dataType format, neccesary to interpret the binary 
        # data with python struct library or numpy
        self._colSchema = []        
        for f in self._info2['valFormat']:    
            self._colSchema.append(dtype_dict.mapDataTypesCP(f))  
        
        dtypeStruct = []                
        for d in self._colSelected:    
            dtypeStruct.append(dtype_dict.structTypes(self._colSchema[d],int(self._info1['nRows'][0])))                    
            
        self._dtypeStruct = dtype_dict.structEndian(self._endian) + ''.join(dtypeStruct)
        self._dobjValid = True

    # -------------------------------------------------           
    def __getColNames(self):        
        if not self._dobjValid:
            return None                      
        return  [self.colNamesAll[i] for i in self._colSelected ]
        
# -------------------------------------------------    
    def __getData(self):
        if not self._dobjValid:
            return self._dobjValid
        
        r = requests.post(self._server, json=self._json, stream=True)
        
        if not r.status_code == 200:
            return('data download failed, code: '+ r.status_code)
        
        # increase the "download" counter on the server to track datausage
        self.__portalUse()
        
        # unpack the binary data
        self._rawData = struct.unpack_from(self._dtypeStruct, r.content)
        
        # get them into a pandas data frame, column by column
        self._dataPandas = pd.DataFrame()
        rows = int(self._info1['nRows'])  
        
        for idx,col in enumerate(self._colSelected):                       
            lst = list(self._rawData[idx*rows:(idx+1)*rows])
            if(self._colSchema[col] == 'CHAR'):
                #convert UTF-16 , this is often used in "Flag" columns
                lst = [chr(i) for i in lst]            
            self._dataPandas[self._info2['colName'][col]] = lst

    # -------------------------------------------------                       
    def __portalUse(self):
        
        """ private function to track data usage """
        #counter = {'previewTimeserie':{
        counter = {'BinaryFileDownload':{
        'params':{
            'objId':self._dobj,
            'columns': self.colNames,            
            'library':__name__, 
            'version':__version__}
            }
        }
        server = 'https://cpauth.icos-cp.eu/logs/portaluse'        
        requests.post(server, json=counter)
        
        
        
        
    
        

