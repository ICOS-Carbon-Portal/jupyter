from netCDF4 import Dataset
import os,sys

x = Dataset('CO_10deg_monthly_for_transportcalc_850-1850.nc','r')
eco = x.variables['mCO_flux_fire' ]
for co in eco:
   print co.shape
