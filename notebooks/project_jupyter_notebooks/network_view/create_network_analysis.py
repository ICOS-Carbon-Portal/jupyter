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
from numpy import loadtxt
data_folder = '/data/project/stc/footprints_2018_averaged'
load_lat=loadtxt(os.path.join(data_folder, 'latitude.csv'), delimiter=',')
load_lon=loadtxt(os.path.join(data_folder, 'longitude.csv'), delimiter=',')
import xarray as xr
path_network_footprints = '/data/project/obsnet/network_footprints'
path_network_footprints_local = 'network_footprints'

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

def create_xarray(fp_list,date):

    data=np.array(fp_list).reshape(1, 480, 400)

    time = [date]

    # put data into a dataset
    ds = xr.Dataset(
        data_vars=dict(
            network_foot=(["time","lat", "lon"], data)
        ),
        coords=dict(
            time=(["time"], time),
            lat=(["lat"], load_lat),
            lon=(["lon"], load_lon),
        ),
        attrs=dict(description="network footprints"),
    )
 
    return ds


def create_network_fps(stations, date_range, time_selection, name_save, threshold, notes = ''):
    
    if not os.path.exists(os.path.join('network_footprints', name_save)):
        os.makedirs(os.path.join('network_footprints', name_save))
        
    if not os.path.exists('network_footprints_representation'):
        os.makedirs('network_footprints_representation')
    
   
    # relevant for footprint creation 
    f = IntProgress(min=0, max=len(date_range), description='Creating network footprints:', style= {'description_width': 'initial'}) # instantiate the bar
    display(f) # display the bar

    i = 0
    missing = []
    list_xarray = []
    first = True
    for date in date_range:
        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)
        if first or date.month != month_current:
            
            if not first:
                
                xarray_month = xr.concat(list_xarray, dim='time')

                file_path = os.path.join('network_footprints', name_save, name_save + '_' + str(month_current) + '.nc')
                
                xarray_month.to_netcdf(file_path)

                #empty the xarray list:
                list_xarray = []
                
            month_current = date.month
                
        first = False
            
        f.value += 1

        index = 1

        df_footprints_network = pd.DataFrame()
        for station in stations:
            filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
                 +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename):

                f_fp = cdf.Dataset(filename)
                fp=f_fp.variables['foot'][:,:,:]
                # make it the 50% most important
                fp_50 = update_footprint_based_on_threshold(fp, threshold)

                df_footprints_network[('fp_' + str(index))]=fp_50.flatten()

                index = index + 1

            else:
                missing.append(station + ':' + date_string)

        # make a footprint based on all max values of the combined footprints. 
        fp_network_50_list = df_footprints_network[df_footprints_network.columns].max(axis=1)
              
        xarray_individual = create_xarray(fp_network_50_list, date)
        list_xarray.append(xarray_individual)

    if len(list_xarray)>0:
        
        xarray_month = xr.concat(list_xarray, dim='time')
        file_path = os.path.join('network_footprints', name_save, name_save + '_' + str(month_current) + '.nc')
        xarray_month.to_netcdf(file_path)

    today = date.today()
    today_string = today.strftime("%B %d, %Y")
    network_fp_dict = {"fileName": name_save, \
                      "startYear": min(date_range).year,
                      "startMonth": min(date_range).month,
                      "startDay": min(date_range).day,
                      "endYear": max(date_range).year,
                      "endMonth": max(date_range).month,
                      "endDay": max(date_range).day,
                      "timeOfDay": time_selection,
                      "missing": missing,
                      "fpPercent": (threshold),
                      "stations": stations,
                      "dateCreated": today_string,
                      "notes": notes}

    jsonString = json.dumps(network_fp_dict)
    jsonFile = open(os.path.join('network_footprints', name_save + '.json'), "w")
    jsonFile.write(jsonString)
    jsonFile.close()

def create_network_fps_by_extension(stations, folder, name_save, notes=""):
    
    
    if not os.path.exists(os.path.join('network_footprints', name_save)):
        os.makedirs(os.path.join('network_footprints', name_save))
        
    if not os.path.exists('network_footprints_representation'):
        os.makedirs('network_footprints_representation')

    if folder[-5:] == 'local': 
        folder = folder[:-6]
        path = path_network_footprints_local
    else:
        folder = folder
        path = path_network_footprints

    json_file = folder + '.json' 
    network_info = open(os.path.join(path, json_file))
    network_info = json.load(network_info)
    footprint_stations = network_info['stations']
    date_range_full = pd.date_range(dt.datetime(network_info['startYear'],network_info['startMonth'],network_info['startDay'], 0), (dt.datetime(network_info['endYear'],network_info['endMonth'],network_info['endDay'], 21)), freq='3H')   
    date_range = [date for date in date_range_full if date.hour in network_info['timeOfDay']]
    footprint_missing = network_info['missing']
    fp_percent = network_info['fpPercent']
    
    f = IntProgress(min=0, max=len(date_range), style= {'description_width': 'initial'}) # instantiate the bar

    display(f) # display the bar

    missing = []
    list_xarray = []
    first = True
    for date in date_range:
        f.value += 1
        date_string = str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' +  str(date.hour)
        
        # for saving the extended xarrays in monthly files
        if first or date.month != current_month:
            
            if not first:
                
                xarray_month = xr.concat(list_xarray, dim='time')

                file_path = os.path.join('network_footprints', name_save, name_save + '_' + str(current_month) + '.nc')
                xarray_month.to_netcdf(file_path)

                #empty the xarray list:
                list_xarray = []
            current_month = date.month
            footprints = xr.open_dataset(os.path.join(path, folder, folder + '_' + str(current_month) + '.nc'))
            first = False


        # added station / network
        df_footprints_network = pd.DataFrame()
        # take the netwrok footprint
        df_footprints_network['starting_network'] = footprints.sel(time=date).network_foot.data.flatten()
        
        for station in stations:

            filename=(pathFP+station+'/'+str(date.year)+'/'+str(date.month).zfill(2)+'/'
                 +str(date.year)+'x'+str(date.month).zfill(2)+'x'+str(date.day).zfill(2)+'x'+str(date.hour).zfill(2)+'/foot')

            if os.path.isfile(filename):
                
                f_fp = cdf.Dataset(filename)

                fp=f_fp.variables['foot'][:,:,:]

                fp_50=update_footprint_based_on_threshold(fp, 0.5)

                df_footprints_network['fp_added_' + station]=fp_50.flatten()

            else:
                missing.append(station + ':' + date_string)

        #network footprint for sites (before including also original network footprint)
        stations_network_fp_list = df_footprints_network[df_footprints_network.columns].max(axis=1)

        xarray_individual = create_xarray(stations_network_fp_list, date)
        
        list_xarray.append(xarray_individual)

   
    if len(list_xarray)>0:

        xarray_month = xr.concat(list_xarray, dim='time')
        file_path = os.path.join('network_footprints', name_save, name_save + '_' + str(current_month) + '.nc')
        xarray_month.to_netcdf(file_path)
    
    ## create a json file with the information about the created network footprint
    today = date.today()
    today_string = today.strftime("%B %d, %Y")
    network_fp_dict = {"fileName": name_save, \
                      "startYear": min(date_range).year,
                      "startMonth": min(date_range).month,
                      "startDay": min(date_range).day,
                      "endYear": max(date_range).year,
                      "endMonth": max(date_range).month,
                      "endDay": max(date_range).day,
                      "timeOfDay": network_info['timeOfDay'],
                      "missing": footprint_missing + missing,
                      "fpPercent": fp_percent,
                      "stations": footprint_stations + stations,
                      "dateCreated": today_string,
                      "notes": notes}

    jsonString = json.dumps(network_fp_dict)
    jsonFile = open(os.path.join('network_footprints', name_save + '.json'), "w")
    jsonFile.write(jsonString)
    jsonFile.close()
    
    establish_representation(date_range, name_save)
          
def establish_representation(date_range, network_footprint):
    
    f = IntProgress(min=0, max=len(date_range), description='Establishing representation:', style= {'description_width': 'initial'}) # instantiate the bar
    display(f) # display the bar

    # relevant for establishing representation
    countries = ["ALB","Andorra","AUT", "BLR","BEL","BIH", "BGR","HRV","CYP","CZE","DNK","EST","FIN", "FRA","DEU","GRC","HUN","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MKD","MTL", "MDA",\
                 "MNE","NLD","NOR", "POL", "PRT","SRB","ROU","SMR","SVK","SVN","ESP","SWE","CHE","GBR", "Europe"]

    # grid area (m2) of each cell
    f_gridarea = cdf.Dataset('/data/project/stc/gridareaSTILT.nc')
    # grid area (km2) of each cell 
    gridarea = f_gridarea.variables['cell_area'][:]/1000000

    # access HILDA land cover data
    broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland, pasture, urban, unknown = import_landcover_HILDA(year='2018')

    list_classes_names = ['broad_leaf_forest', 'coniferous_forest', 'mixed_forest', 'ocean', 'other', 'grass_shrub', 'cropland', \
                          'pasture', 'urban', 'unknown']

    list_classes_km2 = [broad_leaf_forest, coniferous_forest, mixed_forest, ocean, other, grass_shrub, cropland,\
                        pasture, urban, unknown]

    # want vegetation fraction HILDA land cover maps (as opposed to km2 for the entire cell - "list_classes_km2")
    list_classes = []

    i = 0
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

    first_vprm = True
    first_month = True
    for date in date_range:
        
        # access the correct VPRM flux dataset (yearly files)
        if first_vprm or date.year!=current_year:

            current_year = date.year

            filename_resp = check_cp(path_cp,'VPRM_ECMWF_RESP_' + str(current_year) + '_CP.nc')

            filename_gee = check_cp(path_cp,'VPRM_ECMWF_GEE_' + str(current_year) + '_CP.nc')

            f_resp = cdf.Dataset(filename_resp)

            f_gee = cdf.Dataset(filename_gee)

            # same for both datasets
            times = f_gee.variables['time']

            first_vprm = False
            
        if first_month or date.month!=current_month:
            
            current_month = date.month
            xarray_data = xr.open_dataset(os.path.join('network_footprints', network_footprint, network_footprint + '_' + str(current_month) + '.nc'))
            
            first_month = False

        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day) + ' ' +  str(date.hour)

        fp_network_50 = xarray_data.sel(time=date).network_foot.data

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
        
        f.value += 1

    df_to_analyze.to_csv(os.path.join('network_footprints_representation', network_footprint + '_representation.csv'))
