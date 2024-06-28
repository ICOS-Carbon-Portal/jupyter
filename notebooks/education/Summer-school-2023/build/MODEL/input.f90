module input
use dimension
use units
implicit none
character(len=60) ::inputfile
integer           ::iostat
character(len=40) ::title='Tracer'
integer           ::iyear_start,imon_start,iday_start
integer           ::iyear_end,imon_end,iday_end
real              ::e_land=0.0,e_sea=0.0,e_snow=0.0
real              ::mol_mass_tracer = 28.5
real              ::lifetime = -1.0   !infinit 
logical           ::sink_flag = .false.
character(len=8)  ::name_tracer = 'Tracer'
real              ::start_conc = -1.0
real,dimension(3) ::co2_land_sink = (/0.0,0.0,0.0/)   ! in PgC/yr
logical           ::convection_flag = .true.
logical           ::o_zama = .false.
logical           ::o_llma = .false.
logical           ::o_zada = .false.
logical           ::o_zaya = .false.
logical           ::concentration_fixer = .false.
logical           ::pointsource = .false.
logical           ::off_surface = .false.
logical           ::chemistry = .false.
logical           ::emission_file = .false.
logical           ::emission_file_hdf = .false.
logical           ::emission_distribution = .false.
logical           ::chemistry_emission = .false.
real,dimension(nu,nv)    :: emission_dist
real                     :: suma
integer                  :: n_year_emit
integer,dimension(100)   :: i_year_emit
real,dimension(100)      :: emit_year  !in kt / yr
real,dimension(nv,nw)    :: zama=0.0,zaya=0.0,zada=0.0
real,dimension(nu,nv,10) :: llma=0.0
integer               :: n_zama=0,n_zaya=0,n_zada=0,n_llma=0
integer               :: n_station = 0, station_output = 1
real,dimension(100)   :: conc_station = 0.0
integer               :: station_output_counter = 0
integer,dimension(100,3) :: station_c = 0
integer               :: n_point = 0, n_conc=0
integer,dimension(100,3) :: c_point = 0, c_conc = 0
real,dimension(100)   :: s_point = 0.0, s_conc = 0.0
character(len=20),dimension(100) ::station_name = ' '
integer               :: n_latlon=0
integer,dimension(10) :: level_ll=0
real                  :: ae_factor = 0.0 , be_factor = 0.0, conc_chem = 0.0, totch4 = 0.0
real                  :: a_factor = 0.0, b_factor = 0.0   !for rate constant chemistry
real                  :: c_factor = 0.0       ! rate = a exp (b/T) *(1+c*(11-k)) with k = level
real, dimension(nu2,nv,nw) :: OH

contains
  
subroutine get_input
use hdf
use units
implicit none
character(len=133) ::line
character(len=60)  ::word
integer            ::istat,iend,sfstart
logical            ::o_monthly,o_daily,o_yearly,o_za,o_latlon
integer            ::i,ilon,ilat,ipos,ipres
open(unit=7,file=outpath//'input_read',status='unknown')
!print*,'Give input file name (in the MOGUNTIA_IN folder)'
!read(*,*) inputfile
!open(unit=5,file='HD:MOGUNTIA_IN:'//inputfile,iostat=iostat,status='OLD')
!print*,'iostat',iostat
!print*,'inputfile name:',inputfile
!if(iostat.eq.2) call stopit('This input file does not exist')

do
  read(5,'(a)',end=999) line
  if (line(1:1).eq.' ') cycle   !inactivated line
  call get_word(line,word,iend)
  select case(word)
      case('END')
         write(7,*) 'END'
         exit
      case('TITLE')
         call get_word(line,word,iend)
         title = word
         close(i_fileswritten)
         open(unit = i_fileswritten, file = outpath//trim(title)//'files_written',form='formatted',status='unknown')
         write(7,*) 'TITLE  ',title
         close(7)
         open(unit=7,file=outpath//trim(title)//'input_read',status='unknown')
      case('CONVECTION')
         call get_word(line,word,iend)
         if(word.eq.'NO'.or.word.eq.'OFF') convection_flag = .false.
         write(7,*) 'CONVECTION  ',convection_flag
      case('NAME')
         call get_word(line,word,iend)
         name_tracer = word(1:8)
         xname(1) = name_tracer
         write(7,*) 'NAME  ',name_tracer
      case('START_DATE')
         call get_word(line,word,iend)
         read(word,'(i4.4,2i2.2)') iyear_start,imon_start,iday_start
         write(7,*) 'START_DATE',iyear_start,imon_start,iday_start
      case('END_DATE')
         call get_word(line,word,iend)
         read(word,'(i4.4,2i2.2)') iyear_end,imon_end,iday_end
         write(7,*) 'END_DATE',iyear_end,imon_end,iday_end
      case('EMISSION')
         emitloop: do
         call get_word(line,word,iend)
         select case(word)
                case('OH')
                  call get_word(line,word,iend)
                  chemistry_emission = .true.
                  read(line,*) conc_chem, ae_factor, be_factor
                  WRITE(7,*) 'EMISSION OH ',word,conc_chem,ae_factor,be_factor 
                  exit emitloop
                case('FILE')
                  call get_word(line,word,iend)
                  emission_file = .true.
                  open(unit_emission,file = path//word, form = 'formatted', status = 'old')
                  exit emitloop
                case('FILE_HDF')
                  call get_word(line,word,iend)
                  emission_file_hdf = .true.
                  iemis = sfstart(path//word,DFACC_READ)
                  print *, 'FILE opened for emissions:', iemis
                  exit emitloop
                case('LAND')
                  call get_word(line,word,iend)
                  read(word,*) e_land
                  write(7,*) 'EMISSION land',e_land
                case('SEA')
                  call get_word(line,word,iend)
                  read(word,*) e_sea
                  write(7,*) 'EMISSION sea ',e_sea
                case('SNOW')
                  call get_word(line,word,iend)
                  read(word,*) e_snow
                  write(7,*) 'EMISSION snow',e_snow
                case('DISTRIBUTION')
                  call get_word(line,word,iend)
                  emission_distribution = .true.
                  open(unit_dummy,file=path//word, form='formatted', status='old')
                  read(unit_dummy,*) emission_dist
                  suma=sum(emission_dist)
                  if(abs(suma-1.).gt.0.1) call stopit('Sum of the emission distribution differs from 1')
                  close(unit_dummy)
                  write(7,*) 'EMISSION DISTRIBUTION '//word
                  call get_word(line,word,iend)
                  read(word,*) n_year_emit
                  if(n_year_emit.gt.100) call stopit('More than 100 years of emissions not allowed')
                  write(7,*) 'Number of years: ',n_year_emit
                  do i=1,n_year_emit
                     read(5,*) i_year_emit(i),emit_year(i)
                     write(7,*)  i_year_emit(i),emit_year(i)
                  enddo
                case(' ')
                  exit
                case('POINT')
                  pointsource=.true.
                  n_point = n_point+1
                  if(n_point.gt.100) call stopit( 'Too many point sources defined ***ERROR***')
                  call get_word(line,word,iend)
                  read(word,*) s_point(n_point)
                  call get_coord(line,ilon,ilat,ipres)
                  c_point(n_point,1) = ilon
                  c_point(n_point,2) = ilat
                  c_point(n_point,3) = ipres
                case default
                  if(word(1:1).ne.'!')then
                     print*,word//line
                     print*,'EMIS...Unrecognized word in input line ******WARNING*******'
                  endif
                  exit
         end select      
         enddo emitloop
      case('SINK')
         sinkloop: do
         call get_word(line,word,iend)
         !print *, 'word:',word
         select case(word)
                case('FILE')
                  call get_word(line,word,iend)
                  sink_flag = .true.
                  open(unit_sink,file = path//word, form = 'formatted', status = 'old')
                  write(7,*) 'SINK FILE '//path//word
                  open(unit_sinke,file = path//'co2_sink_bio1Pg.dat', form = 'formatted', status = 'old')
                  exit sinkloop
                case('EXTRA_LAND')
                  call get_word(line,word,iend)
                  read(word,*) co2_land_sink(1)
                  co2_land_sink(2) = co2_land_sink(1)
                  co2_land_sink(3) = co2_land_sink(1)
                  write(7,*) 'SINK STRENGTH GLOBAL ',co2_land_sink(1)
                case('EXTRA_LAND_SH')
                  call get_word(line,word,iend)
                  open(unit_sinke,file = path//'co2_sink_bio1Pg.dat', form = 'formatted', status = 'old')
                  read(word,*) co2_land_sink(3)
                  write(7,*) 'SINK STRENGTH SH ',co2_land_sink(3)
                case('EXTRA_LAND_NH')
                  call get_word(line,word,iend)
                  read(word,*) co2_land_sink(1)
                  write(7,*) 'SINK STRENGTH NH ',co2_land_sink(1)
                case('EXTRA_LAND_TR')
                  call get_word(line,word,iend)
                  read(word,*) co2_land_sink(2)
                  write(7,*) 'SINK STRENGTH TR ',co2_land_sink(2)
                case(' ')
                  exit
                case default
                  if(word(1:1).ne.'!')then
                     print*,word//line
                     print*,'Unrecognized word in input line ******WARNING*******'
                  endif
                  exit
         end select      
         enddo sinkloop
      case('MOLMASS')
         call get_word(line,word,iend)
         read(word,*) mol_mass_tracer
         write(7,*) 'MOLMASS  ',mol_mass_tracer
      case('STATION_OUTPUT')
         call get_word(line,word,iend)
         select case(word)
                case('STEP')
                   station_output = 1
                case('DAILY')
                   station_output = 12
                case('MONTHLY')
                   station_output = 360
                case default
                   read(word,*) station_output 
         end select
         write(7,*) 'STATION_OUTPUT', station_output
      case('CONCENTRATION')
         concentration_fixer = .true.
         n_conc = n_conc+1
         if(n_conc.gt.100) call stopit( 'Too many fixed concentrations defined ***ERROR***')
         call get_word(line,word,iend)
         read(word,*) s_conc(n_conc)
         call get_coord(line,ilon,ilat,ipres)
         c_conc(n_conc,1) = ilon
         c_conc(n_conc,2) = ilat
         c_conc(n_conc,3) = ipres
         write(7,*) 'Fixed concentration ',n_conc,s_conc(n_conc),c_conc(n_conc,:)
         s_conc(n_conc) = s_conc(n_conc)*1e-9
      case('STATION')
         n_station = n_station+1
         if(n_station.gt.100) call stopit( 'Too many stations defined ***ERROR***')
         call get_word(line,word,iend)
      
         station_name(n_station) = word(1:20) 
         if (word.eq.'NH_MEAN') then
           station_c(n_station,1) = -1
           station_c(n_station,2) = -1
           station_c(n_station,3) = -1
           write(7,*) 'STATION NH_MEAN'
         else if (word.eq.'SH_MEAN') then
           station_c(n_station,1) = -2
           station_c(n_station,2) = -2
           station_c(n_station,3) = -2
           write(7,*) 'STATION SH_MEAN'
         else
           call get_coord(line,ilon,ilat,ipres)
           station_c(n_station,1) = ilon
           station_c(n_station,2) = ilat
           station_c(n_station,3) = ipres
           write(7,*) 'STATION ',n_station,station_name(n_station),station_c(n_station,:)
         
         endif
      case('LIFE_TIME')
         call get_word(line,word,iend)
         read(word,*) lifetime
         write(7,*) 'LIFE_TIME  ',lifetime
      case('CHEMISTRY')
         call get_word(line,word,iend)
         if(word.ne.'OH') print*,'CHEMISTRY option not recognised *****WARNING*****'
         open(unit_oh,file = path//'ohfields.dat',form='formatted',status = 'old')
         chemistry = .true.
         read(line,*) a_factor, b_factor 
         ipos = index(line,'PRESSURE')
         if (ipos.gt.0) read(line(ipos+8:),*) c_factor
         write(7,*) 'CHEMISTRY OH ',a_factor,b_factor,c_factor
      case('START_CONCENTRATION')
         call get_word(line,word,iend)
         if(word.eq.'PREVIOUS') then
           open(unit=106,file=outpath//'previous.bin',form = 'unformatted', status = 'old')
           read(106) tr
           close(106)
           write(7,*) 'START_CONCENTRATION PREVIOUS'
         else
           read(word,*) start_conc
           write(7,*) 'START_CONCENTRATION',start_conc
           call startc(tr,nu2*nv*nw*nspecies,start_conc*1e-9)
         endif
      case('OUTPUT')
         o_monthly = .false.
         o_yearly  = .false.
         o_daily   = .false.
         o_za      = .false.
         o_latlon  = .false.
         call get_word(line,word,iend)     
         select case(WORD)
                case('DAILY')
            call stopit( 'not implemented yet')
                case('MONTHLY')
                  o_monthly = .true.    
                case('YEARLY')
            call stopit( 'not implemented yet')
                case default
                    print*,word
                    call stopit( 'word not recognized')
         end select
         call get_word(line,word,iend)     
         select case(WORD)
                case('ZONAL_AVERAGE')
                    o_za = .true.
                case('LATLON')
                    call get_word(line,word,iend)     
                    ipos=index(word,'HPA')
                    if(ipos.le.0) then
                      print*,word//' not recognised'
                      call stopit( 'ERROR in input')
                    endif 
                    read(word(1:ipos-1),*) ipres
                    o_latlon = .true.
                    ipres = 1000-ipres
                    ipres = MAX(1,MIN((ipres+150)/100,10))
                case DEFAULT
                    print*,word//line,' NOT IMPLEMENTED warning******'
         end select
         if(o_monthly.and.o_za) then
            o_zama = .true.
            write(7,*)  'OUTPUT MONTHLY ZONAL_AVERAGE',o_zama
         endif
         if(o_monthly.and.o_latlon) then
            n_latlon = n_latlon+1
            level_ll(n_latlon) = ipres
            o_llma = .true.
            write(7,*)  'OUTPUT MONTHLY LATLON level',ipres
         endif
      case(' ')
         exit
      case default
         print*,word//line
         print*,'...Unrecognized word in input line *******WARNING*******'
  end select     
enddo
999 continue

! check consistency of the input
 
if (imon_start.lt.1.or.imon_end.lt.1.or.iday_start.lt.1.or.iday_end.lt.1) then
   print*,'day/month < 1'
   print*,iday_start,iday_end,imon_start,imon_end
   call stopit( 'ERROR')
endif
if (imon_start.gt.12.or.imon_end.gt.12) then 
   print*,'start/end month > 12',imon_start,imon_end
   call stopit( 'ERROR')
endif
if (iday_start.gt.30) then
  print*,'iday_start set to 30    ****warning*****'
  iday_start = 30
endif
if (iday_end.gt.30) then
  print*,'iday_end set to 30    ****warning*****'
  iday_end = 30
endif
if (iyear_end-iyear_start.ge.1001) then
   print*,'Maximum simulation lasts 1001 years: split up runs'
   call stopit( 'ERROR')
endif
if (mol_mass_tracer.lt.1e-5) then
   print*,'Tracer mol mass too small',mol_mass_tracer
   call stopit( 'ERROR')
endif
if (e_land.lt.0.0.or.e_sea.lt.0.0.or.e_snow.lt.0.0) then
   print*,'Emission should be positive',e_land,e_sea,e_snow
   call stopit( 'ERROR')
endif
do i=1,n_station
  if(station_c(i,1).eq.0.or.station_c(i,2).eq.0) then
   print*,'Station not properly defined'
   call stopit( 'ERROR')
  endif
enddo
do i=1,n_point
  if(c_point(i,1).eq.0.or.c_point(i,2).eq.0) then
   print*,'Point source',i,' not properly defined'
   call stopit( 'ERROR')
  endif
enddo
do i=1,n_conc
  if(c_conc(i,1).eq.0.or.c_conc(i,2).eq.0) then
   print*,'Fixed concentration ',i,' not properly defined'
   call stopit( 'ERROR')
  endif
enddo
if(n_station.gt.0) then 
   open(unit = unit_station,file = outpath//trim(title)//'.stations',form = 'formatted',status='unknown')
   write(unit_station,*) n_station, station_output
   do i=1,n_station
      write(unit_station,'(A,3i3)') station_name(i),station_c(i,:)
   enddo
   write( i_fileswritten,'(a)') trim(title)//'.stations'
endif
if(n_point.gt.0) then
   do i=1,n_point
      write(7,*) 'Point_source:',i,s_point(i),c_point(i,:)
   enddo
endif
close(7)
 
end subroutine get_input

subroutine output_average
implicit none
integer  ::j,l,i,ipres
if(o_zama) then
   n_zama = n_zama+1
   do l=1,nw
   do j=1,nv
      zama(j,l) = zama(j,l) + sum(tr(1:nu,j,l,1))/nu
   enddo
   enddo
endif
if(o_llma) then
   n_llma = n_llma+1
   do i=1,n_latlon
   ipres = level_ll(i)
   do l=1,nv
   do j=1,nu
      llma(j,l,ipres) = llma(j,l,ipres) + tr(j,l,ipres,1)
   enddo
   enddo
   enddo
endif
if (n_station.ge.1) then
  station_output_counter = station_output_counter + 1
  do i=1,n_station
     if (station_c(i,1).gt.0) then 
         conc_station(i) = conc_station(i) + tr(station_c(i,1), station_c(i,2), station_c(i,3), 1)
     else if(station_c(i,1).eq.-1) then
         conc_station(i) = conc_station(i) + sum(air(1:36,1:9,1:10)*tr(1:36,1:9,1:10,1)*ar(1:36,1:9,1:10)) &
            /sum(air(1:36,1:9,1:10)*ar(1:36,1:9,1:10))
     else 
         conc_station(i) = conc_station(i) + sum(air(1:36,10:18,1:10)*tr(1:36,10:18,1:10,1)*ar(1:36,10:18,1:10)) &
            /sum(air(1:36,10:18,1:10)*ar(1:36,10:18,1:10))   
     endif 
  enddo
  if(station_output_counter .eq. station_output) then
      !WP! write(unit_station,'(5ES14.4)') (conc_station(i)/station_output,i=1,n_station)
      write(unit_station,*) (conc_station(i)/station_output,i=1,n_station)
      station_output_counter = 0
      conc_station(1:n_station) = 0.0
  endif
endif
  
end subroutine output_average

subroutine output_write_monthly
implicit none
character(len=80) ::file
character(len=7)  ::ym
integer           ::i

if(o_zama) then
  write(ym,'(i4.4,a1,i2.2)') iyear,'_',imon
  file = outpath//trim(title)//'za.'//ym
  write(i_fileswritten,'(A)') trim(title)//'za.'//ym
  open(unit=106,file=file,form='formatted',status='unknown')
  write(106,*) zama/max(n_zama,1)
  close(106)
  zama = 0.0
  n_zama = 0
endif
if(o_llma) then
  write(ym,'(i4.4,a1,i2.2)') iyear,'_',imon
  file = outpath//trim(title)//'ll.'//ym
  write(i_fileswritten,'(A)') trim(title)//'ll.'//ym
  open(unit=106,file=file,form='formatted',status='unknown')
  write(106,*) n_latlon
  do i=1,n_latlon
    write(106,*) level_ll(i)
    write(106,*) llma(:,:,level_ll(i))/(max(n_llma,1))
  enddo
  close(106)
  llma = 0.0
  n_llma = 0
endif
end subroutine output_write_monthly

end module input

subroutine get_word(rstring,rword,iend)
implicit none
character(len=*),intent(inout)        ::rstring
character(len=*),intent(out)          ::rword
integer,intent(out)                   ::iend
integer                               ::i,j
rstring = adjustl(rstring)
i = len_trim(rstring)
if (i.eq.0) then
   rword = ' '
   iend = 1
else   
   j = index(rstring,' ')
   if (j.gt.60) call stopit( ' word > 40 in get_word')
   rword = rstring(1:j)
   rstring = rstring(j+1:)
   iend = 0
endif   
!print *, rstring,rword
end subroutine get_word

subroutine get_coord(line,ilon,ilat,ipres)
implicit none
character(len=*)    :: line
character(len=60)   :: word
integer,intent(out) :: ilon,ilat,ipres
integer             :: ipos,iend
ipres = 1
ilon  = 0
ilat  = 0
do
    call get_word(line,word,iend)
    if(WORD.eq.' '.or.WORD(1:1).eq.'!') exit
    ipos = index(word,'E')
    if(ipos.gt.1) then
      read(word(1:ipos-1),*) ilon
      ilon = MAX(1,MIN((ilon+10)/10,36))
    endif
    ipos = index(word,'W')
    if(ipos.gt.1) then
      read(word(1:ipos-1),*) ilon
      ilon=360-ilon
      ilon = MAX(1,MIN((ilon+10)/10,36))
    endif
    ipos = index(word,'N')
    if(ipos.gt.1) then
      read(word(1:ipos-1),*) ilat
      ilat = 90-ilat
      ilat = MAX(1,MIN((ilat+10)/10,18))
    endif
    ipos = index(word,'S')
    if(ipos.gt.1) then
      read(word(1:ipos-1),*) ilat
      ilat = 90+ilat
      ilat = MAX(1,MIN((ilat+10)/10,18))
    endif
    ipos = index(word,'HPA')
    if(ipos.gt.1) then
      read(word(1:ipos-1),*) ipres
      ipres = 1000-ipres
      ipres = MAX(1,MIN((ipres+150)/100,10))
    endif
    enddo
end

subroutine stopit(string)
implicit none
character(len=*), intent(in) :: string
print *,string
close(5)
read(*,*,end=999)
999 stop
end

