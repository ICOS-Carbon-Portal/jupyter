#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 11:45:36 2019
"""

__author__ = "Claudio D'Onofrio"
__credits__ = ["ICOS Carbon Portal Dev Team"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Claudio D'Onofrio"
__email__ = ["claudio.donofrio at nateko.lu.se", 'info@icos-cp.eu']
__status__ = "Development"


""" check the usage of this download library """

import requests
import json
import pandas as pd


class Logfile():
    
    def __init__(self):
        self.server = 'https://restheart.icos-cp.eu/db/portaluse/'        
        self.flt = "?filter={'BinaryFileDownload':{'$exists':'true'}}"        
        self._log = None
    
    @property
    def getLog(self):
        self.__getLogFile()        
        return self.__convertLog()

    def __getLogFile(self):
        url = self.server + self.flt
        r = requests.get(url)
        self._log = r.text
        
    def __convertLog(self):
        # decode json object. what we are interessted in
        # is the key "_embedded" and "BinaryFileDownload'
        log = json.loads(self._log)
        log = log['_embedded']
        return pd.DataFrame(log)
        
        
        
if __name__ == '__main__':
    log = Logfile().getLog
    print(str(len(log)) + ' downloads counted')