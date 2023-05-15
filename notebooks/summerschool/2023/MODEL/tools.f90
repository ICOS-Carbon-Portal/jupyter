subroutine fill_emission_field(emission_field)
use dimension
use input
real,intent(out),dimension(nu,nv,nw) ::emission_field
real    ::emit_box,k
integer ::i,j,ilon,ilat,ipres
character*80 :: line
real         :: e_amount

emission_field = 0.0
if (emission_file) then
   read(unit_emission,*) line
   print *,line
   read(unit_emission,*) emission_field(:,:,1)
   emission_field(:,:,1) = emission_field(:,:,1)*dtim   !mr change / timestep
endif
if (e_land + e_sea + e_snow.gt.0.0) then
do j=1,nv
do i=1,nu
   !emit_box = (1.-asland(i,j))*e_sea + asland(i,j)*((1.-snow(i,j))*e_land + snow(i,j)*e_snow)  !#/cm2/s
   emit_box = (1.-asland(i,j))*e_sea + asland(i,j)*e_land !#/cm2/s
   emit_box = emit_box*1e4*dtim   !#/m2/timestep
   emission_field(i,j,1) = emission_field(i,j,1) + emit_box/(air(i,j,1)*dthick(i,j,1)*1e6)  !delta mixing-ratio/timestep
enddo
enddo
endif
if (pointsource) then
do i=1,n_point
   ilon = c_point(i,1)
   ilat = c_point(i,2)
   ipres = c_point(i,3)
   if(ipres.ne.1) off_surface = .true.
   emit_box = s_point(i)*1e4*dtim/(air(ilon,ilat,ipres)*dthick(ilon,ilat,ipres)*1e6)
   emission_field(ilon,ilat,ipres) =  emission_field(ilon,ilat,ipres) + emit_box
enddo
endif
if (chemistry_emission) then
  ! print*,ae_factor,be_factor,temp(9,9,1),conc_chem,dtim
  ! print*,OH(9,9,1)*air(9,9,1)*1e-9
   do l=1,nw
   do j=1,nv
   do i=1,nu
      off_surface = .true.
      k = ae_factor*exp(be_factor/(temp(i,j,l)+TK0))        ! in cm3/(s #)
      emit_box = k*conc_chem*1e-9*air(i,j,l)*oh(i,j,l)*1e-9*dtim   ! in mixing ratio / timestep
      emission_field(i,j,l) =  emission_field(i,j,l) + emit_box
      totch4 = totch4 + emit_box*air(i,j,l)/AVO*1e6*ar(i,j,l)*16.0e-12*12*30    ! in Tg/month
   enddo
   enddo
   enddo
endif
if (emission_distribution) then 
   do i=1,n_year_emit
      if(i_year_emit(i) .eq. iyear) exit
   enddo
   if (i.gt.n_year_emit) call stopit('No emission amount found for this year')
   e_amount = emit_year(i)*1.e9*dtim/3.1104e7   !kt/yr-->gram/timestep
   e_amount = e_amount*XMAIR/XMASS(1)           !gram air / timestep
   do j=1,nv
   do i=1,nu
      emit_box = emission_dist(i,j)*e_amount/ar(i,j,1)/rhom(i,j,1)    !mixing ratio change / timestep
      emission_field(i,j,1) = emission_field(i,j,1) + emit_box
   enddo
   enddo
endif
end 

subroutine fill_sink_field(sink)
use dimension
use input
real,intent(out),dimension(nu,nv,nw) ::sink    ! tr = tr - sink (sink is positively defined)
real,dimension(nu,nv)                ::sinke   ! extra sink over land
real,dimension(nv)                   ::dxyp
integer ::i,j
character*80 :: line

sink = 0.0
sinke = 0.0
if (sink_flag) then
   if (abs(co2_land_sink) > tiny(co2_land_sink)) then
      read(unit_sinke,*) line
      print *,line
      read(unit_sinke,*) sinke   ! land sink in mol/m2/s
      sinke = sinke*co2_land_sink   ! convert to right sink strength
   endif
   read(unit_sink,*) line
   print *,line
   read(unit_sink,*) sink(:,:,1)   ! mol/m2/s
   do j=1,nv
   do i=1,nu
      sink(i,j,1) = dtim*(sink(i,j,1)+sinke(i,j))*avo/(air(i,j,1)*dthick(i,j,1)*1e6)  !delta mixing-ratio/timestep
   enddo
   enddo
endif
end subroutine fill_sink_field

subroutine area(im,jm,dxyp)
    implicit none
    integer, intent(in) :: im,jm
    real,dimension(jm), intent(out)  :: dxyp
    real    :: radius = 6371000.
    real    :: grav   = 9.80665
    real    :: pi = 3.1415926535897931
    real    :: dx,dy,gtor,dxx,dyy,lat
    integer :: j
    dx = 360./im
    dy = 180./jm
    radius=6371000.
    grav = 9.80665
    gtor = pi/180.0
    dxx = dx*gtor
    dyy = dy*gtor
    lat = -90.0*gtor
    do j = 1,jm
      dxyp(j) = dxx*(sin(lat+dyy)-sin(lat))*radius**2.0
      lat = lat + dyy
    enddo
    !print *, 'global area',4*pi*radius**2.0
    !print *, 'area ',sum(dxyp)*im
end subroutine area


subroutine calc_chemistry(chem_loss)
use dimension
use units
use input
implicit none
real,intent(out),dimension(nu,nv,nw) ::chem_loss
integer  ::i,j,l
real     ::k,loss

call lees(OH,nu2*nv*nw,unit_oh,0)

do i=1,nu
do j=1,nv
do l=1,nw
  k = a_factor*exp(b_factor/(temp(i,j,l)+TK0))*(1.0+c_factor*(11-l))   !in cm3/#s
  loss = k*OH(i,j,l)*1e-9*air(i,j,l)           !in 1/s  (OH was in ppb)
  chem_loss(i,j,l) = exp(-dtim*loss)
enddo
enddo
enddo
end

subroutine startc(a,n1,c)
implicit none
integer,intent(in)  :: n1
real,dimension(n1)  :: a
real,intent(in)     :: c
a=c
end
      subroutine lees(a,n,unit,iprint)
      implicit none
      integer n,unit,iprint
      character*60 text
      real a(n)
      real max,min,r999
      integer nel,i
      integer,dimension(:),allocatable  :: index
      allocate(index(n))
      read(unit,'(a)') text
      if (iprint.eq.1)  print *,'LEES:',text
      read(unit,*) max,min,nel
      if (iprint.eq.1)  print *,'LEES:',max,min,nel
      if (nel.eq.n) then
	read(unit,'(20i3)') (index(i),i=1,n)
      else
	 print *,'DIMENSION WRONG IN LEES'
	 stop 'LEES ERROR'
      endif
      r999=(max-min)/999.
      a=min+index*r999
      deallocate(index)
      end
      subroutine schrijf(a,n,unit,iprint,text)
      implicit none
      integer,dimension(:),allocatable :: index
      integer n,unit,iprint
      character*60 text
      integer i
      real a(n)
      real max,min,r999
      allocate(index(n))
      write(unit,'(a)') text
      if (iprint.eq.1)  print *,'SCHRIJF:',text
      max = maxval(a)
      min = minval(a)
      write(unit,*) max,min,n
      if (iprint.eq.1)  print *,'SCHRIJF:',max,min,n
      index=nint((a-min)*999/(max-min))
      write(unit,'(20i3)') (index(i),i=1,n)
      deallocate(index)
      end
      subroutine schrijf_r4(a,n,unit,iprint,text)
      implicit none
      integer,dimension(:),allocatable :: index
      integer n,unit,iprint
      character*60 text
      integer i
      real*4 a(n)
      real*4 max,min,r999
      allocate(index(n))
      write(unit,'(a)') text
      if (iprint.eq.1)  print *,'SCHRIJF:',text
      max = maxval(a)
      min = minval(a)
      write(unit,*) max,min,n
      if (iprint.eq.1)  print *,'SCHRIJF:',max,min,n
      index=nint((a-min)*999/(max-min))
      write(unit,'(20i3)') (index(i),i=1,n)
      deallocate(index)
      end
      subroutine read_emis_field(ipos,emission_field)
      use dimension
      use units
      use hdf
      implicit none
      real,intent(out),dimension(nu,nv,nw) ::emission_field
      integer,intent(in) :: ipos
      integer            :: sffinfo,sfselect,sfginfo,sfrdata,sfendacc
      integer            :: im,jm,sd_id
      integer            :: rank = 2    ,istat
      integer            :: sds_id,ndatasets, nglobat, i, xrank, xtype, natt, j
      integer,dimension(10) :: dimsizes
      character(len=40)     :: dsname
      real,dimension(nu,nv) :: data
      real, parameter       :: tf = htim/(3600*24.*30)
      print *, ipos, '.....ipos'
      istat  = sffinfo(iemis, ndatasets, nglobat)
      !print*, 'sffinfo returns #datasets #attributes',ndatasets,nglobat
      emission_field = 0.0
      do i=0,ndatasets-1
          sds_id = sfselect(iemis,i)
          istat  = sfginfo(sds_id,dsname,xrank,dimsizes,xtype,natt)
          !print*,'sfginfo returns',istat,dsname,xrank,dimsizes
          if ( trim(dsname) .eq. 'mCO_flux_fire' ) then 
             istat= sfrdata(sds_id,(/0,0,ipos-1/),(/1,1,1/),(/nu,nv,1/),data)
             print *, 'istat = ', istat, sum(data)
             istat = sfendacc(sds_id)
             ! gC/m2 month  ---> mr / timestep, swap NP-->SP
             !  gC/m2 month * tf (dtim/(3600*24*30)) --> gC/m2 timestep
             !  gC/m2 timestep / 12.0  ---> moles CO / (m2 timestep)
             !  moles CO/(m2 timestep)  / (g air /m3  * m) ---> moles CO/(g air timestep)
             !  moles CO/(g air timestep)*xmair ---> mixing ratio / timestep
 
             do j=1,18 
             emission_field(:,j,1)  =  &
               data(:,19-j)*tf*(xmair/12.0)/(rhom(1:36,j,1)*dthick(:,j,1))
             enddo
             exit
          endif
          istat = sfendacc(sds_id)
      enddo
      end
      
