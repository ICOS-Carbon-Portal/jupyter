subroutine readmet(mon)
use dimension
use convection
use units
use hdf
implicit none
integer,intent(in)  ::mon
integer i,j,k
real fac,dummy
integer :: monptr 
integer sds_id,istat,sfrdata,sfselect,sfendacc

monptr = 1+(mon-1)*11

sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),Z)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
!print*,z(9,9,1),'z'

monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),DZ)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
!print*,dz(9,9,1),'dz'

monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),DTHICK)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
!print*,dthick(9,9,2),'dthick'
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu2,nv,nw/),TEMP)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
!print*,temp(9,9,1),'temp'

 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu2,nv,nw/),RHOM)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),AR)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),H2O)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0/),(/1,1/),(/nu2,nv/),PORO)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0/),(/1,1/),(/nu2,nv/),IORO)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0/),(/1,1/),(/nu,nv/),ITROPO)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(imeteo,monptr)
istat= sfrdata(sds_id,(/0,0/),(/1,1/),(/nu,nv/),SNOW)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
!print*,snow(9,9),'snow'
FAC=AVO/XMAIR*1.E-6
DO 116 I=1,NU
  DO 116 J=1,NV
    DO 116 K=1,NW
       AIR(I,J,K)=RHOM(I,J,K)*FAC
 116  CONTINUE 
dummy=1e-3*1e9*XMAIR/XMH2O   !ppb 1e9 1e-3=kg-->g
h2o = h2o * dummy

 call saturat !vapor concentration in ppb for saturation
 
! read convection files

monptr = 720+(mon-1)*2
sds_id = sfselect(iconvection,monptr)
istat= sfrdata(sds_id,(/0,0,0/),(/1,1,1/),(/nu,nv,nw/),dfmu)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat
 
monptr = monptr + 1
sds_id = sfselect(iconvection,monptr)
istat= sfrdata(sds_id,(/0,0/),(/1,1/),(/nu,nv/),ksurf)
!print*,'sfrdata returns',istat
istat=sfendacc(sds_id)
!print*, 'sfendacc returns: ', istat

end
SUBROUTINE SATURAT
use dimension
implicit none
real tkt,tr1,tr2,tr3,tr4,esat
integer i,j,k
!
!  SUBROUTINE TO CALCULATE SATURATION CONCENTRATION ppb
! AFTER RICHARDS (1971) CF BROTSAERT 1982.
!
       DO 66 I=1,NL
       DO 66 J=1,NP
       DO 66 K=1,NR
       TKT =TEMP(I,J,K)+TK0 !TK0=273.15
       TR1=1.-373.15/TKT
       TR2=TR1*TR1
       TR3=TR2*TR1
       TR4=TR2*TR2
       ESAT=13.3185*TR1-1.9760*TR2-.6445*TR3-.1299*TR4
       ESAT=1013.25*EXP(ESAT) !hPa
       esat=esat/(ra(k))*0.622!Brutsaert
       satur(i,j,k)=esat*xmair/xmh2o*1e9 !in ppb!!!
       if(h2o(i,j,k).gt.0.9*satur(i,j,k)) satur(i,j,k)=h2o(i,j,k)/0.9
 66    CONTINUE
       END
