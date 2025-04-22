MODULE HDF
implicit none
include 'hdfinc.f90'
integer,parameter  :: comp_type = 4 
integer,parameter,dimension(1)  :: comp_prm = (/ 1 /)
CONTAINS



SUBROUTINE IO_WRITE3D_32(sd_id,im,jm,lm,data,name)

implicit none
integer            :: sfcreate,sfscompress,sfwdata,sfendacc
integer,intent(in) :: im,jm,lm,sd_id
character(len=*),intent(in) :: name
integer            :: rank = 3    ,istat
integer,dimension(3) :: start = (/ 0,0,0 /), stride= (/1,1,1/)
real,dimension(im,jm,lm),intent(in) ::data
integer            :: sds_id

sds_id = sfcreate(sd_id, name, DFNT_FLOAT32, rank, (/im,jm,lm/) )
print*,'sfcreate returns dataset id:',sds_id
istat = sfscompress(sds_id,comp_type,comp_prm)
print*,'sfscompress returns:',istat
istat  = sfwdata(sds_id, start, stride, (/im,jm,lm/) , real(data,kind=4) )
print*,'sfwdata returns:',istat
istat = sfendacc(sds_id)
print*, 'sfendacc returns: ', istat

END SUBROUTINE IO_WRITE3D_32

SUBROUTINE IO_WRITE2D_32(sd_id,im,jm,data,name)

implicit none
integer            :: sfcreate,sfscompress,sfwdata,sfendacc
integer,intent(in)          :: im,jm,sd_id
character(len=*),intent(in) :: name
integer            :: rank = 2    ,istat
integer,dimension(2) :: start = (/ 0,0 /), stride= (/1,1/)
real,dimension(im,jm),intent(in) ::data
integer            :: sds_id

sds_id = sfcreate(sd_id, name, DFNT_FLOAT32, rank, (/im,jm/) )
print*,'sfcreate returns dataset id:',sds_id
istat = sfscompress(sds_id,comp_type,comp_prm)
print*,'sfscompress returns:',istat
istat  = sfwdata(sds_id, start, stride, (/im,jm/) , real(data,kind=4) )
print*,'sfwdata returns:',istat
istat = sfendacc(sds_id)
print*, 'sfendacc returns: ', istat

END SUBROUTINE IO_WRITE2D_32
 
SUBROUTINE IO_WRITE2D_I16(sd_id,im,jm,data,name)

implicit none
integer            :: sfcreate,sfscompress,sfwdata,sfendacc
integer,intent(in)          :: im,jm,sd_id
character(len=*),intent(in) :: name
integer            :: rank = 2    ,istat
integer,dimension(2) :: start = (/ 0,0 /), stride= (/1,1/)
integer(kind=2),dimension(im,jm),intent(in) ::data
integer            :: sds_id

sds_id = sfcreate(sd_id, name, DFNT_INT16, rank, (/im,jm/) )
print*,'sfcreate returns dataset id:',sds_id
istat = sfscompress(sds_id,comp_type,comp_prm)
print*,'sfscompress returns:',istat
istat  = sfwdata(sds_id, start, stride, (/im,jm/) , data)
print*,'sfwdata returns:',istat
istat = sfendacc(sds_id)
print*, 'sfendacc returns: ', istat

END SUBROUTINE IO_WRITE2D_I16

SUBROUTINE IO_WRITE2D_I32(sd_id,im,jm,data,name)

implicit none
integer            :: sfcreate,sfscompress,sfwdata,sfendacc
integer,intent(in)          :: im,jm,sd_id
character(len=*),intent(in) :: name
integer            :: rank = 2    ,istat
integer,dimension(2) :: start = (/ 0,0 /), stride= (/1,1/)
integer(kind=4),dimension(im,jm),intent(in) ::data
integer            :: sds_id

sds_id = sfcreate(sd_id, name, DFNT_INT32, rank, (/im,jm/) )
print*,'sfcreate returns dataset id:',sds_id
istat = sfscompress(sds_id,comp_type,comp_prm)
print*,'sfscompress returns:',istat
istat  = sfwdata(sds_id, start, stride, (/im,jm/) , data)
print*,'sfwdata returns:',istat
istat = sfendacc(sds_id)
print*, 'sfendacc returns: ', istat

END SUBROUTINE IO_WRITE2D_I32


SUBROUTINE IO_READ2D_I16(sd_id,im,jm,data,name)

implicit none
integer            :: sffinfo,sfselect,sfginfo,sfrdata,sfendacc
integer,intent(in)          :: im,jm,sd_id
character(len=*),intent(in) :: name
integer            :: rank = 2    ,istat
integer,dimension(2) :: start = (/ 0,0 /), stride= (/1,1/)
integer(kind=2),dimension(im,jm),intent(out) ::data
integer            :: sds_id,ndatasets, nglobat, i, xrank, xtype, natt, j
integer,dimension(10) :: dimsizes
character(len=40)     :: xname

istat  = sffinfo(sd_id, ndatasets, nglobat)
print*, 'sffinfo returns #datasets #attributes',ndatasets,nglobat
do i=0,ndatasets-1
   sds_id = sfselect(sd_id,i)
   !print*,'sfselect returns dataset id:',sds_id
   istat  = sfginfo(sds_id,xname,xrank,dimsizes,xtype,natt)
   print*,'sfginfo returns',istat
   istat = index(name,' ')
   if ((name(1:istat-1).eq.xname(1:istat-1)).and.(rank.eq.xrank).and.(xtype.eq.DFNT_INT16)) then
   if(dimsizes(1).eq.im.and.dimsizes(2).eq.jm) then
     istat= sfrdata(sds_id,start,stride,(/im,jm/),data)
     print*,'sfrdata returns',istat 
     istat=sfendacc(sds_id)
     print*, 'sfendacc returns: ', istat
     exit
   endif
   endif
   istat = sfendacc(sds_id)
enddo

END SUBROUTINE IO_READ2D_I16
END MODULE HDF

