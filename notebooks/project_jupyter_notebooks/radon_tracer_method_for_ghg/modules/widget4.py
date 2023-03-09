# -*- coding: utf-8 -*-
"""
Created on Fri Jan  22 2021

@author: Camille Yver Kwok

Functions to run the RTM.
Works with jupyterlab, added progressbar, calculate all fluxes with criteria to sort after.
"""

#Import Modules
import os
from os.path import exists
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.odr import *
from sklearn.metrics import r2_score
import datetime as DT
from datetime import datetime
import netCDF4 as cdf
#import paramiko
HOME = os.path.expanduser("~")+'/'
import getpass
import json 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, LAKES
import matplotlib.pyplot as p
import matplotlib.ticker as mticker
from matplotlib.backends.backend_pdf import PdfPages
import xarray as xr

from pprint import pprint
from modules.helper import get_radon_maps

#Import ICOS tools:
from icoscp.cpb.dobj import Dobj
from icoscp.sparql.runsparql import RunSparql
from icoscp.sparql import sparqls
from icoscp.station import station

#regridding tools
from cdo import *
cdo = Cdo()

#for the widgets
from IPython.core.display import display, HTML 
from ipywidgets import DatePicker,SelectMultiple,Text, Button, IntText, Password, Dropdown, RadioButtons, Output, IntProgress
from IPython.display import clear_output, display
from ipyfilechooser import FileChooser

path_stiltweb = '/data/stiltweb/'

#log
import logging
logging.basicConfig(level=logging.INFO, filename="RTM.log",filemode="w")

##Functions
#-----------------------------------------------------------------------------------------------------------
#function to choose between RTM with ATC or CP
def choose_RTM(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice, plot_type,stations):
    print('choose_RTM')
    style = {'description_width': 'initial'}
    if plot_db.value=='ATC':
        form_out = Output(layout={'border': '1px solid black'})
        #get login and password
        login=Text(
            value=None,
            description='Enter your login to the icos server:',
            disabled=False,
            style=style)
        log=Output()
        with log:
            display(login)
        
        pawd=Password(placeholder='Enter password', description= 'Password:',disabled=False)
        passe=Output()
        with passe:
            display(pawd)
        #go button
        enter_button = Button(description='Enter',
                           disabled=False,
                           button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
        def update_func(button_c):
            RTM_go(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice, login, pawd, plot_type,stations)
        enter_button.on_click(update_func)
    
        enbut=Output()
        with enbut:
            display(enter_button)
        with form_out:
            display(log,passe,enbut)
        display(form_out)
        
    else:
        #Run the CP TRM
        login='login'
        pawd='pawd'
        RTM_go(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice,login, pawd, plot_type,stations)
#--------------------------------------------------------------------------------------------------------------
# function to read Rn flux maps
def read_rnmap(filename):    
    # read INGOS Rn flux map
    # latitude and longitude are center of grid cell
    f = cdf.Dataset(filename)
    rn_flux=f.variables["rn_flux"][:,:,:] 
    rn_lon=f.variables["lon"][:]
    rn_lat=f.variables["lat"][:]
    time=f.variables["time"][:]
    unit="["+f.variables["rn_flux"].units+"]"
   # datetime=cdf.num2date(f.variables["time"][:],units=f.variables["time"].units)
    f.close()
    return rn_flux, rn_lon, rn_lat, time, unit

#----------------------------------------------------------------------------------------------------------------------
####For one station, compute the aggregated footprints over one year and save a new netCDF file to read later
##Only need to be done once per site
def aggegated_fp(ist, start_date, end_date):

    stations = create_STILT_dictionary()
    logging.info("in aggreg")
    
    if not ist:
            ist="SAC100"
    if not start_date:
        start_date=DT.datetime(2019,1,1,0)
    if not end_date:
        end_date=DT.datetime(2019,12,31,23)

    if not ist in stations.keys():
        logging.info('no footprints for station: ',ist)
    else:
        logging.info('station: ',ist)
        date_range = pd.date_range(start_date, end_date, freq='3H')
        date_range = date_range[((22 <= date_range.hour) & (date_range.hour <= 24)) | ((0<=date_range.hour) & (date_range.hour<=4))]
        #print(date_range)
        timeselect="nighttime"
        nfp, fp, lon1, lat1, title2, found = read_aggreg_footprints(stations, ist, date_range, timeselect=timeselect)
        #print(lon)
        #print(lon1.shape)
        #print(fp.shape)
        #fp[1,lat==(lat[(lat<=latitude)][-1]),lon==(lon[(lon<=longitude)][-1])]
        #Plot footprint map 
        title = (str(nfp)+' mean footprint '+title2+'\n'+
                     'station: '+stations[ist]['name']+'  '+ist+'  '+stations[ist]['locIdent'])
        # indicate station location 
        # zoom in around station selected by zoom
       # plot_maps(fp, lon1, lat1, title=title, label='surface influence', unit='[ppm / ($\mu$mol / m$^{2}$s)]', 
        #              linlog='log10', vmin=-6, vmax=-2, station=[ist], stations=stations, zoom=ist)
        fn = '/data/radon_map/rtm/inputData/2019_'+ist+'_aggregfootprints_nighttime.nc'
        ds = cdf.Dataset(fn, 'w', format='NETCDF4')
        lat = ds.createDimension('lat', 480)
        lon = ds.createDimension('lon', 400)
        lats = ds.createVariable('lat', 'f4', ('lat',))
        lons = ds.createVariable('lon', 'f4', ('lon',))
        fpw = ds.createVariable('fpw', 'f4', ('lat', 'lon',))
        fpw.units = 'None'
        lats.unit="degrees_north"
        lons.unit="degrees_east"
        lats[:]=lat1
        lons[:]=lon1 
        
        #Normalise the aggregated footprints to get weights without unit to aply to the Rn flux from the Radon flux mapimport netCDF4 as cdf
        fpw[:,:]=fp[:,:]/np.sum(fp)
        #print(np.mean(fpw))
        ds.close()
#-----------------------------------------------------------------------------------        
def updateProgress(f, desc=''):
    # custom progressbar updates
    f.value += 1
    if not desc:
        f.description = 'Day ' + str(f.value) + '/' + str(f.max)
    else:
        f.description = str(desc)
#--------------------------------------------------------------------------------------------------------------
def RTM_go(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice, login, pawd, plot_type,stations):
    sitelevel=station_choice.value
    if len(sitelevel)<4:
        site=sitelevel
        level="{0:0>3}".format([value['alt'] for key,value in stations_icos.items() if key==site][0])
        #sitelevel=site+level
    else:
        site=sitelevel[0:3]
        level=sitelevel[3:6]

    #name of the dataproducts to look at
    #for NRT data
    prdict = {'co2':'ICOS ATC NRT CO2 growing time series',
              'ch4':'ICOS ATC NRT CH4 growing time series',
              'co':'ICOS ATC NRT CO growing time series',
              'meteo':'ICOS ATC NRT Meteo growing time series',
              'rn222': 'ICOS ATC NRT radon data csv time series'}
    #for release data
    prdict2 = {'co2':'ICOS ATC CO2 Release',
              'ch4':'ICOS ATC CH4 Release',
              'co':'ICOS ATC CO Release'}
    #Average Rn flux for the station we are looking at, in Bq/m2/h
    Jrn1=flux_choice.value

    #Name of output file for the fluxes
    species=species_choice.value
    fileout='outputData/RTMFlux_'+str.upper(species)+'_'+sitelevel+'_'+str(fmap_choice.value)+'_'+str(fdate_choice.value)+'_'+str(edate_choice.value)
    #Variables depending on the species
    
    Vm=0.224 #molar volume 
    if species=="co2":
        Mm=44 #molar mass
        Pp=0.000001 #conversion ppm to mol 
    if species=="ch4":
        Mm=16 #molar mass
        Pp=0.000000001 #conversion ppb to mol
    if species=="co":
        Mm=28 #molar mass
        Pp=0.000000001 #conversion ppb to mol     
    if species=="n2o":
        Mm=44 #molar mass
        Pp=0.000000001 #conversion ppb to mol 
        
    #get the metadat info (lat, lon)
    tower = station.get(site)
    latitude=(tower.info()['lat'])
    longitude=(tower.info()['lon'])
    if site=='WAO':
        latitude=latitude-0.01
    
    #Chosen period: 
    Fd=fdate_choice.value #DT.datetime.strptime(fdate_choice.value, '%Y-%m-%d')
    Ed=edate_choice.value  #DT.datetime.strptime(edate_choice.value, '%Y-%m-%d')

    #Dataframe to save the data
    Flux=pd.DataFrame()

    #Get the two days beginning as Fd
    one_day = DT.timedelta(days=1)
    half_day= DT.timedelta(days=0.5)

    endrange=int((str(Ed-Fd).split()[0]))
    with progress_bar:
        g = IntProgress(min=0, max=endrange, style=style)
        display(g)
    updateProgress(g,"Calculation")
        
    for i in range(0,endrange):
        fd=Fd+i*one_day
        ed=fd+one_day       
        logging.info(str(fd)+str(ed))
                
        my_maps = get_radon_maps(outfmt='dict')     
        rn_map = xr.open_dataset(my_maps[fmap_choice.value])
        rn_flux=rn_map.rn_flux
        if (rn_flux.time==np.datetime64(fd)).any(): 
            Jrn2=np.float(np.mean(rn_flux[rn_flux.time==np.datetime64(fd),np.round(rn_flux.lat,1)==np.round(latitude,1),np.round(rn_flux.lon,1)==np.round(longitude,1)]))        
        else:
            Jrn2=-99/3600
            logging.info("The flux map year is not matching the asked year")
        
        #logging.info(Jrn2)
        #Jrn3: Calculate the average flux from aggregated yearly footprints and radon map - just for STILT
        #read netCDF file
        fn ="/data/radon_map/rtm/inputData/2019_"+sitelevel+"_aggregfootprints_nighttime.nc"
        # check if file exists
        if os.path.isfile(fn)==False:
            aggegated_fp(sitelevel,DT.datetime(2019,1,1,0),DT.datetime(2019,12,31,23))
        f = cdf.Dataset(fn)
        fp_weight=f.variables["fpw"][:,:] 
     
        #read radon map: need regridded version, check if exists
        
        radon_map=fmap_choice.value
        radon_map_regrid= '/data/radon_map/rtm/inputData/'+radon_map.split('.nc')[0]+'_regridded.nc'
        if os.path.isfile(radon_map_regrid)==False:
            print('Regridding')
            #my_maps[radon_map]
            cdo.remapcon('/data/radon_map/rtm/inputData/gridfile.txt', input='/data/radon_map/rtm/inputData/'+radon_map, output=radon_map_regrid)
            print('Done regridding')
            
        rn_map = xr.open_dataset(radon_map_regrid)
        rn_flux=rn_map.rn_flux
        #attribute a weight to each flux
        rn_weight=rn_flux*fp_weight
        #careful to remember there is a time variable in rn_weight...get the value for the day we are 
        #check that we have the right year for the map
        if (rn_weight.time==np.datetime64(fd)).any():    
            Jrn3=np.float(np.sum(rn_weight[rn_weight.time==np.datetime64(fd)]))
        else:
            
            Jrn3=-99/3600
        #Jrn4: use the footprint of the day for data before 2021.
        tdelta = DT.time(hour=0, minute=0)
        ffd=datetime.combine(fd, tdelta)
        
       
        timeselect="nighttime"
        date_range = pd.date_range(ffd+half_day, ffd+one_day+half_day, freq='3H')
        date_range = date_range[((21 <= date_range.hour) & (date_range.hour <= 24)) | ((0<=date_range.hour) & (date_range.hour<=4))]
        found = read_aggreg_footprints(stations, sitelevel, date_range, timeselect=timeselect)
        #print(date_range)            #print(found)
        if found!="no":
            #print('found yes')
            nfp, fp, lon, lat, title2, found= read_aggreg_footprints(stations, sitelevel, date_range, timeselect=timeselect)
            #normalize
            fpw=fp[:,:]/np.sum(fp)
            #print(fpw)
            #attribute a weight to each flux
            rn_weight=rn_flux*fpw
                
            #careful to remember there is a time variable in rn_weight...get the value for the day we are 
            if (rn_weight.time==np.datetime64(fd)).any():   
                Jrn4=np.float(np.sum(rn_weight[rn_weight.time==np.datetime64(fd)]))
            else:
                Jrn4=-99/3600
            #print(Jrn4)
            #print(Jrn1/3.6, Jrn2,Jrn3,Jrn4)
        else:  
            logging.info("No STILT run for this date")
            Jrn4=-99/3600
                
      #  print(Jrn1,Jrn2,Jrn3,Jrn4)   
        if plot_db.value=="ATC":
            #extract the data from the ICOS database, put it in temporary file
            host = "icos-ssh.lsce.ipsl.fr"
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=login.value,password=pawd.value, allow_agent=True)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('/home/icos/PROG/launch RADONGAS -rdf '+fd.strftime("%Y-%m-%d")+","+ed.strftime("%Y-%m-%d")+" 2 --site "+ site+" --type air --samplingHeight "+level+" --flag O,U,R")
            error = ssh_stderr.read()
            meta=(ssh_stdout.read()).decode('utf-8').split('\n')
            meta=[line for line in meta if not line.strip().startswith('WARN') and not line.strip().startswith('#') and line!=' ']    
            with open("Rntemp", 'w') as file_object:
                file_object.write('\n'.join(meta))
            #Reading the error stream of the executed command
            #print("err", error, len(error) )
            ssh.close()
            #Read the temp file and store it as panda dataframe
            RnNRT = pd.read_table("Rntemp", header=None,sep=";", names=['Site','SamplingHeight','Year','Month','Day','Hour','Minute','Second','DecimalDate','LLD','Flag','InsrumentId','QualityId','InternalFlag','AutoDescriptiveFlag','ManualDescriptiveFlag','LLDCorrected','RnCalibrationCorrected'])
            RnNRT['date']=pd.to_datetime(RnNRT.Year.astype(str)+'-'+RnNRT.Month.astype(str)+'-'+RnNRT.Day.astype(str)+' '+RnNRT.Hour.astype(str)+':'+RnNRT.Minute.astype(str))  
            RnEmpty=RnNRT.shape[0]
            Rndata=RnNRT[["date","RnCalibrationCorrected"]].copy()
            Rndata.columns=['date','rn']
            Rndata=Rndata.drop_duplicates()
            
            #crude time correction switch by 30minutes
            Rndata['date_raw']=Rndata['date']
            Rndata['date']=Rndata['date_raw']- pd.DateOffset(minutes=30)
                        
            #print(RnEmpty)
        elif plot_db.value=="CP":
            #CP data 
            #extract all data products for this station as a dictionary. This way it is very simple to use it as a filter for the data objects later on
            dataproducts = tower.products('dict')[0]
            #print(dataproducts)
            dataobjects = tower.data(1)
            dataobjects2 = tower.data(2)
            RnNRT = dataobjects[dataobjects.specLabel == prdict['rn222']]
            mask = (RnNRT.timeStart >= (fd).isoformat()) & (RnNRT.timeEnd < (fd+2*one_day).isoformat())
            RnNRT=RnNRT[mask]
            RnEmpty=RnNRT.shape[0]
        
        #Extract the data we selected
        if RnEmpty<2:
            logging.info("No Rn data")
        else:
            logging.info('go')
            if plot_db.value=="ATC":
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=login.value,password=pawd.value, allow_agent=True)
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('/home/icos/PROG/launch PICARRO -mdf '+fd.strftime("%Y-%m-%d")+","+ed.strftime("%Y-%m-%d")+" -s "+species+" --site "+ site+" --type air --samplingHeight "+level+" --flag O,U,R")
                error = ssh_stderr.read()
                meta=(ssh_stdout.read()).decode('utf-8').split('\n')
                meta=[line for line in meta if not line.strip().startswith('WARN') and not line.strip().startswith('#') and line!='']
                with open("co2temp", 'w') as file_object:
                    file_object.write('\n'.join(meta))
                #Reading the error stream of the executed command
                #print("err", error, len(error) )
                ssh.close()
                #Read the temp file and store it as panda dataframe
                co2NRT = pd.read_table("co2temp", header=None,sep=";",names=['Site','SamplingHeight','Year','Month','Day','Hour','Minute','DecimalDate',species,'Stdev','NbPoints','Flag','InstrumentId','QualityId','InternalFlag','AutoDescriptiveFlag','ManualDescriptiveFlag'])
                co2NRT['Date']=pd.to_datetime(co2NRT.Year.astype(str)+'-'+co2NRT.Month.astype(str)+'-'+co2NRT.Day.astype(str)+' '+co2NRT.Hour.astype(str)+':'+co2NRT.Minute.astype(str))  
               
                #30minute average
                co2data=co2NRT[["Date",species]].copy()
                co2data=co2data.set_index('Date')
                std=co2data.resample('30min').std()
                std.columns=['std']
                co2data=co2data.resample('30min').mean()
                co2data=pd.merge(co2data, std, on='Date',sort=True)
                co2Empty=co2data.shape[0]
            else:
                #CP data
                #check if fd is before or after the release to select the right file, to do so extract growing data
                co2NRT = dataobjects[dataobjects.specLabel == prdict[species]]
                #check if radon at the same height than data
                if (np.unique(co2NRT.samplingheight) == str(np.unique(RnNRT.samplingheight)[0])).any():
                    mask = (co2NRT.samplingheight == str(np.unique(RnNRT.samplingheight)[0]))
                    
                    co2NRT=co2NRT[mask]
                    co2Empty=co2NRT.shape[0]
                
                    rel_date=co2NRT.timeStart
                   
                    relt=rel_date>fd.isoformat()
                
                    if (relt.bool()==True):
                        #get release data 
                        co2NRT = dataobjects2[dataobjects2.specLabel == prdict2[species]]
                    else:
                        co2NRT = dataobjects[dataobjects.specLabel == prdict[species]]
                    mask = (co2NRT.samplingheight == str(np.unique(RnNRT.samplingheight)[0]))
                    co2NRT=co2NRT[mask]
                    co2Empty=co2NRT.shape[0]
                        
                    if co2Empty!= 0:    
                        co2data = Dobj(co2NRT.dobj.iloc[0]).data
                        co2data['date']=co2data.TIMESTAMP
                        mask=(co2data.TIMESTAMP >= pd.to_datetime(fd)) & (co2data.TIMESTAMP < pd.to_datetime(fd+2*one_day))
                        co2data=co2data[mask]
                        co2data['std']=co2data.Stdev
                
                    Rndata = Dobj(RnNRT.dobj.iloc[0]).data
                    Rndata2 = Dobj(RnNRT.dobj.iloc[1]).data
                    Rndata=Rndata.append(Rndata2)
                    Rndata['date']=Rndata.TIMESTAMP
                else:
                    co2Empty=0
                    logging.info("GHG and Rn not at the same sampling height")
           
                if co2Empty== 0:
                    logging.info("No GHG data")
                else:
                    #add error on the measure at 5% (from Chambers, 2015, 3.5% at 1Bq, 17% at 100mB)
                    Rndata['std']=Rndata.rn*5/100
                    #Run 
                    #calculate the correlation between GHG and rn for the chosen window 21:00 UTC to avoid traffic and be at night and 6UTC before traffic
                    #first check that the Rn increase over the window is >1Bq.m-2
                    fh=time_choice1.value
                    th=time_choice2.value
                   # print(fh)
                   # print(th)
                    begin=datetime.combine(fd, DT.time(fh, 0))
                    end=datetime.combine(fd+one_day, DT.time(th, 0))
                    rn_night=Rndata[(Rndata.date>= begin) & (Rndata.date<=end)]
                   # print(rn_night)
                   # print(co2data)
                   # print(co2data.index)
                    if plot_db.value=="ATC":
                        co2data['date']=co2data.index
                    #print(rn_night)
                    if (rn_night.shape[0]> 0):
                        rise=max(rn_night.rn)-min(rn_night.rn)   
                        #then calculate if Rn increase stops before 08:00 UTC, must be >0
                        end=datetime.combine(fd+one_day, DT.time(th+3, 0))
                        rn_long=Rndata[(Rndata.date>= begin) & (Rndata.date<=end)]
                        risestop=max(rn_long.rn)-rn_long.rn.iloc[-1]
                      
                        # check if at least 2hours available when resizing the window to the max(Rn) and do the correl on that window
                           
                        rn_night=rn_night.dropna()
                        isempty=rn_night.empty
                        if isempty==False: 
                            nb_hrs=rn_night.date[rn_night.rn==max(rn_night.rn)]-rn_night.date.iloc[0]  
                       
                            if (nb_hrs>=pd.to_timedelta(2,unit='h')).all():
                                nb_hrs=nb_hrs.iloc[0]
                                nb_hrs=nb_hrs.seconds/3600
                                rn_sel=rn_night[rn_night.date<=(rn_night.date[rn_night.rn==max(rn_night.rn)]).values[0]]               
                                ghg_sel=co2data[(co2data.date>=begin) & (co2data.date<=(rn_night.date[rn_night.rn==max(rn_night.rn)]).values[0])]
            
                                #remove NA data if any (like when measuring different samples and 30 minutes missing)
                                ghg_sel=ghg_sel.dropna()             
                                rn_sel=rn_sel.dropna()
                
                                #merge by date to have the same length vector
                                msel=pd.merge(rn_sel, ghg_sel, on='date',sort=True)          
                                # print(msel)
                                #check if data are available over our window and do the linear regression
                                nb_pt=msel.shape[0]
                            
                                if nb_pt>1:
                                    #Function to fit (linear)
                                    def f(B, x):
                                        return B[0]*x + B[1]
                                    linear = Model(f)
                                    #create data array to be fitted
                                    sx=msel.std_x
                                    sy=msel.std_y
                                    mydata = RealData(msel.rn, msel[species], sy=sy, sx=sx)
                                    odr = ODR(mydata, linear, beta0=[15., 393.])
                                    out=odr.run()
                                    #out.pprint()
                                    x_fit = msel.rn
                                    y_fit = out.beta[0]*msel.rn+out.beta[1]
                                    r2=r2_score(msel[species], y_fit)
                                    err=out.sd_beta[0]/out.beta[0]*100
                                                                
                                    #now we can calculate the emission rate: 
                                    #Jghg=Jrn*slope(ghg/rn)*(1-lrnCrn/DCrn/Dt) <- this term is the radioactive decay estimate at 3to 4%M over night so 0.965.
                                    #Jrn can be calculated in different ways: average value from previous studies or from daily/hourly maps
                                    nw=1000
                                    if fmap_choice.value=='InGOS_Radon_fluxmap_v2.0_climatology.nc':
                                        nw=1
                                    Jghg1=Jrn1*1000*out.beta[0]*0.965*Mm*Pp/Vm #unit: ppm or ppb/m2/h * molar mass/molar volume to get it in mg/h/m2
                                    Jghg2=Jrn2*3600*nw*out.beta[0]*0.965*Mm*Pp/Vm #3600 as mBq/m2/s to convert in mBq/m2/h
                                    Jghg3=Jrn3*3600*nw*out.beta[0]*0.965*Mm*Pp/Vm
                                    Jghg4=Jrn4*3600*nw*out.beta[0]*0.965*Mm*Pp/Vm
                                    # Fl=[fd,'{:10.6f}'.format(Jghg1), '{:10.6f}'.format(Jghg2),'{:10.6f}'.format(Jghg3),'{:10.6f}'.format(Jghg4),'{:10.6f}'.format(r2),'{:10.6f}'.format(err),nb_pt,nb_hrs,'{:6.3f}'.format(risestop),'{:6.3f}'.format(rise), Jrn1,'{:7.3f}'.format(Jrn2*3.6*nw),'{:7.3f}'.format(Jrn3*3.6*nw),'{:7.3f}'.format(Jrn4*3.6*nw)]
                                    logging.info("Flux calculated!")
                                    print("Flux calculated!")
                                    Fl=[fd,'{:10.6f}'.format(Jghg1),'{:10.6f}'.format(r2),'{:10.6f}'.format(err),nb_pt,nb_hrs,'{:6.3f}'.format(risestop),'{:6.3f}'.format(rise), Jrn1, 'UserValue']
                                                            
                                    Flux=Flux.append(pd.DataFrame([Fl]),ignore_index=True)
                                    Fl=[fd,'{:10.6f}'.format(Jghg2),'{:10.6f}'.format(r2),'{:10.6f}'.format(err),nb_pt,nb_hrs,'{:6.3f}'.format(risestop),'{:6.3f}'.format(rise),'{:7.3f}'.format(Jrn2*3.6*nw),'StationPixel']
                                                            
                                    Flux=Flux.append(pd.DataFrame([Fl]),ignore_index=True)
                                    Fl=[fd,'{:10.6f}'.format(Jghg3),'{:10.6f}'.format(r2),'{:10.6f}'.format(err),nb_pt,nb_hrs,'{:6.3f}'.format(risestop),'{:6.3f}'.format(rise), '{:7.3f}'.format(Jrn3*3.6*nw),'2019Aggreg']
                                                            
                                    Flux=Flux.append(pd.DataFrame([Fl]),ignore_index=True)
                                    Fl=[fd,'{:10.6f}'.format(Jghg4),'{:10.6f}'.format(r2),'{:10.6f}'.format(err),nb_pt,nb_hrs,'{:6.3f}'.format(risestop),'{:6.3f}'.format(rise), '{:7.3f}'.format(Jrn4*3.6*nw),'DayFootprint']
                                                            
                                    Flux=Flux.append(pd.DataFrame([Fl]),ignore_index=True)
                                else:
                                    logging.info("No valid data over the window")
                            else:
                                logging.info("Less than 2hours of Rn data from the beginning of the window to the Rn max")
        updateProgress(g)
    Flux.to_csv(fileout, sep='\t', mode='w',index=False, header=False)
    if os.path.exists('co2temp'):
        os.remove('co2temp')
    if os.path.exists('Rntemp'):
        os.remove('Rntemp')
        
    if plot_type.value=="Yes":
        #Choose the flux file we want (only one at a time)
        fc = FileChooser("outputData")
        fc.title = '<b>Select a file to plot from</b>'
        with fcc:
            display(fc)
     #go button
        plot_button = Button(description='Plot',
                           disabled=False,
                           button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
        def plot_func(button_c):
            plot_flux(fc,site,species,sitelevel,stations)
        plot_button.on_click(plot_func)
        with plbut:
            display(plot_button)   
    
#----------------------------------------------------------------------------------------------------------------
def plot_flux(fc,site,species,sitelevel,stations):
    half_day= DT.timedelta(days=0.5)
    #Read the selected file and plot the flux vs time
    Flux = pd.read_table(fc.selected, header=None, names=['Date',"Jghg","R2","Error","Nb_pts","Nb_hrs","Rise_stop","Rn_amplitude","JRn","Type"])
    Flux.replace(0, np.nan, inplace=True)  
    Flux['Date'] =pd.to_datetime(Flux.Date)
    Flux=Flux[Flux.Type=='DayFootprint']
    if len(Flux.Date)>0:
        with progress_bar2:
            g = IntProgress(min=0, max=len(Flux.Date), style=style)
            display(g)
        #plot
        #Plot the GHG footprint when a footprint is available
        #loop on the dates in the file
        
        with PdfPages('Plots/Footprint_'+species+'_'+site+'_'+str(Flux.Date.iloc[0])+'-'+str(Flux.Date.iloc[-1]) +'.pdf') as pdf:
           
            for pl in range(len(Flux.Date)):
                
                #plot when Jghg4 is different than NA
                if np.isnan(Flux.Jghg.iloc[pl])==False:
                
                    fd=Flux.Date.iloc[pl]
                    date_range = pd.date_range(fd+half_day,fd+3*half_day, freq='3H')
                    date_range = date_range[((21 <= date_range.hour) & (date_range.hour <= 24)) | ((0<=date_range.hour) & (date_range.hour<=4))]
                    timeselect="nighttime"
                    nfp, fp, lon, lat,title, found= read_aggreg_footprints(stations, sitelevel, date_range, timeselect=timeselect)
                    #normalize
                    fpw=fp[:,:]/np.sum(fp)
                    #distribute the GHG flux on the footprint
                    ghg_fp=Flux.Jghg.iloc[pl]*fpw
                    title='Jghg day footprint '+str(Flux.Date.iloc[pl])
                
                    plot_maps(pdf,ghg_fp, lon, lat, title=title, label='Jghg Footprint', unit='[ppm / ($\mu$mol / m$^{2}$s)]', 
                    linlog='log10', vmin=-6, vmax=-2, station=[sitelevel], stations=stations, zoom=sitelevel)
                updateProgress(g)
    else:      
        txt=Text(value="No Flux calculated for this period",
            placeholder='Info',description='Info:',
            disabled=False)
        with pltxt:
            display(txt)
       
        
    
#-------------------------------------------------------------------------------------------------------------------------    
#function to read and aggregate footprints for given time range
def read_aggreg_footprints(stations, station, date_range, timeselect='all'):
    
    # loop over all dates and read netcdf files

    # path to footprint files in new stiltweb directory structure
    
    pathFP=path_stiltweb

    # print ('date range: ',date_range)
    fp=[]
    nfp=0
    first = True
    for dd in date_range:
        filename=(pathFP+'slots/'+stations[station]['locIdent']+'/'+str(dd.year)+'/'+str(dd.month).zfill(2)+'/'
                  +str(dd.year)+'x'+str(dd.month).zfill(2)+'x'+str(dd.day).zfill(2)+'x'+str(dd.hour).zfill(2)+'/foot')
        #print (filename)
        if os.path.isfile(filename):
            f_fp = cdf.Dataset(filename)
            if (first):
                fp=f_fp.variables['foot'][:,:,:]
                lon=f_fp.variables['lon'][:]
                lat=f_fp.variables['lat'][:]
                first = False
            else:
                fp=fp+f_fp.variables['foot'][:,:,:]
            f_fp.close()
            nfp+=1
        else:
            logging.info('file does not exist: '+filename)
    if nfp > 0:
        fp=fp/nfp
        #print (np.shape(fp))
        #print (np.max(fp))
        title = (date_range[0].strftime('%Y-%m-%d')+' - '+date_range[len(date_range)-1].strftime('%Y-%m-%d')+'\n'+
             'time selection: '+timeselect)
        found='yes'
        return nfp, fp, lon, lat, title, found
    else:
        logging.info('no footprints found')
        found='no'
        return found

    

#-----------------------------------------------------------------------------------------------------------
def create_STILT_dictionary():
    # store all STILT station information in a dictionary 
    #
    # Dictionary contains information on
    #    STILT station id
    #    Station coordinates (latitude, longitude)
    #    Altitude of tracer release in STILT simultation
    #    STILT location identifier
    #    Station name - if available 
    #
    # get all ICOS station IDs by listing subdirectories in stiltweb
    # extract location from filename of link

    path_stations = path_stiltweb+'/stations/'
    all_stations = os.listdir(path_stations)

    # empty dictionary
    stations = {}

    # fill dictionary with ICOS station id, latitude, longitude and altitude
    for ist in sorted(list(set(all_stations))):
        stations[ist] = {}
        # get filename of link (original stiltweb directory structure) 
        # and extract location information
        if os.path.exists(path_stations+ist):
            loc_ident = os.readlink(path_stations+ist)
            clon = loc_ident[-13:-6]
            lon = np.float(clon[:-1])
            if clon[-1:] == 'W':
                lon = -lon
            clat = loc_ident[-20:-14]
            lat = np.float(clat[:-1])
            if clat[-1:] == 'S':
                lat = -lat
            alt = np.int(loc_ident[-5:])

            stations[ist]['lat']=lat
            stations[ist]['lon']=lon
            stations[ist]['alt']=alt
            stations[ist]['locIdent']=os.path.split(loc_ident)[-1]

        
    # add information on station name (and new STILT station id) from stations.csv file used in stiltweb 

    url="https://stilt.icos-cp.eu/viewer/stationinfo"
    df = pd.read_csv(url)

    for ist in sorted(list(set(stations))):
        stationName = df.loc[df['STILT id'] == ist]['STILT name']
        if len(stationName.value_counts()) > 0:
            stations[ist]['name'] = stationName.item()
        else:
            stations[ist]['name'] = ''

    # Get list of ICOS class 1 and class 2 stations from Carbon Portal
    #query = sparqls.get_station_class()
    query = get_station_class()
    fmt = 'pandas'
    df_datatable = RunSparql(query, fmt).run()

    # add information if ICOS class 1 or class 2 site
    # add ICOS station name
    for ist in sorted(list(set(stations))):
        stations[ist]['stationClass'] = np.nan
        stations[ist]['icosName'] = ''
        stations[ist]['icosId'] = ''
        stations[ist]['icosLon'] = np.nan
        stations[ist]['icosLat'] = np.nan       
        for istICOS in df_datatable['stationId']:
            ic = int(df_datatable[df_datatable['stationId']==istICOS].index.values)
            if istICOS in ist:
                stations[ist]['stationClass'] = int(df_datatable['stationClass'][ic])
                stations[ist]['icosName'] = df_datatable['longName'][ic]
                stations[ist]['icosId'] = df_datatable['stationId'][ic]
                stations[ist]['icosLon'] = float(df_datatable['lon'][ic])
                stations[ist]['icosLat'] = float(df_datatable['lat'][ic])
                

    # add available sampling heights
    # find all co2 data files for station
    query = get_icos_stations_atc_samplingheight()
    fmt = 'pandas'
    df_datatable_hgt = RunSparql(query, fmt).run()
    for ist in sorted(list(set(stations))):
        stations[ist]['icosHeight'] = np.nan
        if (len(stations[ist]['icosName']) > 0):
            heights = df_datatable_hgt[df_datatable_hgt['stationId']==ist[0:3]]['height'].unique()
            ih = np.nan
            if (len(heights) > 0):
                if (len(ist[3:])==0):
                    ih = int(float(heights[0]))
                else:
                    # special case Jungfraujoch STILT runs for 960m
                    if ist[0:3]=='JFJ':
                        ih = int(float(heights[0]))
                    else:
                        if ist[3:]=='_test':
                            ih=0
                        else:
                            ih = [int(float(el)) for el in heights if (abs(int(float(el))-int(ist[3:]))<6)]
            if isinstance(ih, list):
                if (len(ih) == 0):
                    stations[ist]['icosHeight'] = np.nan
                else:
                    stations[ist]['icosHeight'] = ih[0]
            else:
                stations[ist]['icosHeight'] = ih

    # print dictionary
    #for ist in sorted(stations):
    #    print ('station:', ist)
    #    for k in stations[ist]:
    #        print (k,':', stations[ist][k])

    # write dictionary to json file for further use
    if os.access('./', os.W_OK):
        with open("stationsDict", "w") as outfile:
            json.dump(stations, outfile)
    
    return stations
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
                            1. Station ID (var_name: 'stationId', var_type: String)
                            2. URL to ICOS RI Data Object Landing Page (var_name: 'dobj', var_type: String)
                            3. Filename for Data Object (var_name: 'filename', var_type: String)
                            4. Station name (var_name: 'stationName', var_type: String)
                            5. Sampling height a.g.l. (var_name: 'height', var_type: String)
                            6. Sampling Start Time (var_name: 'timeStart', var_type: String)
                            7. Sampling End Time (var_naem: 'timeEnd', var_type: String)
    """
    
    query = """
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>

        select ?stationId ?dobj ?fileName ?stationName ?height ?timeStart ?timeEnd 
        where {
            VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/atcCo2L2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCo2NrtGrowingDataObject>}
            ?station cpmeta:hasStationId ?stationId;cpmeta:hasName ?stationName .
            ?dobj cpmeta:hasObjectSpec ?spec .
            ?dobj cpmeta:hasName ?fileName .
            ?dobj cpmeta:wasAcquiredBy [
                prov:startedAtTime ?timeStart ;
                prov:endedAtTime ?timeEnd ;
                prov:wasAssociatedWith ?station ;
                cpmeta:hasSamplingHeight ?height
                ]
            FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
        }
        order by ?stationId
    """
    return query
#------------------------------------------------------------------------------

# function to plot maps (show station location if station is provided and zoom in second plot if zoom is provided)
def plot_maps(pdf,field, lon, lat, title='', label='', unit='', linlog='linear', station=[''], stations=None, zoom='', 
              vmin=None, vmax=None, colors='GnBu',pngfile=''):
    """Plot maps (emissions or footprints)
    show station location if station is provided and zoom in second plot if zoom is provided
    """    
    # Check if dictionary with all STILT stations is provided in case station location or zoom options are chosen
    if ((station[0] != '') or (zoom != '')):
        if stations is None:
            print('Please provide dictionary with all STILT stations in "stations = ..."') 
            station[0] = ''
            zoom = ''
            
    mcolor='m'
    
    # Set scale for features from Natural Earth
    #NEscale = '110m'
    NEscale = '50m'
    #NEscale = '10m'
    
    # Create a feature for Countries at 1:50m from Natural Earth
    countries = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_countries',
        scale=NEscale,
        facecolor='none')
    
    #Create a feature for Lakes at 1.50m from Natural Earth:
    lakes = cfeature.NaturalEarthFeature(
        category='physical',
        name='lakes',
        scale=NEscale,
        facecolor='none')    
 
    #print (np.shape(field))
    
    if np.shape(field)[0] > 1:
        print ('More than one field: ',np.shape(field)[0],' Only the first will be plotted!!!')
        
    fig = p.figure(figsize=(15,15))

    # set up a map
    ax = p.subplot(1, 2, 1, projection=ccrs.PlateCarree())
    img_extent = (lon.min(), lon.max(), lat.min(), lat.max())
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],crs=ccrs.PlateCarree())
    ax.add_feature(countries, edgecolor='black', linewidth=0.3)
    ax.add_feature(lakes, edgecolor='black', linewidth=0.3)

    # add gridlines:
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=0.3, color='black')

    # set gridline-parameters (spatial extent (min/max values of lat/lon) and interval(here=10))
    gl.ylocator = mticker.FixedLocator(np.arange(-90.,90.,10.))
    gl.xlocator = mticker.FixedLocator(np.arange(-180.,180.,10.))
   
    cmap = p.get_cmap(colors)
    if linlog == 'linear':
        im = ax.imshow(field[0,:,:],interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        cbar.set_label(label+'  '+unit)
    else:
        im = ax.imshow(np.log10(field)[0,:,:],interpolation='none',origin='lower',
                       extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        cbar.set_label(label+'  log$_{10}$ '+unit)
    p.title(title)
    ax.text(0.01, -0.3, 'min: %.5f' % np.min(field[0,:,:]), horizontalalignment='left',transform=ax.transAxes)
    ax.text(0.99, -0.3, 'max: %.5f' % np.max(field[0,:,:]), horizontalalignment='right',transform=ax.transAxes)
    
    #show station location if station is provided
    if station[0] != '':
        station_lon=[]
        station_lat=[]
        for ist in station:
            station_lon.append(stations[ist]['lon'])
            station_lat.append(stations[ist]['lat'])
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
    #zoom   
    if zoom != '':
        #grid cell index of station 
        ix,jy = lonlat_2_ixjy(stations[zoom]['lon'],stations[zoom]['lat'],lon,lat)
        #print (stations[zoom]['lon'],stations[zoom]['lat'],ix,jy)

        # define zoom area 
        i1 = np.max([ix-35,0])
        i2 = np.min([ix+35,400])
        j1 = np.max([jy-42,0])
        j2 = np.min([jy+42,480])

        lon_z=lon[i1:i2]
        lat_z=lat[j1:j2]
        field_z=field[0,j1:j2,i1:i2]

        #print (i1,i2,j1,j2)

        # set up a map
        ax = p.subplot(1, 2, 2, projection=ccrs.PlateCarree())
        img_extent = (lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max())
        ax.set_extent([lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()],crs=ccrs.PlateCarree())
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)
        ax.add_feature(lakes, edgecolor='black', linewidth=0.3)

        # add gridlines:
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=0.3, color='black')

        # set gridline-parameters (spatial extent (min/max values of lat/lon) and interval(here=10))
        gl.ylocator = mticker.FixedLocator(np.arange(-90.,90.,10.))
        gl.xlocator = mticker.FixedLocator(np.arange(-180.,180.,10.))
    
        if linlog == 'linear':
            im = ax.imshow(field_z,interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
            #im = m.imshow(field[0,j1:j2,i1:i2],interpolation='none',origin='lower',vmin=vmin,vmax=vmax,cmap=cmap)
            #cbar=m.colorbar(im,location='bottom',pad='5%')
            cbar.set_label(label+'  '+unit)
        else:
            im = ax.imshow(np.log10(field_z),interpolation='none',origin='lower', extent=img_extent,cmap=cmap,vmin=vmin,vmax=vmax)
            cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
            #im = m.imshow(np.log10(field)[0,j1:j2,i1:i2],interpolation='none',origin='lower',vmin=vmin,vmax=vmax,cmap=cmap)
            #cbar=m.colorbar(im,location='bottom',pad='5%')
            cbar.set_label(label+'  log$_{10}$ '+unit)

        #show station location if station is provided
        if station[0] != '':
            station_lon=[]
            station_lat=[]
            for ist in list(set([zoom] + station)):
                station_lon.append(stations[ist]['lon'])
                station_lat.append(stations[ist]['lat'])
            ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=1,transform=ccrs.PlateCarree())
        p.title(title)
        ax.text(0.01, -0.3, 'min: %.5f' % np.min(field[0,j1:j2,i1:i2]), horizontalalignment='left',transform=ax.transAxes)
        ax.text(0.99, -0.3, 'max: %.5f' % np.max(field[0,j1:j2,i1:i2]), horizontalalignment='right',transform=ax.transAxes)
    #p.tight_layout()
    p.show()
    pdf.savefig(fig)  # saves the current figure into a pdf page
                
    if len(pngfile)>0:
        plotdir='plots'
        if not os.path.exists(plotdir):
            os.mkdir(plotdir)
        fig.savefig(plotdir+'/'+pngfile+'.png',dpi=100)
    p.close()
#------------------------------------------------------------------------------------------------------------------------
    # function to convert station longitude and latitude (slat, slon) to indices of STILT model grid (ix,jy)

def lonlat_2_ixjy(slon,slat,mlon,mlat):
    #slon, slat: longitude and latitude of station
    #mlon, mlat: 1-dim. longitude and latitude of model grid
    ix = (np.abs(mlon-slon)).argmin()
    jy = (np.abs(mlat-slat)).argmin()
    return ix,jy

#--------------------------------------------------------------------------------------------------------------------------------
def update_func(button_c):
    #print('choose_RTM')
    style = {'description_width': 'initial'}
    if plot_db.value=='ATC' or plot_db.value=='Deconv' :
       # form_out2 = Output(layout={'border': '1px solid black'})
        #get login and password
        login=Text(
            value=None,
            description='Enter your login to the icos server:',
            disabled=False,
            style=style)
        #log=Output()
        with log:
            display(login)
        
        pawd=Password(placeholder='Enter password', description= 'Password:',disabled=False)
        #passe=Output()
        with passe:
            display(pawd)
        #go button
        enter_button = Button(description='Enter',
                           disabled=False,
                           button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
        def update_func(button_c):
            RTM_go(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice, login, pawd, plot_type,stations)
        enter_button.on_click(update_func)
    
        #enbut=Output()
        with enbut:
            display(enter_button)
        
        
    else:
        #Run the CP TRM
        login='login'
        pawd='pawd'
        RTM_go(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice,login, pawd, plot_type,stations)
#-----------------------------------------------------------------------------------------------------------------------------------
#Widgets menu
stations = create_STILT_dictionary()
stations_icos={key:value for key,value in stations.items() if value['icosId']!=''}
style = {'description_width': 'initial'}
    
station_choice = Dropdown(layout={'width': 'max-content'},options = list(stations_icos),
                       description = 'Station',
                       value=None,disabled= False,)
stat = Output()
with stat:
    display(station_choice)

fdate_choice= DatePicker(
        description='Pick a beginning Date',
        disabled=False, style=style  )
fdat = Output()
with fdat:
    display(fdate_choice)
        
edate_choice= DatePicker(
        description='Pick an end Date',
        disabled=False, style=style  )
edat = Output()
with edat:
    display(edate_choice)

time_choice1=Dropdown(style={'description_width': 'initial'},layout={'width': 'max-content'},options = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                       description = 'First hour of the RTM window (UTC)',
                       value=21,disabled= False,)
tch1 = Output()
with tch1:
    display(time_choice1)
    
time_choice2=Dropdown(style={'description_width': 'initial'},layout={'width': 'max-content'},options = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                       description = 'Last hour of the RTM window (UTC)',
                       value=5,disabled= False,)
tch2 = Output()
with tch2:
    display(time_choice2)
    
my_maps = get_radon_maps(outfmt='dict')
my_maps_arr=pd.DataFrame(np.array(list(my_maps.items())))
my_maps_list=np.array(my_maps_arr[0])   
fmap_choice = Dropdown(style={'description_width': 'initial'},layout={'width': 'max-content'},options = my_maps_list,
                       description = 'Flux map (check the year)',
                       value=my_maps_list[0],disabled= False,)
fmch = Output()
with fmch:
    display(fmap_choice)
    
#Enter manually the Rn flux from litterature or measurements in fields
flux_choice=IntText(
        value=None,
        description='Rn flux from litterature (Bq/m2/h):',
        disabled=False, style=style     )
flch = Output()
with flch:
    display(flux_choice)

#choose the species
species_choice=Dropdown(style={'description_width': 'initial'},layout={'width': 'max-content'},options=["co2","ch4","co","n2o"],
        value="co2",
        description='Species:',
        disabled=False )
spch = Output()
with spch:
    display(species_choice)
    
plot_type=RadioButtons(
            options=['Yes', 'No'],
            value='Yes',
            description='Do you want to plot the data? ', style=style,
            disabled=False)
plty = Output()
with plty:
    display(plot_type)
    
#choose between CP or ATC data
plot_db=RadioButtons(
            options=['CP', 'CP'],
            value='CP',
            description='Which database do you want to use? ', style=style,
            disabled=False)
pldb = Output()
with pldb:
    display(plot_db)
    
#go button
go_button = Button(description='Run the RTM',
                           disabled=False,
                           button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
        
        
#choose_RTM(plot_db,station_choice, flux_choice, species_choice, fdate_choice, edate_choice, plot_type,stations)
go_button.on_click(update_func)
button = Output()
with button:    
    display(go_button)
form_out = Output()

    
    #return station_choice, flux_choice, species_choice, fdate_choice, edate_choice, plot_db, plot_type,stations

#Initialize output
log=Output()
passe=Output()
enbut=Output()
progress_bar=Output()
progress_bar2=Output()
fcc=Output()
plbut=Output()
pltxt=Output()
#Open form object:
with form_out:
    display(stat,fdat,tch1,edat,tch2,fmch,flch,spch,plty,pldb,button,log,passe,enbut,progress_bar,fcc,plbut,progress_bar2,pltxt)
    
display(form_out)
