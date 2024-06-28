      subroutine init
      use dimension
      use units
      use hdf
      integer    ::istat,sds_id,sfselect,sfrdata,sfendacc
      real    :: gtr
!      read(iasland) asland
      sds_id = sfselect(imeteo,0)
      istat = sfrdata(sds_id,(/0,0/),(/1,1/),(/nu,nv/),asland)
      print*,'HDF read asland returns:',istat
      istat = sfendacc(sds_id)


!
!------first fill some data
!
       
      gtr=pi/180.
      API180=A*gtr
      do i=1,nr
        zra(i)=ra(i)
      enddo
      call zlog(zra,nr)     !calculate height that corresponds to pres.
      end
      SUBROUTINE ZLOG(ARAD,nra)
      implicit none
      integer,intent(in)                ::nra
      real,dimension(nra),intent(inout) ::arad
      real,parameter                    ::be = 5.255, al = 2.184e-5
      integer ::i
      real :: p
!
!stimate the height that corresponds to pressure levels 
!
      print*,' Pressure (hPa) - Height (m)'
      DO I=1,NRA
        p = arad(i)
        ARAD(I) = (1.0-(p/1000.0)**(1.0/BE))/AL
        print'(f10.1,f10.0)',p,arad(i)
      enddo
      RETURN
      END
