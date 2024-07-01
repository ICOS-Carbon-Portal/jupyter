module convection
use dimension
use units
implicit none

real, dimension(nu,nv,nw)  ::DFMU  !mass flux in convection routine
integer, dimension(nu,nv)  ::ksurf !surface field that describes active convection
integer(kind=2),dimension(12)     ::nh    !number of convection events every two hours
integer(kind=2),dimension(12,370) ::nkon  !geographical distribution convection events
integer, dimension(8)      ::nkonv !shuffles convection 
integer,parameter          ::konvec=1  !non-diffusive convection

contains

      SUBROUTINE KONVMK(XMK,IHH,NN,MON,MRATIO,IFKON,xmolg)
!
!
!
!
!    BERECHNET AUS DEN MASSENFLUESSEN DIE NEUEN
!    KONZENTRATIONEN IN G/G

     real,dimension(nu2,nv,nw),intent(inout)   ::xmk   !trace distribution before/after convection
     integer,intent(in) ::ihh,mon,mratio,ifkon
     integer(kind=2),intent(in) ::nn
     real,intent(in)  ::xmolg !molmass of the tracer
     real,DIMENSION(nw) :: XMASSLA,XMASSLN,XMASST
     real,parameter ::BG=1.,FUP=0.03
     integer        ::mona=0
     save mona

!   nur zum drucken >

    real,dimension(nw) ::xmijk,dfijk

    integer            ::i,j,k,npm,ku,n,ke
    real               ::df7,df8,volfak,fupdr,rvolfak,sumte,sumdfd,sume,hil,dmasst,dmassl
    real               ::suma,dmt,xmasstu,fak,xmss

      FUPDR=BG*FUP
      VOLFAK=XMOLG/XMAIR
      IF(MRATIO.EQ.0) VOLFAK=1.
      RVOLFAK=1./VOLFAK
      DO 90 N=1,NN
      I=NKON(IHH,N)/100.
      J=NKON(IHH,N)-I*100
  180 FORMAT(2X,'I,J,KU,N,XMASS',4I3,E12.4)
      KU=KSURF(I,J)
      IF(KU.EQ.0) GO TO 90
      SUMA=0.
      DO 10 K=KU,NR
      XMASSLA(K)=AR(I,J,K)*RHOM(I,J,K)
      XMASSLN(K)=XMASSLA(K)
      XMASST(K)=XMK(I,J,K)*XMASSLA(K)*VOLFAK
      SUMA=SUMA+XMASST(K)
      XMIJK(K)=XMK(I,J,K)
      DFIJK(K)=DFMU(I,J,K)

   10 CONTINUE
!      Neuverteilung durch Aufsteigen in den updrafts
      IF(SUMA.EQ.0.) GO TO 90
      SUMTE=0.
      SUMDFD=0.
      SUME=0.
      DO 20 K=KU,NR
      SUME=SUME+XMASST(K)
      IF(DFMU(I,J,K).LE.0.) GO TO 21
      DMT=XMASST(K)*DFMU(I,J,K)/XMASSLN(K)
      SUMTE=SUMTE+DMT
      XMASSLN(K)=XMASSLN(K)-DFMU(I,J,K)
      XMASST(K)=XMASST(K)-DMT
      GO TO 20
   21 CONTINUE
      SUMDFD=SUMDFD+DFMU(I,J,K)
   20 CONTINUE
      FAK=SUMTE/SUMDFD
      DO 30 K=KU,NR
      IF(DFMU(I,J,K).GE.0.) GO TO 30
      XMASSLN(K)=XMASSLN(K)-DFMU(I,J,K)
      XMASST(K)=XMASST(K)+FAK*DFMU(I,J,K)
   30 CONTINUE
      XMSS=0.
      XMASSTU=0.
      DO 15 K=KU,NR
      IF(DFMU(I,J,K).LT.0.) GO TO 16
      XMSS=XMSS+XMASSLN(K)
      XMASSTU=XMASSTU+XMK(I,J,K)*XMASSLN(K)*VOLFAK
      KE=K
   15 CONTINUE
   16 CONTINUE
      XMASSTU=XMASSTU*FUPDR
      DO 35 K=KU,KE
      XMASST(K)=XMASST(K)*(1.-FUPDR)+XMASSTU*XMASSLN(K)/XMSS
   35 CONTINUE
   99 CONTINUE
!     kompensierendes Absinken
      DMASSL=XMASSLA(NR)-XMASSLN(NR)
      DMASST=DMASSL*XMASST(NR)/XMASSLN(NR)
      XMASSLN(NR)=XMASSLN(NR)+DMASSL
      XMASST(NR)=XMASST(NR)+DMASST
      DO 40 K=NR-1,KU+1,-1
!      Absinken von oben
      XMASSLN(K)=XMASSLN(K)-DMASSL
      XMASST(K)=XMASST(K)-DMASST
!      Absinken nach unten
      DMASSL=XMASSLA(K)-XMASSLN(K)
      DMASST=DMASSL*XMASST(K)/XMASSLN(K)
      XMASSLN(K)=XMASSLN(K)+DMASSL
      XMASST(K)=XMASST(K)+DMASST
  40  CONTINUE
      XMASSLN(KU)=XMASSLN(KU)-DMASSL
      XMASST(KU)=XMASST(KU)-DMASST
      SUME=0.
      DO 50 K=KU,NR
      HIL=XMASST(K)/XMASSLA(K)*RVOLFAK
      XMK(I,J,K)=HIL
      XMIJK(K)=HIL
      SUME=SUME+XMASST(K)
  50  CONTINUE
   90 CONTINUE
      RETURN
      END SUBROUTINE KONVMK

      subroutine read_convection
      use hdf
      implicit none
      integer :: ih,n,ic_tel,sfselect,sfrdata,sfendacc,istat,sds_id,maxnh
      ic_tel = ((imon-1)*30 + (iday-1))*2 
      sds_id = sfselect(iconvection,ic_tel)
      istat = sfrdata(sds_id,(/0/),(/1/),(/12/),NH )
!      print*,'convection returns:',istat,ic_tel
      istat = sfendacc(sds_id)
      sds_id = sfselect(iconvection,ic_tel+1)
      maxnh = MAXval(NH)
      istat = sfrdata(sds_id,(/0,0/),(/1,1/),(/12,maxnh/),NKON(1:12,1:maxnh))
!      print*,'convection returns:',istat
      istat = sfendacc(sds_id)

      END SUBROUTINE read_convection
end module convection
