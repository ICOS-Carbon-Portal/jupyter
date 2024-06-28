#define pi      3.141592654
#define GRAD    57.29577951     /* 180/pi */
#define RAD     0.0174532925    /* pi/180 */
#define rEarth  6371000.0       /* Earth's radius in m */
#define RErad   111192.9        /* rEarth*rad */
#define RErad2  1.23643e10      /* RErad^2 */
#define Ro      287.05          /* gas-constant per kg */
#define Rgas    8.3143          /* gas-constant per mol */
#define Mair    0.028966        /* molecule mass of dry air kg/mol */
#define avo     6.0248e23
#define G       9.81
#define T0      273.15

#define datafolder "/mfo1/prakchem/MOGUNTIA_IN/"

#define NLON    35
#define NLON1   36
#define NLON2   37
#define NLAT    17
#define NLAT1   18
#define NLAT2   19
#define NPRES    9
#define NPRES1  10
#define NPRES2  11

#define DEGx    10		/* dx in degrees */
#define DEGy    10		/* dy in degrees */
#define deg0     5		/* 0.5 DEGy */
#define deg1     5		/* 0.5 DEGx */

#define dt     7200.0		/* transport timestep in seconds */
#define DAYSTEPS 12		/* number of timesteps per day */
#define MONTHSTEPS 360		/* number of timesteps per month */
#define YEARSTEPS 4320		/* number of timesteps per year */
#define NMONTH 12
#define NDAYS  30

typedef float  blkdata  [ NLON1 ][ NLAT1 ][ NPRES1 ];
typedef float  blkdata1 [ NLON1 ][ NLAT2 ][ NPRES1 ];
typedef float  blkdata2 [ NLON1 ][ NLAT1 ][ NPRES2 ];
typedef short  blkdata_s[ NLON1 ][ NLAT1 ][ NPRES1 ];
typedef char   blkdata_c[ NLON1 ][ NLAT1 ][ NPRES1 ];
typedef unsigned char   blkdata_uc[ NLON1 ][ NLAT1 ][ NPRES1 ];

typedef float  planeV   [ NLAT2 ][ NPRES1 ];
typedef float  planeH   [ NLON1 ][ NLAT2  ];

typedef float  xyplane  [ NLON1 ][ NLAT1 ];
typedef float  xzplane  [ NLON1 ][ NPRES1 ];
typedef float  yzplane  [ NLAT1 ][ NPRES1 ];

typedef double  dblkdata  [ NLON1 ][ NLAT1 ][ NPRES1 ];
typedef double  dblkdata1 [ NLON1 ][ NLAT2 ][ NPRES1 ];
typedef double  dblkdata2 [ NLON1 ][ NLAT1 ][ NPRES2 ];

typedef double  dplaneV   [ NLAT2 ][ NPRES1 ];
typedef double  dplaneH   [ NLON1 ][ NLAT2  ];

typedef double  xydplane  [ NLON1 ][ NLAT1 ];
typedef double  xzdplane  [ NLON1 ][ NPRES1 ];
typedef double  yzdplane  [ NLAT1 ][ NPRES1 ];

typedef float coefblk[ NLON1 ][ NLAT1 ][ NPRES1 ][11];


