      module units
      implicit none 
!cmk      integer,parameter   ::imeteo = 39,iconvection=40,iasland=41,imassflux=42,i_fileswritten=43,unit_station=44
      integer,parameter   ::iasland=41,i_fileswritten=43,unit_station=44
      integer,parameter   ::unit_oh = 45,unit_emission=46,unit_dummy=27,unit_sink=47,unit_sinke=48
      integer             ::imeteo,iconvection,iemis
      contains

      subroutine ZOPEN 
      use dimension
      use hdf 
      implicit none
      integer ::i,sfstart

!cmk      open(unit = imeteo, file = path//'meteo.bin', form = 'unformatted', status = 'old')
!cmk      open(unit = iasland, file = path//'asland.bin', form = 'unformatted', status = 'old')
      imeteo = sfstart(path//'meteo.hdf',DFACC_READ)
      iconvection = sfstart(path//'convection.hdf',DFACC_READ)
!cmk      open(unit = iconvection, file = path//'convection.bin', form = 'unformatted', status = 'old')
!cmk      open(unit = imassflux, file = path//'massfluxes.bin', form = 'unformatted', status = 'old')
      end subroutine zopen

      end module units
