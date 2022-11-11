import pandas as pd
import datetime as dt
from ipywidgets import IntProgress
import os
import numpy as np
import netCDF4 as cdf
import json
from icoscp.sparql.runsparql import RunSparql
from netCDF4 import Dataset, date2index
pathFP='/data/stiltweb/stations/'
path_cp = '/data/dataAppStorage/netcdf/'
stcDataPath = '/data/project/stc/'
country_masks = Dataset(os.path.join(stcDataPath,'europe_STILT_masks.nc'))
# create an object that takes these. 
# based on network char gui?

def update_footprint_based_on_threshold(input_footprint, threshold):

    threshold_sensitivity=input_footprint.sum()*threshold

    #create a dataframe that will have the updated sensitivity values + the steps on the way
    df_sensitivity = pd.DataFrame()

    #one column with the original sensitivity values. Has an index that will be used to sort back to 
    #this order (flattened 2D... back to 2D with updated sensitivity values in last step)
    df_sensitivity['sensitivity']=input_footprint.flatten()
    
    #sensitivity values sorterd from largest to smallest
    df_sensitivity_sorted=df_sensitivity.sort_values(by=['sensitivity'], ascending=False)
    
    #another column that has the cumilated sum of the values in the sensitivity column.
    #used to determine when the footprint threshold is met. 
    df_sensitivity_sorted['cumsum_sens']=df_sensitivity_sorted.cumsum()

    if threshold==1:

        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['sensitivity']==0, 0, 1)
    else:
        df_sensitivity_sorted['mask_threshold']= np.where(df_sensitivity_sorted['cumsum_sens']>=threshold_sensitivity, 0, 1)
    
    #mask*sensitivity = for "new" footprint that only has sensitivity values in the cells that have the value 1.
    df_sensitivity_sorted['mask_sensitivity']=df_sensitivity_sorted['mask_threshold']*df_sensitivity_sorted['sensitivity']

    #sort it back (so in correct lat/lon order for "packing back up" to 2D)
    df_sensitivity_upd=df_sensitivity_sorted.sort_index()

    list_updated_sensitivity=df_sensitivity_upd['mask_sensitivity'].tolist()
    
    upd_footprint_sens=np.array(list_updated_sensitivity).reshape(480, 400)

    return upd_footprint_sens

def find_dobj_from_name(filename):

    '''
    Description: Function that returns the data object 
                 for a specified level 3 product netcdf filename. 
                
    Input:       netcdf filename
    
    Output:      Data Object ID (var_name: "dobj", var_type: String)
    '''
    
    query = '''
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        select ?dobj 
        where{
        ?dobj cpmeta:hasName "'''+filename+'''"^^xsd:string .
        FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
        FILTER EXISTS {?dobj cpmeta:hasSizeInBytes ?size }
        }
    '''
    return query

def check_cp(cp_path,filename):
    cp_name = ''
    dobj_L3 = RunSparql(sparql_query=find_dobj_from_name(filename),output_format='csv').run()

    if len(dobj_L3.split('/')) > 1:
        cp_name = (cp_path+dobj_L3.split('/')[-1]).strip()
    if not(os.path.exists(cp_name)):
        cp_name = ''
        print('file '+filename+' does not exist in CP')
        
    return cp_name

def import_landcover_HILDA(year='2018'):
    
    name_data = 'hilda_lulc_'+ year +'.nc' 
    
    all_hilda_classes= Dataset(stcDataPath + name_data)

    #access all the different land cover classes in the .nc files:
    cropland = all_hilda_classes.variables['cropland'][:,:]
    ocean = all_hilda_classes.variables['ocean'][:,:]
    forest_decidious_broad_leaf = all_hilda_classes.variables['f_de_br_le'][:,:]
    forest_decidious_needle_leaf = all_hilda_classes.variables['f_de_ne_le'][:,:]
    forest_evergreen_broad_leaf = all_hilda_classes.variables['f_eg_br_le'][:,:]
    forest_evergreen_needle_leaf = all_hilda_classes.variables['f_eg_ne_le'][:,:]
    mixed_forest = all_hilda_classes.variables['forest_mix'][:,:]
    forest_unknown = all_hilda_classes.variables['forest_unk'][:,:]
    grass_shrub = all_hilda_classes.variables['grass_shru'][:,:]
    other_land = all_hilda_classes.variables['other_land'][:,:]
    pasture = all_hilda_classes.variables['pasture'][:,:]
    urban = all_hilda_classes.variables['urban'][:,:]
    water = all_hilda_classes.variables['water'][:,:]
    unknown = all_hilda_classes.variables['unknown'][:,:]
    
    # aggregated classes:
    broad_leaf_forest = forest_decidious_broad_leaf + forest_evergreen_broad_leaf 
    coniferous_forest = forest_decidious_needle_leaf+ forest_evergreen_needle_leaf
    mixed_forest = mixed_forest + forest_unknown
    other = other_land + water
       
        
    return broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown
    

def return_europe_mask():
    
    all_countries= ["ALB","Andorra", "AUT", "BLR","BEL", "BIH", "BGR", "HRV", "CYP", "CZE", "DNK","EST","FIN","FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD", "MTL","MDA","MNE","NLD","NOR","POL","PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR"]
    first_country = True
    for country_code in all_countries:
        
        country_mask = country_masks.variables[country_code][:,:]

        if first_country:

            europe_mask = country_mask

            first_country = False

        else:
            europe_mask = europe_mask + country_mask
            
    return europe_mask

def create_network_fps(year, stations, name_save, fp_percent, notes = ''):
    
    # relevant for footprint creation 
    path_name_save = os.path.join('network_footprints', name_save)
    if not os.path.exists(path_name_save):
        os.makedirs(path_name_save)
    
    path_name_save_representation = os.path.join('network_footprints_representation', name_save)
    if not os.path.exists(path_name_save_representation):
        os.makedirs(path_name_save_representation)
    
    date_range = pd.date_range(dt.datetime(year,1,1,0), (dt.datetime(year, 1, 3, 0)-dt.timedelta(hours=3)), freq='3H')
    #date_range = pd.date_range(dt.datetime(year,1,1,0), (dt.datetime(year+1, 1, 1, 0)-dt.timedelta(hours=3)), freq='3H')

    time_of_day = [0, 3, 6, 9, 12, 15, 18, 21]

    notes = notes

    # not working currently - becomes a list of dates (which works but .min() to write to the json does not work).
    #date_range = [date for date in date_range if date.hour in time_of_day]

    f = IntProgress(min=0, max=len(date_range), description='Creating footprints and establishing representation:', style= {'description_width': 'initial'}) # instantiate the bar
    display(f) # display the bar
    
    ##########################
    # relevant for establishing representation
    countries = ["ALB","Andorra","AUT", "BLR","BEL","BIH", "BGR","HRV","CYP","CZE","DNK","EST","FIN", "FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD","MTL", "MDA",\
                 "MNE","NLD","NOR", "POL", "PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR", "Europe"]

    # grid area (m2) of each cell
    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')
    # grid area (km2) of each cell 
    gridarea = f_gridarea.variables['cell_area'][:]/1000000

    # access the flux data
    filename_resp = check_cp(path_cp,'VPRM_ECMWF_RESP_2020_CP.nc')
    filename_gee = check_cp(path_cp,'VPRM_ECMWF_GEE_2020_CP.nc')

    f_resp = cdf.Dataset(filename_resp)
    f_gee = cdf.Dataset(filename_gee)

    # same for both datasets
    times = f_resp.variables['time']

    # access HILDA land cover data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    list_classes_names = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    list_classes_km2 = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland,\
                        pasture, urban, unknown]

    # want vegetation fraction HILDA land cover maps (as opposed to km2 for the entire cell - "list_classes_km2")
    list_classes = []

    for landcover in list_classes_km2:

        landcover_fraction = landcover/gridarea

        list_classes.append(landcover_fraction)

    # what columns to have in the resulting dataframe depend on selection of countries.
    # here create a loop that creates file names.
    # order here is essential. The same order will be kept in the loop that creates and finally sets the data into 
    # this dataframe
    columns_save= ['date']
    list_for_columns = ['total', 'broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    for country in countries:

        for column in list_for_columns:
            columns_save.append(country + '_' + column + '_resp')
            columns_save.append(country + '_' + column + '_gee')
            columns_save.append(country + '_' + column + '_resp_even')
            columns_save.append(country + '_' + column + '_gee_even')

    df_to_analyze = pd.DataFrame(columns=columns_save)

    # counter to place the data in a new row for each date
    i = 0
    missing = []

    for date in date_range:
        df_footprints_network_average = pd.DataFrame()
        f.value += 1
        fp_string = str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' +  str(date.hour)
        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)
        index = 1
        # network footprint for specific day
        df_footprints_network = pd.DataFrame()
        for station in stations:
            filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
                 +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename):

                f_fp = cdf.Dataset(filename)
                fp=f_fp.variables['foot'][:,:,:]
                # make it the 50% most important
                fp_50 = update_footprint_based_on_threshold(fp, fp_percent)

                df_footprints_network[('fp_' + str(index))]=fp_50.flatten()

                index = index + 1

            else:
                missing.append(station + ':' + date_string)

        # make a footprint based on all max values of the combined footprints. 
        fp_network_50_list = df_footprints_network[df_footprints_network.columns].max(axis=1)
        fp_network_50=np.array(fp_network_50_list.tolist()).reshape(480, 400)
        
        # save network footprint. 
        df_footprints_network_average[fp_string]=fp_network_50_list
        df_footprints_network_average.to_csv(os.path.join('network_footprints', name_save, fp_string + '.csv'), index = False)
        
        # use network footprint to calculate representation:
        ntime = date2index(date,times,select='nearest')

        resp = f_resp.variables['RESP'][ntime][:][:]
        gee = f_gee.variables['GEE'][ntime][:][:]

        fp_network_50_resp = fp_network_50 * resp 
        fp_network_50_gee = fp_network_50 * gee 

        # the list "data_specific_date" will be filled with data for all the columns for this specific date
        # added to the dataframe when the country loop is done (load data for all selected countries), and the 
        # loop over land cover classes which is started once for each country (sensing of broad leaf forest
        # for specific country for specific day)
        data_specific_date = [date_string]
        for country_code in countries:

            if country_code == "Europe":
                country_mask = return_europe_mask()

            else:
                country_mask = country_masks.variables[country_code][:,:]


            fp_network_50_resp_country = fp_network_50_resp * country_mask
            fp_network_50_gee_country = fp_network_50_gee * country_mask

            # here - added multiplied by gridarea... total area associated with flux
            # to be compared with area of each land cover associated with the flux.
            total_resp_country = fp_network_50_resp_country.sum()
            total_gee_country = fp_network_50_gee_country.sum()


            # compare to if footprint spread out evenly
            # sum of sensing within the country (area) border
            sum_country = (country_mask * fp_network_50).sum()
            # if sensing spread out evenly to all cells in the country, this would be the value
            # note that this is disregarding that cells further south has a larger area (1/8th * 1/12 of a degree). 
            average_sens_country = sum_country / country_mask.sum()
            #create "fake footprint" where evenly spread out (only used for the area of the country):
            sens_per_cell_list = [average_sens_country]*192000

            fp_network_50_even=np.array(sens_per_cell_list).reshape(480, 400)

            fp_network_50_even_resp = fp_network_50_even * resp * country_mask 
            fp_network_50_even_gee = fp_network_50_even * gee * country_mask 

            total_resp_country_even = fp_network_50_even_resp.sum()
            total_gee_country_even = fp_network_50_even_gee.sum()

            # add to average ratio, one column for each country:
            data_specific_date.extend([total_resp_country, total_gee_country, total_resp_country_even, total_gee_country_even])

            for landcover_hilda, landcover_name in zip(list_classes, list_classes_names):
                # * country_mask added. Else can be mulitiplied by too much on the borders. 
                total_resp_landcover_country = (fp_network_50_resp_country * landcover_hilda).sum()
                total_gee_landcover_country = (fp_network_50_gee_country * landcover_hilda).sum()

                total_resp_landcover_even_country = (fp_network_50_even_resp * landcover_hilda).sum()
                total_gee_landcover_even_country = (fp_network_50_even_gee * landcover_hilda).sum()  

                data_specific_date.extend([total_resp_landcover_country, total_gee_landcover_country,\
                                 total_resp_landcover_even_country,total_gee_landcover_even_country])      
        df_to_analyze.loc[i] = data_specific_date
        i = i + 1

    df_to_analyze.to_csv(os.path.join('network_footprints_representation', name_save +'_representation' + '.csv'), index=False)

    
    # create json files with information about the run:
    # network footprint file:
    today = date.today()
    today_string = today.strftime("%B %d, %Y")
    network_fp_dict = {"fileName": name_save, \
                      "startYear": date_range.min().year,
                      "startMonth": date_range.min().month,
                      "startDay": date_range.min().day,
                      "endYear": date_range.max().year,
                      "endMonth": date_range.max().month,
                      "endDay": date_range.max().day,
                      "timeOfDay": [0, 3, 6, 9, 12, 15, 18, 21],
                      "missing": missing,
                      "fpPercent": fp_percent,
                      "stations": stations,
                      "dateCreated": today_string,
                      "notes": notes}

    jsonString = json.dumps(network_fp_dict)
    jsonFile = open(os.path.join('network_footprints', name_save + '.json'), "w")
    jsonFile.write(jsonString)
    jsonFile.close()
    
    today = date.today()
    today_string = today.strftime("%B %d, %Y")
    network_fp_dict_rep= {"fileName": name_save +'_representation',
                      "fileNameNetwork": name_save, 
                      "countries": countries,
                      "startYear": date_range.min().year,
                      "startMonth": date_range.min().month,
                      "startDay": date_range.min().day,
                      "endYear": date_range.max().year,
                      "endMonth": date_range.max().month,
                      "endDay": date_range.max().day,
                      "timeOfDay": [0, 3, 6, 9, 12, 15, 18, 21],
                      "dateCreated": today_string,
                      "notes": notes}

    jsonString = json.dumps(network_fp_dict_rep)
    jsonFile = open(os.path.join('network_footprints_representation', name_save + '_representation' + '.json'), "w")
    jsonFile.write(jsonString)
    jsonFile.close()
