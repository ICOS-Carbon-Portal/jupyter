program moguntia
!
! tracer version 
!
use dimension
use input
use convection
use units
implicit none

integer    ::mratio=1   !volume mixing ratios
integer    ::itr,IH,N,IHH,ILONG, i,j,ipos
real,dimension(nu,nv,nw) :: emission_field,chem_loss,sink
logical                  :: decay_flag,started = .false.
real                     :: decay 
!
call zopen           !link units to input files
call init_transport  !some initialization of the transport routine
call init            !some other initialisations
call get_input
xmass(1) = mol_mass_tracer
if(lifetime.gt.0.0) then
   decay = exp(-2./(lifetime*24.))
   decay_flag = .true.
else
   decay_flag = .false.
endif
ipos = 0
yearloop: do iyear=iyear_start,iyear_end
  print *, 'Simulation year:', iyear
  do imon = 1,12
    ipos = ipos + 1
    call readmet(imon)             !
    if (chemistry) call calc_chemistry(chem_loss)   !read also OH
    if (emission_file_hdf) then 
        call read_emis_field(ipos,emission_field)
    else
        call fill_emission_field(emission_field)
    endif
    if(sink_flag) call fill_sink_field(sink) ! calculate as negative emission

    CALL readcoefs(IMON) ! IMON=1..12, read transport coefficeints.
 
    dayloop: do iday=1,30
      call read_convection

!--------determine stop/end
      if(imon.ge.imon_start.and.iday.ge.iday_start) started=.true.
      if(iyear.ge.iyear_end.and.iday.ge.iday_end.and.imon.ge.imon_end) exit yearloop
      if(.not.started) cycle dayloop
!       print*,iyear,imon,iday
!--------
      IHH=0                                   
      DO ihour = 2,24,2
        tr(1:nu,1:nv,1,1) =  tr(1:nu,1:nv,1,1) + emission_field(:,:,1)
        if (sink_flag) then
          tr(1:nu,:,1,1) = tr(1:nu,:,1,1) + sink(:,:,1)
        endif
        if (off_surface) then 
             tr(1:nu,1:nv,2:10,1) =  tr(1:nu,1:nv,2:10,1) + emission_field(:,:,2:10)
        endif
        ihh=ihh+1  
        do ilong = 1,NLONG
           CALL TRANSXM (tr(1,1,1,ilong),xmass(ilong),IHH,mratio)
        enddo
        if (decay_flag) tr(1:nu,:,:,1) = tr(1:nu,:,:,1)*decay
        if (chemistry) tr(1:nu,:,:,1) = tr(1:nu,:,:,1)*chem_loss
        if (concentration_fixer) then
          do i = 1, n_conc
             tr(c_conc(i,1),c_conc(i,2),c_conc(i,3),1) = s_conc(i)
          enddo
        endif
        call output_average
      ENDDO   !time loop
    enddo dayloop
    if((o_zama.or.o_llma).and.started) call output_write_monthly
  enddo    !month loop
  if (chemistry) rewind(unit_oh)
  if (emission_file) rewind(unit_emission)
  if (sink_flag) rewind(unit_sink)
  if (sink_flag) rewind(unit_sinke)
enddo yearloop 
999 continue
open(unit=106,file=outpath//'previous.bin',form='unformatted',status='unknown')
write(106) tr
close(106)
!print *,'total CH4 consumed in Tg',totch4
stop
end


SUBROUTINE TRANSXM (TRT,XMTR,IHH,mratio)
use dimension
use convection
use units
use input
implicit none
real,intent(inout),dimension(nu2,nv,nw) ::trt    !the tracer to be transported
real,intent(in)                         ::xmtr  !the moll mass
integer,intent(in)                      ::ihh   !pointer to array NH with # convection events
integer,intent(in)                      ::mratio  !1=volume mixing ratios

if(nh(ihh).gt.0.and.convection_flag) then
   CALL KONVMK(TRT,IHH,NH(IHH),imon,MRATIO,77,xmtr)  
endif

call dotransport(trt)   !transport the tracer field by the QUICKEST scheme
 
END              
