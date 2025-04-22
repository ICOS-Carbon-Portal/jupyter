#include <stdio.h>
#include <stdlib.h>
#include "types.h"

const int NPOINTS = NLON1*NLAT1*NPRES1;
const int NPOINTS1 = NLON1*NLAT2*NPRES1;
const int XYPLANE = NLON1*NLAT1;
const int XZPLANE = NLON1*NPRES1;
const int YZPLANE = NPRES1*NLAT1;
const int LON2    = NLON1/2;

const float PRESS[] = {10e4, 9e4, 8e4, 7e4, 6e4, 5e4, 4e4, 3e4, 2e4, 1e4};
const float PRBOUND[] = {10.e4, 9.5e4, 8.5e4, 7.5e4, 6.5e4, 5.5e4, 4.5e4, 3.5e4, 2.5e4, 1.5e4, 1e4};
float DPRES[NPRES1]; /* thickness of layer */
float DLAYER[NPRES]; /* distance between centre of layers */

blkdata      dz;
double       dx[NLAT1];
const double dy = DEGy*RErad;
double       coslat[NLAT1], coslatb[NLAT2];

const char months_long[][10] = {"January","February","March","April","May",
  "June","July","August","September","October","November","December"};


