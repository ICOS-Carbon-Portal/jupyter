module dimension
implicit none

! to adapt with implimentation
 character(len=47)  :: path = '/home/jovyan/education/Summer-school-2023/DATA/'
 character(len=61)  :: outpath = '/home/jovyan/education/Summer-school-2023/build/MODEL/OUTPUT/'

 integer, parameter :: nu = 36, nv = 18, nw = 10, nu2 = 37 
 integer, parameter :: nl = 36, np = 18, nr = 10, nl1 = 37
 integer, parameter :: nw1 = 36, nw2 = 18, nw3 = 10

 real,dimension(nr),parameter         ::ra = (/ 1000.,900.,800.,700.,600.,500.,400.,300.,200.,100.  /)

 integer, parameter :: nspecies = 1, nlong = 1, nshort = nspecies-nlong

 real,dimension(nl1,np,nr,nspecies)   :: tr = 0.0  !the tracers (both transported and non-transported
 character(len=8),dimension(nspecies) :: xname  = (/ 'Tracer' /)
 real,dimension(nspecies)             :: xmass  =  (/ 28.5 /)

! meteo information  (read in each month)

 real,dimension(nu,nv,nw)             ::z        !height of the levels (m)
 real,dimension(nu,nv,nw)             ::dz       !differences is level-heights (m)
 real,dimension(nu,nv,nw)             ::dthick   !thickness of layer (m)
 real,dimension(nu2,nv,nw)            ::temp     !temperature (C) 
 real,dimension(nu2,nv,nw)            ::rhom     !density     (g/m^3)
 real,dimension(nu2,nv,nw)            ::air      !density     (#/cm^3)
 real,dimension(nu,nv,nw)             ::ar       !volume      (m^3)
 real,dimension(nu,nv,nw)             ::h2o      !volume mixing ration of water vapor
 real,dimension(nu,nv,nw)             ::satur    !saturation vapor pressure ???

! land fraction, etc.

 real,dimension(nl,np)                ::asland   !landfraction
 integer,dimension(nl1,np)            ::ioro     !orography (set to 1 normally)
 real,dimension(nl1,np)               ::poro     !orography >>>??? 
 integer,dimension(nl ,np)            ::itropo   !tropopause level (set to nw normally)
 real,dimension(nr)                   ::zra      !average height (m)
 real,dimension(nl,np)                ::snow     !monthly varying snowcover. 1 means that all land is covered!!, 0: not!
 real,dimension(nl,np)                ::azkbl    !k-diffusivity Boundary layer (m2/s) ??
 real,dimension(nl,np)                ::precip   !precipitation (???)
 real,dimension(np,nr)                ::rainlay  !distribution of precipitation

! model time

 integer     :: iyear,imon,iday,ihour,itim 

 integer, parameter:: dtim = 7200    !integer timestep in seconds
 real, parameter   :: htim = 7200.0  !real timestep in seconds
 real, parameter   :: xmair = 28.5   !mol-mass of air
 real, parameter   :: a = 6371000.   !radius earth in m
 real, parameter   :: tk0 = 273.15   !temperuture in K for 0 Celsius
 real, parameter   :: gam = 0.006    !???
 real, parameter   :: g = 9.81       !gravity constant (m/s^2)
 real, parameter   :: rw0 = 287.05   !gas-constant in ???
 real, parameter   :: pi  = 3.141592654 
 real, parameter   :: avo = 6.02217e23  !#molecules/mol
 real, parameter   :: xmn = 14.0, xmo = 16.0, xmc = 12.0, xmh = 1.01  !mol-mass atoms (not used??)
 real, parameter   :: xmh2o = 18.02     !mol mass water (g)

end module dimension
