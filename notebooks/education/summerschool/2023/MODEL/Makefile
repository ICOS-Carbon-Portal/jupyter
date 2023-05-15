#
# Make file moguntia + quickest transport:
# Tracer version used for MCF simulation!

FFILES = dimension.f90 hdf.f90 .units.f90 convection.f90 input.f90 moguntia.f90 readmet.f90 init.f90 tools.f90

CFILES = globals.c transport.c 

OBJECTS = dimension.o hdf.o units.o convection.o input.o moguntia.o globals.o transport.o readmet.o init.o tools.o 

LIBDIR= /home/jovyan/education/summerschool/local/gnu_11.2.0
HDF4= $(LIBDIR)/hdf-4.2.15/lib/
JPEG= $(LIBDIR)/jpegsrc.v6b/lib/
SZIP= $(LIBDIR)/szip-2.1/lib/
ZLIB= $(LIBDIR)/zlib-1.2.7/lib/
#FFLAGS=  -O5 -c 
#FFLAGS=  -g -c 
FFLAGS = -c -fno-second-underscore -w -fallow-argument-mismatch -O2 
#FFLAGS = -c -g -fno-second-underscore -w -fallow-argument-mismatch -O2 
#FFLAGS = -O2 -c -YEXT_NAMES=LCS 
#CFLAGS=  -O3 -c
CFLAGS=  -O3 -c
#LFLAGS=  -L/sw/arch/Debian10/EB_production/2019/software/HDF/4.2.14-GCCcore-8.3.0/lib -lmfhdf -ldf -ljpeg -lz -lsz
LFLAGS=  -L$(HDF4) -lmfhdf -ldf -L$(JPEG) -ljpeg -L$(ZLIB) -lz -L$(SZIP) -lsz -ltirpc
#LFLAGS=  -L ./hdf-4.2.10/hdf4/lib/ -lmfhdf -ldf -L/opt/local/lib -ljpeg -lz -lsz

LINKER=gfortran
FC=gfortran
CC=gcc 
MOGUNTIA : $(OBJECTS) 
	$(LINKER) $(OBJECTS) $(LFLAGS) -o $@
.f90.o: $(FFILES)
	$(FC) $(FFLAGS) $<
.c.o: $(CFILES)
	$(CC) $(CFLAGS) $<

clean:
	rm -f *.o MOGUNTIA *.mod

.SUFFIXES:
.SUFFIXES: .f90 .o .c .mod

