#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import netCDF4 as cdf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as p
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from cartopy import config
import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, LAKES
import cartopy.feature as cfeature
import json 
import requests
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')
from dateutil.rrule import rrule, MONTHLY
from IPython.core.display import display, HTML 
from ipywidgets import interact, interact_manual, Dropdown, SelectMultiple, HBox, VBox, Button, Output, FloatText, IntText, IntRangeSlider
from IPython.display import clear_output
#display(HTML("<style>.container { width:100% !important; }</style>"))


#Set path to ICOS tools:
sys.path.insert(0,'/data/project/pytools')
#Import ICOS tools:
from icoscp.sparql import sparqls
from icoscp.sparql.runsparql import RunSparql

# get path to user home directory
my_home = os.getenv('HOME')
sys.path.insert(1,'modules')
from extra_sparqls import atc_station_tracer_query

from STILT_modules_plus import create_STILT_dictionary, print_STILT_dictionary 
from STILT_modules_plus import lonlat_2_ixjy, read_emissions
from STILT_modules_plus import read_stilt_timeseries_RINGO_T13
from STILT_modules_plus import read_icos_data

# paths --- changed for new JupyterHub instance
# path to footprint tool results (3-hrl footprints)
path_stiltweb = '/data/stiltweb/'
# path to RINGO specific STILT results (1-hourly footprints and concentrations for selected stations)
path_stilt = '/data/stilt/'
# path to constant EDGAR emissions for 2010 (for testing purposes only)
path_edgar = '/data/stilt/Emissions/'

# create directory for storing plots - if not already exists
path_plots = 'Figures/'
if os.access('./', os.W_OK):
    if not os.path.exists(path_plots):
        os.makedirs(path_plots)
else:
    os.makedirs(HOME+path_plots, exist_ok=True)
    path_plots = HOME+path_plots
#------------------------------------------------------------------------------------------------------------------

# define colors
orange='#ff8c00'
lime='#00ff00'
aqua='#00ffff'
brown='#663300'
lightgray="#C0C0C0"
gray="#808080"
cb_lightgreen='#b2df8a'
cb_green='#33a02c'
cb_lightblue='#a6cee3'
cb_blue='#1f78b4'
royal='#4169E1'

p.rcParams.update({'xtick.labelsize': 14})
p.rcParams.update({'ytick.labelsize': 14})
p.rcParams.update({'axes.labelsize': 14})
p.rcParams.update({'legend.fontsize': 14})
p.rcParams.update({'axes.titlesize': 18})

#------------------------------------------------------------------------------------------------------------------
# plot STILT footprints for selected station and time range
def plot_footprints(station, station_lat, station_lon, loc_ident, daterange, 
                    fxe_vmax=2.0, ident='', secsplit=False, pngfile=''):

    #path to RINGO specific 1-hourly STILT footprints
    path_fp=path_stilt+'/Footprints/'
    #path to STILT footprints from the Footprint Tool (3-hourly only)
    path_fp_3=path_stiltweb+'/slots/'

    # loop over all dates and read netcdf files
    # latitude, longitude are for grid center
    fp=[]
    nfp=0
    first = True
    for dd in daterange:
        date_ident=str(dd.year)+'x'+str(dd.month).rjust(2, '0')+'x'+str(dd.day).rjust(2, '0')+'x'+str(dd.hour).rjust(2, '0')
        filename=station+'/foot'+date_ident+'x'+loc_ident+'_aggreg.nc'
        filename_3=loc_ident+'/'+str(dd.year)+'/'+str(dd.month).rjust(2, '0')+'/'+date_ident+'/foot'
        #print(filename)
        #print(filename_3)
        read = False
        if os.path.isfile(path_fp+filename):
            f_fp = cdf.Dataset(path_fp+filename)
            read = True
        elif os.path.isfile(path_fp_3+filename_3):
            f_fp = cdf.Dataset(path_fp_3+filename_3)
            read = True
        if (read):
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
            print('files do not exist: ',path_fp+filename,' ',path_fp_3+filename_3)
            
    if nfp > 0:
        mfp=fp/nfp
        print(str(nfp)+' footprints found'+'   '+ident)
    else:
        print('no footprints found'+'   '+ident)
        return
        
        

    # plot aggregated footprint

    # select colormap
    #cmap = p.get_cmap('YlOrRd')
    #cmap = p.get_cmap('inferno_r')
    #cmap = p.get_cmap('bone_r')
    cmap = p.get_cmap('GnBu')
    #cmap = p.get_cmap('gist_heat_r')
    
    # select marker color
    #mcolor = 'b'
    mcolor = 'r'
    
    # select value range for logarithmic footprints  
    vmin=-7
    vmax=-1
    
    #grid cell index of station 
    ix,jy = lonlat_2_ixjy(station_lon,station_lat,lon,lat)
    #print(station,station_lon,station_lat,ix,jy)

    # define zoom area around station grid cell
    i1 = np.max([ix-65,0])
    i2 = np.min([ix+45,400])
    j1 = np.max([jy-70,0])
    j2 = np.min([jy+70,480])


    lon_z=lon[i1:i2]
    lat_z=lat[j1:j2]
    fp_z=fp[0,j1:j2,i1:i2]

    fig = p.figure(figsize=(17,17))
    
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

    # total annual emissions original EDGAR 4.3 for base year 2010
    path_edgar=path_stilt+'/Emissions/'
    filename='EDGARv4.3_2010_total.nc'
    emis, lon, lat, dd, unit = read_emissions(path_edgar+filename)

    # footprint * emission 
    fp_emis=fp*emis
    fp_emis[fp<=0.0]=np.nan
    
    fp_emis_z=fp_emis[0,j1:j2,i1:i2]
        
    if not secsplit:
        # set up a map
        ax = p.subplot(1, 2, 1, projection=ccrs.PlateCarree())
        img_extent = [lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()]
        ax.set_extent(img_extent,crs=ccrs.PlateCarree())
        #Add Natural Earth countries:
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)
        #Add Natural Earth lakes:
        ax.add_feature(lakes, edgecolor='black', linewidth=0.3)

        #Add raster with values:
        im = ax.imshow(np.log10(fp_z),interpolation='none',origin='lower', extent=img_extent,
                       cmap=cmap,vmin=vmin,vmax=vmax)
        #Add colorbar:
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='both')
        cbar.set_label('surface influence log$_{10}$ [ppm / ($\mu$mol / m$^{2}$s)]')

        #Add plot title:
        p.title('{} aggregated footprints '.format(nfp)+'\n'+'station: '+station+'     '+
                np.min(daterange).strftime('%Y-%m-%d')
                +' -- '+np.max(daterange).strftime('%Y-%m-%d')+'\n'+ident)
        #Add explanatory text under the colorbar (raster dataset min value):
        ax.text(0.01, -0.29, 'min: %.5e' % np.nanmin(fp_z), 
                horizontalalignment='left',transform=ax.transAxes)
        #Add explanatory text under the colorbar (raster dataset max value):
        ax.text(0.99, -0.29, 'max: %.5e' % np.nanmax(fp_z), 
                horizontalalignment='right',transform=ax.transAxes)
 
        # station location
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=2,transform=ccrs.PlateCarree())

        # set up second map
        ax = p.subplot(1, 2, 2, projection=ccrs.PlateCarree())
        img_extent = [lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()]
        ax.set_extent(img_extent,crs=ccrs.PlateCarree())
        #Add Natural Earth countries:
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)
        #Add Natural Earth lakes:
        ax.add_feature(lakes, edgecolor='black', linewidth=0.3)

        #Add raster with values:
        im = ax.imshow((fp_emis_z)[:,:],interpolation='none',origin='lower',extent=img_extent,
                       vmin=0,vmax=fxe_vmax,cmap=cmap)
        #Add colorbar:
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='max')
        cbar.set_label('surface influence [ppm]')
        #Add plot title:
        p.title('Footprints x Emissions '+'\n'+'station: '+station+'     '+np.min(daterange).strftime('%Y-%m-%d')
                +' -- '+np.max(daterange).strftime('%Y-%m-%d')+'\n'+ident)
        #Add explanatory text under the colorbar (raster dataset min value):
        ax.text(0.01, -0.29, 'min: %.5e' % np.nanmin(fp_emis_z), horizontalalignment='left',transform=ax.transAxes)
        #Add explanatory text under the colorbar (raster dataset max value):
        ax.text(0.99, -0.29, 'max: %.5e' % np.nanmax(fp_emis_z), horizontalalignment='right',transform=ax.transAxes)

        #station location
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=2,transform=ccrs.PlateCarree())
    

    else: #if secsplit:

        total_contribution = np.nansum(fp_emis_z)
        print('total_contribution ',total_contribution)

        print('energy/non-energy split with big cities marked')
        # emissions from enery production only, original EDGAR 4.3 for base year 2010
        path_edgar=path_stilt+'/Emissions/'
        filename='EDGARv4.3_2010_ENE.nc'
    
        emis2, lon, lat, dd, unit = read_emissions(path_edgar+filename)

        # footprint * emission 
        fp_emis2=fp*emis2
        fp_emis2[fp<=0.0]=np.nan
    
        fp_emis2_z=fp_emis2[0,j1:j2,i1:i2]

        ENE_contribution = np.nansum(fp_emis2_z)
        ENE_ratio = 100.*ENE_contribution/total_contribution
        print('ENE_contribution', '%.1f' % ENE_ratio,'%')

        # set up a map
        ax = p.subplot(1, 2, 1, projection=ccrs.PlateCarree())
        img_extent = [lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()]
        ax.set_extent(img_extent,crs=ccrs.PlateCarree())
        #Add Natural Earth countries:
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)
        #Add Natural Earth lakes:
        ax.add_feature(lakes, edgecolor='black', linewidth=0.3)

        #Add raster with values:
        im = ax.imshow((fp_emis2_z)[:,:],interpolation='none',origin='lower',extent=img_extent,
                       vmin=0,vmax=fxe_vmax,cmap=cmap)
        #Add colorbar:
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='max')
        cbar.set_label('surface influence [ppm]')
        #Add plot title:
        p.title('avarage footprints x energy emissions '+'%.1f' % ENE_ratio
                +' %'+'\n'+'station: '+station+'     '
                +np.min(daterange).strftime('%Y-%m-%d')+' -- '+np.max(daterange).strftime('%Y-%m-%d')
                +'\n'+ident)
        ax.text(0.01, -0.29, 'min: %.5f' % np.nanmin(fp_emis2_z), horizontalalignment='left',transform=ax.transAxes)
        ax.text(0.99, -0.29, 'max: %.5f' % np.nanmax(fp_emis2_z), horizontalalignment='right',transform=ax.transAxes)

        #station location
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=2,transform=ccrs.PlateCarree())
    
        # big cities in Europe
        df_bigCities = get_df_bigCities()
        ax.scatter(df_bigCities.longitude,df_bigCities.latitude,marker='o',color='k',facecolors='none',s=100,
                   transform=ccrs.PlateCarree())

      
        # emissions from all emissions except enery production, original EDGAR 4.3 for base year 2010
        path_edgar=path_stilt+'/Emissions/'
        filename='EDGARv4.3_2010_nonENE.nc'
    
        emis3, lon, lat, dd, unit = read_emissions(path_edgar+filename)

        # footprint * emission 
        fp_emis3=fp*emis3
        fp_emis3[fp<=0.0]=np.nan
    
        fp_emis3_z=fp_emis3[0,j1:j2,i1:i2]

        nonENE_contribution = np.nansum(fp_emis3_z)
        nonENE_ratio = 100.*nonENE_contribution/total_contribution
        print('nonENE_contribution', '%.1f' % nonENE_ratio,'%')

        ax = p.subplot(1, 2, 2, projection=ccrs.PlateCarree())
        img_extent = (lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max())
        ax.set_extent([lon_z.min(), lon_z.max(), lat_z.min(), lat_z.max()],crs=ccrs.PlateCarree())
        ax.add_feature(countries, edgecolor='black', linewidth=0.3)

        im = ax.imshow((fp_emis3_z)[:,:],interpolation='none',origin='lower',extent=img_extent,
                       vmin=0.000001,vmax=fxe_vmax,cmap=cmap)
        cbar=p.colorbar(im,orientation='horizontal',pad=0.03,fraction=0.055,extend='max')
        cbar.set_label('surface influence [ppm]')
        p.title('average footprints x non-energy emissions '+'%.1f' % nonENE_ratio
                +' %'+'\n'+'station: '+station+'     '
                +np.min(daterange).strftime('%Y-%m-%d')+' -- '+np.max(daterange).strftime('%Y-%m-%d')
                +'\n'+ident)
        ax.text(0.01, -0.29, 'min: %.5f' % np.nanmin(fp_emis3_z), horizontalalignment='left',transform=ax.transAxes)
        ax.text(0.99, -0.29, 'max: %.5f' % np.nanmax(fp_emis3_z), horizontalalignment='right',transform=ax.transAxes)

        #station location
        ax.plot(station_lon,station_lat,'+',color=mcolor,ms=10,markeredgewidth=2,transform=ccrs.PlateCarree())
    
        # big cities in Europe
        ax.scatter(df_bigCities.longitude,df_bigCities.latitude,marker='o',color='k',facecolors='none',s=100,
                   transform=ccrs.PlateCarree())#,latlon=True)


       
    p.tight_layout()
    p.show()
    if len(pngfile)>0:
        fig.savefig(pngfile+'.png',dpi=100)
    p.close()

#------------------------------------------------------------------------------------------------------------------

# function to apply temporal sampling of STILT time series + plot results
def plot_stilt_ts_selection(df,start_date,end_date,noon_time,midday_range,
                            obs=None,meteo=None,pngfile='',high=5.0, low=1.5, highco=0.05, var_limit=1.,summary=False):
    
    # selections

    # afternoon sampling
    # e.g. local time 12-15=> utc 11-14
    dd1, dd2 = midday_range
    df_day = df.loc[(df['hour'] >= dd1) & (df['hour'] <= dd2)]
    # range in afternoon values (max-min)
    df_range = df_day.resample('D',loffset='12H').max() - df_day.resample('D',loffset='12H').min()
    df_range.loc[(df_range['co2.stilt'] <= 0)]=np.nan
    
    # low variability selection for QC  (use range as variability)
    df_var = df_range.loc[(df_range['co2.stilt'] < var_limit)]
    df_var3 = df_var.iloc[::3, :]

    # find n lowest-variability-footprints 
    df_var_smallest = df_range[(df_range.index >= start_date) & (df_range.index <= end_date)].nsmallest(10, 'co2.stilt')

    # single noon value at 12 UTC => 13 LT for CET
    ddm=noon_time
    df_noon = df.loc[(df['hour'] >= ddm) & (df['hour'] <= ddm)]

    # low fossil fuel CO2 => background
    df_low=df_noon.loc[(df_noon['co2.fuel.coal']+df_noon['co2.fuel.oil']+df_noon['co2.fuel.gas'] < low)]
    
    # high ffCO2 => target
    df_high=df_noon.loc[(df_noon['co2.fuel.coal']+df_noon['co2.fuel.oil']+df_noon['co2.fuel.gas'] > high)]

    # select background based on wind direction
    # example for Gartow
    df_nordsee=df_low.loc[(df_low['wind.dir'] < 360) & (df_low['wind.dir'] > 270)]

    df_noon.name = df.name
    df_noon.model = df.model

    # select only every 3rd noon value
    df_noon3 = df_noon.iloc[::3, :]

    # select lowest value for previous 'ndrol' days
    ndrol='3'
    df_min = df.rolling(ndrol+'d',closed='right').min()
    # only noon value (select based on date info in original time series)
    df_min_noon = df_min.loc[(df['hour'] >= ddm) & (df['hour'] <= ddm)]

    # difference between 7-day minimum and value at noon
    df_offset=df_noon.subtract(df_min_noon)

    # high CO offset as indicator for high ffCO2
    df_highco=df_noon.loc[(df_offset['co.stilt'] > highco)]
    

    #plot time series
    if (df.name=='GAT344'):
        titlex = 'Gartow 341m'
    else:
        titlex = stilt_stations[df.name]['name']

    fig = p.figure(figsize=(15,14))
    ax = fig.add_subplot(5,1,1)
    p.plot(df.index,df['co2.stilt'],'.',color=lightgray,label='hourly values')
    p.plot(df_noon.index,df_noon['co2.stilt'],'.',color='b',label='at '+str(ddm+1)+' LT',markersize=12)
    p.plot(df_high.index,df_high['co2.stilt'],'x',color='r',label='if ffCO$_2$ offset >'+str(high)+' ppm'
            ,markersize=10,markeredgewidth=2)
    p.plot(df_highco.index,df_highco['co2.stilt'],'+',color='m',label='if CO offset >'+str(highco)+' ppm'
            ,markersize=12,markeredgewidth=2)
    p.title(titlex+'  '+str(df['latstart'][0])+'$^\circ$N'+'  '
            +str(df['lonstart'][0])+'$^\circ$E')
    ax.set_xlim(start_date,end_date)
    #ax.set_xticklabels([])
    ax.set_ylim(380,465)
    ax.set_ylabel('STILT CO$_2$  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='upper left',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    ax = fig.add_subplot(5,1,2)
    p.plot(df.index,df['co.stilt'],'.',color=lightgray,label='hourly values')
    p.plot(df_noon.index,df_noon['co.stilt'],'.',color='b',label='at '+str(ddm+1)+' LT',markersize=12)
    p.plot(df_min_noon.index,df_min_noon['co.stilt'],'-',color=gray,label=ndrol+' day minimum')
    p.plot(df_highco.index,df_highco['co.stilt'],'+',color='m',label='if CO offset >'+str(highco)+' ppm'
            ,markersize=12,markeredgewidth=2)
    ax.set_xlim(start_date,end_date)
    #ax.set_xticklabels([])
    ax.set_ylim(-0.01,0.24)
    ax.set_ylabel('regional STILT CO  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='upper left',ncol=8)

    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    ax = fig.add_subplot(5,1,3)
    p.plot(df_noon.index,df_noon['co2.bio'],'.',color='g',label='STILT bio CO$_2$ at '+str(ddm+1)+' LT')
    p.plot(df_noon.index,df_noon['co2.ff'],'.',color='r',label='STILT ff CO$_2$ at '+str(ddm+1)+' LT')
    p.plot(df_high.index,df_high['co2.ff'],'x',color='r',label='STILT ffCO$_2$ >'+str(high),
           markersize=10,markeredgewidth=2)
    p.plot(df_highco.index,df_highco['co2.ff'],'+',color='m',label='STILT ffCO$_2$ (CO offset >'+str(highco)+')',
           markersize=12,markeredgewidth=2)
    ax.set_xlim(start_date,end_date)
    #ax.set_xticklabels([])
    ax.set_ylim(-2,30)
    ax.set_ylabel('CO$_2$ components  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='upper left',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    ax = fig.add_subplot(5,1,4)
    p.plot(df_range.index,df_range['co2.stilt'],'.',color='r',label='range STILT CO$_2$ '
           +str(dd1+1)+'-'+str(dd2+1)+' LT')
    p.plot(df_var.index,df_var['co2.stilt'],'o',color='b',label='range STILT CO$_2$ < '
           +str(var_limit)+' '+str(dd1+1)+'-'+str(dd2+1)+' LT')
    ax.set_xlim(start_date,end_date)
    ax.set_xticklabels([])
    #ax.set_ylim(390,410)
    ax.set_ylabel('CO$_2$  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='best',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    ax = fig.add_subplot(5,1,5)
    p.plot([start_date,end_date],[0,0],color=gray,linewidth=0.5)
    p.plot([start_date,end_date],[90,90],color=gray,linewidth=0.5)
    p.plot([start_date,end_date],[180,180],color=gray,linewidth=0.5)
    p.plot([start_date,end_date],[270,270],color=gray,linewidth=0.5)
    p.plot([start_date,end_date],[360,360],color=gray,linewidth=0.5)
    p.plot(df.index,df['wind.dir'],'.',color=lightgray,label='STILT wind dir')
    ax.set_xlim(start_date,end_date)
    ax.set_ylim(0,360)
    ax.set_ylabel('wind direction')
    ax.grid(axis='x')
    #ax.grid(axis='y')
    ax.legend(loc='best',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    
    p.tight_layout(h_pad=0.005)
    p.show()
    if len(pngfile)>0:
        fig.savefig(pngfile+'.png',dpi=100)
    p.close()

    
    if summary:
        # print summary 
        summary_file=path_plots+df.name+'_selection_STILT_counts.csv'
        open(summary_file,'w').write(stilt_stations[df.name]['name']+'  '+str(df['latstart'][0])+' N'+'  '
            +str(df['lonstart'][0])+' E'+'\n')
        n_highffco2 = df_high.groupby(pd.Grouper(freq='M')).count()
        display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with ffCO2 offset > '+str(high)+' ppm</p>'))
        display(HTML(n_highffco2['co2.stilt'].to_frame(name='counts per month').to_html())) 
        open(summary_file,'a').write('Events with ffCO2 offset > '+str(high)+' ppm'+'\n')
        n_highffco2['co2.stilt'].to_frame(name='counts per month').to_csv(summary_file,mode='a')
        
        n_highco = df_highco.groupby(pd.Grouper(freq='M')).count()
        display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with CO offset > '+str(highco)+' ppm</p>'))
        display(HTML(n_highco['co2.stilt'].to_frame(name='counts per month').to_html())) 
        open(summary_file,'a').write('Events with CO offset > '+str(highco)+' ppm'+'\n')
        n_highco['co2.stilt'].to_frame(name='counts per month').to_csv(summary_file,mode='a')

        n_var = df_var.groupby(pd.Grouper(freq='M')).count()
        display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with small daytime CO2 difference < '+str(var_limit)+' ppm</p>'))
        display(HTML(n_var['co2.stilt'].to_frame(name='counts per month').to_html())) 
        open(summary_file,'a').write('Events with small daytime CO2 difference < '+str(var_limit)+' ppm'+'\n')
        n_var['co2.stilt'].to_frame(name='counts per month').to_csv(summary_file,mode='a')

        n_var_smallest = df_var_smallest.groupby(pd.Grouper(freq='M')).count()
        max_var_smallest = df_var_smallest.groupby(pd.Grouper(freq='M')).max()
        display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">10 events with smallest daytime CO2 differences</p>'))
        #display(HTML(n_var_smallest['co2.stilt'], ' max value: ', max_var_smallest['co2.stilt']
        display(HTML(max_var_smallest['co2.stilt'].to_frame(name='max of 10 smallest var').to_html()))        
        open(summary_file,'a').write('10 events with smallest daytime CO2 differences'+'\n')
        max_var_smallest['co2.stilt'].to_frame(name='counts per month').to_csv(summary_file,mode='a')
        
        display(HTML('<br> <br>'))

    df_select_high=df_high[(df_high.index >= start_date) & (df_high.index <= end_date)]
    df_select_highco=df_highco[(df_highco.index >= start_date) & (df_highco.index <= end_date)]
    df_select_low=df_low[(df_low.index >= start_date) & (df_low.index <= end_date)]
    df_select_noon=df_noon[(df_noon.index >= start_date) & (df_noon.index <= end_date)]
    df_select_noon3=df_noon3[(df_noon3.index >= start_date) & (df_noon3.index <= end_date)]
    df_select_var=df_var[(df_var.index >= start_date) & (df_var.index <= end_date)]
    df_select_var_smallest=df_var_smallest[(df_var_smallest.index >= start_date) & (df_var_smallest.index <= end_date)]
        
    return df_select_low, df_select_high, df_select_highco, df_select_noon, df_select_noon3, df_select_var, df_select_var_smallest


#------------------------------------------------------------------------------------------------------------------

# function to call temporal secletion function and aggregate footprints accordingly
def all_selection_plots(station,sdate,edate,loc_ident,station_lat,station_lon,
                        high,low,highco,var_limit, noon_time, midday_range,summary=False,plot_foot=True):
    
    # read 1-hourly STILT results (RINGO specific STILT runs)
    df_stilt_1hr = pd.DataFrame()
    for year in range(sdate.year,edate.year+1):
        df = read_stilt_timeseries_RINGO_T13(station,year,loc_ident)
        df_stilt_1hr = df_stilt_1hr.append(df)
        df_stilt_1hr.name = df.name
        df_stilt_1hr.model = df.model
        
    for yrmon in rrule(MONTHLY, dtstart=sdate, until=edate):

        start_date = dt.datetime(yrmon.year,yrmon.month,1,0)
        if yrmon.month >= 12:
            end_date = dt.datetime(yrmon.year+1,1,1,0)
        else:
            end_date = dt.datetime(yrmon.year,yrmon.month+1,1,0)
        end_date = end_date - dt.timedelta(hours=1)
    
        # return time serie selection
        pngfile='selection_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
        df_select_noon_low, df_select_noon_high, df_select_noon_highco, df_select_noon, df_select_3rdnoon, df_select_noon_var, df_select_noon_var_smallest = \
                                 plot_stilt_ts_selection(df_stilt_1hr,start_date,end_date,noon_time,midday_range,pngfile=path_plots+pngfile,
                                                         low=low,high=high,highco=highco,summary=summary)
        summary = False

        if plot_foot:
            # aggregated footprints

            # set upper limit for color scale in 'footprint x emissions' map
            # e.g. fxe_vmax=0.16
            # in all other maps the color scale is set automatically

            # all footprints at noontime 
            selected=df_select_noon.index
            pngfile='FP_noon_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='all '+str(noon_time+1)+' LT',pngfile=path_plots+pngfile)
        
            # footprints at noontime, every 3rd day only 
            selected=df_select_3rdnoon.index
            pngfile='FP_noon3_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident=str(noon_time+1)+' LT every 3rd day',pngfile=path_plots+pngfile)
        
            # 10 footprints for situations with lowest variability around noon
            selected=df_select_noon_var_smallest.index
            pngfile='FP_10lowestvar_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='10 lowest variability',pngfile=path_plots+pngfile)
            
            # footprints for situations with low variability around noon
            selected=df_select_noon_var.index
            pngfile='FP_var_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='low variability < '+str(var_limit)+' ppm',pngfile=path_plots+pngfile)

            # footprints for low ffCO2
            selected=df_select_noon_low.index
            pngfile='FP_lowffCO2_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='low ffCO2 < '+str(low)+' ppm',pngfile=path_plots+pngfile)

            # footprints for high ffCO2
            selected=df_select_noon_high.index
            pngfile='FP_highffCO2_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='high ffCO2 > '+str(high)+' ppm',secsplit=False,pngfile=path_plots+pngfile)

            # footprints for high ffCO2, split into energy and non-energy emissions
            selected=df_select_noon_high.index
            pngfile='FP_highffCO2_secsplit_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='high ffCO2 > '+str(high)+' ppm',secsplit=True,
                            pngfile=path_plots+pngfile)

            # footprints for high CO offset
            selected=df_select_noon_highco.index
            pngfile='FP_highffCO_STILT_'+station+'_'+str(start_date.year)+str(start_date.month).zfill(2)
            plot_footprints(station,station_lat,station_lon,loc_ident,selected,
                            fxe_vmax=0.14,ident='high CO offset > '+str(highco)+' ppm',pngfile=path_plots+pngfile)

#------------------------------------------------------------------------------------------------------------------

# function to plot STILT time series together with observations 
def plot_icos_stilt_timeseries(station, df, start_date, end_date,
                               obs=None,meteo=None,title2='',linestyle = '.',
                               pngfile='',add_tracer=[], citation=''):
    #plot time series
    tracer = add_tracer + ['co2']
    tracer = [x.lower() for x in tracer]

    if obs is not None and not obs.empty:
        if obs.columns.str.contains('Flag').any():
            obs = obs.drop(columns=['Flag_co2', 'Flag_co'])

    fig = p.figure(figsize=(15,8.8))

    ax = fig.add_subplot(3,1,1)
    p.plot(df.index,df['co2.stilt'],linestyle,color='b',label='STILT CO$_2$')
    p.plot(df.index,df['co2.background'],linestyle,color='c',label='STILT CO$_2$ background')
    if obs is not None and not obs.empty:
        if 'DateTime' in obs:
            p.plot(obs.DateTime,obs['CO2'],linestyle,color='k',label='Observation CO$_2$')
        else:
            if 'co2' in obs:
                p.plot(obs.index,obs['co2'],linestyle,color='k',label='Observation CO$_2$')
            if 'CO2' in obs:
                p.plot(obs.index,obs['CO2'],linestyle,color='k',label='Observation CO$_2$')
    p.title(stilt_stations[df.name]['icosName']+'  {:.0f}m'.format(stilt_stations[df.name]['icosHeight'])+'  '
            +str(df['latstart'][0])+'$^\circ$N'+'  '+str(df['lonstart'][0])+'$^\circ$E'+'    '+title2)
    ax.set_xlim(start_date,end_date)
    ax.set_ylim(380,465)
    ax.set_ylabel('CO$_2$  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='upper left',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    ax = fig.add_subplot(3,1,2)
    p.plot(df.index,df['co2.fuel.coal']+df['co2.fuel.oil']+df['co2.fuel.gas'],linestyle,color='r',label='ffCO$_2$ offset')
    p.plot(df.index,df['co2.bio'],linestyle,color='g',label='biospheric CO$_2$ offset')
    ax.set_xlim(start_date,end_date)
    ax.set_ylim(-31,54)
    ax.set_ylabel('STILT CO$_2$  [ppm]')
    ax.grid(axis='x')
    ax.grid(axis='y')
    ax.legend(loc='upper left',ncol=8)
    # Define the date format
    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    # Ensure a major tick for each week using (interval=1) 
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    if ('co.stilt' in df) and ('co' in tracer):
        ax = fig.add_subplot(3,1,3)
        p.plot(df.index,df['co.stilt'],linestyle,color='m',label='STILT CO (no background)')
        if obs is not None and not obs.empty:
            if 'DateTime' in obs:
                p.plot(obs.index,obs['CO'],linestyle,color='k',label='Observation CO')
            else:
                # select lowest value for previous 'nrol' days
                # only works if DateTime is defined as index
                # in case of many missing values, 'min' is not defined, better use very low quantile 
                nrol='3'
                df_obs_min = obs.rolling(nrol+'d',closed='right',min_periods=1).quantile(0.001) 
                if 'co' in obs:
                    p.plot(obs.index,obs['co']-df_obs_min['co'],linestyle,color='k',label='Observation CO')
                if 'CO' in obs:
                    p.plot(obs.index,obs['CO']-df_obs_min['CO'],linestyle,color='k',label='Observation CO')               
        ax.set_xlim(start_date,end_date)
        ax.set_ylabel('CO  [ppm]')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='best',ncol=8)
        # Define the date format
        date_form = DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(date_form)
        # Ensure a major tick for each week using (interval=1) 
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    #if ('rn' in df) and ('rn' in tracer):
    #    ax = fig.add_subplot(4,1,4)
    #    p.plot(df.index,df['rn'],linestyle,color='y',label='STILT 222Rn')
    #    if obs is not None and 'rn' in obs and not obs.empty:
    #        p.plot(obs.index,obs['rn'],linestyle,color='k',label='Observation 222Rn')
    #    ax.set_xlim(start_date,end_date)
    #    ax.set_ylabel('222RN  [mBq/m3]')
    #    ax.grid(axis='x')
    #    ax.grid(axis='y')
    #    ax.legend(loc='best',ncol=8)
    #    # Define the date format
    #    date_form = DateFormatter("%Y-%m-%d")
    #    ax.xaxis.set_major_formatter(date_form)
    #    # Ensure a major tick for each week using (interval=1) 
    #    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    
    ax.text(0.01, -0.24, citation, verticalalignment='top', transform=ax.transAxes)

    p.tight_layout()
    p.show()
    if len(pngfile)>0:
        fig.savefig(pngfile+'.png',dpi=100)
    p.close()

#------------------------------------------------------------------------------------------------------------------

# function for comparison of STILT results with ICOS data and plot time series
def plot_comparison(ist,df_co2,df_co,df_meteo,sdate,edate,citation=''):
    
    # check if ICOS data (CO2,CO) is available and combine CO2 and CO in one data frame
    if not df_co2.empty and not df_co.empty: 
        df_obs = pd.merge(df_co2,df_co,left_index=True, right_index=True, how='outer', suffixes=('_co2', '_co'))
        if df_obs.columns.str.contains('Flag').any():
            df_obs = df_obs.drop(columns=['Flag_co2', 'Flag_co'])

    else:
        df_obs = pd.DataFrame(None)

    # check if STILT results are available for the station 
    if not ist in stilt_stations.keys():
        print('no STILT results for station: ',ist)
    else:
        # read 1-hourly STILT time series, available only for specific stations
        df_stilt = pd.DataFrame()
        for year in range(sdate.year,edate.year+1):
            df = read_stilt_timeseries_RINGO_T13(ist,year,stilt_stations[ist]['locIdent'])
            df_stilt = df_stilt.append(df)
            df_stilt.name = df.name
            df_stilt.model = df.model

        if df.empty:
            print('no 1-hourly STILT results for station: ',ist)
        else:
            # monthly plots
            for yrmon in rrule(MONTHLY, dtstart=sdate, until=edate):

                start_date = dt.datetime(yrmon.year,yrmon.month,1,0)
                if yrmon.month >= 12:
                    end_date = dt.datetime(yrmon.year+1,1,1,0)
                else:
                    end_date = dt.datetime(yrmon.year,yrmon.month+1,1,0)
                end_date = end_date - dt.timedelta(hours=1)

                timeselect='all'

                # plot time series
                pngfile='comparison_ICOS_STILT_'+ist+'_'+str(start_date.year)+str(start_date.month).zfill(2)
                plot_icos_stilt_timeseries(ist, df_stilt, start_date, end_date, obs = df_obs, 
                                           linestyle='-',add_tracer=['co'],pngfile=path_plots+pngfile,citation=citation)
                

#------------------------------------------------------------------------------------------------------------------

# function to apply temporal sampling of ICOS measurements time series and plot results
def plot_icos_ts_selection(ist, df_co2, df_co, df_meteo, highco, var_limit, stdev_limit, 
                           noon_time, midday_range, start=None, end=None, summary=False, citation=''):

    # check if ICOS data (CO2,CO) is available and combine CO2 and CO in one data frame
    if not df_co2.empty and not df_co.empty:         
        df_obs = pd.merge(df_co2,df_co,left_index=True, right_index=True, how='outer', suffixes=('_co2', '_co'))
        if df_obs.columns.str.contains('Flag').any():
            df_obs = df_obs.drop(columns=['Flag_co2', 'Flag_co'])
       
        # afternoon sampling
        # e.g. local time 12-15=> utc 11-14
        dd1, dd2 = midday_range
        ddm = noon_time

        df_obs_day = df_obs.loc[(df_obs.index.hour >= dd1) & (df_obs.index.hour <= dd2)]
        # range in afternoon values (max-min)
        df_co2_range = (df_obs_day['co2'].resample('D',loffset='12H').max() - df_obs_day['co2'].resample('D',loffset='12H').min()).to_frame()
        df_co2_range.loc[(df_co2_range['co2'] <= 0)]=np.nan

        # low variability selection for QC  (use range as variability)
        df_obs_var = df_co2_range.loc[(df_co2_range['co2'] < var_limit)]
        df_obs_var3 = df_obs_var.iloc[::3, :]

        df_obs_lowStdev=df_obs.loc[(df_obs['Stdev_co2'] < stdev_limit)]
                        
        # single noon value at 12 UTC => 13 LT for CET
        df_obs_noon = df_obs.loc[(df_obs.index.hour >= ddm) & (df_obs.index.hour <= ddm)]

        # high CO as indicator for high ffCO2
        df_obs_highco=df_obs_noon.loc[(df_obs_noon['co'] > highco)]

        # select only every 3rd noon value
        df_obs_noon3 = df_obs_noon.iloc[::3, :]

        # select lowest value for previous 'nrol' days
        # in case of many missing values, 'min' is not defined, better use very low quantile 
        nrol='3'
        df_obs_min = df_obs.rolling(nrol+'d',closed='right',min_periods=1).min()###.quantile(0.001,numeric_only=True)
        # only noon value (select based on date info in original time series)
        df_obs_min_noon = df_obs_min.loc[(df_obs.index.hour >= ddm) & (df_obs.index.hour <= ddm)]

        # difference between 'nrol'-day minimum and value at noon
        df_obs_offset=df_obs_noon.subtract(df_obs_min_noon)

        # high CO offset as indicator for high ffCO2
        df_obs_highco=df_obs_noon.loc[(df_obs_offset['co'] > highco)]
    
        # low standard deviation at noon
        df_obs_lowStdev_noon=df_obs_noon.loc[(df_obs_noon['Stdev_co2'] < stdev_limit)]
    

        # plot time series for each month
        # if start and/or end date are specified in the parameters list, use them
        # otherwise extract start and end date of time series
        sd0 = df_obs.index[0]
        ed0 = df_obs.index[-1]+dt.timedelta(days=32-df_obs.index[-1].day) #round up to next month/year
        if start is not None:
            sd = start
        else:
            #sd0 = df_obs.index[0]
            sd = dt.datetime(sd0.year,sd0.month,1,0)

        if end is not None:
            ed = end
        else:
            #ed0 = df_obs.index[-1]+dt.timedelta(days=32-df_obs.index[-1].day) #round up to next month/year
            ed = dt.datetime(ed0.year,ed0.month,1,0)

        for yrmon in rrule(MONTHLY, dtstart=sd, until=ed):
            start_date = dt.datetime(yrmon.year,yrmon.month,1,0)
            if yrmon.month >= 12:
                end_date = dt.datetime(yrmon.year+1,1,1,0)
            else:
                end_date = dt.datetime(yrmon.year,yrmon.month+1,1,0)
            end_date = end_date - dt.timedelta(hours=1)

            if (start_date > ed0) or (end_date < sd0):
                display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">no ICOS data available for '
                             +start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))

            else:
                fig = p.figure(figsize=(15,14))
                ax = fig.add_subplot(5,1,1)
                p.plot(df_obs.index,df_obs['co2'],'.',color=lightgray,label='hourly values')
                p.plot(df_obs_noon.index,df_obs_noon['co2'],'.',color='b',label='at '+str(ddm+1)+' LT',markersize=12)
                p.plot(df_obs_highco.index,df_obs_highco['co2'],'+',color='m',label='if obs CO offset >'+str(highco)+' ppm',
                       markersize=12,markeredgewidth=2)
                p.title(stilt_stations[ist]['icosName']+'  {:.0f}m'.format(stilt_stations[ist]['icosHeight'])
                        +'  {:.2f}$^\circ$N'.format(stilt_stations[ist]['icosLat'])
                        +'  {:.2f}$^\circ$E'.format(stilt_stations[ist]['icosLon']))         
                ax.set_xlim(start_date,end_date)
                ax.set_ylim(380,465)
                ax.set_ylabel(' obs CO$_2$  [ppm]')
                ax.grid(axis='x')
                ax.grid(axis='y')
                ax.legend(loc='upper left',ncol=8)
                # Define the date format
                date_form = DateFormatter("%Y-%m-%d")
                ax.xaxis.set_major_formatter(date_form)
                # Ensure a major tick for each week using (interval=1) 
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

                ax = fig.add_subplot(5,1,2)
                #p.plot([start_date,end_date],[highco,highco],':',color='k')#,linewidth=0.5)
                p.plot(df_obs.index,df_obs['co'],'.',color=lightgray,label='hourly values')
                p.plot(df_obs_noon.index,df_obs_noon['co'],'.',color='b',label='at '+str(ddm+1)+' LT',markersize=12)
                #p.plot(df_obs_min_noon.index,df_obs_min_noon['co'],'-',color=gray,label=nrol+' day minimum at '+str(ddm+1)+' LT')
                p.plot(df_obs_min_noon.index,df_obs_min_noon['co'],'-',color=gray,label=nrol+' day minimum')
                p.plot(df_obs_highco.index,df_obs_highco['co'],'+',color='m',label='if obs CO offset >'+str(highco)+' ppm',
                       markersize=12,markeredgewidth=2)
                ax.set_xlim(start_date,end_date)
                ax.set_ylim(0.06,0.31)
                ax.set_ylabel('obs CO  [ppm]')
                ax.grid(axis='x')
                ax.grid(axis='y')
                ax.legend(loc='upper left',ncol=8)
                # Define the date format
                date_form = DateFormatter("%Y-%m-%d")
                ax.xaxis.set_major_formatter(date_form)
                # Ensure a major tick for each week using (interval=1) 
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

                ax = fig.add_subplot(5,1,3)
                p.plot(df_obs.index,df_obs['Stdev_co2'],'.',color=lightgray,label='CO$_2$ Stdev ')
                p.plot(df_obs_noon.index,df_obs_noon['Stdev_co2'],'.',color=lime,label='CO$_2$ Stdev at '+str(ddm+1)+' LT')
                #p.title(ist)
                ax.set_xlim(start_date,end_date)
                #ax.set_ylim(-0.5,6)
                ax.set_ylabel('CO$_2$  [ppm]')
                ax.grid(axis='x')
                ax.grid(axis='y')
                ax.legend(loc='best',ncol=8)
                # Define the date format
                date_form = DateFormatter("%Y-%m-%d")
                ax.xaxis.set_major_formatter(date_form)
                # Ensure a major tick for each week using (interval=1) 
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            
                ax = fig.add_subplot(5,1,4)
                p.plot([start_date,end_date],[var_limit,var_limit],':',color='k')#,linewidth=0.5)
                p.plot([start_date,end_date],[stdev_limit,stdev_limit],':',color='k')#,linewidth=0.5)
                p.plot(df_co2_range.index,df_co2_range['co2'],'.',color='r',label='range CO$_2$ '+str(dd1+1)+'-'+str(dd2+1)+' LT')
                p.plot(df_obs_var.index,df_obs_var['co2'],'o',color='b',label='range CO$_2$ < '+str(var_limit)+' '+str(dd1+1)+'-'+str(dd2+1)+' LT')
                p.plot(df_obs_noon.index,df_obs_noon['Stdev_co2'],'.',color=lime,label=' CO$_2$ Stdev at '+str(ddm+1)+' LT')
                p.plot(df_obs_lowStdev_noon.index,df_obs_lowStdev_noon['Stdev_co2'],'^',color='g',label=' CO$_2$ Stdev < '+str(stdev_limit)+' '+str(ddm+1)+' LT')
                ax.set_xlim(start_date,end_date)
                #ax.set_ylim(-0.5,6)
                #ax.set_ylim(390,410)
                ax.set_ylabel('CO$_2$ [ppm]')
                ax.grid(axis='x')
                ax.grid(axis='y')
                ax.legend(loc='best',ncol=8)
                # Define the date format
                date_form = DateFormatter("%Y-%m-%d")
                ax.xaxis.set_major_formatter(date_form)
                # Ensure a major tick for each week using (interval=1) 
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))


                ax = fig.add_subplot(5,1,5)
                p.plot([start_date,end_date],[0,0],color=gray,linewidth=0.5)
                p.plot([start_date,end_date],[90,90],color=gray,linewidth=0.5)
                p.plot([start_date,end_date],[180,180],color=gray,linewidth=0.5)
                p.plot([start_date,end_date],[270,270],color=gray,linewidth=0.5)
                p.plot([start_date,end_date],[360,360],color=gray,linewidth=0.5)
                if not df_meteo.empty:
                    p.plot(df_meteo.index,df_meteo['WD'],'.',color='lightgray',label='wind dir')
                ax.set_xlim(start_date,end_date)
                ax.set_ylim(0,360)
                ax.set_ylabel('wind direction  [$^\circ$]')
                ax.grid(axis='x')
                #ax.grid(axis='y')
                ax.legend(loc='best',ncol=8)
                # Define the date format
                date_form = DateFormatter("%Y-%m-%d")
                ax.xaxis.set_major_formatter(date_form)
                # Ensure a major tick for each week using (interval=1) 
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                
                ax.text(0.01, -0.24, citation, verticalalignment='top',transform=ax.transAxes)

                p.tight_layout()
                p.show()
                pngfile='selection_ICOS_'+ist+'_'+str(start_date.year)+str(start_date.month).zfill(2)
                fig.savefig(path_plots+pngfile+'.png',dpi=100)
                p.close()

        if summary:
            # print summary 
            summary_file=path_plots+ist+'_selection_ICOS_counts.csv'
            open(summary_file,'w').write(stilt_stations[ist]['icosName']+' {:.0f}'.format(stilt_stations[ist]['icosHeight'])
                                         +' {:.2f}'.format(stilt_stations[ist]['icosLat'])
                                         +' {:.2f}'.format(stilt_stations[ist]['icosLon'])+'\n')
            n_highco = df_obs_highco.groupby(pd.Grouper(freq='M')).count()
            display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with CO offset > '+str(highco)+' ppm</p>'))
            display(HTML(n_highco['co'].to_frame(name='counts per month').to_html())) 
            open(summary_file,'a').write('Events with CO offset > '+str(highco)+' ppm'+'\n')
            n_highco['co'].to_frame(name='counts per month').to_csv(summary_file,mode='a')
            
            ny_highco = n_highco['co2'].to_frame().groupby(n_highco['co2'].to_frame().index.month).mean()
            display(HTML('<br> <b>multi-annual mean</b>'))
            display(HTML(ny_highco['co2'].to_frame(name='counts per month').to_html())) 

            n_lowStdev = df_obs_lowStdev_noon.groupby(pd.Grouper(freq='M')).count()
            display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with low CO2 variability < '+str(stdev_limit)+'ppm</p>'))
            display(HTML(n_lowStdev['Stdev_co2'].to_frame(name='counts per month').to_html())) 
            open(summary_file,'a').write('Events with low CO2 variability < '+str(stdev_limit)+'ppm'+'\n')
            n_lowStdev['co'].to_frame(name='counts per month').to_csv(summary_file,mode='a')

            ny_lowStdev = n_lowStdev['co2'].to_frame().groupby(n_lowStdev['co2'].to_frame().index.month).mean()
            display(HTML('<br> <b>multi-annual mean</b>'))
            display(HTML(ny_lowStdev['co2'].to_frame(name='counts per month').to_html())) 

            n_var = df_obs_var.groupby(pd.Grouper(freq='M')).count()
            display(HTML('<br> <p style="font-size:15px;font-weight:bold;color:royalblue;">Events with small daytime CO2 difference < '+str(var_limit)+'ppm</p>'))
            display(HTML(n_var['co2'].to_frame(name='counts per month').to_html())) 
            open(summary_file,'a').write('Events with small daytime CO2 difference < '+str(var_limit)+'ppm'+'\n')
            n_var['co2'].to_frame(name='counts per month').to_csv(summary_file,mode='a')

            ny_var = n_var['co2'].to_frame().groupby(n_var['co2'].to_frame().index.month).mean()
            display(HTML('<br> <b>multi-annual mean</b>'))
            display(HTML(ny_var['co2'].to_frame(name='counts per month').to_html())) 

#------------------------------------------------------------------------------------------------------------------

# function to read dataframe with big cities in Europe
def get_df_bigCities():
    filename='majorCitiesEurope.xlsx'
    df_bigCities = pd.read_excel(filename,sheet_name='Tabelle2',skiprows=1,
                             names=['Rang','Name','Einwohner','longitude','latitude','inhabitants'])
    #problems with decimlal points... 
    df_bigCities.inhabitants[df_bigCities.inhabitants > 100] = df_bigCities.inhabitants/1000.
    return df_bigCities

#------------------------------------------------------------------------------------------------------------------

# function to test sensitivity of selection strategy on monthly mean 
def sensitivity_selection_icos(ist, df_co2, df_co, df_meteo, highco, var_limit, stdev_limit, 
                               noon_time, midday_range, start=None, end=None, summary=False, citation=''):

    # colorbrewer colors red to blue
    cb=['#b2182b','#d6604d','#f4a582','#fddbc7','#d1e5f0','#92c5de','#4393c3','#2166ac']

    # check if ICOS data (CO2,CO) is available and combine CO2 and CO in one data frame
    if not df_co2.empty and not df_co.empty:         
        df_obs = pd.merge(df_co2,df_co,left_index=True, right_index=True, how='outer', suffixes=('_co2', '_co'))
        if df_obs.columns.str.contains('Flag').any():
            df_obs = df_obs.drop(columns=['Flag_co2', 'Flag_co'])

        # afternoon sampling
        # e.g. local time 12-15=> utc 11-14
        dd1, dd2 = midday_range 
        ddm = noon_time

        df_obs_noon = df_obs.loc[df_obs.index.hour == ddm]
        df_obs_day = df_obs.loc[(df_obs.index.hour >= dd1) & (df_obs.index.hour <= dd2)]
        df_obs_dm = df_obs_day.resample('D',loffset=str(ddm)+'H').mean()
        df_obs_dm_3_1 = df_obs_noon.iloc[0::3, :]
        df_obs_dm_3_2 = df_obs_noon.iloc[1::3, :]
        df_obs_dm_3_3 = df_obs_noon.iloc[2::3, :]
        df_obs_dm_7_1 = df_obs_noon.iloc[0::7, :]
        df_obs_dm_mm = df_obs_dm.resample('M',loffset='-15D').mean()
        df_obs_dm_3_1_mm = df_obs_dm_3_1.resample('M',loffset='-15D').mean()
        df_obs_dm_3_2_mm = df_obs_dm_3_2.resample('M',loffset='-15D').mean()
        df_obs_dm_3_3_mm = df_obs_dm_3_3.resample('M',loffset='-15D').mean()
        df_obs_dm_7_1_mm = df_obs_dm_7_1.resample('M',loffset='-15D').mean()
        df_obs_dm_std = df_obs_dm.resample('M',loffset='-15D').std()
        df_obs_dm_3_1_std = df_obs_dm_3_1.resample('M',loffset='-15D').std()
        df_obs_dm_3_2_std = df_obs_dm_3_2.resample('M',loffset='-15D').std()
        df_obs_dm_3_3_std = df_obs_dm_3_3.resample('M',loffset='-15D').std()
        df_obs_dm_7_1_std = df_obs_dm_7_1.resample('M',loffset='-15D').std()
        df_obs_dm_count = df_obs_dm.resample('M',loffset='-15D').count()
        df_obs_dm_3_1_count = df_obs_dm_3_1.resample('M',loffset='-15D').count()
        df_obs_dm_3_2_count = df_obs_dm_3_2.resample('M',loffset='-15D').count()
        df_obs_dm_3_3_count = df_obs_dm_3_3.resample('M',loffset='-15D').count()
        df_obs_dm_7_1_count = df_obs_dm_7_1.resample('M',loffset='-15D').count()

        # find n lowest-variability-footprints 
        df_var_smallest = pd.DataFrame()

        
        # plot time series for each month
        # if start and/or end date are specified in the parameters list, use them
        # otherwise extraxt start and end date of time series
        if start is not None:
            sd = start
        else:
            sd0 = df_obs.index[0]
            sd = dt.datetime(sd0.year,sd0.month,1,0)

        if end is not None:
            ed = end
        else:
            ed0 = df_obs.index[-1]+dt.timedelta(days=32-df_obs.index[-1].day) #round up to next month/year
            ed = dt.datetime(ed0.year,ed0.month,1,0)

        for yrmon in rrule(MONTHLY, dtstart=sd, until=ed):
            start_date = dt.datetime(yrmon.year,yrmon.month,1,0)
            if yrmon.month >= 12:
                end_date = dt.datetime(yrmon.year+1,1,1,0)
            else:
                end_date = dt.datetime(yrmon.year,yrmon.month+1,1,0)
            end_date = end_date - dt.timedelta(hours=1)

            df_vs = df_obs_noon[(df_obs_noon.index >= start_date) & 
                                (df_obs_noon.index <= end_date)].nsmallest(10, 'Stdev_co2')
            df_var_smallest = df_var_smallest.append(df_vs)


        df_var_smallest_mm = df_var_smallest.resample('M',loffset='-15D').mean()
        df_var_smallest_std = df_var_smallest.resample('M',loffset='-15D').std()
        df_var_smallest_count = df_var_smallest.resample('M',loffset='-15D').count()


        idx = df_obs_dm_mm.index.intersection(df_obs_dm_7_1_mm.index)
        idxx = df_obs_dm_mm.index.intersection(df_var_smallest_mm.index)
        
        fig = p.figure(figsize=(15,17))

        start_date = dt.datetime(2016,5,1,0)
        end_date = dt.datetime(2019,5,1,0)
        idx = pd.date_range(df_obs_dm_3_1.index[0],df_obs_dm_3_1.index[-1],freq='3D' )
        df_obs_dm_3_1 = df_obs_dm_3_1.reindex(idx, fill_value=np.nan)

        ax = fig.add_subplot(5,1,1)
        p.plot(df_obs.index,df_obs['co2'],'.',color=lightgray,label='hourly CO$_2$ obs ')
        p.plot(df_obs_dm_3_1.index,df_obs_dm_3_1['co2'],'.',color=cb[7],label='_nolegend_')
        p.plot(df_obs_dm_3_2.index,df_obs_dm_3_2['co2'],'.',color=cb[6],label='_nolegend_')
        p.plot(df_obs_dm_3_3.index,df_obs_dm_3_3['co2'],'.',color=cb[5],label='_nolegend_')
        p.plot(df_obs_dm_3_1.index,df_obs_dm_3_1['co2'],'-',color=cb[7],label='_nolegend_')#,label=str(ddm+1)+' LT every 3rd day')#,label=ist+' CO2 obs mean('+str(dd1+1)+'-'+str(dd2+1)+' LT)')
        p.plot(df_obs_dm_3_2.index,df_obs_dm_3_2['co2'],'-',color=cb[6],label='every 3rd day at '+str(ddm+1)+' LT ')#,label=ist+' CO2 obs mean('+str(dd1+1)+'-'+str(dd2+1)+' LT)')
        p.plot(df_obs_dm_3_3.index,df_obs_dm_3_3['co2'],'-',color=cb[5],label='_nolegend_')#,label=str(ddm+1)+' LT every 3rd day')
        p.plot(df_var_smallest.index,df_var_smallest['co2'],'.',color=cb[0],label='10 days per month w/ smallest var at '+str(ddm+1)+' LT')#,label=ist+' CO2 obs mean('+str(dd1+1)+'-'+str(dd2+1)+' LT)')
        p.title(stilt_stations[ist]['icosName']+'  {:.0f}m'.format(stilt_stations[ist]['icosHeight'])
                +'  {:.2f}$^\circ$N'.format(stilt_stations[ist]['icosLat'])
                +'  {:.2f}$^\circ$E'.format(stilt_stations[ist]['icosLon']))         
        ax.set_xlim(start_date,end_date)
        ax.set_ylim(380,460)
        ax.set_ylabel('CO$_2$  [ppm]')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='upper left',ncol=8)

        ax = fig.add_subplot(5,1,2)
        p.errorbar(df_obs_dm_mm.index-dt.timedelta(days=4), df_obs_dm_mm['co2'], 
                   yerr=df_obs_dm_std['co2'], fmt='o', color='k',ms=10,label=str(dd1+1)+'-'+str(dd2+1)+' LT mean every day')
        p.errorbar(df_var_smallest_mm.index-dt.timedelta(days=-4), df_var_smallest_mm['co2'], 
                   yerr=df_var_smallest_std['co2'], fmt='o', color=cb[0],label='10 days per month w/ smallest var at '+str(ddm+1)+' LT')
        p.errorbar(df_obs_dm_3_1_mm.index-dt.timedelta(days=2), df_obs_dm_3_1_mm['co2'], 
                   yerr=df_obs_dm_3_1_std['co2'], fmt='o', color=cb[7],label='_nolegend_')
        p.errorbar(df_obs_dm_3_2_mm.index-dt.timedelta(days=0), df_obs_dm_3_2_mm['co2'], 
                   yerr=df_obs_dm_3_2_std['co2'], fmt='o', color=cb[6],label='every 3rd day at '+str(ddm+1)+' LT')
        p.errorbar(df_obs_dm_3_3_mm.index-dt.timedelta(days=-2), df_obs_dm_3_3_mm['co2'], 
                   yerr=df_obs_dm_3_3_std['co2'], fmt='o', color=cb[5],label='_nolegend_')
        ax.set_xlim(start_date,end_date)
        ax.set_ylim(380,460)
        ax.set_ylabel('monthly mean CO$_2$  [ppm]')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='upper left',ncol=8)

        ax = fig.add_subplot(5,1,3)
        p.plot(df_obs_dm_mm.index-dt.timedelta(days=5), df_obs_dm_mm['co2']-df_obs_dm_mm['co2'], '-', 
               color='gray',label='_nolegend_')
        p.plot(df_var_smallest_mm.index-dt.timedelta(days=-4), df_var_smallest_mm['co2']-df_obs_dm_mm.loc[idxx]['co2'], '-',
               color=cb[0],label=str(ddm+1)+' LT smallest var - '+str(dd1+1)+'-'+str(dd2+1)+' LT mean every day')
        p.plot(df_obs_dm_3_1_mm.index-dt.timedelta(days=2), df_obs_dm_3_1_mm['co2']-df_obs_dm_mm['co2'], '-', 
               color=cb[7],label='_nolegend_')
        p.plot(df_obs_dm_3_2_mm.index-dt.timedelta(days=0), df_obs_dm_3_2_mm['co2']-df_obs_dm_mm['co2'], '-', 
               color=cb[6],label=str(ddm+1)+' LT every 3rd day - '+str(dd1+1)+'-'+str(dd2+1)+' LT mean every day')
        p.plot(df_obs_dm_3_3_mm.index-dt.timedelta(days=-2), df_obs_dm_3_3_mm['co2']-df_obs_dm_mm['co2'], '-', 
               color=cb[5],label='_nolegend_')
        ax.set_xlim(start_date,end_date)
        ax.set_ylim(-6,6)
        ax.set_ylabel('CO$_2$ deviation  [ppm]')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='upper left',ncol=8)

        ax = fig.add_subplot(5,1,4)
        p.bar(df_obs_dm_std.index-dt.timedelta(days=0), df_obs_dm_std['co2'], color='gray',
              label='afternoon mean every day')
        p.bar(df_var_smallest_std.index-dt.timedelta(days=-4), df_var_smallest_std['co2'], color=cb[0],
              label=str(ddm+1)+' LT smallest var')
        p.bar(df_obs_dm_3_1_std.index-dt.timedelta(days=2), df_obs_dm_3_1_std['co2'], color=cb[7],
              label=str(ddm+1)+' LT every 3th day')
        p.bar(df_obs_dm_3_2_std.index-dt.timedelta(days=0), df_obs_dm_3_2_std['co2'], color=cb[6],
              label=str(ddm+1)+' LT every 3th day')
        p.bar(df_obs_dm_3_3_std.index-dt.timedelta(days=-2), df_obs_dm_3_3_std['co2'], color=cb[5],
              label=str(ddm+1)+' LT every 3th day')
        #p.title(ist)
        ax.set_xlim(start_date,end_date)
        #ax.set_ylim(380,460)
        ax.set_ylabel('standard deviation [ppm]')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='best',ncol=1)

        ax = fig.add_subplot(5,1,5)
        p.bar(df_obs_dm_count.index-dt.timedelta(days=4), df_obs_dm_count['co2'], color='gray',
              label='afternoon mean every day')
        p.bar(df_var_smallest_count.index-dt.timedelta(days=-4), df_var_smallest_count['co2'], color=cb[0],
              label=str(ddm+1)+' LT smallest var')
        p.bar(df_obs_dm_3_1_count.index-dt.timedelta(days=2), df_obs_dm_3_1_count['co2'], color=cb[7],
              label=str(ddm+1)+' LT every 3th day')
        p.bar(df_obs_dm_3_2_count.index-dt.timedelta(days=0), df_obs_dm_3_2_count['co2'], color=cb[6],
              label=str(ddm+1)+' LT every 3th day')
        p.bar(df_obs_dm_3_3_count.index-dt.timedelta(days=-2), df_obs_dm_3_3_count['co2'], color=cb[5],
              label=str(ddm+1)+' LT every 3th day')
        #p.title(ist)
        ax.set_xlim(start_date,end_date)
        #ax.set_ylim(380,460)
        ax.set_ylabel('afternoon values per month')
        ax.grid(axis='x')
        ax.grid(axis='y')
        ax.legend(loc='best',ncol=1)

        ax.text(0.01, -0.24, citation, verticalalignment='top', transform=ax.transAxes)

        p.tight_layout()
        
        #display(HTML('<p style="font-size:12px;"> <br> '+citation+' </p>'))        

        pngfile='sensitivity_ICOS_'+ist+'_'+str(start_date.year)+str(start_date.month).zfill(2)
        fig.savefig(path_plots+pngfile+'.png',dpi=100)
        p.show()
        p.close()

        if summary:
            # print summary        
            display(HTML('<br> <b>afternoon mean every day</b>'))
            display(HTML(df_obs_dm['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))
            display(HTML('<br> <b>'+str(ddm+1)+' LT every 3rd day</b>'))
            display(HTML(df_obs_dm_3_1['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))
            display(HTML('<br> <b>'+str(ddm+1)+' LT every 3rd day</b>'))
            display(HTML(df_obs_dm_3_2['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))
            display(HTML('<br> <b>'+str(ddm+1)+' LT every 3rd day</b>'))
            display(HTML(df_obs_dm_3_3['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))
            display(HTML('<br> <b>'+str(ddm+1)+' LT every 7th day</b>'))
            display(HTML(df_obs_dm_7_1['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))
            display(HTML('<br> <b>'+str(ddm+1)+' LT lowest variability</b>'))
            display(HTML(df_var_smallest['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_html()))

            summary_file=path_plots+ist+'_sensitivity_monthly_ICOS_counts.csv'
            open(summary_file,'w').write(stilt_stations[ist]['icosName']+' {:.0f}'.format(stilt_stations[ist]['icosHeight'])
                                         +' {:.2f}'.format(stilt_stations[ist]['icosLat'])
                                         +' {:.2f}'.format(stilt_stations[ist]['icosLon'])+'\n')
            open(summary_file,'a').write('afternoon mean every day'+'\n')
            df_obs_dm['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
            open(summary_file,'a').write(str(ddm+1)+' LT every 3rd day'+'\n')
            df_obs_dm_3_1['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
            open(summary_file,'a').write(str(ddm+1)+' LT every 3rd day'+'\n')
            df_obs_dm_3_2['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
            open(summary_file,'a').write(str(ddm+1)+' LT every 3rd day'+'\n')
            df_obs_dm_3_3['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
            open(summary_file,'a').write(str(ddm+1)+' LT every 7th day'+'\n')
            df_obs_dm_7_1['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
            open(summary_file,'a').write(str(ddm+1)+' LT lowest variability'+'\n')
            df_var_smallest['co2'].groupby(pd.Grouper(freq='M')).agg(['mean', 'std','count']).to_csv(summary_file,mode='a')
#------------------------------------------------------------------------------------------------------------------

# call all functions for selection of STILT time series, footprints and comparison with ICOS measurement data
def run_all(stilt_stations,station_selection, ystart, mstart, yend, mend, 
            low_stilt, high_stilt, highco_stilt, var_limit_stilt,
            highco_obs, var_limit_obs, stdev_limit_obs, 
            noon_time, midday_range):

    global_start_date = dt.datetime(ystart,mstart,1,0)
    global_end_date = dt.datetime(yend,mend,1,0)
    if (global_start_date > global_end_date):
        global_start_date = global_end_date
    if mend >= 12:
        global_end_date = dt.datetime(yend+1,1,1,0) 
    else:
        global_end_date = dt.datetime(yend,mend+1,1,0) 
    global_end_date = global_end_date - dt.timedelta(hours=1)
    if (global_start_date > global_end_date):
        print('Select Start Date < End Date')
        return
        
    for station in station_selection:

        loc_ident=stilt_stations[station]['locIdent']
        station_lat=stilt_stations[station]['lat']
        station_lon=stilt_stations[station]['lon']
        height = stilt_stations[station]['icosHeight']

        # selection of STILT time series (temporal and concentration thresholds)
        # only for those station for which 1-hourly results are availabe (see dropdown list)
        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Test sampling strategy on 1-hourly STILT time series </p>'))
        all_selection_plots(station,global_start_date,global_end_date,loc_ident,station_lat,station_lon,
                            high_stilt, low_stilt, highco_stilt, var_limit_stilt, noon_time, midday_range, summary=True)

        # read ICOS data from ICOS Carbon Portal
        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Read ICOS observation time series from Carbon Portal </p>'))

        tracer = 'CO2'
        dobj_L2_co2 = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_co2 = read_icos_data(dobj_L2_co2,tracer)
        if not df_co2.loc[global_start_date:global_end_date].empty:
            citation_co2 = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_co2.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_co2 = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))


        tracer = 'CO'
        dobj_L2_co = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_co = read_icos_data(dobj_L2_co,tracer)
        if not df_co.empty:
            df_co['co'] = df_co['co'] / 1000. #convert observed CO from ppb to ppm 
        if not df_co.loc[global_start_date:global_end_date].empty:
            citation_co = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_co.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_co = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))

        tracer = 'MTO'
        dobj_L2_mto = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_mto = read_icos_data(dobj_L2_mto,tracer)
        if not df_mto.loc[global_start_date:global_end_date].empty:
            citation_mto = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_mto.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_mto = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))
        
        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Comparison ICOS observation time series with STILT results </p>'))
        citation=citation_co2+'\n'+citation_co+'\n'+citation_mto
        plot_comparison(station, df_co2, df_co, df_mto, global_start_date,global_end_date, citation=citation)

        if ((len(citation_co2) > 0) & (len(citation_co) > 0)):
            citation=citation_co2+'\n'+citation_co
            # specify start and end date in case you want to analyse the same time period 
            display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Apply selection to ICOS observation time series </p>'))
            plot_icos_ts_selection(station, df_co2, df_co, df_mto,
                                   highco_obs, var_limit_obs, stdev_limit_obs, noon_time, midday_range,
                                   start=global_start_date, end=global_end_date, summary=True, citation=citation)
        
            # if you want plots for the full time series at the ICOS site, use this call
            #plot_icos_ts_selection(station, df_co2, df_co, df_mto,
            #                       highco_obs, var_limit_obs, stdev_limit_obs, citation=citation)
        
        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Sensitivity of selection strategy on monthly mean </p>'))
        # specify start and end date in case you want to analyse the same time period 
        #sensitivity_selection_icos(station, df_co2, df_co, df_mto,
        #                           highco_obs, var_limit_obs, stdev_limit_obs, 
        #                           start=global_start_date, end=global_end_date, summary=True, citation=citation)
        
        # if you want plots for the full time series at the ICOS site, use this call
        sensitivity_selection_icos(station, df_co2, df_co, df_mto,
                                   highco_obs, var_limit_obs, stdev_limit_obs, noon_time, midday_range,
                                   summary=True, citation=citation_co2)
        
#------------------------------------------------------------------------------------------------------------------

# call all functions for selection of ICOS measurement time series
def run_obs(stilt_stations,station_selection, ystart, mstart, yend, mend, 
            highco_obs, var_limit_obs, stdev_limit_obs, 
            noon_time, midday_range):

    global_start_date = dt.datetime(ystart,mstart,1,0)
    global_end_date = dt.datetime(yend,mend,1,0)
    if (global_start_date > global_end_date):
        global_start_date = global_end_date
    if mend >= 12:
        global_end_date = dt.datetime(yend+1,1,1,0) 
    else:
        global_end_date = dt.datetime(yend,mend+1,1,0) 
    global_end_date = global_end_date - dt.timedelta(hours=1)
    if (global_start_date > global_end_date):
        print('Select Start Date < End Date')
        return
        
    for station in station_selection:

        loc_ident=stilt_stations[station]['locIdent']
        station_lat=stilt_stations[station]['lat']
        station_lon=stilt_stations[station]['lon']
        height = stilt_stations[station]['icosHeight']

        # read ICOS data from ICOS Carbon Portal
        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Read ICOS observation time series from Carbon Portal </p>'))

        tracer = 'CO2'
        dobj_L2_co2 = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_co2 = read_icos_data(dobj_L2_co2,tracer)
        if not df_co2.loc[global_start_date:global_end_date].empty:
            citation_co2 = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_co2.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_co2 = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))

        tracer = 'CO'
        dobj_L2_co = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_co = read_icos_data(dobj_L2_co,tracer)
        if not df_co.empty:
            df_co['co'] = df_co['co'] / 1000. #convert observed CO from ppb to ppm 
        if not df_co.loc[global_start_date:global_end_date].empty:
            citation_co = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_co.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_co = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))

        tracer = 'MTO'
        dobj_L2_mto = RunSparql(sparql_query=atc_station_tracer_query(station[0:3], height, tracer, level=2),output_format='pandas').run()
        df_mto = read_icos_data(dobj_L2_mto,tracer)
        if not df_mto.loc[global_start_date:global_end_date].empty:
            citation_mto = RunSparql(sparql_query=sparqls.get_icos_citation(dobj_L2_mto.dobj.iloc[0]), output_format='pandas').run().cit[0]
        else:
            citation_mto = ''
            display(HTML('<p style="font-size:15px;font-weight:bold;color:red;">No ICOS '+tracer+' data available for '
                         +global_start_date.strftime("%Y-%m-%d %H:%M:%S")+' - '+global_end_date.strftime("%Y-%m-%d %H:%M:%S")+'</p>'))
        
        if ((len(citation_co2) > 0) & (len(citation_co) > 0)):
            citation=citation_co2+'\n'+citation_co
            # specify start and end date in case you want to analyse the same time period 
            display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Apply selection to ICOS observation time series </p>'))
            plot_icos_ts_selection(station, df_co2, df_co, df_mto,
                                   highco_obs, var_limit_obs, stdev_limit_obs, noon_time, midday_range, 
                                   start=global_start_date, end=global_end_date, summary=True, citation=citation)
        
            # if you want plots for the full time series at the ICOS site, use this call
            #plot_icos_ts_selection(station, df_co2, df_co, df_mto,
            #                       highco_obs, var_limit_obs, stdev_limit_obs, citation=citation)

        display(HTML('<p style="font-size:20px;font-weight:bold;color:royalblue;"> <br> Sensitivity of selection strategy on monthly mean </p>'))

        #sensitivity_selection_icos(station, df_co2, df_co, df_mto,
        #                           highco_obs, var_limit_obs, stdev_limit_obs, 
        #                           start=global_start_date, end=global_end_date, summary=True)
        
        sensitivity_selection_icos(station, df_co2, df_co, df_mto, 
                                   highco_obs, var_limit_obs, stdev_limit_obs, noon_time, midday_range,
                                   summary=True, citation=citation_co2)        

#------------------------------------------------------------------------------------------------------------------

# create widgets for selection (STILT results + ICOS data)
def create_widget_selection():

    # Read dictionary with all stations available in STILT - for 3-hourly STILT results only
    global stilt_stations
    stilt_stations = create_STILT_dictionary()

    # find stations for which 1-hourly STILT results are available 
    allStations = sorted([stilt_stations[kk]['name'] for kk in os.listdir(path_stilt+'/Results_RINGO_T1.3/')])
    
    #Create a Dropdown widget with station names:
    station = Dropdown(options = allStations,
                       description = 'Station',
                       disabled= False,)
    
    #Create a Dropdown widget with year values (start year):
    s_year = Dropdown(options = [2017, 2018],
                      description = 'Start Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (start month):
    s_month = Dropdown(options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                       description = 'Start Month',
                       disabled= False,)
    
    #Create a Dropdown widget with year values (end year):
    e_year = Dropdown(options = [2017, 2018],
                      description = 'End Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (end month):
    e_month = Dropdown(options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                       description = 'End Month',
                       disabled= False,)
    
    #Create a Button widget to control execution:
    update_button = Button(description='Update',
                           disabled=False,
                           button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)

    #Create a FloatText widget for STILT low fossil fuel CO2 threshold:
    low_stilt = FloatText(value=1.0,
                          description='Low ffCO2',
                          step=0.01,
                          description_long='Click me',
                          disabled=False)

    #Create a FloatText widget for STILT high fossil fuel CO2 threshold:
    high_stilt = FloatText(value=4.0,
                          description='High ffCO2',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget for STILT high CO threshold:
    highco_stilt = FloatText(value=0.04,
                          description='High ffCO',
                          step=0.01,
                          disabled=False)

    #Create a FloatText widget for STILT variability threshold:
    var_stilt = FloatText(value=1.0,
                          description='Var',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget for threshold of high CO in ICOS observation:
    highco_obs = FloatText(value=0.04,
                          description='High CO',
                          step=0.01,
                          disabled=False)

    #Create a FloatText widget for threshold of variability in ICOS observation:
    var_obs = FloatText(value=0.5,
                          description='Var',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget with threshold of variability in ICOS observation:
    stdev_obs = FloatText(value=0.5,
                          description='Stdev',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget for selection of noon hour:
    noon = IntText(value=12,
                description='noon',
                step=1,
                disabled=False)

    #Create a FloatText widget for selection of mid-day time range:
    midday = IntRangeSlider(value=[10, 14],
                             min=6,
                             max=19,
                             step=1,
                             description='Mid-day',
                             disabled=False,
                             orientation='horizontal',
                             readout=True,
                             readout_format='d')

    
    header_station = Output()
    with header_station:
        display(HTML('<p style="font-size:15px;font-weight:bold;color:royalblue;">Select here station and time range: </p>'))

    header_stilt_1 = Output()
    with header_stilt_1:
        display(HTML('<p style="font-size:15px;font-weight:bold;color:royalblue;">Select here thresholds for STILT time series (all thresholds in ppm): </p>'))

    header_stilt_2 = Output()
    with header_stilt_2:
        display(HTML('Select here thresholds for high fossil fuel CO2 and high fossil fuel CO in STILT time series: '))

    header_stilt_3 = Output()
    with header_stilt_3:
        display(HTML('Select here thresholds for low fossil fuel CO2 and low CO2 variability in STILT time series: '))
    
    header_obs_1 = Output()
    with header_obs_1:
        display(HTML('<p style="font-size:15px;font-weight:bold;color:royalblue;">Select here thresholds for ICOS observation time series (all thresholds in ppm): </p>'))

    header_obs_2 = Output()
    with header_obs_2:
        display(HTML('Select here thresholds for high CO in ICOS observation time series: '))

    header_obs_3 = Output()
    with header_obs_3:
        display(HTML('Select here thresholds for low CO2 variability during mid-day (Var) '+
                     'and standard deviation in noon-time measurement (Stdev) <br> '+
                     'in ICOS observation time series: '))

    header_noon_1 = Output()
    with header_noon_1:
        display(HTML('Select here the mid-day time range and noon-time hour (in UTC): '))


    station_box = VBox([header_station,station])
    
    #Create a VBox for year and month:
    year_box = VBox([s_year, e_year])
    month_box = VBox([s_month, e_month])

    #Create a HBox for STILT thresholds:
    var_stilt_box = HBox([low_stilt, var_stilt])
    high_stilt_box = HBox([high_stilt, highco_stilt])

    #Add both time-related VBoxes to a HBox:
    time_box = HBox([year_box, month_box])

    #Create a Vbox for mid-day selection:
    noon_box = HBox([midday,noon])
    noon_box_header = VBox([header_noon_1,noon_box])

    high_stilt_box_header = VBox([header_stilt_2, high_stilt_box])
    var_stilt_box_header = VBox([header_stilt_3, var_stilt_box])
    stilt_box = VBox([header_stilt_1, high_stilt_box_header, var_stilt_box_header])
    
    #Create a HBox for ICOS observation thresholds:
    var_obs_box = HBox([var_obs, stdev_obs])
    high_obs_box = HBox([highco_obs])
    
    high_obs_box_header = VBox([header_obs_2, high_obs_box])
    var_obs_box_header = VBox([header_obs_3, var_obs_box])
    obs_box = VBox([header_obs_1, high_obs_box_header, var_obs_box_header])    
    
    #Add all widgets to a VBox:
    form = VBox([station_box, time_box, noon_box_header, stilt_box, obs_box, update_button])

    #Set font of all widgets in the form:
    station.layout.width = '603px'
    update_button.style.button_color=royal
    time_box.layout.margin = '25px 0px 10px 0px'
    year_box.layout.margin = '0px 0px 0px 0px'
    stilt_box.layout.margin = '25px 0px 0px 0px'
    high_stilt_box_header.layout.margin = '5px 0px 0px 0px'
    var_stilt_box_header.layout.margin = '5px 0px 0px 0px'
    obs_box.layout.margin = '25px 0px 0px 0px'
    update_button.layout.margin = '50px 100px 40px 275px' #top, right, bottom, left

    #Initialize form output:
    form_out = Output()
    
    #Initialize results output:
    results_out = Output()

    
    #Define update function:
    def update_func(button_c):
        
        #Display selection:
        with results_out:
            
            #Clear previous results:
            clear_output()

            display(HTML('<p style="font-size:15px;font-weight:bold;">All plots and tables are also saved in the folder: '+path_plots+'</p><br>'))

            #Print "results" (current selection):
            print('Station: ', station.value)
            print('Start Year: ', s_year.value, '\t Start Month: ', s_month.value)
            print('End Year: ', e_year.value, '\t End Month: ', e_month.value)
            print('Noon: ',noon.value,' UTC', '\t \t Mid-day range: ',midday.value,' UTC')
            print('Threshold for low ffCO2 in STILT: ', low_stilt.value)
            print('Threshold for high ffCO2 in STILT: ', high_stilt.value)
            print('Threshold for high ffCO in STILT: ', highco_stilt.value)
            print('Threshold for low variability in STILT: ', var_stilt.value)
            print('Threshold for high CO in ICOS observations: ', highco_obs.value)
            print('Threshold for low mid-day variability in ICOS CO2 observations: ', var_obs.value)
            print('Threshold for low noon-time standard deviation in ICOS CO2 observations: ', stdev_obs.value)
            station_selection = [key for (key, value) in stilt_stations.items() if value['name'] == station.value]
            run_all(stilt_stations,station_selection, s_year.value, s_month.value, e_year.value, e_month.value, 
                    low_stilt.value, high_stilt.value, highco_stilt.value, var_stilt.value,
                    highco_obs.value, var_obs.value, stdev_obs.value, noon.value, midday.value)

        
    #Call update-function when button is clicked:
    update_button.on_click(update_func)

    
    #Open form object:
    with form_out:
        
        #Clear previous selections in form:
        clear_output()
        
        #Display form and results:
        display(form, results_out)
        
    #Display form:
    display(form_out)

#------------------------------------------------------------------------------------------------------------------
# Create widgets for selection (ICOS data only)
def create_widget_selection_icos():

    # Read dictionary with all stations available in STILT - for 3-hourly STILT results only
    global stilt_stations
    stilt_stations = create_STILT_dictionary()

    # find stations for which 1-hourly STILT results are available 
    allStations = sorted([stilt_stations[kk]['name'] for kk in os.listdir(path_stilt+'/Results_RINGO_T1.3/')])
    
    #Create a Dropdown widget with station names:
    station = Dropdown(options = allStations,
                       description = 'Station',
                       disabled= False,)
    
    #Create a Dropdown widget with year values (start year):
    s_year = Dropdown(options = [2017, 2018, 2019],
                      description = 'Start Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (start month):
    s_month = Dropdown(options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                       description = 'Start Month',
                       disabled= False,)
    
    #Create a Dropdown widget with year values (end year):
    e_year = Dropdown(options = [2017, 2018, 2019],
                      description = 'End Year',
                      disabled= False,)
    
    #Create a Dropdown widget with month values (end month):
    e_month = Dropdown(options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                       description = 'End Month',
                       disabled= False,)
    
    #Create a Button widget to control execution:
    update_button = Button(description='Update',
                           disabled=False,
                           button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                           tooltip='Click me',)
    
    #Create a FloatText widget for threshold of high CO in ICOS observation:
    highco_obs = FloatText(value=0.04,
                          description='High CO',
                          step=0.01,
                          disabled=False)

    #Create a FloatText widget for threshold of variability in ICOS observation:
    var_obs = FloatText(value=0.5,
                          description='Var',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget with threshold of variability in ICOS observation:
    stdev_obs = FloatText(value=0.5,
                          description='Stdev',
                          step=0.01,
                          disabled=False)
    
    #Create a FloatText widget for selection of noon hour:
    noon = IntText(value=12,
                description='noon',
                step=1,
                disabled=False)

    #Create a FloatText widget for selection of mid-day time range:
    midday = IntRangeSlider(value=[10, 14],
                             min=6,
                             max=19,
                             step=1,
                             description='Mid-day',
                             disabled=False,
                             orientation='horizontal',
                             readout=True,
                             readout_format='d')

    header_station = Output()
    with header_station:
        display(HTML('<p style="font-size:15px;font-weight:bold;color:royalblue;">Select here station and time range: </p>'))

    header_obs_1 = Output()
    with header_obs_1:
        display(HTML('<p style="font-size:15px;font-weight:bold;color:royalblue;">Select here thresholds for ICOS observation time series (all thresholds in ppm): </p>'))

    header_obs_2 = Output()
    with header_obs_2:
        display(HTML('Select here thresholds for high CO in ICOS observation time series: '))

    header_obs_3 = Output()
    with header_obs_3:
        display(HTML('Select here thresholds for low CO2 variability during mid-day (Var) '+
                     'and standard deviation in noon-time measurement (Stdev) <br> '+
                     'in ICOS observation time series: '))

    header_noon_1 = Output()
    with header_noon_1:
        display(HTML('Select here the mid-day time range and noon-time hour (in UTC): '))


    station_box = VBox([header_station,station])
    
    #Create a VBox for year and month:
    year_box = VBox([s_year, e_year])
    month_box = VBox([s_month, e_month])

    #Add both time-related VBoxes to a HBox:
    time_box = HBox([year_box, month_box])
    
    #Create a Vbox for mid-day selection:
    noon_box = HBox([midday,noon])
    noon_box_header = VBox([header_noon_1,noon_box])

    #Create a HBox for ICOS observation thresholds:
    var_obs_box = HBox([var_obs, stdev_obs])
    high_obs_box = HBox([highco_obs])
    
    high_obs_box_header = VBox([header_obs_2, high_obs_box])
    var_obs_box_header = VBox([header_obs_3, var_obs_box])
    obs_box = VBox([header_obs_1, high_obs_box_header, var_obs_box_header])    
    
    #Add all widgets to a VBox:
    form = VBox([station_box, time_box, noon_box_header, obs_box, update_button])

    #Set font of all widgets in the form:
    station.layout.width = '603px'
    update_button.style.button_color=royal
    time_box.layout.margin = '25px 0px 10px 0px'
    year_box.layout.margin = '0px 0px 0px 0px'
    obs_box.layout.margin = '25px 0px 0px 0px'
    update_button.layout.margin = '50px 100px 40px 275px' #top, right, bottom, left

    #Initialize form output:
    form_out = Output()
    
    #Initialize results output:
    results_out = Output()

    
    #Define update function:
    def update_func(button_c):
        
        #Display selection:
        with results_out:
            
            #Clear previous results:
            clear_output()

            display(HTML('<p style="font-size:15px;font-weight:bold;">All plots and tables are also saved in the folder: '+path_plots+'</p><br>'))

            #Print "results" (current selection):
            print('Station: ', station.value)
            print('Start Year: ', s_year.value, '\t Start Month: ', s_month.value)
            print('End Year: ', e_year.value, '\t End Month: ', e_month.value)
            print('Noon: ',noon.value,' UTC', '\t \t Mid-day range: ',midday.value,' UTC')
            print('Threshold for high CO in ICOS observations: ', highco_obs.value)
            print('Threshold for low mid-day variability in ICOS CO2 observations: ', var_obs.value)
            print('Threshold for low noon-time standard deviation in ICOS CO2 observations: ', stdev_obs.value)
            station_selection = [key for (key, value) in stilt_stations.items() if value['name'] == station.value]
            run_obs(stilt_stations,station_selection, s_year.value, s_month.value, e_year.value, e_month.value, 
                    highco_obs.value, var_obs.value, stdev_obs.value, noon.value, midday.value)

        
    #Call update-function when button is clicked:
    update_button.on_click(update_func)

    
    #Open form object:
    with form_out:
        
        #Clear previous selections in form:
        clear_output()
        
        #Display form and results:
        display(form, results_out)
        
    #Display form:
    display(form_out)

#------------------------------------------------------------------------------------------------------------------
