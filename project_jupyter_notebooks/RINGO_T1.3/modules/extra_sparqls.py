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
