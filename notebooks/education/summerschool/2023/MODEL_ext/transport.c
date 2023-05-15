/* MOGUNTIA-version. Adapted to FORTRAN

  coefficients must be stored in "datafolder" (defined in types.h)
  usage:
  initialise only once at the beginning of the program by:

      CALL INIT_TRANSPORT
  
  monthly update:

      CALL READCOEFS(IMON) ! IMON=1..12

  actual transport:
  
      DO ITIM = 1,12
        CALL DOTRANSPORT(TRACER) ! REAL*8 TRACER(37,18,10)
      ENDDO

  time-steps are fixed (2 hours), but can be changed during pre-processing
  (see types.h).

  DOTRANSPORT replaces TRANSXM and REPAIR.

  ----------------------------------
  Author: Han The RIVM
  Latest update: 24 May 1994
  ----------------------------------

*/

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <math.h>
#include <errno.h>
#include "globals.h"
/* #include "/usr/include/hdf/hdf.h"   */
#include "/home/wouter/include/hdf.h"  
/* #include "/sw/arch/Debian10/EB_production/2019/software/HDF/4.2.14-GCCcore-8.3.0/include/hdf/hdf.h" */
/* #include "/storage/imau/HDFvers/HDF4.1r2/include/hdf.h" */

#define diam(i) ((i+LON2) % NLON1) /* diametral point */
#define rval(i)  ((i)==NLON)?0:(i+1)
#define rval2(i) (i+2)%NLON1
#define lval(i)  ((i)==0)?NLON:(i-1)
#define lval2(i) (i+NLON1-2)%NLON1

static float   ZEROVAL = 0;

static float *concptr[NLON1][NLAT1][NPRES1][11];
static coefblk coefs;

static float *swapper[NLON1][NLAT1][NPRES1];
static float *swapper1[NLON1][NLAT1][NPRES1];

static long int MCOEFBLK = sizeof(coefs);
static long int MBLK = sizeof(float)*NLON2*NLAT1*NPRES1;

static float c_tmp[NPRES1][NLAT1][NLON2];
static float c_new[NPRES1][NLAT1][NLON2];

static FILE *coefdata;
static int itransport;
static int sds_id,  istat;
static int start[1];
static int stride[1];
static int ends[1];

/*------------------------------------------------------------------------*/
void openfile (FILE **fp, char *name, char *mode){
/*
  openfile opens file *fp and gives an error message if it isn't possible.
*/
  errno = 0;
  *fp = fopen(name,mode);
  if (!(*fp)){
    printf("Can't open '%s'.\n", name);
    perror("Program stopped");
    exit(1);
  }
}

/*-------------------------------------------------------------------*/
void setfluxptr(){
/*
  setfluxptr initialises swappers at the beginning of the program.
  swapper: to old concentrations  (c_tmp)
  swapper1: to new concentrations (c_new)

  fluxptr[0]: east
  fluxptr[1]: west
  fluxptr[2]: south
  fluxptr[3]: north
  fluxptr[4]: vertical flux
*/
  register int i,j,k;

  for (k=0; k<NPRES1; k++)
  for (j=0; j<NLAT1; j++)
  for (i=0; i<NLON1; i++){
    swapper[i][j][k] = &c_tmp[k][j][i];
    swapper1[i][j][k]= &c_new[k][j][i];
  }

  for (i=0; i<NLON1; i++)
  for (j=0; j<NLAT1; j++)
  for (k=0; k<NPRES1; k++){
    concptr[i][j][k][0] = swapper[i ][j][k];
    concptr[i][j][k][1] = swapper[rval2(i)][j  ][k];
    concptr[i][j][k][2] = swapper[rval(i) ][j  ][k];
    concptr[i][j][k][3] = swapper[lval(i) ][j  ][k];
    concptr[i][j][k][4] = swapper[lval2(i)][j  ][k];
    concptr[i][j][k][5] = swapper[i ][j+2][k];
    concptr[i][j][k][6] = swapper[i ][j+1][k];
    concptr[i][j][k][7] = swapper[i ][j-1][k];
    concptr[i][j][k][8] = swapper[i ][j-2][k];
    concptr[i][j][k][9] = swapper[i ][j  ][k-1];
    concptr[i][j][k][10]= swapper[i ][j  ][k+1];
  }

/* reset values at Poles */
  for (i=0; i<NLON1; i++)
  for (k=0; k<NPRES1; k++){
    concptr[i][NLAT-1][k][5] = swapper[diam(i)][NLAT][k];
    concptr[i][NLAT][k][5] = &ZEROVAL;
    concptr[i][NLAT][k][6] = swapper[diam(i)][NLAT][k];
    concptr[i][0   ][k][7] = swapper[diam(i)][0   ][k];
    concptr[i][0   ][k][8] = &ZEROVAL;
    concptr[i][1   ][k][8] = swapper[diam(i)][0   ][k];
  }

/* reset values at top and bottom */
  for (i=0; i<NLON1; i++)
  for (j=0; j<NLAT1; j++){
    concptr[i][j][0][9]     = &ZEROVAL;
    concptr[i][j][NPRES][10] = &ZEROVAL;
  }

}

/*-------------------------------------------------------------------*/
void init_transport_(){
  /*  char name[100] = datafolder; */
  /* strcat(name,"transcoef.dat"); */
  /* openfile(&coefdata, name, "r"); */
  /*  openfile(&coefdata, "transcoef.dat", "r"); */
  /* to adapt */
  itransport = SDstart(
  "/home/wouter/summerschool/2023/DATA/transport.hdf",
  DFACC_READ);
  printf("itransport %d\n", itransport);
  setfluxptr();
}

/*-------------------------------------------------------------------*/
void readcoefs_(int *month){
  /* fseek(coefdata, sizeof(coefs)*(*month-1), SEEK_SET);
  fread(coefs, sizeof(coefs), 1, coefdata); */
  sds_id = SDselect(itransport,*month-1);
  /* printf("sds_id gives %d\n", sds_id); */
  ends[0] = sizeof(coefs)/4;  /* four bytes per number */
  start[0] = 0 ;
  stride[0] = 1 ;
  istat = SDreaddata(sds_id, start, stride, ends, (VOIDP) coefs);
  /* printf("Istat gives %d\n", istat); */
  istat = SDendaccess(sds_id);
}

/*-------------------------------------------------------------------*/
void dotransport_(float *cnew){
/*
  dotransport calculates the new concentration values.
  new concentrations are stored in cnew and calculated as:
  cnew =
      coefs[0]*c_old(i,j,k)
    + coefs[1]*c_old(i+2,j,k)
    +...
  old concentrations are stored in global variable conc,
  which are redirected through concptr.
*/

  register int n, m, i, k;
  register float **cp, **cp2, *coefptr;
  register float sum;
  register float *cpn;

  memcpy(c_tmp,cnew,MBLK);
  memcpy(c_new,cnew,MBLK);

/* Calculate new concentration */

  cp2 = (float **)swapper1;
  coefptr = (float *)coefs;
  cp   = (float **)concptr;
  n = NPOINTS;
  while (n--){
    m = 11;
    while (m--) **cp2 += (**cp++)*(*coefptr++);
    cp2++;
  }

  for (m=0; m<NPRES1; m++){
    cpn = c_new[m][0];
    sum = 0;
    n = NLON1;
    while (n--) sum += *cpn++;
    sum /= NLON1;
    n = NLON1;
    cpn = c_new[m][0];
    while (n--) *cpn++ = sum;

    cpn = c_new[m][NLAT];
    sum = 0;
    n = NLON1;
    while (n--) sum += *cpn++;
    sum /= NLON1;
    n = NLON1;
    cpn = c_new[m][NLAT];
    while (n--) *cpn++ = sum;
  }

  cp2   = (float **)swapper1;
  n = NPOINTS;
  while (n--){
    if (**cp2<0) **cp2 = 0;
    cp2++;
  }

  memcpy(cnew,c_new,MBLK);
}

