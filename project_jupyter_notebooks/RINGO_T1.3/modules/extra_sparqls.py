#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
import pandas as pd
import datetime as dt
import json 
import requests

#-----------------------------------------------------------------------------

def get_station_class():
    # Query the ICOS SPARQL endpoint for a station list
    # query stationId, class, long name, country, longitude and latitude

    query = """
    prefix st: <http://meta.icos-cp.eu/ontologies/stationentry/>
    select distinct ?stationId ?stationClass ?country ?longName ?lon ?lat
    from <http://meta.icos-cp.eu/resources/stationentry/>
    where{
      ?s a st:AS .
      ?s st:hasShortName ?stationId .
      ?s st:hasStationClass ?stationClass .
      ?s st:hasCountry ?country .
      ?s st:hasLongName ?longName .
      ?s st:hasLon ?lon .
      ?s st:hasLat ?lat .
      filter (?stationClass = "1" || ?stationClass = "2")
    }
    ORDER BY ?stationClass ?stationId 
    """

    return query

#--------------------------------------------------------------------------------

def get_icos_stations_atc_samplingheight():
    
    """
    Description:      Download ICOS station names for all L1 gases from ICOS CP with a SPARQL-query.
    Input parameters: No input parameter/s
    Output:           Pandas Dataframe
                      columns: 
                            1. URL to ICOS RI Data Object Landing Page (var_name: 'dobj', var_type: String)
                            2. Filename for Data Object (var_name: 'filename', var_type: String)
                            3. Name of gas (var_name: 'variable', var_type: String)
                            4. Station name (var_name: 'stationName', var_type: String)
                            5. Sampling height a.g.l. (var_name: 'height', var_type: String)
                            6. Sampling Start Time (var_name: 'timeStart', var_type: String)
                            7. Sampling End Time (var_naem: 'timeEnd', var_type: String)
                            8. Station ID (var_name: 'stationId', var_type: String)
    """
    
    query = """
        prefix cpres: <http://meta.icos-cp.eu/resources/cpmeta/>
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        select ?dobj ?fileName ?variable ?stationName ?height ?timeStart ?timeEnd ?stationId
        where{
           values ?vtype { cpres:co2MixingRatio cpres:coMixingRatioPpb cpres:ch4MixingRatioPpb}
           #values ?spec {cpres:atcCo2NrtGrowingDataObject cpres:atcCoNrtGrowingDataObject cpres:atcCh4NrtGrowingDataObject}
           ?vtype rdfs:label ?variable .
           ?col cpmeta:hasValueType ?vtype .
           ?dset cpmeta:hasColumn ?col .
           ?spec cpmeta:containsDataset ?dset .
           ?spec cpmeta:hasAssociatedProject <http://meta.icos-cp.eu/resources/projects/icos> .
           ?spec cpmeta:hasDataLevel "1"^^xsd:integer .
           ?dobj cpmeta:hasObjectSpec ?spec .
           ?dobj cpmeta:hasName ?fileName .
           ?dobj cpmeta:hasSizeInBytes ?fileSize .
           filter not exists {[] cpmeta:isNextVersionOf ?dobj}
           ?dobj cpmeta:wasAcquiredBy [
              prov:wasAssociatedWith/cpmeta:hasStationId ?stationId ;
              prov:startedAtTime ?timeStart ;
              prov:endedAtTime ?timeEnd ;
              prov:wasAssociatedWith/cpmeta:hasName ?stationName 
            ] .
            ?dobj cpmeta:wasAcquiredBy/cpmeta:hasSamplingHeight ?height .
        }
        order by ?variable ?stationName ?height
    """
    
    return query

#-------------------------------------------------------------------------------------
#wichtig
def atc_station_tracer_query(station_code, samp_height, tracer, level=2):

    """
        Return SPARQL query to get a data object for 
        a specific ICOS Atmospheric station, sampling height and tracer
         CO2, CO or MTO, level 2 or level 1 (=NRT)
       :input: ATC station code, sampling height, tracer, ICOS data level (default=2)
       :return: SPARQL query to get all ATC Level <level> products for tracer <tracer>
       :rtype: string 
    """
    
    station_label = 'AS_' + station_code
    tracer = tracer.lower().title()
    dataobject = ['NrtGrowingDataObject','L2DataObject']    
  
    #Define URL:
    url = 'https://meta.icos-cp.eu/sparql'
    
    query = """
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        select ?dobj ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd ?samplingHeight
        where {
            VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/atc"""+tracer+dataobject[level-1]+""">}
            ?dobj cpmeta:hasObjectSpec ?spec .
            VALUES ?station {<http://meta.icos-cp.eu/resources/stations/"""+station_label+""">}
            ?dobj cpmeta:wasAcquiredBy/prov:wasAssociatedWith ?station .
            ?dobj cpmeta:hasSizeInBytes ?size .
            ?dobj cpmeta:hasName ?fileName .
            ?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .
            ?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .
            ?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .
            FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
            ?dobj cpmeta:wasAcquiredBy / cpmeta:hasSamplingHeight ?samplingHeight .
            FILTER( ?samplingHeight = '"""+str(samp_height)+"""'^^xsd:float )
        }
        order by desc(?submTime)
    """
    return query

#-------------------------------------------------------------------------------------

def icos_hist_L1_L2_sparql(station_code, samp_height, icos_label):
    
    '''
    Description: Function that returns a pandas DataFrame with file info
                 for a specified station from the drought2018AtmoProduct. 
                
    Input:       1. Station code, characters (var_name: "station_code", var_type: String)
                 2. Station sampling height  (var_name: "samp_height", var_type: Int/Float)
                 3. Label specifying if the station is an ICOS station 
                    (var_name: "icos_label", var_type: Boolean)
    
    Output:      Pandas DataFrame
                
                 1. Data Object ID (var_name: "dobj", var_type: String)
                 2. Data specification (var_name: "spec", var_type: String)
                 3. Filename (var_name: "fileName", var_type: String)
                 4. Size (var_name: "size", var_type: Int)
                 5. Submission time (var_name: "submTime", var_type: String)
                 6. Observation starting time (var_name: "timeStart", var_type: String)
                 7. Observation end date (var_name: "timeEnd", var_type: String)
                 8. Station sampling height (var_name: "samplingHeight", var_type: String)
                
                
    '''    
    
    #If the station is an ICOS station:
    if(icos_label):
        station_label = 'AS_' + station_code
    
    #If the station is NOT an ICOS station:
    else:
        station_label = 'ATMO_' + station_code
   
    #Define URL:
    url = 'https://meta.icos-cp.eu/sparql'
    
    query = '''
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        select ?dobj ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd ?samplingHeight
        where {
            VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/atcCo2NrtGrowingDataObject>
            <http://meta.icos-cp.eu/resources/cpmeta/atcCo2L2DataObject>
            <http://meta.icos-cp.eu/resources/cpmeta/drought2018AtmoProduct>}
            ?dobj cpmeta:hasObjectSpec ?spec .
            VALUES ?station {<http://meta.icos-cp.eu/resources/stations/'''+station_label+'''>}
            ?dobj cpmeta:wasAcquiredBy/prov:wasAssociatedWith ?station .
            ?dobj cpmeta:hasSizeInBytes ?size .
            ?dobj cpmeta:hasName ?fileName .
            ?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .
            ?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .
            ?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .
            FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
            ?dobj cpmeta:wasAcquiredBy / cpmeta:hasSamplingHeight ?samplingHeight .
            FILTER( ?samplingHeight = "'''+str(samp_height)+'''"^^xsd:float )
        }
        order by desc(?submTime)
    '''
    return query

#------------------------------------------------------------------------------

def icos_atm_station_sparql(tracer='co2',level=2):
    
    '''
    Description: Function that returns a pandas DataFrame with info
                 for all stations 
                
    Input:       No input parameters
    
    Output:      Pandas DataFrame
                
                 1. Station code, 3 characrers (var_name: "Short_name", var_type: String)
                 2. Country code, 2 characters (var_name: "Country", var_type: String)
                 3. Station latitude (var_name: "lat", var_type: String)
                 4. Station longitude (var_name: "lon", var_type: String)
                 5. Station elevation (var_name: "alt", var_type: String)
                 6. Station name (var_name: "Long_name", var_type: String)
                 7. Sampling height (var_name: "height", var_type: String)
                
                
    '''
    
    tracer = tracer.lower().title()
    dataobject = ['NrtGrowingDataObject','L2DataObject']    
 
    
    #Define URL:
    url = 'https://meta.icos-cp.eu/sparql'
    
    query = """
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        select
        (str(?sName) AS ?Short_name)
        ?Country
        ?lat ?lon ?alt
        (str(?lName) AS ?Long_name)
        ?height
        where{
        {
        select distinct ?s ?height
        where {
        ?dobj cpmeta:hasObjectSpec <http://meta.icos-cp.eu/resources/cpmeta/atc"""+tracer+dataobject[level-1]+"""> .
        ?dobj cpmeta:wasAcquiredBy/prov:wasAssociatedWith ?s .
        ?dobj cpmeta:hasSizeInBytes ?size .

        OPTIONAL{?dobj cpmeta:wasAcquiredBy/cpmeta:hasSamplingHeight ?height }
        FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
        }
        }
        ?s cpmeta:hasStationId ?sName .
        ?s cpmeta:hasName ?lName .
        ?s cpmeta:countryCode ?Country .
        ?s cpmeta:hasLatitude ?lat .
        ?s cpmeta:hasLongitude ?lon .
        ?s cpmeta:hasElevation ?alt .
        }
    """
    
    return query
#------------------------------------------------------------------------------

def icos_hist_sparql():
    
    '''
    Description: Function that returns a pandas DataFrame with info
                 for all stations included in the drought2018AtmoProduct. 
                
    Input:       No input parameters
    
    Output:      Pandas DataFrame
                
                 1. Station code, 3 characrers (var_name: "Short_name", var_type: String)
                 2. Country code, 2 characters (var_name: "Country", var_type: String)
                 3. Station latitude (var_name: "lat", var_type: String)
                 4. Station longitude (var_name: "lon", var_type: String)
                 5. Station elevation (var_name: "alt", var_type: String)
                 6. Station name (var_name: "Long_name", var_type: String)
                 7. Sampling height (var_name: "height", var_type: String)
                
                
    '''
  
    
    #Define URL:
    url = 'https://meta.icos-cp.eu/sparql'
    
    query = """
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        select
        (str(?sName) AS ?Short_name)
        ?Country
        ?lat ?lon ?alt
        (str(?lName) AS ?Long_name)
        ?height
        where{
        {
        select distinct ?s ?height
        where {
        ?dobj cpmeta:hasObjectSpec <http://meta.icos-cp.eu/resources/cpmeta/drought2018AtmoProduct> .
        ?dobj cpmeta:wasAcquiredBy/prov:wasAssociatedWith ?s .
        ?dobj cpmeta:hasSizeInBytes ?size .
        OPTIONAL{?dobj cpmeta:wasAcquiredBy/cpmeta:hasSamplingHeight ?height }
        FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
        }
        }
        ?s cpmeta:hasStationId ?sName .
        ?s cpmeta:hasName ?lName .
        ?s cpmeta:countryCode ?Country .
        ?s cpmeta:hasLatitude ?lat .
        ?s cpmeta:hasLongitude ?lon .
        ?s cpmeta:hasElevation ?alt .
        }
    """
    
    return query

#------------------------------------------------------------------------------

def get_coords_icos_stations_atc():
    
    """
    Input parameters: No input parameter/s
    Output:           pandas dataframe
                      columns: 
                            1. URL to station landing page (var_name: 'station', var_type: String)
                            2. Name of station PI (var_name: 'PI_names', var_type: String)
                            3. Station name (var_name: 'stationName', var_type: String)
                            4. 3-character Station ID (var_name: 'stationId', var_type: String)
                            5. 2-character Country code (var_name: 'Country', var_type: String)
                            6. Station Latitude (var_name: 'lat', var_type: String)
                            7. Station Longitude (var_name: 'lon', var_type: String)
                            8. Station Elevation (var_name: 'alt', var_type: String)
    """
    

    query = """
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        select *
        from <http://meta.icos-cp.eu/resources/icos/>
        where{
        {
        select ?station (GROUP_CONCAT(?piLname; separator=";") AS ?PI_names)
        where{
          ?station a cpmeta:AS .
          ?pi cpmeta:hasMembership ?piMemb .
          ?piMemb cpmeta:atOrganization ?station  .
           ?piMemb cpmeta:hasRole <http://meta.icos-cp.eu/resources/roles/PI> .
           filter not exists {?piMemb cpmeta:hasEndTime []}
           ?pi cpmeta:hasLastName ?piLname .
        }
        group by ?station
        }
        ?station a cpmeta:AS .
        ?station cpmeta:hasName ?stationName ;
           cpmeta:hasStationId ?stationId ;
           cpmeta:countryCode ?Country ;
           cpmeta:hasLatitude ?lat ;
           cpmeta:hasLongitude ?lon ;
           cpmeta:hasElevation ?alt .
        }
        order by ?Short_name
    """
    
    return query

# -----------------------------------------------------------------------------