from Nio import *
x = open_file('CO_10deg_monthly_for_transportcalc_850-1850_032014.nc','r')
lon = x.variables['lon'][:]
lat = x.variables['lat'][:]
time = x.variables['time'][:]
co = x.variables['mCO_flux_fire'][:]
xo = open_file('CO_10deg_monthly_for_transportcalc_850-1850.hdf','c')
xo.create_dimension('lon',lon.size)
xo.create_dimension('lat',lat.size)
xo.create_dimension('time',time.size)
xo.create_variable('lon','d',('lon',))
xo.create_variable('lat','d',('lat',))
xo.create_variable('time','i',('time',))
xo.create_variable('mCO_flux_fire','f',('time','lat','lon'))
xo.variables['lon'][:] = lon
xo.variables['lat'][:] = lat
xo.variables['time'][:] = time
xo.variables['mCO_flux_fire'][:] = co
xo.variables['mCO_flux_fire'].description = "CO released by biomass burned"
xo.variables['mCO_flux_fire'].units = 'gC/m2'
x.close()
xo.close()



