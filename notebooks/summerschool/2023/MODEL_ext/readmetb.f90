subroutine readmetb(mon)
use dimension
use convection
use units
implicit none
integer,intent(in)  ::mon
integer i,j,k
real fac,dummy
integer :: monptr = 1
save monptr

if(mon.eq.monptr) then
  read(imeteo) z,dz,dthick,temp,rhom,ar,h2o,poro,ioro,itropo,snow
  snow(:,1:2) = 1.0
  snow(:,15:18) = 1.0
  read(imassflux) dfmu,ksurf
else
  rewind(imeteo)
  rewind(imassflux)
  do i=1,mon
     read(imeteo) z,dz,dthick,temp,rhom,ar,h2o,poro,ioro,itropo,snow
     read(imassflux) dfmu,ksurf
  enddo
endif
monptr = monptr + 1
if (monptr.gt.12) then
  rewind(imeteo)
  rewind(imassflux)
  monptr = 1
endif
FAC=AVO/XMAIR*1.E-6
DO 116 I=1,NU
  DO 116 J=1,NV
    DO 116 K=1,NW
       AIR(I,J,K)=RHOM(I,J,K)*FAC
 116  CONTINUE 
dummy=1e-3*1e9*XMAIR/XMH2O   !ppb 1e9 1e-3=kg-->g
h2o = h2o * dummy

 call saturat !vapor concentration in ppb for saturation
 

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
