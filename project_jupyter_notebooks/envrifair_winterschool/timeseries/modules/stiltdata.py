def get_timeseries(station, sDate, eDate, stilt_st_path='/data/stiltweb/stations/', stilt_fp_path='/data/stiltweb/slots/'):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Fri Dec 11 11:00:00 2020
    Last Changed:     Fri Dec 11 11:00:00 2020
    Version:          0.0.1
    Author(s):        Ute Karstens, Karolina Pantazatou
    
    Description:      Function that takes three input parameters; STILT Station ID, a dataframe of Datetime Objects
                      and a dataframe showing the STILT Model Result and ICOS Level-1 & Level-2 data availability,
                      checks if there are STILT concentration time series available for the given parameters, and, if
                      this is the case, returns the available STILT concentration time series in a pandas dataframe.
                      
    Input parameters: 1. STILT Station Code
                         (var_name: 'station', var_type: String)
                      2. Start date for time series e.g. (Year, Month, Day, Hour)
                         (var_name: 'sDate', var_type: tuple)
                      3. End date for time series e.g. (Year, Month, Day, Hour)
                         (var_name: 'eDate', var_type: tuple)
                      4. Path to STILT station information files
                         (var_name: 'stilt_st_path', var_type: String)
                      5. Path to STILT time series files
                         (var_name: 'stilt_fp_path', var_type: String)

    Output:           Pandas Dataframe
                      
                      Columns:
                      1. Time (var_name: "isodate", var_type: date),
                      2. STILT CO2 (var_name: "co2.fuel", var_type: float)
                      3. Biospheric CO2 emissions (var_name: "co2.bio", var_type: float)
                      4. Background CO2 (var_name: "co2.background", var_type: float)
    
    """
    
    #Import modules:
    import os
    import requests
    import numpy as np
    import pandas as pd
    
    #Add URL:
    url = 'https://stilt.icos-cp.eu/viewer/stiltresult'
    
    #Get locIdent for selected station:
    locIdent=os.path.split(os.readlink(stilt_st_path+station))[-1]
    
    #Add headers:
    headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}
    
    #Create an empty list, to store the new time range with available STILT model results:
    new_range=[]
    
    #Define start date:
    start_date = pd.Timestamp(sDate[0],sDate[1],sDate[2],sDate[3])

    #Define end date:
    end_date = pd.Timestamp(eDate[0],eDate[1],eDate[2],eDate[3])
        
    #Create a pandas dataframe containing one column of datetime objects with 3-hour intervals:
    date_range = pd.date_range(start_date, end_date, freq='3H')
    
    #Loop through every Datetime object in the dataframe:
    for zDate in date_range:
        
        #Check if STILT results exist:
        if os.path.exists(stilt_fp_path + locIdent + '/'+
                          str(zDate.year)+'/'+str(zDate.month).zfill(2)+'/'+
                          str(zDate.year)+'x'+str(zDate.month).zfill(2)+'x'+str(zDate.day).zfill(2)+'x'+
                          str(zDate.hour).zfill(2)+'/'):
            
            #If STILT-results exist for the current Datetime object, append current Datetime object to list: 
            new_range.append(zDate)
    
    #If the list is not empty:
    if len(new_range) > 0:
        
        #Assign the new time range to date_range:
        date_range = new_range
        
        #Get new starting date:
        fromDate = date_range[0].strftime('%Y-%m-%d')
        
        #Get new ending date:
        toDate = date_range[-1].strftime('%Y-%m-%d')
        
        #Store the STILT result column names to a variable:
        columns = ('["isodate","co2.stilt","co2.fuel","co2.bio", "co2.background"]')
        #columns = ('["isodate","co2.stilt","co2.fuel","co2.bio","co2.fuel.coal","co2.fuel.oil",'+
                   #'"co2.fuel.gas","co2.fuel.bio","co2.energy","co2.transport", "co2.industry",'+
                   #'"co2.others", "co2.cement", "co2.background",'+
                   #'"co.stilt","co.fuel","co.bio","co.fuel.coal","co.fuel.oil",'+
                   #'"co.fuel.gas","co.fuel.bio","co.energy","co.transport", "co.industry",'+
                   #'"co.others", "co.cement", "co.background",'+
                   #'"rn", "rn.era","rn.noah","wind.dir","wind.u","wind.v","latstart","lonstart"]')
        
        #Store the STILT result data column names to a variable:
        data = '{"columns": '+columns+', "fromDate": "'+fromDate+'", "toDate": "'+toDate+'", "stationId": "'+station+'"}'
        
        #Send request to get STILT results:
        response = requests.post(url, headers=headers, data=data)
        
        #Check if response is successful: 
        if response.status_code != 500:
            
            #Get response in json-format and read it in to a numpy array:
            output=np.asarray(response.json())
            
            #Convert numpy array with STILT results to a pandas dataframe: 
            df = pd.DataFrame(output[:,:], columns=eval(columns))
            
            #Replace 'null'-values with numpy NaN-values:
            df = df.replace('null',np.NaN)
            
            #Set dataframe data type to float:
            df = df.astype(float)
            
            #Convert the data type of the 'date'-column to Datetime Object:
            df['date'] = pd.to_datetime(df['isodate'], unit='s')
            
            #Set 'date'-column as index:
            df.set_index(['date'],inplace=True)
            
            #Add column with station name:
            df['name'] = station
            
            #Add column with model - name:
            df['model'] = 'STILT'
            
        else:
            
            #Print message:
            print("\033[0;31;1m Error...\nToo big STILT dataset!\nSelect data for a shorter time period.\n\n")
            
            #Create an empty dataframe:
            df=pd.DataFrame({'A' : []})
            
            
    #If the request fails, return an empty dataframe:        
    else:
        df=pd.DataFrame({'A' : []})
        
    #Return dataframe:    
    return df